#!/usr/bin/env python3
"""assets/p-<repo>.svg + the FEATURED BUILDS block of README.md.

One poster per featured repo (curated in data/projects.json). Each has generative
cover art seeded from the repo name (so no two look alike), with a motif per
category, plus live data from the GitHub API: language, stars, last push, and a
pill that says where a click goes (LIVE demo or REPO).

Also rewrites the collapsed "more builds" list. Pure SMIL, no JavaScript.
Usage: posters.py [user] [README.md]
"""
import json
import math
import os
import random
import re
import sys
import zlib
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common
import scenes
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
README = sys.argv[2] if len(sys.argv) > 2 else "README.md"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "data", "projects.json")
ASSETS = os.path.join(HERE, "..", "assets")
START, END = "<!--BUILDS_START-->", "<!--BUILDS_END-->"
W, H, ART = 405, 324, 150
TICK = 24  # mission-log strip under the art
SKIP_TOPICS = {"hackathon", "hacktoberfest", "good-first-issue", "typescript", "python", "javascript", "java"}
CATS = {  # label, art colour
    "security": ("SECURITY", t.A1),
    "devtool": ("DEV TOOL", t.A3),
    "product": ("PRODUCT", t.RINGS[2]),
    "learning": ("LEARNING", t.CLOCK[3]),
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wrap(text, width, lines):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = f"{cur} {w}".strip()
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: max(0, width - 1)].rstrip(" ,.;:-") + "…"
    return out


def ago(days):
    return "today" if days == 0 else "yesterday" if days == 1 else f"{days}d ago" if days < 60 else f"{days // 30}mo ago"


# ---------------- generative cover art ----------------
def art_security(rnd, col):
    cx, cy = 262 + rnd.uniform(-50, 50), 62 + rnd.uniform(-6, 6)
    o = []
    for r in (14, 30, 46, 62, 80):
        o.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="none" stroke="{col}" stroke-opacity=".28"/>')
    for a in range(0, 360, 45):
        x, y = cx + 80 * math.cos(math.radians(a)), cy + 80 * math.sin(math.radians(a))
        o.append(f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="{col}" stroke-opacity=".14"/>')
    o.append(f'<g transform="translate({cx:.0f},{cy:.0f})"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{rnd.uniform(5, 8):.1f}s" repeatCount="indefinite"/>'
             f'<path d="M0,0 L80,0 A80,80 0 0 0 {80 * math.cos(math.radians(-38)):.0f},{80 * math.sin(math.radians(-38)):.0f} Z" fill="{col}" fill-opacity=".22"/>'
             f'<line x1="0" y1="0" x2="80" y2="0" stroke="{col}" stroke-width="1.4"/></g></g>')
    for _ in range(6):
        a, r = rnd.uniform(0, 6.283), rnd.uniform(14, 74)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{t.A2}"><animate attributeName="opacity" values=".2;1;.2" dur="{rnd.uniform(2, 4):.1f}s" begin="-{rnd.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(o)


def art_devtool(rnd, col):
    pts = [(rnd.uniform(150, 388), rnd.uniform(16, ART - 16)) for _ in range(15)]
    edges = set()
    for i, p in enumerate(pts):
        near = sorted((j for j in range(len(pts)) if j != i), key=lambda j: (pts[j][0] - p[0]) ** 2 + (pts[j][1] - p[1]) ** 2)[:2]
        for j in near:
            edges.add((min(i, j), max(i, j)))
    o = [f'<line x1="{pts[i][0]:.0f}" y1="{pts[i][1]:.0f}" x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}" stroke="{col}" stroke-opacity=".34"/>' for i, j in edges]
    for n, (i, j) in enumerate(sorted(edges)[:7]):
        d = rnd.uniform(2.2, 4.5)
        o.append(f'<circle r="2" fill="{t.A2}" opacity="0"><animateMotion path="M{pts[i][0]:.0f},{pts[i][1]:.0f} L{pts[j][0]:.0f},{pts[j][1]:.0f}" dur="{d:.1f}s" begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.85;1" dur="{d:.1f}s" repeatCount="indefinite"/></circle>')
    for x, y in pts:
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([2.4, 3, 4])}" fill="{col}"/>')
    return "".join(o)


def art_product(rnd, col):
    o = []
    for k in range(3):
        x, y = 190 + k * 52 + rnd.uniform(-8, 8), 18 + k * 12 + rnd.uniform(-5, 5)
        rot = rnd.uniform(-9, 9)
        o.append(f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})"><rect width="116" height="76" rx="9" fill="{t.SURFACE}" stroke="{col}" stroke-opacity="{.35 + k * .2:.2f}"/>'
                 f'<rect x="10" y="10" width="{rnd.randint(34, 70)}" height="6" rx="3" fill="{col}" opacity=".8"/>'
                 + "".join(f'<rect x="10" y="{26 + n * 11}" width="{rnd.randint(50, 96)}" height="4" rx="2" fill="{t.TEXT3}" opacity=".45"/>' for n in range(3))
                 + f'<circle cx="100" cy="62" r="6" fill="{t.A3}" opacity=".9"/></g>')
    return "".join(o)


