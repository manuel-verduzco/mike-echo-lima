"""The stats page (runs as Python via PyScript, like the game).

It reads the live counts straight from the Supabase database (the single source of truth, see
counters.py and supabase_setup.sql) and lists all the sentences with how often each has landed. While
the page is open it refreshes itself every 30 seconds.
"""

from counters import counts_url, db_namespace, total_url
from database import db_call
from phrases import PHRASES
from pyscript import document, window
from pyscript.ffi import create_proxy

list_el = document.getElementById("list")
empty_el = document.getElementById("empty")
updated_el = document.getElementById("updated")
summary_el = document.getElementById("summary")
search_el = document.getElementById("search")
btn_count = document.getElementById("sort-count")
btn_number = document.getElementById("sort-number")

NS = db_namespace(window.location.hostname)  # 'live' on the real site, 'dev' on your own computer
REFRESH_MS = 30000
NOT_AVAILABLE = "The stats are not available right now. Please try again later."

counts = {}  # sentence number -> how many times it has landed
state = {"sort": "count", "query": "", "loaded": False}


def grouped(value):
    """1234 -> '1,234'"""
    digits = str(int(value))
    out = ""
    while len(digits) > 3:
        out = "," + digits[-3:] + out
        digits = digits[:-3]
    return digits + out


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
    state["loaded"] = True
    updated_el.innerText = "Live numbers, updated at %s" % str(window.Date.new().toLocaleTimeString())
    show_summary(data)
    show_baseline_note(data)
    render()


def fetch_failed():
    if state["loaded"]:
        return  # keep showing the last numbers; the next refresh tries again
    updated_el.innerText = NOT_AVAILABLE
    render()  # still show every sentence, with no counts


def refresh():
    """Read the counts, then the totals, and show them."""

    def on_counts(rows):
        by_number = {}
        for row in rows:
            by_number[str(row["number"])] = int(row["spins"])

        def on_total(total_rows):
            first = total_rows[0] if total_rows else {}
            load_stats({"counts": by_number, "total": int(first.get("total", 0)),
                        "baseline": int(first.get("baseline", 0)), "counted": sum(by_number.values())})

        db_call(total_url(NS), "GET", None, on_total, fetch_failed)

    db_call(counts_url(NS), "GET", None, on_counts, fetch_failed)


def refresh_if_visible():
    if not document.hidden:
        refresh()


btn_count.addEventListener("click", create_proxy(lambda e: set_sort("count")))
btn_number.addEventListener("click", create_proxy(lambda e: set_sort("number")))
search_el.addEventListener("input", create_proxy(on_search))
refresh()
window.setInterval(create_proxy(refresh_if_visible), REFRESH_MS)
