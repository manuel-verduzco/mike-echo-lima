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


# A classic British digestive: golden, flecked with wheat, with docking holes.
BISCUIT = ["#ebc582", "#e4ba74", "#eec98a", "#e0b46c"]
CHOC = "#4a2a14"
# (radius fraction, angle fraction across slice) for the round docking holes
HOLES = [(0.30, 0.50), (0.50, 0.25), (0.50, 0.75), (0.72, 0.38), (0.72, 0.62), (0.88, 0.50)]
# tiny wheat flecks: (radius fraction, angle fraction, size)
FLECKS = [(0.15, 0.30, 1.6), (0.22, 0.80, 1.4), (0.38, 0.12, 1.5), (0.40, 0.88, 1.6),
          (0.58, 0.50, 1.4), (0.62, 0.15, 1.6), (0.64, 0.85, 1.4), (0.80, 0.20, 1.5),
          (0.80, 0.80, 1.6), (0.93, 0.25, 1.4), (0.93, 0.75, 1.5), (0.45, 0.50, 1.4)]


def dot(x, y, size, color):
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * math.pi)
    ctx.fillStyle = color
    ctx.fill()


def draw():
    cx = SIZE / 2
    cy = TOP + SIZE / 2
    r = SIZE / 2 - 10
    ctx.clearRect(0, 0, SIZE, SIZE + TOP + 20)

    # toasted rim with a finely fluted edge
    ctx.beginPath()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fillStyle = "#c98f45"
    ctx.fill()
    flutes = 72
    for k in range(flutes):
        a = angle + k * 2 * math.pi / flutes
        dot(cx + (r - 1) * math.cos(a), cy + (r - 1) * math.sin(a), 5, "#d69d52")

    inner = r - 9
    for i, n in enumerate(numbers):
        a0 = angle + i * extent
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, inner, a0, a0 + extent)
        ctx.closePath()
        ctx.fillStyle = BISCUIT[i % len(BISCUIT)]
        ctx.fill()
        ctx.strokeStyle = "#b7803c"
        ctx.lineWidth = 2
        ctx.stroke()
        for rf, af, size in FLECKS:
            ca = a0 + af * extent
            dot(cx + inner * rf * math.cos(ca), cy + inner * rf * math.sin(ca), size, "#a6702f")
        for rf, af in HOLES:
            ca = a0 + af * extent
            hx = cx + inner * rf * math.cos(ca)
            hy = cy + inner * rf * math.sin(ca)
            dot(hx, hy, 3.6, "#bd8a45")
            dot(hx, hy, 2.2, "#8f5c24")
        mid = a0 + extent / 2
        tx = cx + inner * 0.62 * math.cos(mid)
        ty = cy + inner * 0.62 * math.sin(mid)
        ctx.font = "bold 24px sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.lineWidth = 5
        ctx.strokeStyle = "#f8e8c8"
        ctx.strokeText(str(n), tx, ty)
        ctx.fillStyle = CHOC
        ctx.fillText(str(n), tx, ty)

    # centre hub
    ctx.beginPath()
    ctx.arc(cx, cy, 22, 0, 2 * math.pi)
    ctx.fillStyle = CHOC
    ctx.fill()
    ctx.strokeStyle = "#f8e8c8"
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
button.disabled = False
result.innerText = "Hold the wheel to charge, release to spin!"
draw()