def art_learning(rnd, col):
    n, o, pts = 14, [], []
    for i in range(n):
        h = 14 + (ART - 46) * ((i + 1) / n) ** 1.2 * rnd.uniform(.72, 1)
        x = 168 + i * 16.5
        o.append(f'<rect x="{x:.0f}" y="{ART - 10 - h:.0f}" width="11" height="{h:.0f}" rx="3" fill="{col}" opacity="{.32 + .6 * i / n:.2f}"/>')
        pts.append((x + 5.5, ART - 10 - h))
    o.append('<polyline points="' + " ".join(f"{x:.0f},{y - 7:.0f}" for x, y in pts) + f'" fill="none" stroke="{t.A2}" stroke-width="1.6" stroke-linejoin="round" stroke-opacity=".9"/>')
    o.append(f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1] - 7:.0f}" r="3.4" fill="{t.A3}"><animate attributeName="r" values="3;6;3" dur="2.2s" repeatCount="indefinite"/></circle>')
    return "".join(o)


MOTIFS = {"security": art_security, "devtool": art_devtool, "product": art_product, "learning": art_learning}


def _ticker(text, col, y):
    """A mission log that scrolls forever under the scene (two copies, so the loop is seamless)."""
    msg = escape(f"› {text}")
    L = len(text) * 6.05 + 70
    dur = L / 36
    line = lambda x: f'<text x="{x:.0f}" y="{y + 16}" class="mono" font-size="10" fill="{t.TEXT2}">{msg}</text>'
    return (f'<rect y="{y}" width="{W}" height="{TICK}" fill="{t.CANVAS}"/>'
            f'<rect y="{y}" width="{W}" height="{TICK}" fill="{col}" fill-opacity=".07"/>'
            f'<g clip-path="url(#tick)"><g><animateTransform attributeName="transform" type="translate" from="0 0" to="-{L:.0f} 0" dur="{dur:.1f}s" repeatCount="indefinite"/>'
            f'{line(100)}{line(100 + L)}</g></g>'
            f'<circle cx="18" cy="{y + 12}" r="3.5" fill="{t.BEACON[0]}"><animate attributeName="opacity" values="1;.15;1" dur="1.2s" repeatCount="indefinite"/></circle>'
            f'<text x="28" y="{y + 16}" class="mono" font-size="9.5" font-weight="700" fill="{col}">LIVE LOG</text>'
            f'<rect x="90" y="{y + 5}" width="1" height="{TICK - 10}" fill="{t.HAIRLINE}"/>')


def _hud(col, idx):
    """HUD chrome over the art: corner brackets, scanlines and a light sheen."""
    b = 14
    corners = (f'M10 {10 + b} V10 H{10 + b}', f'M{W - 10 - b} 10 H{W - 10} V{10 + b}',
               f'M10 {ART - 10 - b} V{ART - 10} H{10 + b}', f'M{W - 10 - b} {ART - 10} H{W - 10} V{ART - 10 - b}')
    return (f'<rect width="{W}" height="{ART}" fill="url(#scan)"/>'
            f'<g transform="skewX(-18)"><rect x="-200" y="0" width="110" height="{ART}" fill="url(#sheen)">'
            f'<animate attributeName="x" values="-200;-200;{W + 140}" keyTimes="0;.72;1" dur="7s" begin="{idx * .7:.1f}s" repeatCount="indefinite"/></rect></g>'
            f'<g fill="none" stroke="{col}" stroke-width="1.6" stroke-opacity=".7">' + "".join(f'<path d="{d}"/>' for d in corners) + "</g>")


