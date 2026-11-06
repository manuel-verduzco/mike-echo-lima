# Spin the Bic Bic: notes for Claude

A small game: a spinning biscuit wheel that lands on one of 106 sentences. Read [README.md](README.md) first; it explains
how everything works and how to run it. Live at https://manuel-verduzco.github.io/mike-echo-lima/ (GitHub Pages,
branch `main`, root folder). Repository: `manuel-verduzco/mike-echo-lima`.

## Everyday commands

- Run the checks: `python -m unittest` (must say OK before every push).
- Try it locally: `python -m http.server 8765 --bind 127.0.0.1`, then open `http://localhost:8765/index.html`.
  Stop the server when you are done.
- After changing any of `web.py`, `stats.py`, `database.py`, `counters.py`, `effects.py`, `phrases.py`, `phrases.json`
  or `pyscript.toml`, run `python bump_version.py` (it changes the `?v=NN` cache number in `index.html`, `stats.html` and
  `pyscript.toml`). Skipping it makes visitors load a mix of old and new files. A test fails if the numbers disagree.
- A new `.py` file that a page imports must also be listed in `pyscript.toml` (a test checks this).
- Local-only test shortcuts (they do nothing on the live site): `?force=37` lands on sentence 37, `&fx=crumbs` or
  `&fx=rain` forces an effect, `&milestone=1` shows the spin-1,000 message after the next spin.

## How the code is built (things that bite)

- The page code is Python run in the browser by PyScript on **MicroPython**, not normal Python: no `random.shuffle`,
  and JavaScript's millisecond clock (`Date.now()`) wraps into a wrong number. Pass dates as text instead. `fetch()`
  options must be built as a JavaScript object (`database.py` does this with `JSON.parse(json.dumps(...))`).
- `spin_wheel.py` is a separate desktop (tkinter) version; the tests import it, so Python needs tkinter.
- When editing files with a Python script on Windows, write with `newline="\n"` and avoid putting `\n` inside a
  string you are replacing (it becomes a real line break).

## Data: Supabase is the single source of truth

- Every counter (the worldwide total and the 106 sentence counts) lives in one Supabase project. The address and the
  **publishable** key are in `counters.py`; the tables and the one safe function `record_spin()` come from
  `supabase_setup.sql`, run once in the Supabase SQL Editor (by the user, or through the Supabase connector if it is
  connected).
- Row Level Security is on: the public key can only read the counts and call `record_spin`. **Never put a Supabase
  secret key (`sb_secret_...`) or a `service_role` key anywhere in this repository.** A test scans for them.
- Two sets of rows: `live` (used on the real site) and `dev` (used everywhere else, for example `localhost`), chosen by
  the page's address in `counters.py`. Testing never touches the real numbers. Never write to `live` while testing.
- The first 1,002 spins were only counted as a total, so their per-sentence numbers were made up (sentence 1 = 12). They
  are recorded in `stats_baseline.json` and described in the README.

## How to work with this project's owner

- Explain in plain, non-technical words and say what you could not verify. Test changes in the browser, including a
  phone-sized screen (the wheel page must fit one phone screen without scrolling).
- **Ask before pushing** to GitHub, unless they have just told you to push.
- Check deploys and background jobs **once** with short timeouts and report. Never wait in long polling or sleep loops;
  tell them what is pending and the manual step instead.
- GitHub Pages publishes can get stuck or time out. The fix is the run page's **Cancel workflow** then **Re-run all
  jobs**, or push a new commit.
- Do not publish or change anything outside this project without asking.

## Current state (update this when it changes; last updated 2026-11-06)

- The "📊 Stats" link on the wheel page is **hidden on purpose** (`hidden` on `#statslink` in `index.html`). Remove that
  attribute to show it again. `stats.html` still works if you type the address.
- The move to Supabase was pushed on 2026-11-06, but its first GitHub Pages publish timed out. Until a publish succeeds,
  the live site still runs the older version that counts on the old counter service (Abacus, namespace
  `manuel-verduzco-mike-echo-lima`). When the new version is live, compare that old counter against the numbers loaded
  into Supabase (total 1,010 at 15:50 UTC) and add any spins that landed on the old service in between.
