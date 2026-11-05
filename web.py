"""Browser version of Spin the Wheel (runs as Python via PyScript).

Uses the same phrases.py as the desktop version.
"""

import json
import math
import random

from effects import JACKPOT_NUMBER, choose_effects
from phrases import PHRASES, deal, group_index, label, random_number
from pyscript import document, window
from pyscript.ffi import create_proxy

COLORS = ["#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#9b5de5", "#f78c6b"]
SIZE = 460
PAD = 20  # extra room on the right for the pointer
CHARGE_MS = 1500  # time holding to reach full force
MIN_SPIN_MS, MAX_SPIN_MS = 2000, 6000
MIN_TURNS, MAX_TURNS = 2, 10

canvas = document.getElementById("wheel")
hit = document.getElementById("hit")  # the round clickable area over the wheel
ctx = canvas.getContext("2d")
result = document.getElementById("result")
button = document.getElementById("spin")
fill = document.getElementById("fill")
power = document.getElementById("power")
hint = document.getElementById("hint")
num_el = document.getElementById("num")
counter_el = document.getElementById("counter")

IS_LIVE = window.location.hostname == "manuel-verduzco.github.io"
# For testing only, and ignored on the live site: add ?force=1 to the address to make the
# wheel land on that number, and/or &fx=crumbs (or rain) to force an effect.
FORCE_NUMBER = None
FORCE_FX = None
if not IS_LIVE:
    for part in window.location.search.replace("?", "").split("&"):
        pair = part.split("=")
        if len(pair) == 2 and pair[0] == "force" and pair[1].isdigit():
            FORCE_NUMBER = int(pair[1])
        if len(pair) == 2 and pair[0] == "fx":
            FORCE_FX = pair[1]

# ---- Global spin counter -------------------------------------------------------
# GitHub Pages cannot store anything, so the total lives on a free public counter
# service (https://jasoncameron.dev/abacus/). Each finished spin adds 1. Only the
# counter name is sent, nothing about the player. If the service is unreachable the
# game still works and the counter just stays hidden. Spins made while testing on
# localhost go to a separate "-dev" counter so they do not inflate the real total.
COUNTER_BASE = "https://abacus.jasoncameron.dev"
COUNTER_NS = "manuel-verduzco-mike-echo-lima"
if not IS_LIVE:
    COUNTER_NS += "-dev"
COUNTER_KEY = "spins"


def show_count(value):
    digits = str(int(value))
    out = ""
    while len(digits) > 3:
        out = "," + digits[-3:] + out
        digits = digits[:-3]
    total = digits + out
    counter_el.innerText = "🍪 %s spin%s worldwide" % (total, "" if total == "1" else "s")
    counter_el.style.visibility = "visible"


def counter_request(action, retry=True):
    """action is "get" (just read the total) or "hit" (add one spin, then show the new total)."""
    url = "%s/%s/%s/%s" % (COUNTER_BASE, action, COUNTER_NS, COUNTER_KEY)
    status = [0]

    def on_response(resp):
        status[0] = resp.status
        if resp.ok:
            return resp.json()
        return None

    def on_data(data):
        if data:
            show_count(data.value)
        elif action == "get" and status[0] == 404:
            show_count(0)  # nobody has spun yet, so the counter does not exist yet
        elif retry:
            # the free service hiccuped: try once more shortly, otherwise stay quiet
            window.setTimeout(create_proxy(lambda: counter_request("get", False)), 1500)

    try:
        window.fetch(url).then(create_proxy(on_response)).then(create_proxy(on_data)).catch(create_proxy(lambda e: None))
    except Exception:
        pass


msg_el = document.getElementById("msg")


def say(text, number=None):
    """Show a message in the card. With a number it shows the gold badge and highlights the card."""
    msg_el.innerText = text
    result.classList.remove("jackpot")
    if number is None:
        num_el.style.display = "none"
        result.classList.remove("won")
    else:
        num_el.innerText = "#%d" % number
        num_el.style.display = "inline-block"
        result.classList.add("won")


