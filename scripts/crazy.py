"""The loud parts: the neon heatmap city, the boot terminal, the square wall and the CTF banner."""

import json
import math
import random
from html import escape
from pathlib import Path

from build import FONT, MONO, THEMES, ago, cell, streaks, svg

ROOT = Path(__file__).resolve().parent.parent
DARK = THEMES["dark"]
G = DARK["lv"]
NEON = "#39d353"
CITY = ["#1b222c", "#1a7f37", "#2ea043", "#3fb950", "#56d364"]


def shade(hex_color, k):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def pixel_word(word, x0, y0, px, gap, fill, cls=""):
    out, col = [], 0
    for ch in word:
        for r, bits in enumerate(FONT[ch]):
            for c, b in enumerate(bits):
                if b == "1":
                    out.append(f'<rect x="{x0 + (col + c) * (px + gap)}" y="{y0 + r * (px + gap)}" '
                               f'width="{px}" height="{px}" rx="2" fill="{fill}"/>')
        col += 6
    return f'<g class="{cls}">{"".join(out)}</g>'


# ---------------------------------------------------------------- the city


def city(data):
    W, H = 1200, 600
    weeks = data["weeks"]
    cols = len(weeks)
    rnd = random.Random(7)
    hi = max((d[1] for w in weeks for d in w), default=1) or 1
    best, cur, active, top = streaks(weeks)

    defs = (
        '<defs>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#010409"/><stop offset=".62" stop-color="#0b1a12"/>'
        '<stop offset="1" stop-color="#0d1117"/></linearGradient>'
        '<radialGradient id="glow" cx=".5" cy=".86" r=".6">'
        f'<stop offset="0" stop-color="{NEON}" stop-opacity=".28"/><stop offset="1" stop-color="{NEON}" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{NEON}" stop-opacity="0"/><stop offset=".5" stop-color="{NEON}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{NEON}" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="up" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{NEON}" stop-opacity=".9"/><stop offset="1" stop-color="{NEON}" stop-opacity="0"/>'
        '</linearGradient>'
        '<filter id="neon" x="-20%" y="-40%" width="140%" height="180%">'
        '<feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '</defs>')
    out = [defs, f'<rect width="{W}" height="{H}" rx="14" fill="url(#sky)"/>',
           f'<rect width="{W}" height="{H}" rx="14" fill="url(#glow)"/>']

    for _ in range(90):  # stars
        x, y = rnd.uniform(10, W - 10), rnd.uniform(10, 260)
        out.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice((0.6, 0.9, 1.2))}" fill="#c9d1d9" '
                   f'style="animation-delay:{rnd.uniform(0, 4):.1f}s"/>')

    # Neon sign
    out.append(f'<g filter="url(#neon)">{pixel_word("KAUSHIK", 64, 54, 11, 3, NEON, "sign")}</g>')
    out.append(f'<text class="m" x="64" y="178" font-size="15" fill="{G[3]}" letter-spacing="1">'
               '&gt; full-stack + security engineer // blank repo to live demo</text>')

    # HUD
    hud = [("COMMITS", f"{data['total']:,}"), ("BEST STREAK", f"{best}d"),
           ("ACTIVE DAYS", f"{active}"), ("REPOS", f"{data['repos']}")]
    for i, (k, v) in enumerate(hud):
        x, y = 860 + (i % 2) * 150, 50 + (i // 2) * 66
        out.append(f'<rect x="{x}" y="{y}" width="138" height="54" rx="6" fill="#0d1117" fill-opacity=".7" '
                   f'stroke="{G[2]}"/><text class="m" x="{x + 12}" y="{y + 19}" font-size="10" '
                   f'letter-spacing="1.5" fill="{G[3]}">{k}</text><text class="m" x="{x + 12}" y="{y + 43}" '
                   f'font-size="20" font-weight="700" fill="#e6edf3">{v}</text>')

    # Towers: oblique projection, back rows first.
    dx, bw, sx, sy, dz = 19.2, 13, 7, 8, 6
    ox, base = 74, 540
    today = None
    for r in range(6, -1, -1):
        for c in range(cols):
            day = next((d for d in weeks[c] if (d[0].weekday() + 1) % 7 == r), None)
            if not day:
                continue
            d, n, lv = day
            x0, y0 = ox + c * dx + r * sx, base - r * sy
            h = 3 if n == 0 else 12 + 150 * math.sqrt(n / hi)
            topc = CITY[lv] if n else "#1b222c"
            parts = [
                f'<rect x="{x0:.1f}" y="{y0 - h:.1f}" width="{bw}" height="{h:.1f}" fill="{shade(topc, .72)}"/>',
                f'<path d="M{x0 + bw:.1f} {y0:.1f}V{y0 - h:.1f}l{dz} {-dz}V{y0 - dz:.1f}z" fill="{shade(topc, .48)}"/>',
                f'<path d="M{x0:.1f} {y0 - h:.1f}h{bw}l{dz} {-dz}h{-bw}z" fill="{topc}"/>',
            ]
            if lv >= 3 and h > 40:  # lit windows
                for wy in range(int(y0 - h + 7), int(y0 - 6), 9):
                    for wx in (x0 + 3, x0 + 8):
                        if rnd.random() < 0.55:
                            cls = ' class="win"' if rnd.random() < 0.12 else ""
                            parts.append(f'<rect{cls} x="{wx:.1f}" y="{wy}" width="2.4" height="3.2" fill="#d2ffd9" '
                                         f'opacity=".75" style="animation-delay:{rnd.uniform(0, 5):.1f}s"/>')
            delay = c * 0.025 + (6 - r) * 0.04
            out.append(f'<g class="t" style="animation-delay:{delay:.2f}s">{"".join(parts)}</g>')
            if d == max(dd[0] for w in weeks for dd in w):
                today = (x0 + bw / 2 + dz / 2, y0 - h - dz / 2)

    # Ground line and month labels
    out.append(f'<path d="M40 {base + 4}H{W - 40}" stroke="{G[2]}" stroke-opacity=".6"/>')
    last = None
    for c, wk in enumerate(weeks):
        dd = wk[0][0]
        if dd.month != last and dd.day <= 7:
            out.append(f'<text class="m" x="{ox + c * dx}" y="{base + 22}" font-size="11" fill="{G[3]}">'
                       f'{dd.strftime("%b").upper()}</text>')
        last = dd.month

    if today:
        tx, ty = today
        out.append(f'<rect x="{tx - 1.5:.1f}" y="{ty - 150:.1f}" width="3" height="150" fill="url(#up)" class="beacon"/>'
                   f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="4" fill="{NEON}"><animate attributeName="r" values="3;10;3" '
                   f'dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;.2;1" dur="1.6s" '
                   f'repeatCount="indefinite"/></circle>'
                   f'<text class="m" x="{tx - 10:.1f}" y="{ty - 158:.1f}" font-size="11" fill="{NEON}" text-anchor="end">'
                   'TODAY ▸</text>')

    out.append(f'<rect class="sweep" x="-160" y="190" width="160" height="{base - 180}" fill="url(#beam)"/>')
    out.append(f'<text class="m" x="64" y="{H - 18}" font-size="11" fill="#8b949e">'
               f'one tower = one day of my last year · height = commits · peak {top[1]} on '
               f'{top[0].strftime("%d %b %Y")}</text>')

    desc_file = ROOT / "ctf" / "desc.hex"
    desc = desc_file.read_text().strip() if desc_file.exists() else ""

    css = (
        "@keyframes rise{from{transform:scaleY(.02)}to{transform:scaleY(1)}}"
        ".t{transform-box:fill-box;transform-origin:50% 100%;animation:rise 1.3s cubic-bezier(.2,.9,.25,1) both}"
        "@keyframes tw{0%,100%{opacity:.9}50%{opacity:.15}}.tw{animation:tw 3.5s ease-in-out infinite}"
        "@keyframes flick{0%,17%,21%,24%,52%,56%,100%{opacity:1}19%,23%,54%{opacity:.25}}"
        ".sign{animation:flick 6s linear infinite}"
        "@keyframes win{0%,100%{opacity:.8}50%{opacity:.05}}.win{animation:win 2.8s steps(2) infinite}"
        f"@keyframes sweep{{from{{transform:translateX(0)}}to{{transform:translateX({W + 160}px)}}}}"
        ".sweep{animation:sweep 7s linear infinite}"
        "@keyframes beacon{0%,100%{opacity:.9}50%{opacity:.3}}.beacon{animation:beacon 1.6s ease-in-out infinite}")
    body = f"<desc>{desc}</desc>" + "".join(out)
    return svg(W, H, body, f"A neon city built from my contribution calendar: one tower per day, "
               f"{data['total']:,} contributions in the last year, with KAUSHIK on a flickering sign.", css)


# ---------------------------------------------------------------- boot terminal


def terminal(data):
    W, pad, lh = 1000, 26, 26
    latest = data["latest"]
    names = "  ".join(p["name"] for p in data["projects"][:6])
    lines = [
        ("cmd", "whoami"),
        ("out", "kaushik · full-stack + security engineer · bangalore, IN"),
        ("cmd", "git log --author=kaushik --since=1.year --oneline | wc -l"),
        ("out", f"{data['total']}"),
        ("cmd", "ls ~/shipped"),
        ("out", names + "  ..."),
        ("cmd", "git log -1 --format='%s'  # what I'm building right now"),
        ("out", f"{latest['name']} · {ago((latest.get('pushed_at') or '')[:10])}"),
        ("cmd", "cat ./status"),
        ("hot", "OPEN TO → internships · freelance · project-based roles"),
    ]
    H = 58 + len(lines) * lh + 34
    out = [f'<rect width="{W}" height="{H}" rx="12" fill="#010409" stroke="#30363d"/>',
           f'<path d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v22H0z" fill="#161b22"/>']
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{22 + i * 20}" cy="17" r="6" fill="{col}"/>')
    out.append(f'<text class="m" x="{W / 2}" y="22" font-size="12" fill="#8b949e" text-anchor="middle">'
               'kaushik@github: ~ — zsh</text>')
    t, cw = 0.6, 9.03
    for i, (kind, text) in enumerate(lines):
        y = 62 + i * lh
        if kind == "cmd":
            out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                       f'<text class="m" x="{pad}" y="{y}" font-size="15" fill="{NEON}">❯</text></g>')
            width = len(text) * cw + 4
            dur = max(0.4, len(text) * 0.035)
            out.append(f'<clipPath id="c{i}"><rect x="{pad + 20}" y="{y - 16}" height="22" width="0">'
                       f'<animate attributeName="width" from="0" to="{width:.0f}" begin="{t:.2f}s" dur="{dur:.2f}s" '
                       f'fill="freeze"/></rect></clipPath>'
                       f'<text class="m" x="{pad + 20}" y="{y}" font-size="15" fill="#e6edf3" clip-path="url(#c{i})">'
                       f'{escape(text)}</text>')
            t += dur + 0.25
        else:
            fill = {"out": "#8b949e", "hot": NEON}[kind]
            weight = ' font-weight="700"' if kind == "hot" else ""
            out.append(f'<text class="m" x="{pad + 20}" y="{y}" font-size="15" fill="{fill}"{weight} opacity="0">'
                       f'{escape(text)}<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>')
            t += 0.45
    y = 62 + len(lines) * lh
    out.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
               f'<text class="m" x="{pad}" y="{y}" font-size="15" fill="{NEON}">❯</text>'
               f'<rect class="cur" x="{pad + 20}" y="{y - 14}" width="9" height="18" fill="{NEON}"/></g>')
    css = "@keyframes cur{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:cur 1s steps(1) infinite}"
    return svg(W, H, "".join(out), "Terminal: kaushik, full-stack and security engineer in Bangalore. "
               f"{data['total']} contributions this year. Open to internships, freelance and project-based roles.", css)


