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


BISCUIT = ["#e6b068", "#dba04f", "#eab874", "#d6994a"]
CHOC = "#3b1f12"
# chocolate chips per slice: (radius fraction, angle fraction across slice, size)
CHIPS = [(0.30, 0.30, 7), (0.45, 0.72, 6), (0.52, 0.22, 5), (0.90, 0.35, 6), (0.88, 0.70, 5), (0.20, 0.75, 5)]


def chip(x, y, size, rot):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.beginPath()
    ctx.ellipse(0, 0, size, size * 0.7, 0, 0, 2 * math.pi)
    ctx.fillStyle = CHOC
    ctx.fill()
    ctx.beginPath()
    ctx.ellipse(-size * 0.25, -size * 0.2, size * 0.35, size * 0.2, 0, 0, 2 * math.pi)
    ctx.fillStyle = "#6b4228"
    ctx.fill()
    ctx.restore()


def draw():
    cx = SIZE / 2
    cy = TOP + SIZE / 2
    r = SIZE / 2 - 10
    ctx.clearRect(0, 0, SIZE, SIZE + TOP + 20)

    # baked rim with a bumpy edge
    ctx.beginPath()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fillStyle = "#a8651f"
    ctx.fill()
    bumps = 36
    for k in range(bumps):
        a = angle + k * 2 * math.pi / bumps
        ctx.beginPath()
        ctx.arc(cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a), 9, 0, 2 * math.pi)
        ctx.fillStyle = "#b9772f"
        ctx.fill()

    inner = r - 12
    for i, n in enumerate(numbers):
        a0 = angle + i * extent
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, inner, a0, a0 + extent)
        ctx.closePath()
        ctx.fillStyle = BISCUIT[i % len(BISCUIT)]
        ctx.fill()
        ctx.strokeStyle = "#8a5420"
        ctx.lineWidth = 2
        ctx.stroke()
        for j, (rf, af, size) in enumerate(CHIPS):
            ca = a0 + af * extent
            chip(cx + inner * rf * math.cos(ca), cy + inner * rf * math.sin(ca), size, ca + j)
        mid = a0 + extent / 2
        tx = cx + inner * 0.68 * math.cos(mid)
        ty = cy + inner * 0.68 * math.sin(mid)
        ctx.font = "bold 24px sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.lineWidth = 5
        ctx.strokeStyle = "#f6e3bd"
        ctx.strokeText(str(n), tx, ty)
        ctx.fillStyle = CHOC
        ctx.fillText(str(n), tx, ty)

    # centre hub
    ctx.beginPath()
    ctx.arc(cx, cy, 22, 0, 2 * math.pi)
    ctx.fillStyle = CHOC
    ctx.fill()
    ctx.strokeStyle = "#f6e3bd"
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