def _title(title, idx, y):
    """Project name with a short chromatic glitch every few seconds."""
    dur, beg = f"{7 + idx % 3}s", f"{idx * .45:.2f}s"
    def ghost(dx, col):
        return (f'<text x="{20 + dx}" y="{y}" font-size="18" font-weight="700" fill="{col}" opacity="0">{escape(title)}'
                f'<animate attributeName="opacity" values="0;0;.85;0;.85;0;0" keyTimes="0;.9;.905;.92;.925;.94;1" dur="{dur}" begin="{beg}" repeatCount="indefinite"/></text>')
    return (ghost(-2.5, t.BEACON[0]) + ghost(2.5, t.A2)
            + f'<text x="20" y="{y}" font-size="18" font-weight="700" fill="{t.TEXT}">{escape(title)}'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;2 0;-1.5 0;0 0;0 0" keyTimes="0;.9;.905;.92;.935;1" dur="{dur}" begin="{beg}" repeatCount="indefinite"/></text>')


def poster(cfg, r, now, idx=1):
    name = r["name"]
    cat = cfg.get("category", "product")
    label, col = CATS[cat]
    rnd = random.Random(zlib.crc32(name.encode()))
    blurb = cfg.get("blurb") or (r.get("description") or "No description yet.")
    days = max(0, (now - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days)
    lang = r["language"] or "misc"
    live = bool(r.get("homepage"))
    topics = [x for x in (r.get("topics") or []) if x not in SKIP_TOPICS][:3]
    title = name.rstrip("-_")
    top = ART + TICK
    per = 2 * (W + H - 4) - 16 * (8 - 2 * math.pi)  # perimeter of the rounded border
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(f"Mission {idx:02d}, {title}: {blurb}")}">',
         f"<title>{escape(title)}</title>",
         t.defs(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath><clipPath id="artc"><rect width="{W}" height="{ART}"/></clipPath>'
                f'<clipPath id="tick"><rect x="92" y="{ART}" width="{W - 92}" height="{TICK}"/></clipPath>'
                f'<linearGradient id="art" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t.RAISED}"/><stop offset="1" stop-color="{t.SURFACE}"/></linearGradient>'
                f'<radialGradient id="wash"><stop offset="0" stop-color="{col}" stop-opacity=".42"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
                '<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                '<stop offset=".5" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".25"/></pattern>'
                '<style>@keyframes boot{0%{opacity:0}8%{opacity:1}11%{opacity:.15}14%{opacity:1}18%{opacity:.35}22%{opacity:1}100%{opacity:1}}'
                '.boot{animation:boot 1.6s steps(1,end) both}'
                '@media (prefers-reduced-motion: reduce){.boot{animation:none}}</style>'),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="{t.SURFACE}"/>',
         f'<rect width="{W}" height="{ART}" fill="url(#art)"/>',
         f'<ellipse cx="{rnd.uniform(230, 340):.0f}" cy="{rnd.uniform(30, 70):.0f}" rx="170" ry="90" fill="url(#wash)"/>',
         # animated mission scene, boots in with a CRT flicker, kept inside the art window
         f'<g class="boot" style="animation-delay:{idx * .12:.2f}s" clip-path="url(#artc)">{scenes.scene(name) or MOTIFS[cat](rnd, col)}</g>',
         _hud(col, idx),
         _ticker(scenes.ticker(name) or blurb, col, ART),
         f'<rect y="{ART}" width="{W}" height="1" fill="{col}" fill-opacity=".55"/><rect y="{top}" width="{W}" height="1" fill="{t.HAIRLINE}"/>']
    # mission + category pill, destination pill (over the art)
    pill = f"M{idx:02d} · {label}"
    cw = 18 + 6.9 * len(pill)
    o.append(f'<rect x="16" y="16" width="{cw:.0f}" height="22" rx="11" fill="{t.SURFACE}" fill-opacity=".85" stroke="{col}" stroke-opacity=".6"/>'
             f'<text x="{16 + cw / 2:.0f}" y="31" class="label" text-anchor="middle" style="fill:{col}">{pill}</text>')
    dest = "LIVE &#8599;" if live else "REPO &#8599;"
    dc = t.GREEN if live else t.TEXT2
    o.append(f'<rect x="{W - 84}" y="16" width="68" height="22" rx="11" fill="{t.SURFACE}" fill-opacity=".85" stroke="{dc}" stroke-opacity=".6">'
             + ('<animate attributeName="stroke-opacity" values=".5;1;.5" dur="2s" repeatCount="indefinite"/>' if live else "") + "</rect>"
             f'<text x="{W - 50}" y="31" class="label" text-anchor="middle" style="fill:{dc}">{dest}</text>')
    # text
    o.append(_title(title, idx, top + 30))
    if live:  # a rubber stamp that slams onto shipped projects
        sx, sy = W - 70, top + 22
        o.append(f'<g transform="translate({sx},{sy}) rotate(-8)"><g opacity=".9">'
                 f'<animateTransform attributeName="transform" type="scale" values="2.4;.92;1;1" keyTimes="0;.06;.09;1" dur="8s" begin="{idx * .5:.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.9;.9;.9" keyTimes="0;.05;.06;1" dur="8s" begin="{idx * .5:.1f}s" repeatCount="indefinite"/>'
                 f'<rect x="-46" y="-12" width="92" height="24" rx="4" fill="none" stroke="{t.GREEN}" stroke-width="2"/>'
                 f'<rect x="-42" y="-8" width="84" height="16" rx="2" fill="none" stroke="{t.GREEN}" stroke-width=".8"/>'
                 f'<text y="4" class="mono" font-size="10.5" font-weight="700" fill="{t.GREEN}" text-anchor="middle" letter-spacing="2">SHIPPED</text></g></g>')
    for i, line in enumerate(wrap(blurb, 60, 3)):
        o.append(f'<text x="20" y="{top + 51 + i * 16}" font-size="12" fill="{t.TEXT2}">{escape(line)}</text>')
    # chips
    x = 20
    for tp in topics:
        w = 14 + 6.1 * len(tp)
        o.append(f'<rect x="{x:.0f}" y="{H - 54}" width="{w:.0f}" height="20" rx="10" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{x + w / 2:.0f}" y="{H - 40}" class="mono" font-size="10" fill="{t.TEXT3}" text-anchor="middle">{escape(tp)}</text>')
        x += w + 6
    # footer: language, stars, last push
    lc = t.lang_color(lang if lang in t.LANG else "Other")
    stars = r["stargazers_count"]
    o.append(f'<circle cx="26" cy="{H - 17}" r="4" fill="{lc}"/>'
             f'<text x="38" y="{H - 13}" font-size="11" fill="{t.TEXT2}">{escape(lang)}'
             f'<tspan fill="{t.TEXT3}">  &#183;  &#9733; {stars}  &#183;  pushed {ago(days)}</tspan></text>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    # a spark of light that keeps running around the card edge
    off = -idx * 137 % per
    o.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" '
             f'stroke-dasharray="80 {per - 80:.0f}" opacity=".9">'
             f'<animate attributeName="stroke-dashoffset" from="{off:.0f}" to="{off - per:.0f}" dur="9s" repeatCount="indefinite"/></rect>')
    o.append("</svg>")
    alt = (f"Mission {idx:02d}, {title}: a {label.lower()} project in {lang}. {blurb} "
           f"{'Opens the live demo.' if live else 'Opens the repository.'}")
    return "\n".join(o), alt, (r["homepage"] if live else r["html_url"])



