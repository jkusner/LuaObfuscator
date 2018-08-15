import time
import stringstripper
import tokenizer
import finalize
import random


INVISIBLE_CHAR = "\u202A"
DECRYPT_FUNC = INVISIBLE_CHAR * 7
_G = INVISIBLE_CHAR


current_step = 0
debug_mode = False


def log(s, debug_only=True):
    global current_step

    if not debug_only:
        print(s)
    else:
        if debug_mode:
            print(s)
        else:
            current_step += 1
            print("Step {0}...Done.".format(current_step))


def obfuscate(lua, encoder, globs, debug=False, xor_val=-1):
    """
    Does the complete obfuscation process, returning the result
    :return: Obfuscated Lua, Tokens, Strings, Comments
    """

    # Set the debug_mode global to the debug mode argument passed
    global debug_mode
    debug_mode = debug

    start_time = time.time()

    # Get an XOR to use
    if xor_val == -1:
        xor_val = random.randint(0, 255)
        log("Randomly chose XOR value {0}.".format(xor_val), False)

    # Set the XOR in the decryption code
    decrypt_code = encoder.get_decrypt_code(xor_val)

    # Strip comments and strings
    lua, strings, comments = stringstripper.strip(lua)
    log("Stripped {0} strings and {1} comments.".format(len(strings), len(comments)), False)

    # Tokenize
    tokens = tokenizer.tokenize(lua)
    log("Finished tokenizing {0} tokens.".format(len(tokens)), False)

    # About to begin
    log("Beginning Level {0} obfuscation...".format(encoder.level), False)

    # Make sure all functions are called with ()
    # Ex: print"Hello!" -> print("Hello!")
    tokens = tokenizer.fix_functions(tokens, strings)
    log("Fixed function notation.")

    # Obfuscate
    tokens = rearrange_functions(tokens)
    log("Rearranged functions.")

    tokens = colon_to_dot(tokens)
    tokens, strings = dot_to_index(tokens, strings)
    log("Rewrote table references.")

    tokens, strings = fix_tables(tokens, strings)
    log("Rewrote table keys.")

    tokens = rename_locals(tokens)
    log("Obfuscated locals.")

    tokens = rename_arguments(tokens)
    log("Renamed function arguments.")

    tokens = rename_loops(tokens)
    log("Renamed loop variables.")

    # Copy the old globals
    old_globs = globs[:]
    globs = assume_globals(tokens, globs)
    # Don't print here because the function prints on its own

    assumed = len(globs) - len(old_globs)

    tokens, strings = rename_globals(tokens, strings, globs)
    log("Obfuscated globals (with {0} assumed).".format(assumed))

    strings = encoder.encode_all(strings, xor_val)
    log("Obfuscated strings.")

    tokens = stringstripper.replace(tokens, strings, DECRYPT_FUNC, encoder.get_str_start(), encoder.get_str_end())
    log("Replaced strings.")

    lua = finalize.finalize(tokens, decrypt_code)

    log("Finished in {0:.3f} seconds.".format(time.time() - start_time), False)

    return lua, tokens, strings, comments


def rearrange_functions(tokens, start_index=0):
    """
    First checks for meta functions
    "function _PlayerMeta:Derp(...)" -> "function _PlayerMeta.Derp(self, ...)"

    Then, moves function declarations around
    "function f()"       -> "f = function()"
    "local function f()" -> "local f = function()"
    """
    for i in range(start_index, len(tokens)):
        t = tokens[i]
        # Look for function declaration without '(' after
        # EX:  function f()
        if t == "function":
            if tokens[i+1] != "(":
                # Find the function declaration opening '('
                p = index(tokens, "(", i)

                # Fix meta function if it is a meta function
                c = index(tokens, ":", i)
                if i < c < p:
                    # Colon was found, make it a . and fix function args
                    tokens[c] = "."
                    tokens.insert(p + 1, "self")
                    if tokens[p+2] != ")":
                        # If the function has arguments, add a comma here
                        # otherwise, we are done
                        # "(self a, b, c)" -> "(self, a, b, c)"
                        tokens.insert(p + 2, ",")

                # Insert the new function declaration
                tokens.insert(p, "function")
                tokens.insert(p, "=")

                # Delete the old declaration
                del tokens[i]
                return rearrange_functions(tokens, i)
    return tokens