# ---- Sounds ---------------------------------------------------------------------
# sounds.json says which sentence plays which audio file, e.g. {"37": "apple.mp3"}. The
# files live in the sounds/ folder. A sound plays when its sentence comes up, and there
# is a mute button (always visible). No sounds.json entries means the game is silent,
# exactly as before.
SOUNDS = {}
player = document.getElementById("player")
mute_btn = document.getElementById("mute")
muted = False
audio_unlocked = False
# a tiny silent clip: playing it during the first tap unlocks audio on iPhones, which
# otherwise refuse to play a sound that starts later, after the wheel has stopped
SILENCE = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAABErAAABAAgAZGF0YQAAAAA="


def safe_play():
    try:
        p = player.play()
        if p:
            p.catch(create_proxy(lambda e: None))
    except Exception:
        pass


def play_sound(number):
    name = SOUNDS.get(number)
    if not name or muted:
        return
    player.src = "sounds/" + window.encodeURIComponent(name)
    safe_play()


def stop_sound():
    try:
        player.pause()
    except Exception:
        pass


def unlock_audio():
    global audio_unlocked
    if audio_unlocked or not SOUNDS:
        return
    audio_unlocked = True
    player.src = SILENCE
    safe_play()


def show_mute():
    mute_btn.innerText = "🔇" if muted else "🔊"


def toggle_mute(event=None):
    global muted
    muted = not muted
    show_mute()
    if muted:
        stop_sound()
    try:
        window.localStorage.setItem("muted", "1" if muted else "0")
    except Exception:
        pass


def load_sounds():
    # the number changes every 10 minutes, so edits to sounds.json show up soon after publishing
    url = "sounds.json?t=%d" % int(window.Date.now() / 600000)

    def on_response(resp):
        if resp.ok:
            return resp.text()
        return None

    def on_text(text):
        if not text:
            return
        try:
            data = json.loads(text)
        except Exception:
            return
        for key in data:
            name = data[key]
            ok = isinstance(name, str) and name and "/" not in name and "\\" not in name and ".." not in name
            if key.isdigit() and ok:
                SOUNDS[int(key)] = name

    try:
        window.fetch(url).then(create_proxy(on_response)).then(create_proxy(on_text)).catch(create_proxy(lambda e: None))
    except Exception:
        pass


# ---- Special effects -----------------------------------------------------------
# Which effects fire is decided in effects.py. They are drawn on a see-through canvas
# that covers the whole page (it never blocks clicks). People who ask their device for
# reduced motion get the jackpot banner but no flying particles.
fx = document.getElementById("fx")
fxctx = fx.getContext("2d")
banner = document.getElementById("banner")
particles = []
fx_running = False
fx_last = None
fx_w = 0
fx_h = 0
FXD = 1
CRUMB_COLORS = ["#d9a45a", "#c98f45", "#b8782f", "#e6b970", "#a8651f"]


def reduced_motion():
    try:
        return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    except Exception:
        return False


def spread(lo, hi):
    return lo + (hi - lo) * random.random()


def pick(items):
    return items[random.randint(0, len(items) - 1)]


def fx_size():
    global fx_w, fx_h, FXD
    FXD = 2 if window.devicePixelRatio > 1.5 else 1
    fx_w = window.innerWidth
    fx_h = window.innerHeight
    fx.width = int(fx_w * FXD)
    fx.height = int(fx_h * FXD)


def add_particle(kind, x, y, vx, vy, size, color, life, g=900.0, drag=0.0, vr=0.0):
    particles.append({"kind": kind, "x": x, "y": y, "vx": vx, "vy": vy, "size": size,
                      "color": color, "max": life, "life": 0.0, "g": g, "drag": drag,
                      "rot": random.random() * 6.28, "vr": vr, "flip": random.random() * 6.28})


