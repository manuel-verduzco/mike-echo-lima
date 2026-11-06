"""Small date helpers for the browser pages.

Why this exists: Python in the browser (MicroPython) cannot hold JavaScript's millisecond clock
(about 1.8 trillion): the number silently wraps around into a wrong, even negative, value. Dates
travel as text ("2026-11-06T11:40:12Z") instead, and this turns that text into plain seconds.
"""


def iso_to_seconds(iso):
    """'2026-11-06T11:40:12Z' (or with .123 milliseconds) -> seconds since 1 Jan 1970, UTC."""
    y, m, d = int(iso[0:4]), int(iso[5:7]), int(iso[8:10])
    hh, mm, ss = int(iso[11:13]), int(iso[14:16]), int(iso[17:19])
    if m <= 2:
        y -= 1
    era = y // 400
    yoe = y - era * 400
    mp = m - 3 if m > 2 else m + 9
    doy = (153 * mp + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    days = era * 146097 + doe - 719468
    return days * 86400 + hh * 3600 + mm * 60 + ss


def ago_text(seconds):
    """How long ago, in plain words, for a gap of `seconds`."""
    minutes = int(seconds // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return "%d minute%s ago" % (minutes, "" if minutes == 1 else "s")
    hours = minutes // 60
    if hours < 48:
        return "%d hour%s ago" % (hours, "" if hours == 1 else "s")
    return "%d days ago" % (hours // 24)
