# LuaObfuscator

This lua obfuscator was originally designed for Garry's Mod, but should work on vanilla lua.
Written for private use in January 2016. I never did anything with it so I decided to put it on GitHub.

### Requirements

* Python **3.4.3+** (_VERY IMPORTANT_)

### Optional Things

* pyperclip (`pip install pyperclip`)

### Usage

`python __main__.py [--input input.lua] [--output output.lua] [--level 1] [--dontcopy] [--debug]`

The default values are shown above.

If you don't want the code copied to your clipboard, use `--dontcopy`.

If your script is not running correctly, use `--debug` and you may find the issue.

### Levels

Passed with the `--level x` argument.

Lvl  | Info
-----|----------------------------------------------------------------------------
 0   | Original strings, should be very similar in size to input file
 1   | Creates a small file, less not as good as Lvl 2
**2**| Creates a small file, **recommended level**
3    | Invisible strings, **huge files that appear to be very small**, not recommended!


### Features

* Code is tokenized and _kind of_ understood
* Strings are stripped, ciphered and replaced
* Code rearrangement while retaining functionality
* All variables, local and global, are understood and replaced
* Renaming of variables defined in for loops
* Basic understanding of code heirarchy

### Known issues

* Garry's Mod Lua adds `//` comments, which conflicts with Lua 5.3's `floor division operator`. Code using the floor division operator should be changed to something like `math.floor(a/b)`
