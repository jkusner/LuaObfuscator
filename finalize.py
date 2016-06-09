import re
import tokenizer

WORD_PTRN = re.compile(r"^[^" + re.escape("".join(tokenizer.SPECIAL_CHARS)) + r"]*$")


def finalize(tokens, decrypt_code):
    tokens = finalize_tokens(tokens)
    lua = render_code(tokens, decrypt_code)
    return lua


def finalize_tokens(tokens):
    """
    Render out the tokens into an obfuscated file
    """

    out = []
    skip = (';',)
    last = None
    for t in tokens:
        if last is None:
            out.append(t)
            last = t
            continue

        # Check if the last value was a word, and this value is a word
        # OR check if the last word was a return so it doesn't get called
        if (is_word(last) and is_word(t)) or last in tokenizer.RESERVED_WORDS:
            out.append(" ")

        if t in skip:
            continue

        last = t
        out.append(t)

    return out


def render_code(tokens, decrypt_code):
    return decrypt_code + " " + "".join(tokens)


def is_word(s):
    return WORD_PTRN.match(s)