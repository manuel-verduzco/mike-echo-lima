# Spin the Bic Bic

### ▶ [Play it online: https://manuel-verduzco.github.io/mike-echo-lima/](https://manuel-verduzco.github.io/mike-echo-lima/)

A tiny, fun Python game: spin the biscuit and it lands on a random number with a
saying attached to it. It works in the browser, and there is also a desktop version
built with only the Python standard library (tkinter).

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

Which number is special, how often surprises happen and which effects exist are set at the top
of [`effects.py`](effects.py). People who ask their device for reduced motion get the banner but
no flying particles.

## Sounds for sentences

Record a voice note (or use any mp3) and the game can play it when a sentence comes up. Drop the
file in the [`sounds`](sounds) folder and add a line to [`sounds.json`](sounds.json), for example
`{"37": "apple-in-bowl.mp3"}`. A speaker button appears on the wheel so people can mute it. The
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

## Run it on your computer

```bash
python spin_wheel.py
```

Requires Python 3.8+ (tkinter ships with the standard Windows/macOS installers;
on some Linux distros install `python3-tk`).

## Make it yours

Edit [`phrases.json`](phrases.json): each number maps to a saying. Add as many as
you like. The numbers are combined into 24 slices (like "1-5", "6-10"), shuffled
into new positions every spin. One number is picked at random from ALL of them, so
every sentence is equally likely, and the wheel stops on the slice that holds it.
Change `GROUPS` in [`phrases.py`](phrases.py) for more or fewer slices.

## Files

- `spin_wheel.py` - desktop version (tkinter)
- `index.html`, `web.py`, `pyscript.toml` - browser version (PyScript)
- `sounds.json` and `sounds/` - optional voice notes for sentences
- `phrases.json` - the sayings; `phrases.py` loads them and deals the wheel (shared by both)

## Tests

```bash
python -m unittest
```

## License

MIT
