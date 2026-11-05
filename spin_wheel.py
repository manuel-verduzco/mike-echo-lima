"""Spin the Wheel: click the wheel, get a random number and its saying.

Pure standard-library Python (tkinter) - no installs needed.
Run with:  python spin_wheel.py
"""

import math
import random
import tkinter as tk

from phrases import PHRASES, deal

COLORS = ["#ef476f", "#ffd166", "#06d6a0", "#118ab2", "#9b5de5", "#f78c6b"]
SIZE = 460
MARGIN = 20
SPIN_MS = 4000
BG = "#14141c"
FG = "#f1f1f6"
FRAME_MS = 16


def pick_number(count: int, rng: random.Random = random) -> int:
    """Return a random wheel number in 1..count."""
    return rng.randint(1, count)


def target_angle(number: int, count: int) -> float:
    """Wheel rotation (degrees, tkinter convention) that puts the centre of
    segment `number` under the pointer at the top (90 degrees)."""
    extent = 360 / count
    return (90 - (number - 0.5) * extent) % 360


def number_at_pointer(angle: float, count: int) -> int:
    """Which number is under the top pointer for a given wheel rotation."""
    extent = 360 / count
    return int(((90 - angle) % 360) // extent) + 1


class WheelApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.numbers = deal()
        self.count = len(self.numbers)
        self.angle = 90 - 0.5 * (360 / self.count)  # start on number 1
        self.spinning = False

        root.title("Spin the Wheel")
        root.resizable(False, False)
        root.configure(bg=BG)

        self.canvas = tk.Canvas(root, width=SIZE, height=SIZE + 10,
                                highlightthickness=0, bg=BG)
        self.canvas.pack(padx=10, pady=(10, 0))
        self.canvas.bind("<Button-1>", lambda _e: self.spin())

        self.result = tk.Label(root, text="Click the wheel to spin!",
                               font=("Segoe UI", 14, "bold"),
                               wraplength=SIZE, height=4, bg=BG, fg=FG)
        self.result.pack(padx=10)

        self.button = tk.Button(root, text="SPIN", font=("Segoe UI", 12, "bold"),
                                command=self.spin, width=12,
                                bg="#1b9ac4", fg="white", relief="flat")
        self.button.pack(pady=(0, 12))

        self.draw()

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")
        box = (MARGIN, MARGIN + 10, SIZE - MARGIN, SIZE - MARGIN + 10)
        cx = cy = SIZE / 2
        cy += 10
        radius = (SIZE - 2 * MARGIN) / 2
        extent = 360 / self.count

        for i, number in enumerate(self.numbers):
            start = self.angle + i * extent
            c.create_arc(*box, start=start, extent=extent, fill=COLORS[i % len(COLORS)],
                         outline="white", width=2)
            mid = math.radians(start + extent / 2)
            tx = cx + radius * 0.75 * math.cos(mid)
            ty = cy - radius * 0.75 * math.sin(mid)
            c.create_text(tx, ty, text=str(number), font=("Segoe UI", 16, "bold"),
                          fill="white")

        c.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, fill=BG, outline="white", width=3)
        # pointer at the top
        c.create_polygon(cx - 14, 0, cx + 14, 0, cx, 34, fill="white", outline="white", width=2)

    def spin(self) -> None:
        if self.spinning:
            return
        self.spinning = True
        self.button.config(state="disabled")
        self.result.config(text="Spinning...")

        self.numbers = deal()  # new random arrangement of numbers on the wheel
        number = pick_number(self.count)
        index = number - 1
        # Rotate clockwise (decreasing angle) a few full turns, then settle.
        start = self.angle
        end_mod = target_angle(index + 1, self.count)
        extra = (start - end_mod) % 360 + 360 * random.randint(4, 6)
        self.animate(start, extra, 0, number)

    def animate(self, start: float, total: float, elapsed: int, number: int) -> None:
        t = min(elapsed / SPIN_MS, 1.0)
        eased = 1 - (1 - t) ** 3  # ease-out cubic
        self.angle = (start - total * eased) % 360
        self.draw()
        if t < 1.0:
            self.root.after(FRAME_MS, self.animate, start, total, elapsed + FRAME_MS, number)
        else:
            self.finish(number)

    def finish(self, number: int) -> None:
        key = self.numbers[number - 1]
        self.result.config(text=f"#{key}\n{PHRASES[key]}")
        self.spinning = False
        self.button.config(state="normal")


def main() -> None:
    root = tk.Tk()
    WheelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
