"""Create stats_baseline.json: made-up stand-in numbers for the spins from before sentence counters existed.

Before the stats page launched, spins were only counted as one worldwide total, so nobody knows which
sentences they landed on. This invents a believable spread: the earlier spins are shared out across the
sentences at random (every sentence is equally likely to land, so an even random spread is what real data
looks like), except for any sentence you pin to a chosen number with --pin. The result is saved.
update_stats.py then adds these numbers on top of the real per-sentence counters, so the total on the
stats page matches the worldwide counter from day one.

These numbers are INVENTED, not real. The stats page says so, in words, whenever a baseline is in use.

Run it once, just before the stats go live (it reads the real worldwide total at that moment):

    python make_baseline.py --pin 1=12

It refuses to overwrite an existing baseline, because changing it later would rewrite history.
Options: --pin NUMBER=COUNT (fix one sentence's number by hand, can be repeated, e.g. --pin 1=12),
--dev (use the testing counters), --total N (use this number instead of reading the counter),
--seed N (change the random spread), --out FILE, --force (replace an existing file).

The numbers it prints (average, lowest, highest, how spread out) let you judge whether they look believable.
"""

import argparse
import json
import random
import sys
from pathlib import Path

from counters import LIVE_NAMESPACE, TOTAL_KEY
from phrases import PHRASES
from update_stats import fetch_value, now_iso

HERE = Path(__file__).resolve().parent
NOTE = ("Made-up stand-in numbers for spins made before sentence counters existed. They were filled in "
        "roughly evenly across the sentences and are NOT real data.")


def make_counts(total, numbers, seed, pins=None):
    """Share `total` spins out across `numbers` at random, evenly in the long run.

    `pins` ({number: count}) fixes some sentences at an exact count; the rest share out what is left.
    """
    pins = {str(k): int(v) for k, v in (pins or {}).items()}
    for key in pins:
        if int(key) not in numbers:
            raise ValueError("sentence %s does not exist" % key)
    left = total - sum(pins.values())
    free = [n for n in numbers if str(n) not in pins]
    if left < 0 or (left > 0 and not free):
        raise ValueError("the pinned numbers add up to more than the %d earlier spins" % total)
    rng = random.Random(seed)
    counts = {str(n): 0 for n in numbers}
    counts.update(pins)
    for _ in range(left):
        counts[str(rng.choice(free))] += 1
    return counts


def describe(counts, pins=None):
    """A few numbers to judge whether a spread looks believable."""
    values = list(counts.values())
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    ranked = sorted(counts, key=lambda k: (-counts[k], int(k)))
    return {"average": round(mean, 2), "lowest": min(values), "highest": max(values),
            "spread_ratio": round(variance / mean, 2) if mean else 0.0,  # about 1.0 is typical of real random spins
            "top5": [(int(k), counts[k]) for k in ranked[:5]],
            "ranks": {k: ranked.index(k) + 1 for k in (pins or {})}}


def build(total, numbers, seed, pins=None, now=now_iso):
    data = {"estimated": True, "note": NOTE, "spins": total, "created": now(), "seed": seed,
            "counts": make_counts(total, numbers, seed, pins)}
    if pins:
        data["pinned"] = {str(k): int(v) for k, v in pins.items()}
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dev", action="store_true", help="read the testing counters instead of the real ones")
    parser.add_argument("--total", type=int, help="use this many earlier spins instead of reading the counter")
    parser.add_argument("--seed", type=int, default=2026, help="seed for the random spread (default 2026)")
    parser.add_argument("--pin", action="append", default=[], metavar="NUMBER=COUNT",
                        help="fix one sentence at an exact count, e.g. --pin 1=12 (can be repeated)")
    parser.add_argument("--out", default=str(HERE / "stats_baseline.json"))
    parser.add_argument("--force", action="store_true", help="replace an existing baseline file")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists() and not args.force:
        sys.exit("%s already exists. Changing a baseline later rewrites history, so use --force only if you mean it." % out)
    pins = {}
    for item in args.pin:
        number, _, count = item.partition("=")
        if not (number.isdigit() and count.isdigit()):
            sys.exit("--pin wants NUMBER=COUNT, for example --pin 1=12 (got %r)" % item)
        pins[number] = int(count)
    total = args.total
    if total is None:
        namespace = LIVE_NAMESPACE + ("-dev" if args.dev else "")
        total = fetch_value(namespace, TOTAL_KEY)
        print("Worldwide total right now (%s): %d" % (namespace, total))
    data = build(total, sorted(PHRASES), args.seed, pins)
    out.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print("Wrote %s: %d earlier spins shared across %d sentences." % (out, total, len(data["counts"])))
    print("How it looks: %s" % describe(data["counts"], pins))
    return 0


if __name__ == "__main__":
    sys.exit(main())
