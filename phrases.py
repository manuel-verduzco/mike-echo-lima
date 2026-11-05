"""Loads the sayings from phrases.json (edit that file to make the game your own!).

phrases.json maps a number to its saying, e.g. {"1": "Good evening", "2": "..."}.
The wheel shows SLICES of those numbers at a time, dealt in a random order, so
every spin the numbers are in different places.
"""

import json
import random

SLICES = 12  # how many numbers are on the wheel at once (2-24 looks best)


def _load():
    try:
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phrases.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # e.g. in the browser, where the file sits in the working folder
        with open("phrases.json") as f:
            return json.load(f)


PHRASES = {int(k): v for k, v in _load().items()}


def deal(slices=SLICES):
    """Return `slices` distinct numbers from PHRASES in a random order."""
    pool = sorted(PHRASES)
    slices = min(slices, len(pool))
    for i in range(slices):  # partial Fisher-Yates shuffle (works in MicroPython too)
        j = random.randint(i, len(pool) - 1)
        pool[i], pool[j] = pool[j], pool[i]
    return pool[:slices]
