"""Bump the cache-busting number (?v=NN) on the game's files.

Why: browsers keep website files for about 10 minutes. The page asks for web.py, phrases.py,
effects.py, phrases.json and pyscript.toml with a "?v=NN" on the end, and changing that number
makes everyone fetch the fresh copy straight away. If you change any of those files and forget
to bump it, people can end up with a mix of old and new files and the game shows an error.

Run this after changing any of those files, before you commit:

    python bump_version.py

(The little ?v=2 on the favicon files is separate and does not need touching.)
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ("index.html", "pyscript.toml")
# any .py / .json / .toml file followed by ?v=<number>
PATTERN = re.compile(r"(\.(?:py|json|toml)\?v=)(\d+)")


def current_version(texts):
    versions = [int(m.group(2)) for text in texts for m in PATTERN.finditer(text)]
    if not versions:
        sys.exit("Could not find any ?v=NN numbers in index.html / pyscript.toml.")
    return max(versions)


def main():
    texts = {name: (HERE / name).read_text(encoding="utf-8") for name in FILES}
    old = current_version(texts.values())
    new = old + 1
    for name, text in texts.items():
        (HERE / name).write_text(PATTERN.sub(lambda m: m.group(1) + str(new), text), encoding="utf-8")
    print("Cache version bumped: v%d -> v%d (index.html and pyscript.toml)" % (old, new))


if __name__ == "__main__":
    main()
