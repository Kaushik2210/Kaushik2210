#!/usr/bin/env python3
"""assets/badge.svg: a custom conference-style badge that swings on its lanyard.

Left: the badge (halftone portrait from your avatar, name, handle, live stats, a
barcode derived from your login, a holographic sweep). Right: the invitation to
open the virtual badge page, which runs DOOM with your avatar (?u=<login>).
Original design, built from the GitHub API on each run. Pure SMIL, no JavaScript.
"""
import colorsys
import hashlib
import io
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/badge.svg"
W, H = 830, 452
BX, BY, BW, BH = 100, 92, 240, 340          # badge rect
PCX, PCY = BX + BW / 2, 60                  # pivot: where the lanyard clips on
COLS, PITCH = 32, 4.6                       # portrait halftone grid
CROP = (0.26, 0.34, 0.80, 0.86)             # face + a little shoulder


def portrait():
    raw = urllib.request.urlopen(urllib.request.Request(
        f"https://github.com/{USER}.png?size=460", headers={"User-Agent": "profile-gen"}), timeout=30).read()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    im = im.crop((int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h)))
    rows = round(COLS * im.height / im.width)
    im = im.resize((COLS, rows), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=1)
    lum = im.convert("L")
    blur = lum.filter(ImageFilter.GaussianBlur(3))
    px, lp, bp = im.load(), lum.load(), blur.load()
    for y in range(rows):
        for x in range(COLS):
            l, b = lp[x, y] / 255, bp[x, y] / 255
            adj = max(0.0, min(1.0, 0.4 * l + 0.6 * (0.5 + 2.2 * (l - b))))
            k = adj / l if l > 0.02 else 1.0
            r, g, bl = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(bl * k)))
    return im, rows


