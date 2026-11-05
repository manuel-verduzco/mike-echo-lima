"""Loads the sayings from phrases.json (edit that file to make the game your own!).

phrases.json maps a number to its saying, e.g. {"1": "Good evening", "2": "..."}.
Every number goes on the wheel, dealt in a random order, so the numbers sit in
different places on every spin.
"""

import json
import random

SLICES = None  # numbers on the wheel at once; None means every number in phrases.json


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
    """Return `slices` distinct numbers from PHRASES in a random order
    (all of them when `slices` is None)."""
    pool = sorted(PHRASES)
    slices = len(pool) if slices is None else min(slices, len(pool))
    for i in range(slices):  # partial Fisher-Yates shuffle (works in MicroPython too)
        j = random.randint(i, len(pool) - 1)
        pool[i], pool[j] = pool[j], pool[i]
    return pool[:slices]
