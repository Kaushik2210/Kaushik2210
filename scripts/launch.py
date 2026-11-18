#!/usr/bin/env python3
"""assets/launch.svg: the launch log. Every project I started in the last 12 months as a launch.

  x position   = launch date (repo created)
  altitude     = how long I kept building it (created -> last push)
  green ring   = live demo (repo has a homepage)
  gold         = in orbit (pushed in the last 14 days)
  grey         = parked
"""
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/launch.svg"
W, H = 830, 330
X0, X1 = 44, W - 30
GROUND = H - 52
TOP = 92


def _ctf_desc():
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ctf", "desc.hex")
    return open(f, encoding="utf-8").read().strip() if os.path.exists(f) else ""


def when(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


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

    def x_of(d):
        return X0 + (X1 - X0) * (d - start).total_seconds() / (now - start).total_seconds()

    def alt(r):
        return GROUND - 16 - (GROUND - TOP - 16) * math.sqrt(r["_age"] / hi)

    live = sum(r["_live"] for r in rs)
    orbit = sum(r["_orbit"] for r in rs)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{escape(f"Launch log: {len(rs)} projects started in the last 12 months, {live} with live demos, {orbit} still in active development.")}">',
         "<title>Launch log</title>",
         f"<desc>{_ctf_desc()}</desc>",  # CTF stage 2 lives here (hex, from ctf/desc.hex)
         t.defs('<style>@keyframes up{from{transform:scaleY(0)}to{transform:scaleY(1)}}'
                '.trail{transform-box:fill-box;transform-origin:50% 100%;animation:up 1.1s cubic-bezier(.2,.8,.2,1) both}'
                '@keyframes fade{from{opacity:0}to{opacity:1}}.lbl{animation:fade .6s ease-out both}'
                '@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>'
                '<linearGradient id="trail" x1="0" y1="1" x2="0" y2="0">'
                f'<stop offset="0" stop-color="{t.A1}" stop-opacity="0"/><stop offset="1" stop-color="{t.A2}" stop-opacity=".9"/></linearGradient>'),
         t.card_open(W, H, "LAUNCH LOG", f"{len(rs)} launches · last 12 months")]

    # legend
    lx = 28
    for col, name, n in ((t.GREEN, "live demo", live), (t.A3, "in orbit", orbit), (t.TEXT3, "parked", len(rs) - live - orbit)):
        o.append(f'<circle cx="{lx + 5}" cy="70" r="4.5" fill="{col}"/>'
                 f'<text x="{lx + 15}" y="74" font-size="{t.T_CAP + 1}" fill="{t.TEXT2}">{name} <tspan fill="{t.TEXT3}">{n}</tspan></text>')
        lx += 120
    o.append(f'<text x="{W - 28}" y="74" class="mono" font-size="{t.T_CAP}" fill="{t.TEXT3}" text-anchor="end">altitude = days in development</text>')

    # ground + month ticks
    o.append(f'<line x1="{X0 - 14}" y1="{GROUND}" x2="{X1 + 8}" y2="{GROUND}" stroke="{t.HAIRLINE}" stroke-width="1.5"/>')
    m = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
    while m <= now:
        if m >= start:
            x = x_of(m)
            o.append(f'<line x1="{x:.1f}" y1="{GROUND}" x2="{x:.1f}" y2="{GROUND + 5}" stroke="{t.HAIRLINE}"/>'
                     f'<text x="{x:.1f}" y="{GROUND + 20}" class="mono" font-size="{t.T_CAP}" fill="{t.TEXT3}" text-anchor="middle">{m.strftime("%b").upper()}</text>')
        m = datetime(m.year + (m.month == 12), m.month % 12 + 1, 1, tzinfo=timezone.utc)
    o.append(f'<text x="{X1 + 4}" y="{GROUND + 36}" class="mono" font-size="{t.T_LABEL}" fill="{t.A3}" text-anchor="end">NOW ▸</text>')

    # trajectories, parked first so live/orbit sit on top
    order = sorted(rs, key=lambda r: (r["_live"] or r["_orbit"], r["_age"]))
    # label the projects I actually feature (data/projects.json), never coursework
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.json"), encoding="utf-8"))
    featured = {f["repo"].lower() for f in cfg.get("featured", [])}
    skip = {n.lower() for n in cfg.get("exclude_more", [])}
    prefixes = tuple(p.lower() for p in cfg.get("exclude_prefix_more", []))
    def notable(r):
        n = r["name"].lower()
        return n in featured or ((r["_live"] or r["_orbit"]) and n not in skip and not n.startswith(prefixes) and r.get("description"))
    labelled = sorted((r for r in rs if notable(r)), key=lambda r: (r["name"].lower() in featured, r["_age"]), reverse=True)
    for k, r in enumerate(order):
        x, y = x_of(when(r["created_at"])), alt(r)
        col = t.GREEN if r["_live"] else t.A3 if r["_orbit"] else t.TEXT3
        d = f"{0.03 * k:.2f}s"
        o.append(f'<line class="trail" x1="{x:.1f}" y1="{GROUND}" x2="{x:.1f}" y2="{y:.1f}" stroke="url(#trail)" '
                 f'stroke-width="{2 if (r["_live"] or r["_orbit"]) else 1.2}" style="animation-delay:{d}"/>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4.5 if (r["_live"] or r["_orbit"]) else 3}" fill="{col}">'
                 f'<title>{escape(r["name"])}: launched {r["created_at"][:10]}, {r["_age"]} days of work</title></circle>')
        if r["_live"]:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{t.GREEN}" stroke-width="1.5">'
                     f'<animate attributeName="r" values="5;12;5" dur="2.4s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".9;0;.9" dur="2.4s" repeatCount="indefinite"/></circle>')
    placed = []
    for k, r in enumerate(labelled):
        x, y = x_of(when(r["created_at"])), alt(r)
        if any(abs(x - px) < 46 and abs(y - py) < 34 for px, py in placed) or len(placed) >= 9:
            continue
        placed.append((x, y))
        name = r["name"] if len(r["name"]) <= 18 else r["name"][:17] + "…"
        col = t.GREEN if r["_live"] else t.A3 if r["_orbit"] else t.TEXT2
        o.append(f'<text class="lbl" x="{x + 6:.1f}" y="{y - 8:.1f}" font-size="{t.T_CAP}" font-weight="600" fill="{col}" '
                 f'transform="rotate(-28 {x + 6:.1f} {y - 8:.1f})" style="animation-delay:{0.6 + 0.05 * k:.2f}s">{escape(name)}</text>')

    o += [t.card_border(W, H, 16), "</svg>"]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(o))
    print(f"wrote {OUT}: {len(rs)} launches, {live} live, {orbit} in orbit")


if __name__ == "__main__":
    main()