def pointer_pos():
    """Where the pointer tip is on the screen."""
    r = canvas.getBoundingClientRect()
    k = r.width / (SIZE + PAD)
    return r.left + (SIZE - 20) * k, r.top + SIZE / 2 * k


def fx_crumbs(x, y):
    for _ in range(80):
        a = spread(-1.4, 1.4)
        speed = spread(220, 640)
        add_particle("crumb", x, y, speed * math.cos(a), speed * math.sin(a) - 160,
                     spread(3, 7), pick(CRUMB_COLORS), spread(1.4, 2.6), vr=spread(-8, 8))
    for _ in range(18):
        a = spread(-1.5, 1.5)
        speed = spread(200, 520)
        add_particle("chip", x, y, speed * math.cos(a), speed * math.sin(a) - 200,
                     spread(5, 9), "#5a3420", spread(1.5, 2.6), vr=spread(-6, 6))


def fx_rain(n=26):
    for _ in range(n):
        add_particle("emoji", spread(0, fx_w), spread(-fx_h * 0.6, -30), spread(-30, 30),
                     spread(120, 260), spread(22, 40), "", spread(6.0, 9.0), g=60.0, vr=spread(-3, 3))


def fx_draw(p):
    left = p["max"] - p["life"]
    fxctx.globalAlpha = 1.0 if left > 0.6 else max(0.0, left / 0.6)
    fxctx.save()
    fxctx.translate(p["x"], p["y"])
    fxctx.rotate(p["rot"])
    kind = p["kind"]
    s = p["size"]
    if kind == "emoji":
        fxctx.font = "%dpx serif" % int(s)
        fxctx.textAlign = "center"
        fxctx.textBaseline = "middle"
        fxctx.fillText("🍪", 0, 0)
    elif kind == "chip":
        fxctx.beginPath()
        fxctx.ellipse(0, 0, s, s * 0.7, 0, 0, 2 * math.pi)
        fxctx.fillStyle = p["color"]
        fxctx.fill()
    else:  # crumb
        fxctx.fillStyle = p["color"]
        fxctx.fillRect(-s / 2, -s / 2, s, s * 0.8)
    fxctx.restore()
    fxctx.globalAlpha = 1.0


def fx_step(now):
    global fx_running, fx_last
    dt = 0.016 if fx_last is None else min(0.05, (now - fx_last) / 1000)
    fx_last = now
    fxctx.setTransform(FXD, 0, 0, FXD, 0, 0)
    fxctx.clearRect(0, 0, fx_w, fx_h)
    alive = []
    for p in particles:
        p["life"] += dt
        if p["life"] > p["max"]:
            continue
        p["vy"] += p["g"] * dt
        keep = 1 - p["drag"] * dt
        p["vx"] *= keep
        p["vy"] *= keep
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["rot"] += p["vr"] * dt
        p["flip"] += 6 * dt
        if p["y"] > fx_h + 60:
            continue
        fx_draw(p)
        alive.append(p)
    particles[:] = alive
    if alive:
        window.requestAnimationFrame(fx_proxy)
    else:
        fxctx.clearRect(0, 0, fx_w, fx_h)
        fx_running = False


fx_proxy = create_proxy(fx_step)


def fx_start():
    global fx_running, fx_last
    if not fx_running:
        fx_running = True
        fx_last = None
        window.requestAnimationFrame(fx_proxy)


def fire_effects(effects, number):
    """Called when a spin has finished and the result is showing."""
    if "jackpot" in effects:
        banner.innerText = PHRASES[number]  # e.g. GOOD EVENING, taken straight from the list
        banner.classList.remove("show")
        banner.offsetWidth  # forces the browser to restart the banner animation
        banner.classList.add("show")
        result.classList.add("jackpot")
    if reduced_motion():
        return
    if "crumbs" in effects or "rain" in effects or "jackpot" in effects:
        fx_size()
        if "crumbs" in effects:
            x, y = pointer_pos()
            fx_crumbs(x, y)
        if "rain" in effects:
            fx_rain()
        if "jackpot" in effects:
            fx_rain(90)  # a proper downpour of cookies
        fx_start()


