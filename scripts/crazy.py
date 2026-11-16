"""The loud parts: the synthwave city, the square wall and the CTF banner."""

import json
import math
import random
from html import escape
from pathlib import Path

import palette as P
from build import FONT, cell, streaks, svg

ROOT = Path(__file__).resolve().parent.parent
TOWER = ["#241a4d", "#4c1d95", "#a21caf", "#ff2a6d", "#05d9e8"]


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
    W, H = 1200, 660
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
        '<stop offset="0" stop-color="#05010f"/><stop offset=".45" stop-color="#1a0638"/>'
        '<stop offset=".72" stop-color="#4a0b5e"/><stop offset=".73" stop-color="#0b0221"/>'
        '<stop offset="1" stop-color="#0b0221"/></linearGradient>'
        '<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{P.YELLOW}"/><stop offset=".55" stop-color="{P.ORANGE}"/>'
        f'<stop offset="1" stop-color="{P.PINK}"/></linearGradient>'
        '<linearGradient id="sign" gradientUnits="userSpaceOnUse" x1="64" y1="0" x2="640" y2="0">'
        f'<stop offset="0" stop-color="{P.PINK}"/><stop offset=".5" stop-color="#ff6ad5"/>'
        f'<stop offset="1" stop-color="{P.CYAN}"/></linearGradient>'
        '<radialGradient id="haze" cx=".53" cy=".72" r=".55">'
        f'<stop offset="0" stop-color="{P.PINK}" stop-opacity=".45"/><stop offset="1" stop-color="{P.PINK}" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{P.CYAN}" stop-opacity="0"/><stop offset=".5" stop-color="{P.CYAN}" stop-opacity=".2"/>'
        f'<stop offset="1" stop-color="{P.CYAN}" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="up" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{P.CYAN}" stop-opacity=".95"/><stop offset="1" stop-color="{P.CYAN}" stop-opacity="0"/>'
        '</linearGradient>'
        '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".15"/><stop offset="1" stop-color="#fff"/></linearGradient>'
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

    # Striped sunset sun
    out.append('<g clip-path="url(#above)">')
    out.append(f'<circle cx="{sun_cx}" cy="{sun_cy}" r="{sun_r + 30}" fill="{P.PINK}" opacity=".18" filter="url(#soft)"/>')
    stripes = []
    for i in range(9):
        y = sun_cy + 10 + i * 17
        stripes.append(f'<rect x="{sun_cx - sun_r}" y="{y}" width="{sun_r * 2}" height="{2 + i * 1.3:.1f}" fill="#000"/>')
    out.append(f'<mask id="sunmask"><rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>{"".join(stripes)}</mask>'
               f'<circle cx="{sun_cx}" cy="{sun_cy}" r="{sun_r}" fill="url(#sun)" mask="url(#sunmask)" class="sunp"/></g>')

    # Wireframe mountains on the horizon
    for layer, (amp, col, op) in enumerate(((95, P.PURPLE, .55), (60, "#5b1a8f", .9))):
        pts, x = [], -20
        r2 = random.Random(layer + 3)
        while x <= W + 20:
            pts.append(f"{x},{base - 4 - r2.uniform(0.2, 1) * amp * (0.55 + 0.45 * math.sin(x / 140 + layer)):.1f}")
            x += r2.randint(40, 90)
        out.append(f'<polygon points="-20,{base} {" ".join(pts)} {W + 20},{base}" fill="#12052e" '
                   f'stroke="{col}" stroke-width="1.5" stroke-opacity="{op}"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#haze)"/>')

    # Neon sign
    out.append(f'<g filter="url(#glow)">{pixel_word("KAUSHIK", 64, 52, 11, 3, "url(#sign)", "sign")}</g>')
    out.append(f'<text class="m" x="64" y="176" font-size="15" fill="{P.CYAN}" letter-spacing="1.5">'
               '&gt; full-stack + security engineer // blank repo to live demo</text>')

    # HUD
    hud = [("COMMITS", f"{data['total']:,}"), ("BEST STREAK", f"{best}d"),
           ("ACTIVE DAYS", f"{active}"), ("REPOS", f"{data['repos']}")]
    for i, (k, v) in enumerate(hud):
        x, y = 860 + (i % 2) * 150, 48 + (i // 2) * 66
        out.append(f'<rect x="{x}" y="{y}" width="138" height="54" rx="6" fill="{P.BG}" fill-opacity=".75" '
                   f'stroke="{P.PINK}" stroke-opacity=".7"/><text class="m" x="{x + 12}" y="{y + 19}" font-size="10" '
                   f'letter-spacing="1.5" fill="{P.CYAN}">{k}</text><text class="m" x="{x + 12}" y="{y + 43}" '
                   f'font-size="20" font-weight="700" fill="{P.TEXT}">{v}</text>')

    # Grid floor: converging verticals + horizontals that roll toward the viewer
    vx, vy = sun_cx, base - 60
    floor = [f'<rect x="0" y="{base}" width="{W}" height="{H - base}" fill="#0b0221"/>']
    for i in range(-24, 25):
        x2 = vx + i * 70
        floor.append(f'<path d="M{vx} {vy}L{x2 * 3 - vx * 2} {H + (H - vy) * 2}" stroke="{P.PINK}" stroke-width="1.2"/>')
    rows_ = []
    for k in range(14):
        y = base + 4 + (k ** 1.85) * 2.6
        rows_.append(f'<path d="M0 {y:.1f}H{W}" stroke="{P.CYAN}" stroke-width="{0.8 + k * 0.12:.2f}"/>')
    floor.append(f'<g class="roll">{"".join(rows_)}</g>')
    out.append(f'<g clip-path="url(#floor)" mask="url(#floorfade)" opacity=".85">{"".join(floor)}</g>')
    out.append(f'<path d="M0 {base + 1}H{W}" stroke="{P.PINK}" stroke-width="2" filter="url(#glow)"/>')

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
                   f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="4" fill="{P.CYAN}"><animate attributeName="r" values="3;10;3" '
                   f'dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;.2;1" dur="1.6s" '
                   f'repeatCount="indefinite"/></circle>'
                   f'<text class="m" x="{tx - 10:.1f}" y="{ty - 158:.1f}" font-size="11" fill="{P.CYAN}" text-anchor="end">'
                   'TODAY ▸</text>')

    out.append(f'<rect class="sweep" x="-160" y="190" width="160" height="{base - 190}" fill="url(#beam)"/>')
    out.append(f'<rect x="0" y="{H - 34}" width="{W}" height="34" fill="{P.BG}" opacity=".7"/>'
               f'<text class="m" x="64" y="{H - 13}" font-size="11" fill="{P.MUTED}">'
               f'one tower = one day of my last year · height = commits · peak {top[1]} on '
               f'{top[0].strftime("%d %b %Y")}</text>')
    out.append("</g>")

    desc_file = ROOT / "ctf" / "desc.hex"
    desc = desc_file.read_text().strip() if desc_file.exists() else ""
    step = (base + 4 + 13 ** 1.85 * 2.6) - (base + 4 + 12 ** 1.85 * 2.6)
    css = (
        "@keyframes rise{from{transform:scaleY(.02)}to{transform:scaleY(1)}}"
        ".t{transform-box:fill-box;transform-origin:50% 100%;animation:rise 1.3s cubic-bezier(.2,.9,.25,1) both}"
        "@keyframes tw{0%,100%{opacity:.9}50%{opacity:.15}}.tw{animation:tw 3.5s ease-in-out infinite}"
        "@keyframes flick{0%,17%,21%,24%,52%,56%,100%{opacity:1}19%,23%,54%{opacity:.3}}"
        ".sign{animation:flick 6s linear infinite}"
        "@keyframes win{0%,100%{opacity:.85}50%{opacity:.05}}.win{animation:win 2.8s steps(2) infinite}"
        f"@keyframes sweep{{from{{transform:translateX(0)}}to{{transform:translateX({W + 160}px)}}}}"
        ".sweep{animation:sweep 7s linear infinite}"
        "@keyframes roll{from{transform:translateY(0)}to{transform:translateY(" + f"{step:.1f}" + "px)}}"
        ".roll{animation:roll 1.2s linear infinite}"
        "@keyframes sunp{0%,100%{opacity:1}50%{opacity:.86}}.sunp{animation:sunp 4s ease-in-out infinite}"
        "@keyframes beacon{0%,100%{opacity:.9}50%{opacity:.3}}.beacon{animation:beacon 1.6s ease-in-out infinite}")
    body = f"<desc>{desc}</desc>" + "".join(out)
    return svg(W, H, body, f"A synthwave city built from my contribution calendar: one neon tower per day under a "
               f"striped sunset, {data['total']:,} contributions in the last year, with KAUSHIK on a flickering sign.", css)


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
                       f'fill="none" stroke="{P.CYAN}" stroke-width="1.6"/>')
        else:
            out.append(cell(x, y, size, t["lv"][0]))
    lx = gx + cols * pitch + 24
    out.append(f'<text class="m" x="{lx}" y="{gy + 10}" font-size="11" letter-spacing="1.5" fill="{P.PINK}">LATEST</text>')
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


