"""Which special effects fire on a spin (kept separate from the drawing code so it can be tested).

- Landing on JACKPOT_NUMBER always fires the special: the sentence for that number shown
  huge as a banner (GOOD EVENING), a golden result card and a downpour of cookies.
- Any other spin has an EFFECT_CHANCE of getting one random effect from EFFECTS:
    crumbs - crumbs and chocolate chips pop out of the pointer
    rain   - a shower of biscuits falls down the screen
"""

import random

JACKPOT_NUMBER = 1  # number 1 on the list, "GOOD EVENING"
EFFECT_CHANCE = 0.25  # about 1 spin in 4 gets a random effect
EFFECTS = ("crumbs", "rain")


def choose_effects(number, rand=random.random, randint=random.randint):
    """Return the list of effect names for a spin that landed on `number`."""
    if number == JACKPOT_NUMBER:
        return ["jackpot"]
    if rand() < EFFECT_CHANCE:
        return [EFFECTS[randint(0, len(EFFECTS) - 1)]]
    return []


# Secret shortcut: tap the page title SECRET_TAPS times in a row (each tap within
# SECRET_GAP_MS of the one before) to make the next spin land on JACKPOT_NUMBER.
SECRET_TAPS = 5
SECRET_GAP_MS = 1500


def register_tap(taps, now_ms):
    """Record a tap at time `now_ms`. Returns (taps_so_far, triggered)."""
    if taps and now_ms - taps[-1] > SECRET_GAP_MS:
        taps = []  # too slow: start counting again
    taps = taps + [now_ms]
    if len(taps) >= SECRET_TAPS:
        return [], True
    return taps, False