groups = deal()  # the slices: each is a block of numbers
count = len(groups)
extent = 2 * math.pi / count
angle = -extent / 2  # radians; the pointer sits at 3 o'clock, first slice starts under it
flap = 0.0  # how hard the wheel is currently pushing the pointer (0 when still)
spinning = False
charging = False
charge_start = None


DPR = 2  # draw at 2x resolution so the small numbers stay crisp
DENSE = 25  # with this many slices or more, numbers run along each slice
canvas.width = (SIZE + PAD) * DPR
canvas.height = SIZE * DPR
# The wheel itself is drawn once into this hidden canvas, then just rotated each frame.
body = document.createElement("canvas")
body.width = SIZE * DPR
body.height = SIZE * DPR
bctx = body.getContext("2d")

# Tiny repeatable random generator for the biscuit texture (so it never changes
# between redraws, and does not disturb the real random numbers used for spinning).
_seed = 1


def rnd():
    global _seed
    _seed = (_seed * 75 + 74) % 65537
    return _seed / 65537


def reseed():
    global _seed
    _seed = 1


# Three British biscuits. Each is one continuous surface: a base colour (with a soft
# gradient) plus one texture spread over the whole wheel. The slices are only hinted
# at by faint cut lines, so the biscuit looks like a single biscuit.
def dot(x, y, size, color):
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * math.pi)
    ctx.fillStyle = color
    ctx.fill()


def polar(cx, cy, rad, a):
    return cx + rad * math.cos(a), cy + rad * math.sin(a)


def scatter(cx, cy, inner, lo=0.0):
    """A random point on the biscuit, never nearer the centre than `lo`."""
    return polar(cx, cy, inner * (lo + (0.97 - lo) * math.sqrt(rnd())), rnd() * 2 * math.pi)


def chip(x, y, size, rot):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.beginPath()
    ctx.ellipse(0, 0, size, size * 0.7, 0, 0, 2 * math.pi)
    ctx.fillStyle = "#3b1f12"
    ctx.fill()
    ctx.beginPath()
    ctx.ellipse(-size * 0.25, -size * 0.2, size * 0.35, size * 0.2, 0, 0, 2 * math.pi)
    ctx.fillStyle = "#6b4228"
    ctx.fill()
    ctx.restore()


def texture_digestive(cx, cy, inner):
    reseed()
    for _ in range(150):  # wheat flecks
        x, y = scatter(cx, cy, inner)
        dot(x, y, 1.0 + 0.8 * rnd(), "#a6702f")
    # the little docking holes, in neat staggered rings like a real digestive
    for ring, (rf, holes) in enumerate(((0.17, 6), (0.35, 13), (0.53, 20), (0.71, 27), (0.89, 34))):
        for k in range(holes):
            x, y = polar(cx, cy, inner * rf, (k + 0.5 * (ring % 2)) * 2 * math.pi / holes)
            dot(x, y, 3.4, "#bd8a45")
            dot(x, y, 2.0, "#8f5c24")


def texture_choc(cx, cy, inner):
    reseed()
    ctx.lineCap = "round"
    ctx.strokeStyle = "rgba(0,0,0,0.16)"
    ctx.lineWidth = 1.5
    for rf in (0.22, 0.40, 0.58, 0.76, 0.92):  # faint ridges
        ctx.beginPath()
        ctx.arc(cx, cy, inner * rf, 0, 2 * math.pi)
        ctx.stroke()
    ctx.strokeStyle = "rgba(255,255,255,0.10)"
    ctx.lineWidth = 5
    for _ in range(14):  # little glossy streaks
        a = rnd() * 2 * math.pi
        ctx.beginPath()
        ctx.arc(cx, cy, inner * (0.15 + 0.8 * rnd()), a, a + 0.12 + 0.2 * rnd())
        ctx.stroke()
    ctx.lineCap = "butt"


