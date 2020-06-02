import re


SPECIAL_CHARS = ['+', '-' '*', '/', '=', '^', '%',        # Math
                 '[', ']', '(', ')', '{', '}', '<', '>',  # Brackets
                 '!', '~', '#', '&', '|', '?',            # Logic
                 '@', '$', '\\', ';', ',', '.', ':']      # Symbols

SPECIAL_STRINGS = ['...', '..', '::',
                   '||', '&&',
                   '==', '!=', '~='
                   '>=', '<=',
                   '>>', '<<']

BUILTIN_WORDS = ['and', 'break', 'do', 'else', 'elseif', 'end',
                 'false', 'for', 'function', 'goto', 'if', 'in',
                 'local', 'nil', 'not', 'or', 'repeat', 'return',
                 'then', 'true', 'until', 'while', 'continue']  # 'continue' only in gLua

GM_WORDS = ['ENT', 'WEAPON', 'SWEP', 'GAMEMODE']

RESERVED_WORDS = BUILTIN_WORDS + GM_WORDS

TOKEN_PATTERN = re.compile(r"(\d*\.?\d+|[^\s"  # Checks for decimals with optional lead and required end ex: ".5", "0.5"
                           + re.escape("".join(SPECIAL_CHARS)) + r"]+|"
                           + re.escape("___sep___".join(SPECIAL_STRINGS)
                                       ).replace("___sep___", "|") + r"|["
                           + re.escape("".join(SPECIAL_CHARS)) + r"])")

WORD_PATTERN = re.compile(r"^[^\s"
                          + re.escape("".join(SPECIAL_CHARS)) + r"]+$")

SCOPE_IN = ['do', 'then', 'function']
# 'elseif' because it comes with a second 'then'.
SCOPE_OUT = ['end', 'elseif']


def tokenize(lua):
    return TOKEN_PATTERN.findall(lua)


def fix_functions(tokens, strings):
    """
        All functions called with string literals and table literals
        will be given parenthesis

        ex: print "abc" -> print("abc")
    """

    tokens = _fix_functions_string_literals(tokens, strings)
    tokens = _fix_functions_table_literals(tokens)
    tokens = fix_table_semicolons(tokens)

    return tokens


def fix_table_semicolons(tokens, start_index=0, start_depth=0):
    """
        Replaces semicolons in table definitions with commas

            {                           {
                "a";       ->               "a",
                "b"        ->               "b"
            }                           }
    """

    depth = start_depth
    for i in range(start_index, len(tokens)):
        t = tokens[i]

        if t == "{":
            depth += 1
        elif t == "}":
            depth -= 1
        elif t == "function":
            # Skip ahead to the end of the function
            end = find_function_end(tokens, i)
            return fix_table_semicolons(tokens, end, depth)
        elif depth > 0 and t == ";":
            tokens[i] = ","

    return tokens


def _fix_functions_string_literals(tokens, strings, start_index=0):
    last = None
    for i in range(start_index, len(tokens)):
        t = tokens[i]

        if last is None:
            last = t
            continue

        if is_word(last) and is_word(t):
            if t in strings.keys():
                tokens.insert(i, "(")
                tokens.insert(i + 2, ")")
                return _fix_functions_string_literals(tokens, strings, i)

        last = t

    return tokens


def _fix_functions_table_literals(tokens, start_index=0):
    last = None
    for i in range(start_index, len(tokens)):
        t = tokens[i]

        if last is None:
            last = t
            continue

        if is_word(last) and t == "{":
            end = find_table_end(tokens, i)
            tokens = tokens[:i] + ["("] + tokens[i:end] + [")"] + tokens[end:]
            return _fix_functions_table_literals(tokens, end)

        last = t

    return tokens


def find_table_end(tokens, start_index):
    """
    Find the end of a table declaration where start_index is the first '{'
    """

    depth = 0
    for i in range(start_index, len(tokens)):
        t = tokens[i]

        if t == "{":
            depth += 1
        elif t == "}":
            depth -= 1

            if depth == 0:
                return i + 1

    print("Fatal error occurred.",
          "Please check that your input is syntactically correct.", sep="\n")
    exit(0)


def find_function_end(tokens, start_index):

    depth = 0
    for i in range(start_index, len(tokens)):
        t = tokens[i]

        if t in SCOPE_IN:
            depth += 1
        elif t in SCOPE_OUT:
            depth -= 1

            if depth == 0:
                return i + 1

    return start_index


def is_word(s):
    return s is not None and s not in RESERVED_WORDS and WORD_PATTERN.match(s) is not None and not is_number(s)


def is_number(s):
    return s.isdigit()