def shelf(groups, names, path):
    """assets/shelf.svg: every other build as a game cartridge on a shelf, one shelf per group.
    Cartridges drop in on load, a selector hops between them, and live ones carry a green LED."""
    CW, CH, GAP, X0 = 98, 66, 10, 30
    rows = [(title, members) for title, members in groups if members]
    total = sum(len(m) for _, m in rows)
    per_row = 7
    lines = []
    for title, members in rows:
        for k in range(0, len(members), per_row):
            lines.append((title if k == 0 else "", members[k:k + per_row]))
    RH = CH + 46
    Hs = 64 + len(lines) * RH + 12
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W * 2 + 20} {Hs}" width="{W * 2 + 20}" height="{Hs}" role="img" '
         f'aria-label="{escape(f"More builds: {total} more projects shown as game cartridges on shelves, grouped as " + ", ".join(t_ for t_, _ in rows) + ".")}">',
         "<title>More builds</title>",
         t.defs(f'<clipPath id="card"><rect width="{W * 2 + 20}" height="{Hs}" rx="16"/></clipPath>'
                '<linearGradient id="shine2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".4" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                f'<linearGradient id="plank" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.HAIRLINE}"/><stop offset="1" stop-color="{t.CANVAS}"/></linearGradient>'),
         '<g clip-path="url(#card)">', f'<rect width="{W * 2 + 20}" height="{Hs}" fill="{t.SURFACE}"/>',
         f'<text x="{X0}" y="38" class="mono" font-size="12" font-weight="700" letter-spacing="2" fill="{t.TEXT}">GAME LIBRARY</text>'
         f'<text x="{X0 + 128}" y="38" class="mono" font-size="11" fill="{t.TEXT3}">{total} more builds · colour = language · <tspan fill="{t.GREEN}">●</tspan> = live demo</text>']
    spots, k = [], 0
    for li, (title, members) in enumerate(lines):
        y0 = 64 + li * RH
        if title:
            o.append(f'<text x="{X0}" y="{y0 + 12}" class="label" style="fill:{t.A3}">{escape(title.upper())}</text>')
        cy = y0 + 22
        for j, r in enumerate(members):
            x = X0 + j * (CW + GAP)
            lang = r["language"] or "Other"
            lc = t.lang_color(lang if lang in t.LANG else "Other")
            name = names.get(r["name"]) or r["name"].strip("-_")
            name = name if len(name) <= 14 else name[:13] + "…"
            live = bool(r.get("homepage"))
            d = .15 + k * .06
            o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".3s" begin="{d:.2f}s" fill="freeze"/>'
                     f'<animateTransform attributeName="transform" type="translate" values="0 -26;0 3;0 0" keyTimes="0;.7;1" dur=".5s" begin="{d:.2f}s" fill="freeze"/>'
                     f'<path d="M{x + 6} {cy} H{x + CW - 6} Q{x + CW} {cy} {x + CW} {cy + 6} V{cy + CH} H{x} V{cy + 6} Q{x} {cy} {x + 6} {cy} Z" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                     f'<rect x="{x + CW / 2 - 14}" y="{cy}" width="28" height="5" rx="2" fill="{t.CANVAS}"/>'
                     f'<rect x="{x + 7}" y="{cy + 10}" width="{CW - 14}" height="36" rx="4" fill="{lc}"/>'
                     f'<rect x="{x + 7}" y="{cy + 10}" width="{CW - 14}" height="36" rx="4" fill="url(#shine2)"/>'
                     f'<rect x="{x + 11}" y="{cy + 14}" width="{CW - 22}" height="15" rx="2" fill="{t.CANVAS}" fill-opacity=".78"/>'
                     f'<text x="{x + CW / 2}" y="{cy + 25}" class="mono" font-size="8.6" font-weight="700" fill="{t.TEXT}" text-anchor="middle">{escape(name)}</text>'
                     f'<text x="{x + CW / 2}" y="{cy + 41}" class="mono" font-size="8" font-weight="700" fill="{t.CANVAS}" text-anchor="middle">{escape(lang.upper()[:12])}</text>'
                     + "".join(f'<rect x="{x + 12 + g * 7}" y="{cy + CH - 12}" width="4" height="8" rx="1" fill="{t.HAIRLINE}"/>' for g in range(4))
                     + (f'<circle cx="{x + CW - 12}" cy="{cy + CH - 8}" r="3" fill="{t.GREEN}"><animate attributeName="opacity" values="1;.3;1" dur="1.6s" begin="{k * .1:.1f}s" repeatCount="indefinite"/></circle>' if live else "")
                     + f'<title>{escape(r["name"])}: {escape((r.get("description") or "")[:120])}</title></g>')
            spots.append((x, cy, name))
            k += 1
        o.append(f'<rect x="{X0 - 12}" y="{cy + CH}" width="{(W * 2 + 20) - 2 * X0 + 24}" height="8" rx="2" fill="url(#plank)"/>'
                 f'<rect x="{X0 - 12}" y="{cy + CH}" width="{(W * 2 + 20) - 2 * X0 + 24}" height="1" fill="{t.A1}" opacity=".35"/>')
    # selector: hops from cartridge to cartridge, like browsing a library
    if spots:
        hop = 1.1
        dur = hop * len(spots)
        xs = ";".join(f"{x - 5} {y - 5}" for x, y, _ in spots)
        kt = ";".join(f"{i / len(spots):.4f}" for i in range(len(spots)))
        o.append(f'<g><animateTransform attributeName="transform" type="translate" values="{xs}" keyTimes="{kt}" calcMode="discrete" dur="{dur:.1f}s" begin="{.4 + k * .06:.1f}s" repeatCount="indefinite"/>'
                 f'<rect width="{CW + 10}" height="{CH + 10}" rx="9" fill="none" stroke="{t.A3}" stroke-width="2">'
                 f'<animate attributeName="stroke-opacity" values="1;.4;1" dur=".55s" repeatCount="indefinite"/></rect>'
                 f'<path d="M{CW / 2 - 4} -8 L{CW / 2 + 5} -8 L{CW / 2 + .5} -2 Z" fill="{t.A3}"/></g>')
    o.append(f'<text x="{W * 2 + 20 - X0}" y="38" class="mono" font-size="11" font-weight="700" fill="{t.A3}" text-anchor="end">▶ open the list below for links'
             '<animate attributeName="opacity" values="1;.4;1" dur="1.6s" repeatCount="indefinite"/></text>')
    o += ["</g>", t.card_border(W * 2 + 20, Hs, 16), "</svg>"]
    open(path, "w", encoding="utf-8").write("".join(o))


