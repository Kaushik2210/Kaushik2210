#!/usr/bin/env python3
"""assets/launch.svg: the launch log, drawn as rockets leaving a planet.

Every project I started in the last 12 months lifts off from the planet's surface.
  where it launches = when I created it (left = a year ago, right = today)
  how high it flies = how long I kept building it (created -> last push)
  green satellite   = reached orbit with a live demo (repo has a homepage)
  gold, drifting    = still under power (pushed in the last 14 days)
  grey              = parked
On load the rockets fly in launch order; the newest one keeps relaunching.
"""
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/launch.svg"
W, H = 830, 420
CX, CY, R = W / 2, 1170, 860          # the planet: a huge circle whose top is the horizon
SPAN = 21                              # degrees either side of the top used for the year
ALT = 200                              # max altitude in px


def _ctf_desc():
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ctf", "desc.hex")
    return open(f, encoding="utf-8").read().strip() if os.path.exists(f) else ""


def when(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def polar(theta, r):
    a = math.radians(theta)
    return CX + r * math.sin(a), CY - r * math.cos(a)


def main():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365)
    rs = [r for r in common.repos(USER)
          if r["name"].lower() != USER.lower() and r.get("size", 0) > 0 and when(r["created_at"]) >= start]
    rs.sort(key=lambda r: r["created_at"])
    for r in rs:
        r["_age"] = max(1, (when(r["pushed_at"]) - when(r["created_at"])).days)
        r["_live"] = bool((r.get("homepage") or "").strip())
        r["_orbit"] = (now - when(r["pushed_at"])).days <= 14
    hi = max((r["_age"] for r in rs), default=1)
    live = sum(r["_live"] for r in rs)
    burning = sum(r["_orbit"] and not r["_live"] for r in rs)
    parked = len(rs) - live - burning

    def theta(d):
        return -SPAN + 2 * SPAN * (d - start).total_seconds() / (now - start).total_seconds()

    def alt(r):
        return R + 22 + ALT * math.sqrt(r["_age"] / hi)

    rnd = random.Random(11)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{escape(f"Launch log: {len(rs)} projects started in the last 12 months, drawn as rockets leaving a planet. {live} reached orbit with live demos, {burning} are still under power.")}">',
         "<title>Launch log</title>",
         f"<desc>{_ctf_desc()}</desc>",  # CTF stage 2 lives here (hex, from ctf/desc.hex)
         t.defs('<style>'
                '@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}'
                '.tr{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.1s cubic-bezier(.3,.6,.2,1) forwards}'
                '@keyframes pop{0%{opacity:0;transform:scale(0)}70%{opacity:1;transform:scale(1.6)}100%{opacity:1;transform:scale(1)}}'
                '.pop{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .45s ease-out forwards}'
                '@keyframes fade{from{opacity:0}to{opacity:1}}.lbl{opacity:0;animation:fade .6s ease-out forwards}'
                '@media (prefers-reduced-motion: reduce){.tr,.pop,.lbl{animation:none;opacity:1;stroke-dashoffset:0}}</style>'
                f'<radialGradient id="planet" cx=".5" cy="0" r="1"><stop offset="0" stop-color="{t.RAISED}"/><stop offset=".25" stop-color="{t.SURFACE}"/><stop offset="1" stop-color="{t.CANVAS}"/></radialGradient>'
                f'<radialGradient id="atmo" cx=".5" cy=".5" r=".5"><stop offset=".9" stop-color="{t.A1}" stop-opacity="0"/><stop offset=".955" stop-color="{t.A1}" stop-opacity=".35"/>'
                f'<stop offset=".965" stop-color="{t.A2}" stop-opacity=".18"/><stop offset="1" stop-color="{t.A1}" stop-opacity="0"/></radialGradient>'
                f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.CANVAS}"/><stop offset="1" stop-color="{t.SURFACE}"/></linearGradient>'
                '<clipPath id="frame"><rect width="830" height="420" rx="16"/></clipPath>'),
         '<g clip-path="url(#frame)">',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    for _ in range(90):  # stars
        x, y = rnd.uniform(0, W), rnd.uniform(0, 330)
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([.5, .7, 1])}" fill="{t.STAR_BG}" opacity=".45">'
                 f'<animate attributeName="opacity" values=".1;.7;.1" dur="{rnd.uniform(2, 6):.1f}s" begin="-{rnd.uniform(0, 5):.1f}s" repeatCount="indefinite"/></circle>')
    # a shooting star now and then
    o.append(f'<line x1="0" y1="0" x2="60" y2="18" stroke="{t.TEXT}" stroke-width="1.2" stroke-linecap="round" opacity="0">'
             '<animateTransform attributeName="transform" type="translate" values="80 30;380 120" dur="11s" keyTimes="0;1" repeatCount="indefinite"/>'
             '<animate attributeName="opacity" values="0;0;.8;0" keyTimes="0;.9;.93;.97" dur="11s" repeatCount="indefinite"/></line>')

    # altitude rings (faint orbits)
    for k, frac in enumerate((.25, .5, .75, 1)):
        r = R + 22 + ALT * math.sqrt(frac)
        days = round(hi * frac)
        a, b = polar(-SPAN - 4, r), polar(SPAN + 4, r)
        o.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} A{r},{r} 0 0 1 {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{t.HAIRLINE}" stroke-dasharray="2 7"/>')
        lx, ly = polar(0, r)  # label each ring at the top of the arc
        o.append(f'<rect x="{lx - 17:.0f}" y="{ly - 7:.0f}" width="34" height="14" rx="7" fill="{t.CANVAS}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{lx:.0f}" y="{ly + 3:.0f}" class="mono" font-size="9" fill="{t.TEXT3}" text-anchor="middle">{days}d</text>')

    # planet, atmosphere, city lights
    o.append(f'<circle cx="{CX}" cy="{CY}" r="{R + 46}" fill="url(#atmo)"/>'
             f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#planet)" stroke="{t.A1}" stroke-opacity=".55" stroke-width="1.5"/>')
    for _ in range(70):
        th, d = rnd.uniform(-30, 30), rnd.uniform(6, 60)
        x, y = polar(th, R - d)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.choice([.6, .8, 1.1])}" fill="{t.A3}" opacity="{rnd.uniform(.15, .5):.2f}"/>')
    # month ticks on the surface
    m = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
    while m <= now:
        if m >= start:
            th = theta(m)
            x1, y1 = polar(th, R)
            x2, y2 = polar(th, R - 7)
            tx, ty = polar(th, R - 22)
            o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t.TEXT3}"/>'
                     f'<text x="{tx:.1f}" y="{ty:.1f}" class="mono" font-size="9.5" fill="{t.TEXT3}" text-anchor="middle" '
                     f'transform="rotate({th:.1f} {tx:.1f} {ty:.1f})">{m.strftime("%b").upper()}</text>')
        m = datetime(m.year + (m.month == 12), m.month % 12 + 1, 1, tzinfo=timezone.utc)
    nx, ny = polar(SPAN, R - 40)
    o.append(f'<text x="{nx:.0f}" y="{ny:.0f}" class="mono" font-size="10" font-weight="700" fill="{t.A3}" text-anchor="middle" transform="rotate({SPAN} {nx:.0f} {ny:.0f})">TODAY</text>')

    # trajectories: a gravity turn from the pad to the rocket's altitude
    def traj(r):
        th = theta(when(r["created_at"]))
        ra = alt(r)
        x0, y0 = polar(th, R)
        x1, y1 = polar(th + 2.2, ra)
        cx, cy = polar(th - .3, R + (ra - R) * .75)
        return th, (x0, y0), (x1, y1), f"M{x0:.1f},{y0:.1f} Q{cx:.1f},{cy:.1f} {x1:.1f},{y1:.1f}"

    order = sorted(rs, key=lambda r: (r["_live"] or r["_orbit"], r["_age"]))
    rank = {r["name"]: i for i, r in enumerate(rs)}  # launch order for the intro
    for r in order:
        th, (x0, y0), (x, y), d = traj(r)
        k = rank[r["name"]]
        delay = .3 + 3.2 * k / max(1, len(rs) - 1)
        col = t.GREEN if r["_live"] else t.A3 if r["_orbit"] else t.TEXT3
        hot = r["_live"] or r["_orbit"]
        o.append(f'<path class="tr" pathLength="1" d="{d}" fill="none" stroke="{col}" stroke-opacity="{.55 if hot else .22}" '
                 f'stroke-width="{1.6 if hot else 1}" style="animation-delay:{delay:.2f}s"/>')
        o.append(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="1.6" fill="{col}" opacity=".7"/>')  # launch pad
        tip = f'<title>{escape(r["name"])}: launched {r["created_at"][:10]}, {r["_age"]} days of work</title>'
        land = delay + 1.0
        if r["_live"]:  # a little satellite with a beacon
            o.append(f'<g class="pop" style="animation-delay:{land:.2f}s">{tip}'
                     f'<g transform="translate({x:.1f},{y:.1f}) rotate({th:.0f})">'
                     f'<rect x="-3" y="-3" width="6" height="6" rx="1" fill="{t.GREEN}"/>'
                     f'<rect x="-11" y="-1.6" width="6" height="3.2" fill="{t.A1}"/><rect x="5" y="-1.6" width="6" height="3.2" fill="{t.A1}"/></g></g>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{t.GREEN}" stroke-width="1.2" opacity="0">'
                     f'<animate attributeName="r" values="5;14;5" dur="2.6s" begin="{land:.2f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".8;0;.8" dur="2.6s" begin="{land:.2f}s" repeatCount="indefinite"/></circle>')
        elif r["_orbit"]:  # still burning: drifts along its orbit with a flicker
            ra = alt(r)
            a, b = polar(th + .8, ra), polar(th + 3.6, ra)
            o.append(f'<g class="pop" style="animation-delay:{land:.2f}s">{tip}<circle r="3.8" fill="{t.A3}">'
                     f'<animateMotion path="M{a[0]:.1f},{a[1]:.1f} A{ra:.0f},{ra:.0f} 0 0 1 {b[0]:.1f},{b[1]:.1f}" keyPoints="0;1;0" keyTimes="0;.5;1" calcMode="spline" '
                     f'keySplines=".4 0 .6 1;.4 0 .6 1" dur="{rnd.uniform(8, 12):.1f}s" repeatCount="indefinite"/>'
                     '<animate attributeName="r" values="3.2;4.4;3.2" dur=".7s" repeatCount="indefinite"/></circle></g>')
        else:
            o.append(f'<circle class="pop" cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{t.TEXT3}" style="animation-delay:{land:.2f}s">{tip}</circle>')

    # the newest launch keeps lifting off: a rocket with a flame riding its trajectory
    if rs:
        newest = rs[-1]
        _, _, _, d = traj(newest)
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.4;.45;1" dur="7s" begin="4.5s" repeatCount="indefinite"/>'
                 f'<animateMotion path="{d}" dur="7s" keyPoints="0;1;1" keyTimes="0;.42;1" calcMode="spline" keySplines=".5 0 .9 .6;0 0 1 1" begin="4.5s" rotate="auto" repeatCount="indefinite"/>'
                 f'<path d="M-6 0 L-16 -2.5 L-13 0 L-16 2.5 Z" fill="{t.BEACON[0]}"><animate attributeName="d" values="M-6 0 L-16 -2.5 L-13 0 L-16 2.5 Z;M-6 0 L-21 -3 L-15 0 L-21 3 Z;M-6 0 L-16 -2.5 L-13 0 L-16 2.5 Z" dur=".2s" repeatCount="indefinite"/></path>'
                 f'<path d="M7 0 L-6 -3.5 L-6 3.5 Z" fill="{t.TEXT}"/></g>')

    # labels for the projects I feature (data/projects.json), never coursework
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.json"), encoding="utf-8"))
    featured = {f["repo"].lower() for f in cfg.get("featured", [])}
    skip = {n.lower() for n in cfg.get("exclude_more", [])}
    prefixes = tuple(p.lower() for p in cfg.get("exclude_prefix_more", []))

    def notable(r):
        n = r["name"].lower()
        return n in featured or ((r["_live"] or r["_orbit"]) and n not in skip and not n.startswith(prefixes) and r.get("description"))
    labelled = sorted((r for r in rs if notable(r)), key=lambda r: (r["name"].lower() in featured, r["_age"]), reverse=True)
    boxes = []
    for r in labelled:
        th, _, _, _ = traj(r)
        x, y = polar(th + 2.2, alt(r))
        name = r["name"].rstrip("-_")
        name = name if len(name) <= 16 else name[:15] + "…"
        w = len(name) * 6.2 + 8
        right = x < W - w - 30
        bx = x + 9 if right else x - 9 - w
        box = (bx, y - 14, bx + w, y + 2)
        if len(boxes) >= 10 or any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in boxes):
            continue
        boxes.append(box)
        col = t.GREEN if r["_live"] else t.A3 if r["_orbit"] else t.TEXT2
        o.append(f'<text class="lbl" x="{bx + 4:.1f}" y="{y - 2:.1f}" font-size="10.5" font-weight="600" fill="{col}" '
                 f'style="animation-delay:{.3 + 3.2 * rank[r["name"]] / max(1, len(rs) - 1) + 1.1:.2f}s">{escape(name)}</text>')

    # header: mission-control readout
    o.append(f'<rect x="0" y="0" width="{W}" height="54" fill="{t.CANVAS}" fill-opacity=".55"/>'
             f'<circle cx="28" cy="27" r="3.5" fill="{t.BEACON[0]}"><animate attributeName="opacity" values="1;.2;1" dur="1.2s" repeatCount="indefinite"/></circle>'
             f'<text x="40" y="31" class="label" style="fill:{t.TEXT2}">LAUNCH LOG</text>'
             f'<text x="142" y="31" class="mono" font-size="10.5" fill="{t.TEXT3}">{len(rs)} launches in 12 months · higher = built for longer</text>')
    lx = W - 28
    for col, name, nval, shape in ((t.TEXT3, "parked", parked, "dot"), (t.A3, "under power", burning, "dot"), (t.GREEN, "in orbit, live", live, "sat")):
        label = f"{nval} {name}"
        lx -= len(label) * 6.3 + 26
        o.append(f'<circle cx="{lx + 5}" cy="27" r="4" fill="{col}"/>'
                 f'<text x="{lx + 14}" y="31" class="mono" font-size="10.5" fill="{t.TEXT2}"><tspan fill="{col}" font-weight="700">{nval}</tspan> {name}</text>')
    o.append(f'<line x1="0" y1="54" x2="{W}" y2="54" stroke="{t.HAIRLINE}"/>')
    o += ["</g>", t.card_border(W, H, 16), "</svg>"]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(o))
    print(f"wrote {OUT}: {len(rs)} launches, {live} live, {burning} burning")


if __name__ == "__main__":
    main()
