#!/usr/bin/env python3
"""assets/galaxy.svg: one year of contributions as a phyllotaxis (golden-angle) galaxy.

Each day is a star. The newest day sits at the core, the oldest at the rim, so
your recent history burns brightest at the centre. Star size and colour follow
the contribution count. The galaxy rotates slowly; busy stars twinkle.
"""
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/galaxy.svg"
W, H, CX, CY, R = 830, 480, 222, 240, 192
GOLDEN = math.radians(137.50776)
STARS_DB = os.environ.get("STARS_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stars", "visitors.json")
VISITOR_COLORS = {"cyan": "#38bdf8", "pink": "#ff4fa3", "gold": "#ffc247", "green": "#34d399", "violet": "#9d7bff"}


def load_visitors():
    try:
        with open(STARS_DB, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def h01(s, salt):
    return int(hashlib.sha1(f"{salt}:{s}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def star_points(cx, cy, ro=8.0, ri=3.4):
    pts = []
    for k in range(10):
        r = ro if k % 2 == 0 else ri
        a = -math.pi / 2 + k * math.pi / 5
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return " ".join(pts)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def color(c, mx):
    if c == 0:
        return "#3a3270"
    t = min(1.0, math.log1p(c) / math.log1p(max(mx, 2)))
    stops = [(98, 82, 235), (176, 96, 240), (255, 100, 185), (255, 165, 85), (255, 244, 214)]
    k = t * (len(stops) - 1)
    i = min(int(k), len(stops) - 2)
    return "#%02x%02x%02x" % lerp(stops[i], stops[i + 1], k - i)


def main():
    u = common.user_graph(USER)
    ds = common.days(u)
    n = len(ds)
    cur, longest = common.streaks(ds)
    mx = max(c for _, c in ds)
    best = max(range(n), key=lambda i: ds[i][1])
    total = u["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    active = sum(1 for _, c in ds if c)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Contribution galaxy: each star is one day of commits">',
         f"<title>CONTRIBUTION GALAXY // {escape(USER)}</title>"]
    o.append(f"""<defs>
<linearGradient id="bdr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9d7bff" stop-opacity=".55"/><stop offset=".5" stop-color="#ff4fa3" stop-opacity=".28"/><stop offset="1" stop-color="#ff9a3c" stop-opacity=".55"/></linearGradient>
<radialGradient id="core"><stop offset="0" stop-color="#fff6c0" stop-opacity=".95"/><stop offset=".25" stop-color="#ffcf4a" stop-opacity=".45"/><stop offset="1" stop-color="#ffcf4a" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#6b3cff" stop-opacity=".22"/><stop offset=".6" stop-color="#8b3cff" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<filter id="g" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>text{{font-family:system-ui,-apple-system,'SF Pro Text','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif}}</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="#07050f" stroke="url(#bdr)" stroke-width="1.2"/>""")
    for i in range(110):  # deterministic background stars
        x, y = (i * 7919) % W, (i * 104729) % H
        o.append(f'<circle cx="{x}" cy="{y}" r="{0.4 + (i % 3) * 0.3:.1f}" fill="#d8c8ff" opacity="{0.15 + (i % 5) * 0.07:.2f}"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R+30}" fill="url(#halo)"/>')

    for d, lab in ((90, "3 mo"), (180, "6 mo"), (270, "9 mo"), (n - 1, "1 yr")):
        r = R * math.sqrt(d / (n - 1))
        o.append(f'<circle cx="{CX}" cy="{CY}" r="{r:.1f}" fill="none" stroke="#3a2f6e" stroke-opacity=".5" stroke-dasharray="2 6"/>')
        o.append(f'<text x="{CX}" y="{CY-r-3:.1f}" font-size="10" fill="#948ac0" fill-opacity=".8" text-anchor="middle">{lab}</text>')

    o.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" to="360 {CX} {CY}" dur="240s" repeatCount="indefinite"/>')
    for i, (date, c) in enumerate(ds):
        age = n - 1 - i  # 0 = today
        r = R * math.sqrt(age / (n - 1))
        th = age * GOLDEN
        x, y = CX + r * math.cos(th), CY + r * math.sin(th)
        rad = 1.1 if c == 0 else 2.0 + 3.6 * min(1.0, math.log1p(c) / math.log1p(max(mx, 2)))
        op = 0.35 if c == 0 else 0.95
        twinkle = ""
        if c >= 3:
            twinkle = (f'<animate attributeName="opacity" values="{op};.35;{op}" dur="{2.5 + (i % 7) * .4:.1f}s" '
                       f'begin="-{(i % 11) * .3:.1f}s" repeatCount="indefinite"/>')
        flt = ' filter="url(#g)"' if c >= 2 else ""
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{color(c, mx)}" opacity="{op}"{flt}>{twinkle}</circle>')
        if i == best:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="none" stroke="#ffc247" stroke-width="1">'
                     f'<animate attributeName="r" values="6;16;6" dur="3s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".9;0;.9" dur="3s" repeatCount="indefinite"/></circle>')
    visitors = load_visitors()
    for v in visitors[-60:]:  # named visitor stars live in the same rotating sky
        rr = R * (0.30 + 0.66 * h01(v["login"], "r"))
        th = 2 * math.pi * h01(v["login"], "a")
        x, y = CX + rr * math.cos(th), CY + rr * math.sin(th)
        col = VISITOR_COLORS.get(v.get("color"), "#38bdf8")
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="none" stroke="{col}" stroke-width="1">'
                 f'<animate attributeName="r" values="6;18;6" dur="{3 + 2 * h01(v["login"], "d"):.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values=".8;0;.8" dur="{3 + 2 * h01(v["login"], "d"):.1f}s" repeatCount="indefinite"/></circle>')
        o.append(f'<polygon points="{star_points(x, y)}" fill="{col}" filter="url(#g)"/>')
    o.append("</g>")
    o.append(f'<circle cx="{CX}" cy="{CY}" r="38" fill="url(#core)"/>')
    o.append(f'<text x="{CX}" y="{CY+4}" font-size="9" fill="#07050f" text-anchor="middle" font-weight="bold">NOW</text>')

    px = 452
    bd = ds[best]
    o.append(f'<text x="{px}" y="52" font-size="20" fill="#f3efff" font-weight="700">Contribution galaxy</text>')
    o.append(f'<text x="{px}" y="70" font-size="12" fill="#948ac0">1 star per day · {datetime.now(timezone.utc):%Y-%m-%d}</text>')
    o.append(f'<line x1="{px}" y1="84" x2="{W-30}" y2="84" stroke="#2c2455"/>')
    rows = [("CONTRIBUTIONS", f"{total}"), ("ACTIVE DAYS", f"{active} / {n}"),
            ("CURRENT STREAK", f"{cur} days"), ("LONGEST STREAK", f"{longest} days"),
            ("BRIGHTEST STAR", f"{bd[1]} on {bd[0]}")]
    for i, (k, v) in enumerate(rows):
        y = 110 + i * 26
        o.append(f'<text x="{px}" y="{y}" font-size="13" fill="#948ac0">{k}</text>')
        o.append(f'<text x="{px+158}" y="{y}" font-size="14" fill="#f3efff">{escape(v)}</text>')
    o.append(f'<line x1="{px}" y1="236" x2="{W-30}" y2="236" stroke="#2c2455"/>')
    o.append(f'<text x="{px}" y="258" font-size="12" fill="#ffc247">&#9733; VISITOR STARS <tspan fill="#948ac0">({len(visitors)})</tspan></text>')
    if visitors:
        for i, v in enumerate(reversed(visitors[-5:])):
            col = VISITOR_COLORS.get(v.get("color"), "#38bdf8")
            y = 284 + i * 22
            o.append(f'<polygon points="{star_points(px + 6, y - 4, 6, 2.6)}" fill="{col}"/>')
            o.append(f'<text x="{px + 20}" y="{y}" font-size="12" fill="#f3efff">@{escape(v["login"][:18])} '
                     f'<tspan fill="#948ac0">{escape(v["msg"][:26])}</tspan></text>')
    else:
        for i, t in enumerate(["the sky is empty. be the first.", "click this galaxy to add your own star,", "it stays here and keeps orbiting."]):
            o.append(f'<text x="{px}" y="{286 + i * 22}" font-size="12" fill="#f3efff">&#8250; {t}</text>')
    o.append(f'<text x="{px}" y="{H-66}" font-size="11" fill="#948ac0">centre = today · rim = a year ago · warmer = busier</text>')
    o.append(f'<text x="{px}" y="{H-42}" font-size="11" fill="#948ac0">quiet</text>')
    for i in range(8):
        o.append(f'<circle cx="{px+42+i*18}" cy="{H-45}" r="{2+i*0.6:.1f}" fill="{color(round(mx*(i/7)**2), mx)}"/>')
    o.append(f'<text x="{px+196}" y="{H-42}" font-size="11" fill="#948ac0">busy</text>')
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: {n} stars + {len(visitors)} visitor stars, streak {cur}/{longest}")


if __name__ == "__main__":
    main()