def main():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    repos = {r["name"]: r for r in common.repos(USER)}
    now = datetime.now(timezone.utc)
    cells, used = [], set()
    for item in cfg["featured"]:
        r = repos.get(item["repo"])
        if not r:
            print("skip (repo not found):", item["repo"])
            continue
        svg, alt, href = poster(item, r, now, len(cells) + 1)
        fn = f"p-{slug(r['name'])}.svg"
        open(os.path.join(ASSETS, fn), "w", encoding="utf-8").write(svg)
        used.add(r["name"])
        cells.append(f'<a href="{escape(href, {chr(34): "&quot;"})}"><img src="assets/{fn}" alt="{escape(alt, {chr(34): "&quot;"})}" width="49%"/></a>')
    # "more builds": everything else with a description, grouped; names, wording and hidden repos are curated in data/projects.json
    mc = cfg.get("more", {})
    ex = set(cfg.get("exclude_more", [])) | set(mc.get("hide", []))
    exp = tuple(cfg.get("exclude_prefix_more", []))
    names, descs = mc.get("names", {}), mc.get("desc", {})
    more = [r for r in sorted(repos.values(), key=lambda r: r["pushed_at"], reverse=True)
            if r["name"] not in used and r["name"] not in ex and not r["name"].startswith(exp) and (r.get("description") or "").strip()][:30]
    by_name = {r["name"]: r for r in more}
    groups = [(g["title"], list(g["repos"])) for g in mc.get("groups", [])]
    placed = {n for _, rs in groups for n in rs}
    rest = [r["name"] for r in more if r["name"] not in placed]
    if rest:  # new repos never vanish: they land in a catch-all group until they are curated
        groups.append(("More", rest))

    def row(r):
        d = re.sub(r"\s+", " ", descs.get(r["name"]) or r["description"]).replace("|", "/").strip()
        d = d[:1].upper() + d[1:]
        d = d if len(d) <= 110 else d[:110].rsplit(" ", 1)[0].rstrip(",.;:-") + "…"
        label = names.get(r["name"]) or r["name"].strip("-_")
        link = f"[**{label}**]({r['html_url']})" + (f" · [live]({r['homepage']})" if r.get("homepage") else "")
        return f"| {link} | `{r['language'] or 'misc'}` | {d} |"

    sections, shown, shelves = [], 0, []
    for title, rs in groups:
        members = [by_name[n] for n in rs if n in by_name]
        shelves.append((title, members))
        if members:
            shown += len(members)
            sections.append(f"**{title}**\n\n| Build | Stack | What it is |\n|:--|:--|:--|\n" + "\n".join(row(r) for r in members))
    caption = ("<sub>Nine missions, each acting out what the project does, with its own live log. Tap a card to open the live demo or the repository; "
               "language, stars and last push update automatically.</sub>")
    shelf(shelves, names, os.path.join(ASSETS, "shelf.svg"))
    block = ('<div align="center">\n\n' + " ".join(cells) + f"\n\n{caption}\n\n"
             f'<img src="assets/shelf.svg" alt="More builds: {shown} more projects as game cartridges on shelves, coloured by language, with a light on the ones that have a live demo." width="100%"/>\n\n</div>\n\n'
             f"<details>\n<summary><b>Open the game library: {shown} more builds, with links</b></summary>\n\n" + "\n\n".join(sections) + "\n\n</details>")
    text = open(README, encoding="utf-8").read()
    a, b = text.index(START) + len(START), text.index(END)
    new = text[:a] + "\n" + block + "\n" + text[b:]
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
    print(f"posters: {len(cells)} featured, {shown} in 'more builds' across {len(sections)} groups")


if __name__ == "__main__":
    main()
