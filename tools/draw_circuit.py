import matplotlib

matplotlib.use("Agg")

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

OUT = Path(__file__).resolve().parent.parent / "images"
PARTS = OUT / "parts"
SCALE = 0.12  # inches per drawing unit, keeps fonts the same size in every image

COL = {
    "vbat": "#d62728",
    "v33": "#ff7f0e",
    "gnd": "#333333",
    "sda": "#1f77b4",
    "scl": "#17becf",
    "touch": "#c8792b",
    "bump": "#8c564b",
    "analog": "#e377c2",
    "en": "#6b6b6b",
}
AUDIO = ["#2ca02c", "#1b7a1b", "#5fcf5f"]
MOTOR = ["#9467bd", "#6a3d9a", "#b58ce0", "#4b2a73"]
HEAD = "#1f4e79"

XIAO_PINS = [
    ("5V", ""), ("3V3", ""), ("GND", ""),
    ("D0", "GPIO1"), ("D1", "GPIO2"), ("D2", "GPIO3"), ("D3", "GPIO4"),
    ("D4", "GPIO5"), ("D5", "GPIO6"), ("D6", "GPIO43"), ("D7", "GPIO44"),
    ("D8", "GPIO7"), ("D9", "GPIO8"), ("D10", "GPIO9"),
    ("BAT+", "back pad"), ("BAT−", "back pad"),
]
LEFT_ROW = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]
RIGHT_ROW = ["5V", "GND", "3V3", "D10", "D9", "D8", "D7"]


# ---------------------------------------------------------------- primitives

def setup(w, h):
    fig = plt.figure(figsize=(w * SCALE, h * SCALE))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def subpanel(fig, W, H, x, y, w, h):
    ax = fig.add_axes([x / W, y / H, w / W, h / H])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight", pad_inches=0.15, facecolor="white")
    plt.close(fig)


def box(ax, x, y, w, h, title, fc="#f5f5f5", ec="#222", fs=10, title_y=None, ls="-"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0,rounding_size=1.2",
            fc=fc, ec=ec, lw=1.6, zorder=2, ls=ls,
        )
    )
    if title:
        ty = y + h - 1.2 if title_y is None else title_y
        ax.text(x + w / 2, ty, title, ha="center", va="top", fontsize=fs,
                weight="bold", zorder=5, linespacing=1.15)


def text(ax, x, y, s, ha="left", va="center", fs=8.5, color="#111", weight="normal",
         family=None, z=5):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=color, weight=weight,
            zorder=z, linespacing=1.25, family=family)


def dot(ax, x, y, color="#111"):
    ax.add_patch(Circle((x, y), 0.55, color=color, zorder=6))


def flag(ax, x, y, s, color, side="left", fs=8):
    ha = {"left": "right", "right": "left", "up": "center", "down": "center"}[side]
    va = {"left": "center", "right": "center", "up": "bottom", "down": "top"}[side]
    dx = {"left": -0.6, "right": 0.6, "up": 0, "down": 0}[side]
    dy = {"left": 0, "right": 0, "up": 0.6, "down": -0.6}[side]
    ax.text(x + dx, y + dy, s, ha=ha, va=va, fontsize=fs, color="white",
            weight="bold", zorder=7,
            bbox=dict(boxstyle="round,pad=0.25", fc=color, ec=color))


def gnd(ax, x, y, color=COL["gnd"]):
    ax.plot([x, x], [y, y - 1.2], color=color, lw=1.8, zorder=3)
    for i, half in enumerate([1.6, 1.0, 0.4]):
        yy = y - 1.2 - i * 0.55
        ax.plot([x - half, x + half], [yy, yy], color=color, lw=1.8, zorder=3)


def _label(ax, p1, p2, label, side, fs, off):
    if not label:
        return
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    if abs(p2[0] - p1[0]) < abs(p2[1] - p1[1]):
        if side > 0:
            ax.text(mx + off, my, label, ha="left", va="center", fontsize=fs, zorder=5,
                    linespacing=1.15)
        else:
            ax.text(mx - off, my, label, ha="right", va="center", fontsize=fs, zorder=5,
                    linespacing=1.15)
    else:
        if side > 0:
            ax.text(mx, my + off, label, ha="center", va="bottom", fontsize=fs, zorder=5,
                    linespacing=1.15)
        else:
            ax.text(mx, my - off, label, ha="center", va="top", fontsize=fs, zorder=5,
                    linespacing=1.15)


def resistor(ax, x1, y1, x2, y2, label=None, color="#111", side=1, fs=8):
    p1, p2 = np.array([x1, y1], float), np.array([x2, y2], float)
    d = p2 - p1
    length = np.linalg.norm(d)
    u = d / length
    n = np.array([-u[1], u[0]])
    lead = length * 0.22
    zig = length - 2 * lead
    pts = [p1, p1 + u * lead]
    for i in range(6):
        t = lead + zig * (i + 0.5) / 6
        pts.append(p1 + u * t + n * (0.9 if i % 2 == 0 else -0.9))
    pts += [p1 + u * (length - lead), p2]
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=1.8, zorder=4)
    _label(ax, p1, p2, label, side, fs, 1.6)


def cap(ax, x1, y1, x2, y2, label=None, side=1, fs=8, polar=False, color="#111"):
    p1, p2 = np.array([x1, y1], float), np.array([x2, y2], float)
    d = p2 - p1
    u = d / np.linalg.norm(d)
    n = np.array([-u[1], u[0]])
    m = (p1 + p2) / 2
    a, b = m - u * 0.4, m + u * 0.4
    half = 1.6
    ax.plot(*zip(p1, a), color=color, lw=1.8, zorder=4)
    ax.plot(*zip(b, p2), color=color, lw=1.8, zorder=4)
    ax.plot(*zip(a - n * half, a + n * half), color=color, lw=2.4, zorder=4)
    if polar:
        R = 2.4
        c = b + u * R
        base = np.arctan2(-u[1], -u[0])
        t = np.linspace(base - 0.62, base + 0.62, 20)
        ax.plot(c[0] + R * np.cos(t), c[1] + R * np.sin(t), color=color, lw=2.4, zorder=4)
        plus = a - u * 0.9 + n * (half + 0.2)
        ax.text(plus[0], plus[1], "+", ha="center", va="center", fontsize=7.5,
                weight="bold", zorder=5)
    else:
        ax.plot(*zip(b - n * half, b + n * half), color=color, lw=2.4, zorder=4)
    _label(ax, p1, p2, label, side, fs, 2.2)


def diode(ax, pa, pk, led=False, color="#111", s=1.5):
    pa, pk = np.array(pa, float), np.array(pk, float)
    d = pk - pa
    u = d / np.linalg.norm(d)
    n = np.array([-u[1], u[0]])
    m = (pa + pk) / 2
    b = m - u * s * 0.6
    t = m + u * s * 0.6
    ax.plot(*zip(pa, b), color=color, lw=1.8, zorder=4)
    ax.plot(*zip(t, pk), color=color, lw=1.8, zorder=4)
    ax.add_patch(Polygon([b + n * s, b - n * s, t], closed=True, fc=color, ec=color, zorder=5))
    ax.plot(*zip(t + n * s, t - n * s), color=color, lw=2.2, zorder=5)
    if led:
        for k in (-0.7, 0.5):
            st = m + n * (s + 0.3) + u * k
            en = st + n * 1.7 + u * 0.6
            ax.annotate("", xy=en, xytext=st, zorder=6,
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0,
                                        mutation_scale=7))


def npn(ax, x, y, r=3.5):
    ax.add_patch(Circle((x, y), r, fc="white", ec="#111", lw=1.6, zorder=4))
    bx = x - r * 0.35
    ax.plot([bx, bx], [y - r * 0.5, y + r * 0.5], color="#111", lw=2.6, zorder=5)
    base = (x - r - 2, y)
    ax.plot([base[0], bx], [y, y], color="#111", lw=1.8, zorder=5)
    c_end = (x + r * 0.45, y + r * 0.85)
    e_end = (x + r * 0.45, y - r * 0.85)
    ax.plot([bx, c_end[0]], [y + r * 0.2, c_end[1]], color="#111", lw=1.8, zorder=5)
    ax.plot([bx, e_end[0]], [y - r * 0.2, e_end[1]], color="#111", lw=1.8, zorder=5)
    mid = ((bx + e_end[0]) / 2, (y - r * 0.2 + e_end[1]) / 2)
    ax.annotate("", xy=e_end, xytext=mid, zorder=6,
                arrowprops=dict(arrowstyle="-|>", color="#111", lw=1.5))
    collector = (c_end[0], y + r + 2)
    emitter = (e_end[0], y - r - 2)
    ax.plot([c_end[0]] * 2, [c_end[1], collector[1]], color="#111", lw=1.8, zorder=5)
    ax.plot([e_end[0]] * 2, [e_end[1], emitter[1]], color="#111", lw=1.8, zorder=5)
    return base, collector, emitter


def photo_npn(ax, xl, y, r=2.6):
    """Phototransistor with collector and emitter leads on the vertical line x = xl."""
    cx = xl - r * 0.45
    ax.add_patch(Circle((cx, y), r, fc="white", ec="#111", lw=1.5, zorder=4))
    bx = cx - r * 0.35
    ax.plot([bx, bx], [y - r * 0.5, y + r * 0.5], color="#111", lw=2.4, zorder=5)
    c_end, e_end = (xl, y + r * 0.85), (xl, y - r * 0.85)
    ax.plot([bx, c_end[0]], [y + r * 0.2, c_end[1]], color="#111", lw=1.6, zorder=5)
    ax.plot([bx, e_end[0]], [y - r * 0.2, e_end[1]], color="#111", lw=1.6, zorder=5)
    mid = ((bx + e_end[0]) / 2, (y - r * 0.2 + e_end[1]) / 2)
    ax.annotate("", xy=e_end, xytext=mid, zorder=6,
                arrowprops=dict(arrowstyle="-|>", color="#111", lw=1.3, mutation_scale=9))
    top, bot = (xl, y + r + 1.5), (xl, y - r - 1.5)
    ax.plot([xl, xl], [c_end[1], top[1]], color="#111", lw=1.6, zorder=5)
    ax.plot([xl, xl], [e_end[1], bot[1]], color="#111", lw=1.6, zorder=5)
    return top, bot


def switch(ax, x1, x2, y, color):
    ax.plot([x1 + 0.4, x2 - 0.3], [y + 0.3, y + 2.6], color=color, lw=2.2, zorder=4)
    for x in (x1, x2):
        ax.add_patch(Circle((x, y), 0.5, fc="white", ec=color, lw=1.6, zorder=5))


def motor(ax, x, y, r, label, fs=8.5):
    ax.add_patch(Circle((x, y), r, fc="#f3ecfb", ec=MOTOR[1], lw=1.8, zorder=4))
    ax.text(x, y, "M", ha="center", va="center", fontsize=13, weight="bold",
            color=MOTOR[1], zorder=5)
    text(ax, x + r + 1.2, y, label, fs=fs)


def speaker(ax, x, y, color="#111"):
    ax.add_patch(Rectangle((x, y - 2), 2.6, 4, fc="white", ec=color, lw=1.6, zorder=4))
    ax.add_patch(Polygon([(x + 2.6, y - 2), (x + 2.6, y + 2), (x + 6.4, y + 4.4),
                          (x + 6.4, y - 4.4)], closed=True, fc="white", ec=color, lw=1.6,
                         zorder=4))


def cell(ax, x, y_neg, y_pos, color=COL["vbat"]):
    ym = (y_neg + y_pos) / 2
    ax.plot([x, x], [y_pos, ym + 0.6], color=color, lw=2.2, zorder=4)
    ax.plot([x, x], [ym - 0.6, y_neg], color=COL["gnd"], lw=2.2, zorder=4)
    ax.plot([x - 2.4, x + 2.4], [ym + 0.6, ym + 0.6], color="#111", lw=2.2, zorder=5)
    ax.plot([x - 1.3, x + 1.3], [ym - 0.6, ym - 0.6], color="#111", lw=3.6, zorder=5)
    ax.text(x + 3.0, ym + 1.7, "+", fontsize=10, weight="bold", color=color, zorder=5,
            ha="center", va="center")