# ---------------------------------------------------------------- CTF banner


def ctf_banner(stage1, solved):
    W, cols, rows, pitch, size = 1000, 62, 8, 16, 12
    bits = "".join(f"{ord(ch):08b}" for ch in stage1)
    rnd = random.Random(31)
    ox = (W - cols * pitch) / 2 + 2
    out = ['<defs><linearGradient id="t" x1="0" y1="0" x2="1" y2="0">'
           f'<stop offset="0" stop-color="{P.PINK}"/><stop offset="1" stop-color="{P.CYAN}"/></linearGradient></defs>',
           f'<rect width="{W}" height="230" rx="12" fill="{P.BG}" stroke="{P.BORDER}"/>']
    for i in range(cols * rows):
        b = bits[i % len(bits)]
        x, y = ox + (i % cols) * pitch, 22 + (i // cols) * pitch
        lv = rnd.choice((3, 4)) if b == "1" else rnd.choice((0, 0, 1))
        cls = ' class="fl"' if rnd.random() < 0.08 else ""
        out.append(cell(x, y, size, P.LV[lv], cls + f' style="animation-delay:{rnd.uniform(0, 3):.1f}s"'))
    out.append(f'<rect x="{W / 2 - 250}" y="58" width="500" height="64" rx="8" fill="{P.BG}" fill-opacity=".9" '
               'stroke="url(#t)" stroke-width="2"/>'
               f'<text class="m g" x="{W / 2}" y="98" font-size="22" font-weight="700" fill="url(#t)" text-anchor="middle" '
               'letter-spacing="4">INTERCEPTED TRANSMISSION</text>')
    out.append(f'<text class="m" x="{W / 2}" y="180" font-size="13" fill="{P.MUTED}" text-anchor="middle">'
               'bright square = 1, dark square = 0 · three stages · one flag · a Hall of Fame</text>'
               f'<text class="m" x="{W / 2}" y="204" font-size="13" fill="{P.CYAN}" text-anchor="middle">'
               f'{solved} operator{"s" if solved != 1 else ""} cracked it so far. you could be next.</text>')
    css = ("@keyframes fl{0%,100%{opacity:1}50%{opacity:.1}}.fl{animation:fl .9s steps(2) infinite}"
           "@keyframes g{0%,92%,100%{transform:none}94%{transform:translateX(-3px)}96%{transform:translateX(3px)}}"
           ".g{animation:g 3s linear infinite}")
    return svg(W, 230, "".join(out), "Intercepted transmission: a three-stage CTF hidden in this profile.", css)