def dot_to_index(tokens, strings):
    """
    Replaces "a.b" with "a[[[b]]]"
    TODO a[[[b]]] -> a[_decrypt[[_encrypted_b]]]
    """

    while "." in tokens:
        pos = index(tokens, ".")
        table = tokens[pos - 1]
        field = tokens[pos + 1]
        codename = "__TABLE_" + table + "_FIELD_" + field + "__"
        strings[codename] = field
        tokens[pos] = "["
        tokens[pos + 1] = codename
        tokens.insert(pos + 2, "]")

    return tokens, strings


def colon_to_dot(tokens):
    """
    Replaces a:b() with a.b(a,?)
    """

    # TODO recognize shortcuts. ex: func{"table"}, func"string"

    if ":" in tokens:
        pos = index(tokens, ":")

        # LocalPlayer() : SteamID()
        # Start Index
        #    ex: [ LocalPlayer, (, ), :, SteamID, (, ) ]
        #             0 ^

        start = find_beginning(tokens, pos - 1)
        end = pos
        size = end - start

        # ex: [ LocalPlayer, (, ) ]
        tbl = tokens[start:end]

        # ex: [ LocalPlayer, (, ), :, SteamID, (, LocalPlayer, (, ), ) ]
        tokens = tokens[:end + 3] + tbl + tokens[end + 3:]

        tokens[pos] = "."

        if tokens[pos + 3 + size] != ")":
            # Add a comma if there are other args:  table.field(table, args...)
            tokens.insert(pos + size + 3, ",")

        return colon_to_dot(tokens)

    return tokens


def rename_locals(tokens):
    for i in range(len(tokens)):
        t = tokens[i]
        if t == "local":
            # Look for local declaration
            l = tokens[i+1]

            # Should never happen since rearrange_functions() is called first
            if l == "function":
                continue

            # i + 1   name
            # i + 2   =
            # i + 3   (_G.)named
            start_index = i
            if tokens[i + 2] == "=":
                start_index = i + 4

            new_name = new_local_name(i+1)
            tokens = replace_locals(tokens, l, new_name, start_index)
            tokens[i + 1] = new_name

            # local a, b ...
            if tokens[i+2] == ",":
                j = i + 3
                while True:
                    l = tokens[j]
                    if tokens[j-1] == "," and is_var(l):
                        new_name = new_local_name(j)
                        tokens[j] = new_name
                        tokens = replace_locals(tokens, l, new_name, j+2)
                        j += 2
                    else:
                        break

    return tokens


def rename_globals(tokens, strings, globs, start_index=0):
    for i in range(start_index, len(tokens)):
        t = tokens[i]
        if t in globs and is_not_table_member(tokens, i):
            codename = "__GLOBAL_" + t + "__"
            strings[codename] = t
            tokens[i] = "]"
            tokens.insert(i, codename)
            tokens.insert(i, "[")
            tokens.insert(i, _G)
            return rename_globals(tokens, strings, globs, i)
    return tokens, strings


def rename_arguments(tokens):
    replaced = []
    for i in range(len(tokens)):
        t = tokens[i]
        if t == "function":
            # Look for functions that have arguments
            if tokens[i+1] == "(" and tokens[i+2] != ")":
                e = index(tokens, ")", i+2)

                # Find everything between parenthesis,
                # skip the comma between every 2 args
                args = tokens[i+2:e:2]

                for arg in args:
                    if arg not in replaced:
                        new_name = new_local_name(index(tokens, arg))
                        tokens = replace_locals(tokens, arg, new_name, i)
                        replaced.append(arg)
    return tokens


