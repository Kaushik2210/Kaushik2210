"""Neofetch-style card (avatar drawn in contribution squares) and pixel-font section banners."""

import datetime as dt
import io
import random
import urllib.request
from html import escape

import palette as P
from build import MONO, ago, streaks, svg

G = P.LV
NEON = P.CYAN

# 5x7 pixel font
F = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01111 10000 10000 10000 10000 10000 01111", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01111 10000 10000 10011 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    " ": "000 000 000 000 000 000 000", "!": "1 1 1 1 1 0 1", "/": "00001 00010 00010 00100 01000 01000 10000",
}


def pixels(text, x0, y0, px, gap, colors, rnd):
    out, x = [], x0
    for ch in text.upper():
        rows = F[ch].split()
        for r, bits in enumerate(rows):
            for c, b in enumerate(bits):
                if b == "1":
                    out.append(f'<rect x="{x + c * (px + gap)}" y="{y0 + r * (px + gap)}" width="{px}" height="{px}" '
                               f'rx="1.5" fill="{rnd.choice(colors)}"/>')
        x += (len(rows[0]) + 1) * (px + gap)
    return "".join(out), x


def banner(text, sub=""):
    W, H = 1000, 100
    rnd = random.Random(text)
    body, end = pixels(text, 4, 14, 7, 2, ["url(#bt)"], rnd)
    out = [f'<defs><linearGradient id="bt" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{end}" y2="0">'
           f'<stop offset="0" stop-color="{P.PINK}"/><stop offset=".55" stop-color="#ff6ad5"/>'
           f'<stop offset="1" stop-color="{P.CYAN}"/></linearGradient></defs>', f'<g class="p">{body}</g>']
    # trailing contribution strip, a wave runs through it
    x, i = end + 14, 0
    while x < W - 10:
        for r in range(7):
            lv = rnd.choice((0, 0, 1, 1, 2, 3)) if rnd.random() > 0.3 else 0
            out.append(f'<rect class="w" x="{x}" y="{14 + r * 9}" width="7" height="7" rx="1.5" fill="{G[lv]}" '
                       f'style="animation-delay:{i * 0.05:.2f}s"/>')
        x += 9
        i += 1
    if sub:
        out.append(f'<rect x="{W - len(sub) * 7.3 - 26}" y="{H - 24}" width="{len(sub) * 7.3 + 22}" height="20" rx="4" '
                   f'fill="{P.BG}"/><text class="m" x="{W - 15}" y="{H - 8}" font-size="12" fill="{P.MUTED}" '
                   f'text-anchor="end">{escape(sub)}</text>')
    css = ("@keyframes w{0%,100%{opacity:1}50%{opacity:.25}}.w{animation:w 2.6s ease-in-out infinite}"
           "@keyframes p{0%,94%,100%{opacity:1}96%{opacity:.4}}.p{animation:p 5s linear infinite}")
    return svg(W, H, "".join(out), f"{text.title()}. {sub}", css)


# ---------------------------------------------------------------- neofetch