# ---------------------------------------------------------------- square wall


def load_wall():
    f = ROOT / "squares" / "visitors.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def wall(t, visitors):
    W, pad, cols, rows, pitch, size = 1000, 28, 30, 6, 19, 15
    out = [f'<rect width="{W}" height="10" fill="none"/>']
    gx, gy = pad, 74
    out.append(f'<text x="{pad}" y="36" font-size="20" font-weight="700" fill="{t["text"]}">The square wall</text>'
               f'<text x="{pad}" y="58" font-size="13" fill="{t["muted"]}">Every lit square is a visitor. '
               f'{len(visitors)} lit so far. Open an issue and the next one is yours.</text>')
    n = len(visitors)
    for i in range(cols * rows):
        x, y = gx + (i % cols) * pitch, gy + (i // cols) * pitch
        if i < n:
            v = visitors[i]
            lv = max(1, min(4, int(v.get("level", 3))))
            cls = ' class="new"' if i >= n - 3 else ""
            out.append(cell(x, y, size, t["lv"][lv], cls))
        elif i == n:
            out.append(f'<rect class="slot" x="{x + 1}" y="{y + 1}" width="{size - 2}" height="{size - 2}" rx="2" '
                       f'fill="none" stroke="{t["lv"][4]}" stroke-width="1.6"/>')
        else:
            out.append(cell(x, y, size, t["lv"][0]))
    lx = gx + cols * pitch + 24
    out.append(f'<text class="m" x="{lx}" y="{gy + 10}" font-size="11" letter-spacing="1.5" fill="{t["lv"][3]}">LATEST</text>')
    for j, v in enumerate(reversed(visitors[-5:])):
        y = gy + 34 + j * 20
        out.append(cell(lx, y - 11, 11, t["lv"][max(1, min(4, int(v.get("level", 3))))]))
        out.append(f'<text x="{lx + 18}" y="{y - 1}" font-size="13" fill="{t["text"]}">'
                   f'<tspan font-weight="600">@{escape(v["login"])}</tspan>'
                   f'<tspan fill="{t["muted"]}">  {escape(v["msg"][:28])}</tspan></text>')
    H = gy + rows * pitch + 18
    out[0] = f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}"/>'
    css = ("@keyframes new{0%,100%{opacity:1}50%{opacity:.4}}.new{animation:new 1.6s ease-in-out infinite}"
           "@keyframes slot{0%,100%{opacity:1}50%{opacity:.2}}.slot{animation:slot 1s steps(2) infinite}")
    return svg(W, H, "".join(out), f"The square wall: {n} lit square{'' if n == 1 else 's'} so far. "
               "Latest: " + ", ".join("@" + v["login"] for v in visitors[-5:]), css)


