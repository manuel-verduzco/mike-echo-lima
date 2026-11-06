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
- GitHub Pages publishes can get stuck or time out (a publish sitting in `updating_pages` for 10 minutes fails with
  "Timeout reached"). First try the run page's **Cancel workflow**, then **Re-run all jobs**. If that re-run fails within
  seconds with "Deployment cancelled", the cancelled attempt was still being cleaned up (a re-run reuses the same publish
  ID): do not keep re-running, push a new commit instead, which gets a fresh publish ID and normally goes through.
- Do not publish or change anything outside this project without asking.

## Current state (update this when it changes; last updated 2026-11-06)

- The move to Supabase is **live** (published 16:05 UTC on 2026-11-06). The game and the stats page both read and
  write Supabase; the old counter service (Abacus) is no longer used by the code.
- The "📊 Stats" link on the wheel page is **visible** again (it was hidden for a few hours during the move; to hide it,
  put the `hidden` attribute back on `#statslink` in `index.html`).
- Still to do: a one-off catch-up. Visitors who still had the old page open may have added spins to the old Abacus
  counters (namespace `manuel-verduzco-mike-echo-lima`) after the starting numbers were loaded into Supabase
  (total 1,010 at 15:50 UTC). Read the old counters once and, if the old total is above 1,010, add the difference to the
  `live` rows in Supabase with a short SQL for the owner to run.
