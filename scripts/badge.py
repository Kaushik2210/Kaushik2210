#!/usr/bin/env python3
"""assets/badge.svg: a custom conference-style badge that swings on its lanyard.

Left: the badge (halftone portrait from your avatar, name, handle, live stats, a
barcode derived from your login, a holographic sweep). Right: the invitation to
open the virtual badge page, which runs DOOM with your avatar (?u=<login>).
Original design, built from the GitHub API on each run. Pure SMIL, no JavaScript.
"""
import collections
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



def back(u, rp):
    """The back of the badge: an ID matrix from the login hash and an access card of real facts."""
    o = [f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.47;.4701;.97;.9701;1" dur="16s" repeatCount="indefinite"/>',
         f'<rect x="{BX + 4}" y="{BY + 8}" width="{BW}" height="{BH}" rx="18" fill="#000" opacity=".35"/>',
         f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="18" fill="url(#face)" stroke="url(#foil)" stroke-width="2.4"/>',
         '<g clip-path="url(#bc)">',
         f'<rect x="{BX}" y="{BY}" width="{BW}" height="46" fill="url(#foil)"/>',
         f'<rect x="{PCX - 22}" y="{BY + 11}" width="44" height="9" rx="4.5" fill="{t.CANVAS}"/>',
         f'<text x="{PCX}" y="{BY + 36}" class="mono" font-size="10" letter-spacing="2.4" text-anchor="middle" fill="{t.CANVAS}" font-weight="700">ACCESS LEVEL &#183; ROOT</text>']
    # ID matrix: 17x17 cells from the login's hash, with three corner markers
    n, cs = 17, 7.2
    mx0, my0 = PCX - n * cs / 2, BY + 62
    bits = bin(int(hashlib.sha256(("id:" + USER.lower()).encode()).hexdigest(), 16))[2:].zfill(256) * 2
    o.append(f'<rect x="{mx0 - 8}" y="{my0 - 8}" width="{n * cs + 16}" height="{n * cs + 16}" rx="8" fill="#f5efe6"/>')
    def corner(cx, cy):
        return (f'<rect x="{cx}" y="{cy}" width="{5 * cs}" height="{5 * cs}" fill="{t.CANVAS}"/>'
                f'<rect x="{cx + cs}" y="{cy + cs}" width="{3 * cs}" height="{3 * cs}" fill="#f5efe6"/>'
                f'<rect x="{cx + 2 * cs}" y="{cy + 2 * cs}" width="{cs}" height="{cs}" fill="{t.CANVAS}"/>')
    k = 0
    for r in range(n):
        for c in range(n):
            if (r < 6 and c < 6) or (r < 6 and c >= n - 6) or (r >= n - 6 and c < 6):
                continue
            if bits[k] == "1":
                o.append(f'<rect x="{mx0 + c * cs:.1f}" y="{my0 + r * cs:.1f}" width="{cs:.1f}" height="{cs:.1f}" fill="{t.CANVAS}"/>')
            k += 1
    o.append(corner(mx0, my0) + corner(mx0 + (n - 5) * cs, my0) + corner(mx0, my0 + (n - 5) * cs))
    # scan line over the matrix
    o.append(f'<rect x="{mx0 - 8}" y="{my0}" width="{n * cs + 16}" height="2" fill="{t.BEACON[0]}" opacity=".8">'
             f'<animate attributeName="y" values="{my0};{my0 + n * cs};{my0}" dur="2.4s" repeatCount="indefinite"/></rect>')
    # facts
    langs = collections.Counter(r["language"] for r in rp if r["language"])
    live = sum(1 for r in rp if (r.get("homepage") or "").strip())
    since = u["createdAt"][:4]
    facts = [("BASE", "Bangalore, IN"), ("SHIPPED", f"{live} live sites"), ("TOP LANG", langs.most_common(1)[0][0] if langs else "-"),
             ("MEMBER", f"since {since}"), ("CLEARANCE", "build · break · fix")]
    fy = my0 + n * cs + 30
    for i, (kk, v) in enumerate(facts):
        o.append(f'<text x="{BX + 22}" y="{fy + i * 17}" class="mono" font-size="9.5" fill="{t.TEXT3}">{kk}</text>'
                 f'<text x="{BX + BW - 22}" y="{fy + i * 17}" font-size="11.5" font-weight="600" fill="{t.TEXT}" text-anchor="end">{escape(v)}</text>')
    o.append(f'<text x="{PCX}" y="{BY + BH - 14}" class="mono" font-size="8.5" fill="{t.TEXT3}" text-anchor="middle">if found, return to github.com/{escape(USER)}</text>')
    o.append("</g></g>")
    return "".join(o)


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
           f"The badge flips to show an ID matrix and access card on the back. A small screen boots the badge and runs a corridor demo. "
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
<pattern id="crtscan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".35"/></pattern>
<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/></radialGradient>
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
    # the badge turns over every few seconds: front, then the back with the access card
    FLIP = 16
    o.append(f'<g transform="translate({PCX} 0)"><g><animateTransform attributeName="transform" type="scale" '
             f'values="1 1;1 1;0 1;1 1;1 1;0 1;1 1" keyTimes="0;.44;.47;.5;.94;.97;1" dur="{FLIP}s" repeatCount="indefinite"/>'
             f'<g transform="translate({-PCX} 0)">')
    o.append(f'<g><animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="0;.47;.4701;.97;.9701;1" dur="{FLIP}s" repeatCount="indefinite"/>')
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
    o.append("</g>")  # end of the front
    o.append(back(u, rp))
    o.append("</g></g></g>")  # end of the flip
    for sx, sy_, sz, col, dl in ((BX - 8, BY + 52, 9, SPEC[2], 0), (BX + BW + 10, BY + 120, 11, SPEC[4], .9), (BX + BW - 6, BY - 4, 8, SPEC[6], 1.7),
                                 (BX - 4, BY + BH - 70, 8, SPEC[3], 2.4), (BX + BW + 4, BY + BH - 20, 10, SPEC[1], .5), (BX + 40, BY + BH + 4, 7, SPEC[5], 1.3)):
        o.append(f'<g transform="translate({sx},{sy_})"><path d="M0,{-sz} Q0,0 {sz},0 Q0,0 0,{sz} Q0,0 {-sz},0 Q0,0 0,{-sz}Z" fill="{col}">'
                 f'<animateTransform attributeName="transform" type="scale" values="0;1;0" dur="2.6s" begin="{dl}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;0" dur="2.6s" begin="{dl}s" repeatCount="indefinite"/></path></g>')
    o.append("</g>")

    # ---------------- right: the invitation, with a CRT that boots the badge ----------------
    rx = 436
    o.append(f'<text x="{rx}" y="64" class="label" style="fill:{t.A3};font-size:11px">VIRTUAL BADGE</text>')
    o.append(f'<text x="{rx}" y="106" font-size="38" font-weight="800" letter-spacing="-1.4" fill="url(#aurora)">Does my badge</text>')
    o.append(f'<text x="{rx}" y="146" font-size="38" font-weight="800" letter-spacing="-1.4" fill="url(#aurora)">run DOOM?</text>')
    o.append(f'<text x="{rx + 222}" y="146" font-size="15" font-weight="600" fill="{t.TEXT}">Of course it does.</text>')
    # the screen
    sx0, sy0, sw, sh = rx, 166, 368, 168
    scx, scy = sx0 + sw / 2, sy0 + sh / 2 - 8
    CYC = 12
    o.append(f'<rect x="{sx0 - 8}" y="{sy0 - 8}" width="{sw + 16}" height="{sh + 16}" rx="16" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
             f'<clipPath id="crt"><rect x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" rx="10"/></clipPath>'
             f'<g clip-path="url(#crt)"><rect x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" fill="#07040a"/>')
    # boot sequence (first third of the loop)
    boot = [("> booting badge firmware ...", t.TEXT2), (f"> loading avatar @{USER} ... ok", t.GREEN),
            ("> map: corridor_01 ... ok", t.TEXT2), ("> PRESS START", t.A3)]
    for i, (line, col) in enumerate(boot):
        a0 = .02 + i * .06
        o.append(f'<text x="{sx0 + 16}" y="{sy0 + 34 + i * 22}" class="mono" font-size="11.5" fill="{col}" opacity="0">{escape(line)}'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{a0:.3f};{a0 + .005:.3f};.34;.345;1" dur="{CYC}s" repeatCount="indefinite"/></text>')
    # demo (rest of the loop): rushing down a corridor
    o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;.345;.35;1" dur="{CYC}s" repeatCount="indefinite"/>'
             f'<rect x="{sx0}" y="{scy}" width="{sw}" height="{sy0 + sh - scy}" fill="#1a0c08"/>')
    for k in range(7):
        d = 2.8
        o.append(f'<g transform="translate({scx:.0f} {scy:.0f})"><g><animateTransform attributeName="transform" type="scale" values=".05;2.4" dur="{d}s" begin="-{k * d / 7:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".7 0 1 1"/>'
                 f'<rect x="-60" y="-34" width="120" height="68" fill="none" stroke="url(#foilR)" stroke-width="1.6" vector-effect="non-scaling-stroke">'
                 f'<animate attributeName="stroke-opacity" values="0;1;1;0" keyTimes="0;.2;.8;1" dur="{d}s" begin="-{k * d / 7:.2f}s" repeatCount="indefinite"/></rect></g></g>')
    for dx in (-1, 1):  # corridor edges
        o.append(f'<line x1="{scx:.0f}" y1="{scy:.0f}" x2="{scx + dx * sw:.0f}" y2="{scy - sh:.0f}" stroke="#ff9a3d" stroke-opacity=".25"/>'
                 f'<line x1="{scx:.0f}" y1="{scy:.0f}" x2="{scx + dx * sw:.0f}" y2="{scy + sh:.0f}" stroke="#ff9a3d" stroke-opacity=".25"/>')
    # crosshair + muzzle flash + HUD
    o.append(f'<g stroke="{t.TEXT}" stroke-width="1.4" opacity=".9"><line x1="{scx - 9}" y1="{scy}" x2="{scx - 3}" y2="{scy}"/><line x1="{scx + 3}" y1="{scy}" x2="{scx + 9}" y2="{scy}"/>'
             f'<line x1="{scx}" y1="{scy - 9}" x2="{scx}" y2="{scy - 3}"/><line x1="{scx}" y1="{scy + 3}" x2="{scx}" y2="{scy + 9}"/></g>'
             f'<circle cx="{scx}" cy="{scy + 50}" r="16" fill="#ffd23f" opacity="0"><animate attributeName="opacity" values="0;0;.9;0;0;.9;0" keyTimes="0;.5;.52;.56;.75;.77;.81" dur="{CYC}s" repeatCount="indefinite"/></circle>'
             f'<path d="M{scx - 16} {sy0 + sh} L{scx - 9} {scy + 52} L{scx + 9} {scy + 52} L{scx + 16} {sy0 + sh} Z" fill="#3a3f4a" stroke="#6b7180"/>')
    o.append(f'<rect x="{sx0}" y="{sy0 + sh - 24}" width="{sw}" height="24" fill="#120806" opacity=".9"/>'
             f'<text x="{sx0 + 12}" y="{sy0 + sh - 8}" class="mono" font-size="10.5" font-weight="700" fill="#ff5a3d">HP 100</text>'
             f'<text x="{sx0 + 80}" y="{sy0 + sh - 8}" class="mono" font-size="10.5" font-weight="700" fill="#ffd23f">AMMO {len(rp)}</text>'
             f'<text x="{sx0 + sw - 12}" y="{sy0 + sh - 8}" class="mono" font-size="10.5" fill="{t.TEXT2}" text-anchor="end">@{escape(USER)}</text></g>')
    # scanlines, vignette, a flicker
    o.append(f'<rect x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" fill="url(#crtscan)"/>'
             f'<rect x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" fill="url(#vig)"/>'
             f'<rect x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" fill="#fff" opacity="0"><animate attributeName="opacity" values="0;0;.25;0;0" keyTimes="0;.345;.348;.36;1" dur="{CYC}s" repeatCount="indefinite"/></rect></g>')
    o.append(f'<circle cx="{sx0 + sw - 4}" cy="{sy0 + sh + 1}" r="2.2" fill="{t.GREEN}"><animate attributeName="opacity" values="1;.3;1" dur="1.4s" repeatCount="indefinite"/></circle>')
    # button + controls
    o.append(f'<rect x="{rx}" y="360" width="200" height="42" rx="21" fill="url(#aurora)" filter="url(#rim)" opacity=".45"><animate attributeName="opacity" values=".2;.6;.2" dur="2.8s" repeatCount="indefinite"/></rect>')
    o.append(f'<g><rect x="{rx}" y="360" width="200" height="42" rx="21" fill="url(#aurora)"/>'
             f'<text x="{rx + 100}" y="386" font-size="13.5" font-weight="700" fill="{t.CANVAS}" text-anchor="middle" letter-spacing=".5">PRESS START &#8599;</text></g>')
    for i, (k, d) in enumerate((("ARROWS", "move"), ("CTRL", "fire"), ("SPACE", "use"))):
        kx, ky = rx + 216 + (0 if i < 2 else 0), 352 + i * 19
        wd = 12 + 7 * len(k)
        o.append(f'<rect x="{kx}" y="{ky}" width="{wd:.0f}" height="16" rx="5" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{kx + wd / 2:.0f}" y="{ky + 11.5}" class="mono" font-size="9.5" fill="{t.TEXT}" text-anchor="middle">{k}</text>'
                 f'<text x="{kx + wd + 6:.0f}" y="{ky + 12}" font-size="11" fill="{t.TEXT2}">{d}</text>')
    o.append(f'<text x="{rx}" y="428" font-size="11.5" fill="{t.TEXT3}">In-game, type @your-username + Enter to use your own avatar.</text>')
    o.append(f'<text x="{rx}" y="{H - 14}" class="mono" font-size="9" fill="{t.TEXT3}">built {datetime.now(timezone.utc):%Y-%m-%d} from live GitHub data &#183; peak push hour {peak:02d}:00</text>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: portrait {COLS}x{rows}, {streak_lab.lower()} {streak_val}, {cc['totalCommitContributions']} commits, {len(rp)} repos, {sum(len(x) for x in o) // 1024} KB")


if __name__ == "__main__":
    main()
