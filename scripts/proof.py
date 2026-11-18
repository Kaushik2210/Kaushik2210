#!/usr/bin/env python3
"""assets/proof.svg: the proof strip, five live instruments under the hero.

Each number gets an instrument that is drawn from the real data behind it:
  live sites      a radar, one blip per deployed site, lit as the sweep passes
  repositories    a server rack, one LED per repo in that repo's language colour
  commits         this year's weekly activity, drawn in as a trace
  best streak     a ring of days that light up one after another
  years building  tree rings, one per year on GitHub
Every number rolls up like an odometer. All counts come from the GitHub API. Pure SMIL.
"""
import math
import random
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/proof.svg"
W, H = 830, 196
IY = 64                     # instrument centre line
DH, DW = 34, 19             # odometer digit cell


def odometer(text, cx, y, delay, col):
    """Digits roll up from 0 and settle on the real value."""
    w = DW * len(text)
    x0 = cx - w / 2
    o = []
    for i, ch in enumerate(text):
        x = x0 + i * DW
        if not ch.isdigit():
            o.append(f'<text x="{x + DW / 2:.1f}" y="{y}" class="mono" font-size="30" font-weight="700" fill="{col}" text-anchor="middle">{escape(ch)}</text>')
            continue
        d = int(ch)
        laps = 10 + d                                   # spin a full lap first, so every digit visibly rolls
        strip = "".join(f'<text x="{x + DW / 2:.1f}" y="{y + k * DH}" class="mono" font-size="30" font-weight="700" fill="{col}" text-anchor="middle">{k % 10}</text>'
                        for k in range(laps + 1))
        dur = 1.4 + i * .25
        o.append(f'<g clip-path="url(#od{i}_{int(cx)})"><g transform="translate(0 0)">'
                 f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {-laps * DH}" dur="{dur:.2f}s" begin="{delay:.2f}s" '
                 f'fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".25 .1 .1 1"/>{strip}</g></g>')
        o.append(f'<clipPath id="od{i}_{int(cx)}"><rect x="{x:.1f}" y="{y - DH + 8}" width="{DW}" height="{DH}"/></clipPath>')
    return "".join(o)


def radar(cx, cy, n, rnd):
    r, sweep = 34, 4.0
    o = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t.CANVAS}" stroke="{t.GREEN}" stroke-opacity=".5"/>']
    for k in (.33, .66):
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r * k:.0f}" fill="none" stroke="{t.GREEN}" stroke-opacity=".2"/>')
    o.append(f'<line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{t.GREEN}" stroke-opacity=".15"/>'
             f'<line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy + r}" stroke="{t.GREEN}" stroke-opacity=".15"/>')
    a = math.radians(-40)
    o.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{sweep}s" repeatCount="indefinite"/>'
             f'<path d="M{cx},{cy} L{cx + r},{cy} A{r},{r} 0 0 0 {cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f} Z" fill="{t.GREEN}" fill-opacity=".22"/>'
             f'<line x1="{cx}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{t.GREEN}" stroke-width="1.5"/></g>')
    for k in range(min(n, 40)):  # one blip per live site; it flares when the sweep line passes it
        ang = rnd.uniform(0, 360)
        rad = rnd.uniform(6, r - 5)
        x, y = cx + rad * math.cos(math.radians(ang)), cy + rad * math.sin(math.radians(ang))
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="{t.GREEN}" opacity=".25">'
                 f'<animate attributeName="opacity" values="1;.2;.2" keyTimes="0;.6;1" dur="{sweep}s" begin="{ang / 360 * sweep:.2f}s" repeatCount="indefinite"/></circle>')
    return "".join(o)