def texture_cookie(cx, cy, inner):
    reseed()
    for _ in range(80):  # crumbly speckles
        x, y = scatter(cx, cy, inner)
        dot(x, y, 1.0 + 1.0 * rnd(), "#b97f35")
    for _ in range(34):  # chocolate chips, anywhere on the cookie
        x, y = scatter(cx, cy, inner, 0.14)
        chip(x, y, 5 + 3 * rnd(), rnd() * 6.28)


THEMES = {
    "digestive": {
        "label": "Digestive",
        "rim": "#c98f45", "flute": "#d69d52", "c0": "#f0d196", "c1": "#e1b46b",
        "line": "rgba(150,95,35,0.35)", "text": "#4a2a14", "halo": "#f8e8c8", "hub": "#4a2a14",
        "text_r": 0.62, "texture": texture_digestive, "glare": False,
    },
    "choc": {
        "label": "Choc Digestive",
        "rim": "#c98f45", "flute": "#d69d52", "c0": "#76462b", "c1": "#583019",
        "line": "rgba(25,10,4,0.5)", "text": "#fff1d6", "halo": "#2e170a", "hub": "#2e170a",
        "text_r": 0.66, "texture": texture_choc, "glare": True,
    },
    "cookie": {
        "label": "Choc Chip Cookie",
        "rim": "#b5732b", "flute": "#c4823a", "c0": "#e4b26b", "c1": "#cf9144",
        "line": "rgba(130,75,20,0.35)", "text": "#3b1f12", "halo": "#f8e8c8", "hub": "#3b1f12",
        "text_r": 0.68, "texture": texture_cookie, "glare": False,
    },
}
theme_name = "cookie"


def build_body():
    """Draw the biscuit (at rotation 0) into the hidden canvas. Call after the
    biscuit or the order of the numbers changes."""
    global ctx
    th = THEMES[theme_name]
    dense = count >= DENSE
    radial = dense or max(len(label(g)) for g in groups) > 3  # long labels run along the slice
    main_ctx = ctx
    ctx = bctx
    try:
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0)
        ctx.clearRect(0, 0, SIZE, SIZE)
        cx = SIZE / 2
        cy = SIZE / 2
        r = SIZE / 2 - 10

        # baked rim with a finely fluted edge
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.fillStyle = th["rim"]
        ctx.fill()
        for k in range(72):
            x, y = polar(cx, cy, r - 1, k * 2 * math.pi / 72)
            dot(x, y, 5, th["flute"])

        # the biscuit surface: one gradient, one texture over the whole wheel
        inner = r - 9
        grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, inner)
        grad.addColorStop(0, th["c0"])
        grad.addColorStop(1, th["c1"])
        ctx.beginPath()
        ctx.arc(cx, cy, inner, 0, 2 * math.pi)
        ctx.fillStyle = grad
        ctx.fill()
        th["texture"](cx, cy, inner)

        # faint cut lines between the slices
        ctx.strokeStyle = th["line"]
        ctx.lineWidth = 1.2
        for i in range(count):
            a = i * extent
            ctx.beginPath()
            ctx.moveTo(cx, cy)
            ctx.lineTo(cx + inner * math.cos(a), cy + inner * math.sin(a))
            ctx.stroke()

        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.lineJoin = "round"
        for i, g in enumerate(groups):
            text = label(g)
            mid = i * extent + extent / 2
            ctx.strokeStyle = th["halo"]
            ctx.fillStyle = th["text"]
            if dense:
                # numbers run along their slice, on two alternating rings so they fit
                rad = inner * (0.86 if i % 2 == 0 else 0.60)
                ctx.font = "bold 13px sans-serif"
                ctx.lineWidth = 3
                ctx.save()
                ctx.translate(cx, cy)
                ctx.rotate(mid)
                ctx.strokeText(text, rad, 0)
                ctx.fillText(text, rad, 0)
                ctx.restore()
            elif radial:
                # block labels like "101-106" run along the slice, one ring
                ctx.font = "bold 15px sans-serif"
                ctx.lineWidth = 4
                ctx.save()
                ctx.translate(cx, cy)
                ctx.rotate(mid)
                ctx.strokeText(text, inner * 0.64, 0)
                ctx.fillText(text, inner * 0.64, 0)
                ctx.restore()
            else:
                tx, ty = polar(cx, cy, inner * th["text_r"], mid)
                ctx.font = "bold 24px sans-serif"
                ctx.lineWidth = 5
                ctx.strokeText(text, tx, ty)
                ctx.fillText(text, tx, ty)
    finally:
        ctx = main_ctx


