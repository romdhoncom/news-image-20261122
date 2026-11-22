#!/usr/bin/env python3
"""Sunday 22 November 2026 in one image.

A dense newspaper front page drawn with pure Python standard library:
own raster canvas, own bitmap font, own PNG encoder. No PIL, no network,
no randomness, no clock -- two runs write byte-identical files.

Layout (1024x1024):
  masthead with the day named in full
  3 lead stories with code-drawn pictures
  middle band: world map with numbered pins + 2 more leads
  "MORE FROM SUNDAY": 38 further verified stories, two columns
  date-check strip along the bottom
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- canvas
# Flat RGB bytearray, row-major.
PIX = bytearray(W * H * 3)


def rgb(hexstr):
    hexstr = hexstr.lstrip("#")
    return (int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


PAPER = rgb("faf6ec")
INK = rgb("1a1a1a")
RED = rgb("b02020")
DARKRED = rgb("8c1a1a")
NAVY = rgb("1f3a5f")
BLUE = rgb("2b6cb0")
SKY = rgb("bcd6e8")
LAND = rgb("c9bd93")
LAND2 = rgb("b5a878")
GREY = rgb("5a5a5a")
LIGHTGREY = rgb("e4ddc9")
GOLD = rgb("d9a441")
GREEN = rgb("2e7d32")
ORANGE = rgb("e67e22")
DARK = rgb("222222")


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i] = c[0]
        PIX[i + 1] = c[1]
        PIX[i + 2] = c[2]


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            PIX[i] = c[0]
            PIX[i + 1] = c[1]
            PIX[i + 2] = c[2]


def hline(x, y, w, c):
    fill_rect(x, y, w, 1, c)


def vline(x, y, h, c):
    fill_rect(x, y, 1, h, c)


def line(x0, y0, x1, y1, c):
    """Bresenham line."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        fill_rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)


def fill_ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t < 0:
            continue
        dx = int(rx * (t ** 0.5))
        fill_rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)


