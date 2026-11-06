# Spin the Bic Bic

### ▶ [Play it online: https://manuel-verduzco.github.io/mike-echo-lima/](https://manuel-verduzco.github.io/mike-echo-lima/)

A tiny, fun Python game: spin the biscuit and it lands on a random number with a
saying attached to it. It works in the browser, and there is also a desktop version
built with only the Python standard library (tkinter).

Want to keep working on it from another computer? Jump to
[Continue working on this from another device](#continue-working-on-this-from-another-device).

## Play online

Open **[https://manuel-verduzco.github.io/mike-echo-lima/](https://manuel-verduzco.github.io/mike-echo-lima/)** in any browser, on a computer or a phone. It runs
the Python in the page itself using [PyScript](https://pyscript.net), so there is nothing to install.

In the browser version, **press and hold** the wheel (or the button) to charge the
force bar, then release to spin. A longer hold means a harder, longer spin; a quick
tap gives a gentle one. The result is random either way.

Tap the 🔄 button next to the wheel to change the biscuit (Digestive, Choc Digestive,
Choc Chip Cookie); your choice is remembered.

## Special effects

- **Number 1 is special.** If the wheel lands on number 1 ("GOOD EVENING"), the sentence
  flashes across the screen in big gold letters, the result card turns shiny gold, and it rains
  cookies.
- **Random surprises.** About 1 spin in 4 gets one random effect: a burst of crumbs and chocolate
  chips from the pointer, or a shower of cookies.
- **Spin number 1,000.** The worldwide counter tells each player the new total as their spin is
  counted, so exactly one person's spin comes back as 1,000. Only they see a gold full-screen
  message (with the time, so a screenshot works as proof) and a downpour of cookies. If that
  person's connection drops at that exact moment, nobody sees it, and someone could skip past 1,000
  by calling the public counter directly, so treat it as a bit of fun.

Which number is special, how often surprises happen, which effects exist and the words of the
spin-1,000 message are set in [`effects.py`](effects.py). People who ask their device for reduced motion get the banner but
no flying particles.

## Sounds for sentences

Record a voice note (or use any mp3) and the game can play it when a sentence comes up. Drop the
file in the [`sounds`](sounds) folder and add a line to [`sounds.json`](sounds.json), for example
`{"37": "apple-in-bowl.mp3"}`. A speaker button on the wheel lets people mute it. The
folder's [README](sounds/README.md) has the details and tips. Sentences with no entry stay silent.

## Global spin counter

The online version shows how many spins everyone has done in total ("🍪 1,234 spins worldwide").
GitHub Pages cannot store data, so the total is kept on a free public counter service,
[Abacus](https://jasoncameron.dev/abacus/). When a spin finishes, the page asks it to add 1 and
shows the new total. Only the counter's name is sent, nothing about the player. If the service is
unreachable, the game still works and the counter is simply hidden. Spins made on `localhost` use
a separate "-dev" counter, so testing does not change the real number.

Because it is a public counter, anyone who knows its address could push the number up. That is fine
for a fun game, but do not treat the number as exact.

## Stats page: how often each sentence lands

The **📊 Stats** link next to the worldwide counter opens [`stats.html`](stats.html): all 106 sentences
with how many times each has landed, most landed first, with a search box and a "By number" switch.

How it works:

1. When a sentence lands, the game adds 1 to that sentence's own counter on the same counter service
   (names like `sentence-37`). Spins forced with the test shortcuts are not counted.
2. A browser cannot write into this repository (that would need a secret password in the public code),
   so a **scheduled GitHub Action** does it instead. About every 5 minutes (the shortest gap GitHub
   allows) it runs [`update_stats.py`](update_stats.py), which reads all the counters and saves them into
   `stats.json`. It only saves when something changed.
3. That file is saved on its **own branch, `stats-data`**, not on `main`. A save on `main` would make
   GitHub rebuild the website each time (Pages only allows about 10 rebuilds an hour) and would bury your
   real changes in "Update stats" commits. On its own branch it costs nothing, and the branch's history is
   a neat record of how the numbers grew. You can browse it on GitHub with the branch menu.
4. The stats page reads the file straight from that branch, so it opens instantly and is usually less than
   about 10 minutes behind the live game (up to 5 minutes for the next save, plus GitHub's own 5 minute
   cache).
5. The spins from before the per-sentence counters existed were only counted as a total, so nobody knows which
   sentences they landed on. See "Stand-in numbers for the earlier spins" below.

The Action is [`.github/workflows/update-stats.yml`](.github/workflows/update-stats.yml) and the saving
steps are in [`.github/scripts/save_stats.sh`](.github/scripts/save_stats.sh). To run it
right now instead of waiting: on GitHub open the **Actions** tab, choose **Update stats**, then
**Run workflow**. You can also run the same thing yourself on any computer:

```bash
python update_stats.py          # the real counters, rewrites stats.json in this folder
python update_stats.py --dev    # the testing counters (what a local copy of the game counts into)
```

It takes about a minute and a half because the counter service only allows 30 requests per 10 seconds.
If you test the game on your own computer, its spins go to the separate "-dev" counters. Run
`python update_stats.py --dev`, open `http://localhost:8765/stats.html`, and you will see your test spins.
Do not commit that test version of `stats.json`: run `git checkout stats.json` to put the starting
one back. (The copy of `stats.json` on `main` is only a starting snapshot for local testing and a fallback for
the page until the first scheduled save exists; the real, current numbers live on the `stats-data` branch.) On a local copy you can also add `?statsfrom=live` to the
stats page address to make it read the real snapshot from the branch, like the live site does.

### Stand-in numbers for the earlier spins

So that the stats page adds up to the worldwide counter from day one, `make_baseline.py` makes up numbers
for the spins made *before* the sentence counters existed. It shares them out across the sentences at random
(every sentence is equally likely to land, so an even random spread looks like real data), except for any
sentence you pin to a chosen number. It saves them in `stats_baseline.json`, and `update_stats.py` adds them on
top of the real counters.

**These numbers are made up.** The stats page no longer carries a note saying so (that was a choice made
after launch), but the "Spins counted" card still reads "N of them estimated" while a baseline is in use, and this
README and `stats_baseline.json` (its `note` field) record it. If the page's note is ever wanted again, it lives
in `show_baseline_note` in [`stats.py`](stats.py).

```bash
python make_baseline.py --pin 1=12   # run ONCE, just before the stats go live (it reads the worldwide total right then)
```

`--pin 1=12` fixes sentence 1 at exactly 12 (you can pin several: `--pin 1=12 --pin 37=9`). With about 800 earlier
spins that gives an average of about 7.5 per sentence, a range of roughly 2 to 15, and sentence 1 near the top
ten, which is what real random spins would look like. The command prints how the spread looks so you can judge it.

It refuses to overwrite an existing baseline, because changing it later would rewrite history. Delete
`stats_baseline.json` (and the stand-ins disappear from the next snapshot) if you ever change your mind.

## Make it yours

Edit [`phrases.json`](phrases.json): each number maps to a saying. Add as many as
you like. The numbers are combined into 24 slices (like "1-5", "6-10"), shuffled
into new positions every spin. One number is picked at random from ALL of them, so
every sentence is equally likely, and the wheel stops on the slice that holds it.
Change `GROUPS` in [`phrases.py`](phrases.py) for more or fewer slices.

---

## Continue working on this from another device

Everything lives in this GitHub repository: the code, the sentences and the sound files. Nothing is
stored only on one computer, so any machine can pick the project up where you left off. (The only
things that are not in the repository are each visitor's own choices, such as their favourite
biscuit and the mute button, which their browser remembers.)

### What you need

- **Git**: [git-scm.com](https://git-scm.com/downloads).
- **Python 3.8 or newer**: [python.org](https://www.python.org/downloads/). The online game itself
  runs in the browser and needs no Python on your side. You only need it to run the tests, the
  desktop version and the small local test server. The tests also load the desktop version, so
  Python needs **tkinter**, which comes with the Windows and Mac installers (on some Linux systems,
  install it with `sudo apt install python3-tk`).
- **A GitHub account with access to this repository** (`manuel-verduzco/mike-echo-lima`).
- Optional: a code editor such as VS Code, or [Claude Code](https://claude.com/claude-code), where you
  can open the folder and describe the change you want in plain words.

### 1. Get the code

```bash
git clone https://github.com/manuel-verduzco/mike-echo-lima.git
cd mike-echo-lima
```

Already cloned on that device? Run `git pull` first, so you start from the latest version.

The first time you push from a new device, GitHub asks you to sign in (a browser window opens), or
you can run `gh auth login` if you use the GitHub command line tool. Git also needs to know who you
are for the history, once per device:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 2. Check that everything works

```bash
python -m unittest
```

It should say `OK`. (On some computers the command is `python3`, and on Windows `py` also works.)

### 3. Try the game on your own computer

Start a tiny local web server inside the project folder:

```bash
python -m http.server 8765
```

Then open **http://localhost:8765/index.html**. Stop the server with `Ctrl+C` when you are done.

- **On a phone:** if your phone is on the same Wi-Fi, open `http://<your computer's address>:8765/index.html`
  (find the address with `ipconfig` on Windows or `ifconfig` / `ip a` on Mac and Linux). Some work or
  guest networks block this. If so, test on the live site after publishing instead.
- **Test shortcuts (local only, switched off on the live site):** add `?force=37` to the address
  and the wheel always lands on sentence 37. Add `&fx=crumbs` or `&fx=rain` to force a special effect, or `&milestone=1` to see the
  spin-1,000 message after your next spin.
- Spins made on your own computer are added to a separate "-dev" counter, so they never change the real number.
- The desktop version needs no server: `python spin_wheel.py`.

### 4. Make a change and publish it

1. Edit what you want (see the table below).
2. **If you changed any of the game files** (`web.py`, `effects.py`, `phrases.py`, `phrases.json` or
   `pyscript.toml`), run the version bump. If in doubt, run it, it is harmless:

   ```bash
   python bump_version.py
   ```

   Browsers keep website files for about 10 minutes. This changes the `?v=NN` number the page asks
   for, so everybody gets the fresh files at once instead of a mix of old and new ones.
3. Run the tests, then save and upload your work:

   ```bash
   python -m unittest
   git add -A
   git commit -m "A short note about what you changed"
   git push
   ```

4. The website updates itself about a minute after the push (GitHub Pages publishes the `main`
   branch). Refresh the live page with `Ctrl+Shift+R` to see it.

### Where to change things

| I want to change... | Where | Bump the version? |
|---|---|---|
| The sentences (add, edit, remove) | [`phrases.json`](phrases.json) | yes |
| What the stats page shows or how it looks | [`stats.html`](stats.html) (looks), [`stats.py`](stats.py) (what it does) | yes |
| Add a voice note to a sentence | put the file in [`sounds/`](sounds), add a line to [`sounds.json`](sounds.json) | no |
| The special number, how often surprises happen, the spin-1,000 message | [`effects.py`](effects.py) | yes |
| How many slices the wheel has | `GROUPS` in [`phrases.py`](phrases.py) | yes |
| Biscuit looks, wheel drawing, spin behaviour, effects, sounds | [`web.py`](web.py) | yes |
| Page layout, colours, text, phone layout | [`index.html`](index.html) | no |

### What is in the folder

- `index.html`: the web page (layout and styles) that loads everything else.
- `web.py`: the browser game in Python (drawing, spinning, effects, sounds, counter). It runs through
  PyScript on MicroPython, which has a smaller standard library than normal Python (for example there
  is no `random.shuffle`). If something works in a normal Python test but breaks in the browser, that
  is the likely reason, so always check changes in the browser too.
- `effects.py`: which effects fire and which number is special. Plain logic, shared and tested.
- `phrases.json` and `phrases.py`: the sentences, and the code that loads them and deals the wheel.
- `pyscript.toml`: the list of Python and JSON files the browser has to download. If you ever add a new
  `.py` file that `web.py` imports, list it here too (a test reminds you if you forget).
- `stats.html` and `stats.py`: the stats page, which loads `stats.json`.
- `stats.json`: the saved snapshot of every sentence's counter. Rewritten by the Action, not by hand.
- `make_baseline.py` and `stats_baseline.json`: the stand-in numbers for the earliest spins (see above).
- `timeutil.py`: tiny date helpers (the browser's Python cannot hold JavaScript's millisecond clock).
- `update_stats.py`, `.github/workflows/update-stats.yml` and `.github/scripts/save_stats.sh`: the script, the
  schedule and the saving steps that refresh it.
- `counters.py`: the counter names and addresses shared by the game, the stats page and the script.
- `sounds.json` and `sounds/`: the optional voice notes.
- `favicon.*` and `apple-touch-icon.png`: the cookie icon.
- `spin_wheel.py`: the desktop version (tkinter).
- `bump_version.py`: the cache version helper described above.
- `test_wheel.py`: the automatic checks.

### If something goes wrong

- **The page shows a red error or "can't import name ..." after you publish.** Old and new files got
  mixed. Run `python bump_version.py`, commit and push again, then hard refresh. (The test suite fails
  with the same advice if the version numbers do not match.)
- **The live page still looks old.** Wait a minute, then hard refresh with `Ctrl+Shift+R`, or open it
  in a private window.
- **The update never appears.** On GitHub, open the **Actions** tab. If the latest "pages build and
  deployment" run is stuck for several minutes, cancel it and choose **Re-run all jobs**.
- **Starting from a brand new repository.** In the repository on GitHub, go to Settings, then Pages,
  choose **Deploy from a branch**, branch `main`, folder `/ (root)`, and save.
- **The stats page is not updating.** The first save only happens after the first run of the Action. On GitHub open the **Actions** tab and look at the latest
  **Update stats** run. A red cross means it failed (open it to read why), and you can press **Run
  workflow** to try again. If nothing ever runs, check that Actions are switched on for the repository.
- **Scheduled runs stop after a quiet spell.** GitHub switches off scheduled workflows in a public repository
  that has seen no activity for 60 days. If the stats stop updating, open the **Actions** tab, choose **Update
  stats** and press **Enable workflow**.
- **GitHub refuses to let you push `.github/workflows/...`.** Pushing a workflow file needs the `workflow`
  permission on your sign-in. Run `gh auth refresh -s workflow` (or sign in again and tick the workflow
  permission), then push again.
- **The spin counter shows nothing.** The free counter service may be down. The game works without it.

---

## Run the desktop version

```bash
python spin_wheel.py
```

Requires Python 3.8+ (tkinter ships with the standard Windows/macOS installers;
on some Linux distros install `python3-tk`).

## Tests

```bash
python -m unittest
```

## License

MIT
