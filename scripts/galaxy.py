#!/usr/bin/env python3
"""assets/galaxy.svg: one year of contributions as a phyllotaxis (golden-angle) galaxy.

Each day is a star. The newest day sits at the core, the oldest at the rim, so
your recent history burns brightest at the centre. Star size and colour follow
the contribution count. The galaxy rotates slowly; busy stars twinkle.
"""
import math
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/galaxy.svg"
W, H, CX, CY, R = 940, 470, 250, 235, 205
GOLDEN = math.radians(137.50776)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def color(c, mx):
    if c == 0:
        return "#2a3f5f"
    t = min(1.0, math.log1p(c) / math.log1p(max(mx, 2)))
    stops = [(60, 120, 255), (120, 200, 255), (255, 255, 255), (255, 235, 120)]
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
<radialGradient id="core"><stop offset="0" stop-color="#fff6c0" stop-opacity=".95"/><stop offset=".25" stop-color="#ffcf4a" stop-opacity=".45"/><stop offset="1" stop-color="#ffcf4a" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#3a63ff" stop-opacity=".22"/><stop offset=".6" stop-color="#6a3aff" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<filter id="g" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>text{{font-family:'Fira Code','Cascadia Code',Consolas,monospace}}</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="#05060f" stroke="#1b2147"/>""")
    for i in range(110):  # deterministic background stars
        x, y = (i * 7919) % W, (i * 104729) % H
        o.append(f'<circle cx="{x}" cy="{y}" r="{0.4 + (i % 3) * 0.3:.1f}" fill="#9fb4ff" opacity="{0.15 + (i % 5) * 0.07:.2f}"/>')
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R+30}" fill="url(#halo)"/>')

    for d, lab in ((90, "3 mo"), (180, "6 mo"), (270, "9 mo"), (n - 1, "1 yr")):
        r = R * math.sqrt(d / (n - 1))
        o.append(f'<circle cx="{CX}" cy="{CY}" r="{r:.1f}" fill="none" stroke="#2c3a78" stroke-opacity=".5" stroke-dasharray="2 6"/>')
        o.append(f'<text x="{CX+r+3:.1f}" y="{CY-3}" font-size="8" fill="#6f84d6" fill-opacity=".7">{lab}</text>')

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
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="none" stroke="#ffeb78" stroke-width="1">'
                     f'<animate attributeName="r" values="6;16;6" dur="3s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".9;0;.9" dur="3s" repeatCount="indefinite"/></circle>')
    o.append("</g>")
    o.append(f'<circle cx="{CX}" cy="{CY}" r="38" fill="url(#core)"/>')
    o.append(f'<text x="{CX}" y="{CY+4}" font-size="9" fill="#05060f" text-anchor="middle" font-weight="bold">NOW</text>')

    px = 520
    bd = ds[best]
    o.append(f'<text x="{px}" y="52" font-size="16" fill="#ffeb78" font-weight="bold">CONTRIBUTION GALAXY</text>')
    o.append(f'<text x="{px}" y="70" font-size="10" fill="#7d8590">{n} days · 1 star per day · {datetime.now(timezone.utc):%Y-%m-%d} UTC</text>')
    o.append(f'<line x1="{px}" y1="84" x2="{W-30}" y2="84" stroke="#1b2147"/>')
    rows = [("CONTRIBUTIONS", f"{total}"), ("ACTIVE DAYS", f"{active} / {n}"),
            ("CURRENT STREAK", f"{cur} days"), ("LONGEST STREAK", f"{longest} days"),
            ("BRIGHTEST STAR", f"{bd[1]} on {bd[0]}")]
    for i, (k, v) in enumerate(rows):
        y = 110 + i * 26
        o.append(f'<text x="{px}" y="{y}" font-size="11" fill="#7d8590">{k}</text>')
        o.append(f'<text x="{px+150}" y="{y}" font-size="12" fill="#e6edf3">{escape(v)}</text>')
    o.append(f'<line x1="{px}" y1="252" x2="{W-30}" y2="252" stroke="#1b2147"/>')
    o.append(f'<text x="{px}" y="274" font-size="10" fill="#9fb4ff">HOW TO READ</text>')
    for i, t in enumerate(["centre = today, rim = a year ago",
                           "bigger + warmer star = more commits that day",
                           "dim dust = quiet day (still counts as a day)",
                           "pulsing ring = your single busiest day"]):
        o.append(f'<text x="{px}" y="{296 + i * 20}" font-size="11" fill="#c9d1d9">&#8250; {t}</text>')
    o.append(f'<text x="{px}" y="{H-42}" font-size="9" fill="#7d8590">quiet</text>')
    for i in range(8):
        o.append(f'<circle cx="{px+42+i*18}" cy="{H-45}" r="{2+i*0.6:.1f}" fill="{color(round(mx*(i/7)**2), mx)}"/>')
    o.append(f'<text x="{px+196}" y="{H-42}" font-size="9" fill="#7d8590">busy</text>')
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: {n} stars, streak {cur}/{longest}, best {bd}")


if __name__ == "__main__":
    main()
