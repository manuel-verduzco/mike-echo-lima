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
- `phrases.json` - the sayings; `phrases.py` loads them and deals the wheel (shared by both)

## Tests

```bash
python -m unittest
```

## License

MIT
