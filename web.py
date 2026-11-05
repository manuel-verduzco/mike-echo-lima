"""Browser version of Spin the Wheel (runs as Python via PyScript).

Uses the same phrases.py as the desktop version.
"""

import math
import random

from phrases import PHRASES
from pyscript import document, window
from pyscript.ffi import create_proxy

COLORS = ["#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#9b5de5", "#f78c6b"]
SIZE = 460
TOP = 20
CHARGE_MS = 1500  # time holding to reach full force
MIN_SPIN_MS, MAX_SPIN_MS = 2000, 6000
MIN_TURNS, MAX_TURNS = 2, 10

canvas = document.getElementById("wheel")
ctx = canvas.getContext("2d")
result = document.getElementById("result")
button = document.getElementById("spin")
fill = document.getElementById("fill")
power = document.getElementById("power")
hint = document.getElementById("hint")

numbers = sorted(PHRASES)
count = len(numbers)
extent = 2 * math.pi / count
angle = -math.pi / 2 - extent / 2  # radians, clockwise from 3 o'clock; number 1 under the pointer
spinning = False
charging = False
charge_start = None


# Three British biscuits you can pick from. Each theme is a dict of colours plus
# two optional decoration functions (per slice, and once for the whole wheel).
# (radius fraction, angle fraction across slice) for the round docking holes
HOLES = [(0.30, 0.50), (0.50, 0.25), (0.50, 0.75), (0.72, 0.38), (0.72, 0.62), (0.88, 0.50)]
# tiny flecks / sugar grains: (radius fraction, angle fraction)
FLECKS = [(0.15, 0.30), (0.22, 0.80), (0.38, 0.12), (0.40, 0.88), (0.58, 0.50), (0.62, 0.15),
          (0.64, 0.85), (0.80, 0.20), (0.80, 0.80), (0.93, 0.25), (0.93, 0.75), (0.45, 0.50)]


def dot(x, y, size, color):
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * math.pi)
    ctx.fillStyle = color
    ctx.fill()


def polar(cx, cy, rad, a):
    return cx + rad * math.cos(a), cy + rad * math.sin(a)


def deco_digestive(cx, cy, inner, a0):
    for rf, af in FLECKS:
        x, y = polar(cx, cy, inner * rf, a0 + af * extent)
        dot(x, y, 1.5, "#a6702f")
    for rf, af in HOLES:
        x, y = polar(cx, cy, inner * rf, a0 + af * extent)
        dot(x, y, 3.6, "#bd8a45")
        dot(x, y, 2.2, "#8f5c24")


def deco_choc(cx, cy, inner, a0):
    # glossy chocolate highlights and little ridges
    ctx.lineCap = "round"
    ctx.strokeStyle = "rgba(255,255,255,0.16)"
    ctx.lineWidth = 7
    ctx.beginPath()
    ctx.arc(cx, cy, inner * 0.86, a0 + 0.18 * extent, a0 + 0.5 * extent)
    ctx.stroke()
    ctx.strokeStyle = "rgba(0,0,0,0.22)"
    ctx.lineWidth = 2
    for rf in (0.45, 0.62):
        ctx.beginPath()
        ctx.arc(cx, cy, inner * rf, a0 + 0.12 * extent, a0 + 0.88 * extent)
        ctx.stroke()
    ctx.lineCap = "butt"


# chocolate chips: (radius fraction, angle fraction across slice, size)
CHIPS = [(0.30, 0.30, 7), (0.45, 0.72, 6), (0.52, 0.22, 5), (0.90, 0.35, 6), (0.88, 0.70, 5), (0.20, 0.75, 5)]


def deco_cookie(cx, cy, inner, a0):
    for j, (rf, af, size) in enumerate(CHIPS):
        ca = a0 + af * extent
        x, y = polar(cx, cy, inner * rf, ca)
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ca + j)
        ctx.beginPath()
        ctx.ellipse(0, 0, size, size * 0.7, 0, 0, 2 * math.pi)
        ctx.fillStyle = "#3b1f12"
        ctx.fill()
        ctx.beginPath()
        ctx.ellipse(-size * 0.25, -size * 0.2, size * 0.35, size * 0.2, 0, 0, 2 * math.pi)
        ctx.fillStyle = "#6b4228"
        ctx.fill()
        ctx.restore()
    for rf, af in FLECKS[:6]:
        x, y = polar(cx, cy, inner * rf, a0 + af * extent)
        dot(x, y, 1.6, "#b97f35")


THEMES = {
    "digestive": {
        "label": "Digestive",
        "rim": "#c98f45", "flute": "#d69d52",
        "slices": ["#ebc582", "#e4ba74", "#eec98a", "#e0b46c"], "line": "#b7803c",
        "text": "#4a2a14", "halo": "#f8e8c8", "hub": "#4a2a14", "text_r": 0.62,
        "deco": deco_digestive, "after": None,
    },
    "choc": {
        "label": "Choc Digestive",
        "rim": "#c98f45", "flute": "#d69d52",
        "slices": ["#6b3d22", "#5f341d", "#70422a", "#633720"], "line": "#3a1d0e",
        "text": "#fff1d6", "halo": "#2e170a", "hub": "#2e170a", "text_r": 0.66,
        "deco": deco_choc, "after": None,
    },
    "cookie": {
        "label": "Choc Chip Cookie",
        "rim": "#b5732b", "flute": "#c4823a",
        "slices": ["#dca75a", "#d39a4a", "#e0ae62", "#d09445"], "line": "#a8671f",
        "text": "#3b1f12", "halo": "#f8e8c8", "hub": "#3b1f12", "text_r": 0.68,
        "deco": deco_cookie, "after": None,
    },
}
theme_name = "digestive"


