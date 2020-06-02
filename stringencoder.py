import obfuscator
import random
import math
from string import ascii_letters, digits


class Encoder:
    def __init__(self):
        self.level = 0

    def encode_all(self, strings, xor):
        for k in strings.keys():
            strings[k] = self.encode(strings[k], xor)
        return strings

    def encode(self, string, xor):
        """
        Encode the string in such a way that
        each character is xor'd and backslashes
        are escaped properly
        """

        if len(string) == 0:
            return string

        out = []
        for c in string:
            out.append(self.encode_char(c, xor))
        return ''.join(out)

    def encode_char(self, c, xor):
        return c

    def get_decrypt_code(self, xor):
        """
        No need to decrypt plaintext
        """

        return _read_decrypt_file(self.level, xor)

    def get_str_start(self):
        return "[["

    def get_str_end(self):
        return "]]"


class Level1Encoder(Encoder):
    """
        Encode the string in such a way that
        each character is xor'd and non-letters
        are backslash escaped
    """

    def __init__(self):
        self.level = 1

    def encode_char(self, c, xor):
        c = chr(ord(c) ^ xor)

        if c not in ascii_letters:
            c = "\\" + str(ord(c))

        return c

    def get_str_start(self):
        return '"'

    def get_str_end(self):
        return '"'


class Level2Encoder(Encoder):
    """
        Encode the string in such a way that
        each character is xor'd and then a hex
        value is appended to the string
        (2 characters per input character).
    """

    def __init__(self):
        self.level = 2

    def encode_char(self, c, xor):
        x = ord(c) ^ xor
        return "{:02x}".format(x)

    def get_str_start(self):
        return "'"

    def get_str_end(self):
        return "'"


class Level3Encoder(Encoder):
    """
        Encode the string in such a way that
        each character is xor'd and then
        an invisible character (3 bytes long)
        is repeated as much as possible.
        Up to 2 additional ascii characters will be added,
        and then each character is closed with '|'.
    """

    def __init__(self):
        self.level = 3

    def encode_char(self, c, xor):
        total = ord(c) ^ xor

        # number of regular characters
        regular = total % 3

        # number of invis characters (lua counts 1 invis as 3)
        invis = math.floor(total / 3)

        regchars = ''.join(random.choice(ascii_letters + digits)
                           for _ in range(regular))

        return obfuscator.INVISIBLE_CHAR * invis + regchars + "|"


def get_by_level(level):
    if level == 1:
        return Level1Encoder()
    elif level == 2:
        return Level2Encoder()
    elif level == 3:
        return Level3Encoder()
    else:
        print("Warning!!! Not using an encoder!")
        return Encoder()


def _read_decrypt_file(level, xor):
    with open("__decrypt_" + str(level) + ".lua", "rb") as f:
        return f.read().decode("utf-8").replace("__XOR__", str(xor))
