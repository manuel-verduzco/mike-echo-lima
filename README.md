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

## Counters and stats (Supabase)

Every number the game remembers lives in **one Supabase database**, the single source of truth: the
worldwide spin total ("🍪 1,234 spins worldwide" under the wheel) and one count for each of the 106 sentences
(the stats page). GitHub Pages cannot store anything itself, so it needs a small database next to it.

How it works:

1. When a spin finishes, the page calls one database function, `record_spin`, which adds 1 to the worldwide
   total and 1 to the sentence that landed, in one step, and hands back the new total. Only the sentence
   number is sent, nothing about the player. A spin that is left halfway (tab closed) is never counted.
   Spins forced with the test shortcuts are not counted.
2. The new total is what the page shows, and it is how the spin-1,000 message knows who made the 1,000th spin:
   exactly one player gets that number back.
3. The **📊 Stats** page (`stats.html`) reads the 106 counts straight from the database and refreshes itself
   every 30 seconds while it is open. There is no saved copy, no schedule and no GitHub Action to keep running.
4. If the database cannot be reached the game still works; the counter just stays hidden.

**Setting the database up** (already done for this project; this is for rebuilding it): create a free project at
[supabase.com](https://supabase.com), open its **SQL Editor** and run [`supabase_setup.sql`](supabase_setup.sql). Then put
the project address and the **publishable** key in [`counters.py`](counters.py).

**Safety.** The publishable key is *meant* to be in public web pages. Row Level Security is on for both tables,
so that key can only (a) read the counts and (b) call `record_spin`. It cannot edit, reset or delete a number.
The `secret` / `service_role` keys must **never** go in this repository (a test fails if one ever does).
Someone who knows the address could still call `record_spin` over and over, so treat the numbers as fun, not exact.

**Two sets of numbers.** Spins made anywhere except the real website (for example `localhost` while you are
testing) are counted into separate `dev` rows, so testing never changes the real numbers. To start the `dev`
numbers again, run `update public.spin_totals set total = 0 where namespace = 'dev'; update public.sentence_counts
set spins = 0 where namespace = 'dev';` in the SQL Editor.

**Free plan note.** Supabase's free plan pauses a project after about a week with no activity at all. Players
spinning keep it awake. If it ever pauses, open the project in the dashboard and press **Restore**; nothing is
lost. Under Settings, then API Keys, you can make a new publishable key if you ever want to change it.

**The first 1,002 spins.** The sentence counters were added after the game was already being played, so those
earlier spins were only ever counted as a total. The database was loaded with made-up numbers for them, spread
roughly evenly over the sentences (with sentence 1 set to 12), so that the stats add up to the worldwide
total. They are recorded in [`stats_baseline.json`](stats_baseline.json), and the "Spins counted" card on the
stats page says how many of its spins are estimated. Every spin after that is counted for real.

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
- `stats.html` and `stats.py`: the stats page, which reads the live counts from the database.
- `counters.py` and `database.py`: where the database is and how the pages talk to it.
- `supabase_setup.sql`: the tables and the one safe "add a spin" function, to run once in Supabase.
- `stats_baseline.json`: the made-up starting numbers for the earliest spins (a record of what was loaded).
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
- **The spin counter shows nothing, or the stats page says "not available".** The database may be paused (the free
  plan pauses a project after about a week of no use) or unreachable. Open the project in the Supabase dashboard
  and press **Restore** if it says paused. The game keeps working without the counter.
- **Counts stopped after changing sentences.** The database has rows for sentences 1 to 106. If you add more
  sentences, add rows for them too (raise the `106` in the "starting rows" part of `supabase_setup.sql` and run it
  again); a test warns you.

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
