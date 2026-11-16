"""The city header and the square wall."""

import json
import math
import random
from html import escape
from pathlib import Path

import palette as P
from build import FONT, cell, streaks, svg

ROOT = Path(__file__).resolve().parent.parent
TOWER = ["#16244d", "#2358d8", "#59a2ff", "#ffc233", "#fff4cf"]


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
    W, H = 1200, 560
    weeks = data["weeks"]
    cols = len(weeks)
    rnd = random.Random(7)
    hi = max((d[1] for w in weeks for d in w), default=1) or 1
    best, cur, active, top = streaks(weeks)
    base = 480          # front row baseline = horizon of the grid floor
    sun_cx, sun_cy, sun_r = 640, 400, 170

    defs = (
        '<defs>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#030714"/><stop offset=".5" stop-color="#0a1740"/>'
        '<stop offset=".72" stop-color="#16307a"/><stop offset=".73" stop-color="#040918"/>'
        '<stop offset="1" stop-color="#040918"/></linearGradient>'
        '<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{P.GOLD}"/><stop offset=".55" stop-color="{P.SKY}"/>'
        f'<stop offset="1" stop-color="{P.BLUE}"/></linearGradient>'
        '<linearGradient id="sign" gradientUnits="userSpaceOnUse" x1="64" y1="0" x2="640" y2="0">'
        f'<stop offset="0" stop-color="{P.BLUE}"/><stop offset=".5" stop-color="#f2f7ff"/>'
        f'<stop offset="1" stop-color="{P.GOLD}"/></linearGradient>'
        '<radialGradient id="haze" cx=".53" cy=".72" r=".55">'
        f'<stop offset="0" stop-color="{P.BLUE}" stop-opacity=".22"/><stop offset="1" stop-color="{P.BLUE}" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{P.GOLD}" stop-opacity="0"/><stop offset=".5" stop-color="{P.GOLD}" stop-opacity=".2"/>'
        f'<stop offset="1" stop-color="{P.GOLD}" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="up" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{P.GOLD}" stop-opacity=".95"/><stop offset="1" stop-color="{P.GOLD}" stop-opacity="0"/>'
        '</linearGradient>'
        '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".15"/><stop offset="1" stop-color="#fff"/></linearGradient>'
        '<linearGradient id="ground" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#1b2c5e"/><stop offset=".35" stop-color="#0a1431"/>'
        '<stop offset="1" stop-color="#050b1e"/></linearGradient>'
        f'<mask id="floorfade"><rect x="0" y="{base}" width="{W}" height="{H - base}" fill="url(#fade)"/></mask>'
        f'<clipPath id="floor"><rect x="0" y="{base + 2}" width="{W}" height="{H - base}"/></clipPath>'
        f'<clipPath id="above"><rect width="{W}" height="{base}"/></clipPath>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
        '<filter id="glow" x="-20%" y="-40%" width="140%" height="180%">'
        '<feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="soft"><feGaussianBlur stdDeviation="2.2"/></filter>'
        '</defs>')
    out = [defs, '<g clip-path="url(#card)">', f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']

    for _ in range(110):  # stars, only in the upper sky
        x, y = rnd.uniform(10, W - 10), rnd.uniform(10, 300)
        out.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice((0.6, 0.9, 1.3))}" fill="#fff" '
                   f'style="animation-delay:{rnd.uniform(0, 4):.1f}s"/>')

    # Soft gold moon
    out.append(f'<circle cx="760" cy="96" r="110" fill="{P.GOLD}" opacity=".07" filter="url(#soft)"/>'
               f'<circle cx="760" cy="96" r="30" fill="#fff4cf" opacity=".95"/>'
               f'<circle cx="771" cy="89" r="26" fill="#0a1740" opacity=".55"/>')

    # Wireframe mountains on the horizon
    for layer, (amp, col, op) in enumerate(((95, "#1f3a85", .6), (60, "#2a4aa0", .8))):
        pts, x = [], -20
        r2 = random.Random(layer + 3)
        while x <= W + 20:
            pts.append(f"{x},{base - 4 - r2.uniform(0.2, 1) * amp * (0.55 + 0.45 * math.sin(x / 140 + layer)):.1f}")
            x += r2.randint(40, 90)
        out.append(f'<polygon points="-20,{base} {" ".join(pts)} {W + 20},{base}" fill="#081230" '
                   f'stroke="{col}" stroke-width="1.5" stroke-opacity="{op}"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#haze)"/>')

    # Neon sign
    out.append(f'<g filter="url(#glow)">{pixel_word("KAUSHIK", 64, 52, 11, 3, "url(#sign)")}</g>')
    out.append(f'<text class="m" x="64" y="176" font-size="15" fill="{P.SKY}" letter-spacing="1">'
               'Full-stack + security engineer · I take projects from blank repo to live demo</text>')

    # HUD
    hud = [("COMMITS", f"{data['total']:,}"), ("BEST STREAK", f"{best}d"),
           ("ACTIVE DAYS", f"{active}"), ("REPOS", f"{data['repos']}")]
    for i, (k, v) in enumerate(hud):
        x, y = 860 + (i % 2) * 150, 48 + (i // 2) * 66
        out.append(f'<rect x="{x}" y="{y}" width="138" height="54" rx="6" fill="{P.BG}" fill-opacity=".75" '
                   f'stroke="{P.BLUE}" stroke-opacity=".7"/><text class="m" x="{x + 12}" y="{y + 19}" font-size="10" '
                   f'letter-spacing="1.5" fill="{P.GOLD}">{k}</text><text class="m" x="{x + 12}" y="{y + 43}" '
                   f'font-size="20" font-weight="700" fill="{P.TEXT}">{v}</text>')

    # Ground: quiet gradient with a faint reflection line
    out.append(f'<rect x="0" y="{base}" width="{W}" height="{H - base}" fill="url(#ground)"/>')
    out.append(f'<path d="M0 {base + 1}H{W}" stroke="{P.BLUE}" stroke-opacity=".6" stroke-width="1.5"/>')

    # Towers: oblique projection, back rows first
    dx, bw, sx, sy, dz = 19.2, 13, 7, 8, 6
    ox = 74
    last_day = max(dd[0] for w in weeks for dd in w)
    today = None
    for r in range(6, -1, -1):
        for c in range(cols):
            day = next((d for d in weeks[c] if (d[0].weekday() + 1) % 7 == r), None)
            if not day:
                continue
            d, n, lv = day
            x0, y0 = ox + c * dx + r * sx, base - r * sy
            h = 3 if n == 0 else 12 + 160 * math.sqrt(n / hi)
            topc = TOWER[lv] if n else "#1a1236"
            parts = [
                f'<rect x="{x0:.1f}" y="{y0 - h:.1f}" width="{bw}" height="{h:.1f}" fill="{shade(topc, .55)}"/>',
                f'<path d="M{x0 + bw:.1f} {y0:.1f}V{y0 - h:.1f}l{dz} {-dz}V{y0 - dz:.1f}z" fill="{shade(topc, .32)}"/>',
                f'<path d="M{x0:.1f} {y0 - h:.1f}h{bw}l{dz} {-dz}h{-bw}z" fill="{topc}"/>',
            ]
            if n and h > 30:  # neon edge on the front-left
                parts.append(f'<path d="M{x0:.1f} {y0:.1f}V{y0 - h:.1f}" stroke="{topc}" stroke-width="1" opacity=".9"/>')
            if lv >= 3 and h > 40:  # lit windows
                for wy in range(int(y0 - h + 7), int(y0 - 6), 9):
                    for wx in (x0 + 3, x0 + 8):
                        if rnd.random() < 0.55:
                            cls = ' class="win"' if rnd.random() < 0.12 else ""
                            wc = "#ffe3f1" if lv == 3 else "#d9fbff"
                            parts.append(f'<rect{cls} x="{wx:.1f}" y="{wy}" width="2.4" height="3.2" fill="{wc}" '
                                         f'opacity=".8" style="animation-delay:{rnd.uniform(0, 5):.1f}s"/>')
            delay = c * 0.025 + (6 - r) * 0.04
            out.append(f'<g class="t" style="animation-delay:{delay:.2f}s">{"".join(parts)}</g>')
            if d == last_day:
                today = (x0 + bw / 2 + dz / 2, y0 - h - dz / 2)

    last = None
    for c, wk in enumerate(weeks):
        dd = wk[0][0]
        if dd.month != last and dd.day <= 7:
            out.append(f'<text class="m" x="{ox + c * dx}" y="{base + 20}" font-size="11" fill="{P.TEXT}" '
                       f'opacity=".85">{dd.strftime("%b").upper()}</text>')
        last = dd.month

    if today:
        tx, ty = today
        out.append(f'<rect x="{tx - 1.5:.1f}" y="{ty - 150:.1f}" width="3" height="150" fill="url(#up)" class="beacon"/>'
                   f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="4" fill="{P.GOLD}"><animate attributeName="r" values="3;10;3" '
                   f'dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;.2;1" dur="1.6s" '
                   f'repeatCount="indefinite"/></circle>'
                   f'<text class="m" x="{tx - 10:.1f}" y="{ty - 158:.1f}" font-size="11" fill="{P.GOLD}" text-anchor="end">'
                   'TODAY ▸</text>')

    out.append(f'<rect x="0" y="{H - 34}" width="{W}" height="34" fill="{P.BG}" opacity=".7"/>'
               f'<text class="m" x="64" y="{H - 13}" font-size="11" fill="{P.MUTED}">'
               f'one tower = one day of my last year · height = commits · peak {top[1]} on '
               f'{top[0].strftime("%d %b %Y")}</text>')
    out.append("</g>")

    css = (
        "@keyframes rise{from{transform:scaleY(.02)}to{transform:scaleY(1)}}"
        ".t{transform-box:fill-box;transform-origin:50% 100%;animation:rise 1.3s cubic-bezier(.2,.9,.25,1) both}"
        "@keyframes tw{0%,100%{opacity:.9}50%{opacity:.15}}.tw{animation:tw 3.5s ease-in-out infinite}"
        "@keyframes win{0%,100%{opacity:.85}50%{opacity:.05}}.win{animation:win 2.8s steps(2) infinite}"
        "@keyframes beacon{0%,100%{opacity:.9}50%{opacity:.3}}.beacon{animation:beacon 1.6s ease-in-out infinite}")
    body = "".join(out)
    return svg(W, H, body, f"A night city built from my contribution calendar: one tower per day, {data['total']:,} contributions in the last year, with KAUSHIK on a neon sign.", css)


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
                       f'fill="none" stroke="{P.GOLD}" stroke-width="1.6"/>')
        else:
            out.append(cell(x, y, size, t["lv"][0]))
    lx = gx + cols * pitch + 24
    out.append(f'<text class="m" x="{lx}" y="{gy + 10}" font-size="11" letter-spacing="1.5" fill="{P.BLUE}">LATEST</text>')
    for j, v in enumerate(reversed(visitors[-5:])):
        y = gy + 34 + j * 20
        out.append(cell(lx, y - 11, 11, t["lv"][max(1, min(4, int(v.get("level", 3))))]))
        out.append(f'<text x="{lx + 18}" y="{y - 1}" font-size="13" fill="{t["text"]}">'
                   f'<tspan font-weight="600">@{escape(v["login"])}</tspan>'
                   f'<tspan fill="{t["muted"]}">  {escape(v["msg"][:28])}</tspan></text>')
    H = gy + rows * pitch + 18
    out[0] = f'<rect width="{W}" height="{H}" rx="12" fill="{t["bg"]}" stroke="{P.BORDER}"/>'
    css = ("@keyframes new{0%,100%{opacity:1}50%{opacity:.4}}.new{animation:new 1.6s ease-in-out infinite}"
           "@keyframes slot{0%,100%{opacity:1}50%{opacity:.2}}.slot{animation:slot 1s steps(2) infinite}")
    return svg(W, H, "".join(out), f"The square wall: {n} lit square{'' if n == 1 else 's'} so far. "
               "Latest: " + ", ".join("@" + v["login"] for v in visitors[-5:]), css)
