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
SPIN_MS = 4000

canvas = document.getElementById("wheel")
ctx = canvas.getContext("2d")
result = document.getElementById("result")
button = document.getElementById("spin")

numbers = sorted(PHRASES)
count = len(numbers)
extent = 2 * math.pi / count
angle = -math.pi / 2 - extent / 2  # radians, clockwise from 3 o'clock; number 1 under the pointer
spinning = False


def draw():
    cx = SIZE / 2
    cy = TOP + SIZE / 2
    r = SIZE / 2 - 10
    ctx.clearRect(0, 0, SIZE, SIZE + TOP + 20)
    for i, n in enumerate(numbers):
        a0 = angle + i * extent
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, r, a0, a0 + extent)
        ctx.closePath()
        ctx.fillStyle = COLORS[i % len(COLORS)]
        ctx.fill()
        ctx.strokeStyle = "white"
        ctx.lineWidth = 2
        ctx.stroke()
        mid = a0 + extent / 2
        ctx.fillStyle = "white"
        ctx.font = "bold 22px sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(str(n), cx + r * 0.75 * math.cos(mid), cy + r * 0.75 * math.sin(mid))
    ctx.beginPath()
    ctx.arc(cx, cy, 22, 0, 2 * math.pi)
    ctx.fillStyle = "#222"
    ctx.fill()
    ctx.strokeStyle = "white"
    ctx.lineWidth = 3
    ctx.stroke()
    # pointer at top
    ctx.beginPath()
    ctx.moveTo(cx - 14, 0)
    ctx.lineTo(cx + 14, 0)
    ctx.lineTo(cx, 34)
    ctx.closePath()
    ctx.fillStyle = "#222"
    ctx.fill()


def spin(event=None):
    global spinning
    if spinning:
        return
    spinning = True
    button.disabled = True
    result.innerText = "Spinning..."
    index = random.randint(0, count - 1)
    # angle that centres segment `index` under the pointer (top = -pi/2)
    end_mod = (-math.pi / 2 - (index + 0.5) * extent) % (2 * math.pi)
    start = angle
    total = (end_mod - start) % (2 * math.pi) + 2 * math.pi * random.randint(4, 6)
    t0 = [None]

    def step(now):
        global angle, spinning
        if t0[0] is None:
            t0[0] = now
        t = min((now - t0[0]) / SPIN_MS, 1)
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


button.addEventListener("click", create_proxy(spin))
canvas.addEventListener("click", create_proxy(spin))
button.disabled = False
result.innerText = "Click the wheel to spin!"
draw()