def fill_poly(points, c):
    """Scanline polygon fill. points: list of (x, y)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = points[i]
            x1, yy1 = points[(i + 1) % n]
            if yy0 == yy1:
                continue
            if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                x = x0 + (y - yy0) * (x1 - x0) / (yy1 - yy0)
                xs.append(x)
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = int(xs[k] + 0.5)
            xb = int(xs[k + 1] + 0.5)
            if xb >= xa:
                fill_rect(xa, y, xb - xa + 1, 1, c)


def triangle(x0, y0, x1, y1, x2, y2, c):
    fill_poly([(x0, y0), (x1, y1), (x2, y2)], c)


# ---------------------------------------------------------------- PNG
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path, width, height, pixels):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)  # filter: none
        raw += pixels[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 6)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_chunk(b"IHDR", ihdr))
        f.write(_chunk(b"IDAT", idat))
        f.write(_chunk(b"IEND", b""))

# ---------------------------------------------------------------- font
# 5x7 bitmap font, uppercase + digits + punctuation. Each glyph is 7 rows
# of 5 bits, bit 4 = leftmost pixel. Drawn by hand; kept to ASCII only so
# every headline spells exactly what was verified.
FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (15, 16, 16, 16, 16, 16, 15),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (15, 16, 16, 19, 17, 17, 14),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 19, 21, 25, 17, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (14, 16, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 4, 4, 4),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 1, 14),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 12, 8),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 10, 0, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 2, 4, 0, 4),
    "-": (0, 0, 0, 14, 0, 0, 0),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "/": (1, 1, 2, 4, 8, 16, 16),
    "%": (25, 26, 2, 4, 8, 19, 19),
    "$": (4, 15, 20, 14, 5, 30, 4),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "+": (0, 4, 4, 14, 4, 4, 0),
    "=": (0, 0, 14, 0, 14, 0, 0),
    "*": (0, 4, 21, 14, 21, 4, 0),
    "#": (10, 10, 31, 10, 31, 10, 10),
    "@": (14, 17, 23, 21, 23, 16, 14),
    "_": (0, 0, 0, 0, 0, 0, 31),
    "[": (14, 8, 8, 8, 8, 8, 14),
    "]": (14, 2, 2, 2, 2, 2, 14),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, c):
    """Draw uppercase ASCII text; returns width drawn."""
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    fill_rect(cx + col * scale, y + row * scale, scale, scale, c)
        cx += 6 * scale
    return cx - x


def draw_text_centered(cx, y, s, scale, c):
    w = text_w(s, scale)
    draw_text(cx - w // 2, y, s, scale, c)
    return w


def wrap_text(s, scale, max_w):
    """Word-wrap to lines of at most max_w pixels. Returns list of lines."""
    words = s.upper().split(" ")
    lines = []
    cur = ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, scale, c, max_w, line_h):
    """Draw a wrapped paragraph; returns y after the last line."""
    for ln in wrap_text(s, scale, max_w):
        draw_text(x, y, ln, scale, c)
        y += line_h
    return y

# ---------------------------------------------------------------- pictures
# Small code-drawn scenes. Each takes the top-left corner and a width/height
# and draws inside that box. Kept simple and bold so they read at 300 px.

def pic_globe_flame(x, y, w, h):
    """COP31: a globe under a red flame, with a broken-deal crack."""
    fill_rect(x, y, w, h, rgb("dcebf5"))
    cx, cy, r = x + w // 2, y + h // 2 + 12, 62
    fill_circle(cx, cy, r, rgb("3a7bd5"))
    fill_circle(cx - 6, cy - 6, r - 8, rgb("4a90e2"))
    # land blobs
    fill_ellipse(cx - 22, cy - 18, 20, 12, rgb("3d9b4f"))
    fill_ellipse(cx + 18, cy + 8, 24, 14, rgb("3d9b4f"))
    fill_ellipse(cx - 8, cy + 28, 16, 9, rgb("3d9b4f"))
    fill_ellipse(cx + 26, cy - 26, 12, 8, rgb("3d9b4f"))
    # flame above the globe
    fx, fy = cx, y + 8
    fill_poly([(fx - 16, fy + 34), (fx - 6, fy + 14), (fx, fy),
               (fx + 6, fy + 14), (fx + 16, fy + 34), (fx, fy + 26)],
              rgb("e67e22"))
    fill_poly([(fx - 9, fy + 34), (fx - 3, fy + 20), (fx, fy + 12),
               (fx + 3, fy + 20), (fx + 9, fy + 34)], rgb("c0392b"))
    # crack across the globe: a jagged dark line
    line(cx - 40, cy - 30, cx - 18, cy - 8, DARK)
    line(cx - 18, cy - 8, cx - 30, cy + 14, DARK)
    line(cx - 30, cy + 14, cx - 8, cy + 34, DARK)
    line(cx - 8, cy + 34, cx - 20, cy + 52, DARK)
    # "NO DEAL" stamp
    fill_rect(x + w - 108, y + h - 30, 100, 22, RED)
    draw_text(x + w - 100, y + h - 25, "NO DEAL", 1, rgb("ffffff"))


def pic_helicopter(x, y, w, h):
    """Mexico: desert mountains, a helicopter, a capture star."""
    fill_rect(x, y, w, h, rgb("f2e3c6"))
    fill_rect(x, y + h - 46, w, 46, rgb("c98f4e"))
    # mountains
    fill_poly([(x, y + h - 46), (x + 70, y + 30), (x + 140, y + h - 46)],
              rgb("8a6d3b"))
    fill_poly([(x + 90, y + h - 46), (x + 180, y + 10), (x + 260, y + h - 46)],
              rgb("a08050"))
    fill_poly([(x + 200, y + h - 46), (x + 270, y + 44), (x + w, y + h - 46)],
              rgb("8a6d3b"))
    # sun
    fill_circle(x + w - 40, y + 26, 16, GOLD)
    # helicopter
    hx, hy = x + w // 2 - 10, y + 52
    fill_ellipse(hx + 20, hy + 10, 34, 14, DARK)
    fill_rect(hx + 52, hy + 4, 46, 8, DARK)
    fill_rect(hx + 92, hy - 6, 8, 18, DARK)
    line(hx - 8, hy - 2, hx + 48, hy - 2, DARK)
    line(hx - 8, hy - 2, hx + 48, hy - 2, DARK)
    fill_rect(hx - 22, hy - 4, 84, 3, DARK)
    fill_rect(hx + 8, hy + 24, 4, 12, DARK)
    fill_rect(hx + 30, hy + 24, 4, 12, DARK)
    fill_circle(hx + 34, hy + 8, 7, SKY)
    # capture star badge
    sx, sy = x + 26, y + h - 78
    fill_circle(sx, sy, 22, GOLD)
    fill_circle(sx, sy, 17, rgb("f7d774"))
    draw_text(sx - 9, sy - 4, "11", 1, DARKRED)
    draw_text(x + 52, sy - 4, "KILLED", 1, DARKRED)


def pic_missile_ship(x, y, w, h):
    """Iran / Bahrain: a tanker at sea, a missile with smoke, a blast."""
    fill_rect(x, y, w, h, rgb("dcebf5"))
    fill_rect(x, y + h - 58, w, 58, rgb("2b6cb0"))
    # waves
    for wx in range(x, x + w, 36):
        fill_ellipse(wx + 18, y + h - 58, 20, 5, rgb("7fb3e0"))
        fill_ellipse(wx + 18, y + h - 34, 20, 5, rgb("7fb3e0"))
    # tanker
    tx, ty = x + 40, y + h - 92
    fill_rect(tx, ty + 18, 190, 26, DARK)
    fill_rect(tx + 150, ty, 40, 18, rgb("8c1a1a"))
    fill_rect(tx + 20, ty - 12, 26, 30, RED)
    fill_rect(tx + 52, ty - 12, 26, 30, GOLD)
    fill_rect(tx + 84, ty - 12, 26, 30, rgb("2e7d32"))
    fill_rect(tx + 116, ty - 12, 26, 30, BLUE)
    # missile streaking down from upper right
    mx, my = x + w - 70, y + 14
    fill_poly([(mx, my), (mx + 10, my + 26), (mx + 4, my + 30),
               (mx - 6, my + 8)], rgb("c0392b"))
    line(mx + 2, my + 30, mx - 26, my + 62, rgb("dddddd"))
    line(mx + 2, my + 30, mx - 34, my + 78, rgb("bbbbbb"))
    # blast on the water
    bx, by = x + w - 92, y + h - 66
    fill_circle(bx, by, 20, ORANGE)
    fill_circle(bx, by, 13, GOLD)
    fill_circle(bx, by, 7, rgb("fff3b0"))


def pic_city_blast(x, y, w, h):
    """Ukraine: a city skyline at night, one building hit, blast and smoke.
    Every element scales to the box so nothing spills into the next column."""
    fill_rect(x, y, w, h, rgb("1f2a3a"))
    # stars
    for sx, sy in ((0.06, 0.12), (0.16, 0.26), (0.30, 0.09), (0.40, 0.22),
                   (0.09, 0.45), (0.47, 0.38)):
        set_px(x + int(sx * w), y + int(sy * h), rgb("ffffff"))
        set_px(x + int(sx * w) + 1, y + int(sy * h), rgb("ffffff"))
    # buildings: (x_frac, w_frac, h_frac)
    blds = ((0.02, 0.13, 0.55), (0.17, 0.11, 0.75), (0.30, 0.12, 0.48),
            (0.44, 0.11, 0.82), (0.57, 0.13, 0.58))
    for xf, wf, hf in blds:
        bx = x + int(xf * w)
        bw = max(8, int(wf * w))
        bh = int(hf * h)
        fill_rect(bx, y + h - bh, bw, bh, rgb("0e1420"))
        for wy in range(y + h - bh + 6, y + h - 6, 11):
            for wx in range(bx + 4, bx + bw - 4, 9):
                fill_rect(wx, wy, 3, 4, GOLD)
    # damaged building with a hole and smoke
    dx = x + int(0.74 * w)
    dw = max(10, int(0.20 * w))
    dh = int(0.85 * h)
    dy = y + h - dh
    fill_rect(dx, dy, dw, dh, rgb("0e1420"))
    fill_circle(dx + dw // 2, dy + 10, 7, rgb("1f2a3a"))
    for ox, oy in ((-4, -14), (6, -24), (16, -18)):
        fill_circle(dx + dw // 2 + ox, dy + oy, 8, rgb("8a8a8a"))
        fill_circle(dx + dw // 2 + ox, dy + oy, 5, rgb("aaaaaa"))
    # red blast starburst
    ex, ey = dx + dw // 2, dy + 26
    fill_poly([(ex, ey - 20), (ex + 6, ey - 6), (ex + 20, ey),
               (ex + 6, ey + 6), (ex, ey + 20), (ex - 6, ey + 6),
               (ex - 20, ey), (ex - 6, ey - 6)], rgb("e74c3c"))
    fill_circle(ex, ey, 7, GOLD)


def pic_falling_chart(x, y, w, h):
    """Markets: a red line falling hard, bars behind it, -3.7% tag.
    All heights scale to the box so the line and arrow stay inside."""
    fill_rect(x, y, w, h, rgb("ffffff"))
    # bars, heights as fractions of the box
    fracs = (0.42, 0.48, 0.54, 0.45, 0.51, 0.38, 0.32, 0.25, 0.19, 0.13)
    bw = w // len(fracs)
    for i, f in enumerate(fracs):
        bh = int(f * (h - 16))
        fill_rect(x + i * bw + 4, y + h - 12 - bh, bw - 8, bh, rgb("c9d6e8"))
    # falling line, points as fractions of the box
    fx = (0.03, 0.16, 0.30, 0.44, 0.57, 0.71, 0.85, 0.97)
    fy = (0.14, 0.26, 0.22, 0.44, 0.40, 0.64, 0.72, 0.86)
    pts = [(x + int(a * w), y + int(b * h)) for a, b in zip(fx, fy)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED)
        line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1, RED)
    # arrow head at the end
    ex, ey = pts[-1]
    fill_poly([(ex, ey), (ex - 14, ey - 2), (ex - 5, ey - 12)], RED)
    # tag
    fill_rect(x + w - 118, y + 8, 110, 24, RED)
    draw_text(x + w - 110, y + 13, "-3.7% S&P", 1, rgb("ffffff"))
    draw_text(x + 8, y + h - 12, "NASDAQ -5.3%", 1, DARKRED)

# ---------------------------------------------------------------- map
# Coarse continent outlines in (lon, lat), drawn equirectangular into the
# map box so the numbered pins land on the right part of the world.
MAP_X, MAP_Y, MAP_W, MAP_H = 12, 344, 640, 232


def proj(lon, lat):
    return (MAP_X + int((lon + 180.0) / 360.0 * MAP_W),
            MAP_Y + int((90.0 - lat) / 180.0 * MAP_H))


CONTINENTS = [
    # North America
    [(-168, 66), (-150, 70), (-130, 71), (-110, 73), (-95, 80), (-85, 76),
     (-80, 73), (-70, 62), (-60, 55), (-55, 47), (-65, 44), (-70, 42),
     (-75, 38), (-76, 34), (-80, 32), (-81, 26), (-85, 21), (-90, 21),
     (-95, 19), (-100, 17), (-105, 20), (-110, 23), (-115, 28), (-120, 34),
     (-125, 40), (-125, 49), (-130, 55), (-140, 60), (-155, 58), (-165, 60)],
    # Greenland
    [(-45, 60), (-30, 65), (-25, 70), (-35, 76), (-55, 76), (-60, 70),
     (-55, 64)],
    # South America
    [(-79, 9), (-72, 12), (-62, 10), (-52, 5), (-50, 0), (-44, -3),
     (-38, -5), (-35, -9), (-39, -15), (-41, -22), (-48, -28), (-55, -34),
     (-62, -39), (-68, -45), (-70, -52), (-68, -55), (-72, -50), (-73, -40),
     (-72, -30), (-70, -20), (-75, -15), (-80, -5), (-81, 0), (-80, 6)],
    # Europe
    [(-10, 36), (-9, 38), (-9, 43), (-4, 48), (-1, 46), (-2, 49), (2, 51),
     (5, 53), (8, 55), (8, 57), (10, 59), (13, 56), (18, 56), (21, 55),
     (24, 58), (27, 60), (30, 62), (32, 65), (35, 66), (40, 68), (44, 66),
     (40, 60), (38, 55), (35, 50), (33, 46), (30, 44), (28, 42), (26, 40),
     (23, 37), (20, 40), (18, 42), (15, 44), (12, 44), (8, 44), (3, 43),
     (0, 40), (-2, 37), (-6, 36)],
    # Africa
    [(-17, 15), (-16, 20), (-13, 27), (-10, 30), (-6, 33), (0, 36),
     (10, 37), (11, 34), (15, 32), (20, 32), (25, 32), (30, 31), (32, 30),
     (35, 28), (37, 22), (40, 18), (43, 12), (48, 11), (51, 11), (50, 5),
     (48, 0), (44, -5), (40, -10), (37, -15), (35, -20), (33, -25),
     (30, -30), (26, -33), (20, -35), (17, -32), (15, -27), (13, -20),
     (12, -15), (13, -10), (12, -5), (9, 0), (9, 4), (4, 6), (-2, 5),
     (-8, 5), (-13, 8), (-17, 12)],
    # Asia (mainland)
    [(30, 70), (35, 68), (40, 67), (45, 68), (50, 69), (55, 70), (60, 70),
     (65, 71), (70, 72), (75, 73), (80, 73), (85, 74), (90, 75), (95, 76),
     (100, 76), (105, 77), (110, 75), (115, 73), (120, 72), (125, 71),
     (130, 72), (135, 71), (140, 72), (145, 70), (150, 70), (155, 68),
     (160, 66), (165, 66), (170, 66), (175, 65), (178, 64), (175, 62),
     (170, 60), (165, 60), (160, 58), (158, 55), (155, 58), (150, 60),
     (145, 60), (142, 55), (140, 50), (138, 45), (135, 44), (130, 42),
     (128, 38), (126, 36), (122, 32), (120, 28), (118, 25), (115, 22),
     (112, 21), (110, 18), (108, 12), (106, 10), (104, 8), (102, 6),
     (100, 5), (98, 8), (97, 12), (95, 16), (93, 20), (91, 22), (89, 22),
     (87, 21), (85, 19), (83, 17), (80, 15), (78, 10), (76, 8), (75, 10),
     (73, 15), (72, 20), (70, 22), (68, 24), (66, 25), (64, 25), (62, 26),
     (60, 25), (58, 26), (56, 27), (54, 28), (52, 29), (50, 30), (48, 30),
     (46, 29), (44, 29), (42, 30), (40, 31), (38, 32), (36, 36), (34, 38),
     (32, 42), (30, 45), (28, 48), (30, 55), (30, 62)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 38), (142, 42), (144, 44),
     (141, 45), (139, 40), (136, 36), (132, 33)],
    # Sumatra
    [(95, 5), (98, 2), (100, 0), (103, -3), (105, -5), (103, -6),
     (100, -3), (97, 0)],
    # Borneo
    [(109, 1), (112, 3), (115, 5), (118, 2), (117, -2), (114, -4),
     (110, -3)],
    # New Guinea
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8), (147, -9),
     (142, -8), (137, -6), (132, -4)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -33), (130, -32),
     (135, -35), (138, -35), (140, -38), (145, -38), (150, -37), (153, -32),
     (153, -27), (150, -22), (146, -19), (142, -15), (142, -11), (137, -12),
     (135, -15), (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (176, -38), (178, -37), (175, -40),
     (172, -43), (168, -46)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (44, -25),
     (43, -21)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (-1, 51)],
]

# (number, lon, lat, nudge_x, nudge_y) -- nudges keep crowded European pins
# readable. Numbers match the story numbers in the text.
PINS = [
    (1, 30.7, 37.0, 0, 0),      # COP31, Antalya
    (2, -107.0, 25.0, 0, 0),    # Mexico, Sinaloa
    (3, 50.5, 26.0, 0, 0),      # Iran / Bahrain
    (4, 33.4, 47.9, 0, 0),      # Kryvyi Rih
    (5, -74.0, 40.7, 0, 0),     # New York markets
    (6, 4.3, 52.0, 0, 0),       # ICJ, The Hague
    (7, 106.3, -6.2, 0, 0),     # Cikande fire
    (8, 3.4, 6.5, 0, 0),        # Nigeria boat
    (9, 21.0, 52.2, 0, 0),      # Poland
    (10, 34.5, 31.5, 6, 8),     # Gaza (nudged off Antalya)
    (11, -120.6, 34.6, 0, 0),   # SpaceX, Vandenberg
    (12, 121.5, 25.0, 0, 0),    # Taiwan
]


def draw_map():
    fill_rect(MAP_X, MAP_Y, MAP_W, MAP_H, SKY)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        fill_poly(pts, LAND)
    # continent labels
    draw_text(*proj(-100, 55), "N. AMERICA", 1, GREY)
    draw_text(*proj(-62, -18), "S. AMERICA", 1, GREY)
    draw_text(*proj(15, 62), "EUROPE", 1, GREY)
    draw_text(*proj(20, -2), "AFRICA", 1, GREY)
    draw_text(*proj(95, 55), "ASIA", 1, GREY)
    draw_text(*proj(134, -25), "AUSTRALIA", 1, GREY)
    # title bar
    fill_rect(MAP_X, MAP_Y, MAP_W, 20, NAVY)
    draw_text(MAP_X + 8, MAP_Y + 6, "WHERE IT HAPPENED", 1, rgb("ffffff"))
    draw_text(MAP_X + MAP_W - 190, MAP_Y + 6, "12 STORIES PINNED", 1,
              rgb("ffd166"))
    # pins
    for num, lon, lat, nx, ny in PINS:
        px, py = proj(lon, lat)
        px += nx
        py += ny
        fill_circle(px, py, 9, RED)
        fill_circle(px, py, 7, rgb("ffffff"))
        fill_circle(px, py, 6, RED)
        label = str(num)
        draw_text(px - (3 if len(label) == 1 else 6), py - 3, label, 1,
                  rgb("ffffff"))

# ---------------------------------------------------------------- stories
# 43 verified stories for Sunday 22 November 2026. Leads carry a picture;
# the rest are one-line labels (<=41 chars so each fits its column at 2x).
# Every headline was checked against a live report on 22 Nov 2026.

LEADS_ROW1 = [
    # (picture, kicker, headline lines, sub)
    (pic_globe_flame, "CLIMATE - ANTALYA, TURKEY",
     ["CLIMATE TALKS", "COLLAPSE"],
     "No deal as the EU rejects a text with no mention of fossil fuels."),
    (pic_helicopter, "JUSTICE - SINALOA, MEXICO",
     ["CARTEL BOSS", "CAPTURED"],
     "'El Chapo Isidro' seized in a raid; 11 killed, four of them soldiers."),
    (pic_missile_ship, "CONFLICT - BAHRAIN AND THE GULF",
     ["IRAN STRIKES", "BAHRAIN"],
     "Missiles hit US bases; tankers struck near Hormuz."),
]

LEADS_RIGHT = [
    (pic_city_blast, "UKRAINE - KRYVYI RIH",
     ["MISSILE KILLS 2", "IN ZELENSKYY'S", "HOMETOWN"],
     "Russian strike kills a boy of 7 and a woman of 20; 60 wounded."),
    (pic_falling_chart, "MARKETS - NEW YORK",
     ["MARKETS IN", "CORRECTION"],
     "AI sell-off: S&P -3.7%, Nasdaq -5.3%, Nikkei -5.1%."),
]

MORE = [
    "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
    "EU-INDONESIA DEAL: 98.5% TARIFFS TO GO",
    "CANDY FACTORY FIRE: 3 DEAD, 36 MISSING",
    "BOAT CAPSIZES ON WAY TO FUNERAL, 24 DEAD",
    "KYIV FLATS HIT; 1 DEAD, 14 MISSING",
    "RUSSIAN CARGO SHIP ABLAZE IN BALTIC",
    "RUSSIAN MISSILES FALL IN POLAND",
    "NATO CHIEF: DEFEND EVERY INCH OF POLAND",
    "US: IRAN DID NOT ATTACK AN F-16",
    "HOUTHIS FIRE ON SAUDI ARABIA",
    "ISRAELI STRIKES CONTINUE IN GAZA",
    "SETTLER ATTACKS ARE TERRORISM",
    "LEBANON PRESIDENT BLAMES ISRAEL AND IRAN",
    "DENMARK EXPELS RUSSIAN ATTACHE OVER PLOT",
    "TRUMP-KIM SUMMIT BID FAILED, WSJ REPORTS",
    "TRUMP WANTS UKRAINE DEAL BY EARLY JANUARY",
    "TRUMP ORDERS FIRMS TO REPORT CONGRESS",
    "UK-EU STRIKE DEALS; BURNHAM EYES REJOIN",
    "LIVING-COST PROTESTS SPREAD IN EUROPE",
    "UN KILLER-ROBOT TALKS EXTENDED TO 2028",
    "PAOLO BULGARI DIES AT 89",
    "PHUMZILE MLAMBO-NGCUKA DIES AT 71",
    "BUKELE SEEKS THIRD TERM IN EL SALVADOR",
    "TAIWAN WARNS CANADA ON CHINA TIES",
    "EX-POLICE CHIEF FOUND DEAD, 1992 INQUIRY",
    "RUSSIA SEIZES ON US SECURITY OFFER",
    "SPACEX: 2 LAUNCHES IN 32 HOURS",
    "NEW PULSAR SPINS 261 TIMES A SECOND",
    "FIRST OTTER SATELLITE FAILS IN ORBIT",
    "MARS ROVER PHOTOGRAPHS TWILIGHT CLOUDS",
    "SPACEX TO RETIRE FIRST CAUGHT STARSHIP",
    "COLLEGE CHAOS: UCLA, INDIANA FALL IN OT",
    "GEORGIA INTO SEC TITLE GAME, 34-6",
    "BOISE STATE STUNNED 22-20",
    "NO. 2 UTAH CLINCHES BIG 12 TITLE GAME",
    "MIAMI CLINCHES ACC TITLE GAME",
    "OKLAHOMA BEATS TEXAS A&M 28-7",
    "OKLAHOMA STATE RALLIES FROM 17 DOWN",
]

STORY_COUNT = 5 + len(MORE)  # 43


# ---------------------------------------------------------------- layout
def draw_masthead():
    fill_rect(0, 0, W, 84, PAPER)
    draw_text_centered(W // 2, 8, "THE WORLD IN ONE PICTURE", 3, INK)
    draw_text_centered(W // 2, 34, "SUNDAY 22 NOVEMBER 2026", 4, RED)
    draw_text_centered(W // 2, 66,
                       "THE NEWS OF THE DAY, FROM ANTALYA TO SINALOA",
                       1, GREY)
    fill_rect(0, 84, W, 3, INK)
    fill_rect(0, 89, W, 1, INK)


def draw_leads_row1():
    cols = [12, 351, 690]
    for (pic, kicker, head, sub), x in zip(LEADS_ROW1, cols):
        pic(x, 94, 322, 146)
        draw_text(x, 246, kicker, 1, RED)
        y = 262
        for ln in head:
            draw_text(x, y, ln, 3, INK)
            y += 22
        draw_para(x, 308, sub, 1, GREY, 322, 11)


def draw_leads_right():
    # Two stacked leads to the right of the map.
    slots = [(344, 452), (460, 568)]
    for (pic, kicker, head, sub), (y0, y1) in zip(LEADS_RIGHT, slots):
        pic(664, y0, 140, y1 - y0)
        tx = 812
        draw_text(tx, y0 + 2, kicker, 1, RED)
        y = y0 + 16
        for ln in head:
            draw_text(tx, y, ln, 2, INK)
            y += 16
        draw_para(tx, y + 2, sub, 1, GREY, 200, 11)
        if y0 == 344:
            hline(664, 456, 348, LIGHTGREY)


def draw_more():
    fill_rect(0, 584, W, 2, INK)
    draw_text(12, 592, "MORE FROM SUNDAY", 2, INK)
    draw_text(1024 - 12 - text_w("38 MORE STORIES", 1), 596,
              "38 MORE STORIES", 1, GREY)
    cols = [12, 518]
    half = (len(MORE) + 1) // 2
    for ci, x in enumerate(cols):
        items = MORE[ci * half:(ci + 1) * half]
        y = 618
        for item in items:
            fill_rect(x, y + 4, 6, 6, RED)
            draw_text(x + 12, y, item, 2, INK)
            y += 19


def draw_date_strip():
    fill_rect(0, 988, W, 36, NAVY)
    draw_text_centered(
        W // 2, 1001,
        "CHECKED SUNDAY 22 NOVEMBER 2026 - 43 STORIES - "
        "EVERY EVENT VERIFIED AGAINST LIVE REPORTS",
        1, rgb("ffffff"))


def main():
    fill_rect(0, 0, W, H, PAPER)
    draw_masthead()
    draw_leads_row1()
    draw_map()
    draw_leads_right()
    draw_more()
    draw_date_strip()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    write_png(path, W, H, PIX)
    size = os.path.getsize(path)
    print("wrote %s (%d bytes, %d stories)" % (path, size, STORY_COUNT))


if __name__ == "__main__":
    main()
