# Spin the Bic Bic

A tiny, fun Python game: click the wheel, it spins, and you get a random number
with a saying attached to it.

Built with only the Python standard library (tkinter), so there is nothing to install.

## Play online

Once GitHub Pages is enabled, the game runs in any browser (the Python is executed
by [PyScript](https://pyscript.net)): `https://<your-username>.github.io/<repo-name>/`

In the browser version, **press and hold** the wheel (or the button) to charge the
force bar, then release to spin. A longer hold means a harder, longer spin; a quick
tap gives a gentle one. The result is random either way.

## Run it on your computer

```bash
python spin_wheel.py
```

Requires Python 3.8+ (tkinter ships with the standard Windows/macOS installers;
on some Linux distros install `python3-tk`).

## Make it yours

Edit [`phrases.py`](phrases.py). Each number maps to a phrase; add or remove
entries (2-24) and the wheel resizes itself.

## Files

- `spin_wheel.py` - desktop version (tkinter)
- `index.html`, `web.py`, `pyscript.toml` - browser version (PyScript)
- `phrases.py` - the sayings, shared by both

## Tests

```bash
python -m unittest
```

## License

MIT