def avatar_levels(url, n=26):
    try:
        from PIL import Image, ImageOps
        raw = urllib.request.urlopen(url + ("&" if "?" in url else "?") + "s=160", timeout=20).read()
        img = ImageOps.autocontrast(Image.open(io.BytesIO(raw)).convert("L").resize((n, n), Image.LANCZOS), cutoff=2)
        px = list(img.getdata())
        return [[4 - min(4, px[r * n + c] * 5 // 256) for c in range(n)] for r in range(n)]
    except Exception:  # no Pillow or no network: fall back to a monogram
        grid = [[0] * n for _ in range(n)]
        for r, bits in enumerate(F["K"].split()):
            for c, b in enumerate(bits):
                if b == "1":
                    for dr in range(3):
                        for dc in range(3):
                            grid[3 + r * 3 + dr][5 + c * 3 + dc] = 4
        return grid


def neofetch(data):
    W, H = 1000, 470
    lv = avatar_levels(data["avatar"])
    n = len(lv)
    pitch, size, ox, oy = 14, 12, 34, 62
    out = [f'<rect width="{W}" height="{H}" rx="12" fill="{P.BG}" stroke="{P.BORDER}"/>',
           f'<path d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v22H0z" fill="#1a0b3d"/>']
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{22 + i * 20}" cy="17" r="6" fill="{col}"/>')
    out.append(f'<text class="m" x="{W / 2}" y="22" font-size="12" fill="{P.MUTED}" text-anchor="middle">'
               'kaushik@github: ~ — neofetch</text>')
    for r in range(n):
        for c in range(n):
            d = (r + c) * 0.018
            out.append(f'<rect class="a" x="{ox + c * pitch}" y="{oy + r * pitch}" width="{size}" height="{size}" '
                       f'rx="2" fill="{G[lv[r][c]]}" style="animation-delay:{d:.2f}s"/>')

    created = dt.date.fromisoformat(data["created"][:10])
    days = (dt.date.today() - created).days
    best, cur, active, _ = streaks(data["weeks"])
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:4]
    rows = [
        ("title", "kaushik@github"),
        ("rule", ""),
        ("OS", "Full-stack + security engineer"),
        ("Host", "Bangalore, India · open to remote"),
        ("Uptime", f"{days // 365} years, {days % 365 // 30} months on GitHub"),
        ("Kernel", "security tooling · AI-agent infra · products"),
        ("Packages", f"{data['repos']} repos · {data['live']} live demos · {data['stars']} stars"),
        ("Shell", ", ".join(l for l, _ in langs)),
        ("Commits", f"{data['total']:,} in the last year · best streak {best}d"),
        ("Activity", f"{active} active days · current streak {cur}d"),
        ("Building", f"{data['latest']['name']} ({ago((data['latest'].get('pushed_at') or '')[:10])})"),
        ("rule", ""),
        ("Contact", "linkedin/sodagum-venkata-kaushik · x/@svKaushik2210"),
        ("Status", "● OPEN TO internships · freelance · project work"),
    ]
    tx, ty = ox + n * pitch + 34, 74
    for i, (k, v) in enumerate(rows):
        y = ty + i * 24
        d = f' style="animation-delay:{0.4 + i * 0.12:.2f}s"'
        if k == "title":
            out.append(f'<text class="m l" x="{tx}" y="{y}" font-size="17" font-weight="700"{d}>'
                       f'<tspan fill="{P.PINK}">kaushik</tspan><tspan fill="{P.TEXT}">@</tspan>'
                       f'<tspan fill="{NEON}">github</tspan></text>')
        elif k == "rule":
            out.append(f'<text class="m l" x="{tx}" y="{y - 6}" font-size="15" fill="{P.BORDER}"{d}>{"─" * 46}</text>')
        else:
            dots = "." * max(2, 11 - len(k))
            vfill = NEON if k == "Status" else P.TEXT
            out.append(f'<text class="m l" x="{tx}" y="{y}" font-size="14"{d}><tspan fill="{P.PINK}" '
                       f'font-weight="700">{k}</tspan><tspan fill="{P.FAINT}"> {dots} </tspan>'
                       f'<tspan fill="{vfill}">{escape(v)}</tspan></text>')
    py = ty + len(rows) * 24 + 2
    for i in range(5):
        out.append(f'<rect x="{tx + i * 30}" y="{py}" width="26" height="16" rx="3" fill="{G[i]}"/>')
    out.append(f'<rect class="cur" x="{tx + 162}" y="{py}" width="9" height="16" fill="{NEON}"/>')
    css = ("@keyframes a{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}"
           ".a{transform-box:fill-box;transform-origin:center;animation:a .5s ease-out both}"
           "@keyframes l{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
           ".l{animation:l .35s ease-out both}"
           "@keyframes cur{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:cur 1s steps(1) infinite}")
    return svg(W, H, "".join(out), f"neofetch: kaushik@github. My avatar drawn in contribution squares, next to "
               f"{data['repos']} repos, {data['total']:,} commits this year, and open to project work.", css)
