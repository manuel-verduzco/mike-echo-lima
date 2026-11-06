"""Names and addresses for the counters (shared by the game, the stats page and update_stats.py).

All counts live on the free public counter service Abacus (https://jasoncameron.dev/abacus/):
    - one counter for all spins worldwide:      key "spins"
    - one counter per sentence:                 key "sentence-1" ... "sentence-106"
Spins made anywhere except the real website (for example on your own computer while testing)
use a separate "-dev" namespace, so they never change the real numbers.
"""

COUNTER_BASE = "https://abacus.jasoncameron.dev"
LIVE_HOST = "manuel-verduzco.github.io"  # the address of the real website
LIVE_NAMESPACE = "manuel-verduzco-mike-echo-lima"
TOTAL_KEY = "spins"


def namespace_for(hostname):
    """The counter namespace to use when the page is served from `hostname`."""
    return LIVE_NAMESPACE if hostname == LIVE_HOST else LIVE_NAMESPACE + "-dev"


def sentence_key(number):
    """Counter name for one sentence (the service needs names of 3+ characters)."""
    return "sentence-%d" % number


# The stats snapshot (see update_stats.py). The scheduled Action saves it on its own branch, "stats-data",
# and the stats page reads it from there (GitHub's raw file address allows web pages to read it).
# The copy of stats.json on the main branch is only a starting point for local testing and a fallback.
LIVE_STATS_URL = "https://raw.githubusercontent.com/manuel-verduzco/mike-echo-lima/stats-data/stats.json"
LOCAL_STATS_URL = "stats.json"


def stats_urls(is_live):
    """Addresses to try, in order, for the stats snapshot."""
    return [LIVE_STATS_URL, LOCAL_STATS_URL] if is_live else [LOCAL_STATS_URL]