def draw():
    th = THEMES[theme_name]
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0)
    ctx.clearRect(0, 0, SIZE + PAD, SIZE)
    cx = SIZE / 2
    cy = SIZE / 2
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(angle)
    ctx.drawImage(body, -SIZE / 2, -SIZE / 2, SIZE, SIZE)
    ctx.restore()
    if th["glare"]:
        # a fixed shine that stays put while the chocolate biscuit spins underneath
        ctx.lineCap = "round"
        ctx.strokeStyle = "rgba(255,255,255,0.10)"
        ctx.lineWidth = 16
        ctx.beginPath()
        ctx.arc(cx, cy, (SIZE / 2 - 19) * 0.78, -2.75, -1.75)
        ctx.stroke()
        ctx.lineWidth = 5
        ctx.strokeStyle = "rgba(255,255,255,0.16)"
        ctx.beginPath()
        ctx.arc(cx, cy, (SIZE / 2 - 19) * 0.86, -2.65, -1.95)
        ctx.stroke()
        ctx.lineCap = "butt"

    # centre hub
    ctx.beginPath()
    ctx.arc(cx, cy, 22, 0, 2 * math.pi)
    ctx.fillStyle = th["hub"]
    ctx.fill()
    ctx.strokeStyle = th["halo"]
    ctx.lineWidth = 3
    ctx.stroke()
    # Pointer on the right: a flexible flapper. Each divider between slices pushes it
    # as it goes past, then it springs back, like the flapper on a real prize wheel.
    theta = (-angle) % (2 * math.pi)  # where the pointer sits in the wheel own coordinates
    u = (theta / extent) % 1.0  # 0..1 across the slice under the pointer
    push = max(0.0, 1 - u / 0.3) * 0.55 * flap
    tip_x = cx + (SIZE / 2 - 10) - 10
    ctx.save()
    ctx.translate(tip_x + 38, cy)
    ctx.rotate(-push)
    ctx.beginPath()
    ctx.moveTo(-38, 0)
    ctx.lineTo(0, -15)
    ctx.lineTo(0, 15)
    ctx.closePath()
    ctx.fillStyle = "#ffffff"
    ctx.fill()
    ctx.strokeStyle = "#14141c"
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.restore()
    dot(tip_x + 38, cy, 5, "#14141c")


def set_theme(name, save=True):
    global theme_name
    theme_name = name
    build_body()
    if save:
        try:
            window.localStorage.setItem("biscuit", name)
        except Exception:
            pass
    draw()


ORDER = ["digestive", "choc", "cookie"]


def next_theme(event=None):
    set_theme(ORDER[(ORDER.index(theme_name) + 1) % len(ORDER)])


def set_force(f):
    fill.style.width = "%d%%" % int(f * 100)
    # green -> red as force grows
    fill.style.background = "hsl(%d, 80%%, 50%%)" % int(130 - 130 * f)