def duotone(l):
    for (a, ca), (b, cb) in zip(t.DUOTONE, t.DUOTONE[1:]):
        if l <= b:
            k = (l - a) / (b - a)
            return tuple(round(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
    return t.DUOTONE[-1][1]


def portrait_dots(im, rows, x0, y0):
    out = []
    for y in range(rows):
        for x in range(COLS):
            r, g, b = (v / 255 for v in im.getpixel((x, y)))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 0.10:
                continue
            rad = PITCH * 0.52 * min(1.0, (lum * 1.1) ** 0.6)
            c = duotone(min(1.0, lum * 1.05))
            out.append(f'<circle cx="{x0 + x * PITCH + PITCH / 2:.1f}" cy="{y0 + y * PITCH + PITCH / 2:.1f}" r="{rad:.2f}" fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"/>')
    return "".join(out)


def barcode(seed, x0, y, w, h):
    bits = bin(int(hashlib.sha256(seed.encode()).hexdigest(), 16))[2:].zfill(256)
    x, i, out = x0, 0, []
    while x < x0 + w - 2 and i < len(bits) - 1:
        bw = 1 + 2 * int(bits[i + 1])
        if bits[i] == "1":
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="{h}" fill="{t.TEXT2}"/>')
        x += bw + 1
        i += 2
    return "".join(out)


def main():
    u = common.user_graph(USER)
    cur, longest = common.streaks(common.days(u))
    cc = u["contributionsCollection"]
    rp = common.repos(USER)
    hist, npush = common.push_hours(USER)
    peak = max(range(24), key=lambda h: hist[h])
    streak_val, streak_lab = (cur, "STREAK") if cur >= 5 else (longest, "BEST STREAK")
    im, rows = portrait()
    pw, ph = COLS * PITCH, rows * PITCH
    px0, py0 = BX + (BW - pw) / 2, BY + 62
    sy = py0 + ph + 14   # stats strip top

    alt = (f"A custom conference-style badge for {USER}: halftone portrait, {streak_val}-day {streak_lab.lower()}, "
           f"{cc['totalCommitContributions']} commits this year, {len(rp)} repositories. "
           f"Opens a virtual badge that runs DOOM with my GitHub avatar.")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
         f"<title>{escape(USER)}: custom badge</title>",
         t.defs(f"""
<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<clipPath id="bc"><rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="18"/></clipPath>
<linearGradient id="face" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t.RAISED}"/><stop offset="1" stop-color="{t.SURFACE}"/></linearGradient>
<linearGradient id="holo" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".30"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="strap" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t.A1}"/><stop offset="1" stop-color="{t.A3}"/></linearGradient>
<radialGradient id="glowL"><stop offset="0" stop-color="{t.GLOW[0]}" stop-opacity=".5"/><stop offset="1" stop-color="{t.GLOW[0]}" stop-opacity="0"/></radialGradient>
<radialGradient id="glowR"><stop offset="0" stop-color="{t.GLOW[2]}" stop-opacity=".30"/><stop offset="1" stop-color="{t.GLOW[2]}" stop-opacity="0"/></radialGradient>"""),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="{t.CANVAS}"/>',
         f'<ellipse cx="{PCX}" cy="250" rx="260" ry="220" fill="url(#glowL)"/>',
         f'<ellipse cx="640" cy="350" rx="260" ry="150" fill="url(#glowR)"/>']
    for gx in range(0, W, 28):
        for gy in range(0, H, 28):
            o.append(f'<circle cx="{gx + 6}" cy="{gy + 6}" r=".8" fill="#fff" fill-opacity=".06"/>')

    # ---------------- swinging badge ----------------
    o.append(f'<g><animateTransform attributeName="transform" type="rotate" values="3.4 {PCX} {PCY};-3.4 {PCX} {PCY};3.4 {PCX} {PCY}" dur="6.4s" '
             f'repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>')
    # lanyard straps + clip
    o.append(f'<polygon points="{PCX - 62},-4 {PCX - 44},-4 {PCX + 4},{PCY - 6} {PCX - 10},{PCY - 6}" fill="url(#strap)"/>')
    o.append(f'<polygon points="{PCX + 62},-4 {PCX + 44},-4 {PCX - 4},{PCY - 6} {PCX + 10},{PCY - 6}" fill="url(#strap)" opacity=".8"/>')
    o.append(f'<rect x="{PCX - 14}" y="{PCY - 10}" width="28" height="22" rx="6" fill="{t.HAIRLINE}" stroke="{t.TEXT3}" stroke-width="1.2"/>'
             f'<rect x="{PCX - 6}" y="{PCY + 2}" width="12" height="18" rx="4" fill="{t.TEXT3}"/>')
    # badge body
    o.append(f'<rect x="{BX + 4}" y="{BY + 8}" width="{BW}" height="{BH}" rx="18" fill="#000" opacity=".35"/>')
    o.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="18" fill="url(#face)" stroke="url(#bdr)" stroke-width="1.6"/>')
    o.append('<g clip-path="url(#bc)">')
    o.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="46" fill="url(#aurora)" opacity=".92"/>')
    o.append(f'<rect x="{PCX - 22}" y="{BY + 11}" width="44" height="9" rx="4.5" fill="{t.CANVAS}"/>')           # lanyard slot
    o.append(f'<text x="{PCX}" y="{BY + 36}" class="mono" font-size="9" letter-spacing="2.6" text-anchor="middle" fill="{t.CANVAS}" font-weight="700">BUILDER &#183; ALL ACCESS</text>')
    # portrait frame
    o.append(f'<rect x="{px0 - 6}" y="{py0 - 6}" width="{pw + 12}" height="{ph + 12}" rx="10" fill="{t.SURFACE}" stroke="{t.HAIRLINE}"/>')
    o.append(portrait_dots(im, rows, px0, py0))
    # stats strip
    o.append(f'<text x="{BX + 18}" y="{sy + 22}" font-size="25" font-weight="800" letter-spacing="-.5" fill="{t.TEXT}">KAUSHIK</text>')
    o.append(f'<text x="{BX + 18}" y="{sy + 38}" class="mono" font-size="10" fill="{t.A2}">@{escape(USER)}</text>')
    cells = [(str(streak_val) + "d", streak_lab), (str(cc["totalCommitContributions"]), "COMMITS / YR"), (str(len(rp)), "REPOS")]
    cw = (BW - 24) / 3
    for i, (v, l) in enumerate(cells):
        cx = BX + 12 + i * cw
        o.append(f'<rect x="{cx:.0f}" y="{sy + 50}" width="{cw - 6:.0f}" height="36" rx="8" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{cx + (cw - 6) / 2:.0f}" y="{sy + 66}" font-size="14" font-weight="700" fill="{t.A3}" text-anchor="middle">{escape(v)}</text>'
                 f'<text x="{cx + (cw - 6) / 2:.0f}" y="{sy + 79}" class="mono" font-size="7" letter-spacing=".9" fill="{t.TEXT3}" text-anchor="middle">{l}</text>')
    o.append(barcode(USER.lower(), BX + 18, sy + 96, BW - 36, 14))
    # holographic sweep
    o.append(f'<rect x="{BX - 90}" y="{BY - 20}" width="70" height="{BH + 40}" fill="url(#holo)" transform="skewX(-18)" opacity="0">'
             f'<animate attributeName="x" values="{BX - 40};{BX + BW + 60};{BX + BW + 60}" keyTimes="0;.32;1" dur="7s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;.12;.32;1" dur="7s" repeatCount="indefinite"/></rect>')
    o.append("</g></g>")

    # ---------------- right: the invitation ----------------
    rx = 410
    o.append(f'<text x="{rx}" y="104" class="label" style="fill:{t.A3}">VIRTUAL BADGE</text>')
    o.append(f'<text x="{rx}" y="156" font-size="42" font-weight="800" letter-spacing="-1.5" fill="url(#aurora)">Does my badge</text>')
    o.append(f'<text x="{rx}" y="204" font-size="42" font-weight="800" letter-spacing="-1.5" fill="url(#aurora)">run DOOM?</text>')
    o.append(f'<text x="{rx}" y="238" font-size="14" fill="{t.TEXT}">Of course it does.</text>')
    o.append(f'<text x="{rx}" y="260" font-size="12" fill="{t.TEXT2}">Open the virtual badge with my GitHub avatar on it and play.</text>')
    # button
    o.append(f'<g><rect x="{rx}" y="282" width="188" height="42" rx="21" fill="url(#aurora)"/>'
             f'<text x="{rx + 94}" y="308" font-size="13" font-weight="700" fill="{t.CANVAS}" text-anchor="middle" letter-spacing=".5">OPEN MY BADGE &#8599;</text>'
             f'<rect x="{rx}" y="282" width="188" height="42" rx="21" fill="none" stroke="#fff" stroke-opacity=".7"><animate attributeName="stroke-opacity" values=".15;.8;.15" dur="2.8s" repeatCount="indefinite"/></rect></g>')
    # controls
    for i, (k, d) in enumerate((("ARROWS", "move"), ("CTRL", "fire"), ("SPACE", "use"))):
        kx = rx + i * 104
        wd = 14 + 7.4 * len(k)
        o.append(f'<rect x="{kx}" y="346" width="{wd:.0f}" height="22" rx="6" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{kx + wd / 2:.0f}" y="361" class="mono" font-size="10" fill="{t.TEXT}" text-anchor="middle">{k}</text>'
                 f'<text x="{kx + wd + 7:.0f}" y="361" font-size="11" fill="{t.TEXT3}">{d}</text>')
    o.append(f'<text x="{rx}" y="396" font-size="11" fill="{t.TEXT3}">In-game, type @your-username and press Enter to swap in your own avatar.</text>')
    o.append(f'<text x="{rx}" y="{H - 16}" class="mono" font-size="9" fill="{t.TEXT3}">badge built {datetime.now(timezone.utc):%Y-%m-%d} from live GitHub data &#183; peak push hour {peak:02d}:00</text>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: portrait {COLS}x{rows}, {streak_lab.lower()} {streak_val}, {cc['totalCommitContributions']} commits, {len(rp)} repos, {sum(len(x) for x in o) // 1024} KB")


if __name__ == "__main__":
    main()