def rack(cx, cy, repos, rnd):
    n = len(repos)
    cols = 15
    rows = math.ceil(n / cols)
    s, g = 6, 2.2
    w, h = cols * (s + g) - g, rows * (s + g) - g
    x0, y0 = cx - w / 2, cy - h / 2
    o = [f'<rect x="{x0 - 7:.1f}" y="{y0 - 7:.1f}" width="{w + 14:.1f}" height="{h + 14:.1f}" rx="5" fill="{t.CANVAS}" stroke="{t.HAIRLINE}"/>']
    for i, r in enumerate(sorted(repos, key=lambda r: r["created_at"])):
        row, col = divmod(i, cols)
        lang = r["language"] or "Other"
        c = t.lang_color(lang if lang in t.LANG else "Other")
        o.append(f'<rect x="{x0 + col * (s + g):.1f}" y="{y0 + row * (s + g):.1f}" width="{s}" height="{s}" rx="1.4" fill="{c}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;1" dur=".15s" begin="{.4 + i * .025:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="fill-opacity" values="1;.3;1" dur="{rnd.uniform(1.5, 5):.1f}s" begin="{rnd.uniform(2, 6):.1f}s" repeatCount="indefinite"/></rect>')
    return "".join(o)


def trace(cx, cy, ds):
    weeks = [sum(c for _, c in ds[i:i + 7]) for i in range(max(0, len(ds) - 364), len(ds), 7)]
    hi = max(weeks) or 1
    w, h = 124, 52
    x0, y0 = cx - w / 2, cy + h / 2
    pts = [(x0 + i * w / max(1, len(weeks) - 1), y0 - h * v / hi) for i, v in enumerate(weeks)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{pts[-1][0]:.1f},{y0} L{pts[0][0]:.1f},{y0} Z"
    peak = max(range(len(weeks)), key=lambda i: weeks[i])
    return (f'<line x1="{x0}" y1="{y0}" x2="{x0 + w}" y2="{y0}" stroke="{t.HAIRLINE}"/>'
            f'<path d="{area}" fill="url(#tr)" opacity="0"><animate attributeName="opacity" values="0;1" dur=".8s" begin="2s" fill="freeze"/></path>'
            f'<path d="{line}" fill="none" stroke="{t.A2}" stroke-width="1.6" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">'
            f'<animate attributeName="stroke-dashoffset" values="1;0" dur="2s" begin=".5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".3 0 .2 1"/></path>'
            f'<circle cx="{pts[peak][0]:.1f}" cy="{pts[peak][1]:.1f}" r="3" fill="{t.A3}" opacity="0"><animate attributeName="opacity" values="0;1" dur=".3s" begin="2.4s" fill="freeze"/>'
            f'<animate attributeName="r" values="2.5;5;2.5" dur="1.6s" begin="2.4s" repeatCount="indefinite"/></circle>'
            f'<text x="{x0}" y="{y0 - h - 4}" class="mono" font-size="8.5" fill="{t.TEXT3}">weekly activity</text>')


def streak_ring(cx, cy, n):
    r, cyc = 32, 9.0
    o = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t.HAIRLINE}" stroke-dasharray="1 3"/>']
    n = max(1, n)
    for i in range(n):
        a = math.radians(-90 + 360 * i / n)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        b = .05 + .55 * i / n
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="{t.A3}" opacity=".12">'
                 f'<animate attributeName="opacity" values=".12;.12;1;1;.12" keyTimes="0;{b:.3f};{b + .01:.3f};.93;1" dur="{cyc}s" repeatCount="indefinite"/></circle>')
    o.append(f'<path d="M{cx} {cy - 12} C{cx + 9} {cy - 3} {cx + 7} {cy + 8} {cx} {cy + 10} C{cx - 7} {cy + 8} {cx - 9} {cy - 3} {cx} {cy - 12} Z" fill="{t.A3}" opacity=".85">'
             f'<animate attributeName="opacity" values=".85;.6;.95;.7;.85" dur=".8s" repeatCount="indefinite"/></path>'
             f'<path d="M{cx} {cy - 2} C{cx + 4} {cy + 2} {cx + 3} {cy + 8} {cx} {cy + 9} C{cx - 3} {cy + 8} {cx - 4} {cy + 2} {cx} {cy - 2} Z" fill="{t.BEACON[1]}"/>')
    return "".join(o)