def charge_step(now):
    global charge_start
    if not charging:
        return
    if charge_start is None:
        charge_start = now
    set_force(min((now - charge_start) / CHARGE_MS, 1))
    window.requestAnimationFrame(charge_proxy)


def start_charge(event):
    global charging, charge_start
    event.preventDefault()
    if spinning or charging:
        return
    charging = True
    charge_start = None
    set_force(0)
    unlock_audio()
    power.style.visibility = "visible"
    say("Charging... release to spin!")
    window.requestAnimationFrame(charge_proxy)


def release(event):
    global charging
    if not charging:
        return
    charging = False
    force = min(max((window.performance.now() - charge_start) / CHARGE_MS, 0), 1) if charge_start else 0
    spin(force)


def spin(force):
    global spinning
    if spinning:
        return
    spinning = True
    button.disabled = True
    power.style.visibility = "hidden"  # bar disappears on release
    say("Spinning...")
    stop_sound()  # cut off the previous sentence's sound
    groups[:] = deal()  # shuffle where the slices sit on the wheel
    build_body()
    number = random_number()  # any of ALL the numbers, each equally likely; force only changes the show
    if FORCE_NUMBER:
        number = FORCE_NUMBER  # testing only, never on the live site
    effects = choose_effects(number)  # which special effects this spin gets
    if FORCE_FX and number != JACKPOT_NUMBER:
        effects = [FORCE_FX]
    index = group_index(groups, number)  # the slice that contains it
    turns = MIN_TURNS + int(round((MAX_TURNS - MIN_TURNS) * force))
    duration = MIN_SPIN_MS + (MAX_SPIN_MS - MIN_SPIN_MS) * force
    # Stop somewhere inside that slice (not always dead centre, like a real wheel):
    # u is how far across the slice the pointer ends up, kept off the dividers.
    u = 0.12 + 0.76 * random.random()
    end_mod = (-(index + u) * extent) % (2 * math.pi)
    start = angle
    total = (end_mod - start) % (2 * math.pi) + 2 * math.pi * turns
    t0 = [None]

    def finish():
        global angle, spinning, flap
        angle = start + total
        flap = 0.0
        draw()
        say(PHRASES[number], number)
        counter_request("hit")  # count this finished spin
        play_sound(number)  # its own voice note / sound, if you added one
        fire_effects(effects, number)
        button.disabled = False
        spinning = False

    def step(now):
        global angle, flap
        if t0[0] is None:
            t0[0] = now
        t = min((now - t0[0]) / duration, 1)
        if t < 1:
            angle = start + total * (1 - (1 - t) ** 4)  # long slow crawl at the end
            flap = min(1.0, (1 - t) * 8)  # the flapper relaxes as the wheel slows
            draw()
            window.requestAnimationFrame(step_proxy)
            return
        finish()

    step_proxy = create_proxy(step)
    window.requestAnimationFrame(step_proxy)


charge_proxy = create_proxy(charge_step)
for el in (hit, button):
    el.addEventListener("pointerdown", create_proxy(start_charge))
    el.addEventListener("contextmenu", create_proxy(lambda e: e.preventDefault()))
window.addEventListener("pointerup", create_proxy(release))
window.addEventListener("pointercancel", create_proxy(release))
# keyboard users (Enter/Space on the button) get a medium spin
button.addEventListener("click", create_proxy(lambda e: spin(0.5) if e.detail == 0 else None))
document.getElementById("swap").addEventListener("click", create_proxy(next_theme))
mute_btn.addEventListener("click", create_proxy(toggle_mute))
saved = None
try:
    saved = window.localStorage.getItem("biscuit")
    muted = window.localStorage.getItem("muted") == "1"
except Exception:
    pass
show_mute()
load_sounds()
button.disabled = False
say("Hold the wheel to charge, release to spin!")
set_theme(saved if saved in THEMES else "cookie", save=False)
counter_request("get")
