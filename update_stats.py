"""Save a snapshot of every sentence's counter into stats.json (the stats page reads that file).

Visitors' browsers add 1 to a sentence's counter each time it lands. A scheduled GitHub Action
(.github/workflows/update-stats.yml) runs this script about every 5 minutes: it reads all the counters
and writes them into stats.json, which is committed to the "stats-data" branch of the repository
(see .github/scripts/save_stats.sh). The stats page then loads that one small file instead of making
106 requests of its own.

If a stats_baseline.json exists (see make_baseline.py) its stand-in numbers for the spins from before
sentence counters existed are added on top of the real counters, and the snapshot says how many.

You can also run it yourself:

    python update_stats.py            # the real website's counters
    python update_stats.py --dev      # the counters used while testing on your own computer

The counter service only allows 30 requests per 10 seconds, so this paces itself (about a minute and a half
for everything). Nothing is written if anything goes wrong, so a hiccup can never zero the numbers,
and the file is left alone when nothing has changed (so the history only has useful commits).
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from counters import COUNTER_BASE, LIVE_NAMESPACE, TOTAL_KEY, sentence_key
from phrases import PHRASES

HERE = Path(__file__).resolve().parent
PAUSE = 0.4  # seconds between requests: about 25 per 10 seconds, under the service's limit of 30
USER_AGENT = "bic-bic-stats/1.0 (+https://github.com/manuel-verduzco/mike-echo-lima)"


def fetch_value(namespace, key):
    """Read one counter. Returns its number, or 0 if nobody has ever hit it (404)."""
    url = "%s/get/%s/%s" % (COUNTER_BASE, namespace, key)
    for attempt in range(6):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=20) as response:
                return int(json.load(response)["value"])
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return 0
            if error.code == 429:  # too many requests: wait as long as the service asks, then retry
                retry_ms = error.headers.get("Retry-After")
                time.sleep(min(30.0, (int(retry_ms) / 1000.0) if retry_ms and retry_ms.isdigit() else 3.0) + 0.5)
                continue
            raise
        except urllib.error.URLError:
            time.sleep(2 + attempt * 2)
    raise RuntimeError("could not read %s/%s after several tries" % (namespace, key))


def load_baseline(path):
    """The stand-in numbers for earlier spins: (counts by sentence, how many spins). Empty if no file."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {str(k): int(v) for k, v in data["counts"].items()}, int(data.get("spins", 0))
    except (OSError, ValueError, KeyError):
        return {}, 0


def collect(namespace, numbers, fetch=fetch_value, sleep=time.sleep, baseline=None):
    """Read the worldwide total and one counter per sentence number (plus any baseline numbers)."""
    base_counts, base_spins = baseline if baseline else ({}, 0)
    total = fetch(namespace, TOTAL_KEY)
    counts = {}
    for number in numbers:
        sleep(PAUSE)
        counts[str(number)] = fetch(namespace, sentence_key(number)) + base_counts.get(str(number), 0)
    return {"total": total, "counted": sum(counts.values()), "baseline": base_spins, "counts": counts}


def same_numbers(old, new):
    """True when two snapshots hold the same numbers (the 'updated' time is ignored)."""
    keys = ("total", "counted", "baseline", "counts")
    return all(old.get(k) == new.get(k) for k in keys)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def update(path, namespace, numbers, fetch=fetch_value, sleep=time.sleep, now=now_iso, baseline=None):
    """Refresh the file at `path`. Returns "unchanged" or "updated"."""
    snapshot = collect(namespace, numbers, fetch, sleep, baseline)
    try:
        old = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    if same_numbers(old, snapshot):
        return "unchanged"
    snapshot = {"updated": now(), **snapshot}
    Path(path).write_text(json.dumps(snapshot, indent=1) + "\n", encoding="utf-8")
    return "updated"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dev", action="store_true", help="read the testing counters instead of the real ones")
    parser.add_argument("--out", default=str(HERE / "stats.json"), help="file to write (default: stats.json)")
    parser.add_argument("--baseline", default=str(HERE / "stats_baseline.json"),
                        help="stand-in numbers for earlier spins (default: stats_baseline.json, if it exists)")
    args = parser.parse_args()
    namespace = LIVE_NAMESPACE + ("-dev" if args.dev else "")
    print("Reading %d sentence counters from %s ..." % (len(PHRASES), namespace))
    baseline = load_baseline(args.baseline)
    if baseline[1]:
        print("Adding %d stand-in earlier spins from %s" % (baseline[1], args.baseline))
    result = update(args.out, namespace, sorted(PHRASES), baseline=baseline)
    print("stats.json", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