def draw():
    th = THEMES[theme_name]
    cx = SIZE / 2
    cy = TOP + SIZE / 2
    r = SIZE / 2 - 10
    ctx.clearRect(0, 0, SIZE, SIZE + TOP + 20)

    # baked rim with a finely fluted edge
    ctx.beginPath()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fillStyle = th["rim"]
    ctx.fill()
    flutes = 72
    for k in range(flutes):
        x, y = polar(cx, cy, r - 1, angle + k * 2 * math.pi / flutes)
        dot(x, y, 5, th["flute"])

    inner = r - 9
    for i, n in enumerate(numbers):
        a0 = angle + i * extent
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, inner, a0, a0 + extent)
        ctx.closePath()
        ctx.fillStyle = th["slices"][i % len(th["slices"])]
        ctx.fill()
        ctx.strokeStyle = th["line"]
        ctx.lineWidth = 2
        ctx.stroke()
        th["deco"](cx, cy, inner, a0)
    if th["after"]:
        th["after"](cx, cy, inner)

    for i, n in enumerate(numbers):
        mid = angle + i * extent + extent / 2
        tx, ty = polar(cx, cy, inner * th["text_r"], mid)
        ctx.font = "bold 24px sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.lineWidth = 5
        ctx.strokeStyle = th["halo"]
        ctx.strokeText(str(n), tx, ty)
        ctx.fillStyle = th["text"]
        ctx.fillText(str(n), tx, ty)

    # centre hub
    ctx.beginPath()
    ctx.arc(cx, cy, 22, 0, 2 * math.pi)
    ctx.fillStyle = th["hub"]
    ctx.fill()
    ctx.strokeStyle = th["halo"]
    ctx.lineWidth = 3
    ctx.stroke()
    # pointer at top
    ctx.beginPath()
    ctx.moveTo(cx - 14, 0)
    ctx.lineTo(cx + 14, 0)
    ctx.lineTo(cx, 34)
    ctx.closePath()
    ctx.fillStyle = "#ffffff"
    ctx.fill()


def set_theme(name, save=True):
    global theme_name
    theme_name = name
    for key in THEMES:
        document.getElementById("pick-" + key).classList.toggle("active", key == name)
    if save:
        try:
            window.localStorage.setItem("biscuit", name)
        except Exception:
            pass
    draw()


def make_picker(name):
    return create_proxy(lambda e: set_theme(name))


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
    power.style.visibility = "visible"
    result.innerText = "Charging... release to spin!"
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
    result.innerText = "Spinning..."
    index = random.randint(0, count - 1)  # the result is random; force only changes the show
    turns = MIN_TURNS + int(round((MAX_TURNS - MIN_TURNS) * force))
    duration = MIN_SPIN_MS + (MAX_SPIN_MS - MIN_SPIN_MS) * force
    # angle that centres segment `index` under the pointer (top = -pi/2)
    end_mod = (-math.pi / 2 - (index + 0.5) * extent) % (2 * math.pi)
    start = angle
    total = (end_mod - start) % (2 * math.pi) + 2 * math.pi * turns
    t0 = [None]

    def step(now):
        global angle, spinning
        if t0[0] is None:
            t0[0] = now
        t = min((now - t0[0]) / duration, 1)
        angle = start + total * (1 - (1 - t) ** 3)
        draw()
        if t < 1:
            window.requestAnimationFrame(step_proxy)
        else:
            key = numbers[index]
            result.innerText = "#%d\n%s" % (key, PHRASES[key])
            button.disabled = False
            spinning = False

    step_proxy = create_proxy(step)
    window.requestAnimationFrame(step_proxy)


charge_proxy = create_proxy(charge_step)
for el in (canvas, button):
    el.addEventListener("pointerdown", create_proxy(start_charge))
    el.addEventListener("contextmenu", create_proxy(lambda e: e.preventDefault()))
window.addEventListener("pointerup", create_proxy(release))
window.addEventListener("pointercancel", create_proxy(release))
# keyboard users (Enter/Space on the button) get a medium spin
button.addEventListener("click", create_proxy(lambda e: spin(0.5) if e.detail == 0 else None))
for key in THEMES:
    document.getElementById("pick-" + key).addEventListener("click", make_picker(key))
saved = None
try:
    saved = window.localStorage.getItem("biscuit")
except Exception:
    pass
button.disabled = False
result.innerText = "Hold the wheel to charge, release to spin!"
set_theme(saved if saved in THEMES else "digestive", save=False)
