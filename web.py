"""Browser version of Spin the Wheel (runs as Python via PyScript).

Uses the same phrases.py as the desktop version.
"""

import math
import random

from phrases import PHRASES, deal, group_index, label, random_number
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

groups = deal()  # the slices: each is a block of numbers
count = len(groups)
extent = 2 * math.pi / count
angle = -math.pi / 2 - extent / 2  # radians, clockwise from 3 o'clock; first slice under the pointer
spinning = False
charging = False
charge_start = None


DPR = 2  # draw at 2x resolution so the small numbers stay crisp
DENSE = 25  # with this many slices or more, numbers run along each slice
canvas.width = SIZE * DPR
canvas.height = (SIZE + TOP + 20) * DPR
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


# Three British biscuits. Each theme is a dict of colours plus decoration functions:
# "deco" (per slice, few slices) and "dense" (whole wheel, many slices).
# (radius fraction, angle fraction across slice) for the round docking holes
HOLES = [(0.30, 0.50), (0.50, 0.25), (0.50, 0.75), (0.72, 0.38), (0.72, 0.62), (0.88, 0.50)]
# tiny flecks / sugar grains: (radius fraction, angle fraction)
FLECKS = [(0.15, 0.30), (0.22, 0.80), (0.38, 0.12), (0.40, 0.88), (0.58, 0.50), (0.62, 0.15),
          (0.64, 0.85), (0.80, 0.20), (0.80, 0.80), (0.93, 0.25), (0.93, 0.75), (0.45, 0.50)]
# chocolate chips: (radius fraction, angle fraction across slice, size)
CHIPS = [(0.30, 0.30, 7), (0.45, 0.72, 6), (0.52, 0.22, 5), (0.90, 0.35, 6), (0.88, 0.70, 5), (0.20, 0.75, 5)]


# Where the texture goes so it stays clear of the labels (set in build_body).
hole_rings = ((0.28, 12), (0.73, 40))
chip_bands = ((0.12, 0.46), (0.67, 0.79))


def dot(x, y, size, color):
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * math.pi)
    ctx.fillStyle = color
    ctx.fill()


def polar(cx, cy, rad, a):
    return cx + rad * math.cos(a), cy + rad * math.sin(a)


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


# --- few slices: decorate every slice ---
def deco_digestive(cx, cy, inner, a0):
    for rf, af in FLECKS:
        x, y = polar(cx, cy, inner * rf, a0 + af * extent)
        dot(x, y, 1.5, "#a6702f")
    for rf, af in HOLES:
        x, y = polar(cx, cy, inner * rf, a0 + af * extent)
        dot(x, y, 3.6, "#bd8a45")
        dot(x, y, 2.2, "#8f5c24")


def deco_choc(cx, cy, inner, a0):
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


def deco_cookie(cx, cy, inner, a0):
    for j, (rf, af, size) in enumerate(CHIPS):
        ca = a0 + af * extent
        x, y = polar(cx, cy, inner * rf, ca)
        chip(x, y, size, ca + j)
    for rf, af in FLECKS[:6]:
        x, y = polar(cx, cy, inner * rf, a0 + af * extent)
        dot(x, y, 1.6, "#b97f35")


# --- many slices: one texture over the whole wheel, keeping the number rings clear ---
def dense_digestive(cx, cy, inner):
    reseed()
    for _ in range(90):
        x, y = polar(cx, cy, inner * math.sqrt(rnd()), rnd() * 2 * math.pi)
        dot(x, y, 1.3, "#a6702f")
    for rf, holes in hole_rings:
        for k in range(holes):
            x, y = polar(cx, cy, inner * rf, k * 2 * math.pi / holes)
            dot(x, y, 3, "#bd8a45")
            dot(x, y, 1.8, "#8f5c24")


def dense_choc(cx, cy, inner):
    reseed()
    ctx.lineCap = "round"
    ctx.strokeStyle = "rgba(0,0,0,0.22)"
    ctx.lineWidth = 2
    for rf in (0.40, 0.73):
        ctx.beginPath()
        ctx.arc(cx, cy, inner * rf, 0, 2 * math.pi)
        ctx.stroke()
    ctx.strokeStyle = "rgba(255,255,255,0.14)"
    ctx.lineWidth = 6
    for _ in range(16):
        a = rnd() * 2 * math.pi
        ctx.beginPath()
        ctx.arc(cx, cy, inner * (0.2 + 0.75 * rnd()), a, a + 0.25)
        ctx.stroke()
    ctx.lineCap = "butt"