def tree_rings(cx, cy, years, rnd):
    o = [f'<circle cx="{cx}" cy="{cy}" r="3" fill="{t.A1}"/>']
    full = int(years)
    for k in range(full + (1 if years % 1 > .05 else 0)):
        r = 7 + k * 5.4
        part = 1 if k < full else years % 1
        wob = "".join(f"{cx + (r + rnd.uniform(-.8, .8)) * math.cos(math.radians(a)):.1f},{cy + (r + rnd.uniform(-.8, .8)) * math.sin(math.radians(a)):.1f} "
                      for a in range(-90, int(-90 + 360 * part) + 1, 12))
        d = .6 + k * .35
        o.append(f'<polyline points="{wob}" fill="none" stroke="{t.A1 if k % 2 else t.A2}" stroke-width="1.6" stroke-linecap="round" '
                 f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">'
                 f'<animate attributeName="stroke-dashoffset" values="1;0" dur=".5s" begin="{d:.2f}s" fill="freeze"/></polyline>')
    o.append(f'<circle cx="{cx}" cy="{cy - 7 - full * 5.4}" r="2.4" fill="{t.A3}" opacity="0">'
             f'<animate attributeName="opacity" values="0;1;.3;1" dur="1.8s" begin="{.8 + full * .35:.2f}s" repeatCount="indefinite"/></circle>')
    return "".join(o)


def main():
    u = common.user_graph(USER)
    rp = common.repos(USER)
    ds = common.days(u)
    cc = u["contributionsCollection"]
    _, longest = common.streaks(ds)
    live = sum(1 for r in rp if (r.get("homepage") or "").strip())
    years = (datetime.now(timezone.utc) - datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))).days / 365.25
    rnd = random.Random(5)
    cw = (W - 32) / 5
    cxs = [16 + i * cw + cw / 2 for i in range(5)]
    tiles = [
        (f"{live}", "LIVE SITES", "deployed and running", t.GREEN, radar(cxs[0], IY, live, rnd)),
        (f"{len(rp)}", "REPOSITORIES", "one light per repo", t.A1, rack(cxs[1], IY, rp, rnd)),
        (f"{cc['totalCommitContributions']:,}", "COMMITS THIS YEAR", "last 12 months", t.A2, trace(cxs[2], IY, ds)),
        (f"{longest}", "BEST STREAK", "days in a row", t.A3, streak_ring(cxs[3], IY, longest)),
        (f"{years:.1f}", "YEARS BUILDING", "one ring per year", t.A1, tree_rings(cxs[4], IY, years, rnd)),
    ]
    alt = "Proof strip: " + "; ".join(f"{v} {l.lower()}" for v, l, *_ in tiles) + "."
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
         f"<title>{escape(USER)}: proof</title>",
         t.defs(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
                f'<linearGradient id="tr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.A2}" stop-opacity=".35"/><stop offset="1" stop-color="{t.A2}" stop-opacity="0"/></linearGradient>'
                '<pattern id="grid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0 H0 V16" fill="none" stroke="#fff" stroke-opacity=".025"/></pattern>'),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="{t.SURFACE}"/><rect width="{W}" height="{H}" fill="url(#grid)"/>']
    for i, (val, lab, sub, col, inst) in enumerate(tiles):
        cx = cxs[i]
        o.append(inst)
        o.append(odometer(val, cx, 140, .3 + i * .15, t.TEXT))
        o.append(f'<text x="{cx:.0f}" y="{H - 34}" class="label" text-anchor="middle" style="fill:{col};font-size:10px">{lab}</text>'
                 f'<text x="{cx:.0f}" y="{H - 18}" font-size="10.5" text-anchor="middle" fill="{t.TEXT3}">{sub}</text>')
        if i:
            o.append(f'<line x1="{16 + i * cw:.0f}" y1="26" x2="{16 + i * cw:.0f}" y2="{H - 26}" stroke="{t.HAIRLINE}" stroke-dasharray="2 4"/>')
    o.append(f'<rect x="0" y="0" width="{W}" height="3" fill="url(#aurora)"/>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: " + ", ".join(f"{v} {l.lower()}" for v, l, *_ in tiles))


if __name__ == "__main__":
    main()
