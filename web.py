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
msg_el = document.getElementById("msg")


def say(text, number=None):
    """Show a message in the card. With a number it shows the gold badge and highlights the card."""
    msg_el.innerText = text
    if number is None:
        num_el.style.display = "none"
        result.classList.remove("won")
    else:
        num_el.innerText = "#%d" % number
        num_el.style.display = "inline-block"
        result.classList.add("won")

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
theme_name = "digestive"


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
    groups[:] = deal()  # shuffle where the slices sit on the wheel
    build_body()
    number = random_number()  # any of ALL the numbers, each equally likely; force only changes the show
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

    def step(now):
        global angle, spinning, flap
        if t0[0] is None:
            t0[0] = now
        t = min((now - t0[0]) / duration, 1)
        angle = start + total * (1 - (1 - t) ** 4)  # long slow crawl at the end
        flap = min(1.0, (1 - t) * 8)  # the flapper relaxes as the wheel slows
        draw()
        if t < 1:
            window.requestAnimationFrame(step_proxy)
        else:
            flap = 0.0
            draw()
            say(PHRASES[number], number)
            button.disabled = False
            spinning = False

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
saved = None
try:
    saved = window.localStorage.getItem("biscuit")
except Exception:
    pass
button.disabled = False
say("Hold the wheel to charge, release to spin!")
set_theme(saved if saved in THEMES else "digestive", save=False)
