"""Loads the sayings from phrases.json (edit that file to make the game your own!).

phrases.json maps a number to its saying, e.g. {"1": "Good evening", "2": "..."}.

A wheel with 100+ slices would be unreadable, so the numbers are combined into
GROUPS slices (for example "1-5", "6-10", ...). The game picks one number at
random from ALL of them (every number is equally likely) and the wheel stops on
the slice that contains it. The slices are shuffled into new positions each spin.
"""

import json
import random

GROUPS = 24  # slices on the wheel; use None for one slice per number


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


def make_groups(n_groups=GROUPS):
    """Split all the numbers into `n_groups` consecutive blocks of near-equal size."""
    pool = sorted(PHRASES)
    if n_groups is None or n_groups >= len(pool):
        return [[n] for n in pool]
    size, extra = divmod(len(pool), n_groups)
    groups = []
    pos = 0
    for i in range(n_groups):
        take = size + (1 if i < extra else 0)
        groups.append(pool[pos:pos + take])
        pos += take
    return groups


def shuffled(items):
    """Return a randomly ordered copy (Fisher-Yates; also works in MicroPython)."""
    items = list(items)
    for i in range(len(items) - 1, 0, -1):
        j = random.randint(0, i)
        items[i], items[j] = items[j], items[i]
    return items


def deal(n_groups=GROUPS):
    """The wheel's slices (each a list of numbers) in a fresh random order."""
    return shuffled(make_groups(n_groups))


def label(group):
    """Text shown on a slice: '7' for a single number or '1-5' for a block."""
    return str(group[0]) if len(group) == 1 else "%d-%d" % (group[0], group[-1])


def random_number():
    """A random number from ALL phrases; each one is equally likely."""
    keys = sorted(PHRASES)
    return keys[random.randint(0, len(keys) - 1)]


def group_index(groups, number):
    """Position of the slice that contains `number`."""
    for i, g in enumerate(groups):
        if number in g:
            return i
    raise ValueError(number)
