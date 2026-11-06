"""Where the counters live: one Supabase database, the single source of truth for every number.

    spin_totals      the worldwide spin total (and how many of those spins are stand-ins)
    sentence_counts  how many times each of the 106 sentences has landed

The tables and the one safe "add a spin" function are created by supabase_setup.sql.

The key below is Supabase's PUBLISHABLE key. It is meant to sit in public web pages. Row Level Security
makes it able to do exactly two things: read the counts, and call record_spin(), which adds 1 to the
total and 1 to one sentence. It cannot edit, reset or delete anything. NEVER put a Supabase "secret"
key (it starts sb_secret_) or a "service_role" key anywhere in this repository; a test checks for that.

Spins made anywhere except the real website (for example on your own computer while testing) count
into a separate "dev" set of rows, so testing never changes the real numbers.
"""

DB_URL = "https://nrkmcigbxryjfukuberx.supabase.co"
DB_KEY = "sb_publishable_8bOCxhbcu-fimksoK2cKvA_DTJu_vih"
LIVE_HOST = "manuel-verduzco.github.io"  # the address of the real website


def db_namespace(hostname):
    """Which set of rows to use: 'live' on the real site, 'dev' everywhere else."""
    return "live" if hostname == LIVE_HOST else "dev"


def db_headers():
    return {"apikey": DB_KEY, "Content-Type": "application/json"}


def record_spin_url():
    return DB_URL + "/rest/v1/rpc/record_spin"


def total_url(namespace):
    return "%s/rest/v1/spin_totals?select=total,baseline&namespace=eq.%s" % (DB_URL, namespace)


def counts_url(namespace):
    return "%s/rest/v1/sentence_counts?select=number,spins&namespace=eq.%s" % (DB_URL, namespace)
