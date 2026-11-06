"""The stats page (runs as Python via PyScript, like the game).

It loads stats.json - a snapshot of every sentence's counter, saved into the repository (on its own
"stats-data" branch) about every 10 minutes by update_stats.py - and lists all the sentences with how
often each has landed.
"""

import json

from counters import LIVE_HOST, stats_urls
from phrases import PHRASES
from pyscript import document, window
from pyscript.ffi import create_proxy
from timeutil import ago_text, iso_to_seconds

list_el = document.getElementById("list")
empty_el = document.getElementById("empty")
updated_el = document.getElementById("updated")
summary_el = document.getElementById("summary")
search_el = document.getElementById("search")
btn_count = document.getElementById("sort-count")
btn_number = document.getElementById("sort-number")

counts = {}  # sentence number -> how many times it has landed
state = {"sort": "count", "query": ""}


def grouped(value):
    """1234 -> '1,234'"""
    digits = str(int(value))
    out = ""
    while len(digits) > 3:
        out = "," + digits[-3:] + out
        digits = digits[:-3]
    return digits + out


def now_iso():
    """The current time as text like '2026-11-06T11:40:12.345Z' (see timeutil.py for why text)."""
    return str(window.Date.new().toISOString())


def ago(iso):
    """How long ago a snapshot was saved, in plain words."""
    try:
        gap = iso_to_seconds(now_iso()) - iso_to_seconds(iso)
    except Exception:
        return ""
    return ago_text(max(0, gap))


def short(text, limit=34):
    return text if len(text) <= limit else text[: limit - 1] + "…"


def show_baseline_note(data):
    """A footnote about where the numbers come from. Nothing is shown when stand-in numbers are in use."""
    note = document.getElementById("baseline-note")
    if int(data.get("baseline", 0)) > 0:
        note.hidden = True
        return
    note.innerText = ("Only spins since the stats page launched are counted per sentence (earlier spins were only "
                      "counted as a total), so these numbers start lower than the worldwide counter on the wheel page.")
    note.className = "note"
    note.hidden = False


def show_summary(data):
    counted = int(data.get("counted", 0))
    total = int(data.get("total", 0))
    numbers = sorted(PHRASES)
    best = None
    for n in numbers:
        if counts.get(n, 0) > 0 and (best is None or counts[n] > counts[best]):
            best = n
    document.getElementById("s-counted").innerText = grouped(counted)
    baseline = int(data.get("baseline", 0))
    if total > counted:
        sub = "of %s worldwide" % grouped(total)
    elif baseline:
        sub = "%s of them estimated" % grouped(baseline)
    else:
        sub = "since the stats began"
    document.getElementById("s-counted-sub").innerText = sub
    if best is None:
        document.getElementById("s-top").innerText = "-"
        document.getElementById("s-top-sub").innerText = "no spins counted yet"
    else:
        document.getElementById("s-top").innerText = "#%d" % best
        document.getElementById("s-top-sub").innerText = "%s (%s times)" % (short(PHRASES[best]), grouped(counts[best]))
    summary_el.hidden = False


def render():
    numbers = sorted(PHRASES)
    if state["sort"] == "count":
        numbers.sort(key=lambda n: (-counts.get(n, 0), n))
    query = state["query"].strip().lower()
    if query:
        numbers = [n for n in numbers if query in PHRASES[n].lower() or query in str(n)]
    top = 1
    for value in counts.values():
        if value > top:
            top = value
    list_el.innerHTML = ""
    for n in numbers:
        c = counts.get(n, 0)
        row = document.createElement("li")
        row.className = "row zero" if c == 0 else "row"
        row.style.setProperty("--w", "%d%%" % int(100 * c / top))
        badge = document.createElement("span")
        badge.className = "num"
        badge.innerText = "#%d" % n
        text = document.createElement("span")
        text.className = "txt"
        text.innerText = PHRASES[n]
        number = document.createElement("span")
        number.className = "cnt"
        number.innerText = grouped(c)
        row.appendChild(badge)
        row.appendChild(text)
        row.appendChild(number)
        list_el.appendChild(row)
    empty_el.hidden = len(numbers) > 0


def set_sort(mode):
    state["sort"] = mode
    btn_count.classList.toggle("on", mode == "count")
    btn_number.classList.toggle("on", mode == "number")
    render()


def on_search(event):
    state["query"] = str(search_el.value)
    render()


def load_stats(data):
    for key in data.get("counts", {}):
        counts[int(key)] = int(data["counts"][key])
    when = data.get("updated")
    if when:
        updated_el.innerText = "Snapshot saved %s" % ago(when)
        try:
            updated_el.title = str(window.Date.new(when).toLocaleString())
        except Exception:
            pass
    else:
        updated_el.innerText = "No snapshot saved yet. The first one appears within about 10 minutes of the next spins."
    show_summary(data)
    show_baseline_note(data)
    render()


def fail(message):
    updated_el.innerText = message
    render()  # still show every sentence, with no counts


NOT_AVAILABLE = "The stats are not available right now. Please try again later."


def fetch_stats():
    # On the real site, read the snapshot from the stats-data branch and fall back to the copy that ships
    # with the page. On your own computer only the local copy is used, unless the address ends in
    # ?statsfrom=live (a testing switch that works only away from the real site).
    live = window.location.hostname == LIVE_HOST or "statsfrom=live" in str(window.location.search)
    urls = stats_urls(live)
    stamp = now_iso()[:16]  # changes every minute, so a fresh snapshot is picked up (text, not a number)

    def try_url(i):
        if i >= len(urls):
            fail(NOT_AVAILABLE)
            return

        def on_response(resp):
            if resp.ok:
                return resp.text()
            return None

        def on_text(text):
            data = None
            if text:
                try:
                    data = json.loads(text)
                except Exception:
                    data = None
            if data is None:
                try_url(i + 1)  # missing or unreadable: try the next address
            else:
                load_stats(data)

        try:
            window.fetch("%s?t=%s" % (urls[i], stamp)).then(create_proxy(on_response)).then(create_proxy(on_text)).catch(
                create_proxy(lambda e: try_url(i + 1)))
        except Exception:
            try_url(i + 1)

    try_url(0)


btn_count.addEventListener("click", create_proxy(lambda e: set_sort("count")))
btn_number.addEventListener("click", create_proxy(lambda e: set_sort("number")))
search_el.addEventListener("input", create_proxy(on_search))
fetch_stats()