def dense_cookie(cx, cy, inner):
    reseed()
    for lo, hi in chip_bands:
        for j in range(14):
            a = rnd() * 2 * math.pi
            x, y = polar(cx, cy, inner * (lo + (hi - lo) * rnd()), a)
            chip(x, y, 4.5 + 2 * rnd(), a + j)
    for _ in range(40):
        x, y = polar(cx, cy, inner * math.sqrt(rnd()), rnd() * 2 * math.pi)
        dot(x, y, 1.4, "#b97f35")


THEMES = {
    "digestive": {
        "label": "Digestive",
        "rim": "#c98f45", "flute": "#d69d52",
        "slices": ["#ebc582", "#e4ba74", "#eec98a", "#e0b46c"], "line": "#b7803c",
        "text": "#4a2a14", "halo": "#f8e8c8", "hub": "#4a2a14", "text_r": 0.62,
        "deco": deco_digestive, "dense": dense_digestive, "after": None,
    },
    "choc": {
        "label": "Choc Digestive",
        "rim": "#c98f45", "flute": "#d69d52",
        "slices": ["#6b3d22", "#5f341d", "#70422a", "#633720"], "line": "#3a1d0e",
        "text": "#fff1d6", "halo": "#2e170a", "hub": "#2e170a", "text_r": 0.66,
        "deco": deco_choc, "dense": dense_choc, "after": None,
    },
    "cookie": {
        "label": "Choc Chip Cookie",
        "rim": "#b5732b", "flute": "#c4823a",
        "slices": ["#dca75a", "#d39a4a", "#e0ae62", "#d09445"], "line": "#a8671f",
        "text": "#3b1f12", "halo": "#f8e8c8", "hub": "#3b1f12", "text_r": 0.68,
        "deco": deco_cookie, "dense": dense_cookie, "after": None,
    },
}
theme_name = "digestive"


def build_body():
    """Draw the biscuit (at rotation 0) into the hidden canvas. Call after the
    biscuit or the order of the numbers changes."""
    global ctx, hole_rings, chip_bands
    th = THEMES[theme_name]
    dense = count >= DENSE
    radial = dense or max(len(label(g)) for g in groups) > 3  # long labels run along the slice
    if not dense:
        hole_rings = ((0.2, 10), (0.90, 44))
        chip_bands = ((0.10, 0.36), (0.88, 0.95))
    else:
        hole_rings = ((0.28, 12), (0.73, 40))
        chip_bands = ((0.12, 0.46), (0.67, 0.79))
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

        inner = r - 9
        for i in range(count):
            a0 = i * extent
            ctx.beginPath()
            ctx.moveTo(cx, cy)
            ctx.arc(cx, cy, inner, a0, a0 + extent)
            ctx.closePath()
            ctx.fillStyle = th["slices"][i % len(th["slices"])]
            ctx.fill()
            ctx.strokeStyle = th["line"]
            ctx.lineWidth = 0.8 if dense else 2
            ctx.stroke()
            if not radial:
                th["deco"](cx, cy, inner, a0)
        if radial:
            th["dense"](cx, cy, inner)
        if th["after"]:
            th["after"](cx, cy, inner)

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
    ctx.clearRect(0, 0, SIZE, SIZE + TOP + 20)
    cx = SIZE / 2
    cy = TOP + SIZE / 2
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(angle)
    ctx.drawImage(body, -SIZE / 2, -SIZE / 2, SIZE, SIZE)
    ctx.restore()

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
    groups[:] = deal()  # shuffle where the slices sit on the wheel
    build_body()
    number = random_number()  # any of ALL the numbers, each equally likely; force only changes the show
    index = group_index(groups, number)  # the slice that contains it
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
            result.innerText = "#%d\n%s" % (number, PHRASES[number])
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
document.getElementById("swap").addEventListener("click", create_proxy(next_theme))
saved = None
try:
    saved = window.localStorage.getItem("biscuit")
except Exception:
    pass
button.disabled = False
result.innerText = "Hold the wheel to charge, release to spin!"
set_theme(saved if saved in THEMES else "digestive", save=False)