class Net:
    """Orthogonal wires that hop over earlier wires they cross."""

    def __init__(self, ax, r=0.75):
        self.ax, self.r, self.h, self.v = ax, r, [], []

    def wire(self, pts, color, lw=2.2):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if abs(y1 - y2) < 1e-6 and abs(x1 - x2) > 1e-6:
                self._horizontal(x1, x2, y1, color, lw)
            elif abs(x1 - x2) < 1e-6 and abs(y1 - y2) > 1e-6:
                self._vertical(x1, y1, y2, color, lw)
            else:
                self.ax.plot([x1, x2], [y1, y2], color=color, lw=lw, zorder=3,
                             solid_capstyle="round")

    def _seg(self, xs, ys, color, lw):
        self.ax.plot(xs, ys, color=color, lw=lw, zorder=3, solid_capstyle="round")

    def _horizontal(self, x1, x2, y, color, lw):
        a, b = sorted((x1, x2))
        r = self.r
        hits = sorted(vx for vx, lo, hi in self.v
                      if a + 1.5 * r < vx < b - 1.5 * r and lo + 0.05 < y < hi - 0.05)
        cur = a
        t = np.linspace(np.pi, 0, 24)
        for xc in hits:
            self._seg([cur, xc - r], [y, y], color, lw)
            self._seg(xc + r * np.cos(t), y + r * np.sin(t), color, lw)
            cur = xc + r
        self._seg([cur, b], [y, y], color, lw)
        self.h.append((y, a, b))

    def _vertical(self, x, y1, y2, color, lw):
        a, b = sorted((y1, y2))
        r = self.r
        hits = sorted(hy for hy, lo, hi in self.h
                      if a + 1.5 * r < hy < b - 1.5 * r and lo + 0.05 < x < hi - 0.05)
        cur = a
        t = np.linspace(-np.pi / 2, np.pi / 2, 24)
        for yc in hits:
            self._seg([x, x], [cur, yc - r], color, lw)
            self._seg(x + r * np.cos(t), yc + r * np.sin(t), color, lw)
            cur = yc + r
        self._seg([x, x], [cur, b], color, lw)
        self.v.append((x, a, b))


def pin_row(ax, side, edge, items, fs=7.8, stub=3):
    """Pins on one edge of a module. items: (label, position along the edge)."""
    out = {}
    for label, pos in items:
        if side == "left":
            ax.plot([edge - stub, edge], [pos, pos], color="#444", lw=2.2, zorder=3)
            text(ax, edge + 0.9, pos, label, fs=fs, weight="bold")
            out[label] = (edge - stub, pos)
        elif side == "right":
            ax.plot([edge, edge + stub], [pos, pos], color="#444", lw=2.2, zorder=3)
            text(ax, edge - 0.9, pos, label, ha="right", fs=fs, weight="bold")
            out[label] = (edge + stub, pos)
        elif side == "top":
            ax.plot([pos, pos], [edge, edge + stub], color="#444", lw=2.2, zorder=3)
            text(ax, pos, edge - 1.2, label, ha="center", fs=fs, weight="bold")
            out[label] = (pos, edge + stub)
        else:
            ax.plot([pos, pos], [edge - stub, edge], color="#444", lw=2.2, zorder=3)
            text(ax, pos, edge + 1.2, label, ha="center", fs=fs, weight="bold")
            out[label] = (pos, edge - stub)
    return out


# ---------------------------------------------------------------- XIAO helpers

def xiao_symbol(ax, used, x0=4, x1=26, top=86, bottom=8):
    box(ax, x0, bottom, x1 - x0, top - bottom, "Seeed Studio XIAO\nESP32-S3 Sense",
        fc="#e8f1fb", ec=HEAD, fs=9, title_y=top - 0.8)
    pins = {}
    for i, (name, gpio) in enumerate(XIAO_PINS):
        y = 78 - i * 4.4
        on = name in used
        label = f"{name}  {gpio}" if gpio else name
        text(ax, x1 - 0.9, y, label, ha="right", fs=7.8,
             weight="bold" if on else "normal", color="#111" if on else "#9a9a9a")
        if on:
            ax.plot([x1, x1 + 3], [y, y], color=used[name], lw=2.6, zorder=3)
        pins[name] = (x1 + 3, y)
    return pins


def mini_xiao(ax, x, y, used):
    w, h = 16, 26
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1",
                                fc="#e8f1fb", ec=HEAD, lw=1.3, zorder=3))
    ax.add_patch(Rectangle((x + 5, y + h), 6, 2, fc="#c9c9c9", ec="#555", lw=1, zorder=3))
    text(ax, x + w / 2, y + h + 1, "USB-C", ha="center", fs=5.5)
    for i, name in enumerate(LEFT_ROW):
        yy = y + h - 3.5 - i * 3.3
        on = name in used
        ax.add_patch(Circle((x, yy), 0.85, fc=used.get(name, "white"),
                            ec="#333" if on else "#aaa", lw=1, zorder=4))
        text(ax, x + 1.4, yy, name, fs=6.3, weight="bold" if on else "normal",
             color="#111" if on else "#9a9a9a")
    for i, name in enumerate(RIGHT_ROW):
        yy = y + h - 3.5 - i * 3.3
        on = name in used
        ax.add_patch(Circle((x + w, yy), 0.85, fc=used.get(name, "white"),
                            ec="#333" if on else "#aaa", lw=1, zorder=4))
        text(ax, x + w - 1.4, yy, name, ha="right", fs=6.3,
             weight="bold" if on else "normal", color="#111" if on else "#9a9a9a")
    text(ax, x + w / 2, y - 1.4, "top view, USB up", ha="center", fs=6.3, color="#555")


def where_lines(used):
    lines = []
    for name, _ in XIAO_PINS:
        if name not in used:
            continue
        if name in LEFT_ROW:
            lines.append(f"{name}: left row, pin {LEFT_ROW.index(name) + 1} from the USB end")
        elif name in RIGHT_ROW:
            lines.append(f"{name}: right row, pin {RIGHT_ROW.index(name) + 1} from the USB end")
        elif name == "BAT+":
            lines.append("BAT+: pad on the back, the one farther from USB")
        else:
            lines.append("BAT−: pad on the back, the one nearer USB")
    return lines


def info_panel(ax, used, sections, x=117, top=90, bottom=3, w=61):
    ax.add_patch(FancyBboxPatch((x, bottom), w, top - bottom,
                                boxstyle="round,pad=0,rounding_size=1.2",
                                fc="#fafafa", ec="#b5b5b5", lw=1.2, zorder=1))
    y = top - 2.4
    text(ax, x + 2, y, "Where on the board", fs=10, weight="bold", color=HEAD)
    mini_xiao(ax, x + 3, y - 30, used)
    ty = y - 3.6
    for line in where_lines(used):
        for part in textwrap.wrap(line, 52):
            text(ax, x + 23, ty, part, fs=7.8)
            ty -= 1.35
    y -= 34.5
    for head, lines in sections:
        text(ax, x + 2, y, head, fs=9.5, weight="bold", color=HEAD)
        y -= 2.0
        for line in lines:
            mono = line.startswith("|")
            body = line[1:] if mono else line
            if mono:
                text(ax, x + 3, y, body, fs=7.6, family="DejaVu Sans Mono")
                y -= 1.3
                continue
            bullet = body.startswith("- ")
            body = body[2:] if bullet else body
            wrapped = textwrap.wrap(body, 98 if bullet else 100)
            for i, part in enumerate(wrapped):
                prefix = "•  " if bullet and i == 0 else ("   " if bullet else "")
                text(ax, x + 2.6, y, prefix + part, fs=7.9)
                y -= 1.3
        y -= 0.9
    if y < bottom:
        print(f"  warning: info panel overflows by {bottom - y:.1f} units")


def part_frame(title, subtitle, used):
    fig, ax = setup(180, 100)
    text(ax, 90, 97.6, title, ha="center", fs=17, weight="bold")
    text(ax, 90, 94.2, subtitle, ha="center", fs=9.5, color="#444")
    pins = xiao_symbol(ax, used)
    return fig, ax, pins, Net(ax)


# ---------------------------------------------------------------- full wiring