# ---------------------------------------------------------------- CTF banner


def ctf_banner(stage1, solved):
    W, cols, rows, pitch, size = 1000, 62, 8, 16, 12
    bits = "".join(f"{ord(ch):08b}" for ch in stage1)
    rnd = random.Random(31)
    ox = (W - cols * pitch) / 2 + 2
    out = [f'<rect width="{W}" height="230" rx="12" fill="#010409" stroke="#30363d"/>']
    for i in range(cols * rows):
        b = bits[i % len(bits)]
        x, y = ox + (i % cols) * pitch, 22 + (i // cols) * pitch
        lv = rnd.choice((3, 4)) if b == "1" else rnd.choice((0, 0, 1))
        cls = ' class="fl"' if rnd.random() < 0.08 else ""
        out.append(cell(x, y, size, G[lv], cls + f' style="animation-delay:{rnd.uniform(0, 3):.1f}s"'))
    out.append(f'<rect x="{W / 2 - 250}" y="58" width="500" height="64" rx="8" fill="#010409" fill-opacity=".88" stroke="{NEON}"/>'
               f'<text class="m g" x="{W / 2}" y="98" font-size="22" font-weight="700" fill="{NEON}" text-anchor="middle" '
               'letter-spacing="4">INTERCEPTED TRANSMISSION</text>')
    out.append(f'<text class="m" x="{W / 2}" y="180" font-size="13" fill="#8b949e" text-anchor="middle">'
               'bright square = 1, dark square = 0 · three stages · one flag · a Hall of Fame</text>'
               f'<text class="m" x="{W / 2}" y="204" font-size="13" fill="{G[3]}" text-anchor="middle">'
               f'{solved} operator{"s" if solved != 1 else ""} cracked it so far. you could be next.</text>')
    css = ("@keyframes fl{0%,100%{opacity:1}50%{opacity:.1}}.fl{animation:fl .9s steps(2) infinite}"
           "@keyframes g{0%,92%,100%{transform:none}94%{transform:translateX(-3px)}96%{transform:translateX(3px)}}"
           ".g{animation:g 3s linear infinite}")
    return svg(W, 230, "".join(out), "Intercepted transmission: a three-stage CTF hidden in this profile.", css)
