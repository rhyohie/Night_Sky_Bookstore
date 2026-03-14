import tkinter as tk
import random
from typing import List

class Star:
    def __init__(self, width: int, height: int):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height * 0.6)
        self.size = random.randint(1, 3)
        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.05, 0.05)
        self.brightness = random.uniform(0.6, 1.0)
        self.phase = random.uniform(0, 2 * 3.14159)

class NightSkyCanvas(tk.Canvas):
    def __init__(self, parent, width: int = 900, height: int = 700, bg: str = "#0a0a23", star_count: int = 80, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.star_count = star_count
        self.stars: List[Star] = []
        self._running = False
        self._init_stars()
        self.bind("<Configure>", self._on_configure)
        self._start_animation()

    def _on_configure(self, event):
        try:
            self.width = max(1, event.width)
            self.height = max(1, event.height)
        except Exception: pass
        if len(self.stars) < max(10, int(self.star_count * 0.5)):
            self._init_stars()

    def _init_stars(self):
        self.stars = [Star(self.width, self.height) for _ in range(self.star_count)]
        for iid in getattr(self, "star_items", []):
            try: self.delete(iid)
            except Exception: pass
        self.star_items = []

    def draw_static(self):
        self.delete("static")
        mx, my = int(self.width * 0.12), int(self.height * 0.08)
        r = int(min(self.width, self.height) * 0.06)
        self.create_oval(mx, my, mx + 2 * r, my + 2 * r, fill="#FFD700", outline="", tags="static")
        self.create_oval(mx + int(r * 0.3), my, mx + 2 * r + int(r * 0.3), my + 2 * r, fill=self["bg"], outline="", tags="static")

    def _animate(self):
        if not self._running: return
        self.delete("star")
        for s in self.stars:
            s.x += s.vx
            s.y += s.vy
            s.phase += 0.1
            flick = (0.5 + 0.5 * (random.random())) * s.brightness
            if s.x < 0: s.x = self.width
            elif s.x > self.width: s.x = 0
            if s.y < 0: s.y = 0
            elif s.y > self.height * 0.6: s.y = self.height * 0.6
            size = max(1, s.size)
            intensity = int(200 * flick) + 55
            self.create_oval(s.x, s.y, s.x + size, s.y + size, fill=f"#{intensity:02x}{intensity:02x}{intensity:02x}", outline="", tags="star")
        self.draw_static()
        self.after(90, self._animate)

    def _start_animation(self):
        if self._running: return
        self._running = True
        self._animate()

def center_window(window, width: int, height: int):
    window.update_idletasks()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    x, y = int((sw - width) / 2), int((sh - height) / 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def make_draggable(window, widget):
    def start_move(event):
        window._drag_x = event.x
        window._drag_y = event.y
    def stop_move(event):
        window._drag_x = None
        window._drag_y = None
    def do_move(event):
        try: window.geometry(f"+{event.x_root - window._drag_x}+{event.y_root - window._drag_y}")
        except Exception: pass
    widget.bind("<Button-1>", start_move)
    widget.bind("<ButtonRelease-1>", stop_move)
    widget.bind("<B1-Motion>", do_move)