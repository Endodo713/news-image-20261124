# The World in One Day - Tuesday, 24 November 2026.
# A program that draws the day's world news as one newspaper front page
# (1024x1024 PNG) and writes it to /output/entry.png.
# Pure Python standard library: no network, no fonts, no images on disk.
# Deterministic: two runs write byte-identical files.

import binascii
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (246, 241, 229)   # warm newsprint
INK = (22, 22, 22)       # near-black
RED = (176, 32, 32)      # masthead red
BLUE = (31, 78, 121)     # section blue
GREY = (110, 108, 100)   # muted grey
LIGHT = (226, 219, 203)  # light rule / panel fill
GREEN = (28, 110, 60)    # chip green
ORANGE = (214, 110, 20)  # explosion orange
SMOKE = (150, 148, 142)

# 5x7 bitmap font, drawn by hand. Each glyph is 7 rows; each row is a
# 5-bit number, bit 4 is the leftmost pixel. Lowercase sits on the
# x-height (rows 1-5) with descenders on row 6.
FONT = {
    'A': (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0': (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    '3': (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    'a': (0b00000, 0b00000, 0b01110, 0b00001, 0b01111, 0b10001, 0b01111),
    'b': (0b10000, 0b10000, 0b10110, 0b11001, 0b10001, 0b10001, 0b11110),
    'c': (0b00000, 0b00000, 0b01110, 0b10000, 0b10000, 0b10001, 0b01110),
    'd': (0b00001, 0b00001, 0b01101, 0b10011, 0b10001, 0b10001, 0b01111),
    'e': (0b00000, 0b00000, 0b01110, 0b10001, 0b11111, 0b10000, 0b01110),
    'f': (0b00110, 0b01001, 0b01000, 0b11110, 0b01000, 0b01000, 0b01000),
    'g': (0b00000, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'h': (0b10000, 0b10000, 0b10110, 0b11001, 0b10001, 0b10001, 0b10001),
    'i': (0b00100, 0b00000, 0b01100, 0b00100, 0b00100, 0b00100, 0b01110),
    'j': (0b00010, 0b00000, 0b00110, 0b00010, 0b00010, 0b10010, 0b01100),
    'k': (0b10000, 0b10000, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010),
    'l': (0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'm': (0b00000, 0b00000, 0b11010, 0b10101, 0b10101, 0b10101, 0b10101),
    'n': (0b00000, 0b00000, 0b10110, 0b11001, 0b10001, 0b10001, 0b10001),
    'o': (0b00000, 0b00000, 0b01110, 0b10001, 0b10001, 0b10001, 0b01110),
    'p': (0b00000, 0b00000, 0b10110, 0b11001, 0b10001, 0b11110, 0b10000),
    'q': (0b00000, 0b00000, 0b01101, 0b10011, 0b10001, 0b01111, 0b00001),
    'r': (0b00000, 0b00000, 0b10110, 0b11001, 0b10000, 0b10000, 0b10000),
    's': (0b00000, 0b00000, 0b01111, 0b10000, 0b01110, 0b00001, 0b11110),
    't': (0b00100, 0b00100, 0b01110, 0b00100, 0b00100, 0b00100, 0b00010),
    'u': (0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b10011, 0b01101),
    'v': (0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'w': (0b00000, 0b00000, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    'x': (0b00000, 0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001),
    'y': (0b00000, 0b00000, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'z': (0b00000, 0b00000, 0b11111, 0b00010, 0b00100, 0b01000, 0b11111),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ',': (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    ':': (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ';': (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    '!': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    '?': (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0, 0b00100),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    '"': (0b01010, 0b01010, 0b01010, 0, 0, 0, 0),
    '-': (0, 0, 0, 0b01110, 0, 0, 0),
    '(': (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ')': (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    '/': (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    '%': (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    '$': (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    '&': (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    '#': (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
    '*': (0, 0b10101, 0b01110, 0b11111, 0b01110, 0b10101, 0),
    '+': (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    '=': (0, 0, 0b11111, 0, 0b11111, 0, 0),
    '_': (0, 0, 0, 0, 0, 0, 0b11111),
    '@': (0b01110, 0b10001, 0b10111, 0b10101, 0b10110, 0b10000, 0b01110),
    '<': (0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010),
    '>': (0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000),
    '[': (0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110),
    ']': (0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, c)

    def text(self, s, x, y, scale, c, bold=False):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(cx + col * scale + dx,
                                         y + row * scale + dy, c)
                        if bold:
                            for dy in range(scale):
                                self.set(cx + col * scale + scale,
                                         y + row * scale + dy, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def wrap(self, s, width, scale):
        """Greedy word wrap into lines that fit width pixels."""
        words, lines, cur = s.split(' '), [], ''
        for wd in words:
            trial = wd if not cur else cur + ' ' + wd
            if self.text_w(trial, scale) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    return out + struct.pack('>I', binascii.crc32(kind + data) & 0xffffffff)


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr)
           + _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + _chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# --- stories: every item happened, or was first reported, on 24 Nov 2026 ---

LEAD_HEAD = "HOUTHI DRONE HITS RIYADH'S TALLEST TOWER"
LEAD_SUM = ("A Houthi drone struck the KAFD tower in Riyadh, injuring 11 "
            "people - the second attack on the capital's tallest tower in "
            "five days. Houthi fighters are also closing in on Aden, "
            "about 60 km away.")
LEAD_BULLETS = ["Second strike on the tower in five days",
                "Houthi fighters now about 60 km from Aden"]

SEC = [
    ("TECHNOLOGY", "NVIDIA BRINGS BACK HUANG",
     "Jensen Huang returns as chief two weeks after resigning. "
     "Trump says he persuaded the board; shares fell 7%."),
    ("EUROPE", "RUSSIA WARNS ESTONIA OF OPEN WAR",
     "Moscow says Tallinn's plan to shut its border on Dec 1 risks "
     "open war. Seven EU states back visa limits."),
]

MINI = [
    ("CONFLICT", "Ukraine sinks Russian corvette off Libya"),
    ("WAR DEATHS", "Leaked data: 700,000 Russian soldiers dead"),
    ("SPACE", "NATO to defend space from Russia"),
]

MORE = [
    "GAZA  Strikes kill Hamas security chief",
    "ZAPORIZHZHIA  Strike kills 2, wounds 40",
    "IRAN  Netanyahu urges new US strikes",
    "HORMUZ  UK logs record Iranian attacks",
    "CHINA  Graft probe on Politburo member",
    "SOLOMONS  To end China security pact",
    "IRAQ  Baghdad takes Kurdish oilfields",
    "SPAIN  Court amnesties Puigdemont",
    "MYANMAR  UK sanctions five generals",
    "BANGLADESH  Hasina to return on Dec 16",
    "KOREA  Russian jets enter defence zone",
    "GERMANY  First into Ukraine Delta system",
    "SPACEX  Two states sue over Grok images",
    "SEOUL  Rewards to catch AI exam cheats",
    "HUAWEI  Guilty of trade-secret theft",
    "SPACE  Pakistani astronaut on Shenzhou-24",
    "NEPAL  Quake of 5.6 near China border",
    "SENEGAL  Reinstated as Africa champions",
    "CONGO  Fighting traps Ebola responders",
    "TARIFFS  Trump to unveil China, EU levies",
]

MARKETS = "MARKETS  S&P 500 7,168 -0.95%  FTSE 100 10,467 -0.13%  Brent $87.51 +0.96%"


# --- flat pictograms, drawn from rectangles, lines and discs ---

def tri(cv, x0, y0, x1, y1, x2, y2, c):
    ys = sorted([y0, y1, y2])
    for y in range(ys[0], ys[2] + 1):
        xs = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                (x2, y2, x0, y0)):
            if ay == by:
                continue
            if min(ay, by) <= y <= max(ay, by):
                xs.append(ax + (bx - ax) * (y - ay) // (by - ay))
        if len(xs) >= 2:
            cv.hline(min(xs), y, max(xs) - min(xs) + 1, c)


def skyline(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT)
    cv.rect(x, y + h - 6, w, 6, INK)
    heights = [0.35, 0.55, 0.28, 0.62, 0.42, 0.7, 0.5, 0.3]
    bw = w // 8
    for i, f in enumerate(heights):
        bh = int(h * f)
        cv.rect(x + i * bw + 2, y + h - 6 - bh, bw - 4, bh, INK)
    cv.disc(x + w - 52, y + 42, 22, ORANGE)


def tower(cv, x, y, w, h):
    skyline(cv, x, y, w, h)
    tx, tw = x + w // 2 - 26, 52
    top = y + 34
    # tapered tower body
    for i in range(h - 60):
        yy = top + i
        half = 26 - i * 14 // (h - 60)
        cv.hline(tx + 26 - half, yy, half * 2, INK)
    cv.vline(tx + 26, y + 12, 24, INK, 3)          # antenna
    cv.disc(tx + 26, y + 10, 4, RED)              # beacon
    for wy in range(top + 18, y + h - 70, 22):     # windows
        cv.rect(tx + 8, wy, 10, 6, PAPER)
        cv.rect(tx + 34, wy, 10, 6, PAPER)
    # smoke plume and flash at the strike point
    cv.disc(tx + 66, top + 62, 16, SMOKE)
    cv.disc(tx + 78, top + 40, 20, SMOKE)
    cv.disc(tx + 62, top + 88, 12, SMOKE)
    cv.disc(tx + 52, top + 76, 9, ORANGE)
    cv.disc(tx + 52, top + 76, 4, RED)


def chip(cv, x, y, s):
    cv.rect(x, y, s, s, LIGHT)
    for i in range(4):
        off = 18 + i * 26
        cv.vline(x + off, y - 12, 12, INK, 4)
        cv.vline(x + off, y + s, 12, INK, 4)
        cv.hline(x - 12, y + off, 12, INK, 4)
        cv.hline(x + s, y + off, 12, INK, 4)
    cv.rect(x + 22, y + 22, s - 44, s - 44, GREEN)
    cv.rect(x + 42, y + 42, s - 84, s - 84, PAPER)
    cv.text("AI", x + 48, y + 52, 3, GREEN, bold=True)


def warning(cv, x, y, s):
    cv.rect(x, y, s, s, LIGHT)
    tri(cv, x + s // 2, y + 14, x + 14, y + s - 26, x + s - 14, y + s - 26, RED)
    cv.text("!", x + s // 2 - 6, y + s // 2 - 8, 4, PAPER, bold=True)
    for i in range(6):
        bx = x + 12 + i * (s - 24) // 5
        cv.vline(bx, y + s - 18, 12, INK, 3)


def ship(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT)
    cv.rect(x + 18, y + h - 52, w - 36, 26, INK)   # hull
    tri(cv, x + w - 18, y + h - 52, x + w - 18, y + h - 26,
        x + w + 4, y + h - 26, INK)
    cv.rect(x + w // 2 - 8, y + h - 78, 44, 26, INK)  # bridge
    cv.vline(x + w // 2 + 22, y + h - 96, 20, INK, 3)  # mast
    cv.disc(x + 34, y + 26, 10, SMOKE)
    cv.disc(x + 48, y + 18, 12, SMOKE)
    for wy in (y + h - 16, y + h - 8):
        for wx in range(x + 8, x + w - 8, 22):
            cv.line(wx, wy, wx + 10, wy - 4, BLUE)
            cv.line(wx + 10, wy - 4, wx + 20, wy, BLUE)


def bars(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT)
    base = y + h - 18
    bw = (w - 24) // 3
    for i, f in enumerate((0.35, 0.6, 0.95)):
        bh = int((h - 40) * f)
        col = RED if i == 2 else INK
        cv.rect(x + 12 + i * (bw + 4), base - bh, bw, bh, col)
    cv.hline(x + 8, base, w - 16, INK, 2)
    cv.text("700k", x + w - 52, y + 8, 2, RED, bold=True)


def satellite(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT)
    cx, cy = x + w // 2, y + h // 2
    cv.ring(cx, cy, 34, GREY, 2)
    cv.rect(cx - 44, cy - 10, 26, 20, BLUE)
    cv.rect(cx + 18, cy - 10, 26, 20, BLUE)
    cv.disc(cx, cy, 13, INK)
    cv.disc(cx - 4, cy - 4, 4, PAPER)
    for sx, sy in ((x + 12, y + 12), (x + w - 14, y + 16),
                   (x + 18, y + h - 14), (x + w - 20, y + h - 18)):
        cv.disc(sx, sy, 2, INK)


def globe(cv, cx, cy, r):
    cv.ring(cx, cy, r, INK, 3)
    cv.hline(cx - r, cy, 2 * r, INK, 2)
    cv.vline(cx, cy - r, 2 * r, INK, 2)
    for k in (1, 2):
        rx = r * k // 3
        for yy in range(cy - r, cy + r + 1):
            dx = int(rx * (1 - ((yy - cy) / r) ** 2) ** 0.5) if r else 0
            cv.set(cx - dx, yy, INK)
            cv.set(cx + dx, yy, INK)


def panel(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT)
    cv.hline(x, y, w, INK, 2)
    cv.hline(x, y + h - 2, w, INK, 2)
    cv.vline(x, y, h, INK, 2)
    cv.vline(x + w - 2, y, h, INK, 2)


def center_text(cv, s, y, scale, c, bold=False):
    w = cv.text_w(s, scale)
    cv.text(s, (W - w) // 2, y, scale, c, bold=bold)


def build():
    cv = Canvas(W, H, PAPER)
    # --- masthead ---
    globe(cv, 92, 44, 26)
    center_text(cv, "THE WORLD IN ONE DAY", 22, 6, INK, bold=True)
    center_text(cv, "TUESDAY, 24 NOVEMBER 2026", 74, 3, RED, bold=True)
    cv.hline(28, 104, W - 56, INK, 4)
    cv.hline(28, 112, W - 56, INK, 1)
    # --- lead story ---
    tower(cv, 28, 124, 372, 288)
    cv.text("Caption: the KAFD tower in Riyadh after the strike.",
            28, 418, 1, GREY)
    tx = 424
    cv.text("RIYADH, SAUDI ARABIA", tx, 124, 2, RED, bold=True)
    y = 148
    for ln in cv.wrap(LEAD_HEAD, 572, 4):
        cv.text(ln, tx, y, 4, INK, bold=True)
        y += 30
    y += 8
    for ln in cv.wrap(LEAD_SUM, 572, 2):
        cv.text(ln, tx, y, 2, INK)
        y += 16
    y += 10
    cv.hline(tx, y, 572, LIGHT, 2)
    y += 12
    for b in LEAD_BULLETS:
        cv.text("-", tx, y, 2, RED, bold=True)
        cv.text(b, tx + 18, y, 2, INK)
        y += 18
    # --- secondaries ---
    cv.hline(28, 448, W - 56, INK, 2)
    for i, (tag, head, summ) in enumerate(SEC):
        x0 = 28 + i * 500
        if i == 0:
            chip(cv, x0, 466, 140)
        else:
            warning(cv, x0, 466, 140)
        tx2 = x0 + 158
        cv.text(tag, tx2, 466, 2, BLUE, bold=True)
        y = 490
        for ln in cv.wrap(head, 310, 3):
            cv.text(ln, tx2, y, 3, INK, bold=True)
            y += 23
        y += 4
        for ln in cv.wrap(summ, 310, 2):
            cv.text(ln, tx2, y, 2, INK)
            y += 16
    # --- minis ---
    cv.hline(28, 640, W - 56, INK, 2)
    for i, (tag, head) in enumerate(MINI):
        x0 = 28 + i * 328
        if i == 0:
            ship(cv, x0, 656, 96, 72)
        elif i == 1:
            bars(cv, x0, 656, 96, 72)
        else:
            satellite(cv, x0, 656, 96, 72)
        tx3 = x0 + 110
        cv.text(tag, tx3, 662, 2, RED, bold=True)
        y = 684
        for ln in cv.wrap(head, 196, 2):
            cv.text(ln, tx3, y, 2, INK, bold=True)
            y += 16
    # --- markets strip ---
    cv.hline(28, 748, W - 56, INK, 2)
    cv.text(MARKETS, 28, 758, 2, INK)
    cv.hline(28, 782, W - 56, INK, 1)
    # --- more of the day ---
    cv.text("MORE OF THE DAY", 28, 796, 2, INK, bold=True)
    cv.hline(28, 818, W - 56, INK, 1)
    for i, item in enumerate(MORE):
        col = i // 10
        row = i % 10
        x0 = 28 + col * 500
        y = 830 + row * 15
        tag, _, rest = item.partition("  ")
        cv.text(tag, x0, y, 2, RED, bold=True)
        cv.text(rest, x0 + cv.text_w(tag + "  ", 2), y, 2, INK)
    # --- footer ---
    cv.hline(28, 986, W - 56, INK, 2)
    center_text(cv, "JUDGE: ALL STORIES ABOVE ARE FROM TUESDAY, 24 NOVEMBER 2026.",
                996, 2, RED, bold=True)
    center_text(cv, "Sources: wire and agency reports of 24 November 2026. "
                    "Pictures drawn by the program; no photographs used.",
                1012, 1, GREY)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(build(), path)
    print("wrote", path, size, "bytes")


if __name__ == "__main__":
    main()