def rename_loops(tokens):
    replaced = []
    for i in range(len(tokens)):
        t = tokens[i]
        if t == "for":
            # Look for 'for' loops

            if tokens[i+2] == "=":
                # for a=b,c,d
                # Only one variable @ i+1
                v = tokens[i+1]
                if v not in replaced:
                    tokens = replace_locals(tokens, v, new_local_name(i+1), i)
                    replaced.append(v)

            else:
                # for a,b,c,d... in ...
                # any amount of variables between 'for' and 'in'
                e = index(tokens, "in", i)
                args = tokens[i+1:e:2]
                for arg in args:
                    if arg not in replaced:
                        tokens = replace_locals(tokens, arg, new_local_name(index(tokens, arg)), i)
                        replaced.append(arg)

    return tokens


def fix_tables(tokens, strings):
    """
    Changes table declarations so that

        {                       {
            a = 1      ->           ["a"] = 1
        }                       }

    """

    # Table depth. Only replace keys if the depth is > 0.
    depth = 0

    for i in range(len(tokens)):
        t = tokens[i]

        if t == "{":
            depth += 1
        elif t == "}":
            depth -= 1

        # print(depth, t)

        # Look for a table opening or next entry
        if t == "{" or t == "," and depth > 0:
            # Look for a variable name followed by '='
            if is_var(tokens[i+1]) and tokens[i+2] == "=":
                # Replace the variable name with a '[', '__STRING__', ']'
                n = tokens[i+1]
                s = "__TABLE_KEY_" + n + "__"
                strings[s] = n
                tokens[i+1] = "]"
                tokens.insert(i+1, s)
                tokens.insert(i+1, "[")
                return fix_tables(tokens, strings)

    return tokens, strings


def replace_locals(tokens, old_name, new_name, start_index):
    for i in range(start_index, len(tokens)):
        if tokens[i] == old_name and is_not_table_member(tokens, i):
            tokens[i] = new_name
    return tokens


def assume_globals(tokens, globs):
    """
    Assumes all non-builtin valid variable names
    are global and changes them
    EX: DarkRP will be placed in globs list
    """

    for i in range(len(tokens)):
        t = tokens[i]
        if t not in globs and is_var(t):
            log('Assuming "{0}" is a global.'.format(t), False)
            globs.append(t)

    return globs


def find_beginning(tokens, i):
    """
    Finds the beginning of the expression at the index

    EX:
        Tokens:
            LocalPlayer ( )
            ^             ^
            |             |
            |             input index
            output index
    """

    if is_var(tokens[i]):
        return i

    last = tokens[i]
    depth = 0

    while True:
        i -= 1
        t = tokens[i]
        nxt = None

        if i > 0:
            nxt = tokens[i - 1]

        if last == ")" or last == "}":
            depth += 1
        elif last == "(" or last == "{":
            depth -= 1

        if depth == 0:
            if t in ["="]:
                return i + 1
            if is_var(t) and nxt != "." and not is_var(last):
                return i
            # This will not work for table stuff right now
            # _G.LocalPlayer() will not look for the '_G.'

        last = t


USED_LOCAL_NAMES = []


def new_local_name(i):
    # if variable_obfuscation_type == ...
    #     return INVISIBLE_CHAR * (i + 10)
    # else

    i = len(USED_LOCAL_NAMES) + 2

    left = random.randint(0, 1)
    right = 1 - left

    name = left * INVISIBLE_CHAR * random.randint(1, i) + \
        random.choice(tokenizer.BUILTIN_WORDS) + \
        right * INVISIBLE_CHAR * random.randint(1, i)

    # If the name already exists pick a new one
    if name in USED_LOCAL_NAMES:
        return new_local_name(i)

    USED_LOCAL_NAMES.append(name)

    return name


# This might need to be moved to tokenizer
def is_var(t):
    return INVISIBLE_CHAR not in t and tokenizer.is_word(t) and not t[:2] == "__" and not t[-2:] == "__"


def is_not_table_member(tokens, index):
    """
    Tries to guess if the token at the index is local
    """

    pre = tokens[index - 1]

    return pre != "."


def index(tokens, item, start_index=0):
    """
    Returns the index of a token in a list, or -1
    """
    try:
        i = tokens.index(item, start_index)
        return i
    except:
        return -1
