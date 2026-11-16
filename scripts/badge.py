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
import os
import random
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

# the badge has its own palette, separate from the page's PROFILE_THEME (must be set before theme loads)
os.environ["PROFILE_THEME"] = os.environ.get("BADGE_THEME", "ember")

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/badge.svg"
W, H = 830, 470
BX, BY, BW, BH = 96, 90, 260, 356          # badge rect
PCX, PCY = BX + BW / 2, 60                  # pivot: where the lanyard clips on
COLS, PITCH = 36, 4.6                       # portrait halftone grid
CROP = (0.26, 0.34, 0.80, 0.86)             # face + a little shoulder
SPEC = ("#ff4a2b", "#ff9a3d", "#ffd23f", "#5af0c0", "#5cd0ff", "#b36bff", "#ff5fd0")   # holographic foil spectrum (same in every palette)
TILE = ("#ff7a3d", "#ffd23f", "#5cd0ff")                                                # per-stat accent colours


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
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="{h}" fill="url(#foil)"/>')
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
<linearGradient id="holo" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="foil" gradientUnits="userSpaceOnUse" x1="{BX}" y1="{BY}" x2="{BX + BW}" y2="{BY + BH * 0.6}" spreadMethod="reflect"><stop offset="0.000" stop-color="#ff4a2b"/><stop offset="0.167" stop-color="#ff9a3d"/><stop offset="0.333" stop-color="#ffd23f"/><stop offset="0.500" stop-color="#5af0c0"/><stop offset="0.667" stop-color="#5cd0ff"/><stop offset="0.833" stop-color="#b36bff"/><stop offset="1.000" stop-color="#ff5fd0"/><animateTransform attributeName="gradientTransform" type="translate" values="0 0;{BW} {BH * 0.6};0 0" dur="6s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="foilR" gradientUnits="userSpaceOnUse" x1="410" y1="0" x2="640" y2="0" spreadMethod="reflect"><stop offset="0.000" stop-color="#ff4a2b"/><stop offset="0.167" stop-color="#ff9a3d"/><stop offset="0.333" stop-color="#ffd23f"/><stop offset="0.500" stop-color="#5af0c0"/><stop offset="0.667" stop-color="#5cd0ff"/><stop offset="0.833" stop-color="#b36bff"/><stop offset="1.000" stop-color="#ff5fd0"/><animateTransform attributeName="gradientTransform" type="translate" values="0 0;230 0;0 0" dur="7s" repeatCount="indefinite"/></linearGradient>
<filter id="rim" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="8"/></filter>
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

    # ---------------- rising embers ----------------
    rnd = random.Random(2210)
    for _ in range(20):
        ex, dur = rnd.uniform(16, W - 16), rnd.uniform(5, 12)
        sway, col, r = rnd.uniform(-26, 26), rnd.choice(SPEC[:3]), rnd.choice((1, 1.3, 1.7))
        beg = f'{-rnd.uniform(0, dur):.1f}s'
        o.append(f'<circle r="{r}" fill="{col}" opacity="0"><animateTransform attributeName="transform" type="translate" '
                 f'values="{ex:.0f} {H + 8};{ex + sway:.0f} -10" dur="{dur:.1f}s" begin="{beg}" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.7;.7;0" keyTimes="0;.12;.7;1" dur="{dur:.1f}s" begin="{beg}" repeatCount="indefinite"/></circle>')

    # ---------------- swinging badge ----------------
    o.append(f'<g><animateTransform attributeName="transform" type="rotate" values="3.4 {PCX} {PCY};-3.4 {PCX} {PCY};3.4 {PCX} {PCY}" dur="6.4s" '
             f'repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>')
    o.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="18" fill="none" stroke="url(#foil)" stroke-width="7" filter="url(#rim)" opacity=".5">'
             f'<animate attributeName="opacity" values=".25;.75;.25" dur="3.2s" repeatCount="indefinite"/></rect>')
    # lanyard straps + clip
    o.append(f'<polygon points="{PCX - 62},-4 {PCX - 44},-4 {PCX + 4},{PCY - 6} {PCX - 10},{PCY - 6}" fill="url(#strap)"/>')
    o.append(f'<polygon points="{PCX + 62},-4 {PCX + 44},-4 {PCX - 4},{PCY - 6} {PCX + 10},{PCY - 6}" fill="url(#strap)" opacity=".8"/>')
    o.append(f'<rect x="{PCX - 14}" y="{PCY - 10}" width="28" height="22" rx="6" fill="{t.HAIRLINE}" stroke="{t.TEXT3}" stroke-width="1.2"/>'
             f'<rect x="{PCX - 6}" y="{PCY + 2}" width="12" height="18" rx="4" fill="{t.TEXT3}"/>')
    # badge body
    o.append(f'<rect x="{BX + 4}" y="{BY + 8}" width="{BW}" height="{BH}" rx="18" fill="#000" opacity=".35"/>')
    o.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="18" fill="url(#face)" stroke="url(#foil)" stroke-width="2.4"/>')
    o.append(f'<rect x="{BX + 5}" y="{BY + 5}" width="{BW - 10}" height="{BH - 10}" rx="14" fill="none" stroke="#fff" stroke-opacity=".08"/>')
    o.append('<g clip-path="url(#bc)">')
    o.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="46" fill="url(#foil)"/>')
    o.append(f'<rect x="{PCX - 22}" y="{BY + 11}" width="44" height="9" rx="4.5" fill="{t.CANVAS}"/>')           # lanyard slot
    o.append(f'<text x="{PCX}" y="{BY + 36}" class="mono" font-size="10" letter-spacing="2.4" text-anchor="middle" fill="{t.CANVAS}" font-weight="700">BUILDER &#183; ALL ACCESS</text>')
    # portrait frame
    o.append(f'<rect x="{px0 - 6}" y="{py0 - 6}" width="{pw + 12}" height="{ph + 12}" rx="10" fill="{t.SURFACE}" stroke="url(#foil)" stroke-width="1.6"/>')
    o.append(portrait_dots(im, rows, px0, py0))
    # stats strip
    o.append(f'<text x="{BX + 18}" y="{sy + 22}" font-size="27" font-weight="800" letter-spacing="-.5" fill="url(#foil)">KAUSHIK</text>')
    o.append(f'<text x="{BX + 18}" y="{sy + 38}" class="mono" font-size="11" fill="{t.A2}">@{escape(USER)}</text>')
    cells = [(str(streak_val) + "d", streak_lab), (str(cc["totalCommitContributions"]), "COMMITS / YR"), (str(len(rp)), "REPOS")]
    cw = (BW - 24) / 3
    for i, (v, l) in enumerate(cells):
        cx, col = BX + 12 + i * cw, TILE[i]
        o.append(f'<rect x="{cx:.0f}" y="{sy + 50}" width="{cw - 6:.0f}" height="36" rx="8" fill="{t.RAISED}" stroke="{col}" stroke-opacity=".6"/>'
                 f'<rect x="{cx + 8:.0f}" y="{sy + 50}" width="{cw - 22:.0f}" height="2.5" rx="1.2" fill="{col}"/>'
                 f'<text x="{cx + (cw - 6) / 2:.0f}" y="{sy + 67}" font-size="15" font-weight="700" fill="{col}" text-anchor="middle">{escape(v)}</text>'
                 f'<text x="{cx + (cw - 6) / 2:.0f}" y="{sy + 79}" class="mono" font-size="8" letter-spacing=".7" fill="{t.TEXT3}" text-anchor="middle">{l}</text>')
    o.append(barcode(USER.lower(), BX + 18, sy + 96, BW - 36, 14))
    # holographic sweep
    o.append(f'<rect x="{BX - 90}" y="{BY - 20}" width="70" height="{BH + 40}" fill="url(#holo)" transform="skewX(-18)" opacity="0">'
             f'<animate attributeName="x" values="{BX - 40};{BX + BW + 60};{BX + BW + 60}" keyTimes="0;.32;1" dur="7s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;.12;.32;1" dur="7s" repeatCount="indefinite"/></rect>')
    o.append("</g>")
    for sx, sy_, sz, col, dl in ((BX - 8, BY + 52, 9, SPEC[2], 0), (BX + BW + 10, BY + 120, 11, SPEC[4], .9), (BX + BW - 6, BY - 4, 8, SPEC[6], 1.7),
                                 (BX - 4, BY + BH - 70, 8, SPEC[3], 2.4), (BX + BW + 4, BY + BH - 20, 10, SPEC[1], .5), (BX + 40, BY + BH + 4, 7, SPEC[5], 1.3)):
        o.append(f'<g transform="translate({sx},{sy_})"><path d="M0,{-sz} Q0,0 {sz},0 Q0,0 0,{sz} Q0,0 {-sz},0 Q0,0 0,{-sz}Z" fill="{col}">'
                 f'<animateTransform attributeName="transform" type="scale" values="0;1;0" dur="2.6s" begin="{dl}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;0" dur="2.6s" begin="{dl}s" repeatCount="indefinite"/></path></g>')
    o.append("</g>")

    # ---------------- right: the invitation ----------------
    rx = 436
    o.append(f'<text x="{rx}" y="112" class="label" style="fill:{t.A3};font-size:11px">VIRTUAL BADGE</text>')
    o.append(f'<text x="{rx}" y="166" font-size="46" font-weight="800" letter-spacing="-1.6" fill="url(#aurora)">Does my badge</text>')
    o.append(f'<text x="{rx}" y="218" font-size="46" font-weight="800" letter-spacing="-1.6" fill="url(#aurora)">run DOOM?</text>')
    o.append(f'<text x="{rx}" y="256" font-size="16" font-weight="600" fill="{t.TEXT}">Of course it does.</text>')
    o.append(f'<text x="{rx}" y="280" font-size="13" fill="{t.TEXT2}">Open the virtual badge with my GitHub avatar on it and play.</text>')
    # button
    o.append(f'<rect x="{rx}" y="304" width="210" height="46" rx="23" fill="url(#aurora)" filter="url(#rim)" opacity=".45"><animate attributeName="opacity" values=".2;.6;.2" dur="2.8s" repeatCount="indefinite"/></rect>')
    o.append(f'<g><rect x="{rx}" y="304" width="210" height="46" rx="23" fill="url(#aurora)"/>'
             f'<text x="{rx + 105}" y="332" font-size="14" font-weight="700" fill="{t.CANVAS}" text-anchor="middle" letter-spacing=".5">OPEN MY BADGE &#8599;</text></g>')
    # controls
    for i, (k, d) in enumerate((("ARROWS", "move"), ("CTRL", "fire"), ("SPACE", "use"))):
        kx = rx + (0, 118, 214)[i]
        wd = 16 + 8 * len(k)
        o.append(f'<rect x="{kx}" y="372" width="{wd:.0f}" height="24" rx="7" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{kx + wd / 2:.0f}" y="388" class="mono" font-size="11" fill="{t.TEXT}" text-anchor="middle">{k}</text>'
                 f'<text x="{kx + wd + 8:.0f}" y="388" font-size="12" fill="{t.TEXT2}">{d}</text>')
    o.append(f'<text x="{rx}" y="418" font-size="12" fill="{t.TEXT3}">In-game, type @your-username and press Enter</text>')
    o.append(f'<text x="{rx}" y="435" font-size="12" fill="{t.TEXT3}">to swap in your own avatar.</text>')
    o.append(f'<text x="{rx}" y="{H - 12}" class="mono" font-size="9" fill="{t.TEXT3}">built {datetime.now(timezone.utc):%Y-%m-%d} from live GitHub data &#183; peak push hour {peak:02d}:00</text>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: portrait {COLS}x{rows}, {streak_lab.lower()} {streak_val}, {cc['totalCommitContributions']} commits, {len(rp)} repos, {sum(len(x) for x in o) // 1024} KB")


if __name__ == "__main__":
    main()
