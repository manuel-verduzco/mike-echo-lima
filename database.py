"""Talking to the Supabase database from the browser pages (the game and the stats page).

Python in the page cannot pass a plain dict to fetch(), so the options are built as a real JavaScript
object. Everything here fails quietly: if the database cannot be reached, the pages still work.
"""

import json

from counters import db_headers
from pyscript import window
from pyscript.ffi import create_proxy


def db_options(method, body=None):
    """fetch() options as a real JavaScript object (built from JSON so it works everywhere)."""
    options = {"method": method, "headers": db_headers()}
    if body is not None:
        options["body"] = json.dumps(body)
    return window.JSON.parse(json.dumps(options))


def db_call(url, method, body, on_json, on_fail=None):
    """Call the database, read the answer as JSON and hand it to on_json(data).

    on_fail() is called instead if anything goes wrong (no connection, an error answer, unreadable data).
    """

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
            failed()
        else:
            on_json(data)

    def failed(error=None):
        if on_fail:
            on_fail()

    try:
        window.fetch(url, db_options(method, body)).then(create_proxy(on_response)).then(
            create_proxy(on_text)).catch(create_proxy(failed))
    except Exception:
        failed()
