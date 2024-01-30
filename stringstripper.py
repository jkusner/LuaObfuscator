
import re

STRING_START_MULTILINE = ["[["]
STRING_END_MULTILINE = ["]]"]
STRING_START = ['"', "'"]
STRING_END = ['"', "'"]
COMMENT = ["//", "--"]
COMMENT_START = ["/*", "--[["]
COMMENT_END = ["*/", "]]"]
TABLE_INDEX_BRACKET_START = ["["]
TABLE_INDEX_BRACKET_END = ["]"]

ALL_SYMBOLS = STRING_START_MULTILINE + STRING_END_MULTILINE + \
    STRING_START + STRING_END + COMMENT + COMMENT_START + COMMENT_END


def strip(lua):
    # Start with Multi-Line Comments
    lua, removed_multiline_comments = strip_multiline_comments(lua)

    # Strip strings
    lua, strings = strip_strings(lua)

    # Strip comments
    lua, removed_comments = strip_comments(lua)

    lua = _replace_bracket_table_index(lua)

    # Check for failure
    for s in ALL_SYMBOLS:
        if s in lua:
            print("Error!!! Failed to correctly strip strings.")
            print("Here is a dump of the strings stripped:")
            for v in strings.values():
                print("\t", v)
            exit()

    return lua, strings, removed_multiline_comments + removed_comments


def replace(lua, strings, decrypt_func="", start="[[", end="]]"):
    start = decrypt_func + start
    if isinstance(lua, str):
        for k, v in strings.items():
            lua = lua.replace(k, start + v + end)
    else:
        for k, v in strings.items():
            for i in range(len(lua)):
                if lua[i] == k:
                    lua[i] = start + v + end
    return lua


def strip_multiline_comments(lua):
    removed = []
    for i in range(len(COMMENT_START)):
        r = _build_regex(COMMENT_START[i], COMMENT_END[i])
        while True:
            match = r.search(lua)
            if match is None:
                break
            removed.append(match.group(0))
            lua = lua[:match.start()] + lua[match.end():]
            print(match)

    return lua, removed


def strip_comments(lua):
    removed = []
    for i in range(len(COMMENT)):
        r = _build_regex(COMMENT[i])
        while True:
            match = r.search(lua)
            if match is None:
                break
            removed.append(match.group())
            lua = lua[:match.start()] + lua[match.end():]
    return lua, removed


def strip_strings(lua):
    lua, removed = _strip_multiline_strings(lua)
    lua, _removed = _strip_regular_strings(lua)
    removed.update(_removed)

    for k in removed.keys():
        removed[k] = removed[k].encode("utf-8").decode("unicode_escape")

    return lua, removed


def _strip_regular_strings(lua):
    removed = {}
    patterns = []

    for i in range(len(STRING_START)):
        start, end = STRING_START[i], STRING_END[i]
        patterns.append(_build_regex(start, end, False))

    while True:
        found = None
        first = len(lua) + 1

        # Find the first match
        for r in patterns:
            match = r.search(lua)
            if match is not None:
                if found is None or match.start() < first:
                    found = match
                    first = match.start()

        if found is not None:
            placeholder = _build_string_placeholder()
            removed[placeholder] = found.group()[len(start):-len(end)]
            lua = lua[:found.start()] + " " + placeholder + " " + lua[found.end():]
        else:
            break

    return lua, removed


def _strip_multiline_strings(lua):
    removed = {}
    for i in range(len(STRING_START_MULTILINE)):
        start, end = STRING_START_MULTILINE[i], STRING_END_MULTILINE[i]
        r = _build_regex(start, end)
        while True:
            match = r.search(lua)
            if match is None:
                break
            placeholder = _build_string_placeholder()
            removed[placeholder] = match.group()[len(start):-len(end)]
            lua = lua[:match.start()] + placeholder + lua[match.end():]
    return lua, removed


def _replace_bracket_table_index(lua):
    for i in range(len(TABLE_INDEX_BRACKET_START)):
        start, end = TABLE_INDEX_BRACKET_START[i], TABLE_INDEX_BRACKET_END[i]
        r = _build_regex(start, end)

        _offset = 0
        while True:
            match = r.search(lua, _offset)
            if match is None:
                break

            pre = lua[:match.start()] + " " + match.group() + " "
            lua = pre + lua[match.end():]
            _offset = len(pre) # we need to do this because we dont remove those brackets which would result in an infinite loop
    return lua


string_index = -1
def _build_string_placeholder():
    global string_index
    string_index += 1
    return "__STRING_{0}__".format(string_index)


def _build_regex(start, end=None, multiline=True):

    if end is None:
        # Return a simple single line regex
        return re.compile(re.escape(start) + r".*?$", re.MULTILINE)

    if multiline:
        rs = re.escape(start) + r"(.|\n|\r)*?" + re.escape(end)
    else:
        rs = start + r'(?:[^' + end + r'\\]|\\.)*' + end

    return re.compile(rs)