def figure_wiring():
    fig, ax = setup(200, 140)
    net = Net(ax)
    text(ax, 100, 137, "Bob — full wiring to the Seeed Studio XIAO ESP32-S3 Sense",
         ha="center", fs=18, weight="bold")
    text(ax, 100, 133.2,
         "All signals are 3.3 V.  Flags with the same name (VBAT, 3V3, AIN1, AIN2, LED_K, AMP_EN, "
         "MOTOR_EN, FAULT, VBAT_SENSE) are the same wire.  Dot = joined.  Hop = crossing, not joined.",
         ha="center", fs=10, color="#444")

    # XIAO
    box(ax, 84, 44, 32, 52, "Seeed Studio\nXIAO ESP32-S3 Sense", fc="#e8f1fb",
        ec=HEAD, fs=11, title_y=95)
    ax.add_patch(Rectangle((95, 96), 10, 3, fc="#c9c9c9", ec="#555", zorder=2))
    text(ax, 100, 97.5, "USB-C", ha="center", fs=7)
    left = [("D0", "GPIO1", 90), ("D1", "GPIO2", 83), ("D2", "GPIO3", 76),
            ("D3", "GPIO4", 69), ("D4", "GPIO5", 62), ("D5", "GPIO6", 55),
            ("D6", "GPIO43", 48)]
    right = [("5V", "", 90), ("GND", "", 83), ("3V3", "", 76), ("D10", "GPIO9", 69),
             ("D9", "GPIO8", 62), ("D8", "GPIO7", 55), ("D7", "GPIO44", 48)]
    for name, gpio, y in left:
        ax.plot([84, 80], [y, y], color=HEAD, lw=2.6, zorder=3)
        text(ax, 85.2, y, f"{name}  {gpio}", fs=8.5, weight="bold")
    for name, gpio, y in right:
        ax.plot([116, 120], [y, y], color=HEAD, lw=2.6, zorder=3)
        text(ax, 114.8, y, f"{gpio}  {name}".strip(), ha="right", fs=8.5, weight="bold")
    text(ax, 100, 70,
         "Sense board on top:\ncamera + PDM mic\n(mic on D11 / D12, leave)\n"
         "microSD empty, J3 cut\nfit the antenna",
         ha="center", fs=8, color=HEAD)

    # battery pads
    text(ax, 94, 45.8, "BAT−", ha="center", fs=7.5, weight="bold")
    text(ax, 106, 45.8, "BAT+", ha="center", fs=7.5, weight="bold")
    net.wire([(94, 44), (94, 40)], COL["gnd"])
    gnd(ax, 94, 40)
    net.wire([(106, 44), (106, 40)], COL["vbat"])
    flag(ax, 106, 40, "VBAT", COL["vbat"], side="down")

    # right-side power pins
    text(ax, 121, 90, "unused", fs=7.5, color="#777")
    net.wire([(120, 83), (122, 83)], COL["gnd"])
    gnd(ax, 122, 83)
    net.wire([(120, 76), (121, 76)], COL["v33"])
    flag(ax, 121, 76, "3V3", COL["v33"], side="right")
    text(ax, 126.5, 79.6, "C7 10 µF\nC8 100 nF", fs=7, color="#555")

    # touch pad on D0, through R13
    box(ax, 84, 102, 20, 9, "Copper touch pad", fc="#f6d3ad", ec=COL["touch"], fs=9)
    text(ax, 94, 105, "under the shell, away\nfrom the antenna", ha="center", fs=7.5)
    net.wire([(80, 90), (78, 90), (78, 94)], COL["touch"])
    resistor(ax, 78, 94, 78, 102, "R13\n470 Ω", side=1, fs=7)
    net.wire([(78, 102), (78, 106.5), (84, 106.5)], COL["touch"])

    # bumper on D1, R14 pull-up, C14 filter
    box(ax, 84, 113, 24, 11, "2× bumper microswitch", fc="#efe2dc", ec=COL["bump"], fs=9)
    text(ax, 96, 117.2, "in parallel, COM to GND\npressed = LOW", ha="center", fs=7.5)
    net.wire([(80, 83), (75, 83), (75, 118.5), (84, 118.5)], COL["bump"])
    net.wire([(108, 118.5), (111, 118.5)], COL["gnd"])
    gnd(ax, 111, 118.5)
    dot(ax, 75, 100, COL["bump"])
    resistor(ax, 75, 100, 66, 100, "R14 10 kΩ", fs=7)
    flag(ax, 66, 100, "3V3", COL["v33"])
    dot(ax, 75, 92, COL["bump"])
    cap(ax, 75, 92, 69, 92, "C14 100 nF", fs=7)
    gnd(ax, 69, 92)

    # left motor inputs leave as flags
    net.wire([(80, 76), (79, 76)], MOTOR[0])
    flag(ax, 79, 76, "AIN1", MOTOR[0], fs=7.5)
    net.wire([(80, 69), (79, 69)], MOTOR[1])
    flag(ax, 79, 69, "AIN2", MOTOR[1], fs=7.5)

    # I2C bus
    net.wire([(66, 63), (66, 19)], COL["sda"])
    net.wire([(63, 59), (63, 15)], COL["scl"])
    net.wire([(80, 62), (66, 62)], COL["sda"])
    net.wire([(80, 55), (63, 55)], COL["scl"])
    dot(ax, 66, 62, COL["sda"])
    dot(ax, 63, 55, COL["scl"])
    text(ax, 66.8, 40, "SDA", fs=8, color=COL["sda"], weight="bold")
    text(ax, 59.5, 30, "SCL", fs=8, color=COL["scl"], weight="bold")

    # OLED
    box(ax, 36, 56, 20, 14, "OLED 0.96″\nSSD1306 · 0x3C", fc="#f2f2f2", fs=9, title_y=69)
    text(ax, 55, 63, "SDA", ha="right", fs=7.5, weight="bold")
    text(ax, 55, 59, "SCL", ha="right", fs=7.5, weight="bold")
    text(ax, 37, 63, "VCC", fs=7.5, weight="bold")
    text(ax, 37, 59, "GND", fs=7.5, weight="bold")
    net.wire([(56, 63), (66, 63)], COL["sda"])
    net.wire([(56, 59), (63, 59)], COL["scl"])
    net.wire([(36, 63), (33, 63)], COL["v33"])
    flag(ax, 33, 63, "3V3", COL["v33"])
    net.wire([(36, 59), (33, 59)], COL["gnd"])
    gnd(ax, 33, 59)

    # ADS1115
    box(ax, 36, 32, 20, 20, "ADS1115 ADC\naddr 0x48", fc="#f2f2f2", fs=9, title_y=51)
    text(ax, 55, 48, "SDA", ha="right", fs=7.5, weight="bold")
    text(ax, 55, 44, "SCL", ha="right", fs=7.5, weight="bold")
    net.wire([(56, 48), (66, 48)], COL["sda"])
    dot(ax, 66, 48, COL["sda"])
    net.wire([(56, 44), (63, 44)], COL["scl"])
    dot(ax, 63, 44, COL["scl"])
    for label, y in (("AIN0", 48), ("AIN1", 44.5), ("AIN2", 41), ("AIN3", 37.5)):
        text(ax, 37, y, label, fs=7.5, weight="bold")
    for label, x in (("VDD", 40), ("GND", 46), ("ADDR", 52)):
        text(ax, x, 33.2, label, ha="center", fs=6.5, weight="bold")
    net.wire([(40, 32), (40, 29.5)], COL["v33"])
    flag(ax, 40, 29.5, "3V3", COL["v33"], side="down", fs=7)
    net.wire([(46, 32), (46, 29.5)], COL["gnd"])
    gnd(ax, 46, 29.5)
    net.wire([(52, 32), (52, 29.5)], COL["gnd"])
    gnd(ax, 52, 29.5)
    net.wire([(36, 37.5), (35, 37.5)], COL["vbat"])
    flag(ax, 35, 37.5, "VBAT_SENSE", COL["vbat"], fs=7)

    # edge sensors
    box(ax, 3, 39.5, 21, 16, "3× Sharp GP2S700HCP\nedge sensors, face down",
        fc="#fbe8f4", ec=COL["analog"], fs=8.5)
    text(ax, 11, 45, "LEDs: LED_K\nto PCF P0\ndetail: sheet 04", ha="center", fs=6.8,
         color="#555")
    for label, y in (("Left", 48), ("Right", 44.5), ("Center", 41)):
        text(ax, 23, y, label, ha="right", fs=7.5, weight="bold")
        net.wire([(24, y), (36, y)], COL["analog"])

    # PCF8574
    box(ax, 36, 5, 20, 19, "PCF8574 · 0x20", fc="#f2f2f2", fs=9, title_y=23.4)
    text(ax, 47, 8.2, "VCC 3V3 · GND\nA0–A2 → GND", ha="center", fs=6.5)
    text(ax, 55, 19, "SDA", ha="right", fs=7.5, weight="bold")
    text(ax, 55, 15, "SCL", ha="right", fs=7.5, weight="bold")
    net.wire([(56, 19), (66, 19)], COL["sda"])
    net.wire([(56, 15), (63, 15)], COL["scl"])
    for label, y, flag_name, color in (("P0", 19, "LED_K", COL["analog"]),
                                       ("P1", 15.5, "AMP_EN", COL["en"]),
                                       ("P2", 12, "MOTOR_EN", COL["en"]),
                                       ("P3", 8.5, "FAULT", COL["en"])):
        text(ax, 37, y, label, fs=7.5, weight="bold")
        net.wire([(36, y), (33, y)], color)
        flag(ax, 33, y, flag_name, color, fs=7)
    text(ax, 16, 3.2, "P0 sinks the sensor LEDs directly.\nP1, P2 through BC547 safe "
         "switches Q1, Q2.\nP3 reads the driver fault (R21 pull-up).",
         ha="center", fs=7, color="#555")

    # amplifier below the XIAO
    box(ax, 86, 12, 28, 20, "MAX98357A I2S amp", fc="#e6f5e6", ec=AUDIO[1], fs=9,
        title_y=31.2)
    for label, y in (("BCLK", 27), ("SD", 22), ("GND", 17)):
        text(ax, 87, y, label, fs=7.5, weight="bold")
    for label, y in (("LRC", 27), ("DIN", 22), ("VIN", 17)):
        text(ax, 113, y, label, ha="right", fs=7.5, weight="bold")
    text(ax, 100, 21, "GAIN: R22 100 kΩ\nto VIN (3 dB)\nVIN: C5 + C6", ha="center", fs=6.5)
    net.wire([(80, 48), (80, 27), (86, 27)], AUDIO[0])
    net.wire([(120, 48), (120, 27), (114, 27)], AUDIO[1])
    net.wire([(120, 69), (124, 69), (124, 22), (114, 22)], AUDIO[2])
    net.wire([(86, 22), (83, 22)], COL["en"])
    flag(ax, 83, 22, "AMP_EN", COL["en"], fs=7)
    net.wire([(86, 17), (83, 17)], COL["gnd"])
    gnd(ax, 83, 17)
    net.wire([(114, 17), (117, 17)], COL["vbat"])
    flag(ax, 117, 17, "VBAT", COL["vbat"], side="right", fs=7)
    text(ax, 96, 13.2, "OUT+", ha="center", fs=7, weight="bold")
    text(ax, 104, 13.2, "OUT−", ha="center", fs=7, weight="bold")
    net.wire([(96, 12), (96, 8)], AUDIO[1])
    net.wire([(104, 12), (104, 8)], AUDIO[1])
    box(ax, 90, 2, 20, 6, "", fc="#ffffff", ec=AUDIO[1])
    text(ax, 100, 5, "Speaker 4 Ω, ~1 W", ha="center", fs=8, weight="bold")

    # motor driver
    net.wire([(116, 62), (136, 62), (136, 34), (140, 34)], MOTOR[3])
    net.wire([(116, 55), (132, 55), (132, 28), (140, 28)], MOTOR[2])
    box(ax, 140, 20, 26, 26, "DRV8833\nmotor driver", fc="#f3ecfb", ec=MOTOR[1],
        fs=10, title_y=40)
    text(ax, 141, 34, "BIN2", fs=7.5, weight="bold")
    text(ax, 141, 28, "BIN1", fs=7.5, weight="bold")
    for label, x, color in (("AIN1", 146, MOTOR[0]), ("AIN2", 152, MOTOR[1])):
        text(ax, x, 44.6, label, ha="center", fs=7, weight="bold")
        net.wire([(x, 46), (x, 49)], color)
        flag(ax, x, 49, label, color, side="up", fs=7)
    for label, y in (("AO1", 40), ("AO2", 36), ("BO1", 28), ("BO2", 24)):
        text(ax, 165, y, label, ha="right", fs=7.5, weight="bold")
    bottoms = (("VM", 143, "VBAT", COL["vbat"]), ("GND", 149, None, COL["gnd"]),
               ("SLP", 155, "MOTOR_EN", COL["en"]), ("FLT", 163, "FAULT", COL["en"]))
    for label, x, name, color in bottoms:
        text(ax, x, 21.4, label, ha="center", fs=7, weight="bold")
        net.wire([(x, 20), (x, 17)], color)
        if name:
            flag(ax, x, 17, name, color, side="down", fs=6.5)
        else:
            gnd(ax, x, 17)
    for y in (40, 36, 28, 24):
        net.wire([(166, y), (178.5, y)], MOTOR[1])
    cap(ax, 172, 40, 172, 36, None)
    cap(ax, 172, 28, 172, 24, None)
    text(ax, 174, 38, "C3", fs=7)
    text(ax, 174, 26, "C4", fs=7)
    motor(ax, 182.5, 38, 4.5, "Left motor\nN12 5 V 57 RPM")
    motor(ax, 182.5, 26, 4.5, "Right motor\nN12 5 V 57 RPM")
    notes = [
        "• R3–R6 100 kΩ from AIN1, AIN2, BIN1, BIN2 to GND",
        "• C1 1000 µF + C2 100 nF from VM to GND, at the driver",
        "• C3, C4 100 nF across each motor's two terminals",
        "• The module has no logic VCC pin. VM is its only supply",
        "• Wrong wheel direction: swap that motor's two leads",
    ]
    for i, line in enumerate(notes):
        text(ax, 140, 12 - i * 2.5, line, fs=7.8)

    # power
    ax.add_patch(FancyBboxPatch((138, 72), 60, 54, boxstyle="round,pad=0,rounding_size=1.5",
                                fc="#fff6f6", ec=COL["vbat"], lw=1.4, zorder=1))
    text(ax, 168, 123.5, "Power — one protected 18650", ha="center", fs=11, weight="bold")
    box(ax, 143, 82, 14, 22, "Protected\n18650\n~2500 mAh", fc="#ffffff", ec=COL["vbat"],
        fs=8.5, title_y=97)
    text(ax, 150, 102.4, "+", ha="center", fs=12, weight="bold", color=COL["vbat"])
    text(ax, 150, 83.8, "−", ha="center", fs=12, weight="bold")
    net.wire([(150, 104), (150, 112), (158, 112)], COL["vbat"])
    switch(ax, 158, 165, 112, COL["vbat"])
    text(ax, 161.5, 117.5, "SW1 POWER\n(only control)", ha="center", fs=7.5, weight="bold")
    net.wire([(165, 112), (188, 112)], COL["vbat"])
    dot(ax, 176, 112, COL["vbat"])
    flag(ax, 176, 112.4, "VBAT 3.0–4.2 V", COL["vbat"], side="up", fs=7.5)
    resistor(ax, 188, 112, 188, 100, "R1\n100 kΩ", side=-1, fs=7.5)
    net.wire([(188, 100), (188, 97)], COL["vbat"])
    dot(ax, 188, 97, COL["vbat"])
    net.wire([(188, 97), (184, 97)], COL["vbat"])
    flag(ax, 184, 97, "VBAT_SENSE", COL["vbat"], fs=7)
    resistor(ax, 188, 97, 188, 85, "R2\n100 kΩ", side=-1, fs=7.5)
    net.wire([(188, 85), (188, 84)], COL["gnd"])
    gnd(ax, 188, 84)
    net.wire([(188, 97), (194, 97), (194, 95)], COL["vbat"])
    cap(ax, 194, 95, 194, 89, None)
    gnd(ax, 194, 89)
    text(ax, 195.6, 92, "C9", fs=7)
    net.wire([(150, 82), (150, 79)], COL["gnd"])
    gnd(ax, 150, 79)
    text(ax, 159, 90,
         "VBAT feeds:\n• XIAO BAT+ pad\n• DRV8833 VM (C1, C2)\n• MAX98357 VIN (C5, C6)\n"
         "• R1/R2 divider (C9) → A3",
         va="center", fs=8)
    text(ax, 168, 75, "USB-C charges the cell through the XIAO (switch ON). No second charger.",
         ha="center", fs=7.5, color="#444")

    # legend
    items = [("VBAT", COL["vbat"]), ("3V3", COL["v33"]), ("I2C SDA", COL["sda"]),
             ("I2C SCL", COL["scl"]), ("Motor", MOTOR[0]), ("Audio I2S", AUDIO[0]),
             ("Touch", COL["touch"]), ("Bumper", COL["bump"]), ("Edge sensor", COL["analog"]),
             ("Enable / fault", COL["en"])]
    text(ax, 4, 129, "Wire colours", fs=9, weight="bold")
    for i, (label, color) in enumerate(items):
        cx = 4 + (i % 2) * 22
        cy = 125.5 - (i // 2) * 3.4
        ax.plot([cx, cx + 4], [cy, cy], color=color, lw=3, zorder=3)
        text(ax, cx + 5, cy, label, fs=8)
    text(ax, 4, 106, "Every part on its own sheet:\nimages/parts/01 … 09", fs=8, color="#555")

    save(fig, OUT / "bob-wiring.png")


# ---------------------------------------------------------------- circuit details

def panel_frame(ax, title):
    ax.add_patch(FancyBboxPatch((0.3, 0.3), 95.4, 55.4, boxstyle="round,pad=0,rounding_size=1.5",
                                fc="#fbfbfb", ec="#999", lw=1.2, zorder=1))
    text(ax, 2.5, 53, title, fs=11, weight="bold")


def detail_sensor(ax):
    panel_frame(ax, "A. One edge sensor — build 3 (left, right, center)")
    net = Net(ax)
    net.wire([(8, 46), (46, 46)], COL["v33"])
    flag(ax, 8, 46, "3V3", COL["v33"])
    dot(ax, 22, 46, COL["v33"])
    dot(ax, 46, 46, COL["v33"])
    resistor(ax, 22, 46, 22, 38, "R7 / R8 / R9\n470 Ω", fs=7.5)
    box(ax, 17, 20, 35, 16, "", fc="#fbe8f4", ec=COL["analog"])
    diode(ax, (22, 38), (22, 18), led=True)
    top, bot = photo_npn(ax, 46, 28)
    ax.plot([46, 46], [36, top[1]], color="#111", lw=1.6, zorder=5)
    ax.plot([46, 46], [bot[1], 20], color="#111", lw=1.6, zorder=5)
    net.wire([(46, 36), (46, 46)], COL["v33"])
    text(ax, 34, 33.5, "Sharp GP2S700HCP", ha="center", fs=8, weight="bold")
    text(ax, 18.2, 35, "4 A", fs=6.5, color="#555")
    text(ax, 18.2, 21, "3 K", fs=6.5, color="#555")
    text(ax, 50.8, 35, "2 C", ha="right", fs=6.5, color="#555")
    text(ax, 50.8, 21, "1 E", ha="right", fs=6.5, color="#555")
    net.wire([(22, 18), (22, 11)], COL["analog"])
    flag(ax, 22, 11, "LED_K → PCF8574 P0", COL["analog"], side="down", fs=7)
    net.wire([(46, 20), (46, 15)], COL["analog"])
    dot(ax, 46, 15, COL["analog"])
    resistor(ax, 46, 15, 46, 6, "R10 / R11 / R12\n10 kΩ", side=-1, fs=7.5)
    gnd(ax, 46, 6)
    net.wire([(46, 15), (54, 15), (60, 15)], COL["analog"])
    dot(ax, 54, 15, COL["analog"])
    cap(ax, 54, 15, 54, 8, "C10–C12\n100 nF", fs=7)
    gnd(ax, 54, 8)
    flag(ax, 60, 15, "ADS1115 A0 / A1 / A2", COL["analog"], side="right", fs=7)
    text(ax, 60, 36,
         "LED ≈ 4 mA: (3.3 − 1.2 − 0.4 V) / 470 Ω\n"
         "P0 = 0 → LEDs on.  P0 released → off.\n"
         "Table under sensor → higher voltage\n"
         "Edge (no table) → near 0 V\n"
         "Read LEDs off, then on; use the difference\n"
         "to cancel room light.\n"
         "C13 100 nF across 3V3–GND at the lip.\n"
         "Missing or stuck reading → STOP",
         va="center", fs=7.5)
    text(ax, 60, 23.5, "Check pad numbers against the\ndatasheet that ships with your part.",
         fs=7.2, color="#a00")


def detail_switch(ax):
    panel_frame(ax, "B. Safe switch — build 2 (PCF8574 P1 and P2)")
    net = Net(ax)
    net.wire([(18, 46), (56, 46)], COL["v33"])
    flag(ax, 18, 46, "3V3", COL["v33"])
    flag(ax, 16, 30, "PCF P1 / P2", COL["en"])
    net.wire([(16, 30), (24, 30)], COL["en"])
    dot(ax, 24, 30)
    dot(ax, 24, 46, COL["v33"])
    resistor(ax, 24, 46, 24, 30, "R15 / R18\n100 kΩ", fs=7.5)
    resistor(ax, 24, 30, 36, 30, "R16 / R19 100 kΩ", side=-1, fs=7.5)
    base, collector, emitter = npn(ax, 41.5, 30, r=3.5)
    text(ax, 46.2, 30, "Q1 / Q2\nBC547", fs=7.5, weight="bold")
    gnd(ax, emitter[0], emitter[1])
    net.wire([collector, (collector[0], 38), (70, 38)], COL["en"])
    dot(ax, 54, 38)
    dot(ax, 54, 46, COL["v33"])
    resistor(ax, 54, 46, 54, 38, "R17 / R20\n22 kΩ", fs=7.5)
    flag(ax, 70, 38, "enable line", COL["en"], side="right", fs=7.5)
    text(ax, 72, 28, "BC547, flat face toward you,\nlegs down: C  B  E", fs=7.2,
         color="#555")
    rows = [
        "Pn released (boot, reset, sleep) → Q on → enable LOW → part OFF",
        "Firmware writes Pn = 0 → Q off → enable HIGH (2.7–3.2 V) → part ON",
        "P1 → Q1 → MAX98357 SD (amplifier)     P2 → Q2 → DRV8833 SLP (motor driver)",
        "A broken wire on Pn also leaves the part OFF.  Sleep draw ≈ 0.17 mA per switch.",
    ]
    for i, row in enumerate(rows):
        text(ax, 4, 17 - i * 3, row, fs=8, weight="bold" if i < 2 else "normal")


def detail_divider(ax):
    panel_frame(ax, "C. Battery voltage divider")
    net = Net(ax)
    flag(ax, 18, 46, "VBAT", COL["vbat"])
    net.wire([(18, 46), (30, 46)], COL["vbat"])
    resistor(ax, 30, 46, 30, 34, "R1 100 kΩ")
    net.wire([(30, 34), (30, 30)], "#111")
    dot(ax, 30, 30)
    net.wire([(30, 30), (36, 30), (44, 30)], COL["vbat"])
    dot(ax, 36, 30, COL["vbat"])
    cap(ax, 36, 30, 36, 22, "C9 100 nF", fs=7.5)
    gnd(ax, 36, 22)
    flag(ax, 44, 30, "ADS1115 A3 (VBAT_SENSE)", COL["vbat"], side="right", fs=7.5)
    resistor(ax, 30, 30, 30, 18, "R2 100 kΩ", side=-1)
    net.wire([(30, 18), (30, 15)], COL["gnd"])
    gnd(ax, 30, 15)
    text(ax, 52, 16,
         "Full 4.2 V → 2.10 V at A3\nWarn ≈ 3.5 V → 1.75 V\nMotor stop ≈ 3.4 V → 1.70 V\n"
         "Divider draw ≈ 21 µA\nC9 gives the ADC a stiff source\nand filters motor noise\n\n"
         "Firmware: battery = 2 × A3",
         va="center", fs=8)


def detail_motor(ax):
    panel_frame(ax, "D. Motor driver input and supply")
    net = Net(ax)
    flag(ax, 14, 40, "XIAO D2", MOTOR[0])
    net.wire([(14, 40), (44, 40)], MOTOR[0])
    dot(ax, 26, 40)
    resistor(ax, 26, 40, 26, 28, "R3 100 kΩ")
    net.wire([(26, 28), (26, 26)], COL["gnd"])
    gnd(ax, 26, 26)
    box(ax, 44, 16, 18, 30, "DRV8833", fc="#f3ecfb", ec=MOTOR[1], fs=9.5, title_y=33)
    text(ax, 45, 40, "AIN1", fs=7.5, weight="bold")
    text(ax, 61, 40, "VM", ha="right", fs=7.5, weight="bold")
    text(ax, 53, 17.4, "GND", ha="center", fs=7.5, weight="bold")
    net.wire([(53, 16), (53, 14)], COL["gnd"])
    gnd(ax, 53, 14)
    net.wire([(62, 40), (70, 40), (80, 40), (86, 40)], COL["vbat"])
    flag(ax, 86, 40, "VBAT", COL["vbat"], side="right")
    dot(ax, 70, 40, COL["vbat"])
    dot(ax, 80, 40, COL["vbat"])
    cap(ax, 70, 40, 70, 30, "C1\n1000 µF", polar=True, fs=7.5)
    gnd(ax, 70, 30)
    cap(ax, 80, 40, 80, 30, "C2\n100 nF", fs=7.5)
    gnd(ax, 80, 30)
    text(ax, 4, 7.6,
         "Same 100 kΩ pulldown on D3 → AIN2 (R4), D8 → BIN1 (R5), D9 → BIN2 (R6). They hold every\n"
         "input LOW while the XIAO resets.  SLP comes from the Q2 safe switch.  C3, C4: 100 nF\n"
         "ceramic soldered across each motor's terminals.  The module has no logic VCC: VM only.",
         fs=7.6)


def detail_touch_bumper(ax):
    panel_frame(ax, "E. Touch pad and bumper")
    net = Net(ax)
    flag(ax, 12, 44, "XIAO D0", COL["touch"])
    net.wire([(12, 44), (18, 44)], COL["touch"])
    resistor(ax, 18, 44, 30, 44, "R13 470 Ω", fs=7.5)
    net.wire([(30, 44), (46, 44)], COL["touch"])
    box(ax, 46, 39, 16, 10, "", fc="#f6d3ad", ec=COL["touch"])
    text(ax, 54, 44, "copper pad", ha="center", fs=7.5, weight="bold")
    text(ax, 18, 39.6, "R13 sits next to the XIAO pin", fs=7, color="#555")

    flag(ax, 12, 24, "XIAO D1", COL["bump"])
    net.wire([(12, 24), (22, 24), (32, 24), (44, 24)], COL["bump"])
    dot(ax, 22, 24, COL["bump"])
    resistor(ax, 22, 24, 22, 32, "R14 10 kΩ", fs=7.5)
    flag(ax, 22, 32, "3V3", COL["v33"], side="up", fs=7)
    dot(ax, 32, 24, COL["bump"])
    cap(ax, 32, 24, 32, 16, "C14 100 nF", fs=7.5)
    gnd(ax, 32, 16)
    dot(ax, 44, 24, COL["bump"])
    net.wire([(44, 24), (44, 29), (48, 29)], COL["bump"])
    switch(ax, 48, 56, 29, COL["bump"])
    net.wire([(44, 24), (44, 19), (48, 19)], COL["bump"])
    switch(ax, 48, 56, 19, COL["bump"])
    net.wire([(56, 29), (62, 29), (62, 19)], COL["gnd"])
    net.wire([(56, 19), (62, 19), (62, 15)], COL["gnd"])
    dot(ax, 62, 19, COL["gnd"])
    gnd(ax, 62, 15)
    text(ax, 52, 33, "SW2", ha="center", fs=7.5, weight="bold")
    text(ax, 52, 23.2, "SW3", ha="center", fs=7.5, weight="bold")
    text(ax, 66, 44,
         "GPIO1 = TOUCH1, wakes Bob from\ndeep sleep. Wire under 10 cm,\naway from the antenna.",
         fs=7.5)
    text(ax, 66, 23,
         "NO contact to D1, COM to GND.\nPressed = LOW.  R14 is stiffer\nthan the internal pull-up;\n"
         "R14 + C14 filter motor noise\n(≈ 1 ms).",
         fs=7.5)


def detail_audio_rail(ax):
    panel_frame(ax, "F. Amplifier straps, 3V3 rail, fault pull-up")
    net = Net(ax)
    flag(ax, 10, 44, "VBAT", COL["vbat"])
    net.wire([(10, 44), (18, 44), (26, 44), (30, 44), (34, 44)], COL["vbat"])
    for x in (18, 26, 30):
        dot(ax, x, 44, COL["vbat"])
    cap(ax, 18, 44, 18, 36, None, polar=True)
    gnd(ax, 18, 36)
    text(ax, 14.5, 40, "C5", ha="right", fs=7.5, weight="bold")
    cap(ax, 26, 44, 26, 36, None)
    gnd(ax, 26, 36)
    text(ax, 23.8, 40, "C6", ha="right", fs=7.5, weight="bold")
    resistor(ax, 30, 44, 30, 30, None)
    text(ax, 30.8, 37, "R22", fs=7, weight="bold")
    net.wire([(30, 30), (34, 30)], COL["vbat"])
    box(ax, 34, 22, 20, 26, "MAX98357A", fc="#e6f5e6", ec=AUDIO[1], fs=8.5, title_y=47)
    for label, y in (("VIN", 44), ("GAIN", 30), ("SD", 26)):
        text(ax, 35, y, label, fs=7, weight="bold")
    for label, y in (("BCLK", 40), ("LRC", 35), ("DIN", 30)):
        text(ax, 53, y, label, ha="right", fs=7, weight="bold")
    net.wire([(34, 26), (20, 26)], COL["en"])
    flag(ax, 20, 26, "AMP_EN (Q1)", COL["en"], fs=7)
    for label, y, color in (("D6", 40, AUDIO[0]), ("D7", 35, AUDIO[1]), ("D10", 30, AUDIO[2])):
        net.wire([(54, y), (57, y)], color)
        flag(ax, 57, y, label, color, side="right", fs=7)

    net.wire([(66, 46), (92, 46)], COL["v33"])
    text(ax, 66, 48.2, "3V3 at the XIAO pin", fs=7.5, weight="bold", color=COL["v33"])
    for x in (70, 78, 86):
        dot(ax, x, 46, COL["v33"])
    cap(ax, 70, 46, 70, 39, None, polar=True)
    gnd(ax, 70, 39)
    text(ax, 71.8, 42.5, "C7", fs=7.5, weight="bold")
    cap(ax, 78, 46, 78, 39, None)
    gnd(ax, 78, 39)
    text(ax, 79.8, 42.5, "C8", fs=7.5, weight="bold")
    resistor(ax, 86, 46, 86, 36, None)
    text(ax, 87.6, 41, "R21", fs=7.5, weight="bold")
    net.wire([(86, 36), (86, 33)], COL["en"])
    flag(ax, 86, 33, "FAULT", COL["en"], side="down", fs=7)
    text(ax, 4, 11,
         "C5 100 µF + C6 100 nF at VIN.  R22 100 kΩ from GAIN to VIN = 3 dB, the lowest gain.\n"
         "C7 10 µF + C8 100 nF where 3V3 leaves the XIAO.  R21 10 kΩ pulls the driver's\n"
         "open-drain FLT high; PCF P3 reads it.  I2C pull-ups R23 / R24 4.7 kΩ: fit only if SDA\n"
         "and SCL measure more than 10 kΩ to 3V3 with power off.",
         fs=7.6)


def figure_details():
    W, H = 200, 188
    fig, ax = setup(W, H)
    text(ax, 100, 185, "Bob — circuit details (every resistor, capacitor and transistor)",
         ha="center", fs=18, weight="bold")
    layout = [(detail_sensor, 2, 122), (detail_switch, 102, 122),
              (detail_divider, 2, 62), (detail_motor, 102, 62),
              (detail_touch_bumper, 2, 2), (detail_audio_rail, 102, 2)]
    for fn, x, y in layout:
        fn(subpanel(fig, W, H, x, y, 96, 56))
    save(fig, OUT / "bob-circuit-details.png")


# ---------------------------------------------------------------- one sheet per part

def part_xiao():
    fig, ax = setup(180, 100)
    text(ax, 90, 97.6, "00 · Seeed Studio XIAO ESP32-S3 Sense — what every pin does",
         ha="center", fs=17, weight="bold")
    text(ax, 90, 94.2, "Top view, USB-C up.  Colour = the wire colour used on every other sheet.",
         ha="center", fs=9.5, color="#444")
    ax.add_patch(FancyBboxPatch((72, 22), 36, 62, boxstyle="round,pad=0,rounding_size=2",
                                fc="#e8f1fb", ec=HEAD, lw=2, zorder=2))
    ax.add_patch(Rectangle((84, 84), 12, 4, fc="#c9c9c9", ec="#555", lw=1.2, zorder=2))
    text(ax, 90, 86, "USB-C", ha="center", fs=8, weight="bold")
    ax.add_patch(Circle((76, 80.5), 1.2, fc="#d9b44a", ec="#7a5b00", zorder=3))
    text(ax, 78, 80.5, "U.FL antenna", fs=6.5, color="#555")
    text(ax, 90, 58, "XIAO ESP32-S3\nESP32-S3R8 · 8 MB PSRAM\n8 MB flash · 3.3 V logic\n\n"
         "Sense board on top:\nOV2640 / OV3660 camera\nPDM microphone\nmicroSD slot (leave empty)",
         ha="center", fs=8.3, color=HEAD)
    left = [
        ("D0", "GPIO1 · TOUCH1", "Copper touch pad, through R13 470 Ω. Wakes Bob from sleep.", COL["touch"]),
        ("D1", "GPIO2", "Bumper SW2 + SW3 to GND. R14 10 kΩ pull-up, C14 100 nF.", COL["bump"]),
        ("D2", "GPIO3", "DRV8833 AIN1 (left motor). R3 100 kΩ to GND.", MOTOR[0]),
        ("D3", "GPIO4", "DRV8833 AIN2 (left motor). R4 100 kΩ to GND.", MOTOR[1]),
        ("D4", "GPIO5 · SDA", "I2C data: OLED, ADS1115, PCF8574.", COL["sda"]),
        ("D5", "GPIO6 · SCL", "I2C clock: OLED, ADS1115, PCF8574.", COL["scl"]),
        ("D6", "GPIO43 · U0TXD", "MAX98357A BCLK. Boot log pin, so audio only.", AUDIO[0]),
    ]
    right = [
        ("5V", "USB 5 V", "Not used. Never connect the battery here.", "#9a9a9a"),
        ("GND", "", "Common ground for every module.", COL["gnd"]),
        ("3V3", "regulator out", "3V3 rail. C7 10 µF + C8 100 nF at this pin.", COL["v33"]),
        ("D10", "GPIO9", "MAX98357A DIN (I2S data).", AUDIO[2]),
        ("D9", "GPIO8", "DRV8833 BIN2 (right motor). R6 100 kΩ to GND.", MOTOR[3]),
        ("D8", "GPIO7", "DRV8833 BIN1 (right motor). R5 100 kΩ to GND.", MOTOR[2]),
        ("D7", "GPIO44 · U0RXD", "MAX98357A LRC (word select).", AUDIO[1]),
    ]
    for i, (pin, gpio, job, color) in enumerate(left):
        y = 78 - i * 8.6
        ax.add_patch(Circle((72, y), 1.5, fc=color, ec="#333", lw=1, zorder=4))
        text(ax, 74.4, y, pin, fs=9, weight="bold")
        ax.plot([70.5, 67], [y, y], color=color, lw=2.6, zorder=3)
        text(ax, 66, y + 1.3, f"{pin} · {gpio}", ha="right", fs=9, weight="bold", color=color)
        text(ax, 66, y - 1.5, job, ha="right", fs=8)
    for i, (pin, gpio, job, color) in enumerate(right):
        y = 78 - i * 8.6
        ax.add_patch(Circle((108, y), 1.5, fc=color, ec="#333", lw=1, zorder=4))
        text(ax, 105.6, y, pin, ha="right", fs=9, weight="bold")
        ax.plot([109.5, 113], [y, y], color=color, lw=2.6, zorder=3)
        label = f"{pin} · {gpio}" if gpio else pin
        text(ax, 114, y + 1.3, label, fs=9, weight="bold", color=color)
        text(ax, 114, y - 1.5, job, fs=8)
    notes = [
        ("Back of the XIAO", "BAT+ pad (farther from USB) and BAT− pad (nearer USB) go to the "
         "switched 18650. Meter both before soldering. D11 / D12 pads are the microphone: leave them."),
        ("Sense board jumpers", "CUT J3: it connects the microSD pull-ups to D8, D9 and D10, which "
         "would pull the right-motor inputs high. Do NOT cut the microphone jumpers."),
        ("Why the motors are on D2, D3, D8, D9", "D6 and D7 are GPIO43 / GPIO44 (UART0). They have "
         "pull-ups at reset and D6 prints the boot log, so a reset could twitch a motor. "
         "D2, D3, D8, D9 float at reset and the 100 kΩ pulldowns hold them low."),
    ]
    for i, (head, body) in enumerate(notes):
        x = 4 + i * 58.5
        ax.add_patch(FancyBboxPatch((x, 2), 56, 16, boxstyle="round,pad=0,rounding_size=1",
                                    fc="#fafafa", ec="#b5b5b5", lw=1, zorder=1))
        text(ax, x + 1.5, 16, head, fs=9, weight="bold", color=HEAD)
        for j, line in enumerate(textwrap.wrap(body, 74)):
            text(ax, x + 1.5, 13.4 - j * 1.4, line, fs=7.8)
    save(fig, PARTS / "00-xiao-pinout.png")


def part_power():
    used = {"3V3": COL["v33"], "GND": COL["gnd"], "BAT+": COL["vbat"], "BAT−": COL["gnd"]}
    fig, ax, p, net = part_frame(
        "01 · Power — protected 18650, switch, VBAT and 3V3 rails",
        "One cell feeds everything. The XIAO charges it over USB-C and makes the 3V3 rail.", used)
    net.wire([(48, 20), (48, 12)], COL["gnd"])
    cell(ax, 48, 20, 28)
    text(ax, 45, 24, "BT1 protected 18650\n≈ 2500 mAh, 3.0–4.2 V", ha="right", fs=7.8,
         weight="bold")
    net.wire([p["BAT−"], (54, 12)], COL["gnd"])
    dot(ax, 48, 12, COL["gnd"])
    gnd(ax, 54, 12)
    net.wire([p["BAT+"], (60, 16.4), (60, 36)], COL["vbat"])
    net.wire([(48, 28), (48, 36)], COL["vbat"])
    switch(ax, 48, 56, 36, COL["vbat"])
    text(ax, 52, 40.2, "SW1 power", ha="center", fs=7.8, weight="bold")
    net.wire([(56, 36), (106, 36), (106, 34)], COL["vbat"])
    dot(ax, 60, 36, COL["vbat"])
    text(ax, 82, 33.4, "VBAT 3.0–4.2 V (after SW1)", ha="center", fs=8, weight="bold",
         color=COL["vbat"])

    for tap, c_big, c_small, big, small, label in (
            (65, 70, 78, "C1", "C2", "DRV8833 VM\n(motors)"),
            (86, 91, 99, "C5", "C6", "MAX98357 VIN\n(speaker)")):
        dot(ax, tap, 36, COL["vbat"])
        net.wire([(tap, 36), (tap, 60)], COL["vbat"])
        net.wire([(tap, 50), (c_small, 50)], COL["vbat"])
        dot(ax, tap, 50, COL["vbat"])
        dot(ax, c_big, 50, COL["vbat"])
        cap(ax, c_big, 50, c_big, 43, None, polar=True)
        gnd(ax, c_big, 43)
        cap(ax, c_small, 50, c_small, 43, None)
        gnd(ax, c_small, 43)
        text(ax, c_big + 1.9, 46.5, big, fs=7.5, weight="bold")
        text(ax, c_small + 1.9, 46.5, small, fs=7.5, weight="bold")
        box(ax, tap - 9, 60, 18, 6.5, "", fc="#fff6f6", ec=COL["vbat"])
        text(ax, tap, 63.2, label, ha="center", fs=7.3, weight="bold")

    resistor(ax, 106, 34, 106, 26, "R1 100 kΩ", side=-1, fs=7.5)
    dot(ax, 106, 25, "#111")
    net.wire([(106, 26), (106, 25)], "#111")
    resistor(ax, 106, 25, 106, 16, "R2 100 kΩ", side=-1, fs=7.5)
    gnd(ax, 106, 16)
    net.wire([(106, 25), (111, 25), (111, 24)], COL["vbat"])
    cap(ax, 111, 24, 111, 18, None)
    gnd(ax, 111, 18)
    text(ax, 112.6, 21, "C9", fs=7.5, weight="bold")
    text(ax, 106, 10.6, "midpoint → ADS1115 A3", ha="center", fs=7.3)

    net.wire([p["3V3"], (36, 73.6), (36, 82), (112, 82)], COL["v33"])
    text(ax, 74, 84.4, "3V3 rail (XIAO regulator output)", ha="center", fs=8, weight="bold",
         color=COL["v33"])
    for x, polar, name, value in ((42, True, "C7", "10 µF"), (54, False, "C8", "100 nF")):
        dot(ax, x, 82, COL["v33"])
        cap(ax, x, 82, x, 76, None, polar=polar)
        gnd(ax, x, 76)
        text(ax, x + 1.9, 79, f"{name}\n{value}", fs=7.3, weight="bold")
    for x, label in ((66, "OLED"), (78, "ADS1115"), (90, "PCF8574"), (102, "sensors,\npull-ups")):
        dot(ax, x, 82, COL["v33"])
        net.wire([(x, 82), (x, 79.5)], COL["v33"])
        text(ax, x, 78.8, label, ha="center", va="top", fs=7.3)
    gnd(ax, p["GND"][0], p["GND"][1])
    text(ax, 40, 6, "USB-C on the XIAO charges BT1 only while SW1 is ON. No second charger.",
         fs=8, color="#444")

    info_panel(ax, used, [
        ("What it does", [
            "One protected 18650 feeds the XIAO (BAT pads), the motor driver and the amplifier. "
            "SW1 in the positive lead is the only control. The XIAO regulator makes 3V3 for "
            "the screen, ADC, expander and sensors.",
        ]),
        ("Parts on this sheet", [
            "|BT1  protected 18650, about 2500 mAh",
            "|SW1  slide or toggle switch, 2 A or more",
            "|C1   1000 µF 16 V electrolytic   DRV8833 VM",
            "|C2   100 nF ceramic              DRV8833 VM",
            "|C5   100 µF 16 V electrolytic    MAX98357 VIN",
            "|C6   100 nF ceramic              MAX98357 VIN",
            "|C7   10 µF 16 V                  XIAO 3V3 pin",
            "|C8   100 nF ceramic              XIAO 3V3 pin",
            "|R1, R2 100 kΩ + C9 100 nF        battery sense",
        ]),
        ("Rules", [
            "- Electrolytic stripe = negative. Fit C1 and C5 the right way round.",
            "- Battery, switch, VM and VIN wires: 22–24 AWG. Signal wires: 26–30 AWG.",
            "- Join the battery minus, XIAO BAT−, driver GND and amp GND at one point.",
            "- Never feed the battery into the 5V pin.",
        ]),
        ("Check before power-on", [
            "- SW1 off: VBAT reads 0 V. SW1 on: VBAT reads the cell voltage, + on BAT+.",
            "- If Bob dies the instant SW1 closes, the cell protection may be tripping on the "
            "capacitor inrush. Plug in USB to reset it and change C1 to 470 µF.",
        ]),
    ])
    save(fig, PARTS / "01-power.png")


def part_oled():
    used = {"3V3": COL["v33"], "GND": COL["gnd"], "D4": COL["sda"], "D5": COL["scl"]}
    fig, ax, p, net = part_frame(
        "02 · OLED 0.96″ SSD1306 (I2C) to the XIAO",
        "Status screen. Four wires: power, ground, and the shared I2C bus on D4 / D5.", used)
    box(ax, 70, 40, 34, 40, "0.96″ OLED · SSD1306", fc="#f2f2f2", fs=9, title_y=79)
    ax.add_patch(Rectangle((78, 48), 23, 22, fc="#0b1a33", ec="#333", lw=1.2, zorder=3))
    text(ax, 89.5, 62, "Bob", ha="center", fs=14, weight="bold", color="#7fd3ff")
    text(ax, 89.5, 54.5, "Listening", ha="center", fs=9, color="#7fd3ff")
    text(ax, 89.5, 44, "I2C address 0x3C", ha="center", fs=7.5)
    m = pin_row(ax, "left", 70, [("GND", 74), ("VCC", 70), ("SCL", 66), ("SDA", 62)])
    net.wire([p["GND"], (46, 69.2), (46, 74), m["GND"]], COL["gnd"])
    net.wire([p["3V3"], (50, 73.6), (50, 70), m["VCC"]], COL["v33"])
    net.wire([p["D5"], (58, 42.8), (58, 66), m["SCL"]], COL["scl"])
    net.wire([p["D4"], (54, 47.2), (54, 62), m["SDA"]], COL["sda"])

    box(ax, 66, 8, 46, 24, "", fc="#ffffff", ec="#999", ls="--")
    text(ax, 68, 29.6, "Optional — only if the bus has no pull-ups", fs=8, weight="bold")
    net.wire([(76, 25), (98, 25)], COL["v33"])
    flag(ax, 76, 25, "3V3", COL["v33"])
    for x, name, sig, color in ((82, "R23", "SDA", COL["sda"]), (96, "R24", "SCL", COL["scl"])):
        dot(ax, x, 25, COL["v33"])
        resistor(ax, x, 25, x, 15, f"{name}\n4.7 kΩ", side=-1, fs=7.5)
        flag(ax, x, 15, sig, color, side="down", fs=7)

    info_panel(ax, used, [
        ("What it does", [
            "Shows Bob's state: Listening, Thinking, Offline, the battery warning and reminders. "
            "128 × 64 pixels, monochrome.",
        ]),
        ("Pin by pin", [
            "|OLED GND  →  XIAO GND",
            "|OLED VCC  →  XIAO 3V3   (not 5V)",
            "|OLED SCL  →  XIAO D5",
            "|OLED SDA  →  XIAO D4",
            "Most modules print the header as GND VCC SCL SDA. Some swap GND and VCC. Follow "
            "the print on your module, not the order in this drawing.",
        ]),
        ("Specs", [
            "- SSD1306 controller, I2C at 100–400 kHz, address 0x3C (silk may say 0x78).",
            "- About 10–20 mA with text lit. Display-off command (0xAE) before sleep.",
        ]),
        ("Extra parts", [
            "None needed. The module, the ADS1115 board and the PCF8574 board usually carry "
            "their own SDA / SCL pull-ups. R23 / R24 are only for a bus with none.",
        ]),
        ("Check before power-on", [
            "- Power off: SDA→3V3 and SCL→3V3 should read 1.5–10 kΩ. Above 10 kΩ, fit R23 "
            "and R24. Below 1.5 kΩ, remove the pull-ups on one module.",
            "- I2C scan shows 0x3C. If not, try 0x3D.",
        ]),
    ])
    save(fig, PARTS / "02-oled.png")


def part_ads1115():
    used = {"3V3": COL["v33"], "GND": COL["gnd"], "D4": COL["sda"], "D5": COL["scl"]}
    fig, ax, p, net = part_frame(
        "03 · ADS1115 16-bit ADC — edge sensors and battery voltage",
        "Reads the three GP2S700HCP outputs on A0–A2 and half the battery voltage on A3.", used)
    box(ax, 62, 26, 28, 56, "ADS1115\n16-bit ADC · 0x48", fc="#f2f2f2", fs=9, title_y=81)
    m = pin_row(ax, "left", 62, [("VDD", 73.6), ("GND", 69.2), ("SCL", 64.8), ("SDA", 60.4),
                                 ("ADDR", 56), ("ALRT", 51.6)])
    r = pin_row(ax, "right", 90, [("A0", 73.6), ("A1", 69.2), ("A2", 64.8), ("A3", 47.2)])
    net.wire([p["3V3"], m["VDD"]], COL["v33"])
    net.wire([p["GND"], m["GND"]], COL["gnd"])
    net.wire([p["D5"], (54, 42.8), (54, 64.8), m["SCL"]], COL["scl"])
    net.wire([p["D4"], (50, 47.2), (50, 60.4), m["SDA"]], COL["sda"])
    net.wire([m["ADDR"], (57.5, 56)], COL["gnd"])
    gnd(ax, 57.5, 56)
    text(ax, 58.6, 51.6, "NC", ha="right", fs=7.5, color="#777", weight="bold")
    for name, label in (("A0", "A0 ← left sensor"), ("A1", "A1 ← right sensor"),
                        ("A2", "A2 ← center sensor")):
        flag(ax, r[name][0], r[name][1], label, COL["analog"], side="right", fs=7)
    net.wire([r["A3"], (100, 47.2), (106, 47.2), (106, 46)], COL["vbat"])
    dot(ax, 100, 47.2, COL["vbat"])
    flag(ax, 100, 60, "VBAT", COL["vbat"], side="up", fs=7)
    resistor(ax, 100, 60, 100, 48.5, "R1\n100 kΩ", side=-1, fs=7.5)
    net.wire([(100, 48.5), (100, 47.2)], COL["vbat"])
    resistor(ax, 100, 47.2, 100, 36, "R2\n100 kΩ", side=-1, fs=7.5)
    gnd(ax, 100, 36)
    cap(ax, 106, 46, 106, 40, None)
    gnd(ax, 106, 40)
    text(ax, 107.8, 43, "C9\n100 nF", fs=7.3, weight="bold")
    text(ax, 76, 18,
         "A3 reads half the battery:\n4.20 V → 2.10 V   ·   3.50 V → 1.75 V (warn)   ·   "
         "3.40 V → 1.70 V (motor lock)\nThe divider draws about 21 µA all the time SW1 is on.",
         ha="center", fs=8)

    info_panel(ax, used, [
        ("What it does", [
            "Turns the analog sensor voltages into numbers over I2C, because the XIAO has no "
            "spare analog pins. Also measures the battery, since no XIAO pin is wired to it.",
        ]),
        ("Pin by pin", [
            "|VDD  → XIAO 3V3      GND  → XIAO GND",
            "|SCL  → XIAO D5       SDA  → XIAO D4",
            "|ADDR → GND (0x48)    ALRT → not connected",
            "|A0   ← left GP2S700HCP emitter",
            "|A1   ← right GP2S700HCP emitter",
            "|A2   ← center GP2S700HCP emitter",
            "|A3   ← R1 / R2 midpoint (VBAT ÷ 2)",
        ]),
        ("Specs", [
            "- 16-bit, 8–860 samples/s, 2.0–5.5 V. Use the ±4.096 V range (GAIN_ONE).",
            "- Inputs must stay between GND and VDD. That is why VDD is 3V3 and the battery "
            "goes through the divider.",
        ]),
        ("Extra parts", [
            "- R1, R2 100 kΩ: battery divider.  C9 100 nF: holds A3 steady while the ADC "
            "samples, and filters motor noise.",
            "- C10–C12 100 nF sit on A0–A2 (sheet 04).",
        ]),
        ("Firmware", [
            "Battery = 2 × A3 reading. Single-shot at 860 SPS for the sensors. A failed read or a "
            "missing 0x48 means stop the motors.",
        ]),
    ])
    save(fig, PARTS / "03-ads1115.png")


def part_sensors():
    used = {"3V3": COL["v33"], "GND": COL["gnd"], "D4": COL["sda"], "D5": COL["scl"]}
    fig, ax, p, net = part_frame(
        "04 · Three Sharp GP2S700HCP edge sensors",
        "Each LED is sunk by PCF8574 P0. Each detector output goes to one ADS1115 input.", used)
    net.wire([p["3V3"], (32, 73.6), (32, 84), (112, 84)], COL["v33"])
    gnd(ax, p["GND"][0], p["GND"][1])
    flag(ax, p["D4"][0], p["D4"][1], "SDA", COL["sda"], side="right", fs=7)
    flag(ax, p["D5"][0], p["D5"][1], "SCL", COL["scl"], side="right", fs=7)
    channels = [(40, "LEFT", "R7", "R10", "C10", "A0"),
                (64, "RIGHT", "R8", "R11", "C11", "A1"),
                (88, "CENTER", "R9", "R12", "C12", "A2")]
    for x, name, r_led, r_em, c_em, ain in channels:
        text(ax, x + 5, 86.6, name, ha="center", fs=8, weight="bold")
        dot(ax, x, 84, COL["v33"])
        dot(ax, x + 10, 84, COL["v33"])
        resistor(ax, x, 84, x, 76, f"{r_led} 470 Ω", fs=7.3)
        ax.plot([x, x], [76, 72], color="#111", lw=1.8, zorder=4)
        box(ax, x - 3, 56, 16, 16, "", fc="#fbe8f4", ec=COL["analog"])
        diode(ax, (x, 72), (x, 56), led=True)
        top, bot = photo_npn(ax, x + 10, 64)
        ax.plot([x + 10, x + 10], [72, top[1]], color="#111", lw=1.6, zorder=5)
        ax.plot([x + 10, x + 10], [bot[1], 56], color="#111", lw=1.6, zorder=5)
        net.wire([(x + 10, 72), (x + 10, 84)], COL["v33"])
        for lx, ly, s in ((x - 1, 73.2, "4"), (x - 1, 54.8, "3"), (x + 11, 73.2, "2"),
                          (x + 11, 54.8, "1")):
            text(ax, lx, ly, s, ha="center", fs=6.5, color="#555", weight="bold")
        net.wire([(x + 10, 56), (x + 10, 46)], COL["analog"])
        dot(ax, x + 10, 46, COL["analog"])
        resistor(ax, x + 10, 46, x + 10, 37, f"{r_em}\n10 kΩ", side=-1, fs=7)
        gnd(ax, x + 10, 37)
    for x, name, r_led, r_em, c_em, ain in channels:
        net.wire([(x + 10, 46), (x + 14, 46), (x + 19, 46), (x + 19, 22)], COL["analog"])
        dot(ax, x + 14, 46, COL["analog"])
        cap(ax, x + 14, 46, x + 14, 40, None)
        gnd(ax, x + 14, 40)
        text(ax, x + 15.8, 43, c_em, fs=7, weight="bold")
    net.wire([(40, 56), (40, 22)], COL["analog"])
    net.wire([(64, 56), (64, 50), (40, 50)], COL["analog"])
    net.wire([(88, 56), (88, 50), (64, 50)], COL["analog"])
    dot(ax, 40, 50, COL["analog"])
    dot(ax, 64, 50, COL["analog"])
    text(ax, 76, 51.6, "LED_K: the three cathodes join here", ha="center", fs=7, color="#a0306f")
    dot(ax, 112, 84, COL["v33"])
    cap(ax, 112, 84, 112, 78, None)
    gnd(ax, 112, 78)
    text(ax, 110.4, 80.6, "C13", ha="right", fs=7, weight="bold")

    box(ax, 32, 6, 18, 16, "", fc="#f2f2f2")
    text(ax, 41, 13.5, "PCF8574\nP0 sinks ≈ 13 mA\nwrite 0 = LEDs on", ha="center", fs=7.3)
    text(ax, 40, 20.7, "P0", ha="center", fs=7, weight="bold")
    box(ax, 54, 6, 58, 16, "", fc="#f2f2f2")
    for x, ain in ((59, "A0"), (83, "A1"), (107, "A2")):
        text(ax, x, 20.7, ain, ha="center", fs=7, weight="bold")
    text(ax, 83, 12.6, "ADS1115 (0x48), ±4.096 V range.  A3 = battery (sheet 03).\n"
         "SDA / SCL from XIAO D4 / D5.", ha="center", fs=7.5)

    info_panel(ax, used, [
        ("What it does", [
            "Each sensor shines an IR LED at the table and measures the reflection, about 3 mm "
            "away. Table under it = higher voltage. Past the edge = near 0 V.",
        ]),
        ("Pin by pin, for each sensor", [
            "|pad 4 anode     → R7 / R8 / R9 470 Ω → 3V3",
            "|pad 3 cathode   → LED_K → PCF8574 P0",
            "|pad 2 collector → 3V3",
            "|pad 1 emitter   → R10 / R11 / R12 10 kΩ → GND",
            "|                → ADS1115 A0 / A1 / A2",
            "|                → C10 / C11 / C12 100 nF → GND",
            "C13 100 nF across 3V3 and GND on the sensor lip. Check pad numbers against the "
            "datasheet that ships with your part; an older sheet orders them differently.",
        ]),
        ("Numbers", [
            "- LED current ≈ (3.3 − 1.2 − 0.4 V) / 470 Ω ≈ 3.5–4.5 mA, near Sharp's 4 mA test "
            "current. Three LEDs ≈ 13 mA into P0; the PCF8574 can sink 25 mA per pin.",
            "- R10 × C10 = 1 ms filter. Wait 5 ms after switching the LEDs before reading.",
        ]),
        ("Firmware", [
            "Read with LEDs off (P0 = 1), then on (P0 = 0). Use the difference, which cancels "
            "room light. Any reading outside the calibrated window, or a failed I2C read, stops "
            "the motors.",
        ]),
        ("Mounting", [
            "Face down, about 3 mm above the table, on a lip at least 25 mm ahead of the wheels, "
            "with a small shroud. The 4 × 3 × 2 mm package overheats easily: solder fast.",
        ]),
    ])
    save(fig, PARTS / "04-edge-sensors.png")


def part_pcf8574():
    used = {"3V3": COL["v33"], "GND": COL["gnd"], "D4": COL["sda"], "D5": COL["scl"]}
    fig, ax, p, net = part_frame(
        "05 · PCF8574 I2C expander — LED, amplifier and motor-driver enables",
        "Released pins mean OFF: sensor LEDs dark, amplifier shut down, motor driver asleep.", used)
    box(ax, 46, 10, 20, 78, "PCF8574\nI2C expander\n0x20", fc="#f2f2f2", fs=8.5, title_y=87.2)
    m = pin_row(ax, "left", 46, [("VCC", 73.6), ("GND", 69.2), ("SDA", 47.2), ("SCL", 42.8),
                                 ("INT", 34)])
    r = pin_row(ax, "right", 66, [("P0", 82), ("P1", 64), ("P2", 46), ("P3", 30)])
    text(ax, 56, 22, "P4–P7\nspare,\nleave\nreleased", ha="center", fs=7, color="#555")
    text(ax, 56, 13.2, "A0 A1 A2\n→ GND", ha="center", fs=7)
    text(ax, 42.4, 34, "NC", ha="right", fs=7.5, color="#777", weight="bold")
    for pin, name in (("3V3", "VCC"), ("GND", "GND"), ("D4", "SDA"), ("D5", "SCL")):
        net.wire([p[pin], m[name]], used[pin])

    net.wire([r["P0"], (74, 82)], COL["analog"])
    diode(ax, (80, 82), (74, 82), led=True)
    resistor(ax, 80, 82, 88, 82, None)
    flag(ax, 88, 82, "3V3", COL["v33"], side="right", fs=7)
    text(ax, 81, 85.6, "×3: R7–R9 470 Ω + sensor LED", ha="center", fs=7, color="#555")

    for y, rp, rb, rc, q, label in ((64, "R15", "R16", "R17", "Q1", "AMP_EN → amp SD"),
                                    (46, "R18", "R19", "R20", "Q2", "MOTOR_EN → driver SLP")):
        net.wire([r[f"P{1 if q == 'Q1' else 2}"], (73, y)], COL["en"])
        dot(ax, 73, y)
        resistor(ax, 73, y, 73, y + 7, f"{rp}\n100 kΩ", fs=7)
        flag(ax, 73, y + 7, "3V3", COL["v33"], side="up", fs=6.5)
        resistor(ax, 73, y, 81, y, f"{rb} 100 kΩ", side=-1, fs=7)
        base, collector, emitter = npn(ax, 86, y, r=3)
        text(ax, 89.8, y + 0.3, f"{q} BC547", fs=7.3, weight="bold")
        gnd(ax, emitter[0], emitter[1])
        net.wire([collector, (collector[0], y + 8), (100, y + 8)], COL["en"])
        dot(ax, 94, y + 8)
        resistor(ax, 94, y + 8, 94, y + 14, f"{rc} 22 kΩ", fs=7)
        flag(ax, 94, y + 14, "3V3", COL["v33"], side="up", fs=6.5)
        flag(ax, 100, y + 8, label, COL["en"], side="right", fs=7)

    net.wire([r["P3"], (80, 30), (100, 30)], COL["en"])
    dot(ax, 80, 30)
    resistor(ax, 80, 30, 80, 37, "R21 10 kΩ", fs=7)
    flag(ax, 80, 37, "3V3", COL["v33"], side="up", fs=6.5)
    flag(ax, 100, 30, "FAULT ← driver FLT", COL["en"], side="right", fs=7)

    info_panel(ax, used, [
        ("What it does", [
            "Eight extra I/O pins over the same I2C bus. Bob uses four: P0 lights the sensor "
            "LEDs, P1 enables the amplifier, P2 wakes the motor driver, P3 reads a driver fault.",
        ]),
        ("Pin by pin", [
            "|VCC → 3V3   GND → GND   SDA → D4   SCL → D5",
            "|A0, A1, A2 → GND (address 0x20)   INT → NC",
            "|P0 → LED_K (three LED cathodes)",
            "|P1 → R16 → Q1 base;  Q1 collector → amp SD",
            "|P2 → R19 → Q2 base;  Q2 collector → driver SLP",
            "|P3 ← driver FLT, R21 10 kΩ pull-up to 3V3",
        ]),
        ("How the safe switch works", [
            "Released (power-up, after 0xFF, or a broken wire): R15 / R18 pull the base up, Q "
            "turns on and holds the enable line low, so the part is off. Firmware writes 0: Q "
            "turns off and R17 / R20 pull the enable to about 2.7–3.2 V, so the part is on.",
        ]),
        ("Port byte", [
            "|bit  P0 LEDs  P1 amp  P2 driver  P3 fault",
            "|0    on       on      awake      fault!",
            "|1    off      off     asleep     ok",
        ]),
        ("Watch out", [
            "- The PCF8574 stays powered through an XIAO reset and deep sleep, so it keeps its "
            "last outputs. The first line of setup() writes 0xFF. Write 0xFF before sleep too.",
            "- A PCF8574A board answers at 0x38, not 0x20. Run an I2C scan.",
            "- Released switches draw ≈ 0.17 mA each, about 0.35 mA in sleep.",
        ]),
    ])
    save(fig, PARTS / "05-pcf8574.png")


def part_drv8833():
    used = {"GND": COL["gnd"], "D2": MOTOR[0], "D3": MOTOR[1], "D8": MOTOR[2], "D9": MOTOR[3]}
    fig, ax, p, net = part_frame(
        "06 · DRV8833 motor driver and two N12 motors",
        "Inputs on D2, D3, D8, D9 with 100 kΩ pulldowns. VM from the battery. SLP from the safe "
        "switch.", used)
    box(ax, 62, 20, 28, 54, "", fc="#f3ecfb", ec=MOTOR[1])
    text(ax, 76, 47, "DRV8833\ndual motor\ndriver", ha="center", fs=10, weight="bold")
    m = pin_row(ax, "left", 62, [("GND", 69.2), ("AIN1", 64), ("AIN2", 51.6), ("BIN1", 40),
                                 ("BIN2", 25.2)])
    t = pin_row(ax, "top", 74, [("VM", 78)])
    b = pin_row(ax, "bottom", 20, [("SLP", 70), ("FLT", 82)])
    o = pin_row(ax, "right", 90, [("AOUT1", 67), ("AOUT2", 57), ("BOUT1", 41), ("BOUT2", 31)])
    net.wire([p["GND"], m["GND"]], COL["gnd"])
    net.wire([p["D2"], (33, 56), (33, 64), m["AIN1"]], MOTOR[0])
    net.wire([p["D3"], m["AIN2"]], MOTOR[1])
    net.wire([p["D8"], (41, 29.6), (41, 40), m["BIN1"]], MOTOR[2])
    net.wire([p["D9"], m["BIN2"]], MOTOR[3])
    for x, y, name in ((52, 64, "R3"), (47, 51.6, "R4"), (55, 40, "R5"), (50, 25.2, "R6")):
        dot(ax, x, y)
        resistor(ax, x, y, x, y - 6.5, f"{name} 100 kΩ", side=-1, fs=7)
        gnd(ax, x, y - 6.5)

    net.wire([t["VM"], (78, 86)], COL["vbat"])
    flag(ax, 78, 86, "VBAT", COL["vbat"], side="up", fs=7)
    net.wire([(78, 84), (86, 84), (98, 84)], COL["vbat"])
    dot(ax, 78, 84, COL["vbat"])
    dot(ax, 86, 84, COL["vbat"])
    cap(ax, 86, 84, 86, 78.5, None, polar=True)
    gnd(ax, 86, 78.5)
    text(ax, 87.8, 81.2, "C1\n1000 µF", fs=7, weight="bold")
    cap(ax, 98, 84, 98, 78.5, None)
    gnd(ax, 98, 78.5)
    text(ax, 99.8, 81.2, "C2\n100 nF", fs=7, weight="bold")
    text(ax, 70, 76.4, "GND terminal = header GND", ha="center", fs=6.5, color="#555")

    net.wire([b["SLP"], (70, 15)], COL["en"])
    flag(ax, 70, 15, "MOTOR_EN", COL["en"], side="down", fs=7)
    net.wire([b["FLT"], (82, 15)], COL["en"])
    flag(ax, 82, 15, "FAULT", COL["en"], side="down", fs=7)
    text(ax, 76, 8.6, "SLP ← Q2 safe switch (PCF P2)   ·   FLT → PCF P3, R21 10 kΩ to 3V3",
         ha="center", fs=7.5)

    for (a, bb, cy, cname, mname) in (("AOUT1", "AOUT2", 62, "C3", "M1\nleft"),
                                      ("BOUT1", "BOUT2", 36, "C4", "M2\nright")):
        ya, yb = o[a][1], o[bb][1]
        net.wire([o[a], (106, ya), (106, cy + 4.5)], MOTOR[1])
        net.wire([o[bb], (106, yb), (106, cy - 4.5)], MOTOR[1])
        dot(ax, 98, ya, MOTOR[1])
        dot(ax, 98, yb, MOTOR[1])
        cap(ax, 98, ya, 98, yb, None)
        text(ax, 96.2, cy, cname, ha="right", fs=7, weight="bold")
        motor(ax, 106, cy, 4.5, mname, fs=7.5)
    text(ax, 106, 26.4, "encoder wires: tape back", ha="center", fs=7, color="#555")

    info_panel(ax, used, [
        ("What it does", [
            "Two H-bridges. The XIAO sets direction and speed with PWM on four inputs. The "
            "driver switches battery current through the motors.",
        ]),
        ("Pin by pin", [
            "|VM   ← VBAT (C1 1000 µF + C2 100 nF to GND)",
            "|GND  → common ground",
            "|SLP  ← MOTOR_EN (Q2, PCF P2)  high = awake",
            "|FLT  → FAULT (PCF P3), R21 10 kΩ to 3V3",
            "|AIN1 ← D2   AIN2 ← D3   (R3, R4 to GND)",
            "|BIN1 ← D8   BIN2 ← D9   (R5, R6 to GND)",
            "|AOUT1/AOUT2 → left motor   (C3 across it)",
            "|BOUT1/BOUT2 → right motor  (C4 across it)",
            "There is no logic supply pin. The module's VCC or VM pin is the motor supply.",
        ]),
        ("Specs", [
            "- VM 2.7–10.8 V. 1.5 A RMS, 2 A peak per bridge. Built-in overcurrent and thermal "
            "shutdown. SLP needs 2.5 V to wake; inputs read high above 2.0 V; wake takes 1 ms.",
        ]),
        ("Truth table, per motor", [
            "|IN1   IN2   motor",
            "|0     0     coast (stop)",
            "|PWM   0     forward",
            "|0     PWM   reverse (disabled on the table)",
            "|1     1     brake",
        ]),
        ("Check", [
            "- Wheels in the air first. Stall current under 0.4 A per motor, or use the N20 "
            "fallback. Wrong direction: swap that motor's two leads.",
            "- J3 on the Sense board is cut, so D8 / D9 sit low at reset.",
        ]),
    ])
    save(fig, PARTS / "06-drv8833-motors.png")


def part_max98357():
    used = {"GND": COL["gnd"], "D6": AUDIO[0], "D7": AUDIO[1], "D10": AUDIO[2]}
    fig, ax, p, net = part_frame(
        "07 · MAX98357A I2S amplifier and speaker",
        "Digital audio on D6 / D7 / D10. Power from VBAT. SD from the Q1 safe switch.", used)
    box(ax, 60, 16, 26, 59, "", fc="#e6f5e6", ec=AUDIO[1])
    text(ax, 73, 50, "MAX98357A\nI2S class-D\namplifier", ha="center", fs=10, weight="bold")
    m = pin_row(ax, "left", 60, [("GND", 69.2), ("SD", 62), ("BCLK", 38.4), ("LRC", 34),
                                 ("DIN", 20.8)])
    t = pin_row(ax, "top", 75, [("VIN", 66)])
    r = pin_row(ax, "right", 86, [("GAIN", 64), ("OUT+", 50), ("OUT−", 42)])
    net.wire([p["GND"], m["GND"]], COL["gnd"])
    net.wire([p["D6"], m["BCLK"]], AUDIO[0])
    net.wire([p["D7"], m["LRC"]], AUDIO[1])
    net.wire([p["D10"], m["DIN"]], AUDIO[2])
    net.wire([m["SD"], (54, 62)], COL["en"])
    flag(ax, 54, 62, "AMP_EN (Q1)", COL["en"], fs=7)

    net.wire([t["VIN"], (66, 88)], COL["vbat"])
    flag(ax, 66, 88, "VBAT", COL["vbat"], side="up", fs=7)
    net.wire([(66, 85), (74, 85), (84, 85)], COL["vbat"])
    dot(ax, 66, 85, COL["vbat"])
    dot(ax, 74, 85, COL["vbat"])
    cap(ax, 74, 85, 74, 79.5, None, polar=True)
    gnd(ax, 74, 79.5)
    text(ax, 75.8, 82.2, "C5\n100 µF", fs=7, weight="bold")
    cap(ax, 84, 85, 84, 79.5, None)
    gnd(ax, 84, 79.5)
    text(ax, 85.8, 82.2, "C6\n100 nF", fs=7, weight="bold")

    net.wire([r["GAIN"], (90, 64)], COL["vbat"])
    resistor(ax, 90, 64, 99, 64, "R22 100 kΩ", fs=7)
    flag(ax, 99, 64, "VBAT (= VIN)", COL["vbat"], side="right", fs=7)
    net.wire([r["OUT+"], (98, 50), (98, 47.2), (101, 47.2)], AUDIO[1])
    net.wire([r["OUT−"], (96, 42), (96, 44.8), (101, 44.8)], AUDIO[1])
    speaker(ax, 101, 46)
    text(ax, 104, 38.6, "LS1 speaker\n4 Ω, ~1 W", ha="center", fs=7.5, weight="bold")
    text(ax, 102, 33, "OUT− is not ground.\nNever wire a speaker\nlead to GND.",
         ha="center", va="top", fs=7.3, color="#a00")

    info_panel(ax, used, [
        ("What it does", [
            "Takes I2S digital audio straight from the XIAO and drives the speaker. No DAC, no "
            "master clock.",
        ]),
        ("Pin by pin", [
            "|VIN  ← VBAT (C5 100 µF + C6 100 nF to GND)",
            "|GND  → common ground",
            "|SD   ← AMP_EN (Q1, PCF P1)  low = shut down",
            "|GAIN → R22 100 kΩ → VIN   (3 dB gain)",
            "|BCLK ← D6 (GPIO43)",
            "|LRC  ← D7 (GPIO44)",
            "|DIN  ← D10 (GPIO9)",
            "|OUT+ / OUT− → speaker only",
            "Board pin order differs between modules; match the printed names.",
        ]),
        ("Straps", [
            "- SD below 0.16 V = off. Above 1.4 V = left channel. The 22 kΩ pull-up and the "
            "chip's 100 kΩ pulldown put the enabled line near 2.7 V, so it plays the left slot.",
            "- GAIN: VDD via 100 kΩ = 3 dB, VDD = 6, open = 9 (module default), GND = 12, "
            "GND via 100 kΩ = 15 dB.",
        ]),
        ("Specs", [
            "2.5–5.5 V supply. About 3 W into 4 Ω at 5 V; quieter on one cell. Audio is 16-bit "
            "mono, 16 kHz, left slot.",
        ]),
        ("Watch out", [
            "- D6 prints the boot log at reset. The amp is shut down then, so the speaker stays "
            "quiet.",
            "- Stop the microphone before playback, or Bob hears himself.",
        ]),
    ])
    save(fig, PARTS / "07-max98357-speaker.png")


def part_touch():
    used = {"D0": COL["touch"]}
    fig, ax, p, net = part_frame(
        "08 · Copper touch pad — wake and the motion unlock",
        "One wire from D0 through R13. Touch wakes Bob from deep sleep; a 2-second hold unlocks "
        "motion.", used)
    net.wire([p["D0"], (31, 64.8)], COL["touch"])
    resistor(ax, 31, 64.8, 41, 64.8, "R13 470 Ω", fs=7.8)
    net.wire([(41, 64.8), (70, 64.8)], COL["touch"])
    text(ax, 55.5, 62.6, "short wire, under 10 cm", ha="center", fs=7.5, color="#555")
    text(ax, 36, 69.6, "next to the XIAO pin", ha="center", fs=7, color="#555")
    ax.add_patch(FancyBboxPatch((70, 52), 30, 26, boxstyle="round,pad=0,rounding_size=1.5",
                                fc="#e8a86a", ec="#b06a2a", lw=2, zorder=2, hatch="//"))
    dot(ax, 70, 64.8, "#7a4a1a")
    ax.text(85, 65, "Copper foil pad\n≈ 20 × 30 mm\ninside the shell", ha="center",
            va="center", fontsize=9, weight="bold", zorder=6, linespacing=1.25,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#b06a2a", alpha=0.9))
    text(ax, 85, 48.8, "keep it at least 3 cm from the antenna,\nmotor wires and any ground copper",
         ha="center", fs=7.5, color="#a00")

    box(ax, 38, 8, 72, 32, "", fc="#ffffff", ec="#999", ls="--")
    text(ax, 40, 37.6, "Fallback, only if the pad fails Phase 2 or Phase 7: TTP223 module",
         fs=8, weight="bold")
    box(ax, 62, 14, 18, 18, "TTP223", fc="#f2f2f2", fs=8.5)
    tp = pin_row(ax, "left", 62, [("VCC", 27), ("I/O", 22.5), ("GND", 18)])
    net.wire([tp["VCC"], (56, 27)], COL["v33"])
    flag(ax, 56, 27, "3V3", COL["v33"], fs=7)
    net.wire([tp["I/O"], (56, 22.5)], COL["touch"])
    flag(ax, 56, 22.5, "D0 (via R13)", COL["touch"], fs=7)
    net.wire([tp["GND"], (57, 18)], COL["gnd"])
    gnd(ax, 57, 18)
    text(ax, 82, 23, "Then wake with ext0 on\nGPIO1 instead of touch\nwake. Same pin, same\nfirmware "
         "otherwise.", fs=7.5)

    info_panel(ax, used, [
        ("What it does", [
            "The ESP32-S3 measures the pad's capacitance. A finger raises it. Touch channel 1 can "
            "wake the chip from deep sleep, so the pad is Bob's wake button.",
        ]),
        ("Pin by pin", [
            "|XIAO D0 (GPIO1, TOUCH1) → R13 470 Ω → pad",
        ]),
        ("Why R13", [
            "Espressif recommends a 470 Ω–2 kΩ series resistor (510 Ω typical) within a few mm "
            "of the touch pin. It forms a small RC filter with the wire and helps against static "
            "discharge. 470 Ω is the same value as the sensor LED resistors.",
        ]),
        ("Build", [
            "- Self-adhesive copper foil behind a thin plastic or cardboard wall.",
            "- Solder the wire to a folded corner of the foil, then tape over it.",
            "- Re-run the touch test on the finished body: the shell changes the numbers.",
        ]),
        ("Firmware", [
            "Read touchRead(T1) touched and untouched, set the threshold between them. Use "
            "touchSleepWakeUpEnable(T1, threshold) before deep sleep. Do not copy the classic "
            "ESP32 pin numbers from generic samples.",
        ]),
    ])
    save(fig, PARTS / "08-touch-pad.png")


def part_bumper():
    used = {"3V3": COL["v33"], "GND": COL["gnd"], "D1": COL["bump"]}
    fig, ax, p, net = part_frame(
        "09 · Bumper — two microswitches in parallel",
        "Either switch pulls D1 low. R14 is the pull-up; C14 filters motor noise.", used)
    net.wire([p["3V3"], (40, 73.6)], COL["v33"])
    resistor(ax, 40, 73.6, 40, 63, "R14 10 kΩ", fs=7.8)
    net.wire([(40, 63), (40, 60.4)], COL["bump"])
    gnd(ax, p["GND"][0], p["GND"][1])
    net.wire([p["D1"], (40, 60.4), (50, 60.4), (70, 60.4)], COL["bump"])
    dot(ax, 40, 60.4, COL["bump"])
    dot(ax, 50, 60.4, COL["bump"])
    cap(ax, 50, 60.4, 50, 53, "C14 100 nF", fs=7.8)
    gnd(ax, 50, 53)
    dot(ax, 70, 60.4, COL["bump"])
    net.wire([(70, 60.4), (70, 68), (76, 68)], COL["bump"])
    net.wire([(70, 60.4), (70, 52), (76, 52)], COL["bump"])
    switch(ax, 76, 86, 68, COL["bump"])
    switch(ax, 76, 86, 52, COL["bump"])
    net.wire([(86, 68), (94, 68), (94, 52)], COL["gnd"])
    net.wire([(86, 52), (94, 52), (94, 47)], COL["gnd"])
    dot(ax, 94, 52, COL["gnd"])
    gnd(ax, 94, 47)
    text(ax, 81, 73, "SW2 left bumper", ha="center", fs=8, weight="bold")
    text(ax, 81, 57, "SW3 right bumper", ha="center", fs=8, weight="bold")
    for y in (68, 52):
        text(ax, 76, y - 1.8, "NO", ha="center", fs=6.5, color="#555")
        text(ax, 86, y - 1.8, "COM", ha="center", fs=6.5, color="#555")

    box(ax, 38, 8, 72, 30, "", fc="#ffffff", ec="#999", ls="--")
    text(ax, 40, 35.6, "Which legs to use on a 3-pin microswitch", fs=8, weight="bold")
    ax.add_patch(Rectangle((50, 17), 22, 10, fc="#2b2b2b", ec="#111", zorder=3))
    ax.plot([52, 71], [27, 31], color="#999", lw=3, zorder=3)
    for x, name, color in ((53, "COM", COL["gnd"]), (61, "NO", COL["bump"]),
                           (69, "NC", "#aaa")):
        ax.plot([x, x], [17, 12.5], color=color, lw=3, zorder=3)
        text(ax, x, 10.8, name, ha="center", fs=7.5, weight="bold")
    text(ax, 76, 23, "COM → GND\nNO → D1\nNC → leave empty\n\nThe print varies:\nconfirm with "
         "a meter.", fs=7.5)

    info_panel(ax, used, [
        ("What it does", [
            "A front bump closes one switch and pulls D1 to ground. Firmware stops both motors "
            "at once and never reverses on its own.",
        ]),
        ("Pin by pin", [
            "|D1 (GPIO2) ← R14 10 kΩ ← 3V3",
            "|D1         → C14 100 nF → GND",
            "|D1         ← SW2 NO,  SW2 COM → GND",
            "|D1         ← SW3 NO,  SW3 COM → GND",
        ]),
        ("Why R14 and C14", [
            "The internal pull-up is about 45 kΩ, weak for wires that run past the motors. "
            "R14 10 kΩ holds the line firmly high; with C14 it forms a 1 ms filter that ignores "
            "motor spikes but still sees a real bump.",
        ]),
        ("Firmware", [
            "pinMode(D1, INPUT_PULLUP) is still fine. LOW = pressed. Stop on the first LOW "
            "reading; require 20 ms HIGH before the bumper counts as released.",
        ]),
        ("Check", [
            "D1 reads about 3.3 V released and 0 V with either switch held. A reading stuck LOW "
            "at boot means a shorted switch: motion stays locked.",
        ]),
    ])
    save(fig, PARTS / "09-bumper.png")


if __name__ == "__main__":
    figure_wiring()
    figure_details()
    for fn in (part_xiao, part_power, part_oled, part_ads1115, part_sensors, part_pcf8574,
               part_drv8833, part_max98357, part_touch, part_bumper):
        print(fn.__name__)
        fn()
    print(f"saved to {OUT}")
