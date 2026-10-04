#!/usr/bin/env python3
"""Generate assets/radar.svg: an animated threat-radar of a GitHub user's repos.

Every non-fork repo is a blip.
  bearing = language sector (bigger languages get wider sectors)
  range   = days since last push (close to the centre = fresh)
  size    = stars + repo size
A sweep arm rotates; each blip flashes as the arm passes over it. Pure SMIL
animation, so it plays inside an <img> tag on a GitHub README (no JS).

Stdlib only. Usage: radar.py [user] [out.svg]   (GITHUB_TOKEN optional)
"""
import hashlib
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/radar.svg"

# stage 2 of the README CTF lives in <desc>; written by scripts/ctf_build.py
DESC_FILE = os.path.join(os.path.dirname(__file__), "..", "ctf", "desc.hex")

W, H = 830, 500
CX, CY, R = 222, 250, 192
PERIOD = 9.0  # seconds per sweep
BG, GRID, GREEN = "#0d1117", "#0f5d2c", "#00ff41"

LANG_COLOR = {
    "Python": "#ffd43b", "TypeScript": "#4aa8ff", "JavaScript": "#f7df1e",
    "Java": "#ff7a45", "HTML": "#ff5f87", "C": "#b48cff", "Other": "#9aa4b2",
}


def fetch_repos():
    repos, page = [], 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&sort=pushed",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "radar-gen"},
        )
        tok = os.environ.get("GITHUB_TOKEN")
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def polar(bearing, radius):
    b = math.radians(bearing)
    return CX + radius * math.sin(b), CY - radius * math.cos(b)


def jitter(name, span):
    h = int(hashlib.sha1(name.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    return (h - 0.5) * span


def main():
    now = datetime.now(timezone.utc)
    repos = [r for r in fetch_repos() if not r["fork"] and r["name"].lower() != USER.lower()]
    for r in repos:
        pushed = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
        r["days"] = max(0, (now - pushed).days)
        lang = r["language"] if r["language"] in LANG_COLOR else ("Other" if r["language"] else "Other")
        r["lang"] = lang

    # sectors: width proportional to repo count (with a floor)
    groups = {}
    for r in repos:
        groups.setdefault(r["lang"], []).append(r)
    order = sorted(groups, key=lambda k: -len(groups[k]))
    total = sum(max(len(groups[k]), 3) for k in order)
    sector, start = {}, 0.0
    for k in order:
        span = 360 * max(len(groups[k]), 3) / total
        sector[k] = (start, span)
        start += span

    blips = []
    for k in order:
        a0, span = sector[k]
        members = sorted(groups[k], key=lambda r: r["days"])
        for i, r in enumerate(members):
            bearing = a0 + span * (i + 0.5) / len(members)
            # log range: last 3 days sits at ~25%, a year out hits the rim
            rad = R * (0.14 + 0.82 * min(1.0, math.log1p(r["days"]) / math.log1p(365)))
            rad += jitter(r["name"], 14)
            x, y = polar(bearing, max(24, min(R - 8, rad)))
            size = 3.2 + min(5.0, math.sqrt(r["stargazers_count"]) * 1.6) + min(2.0, r["size"] / 40000)
            blips.append(dict(r=r, bearing=bearing, x=x, y=y, size=size, color=LANG_COLOR[k]))

    # label the most interesting contacts: described, recently pushed, starred
    def score(b):
        r = b["r"]
        return (bool(r["description"]) * 3) + r["stargazers_count"] * 2 - math.log1p(r["days"]) * 0.6
    labelled, placed = set(), []
    for b in sorted(blips, key=score, reverse=True):
        if len(labelled) == 9:
            break
        if all(math.hypot(b["x"] - px_, b["y"] - py_) > 70 for px_, py_ in placed):
            labelled.add(id(b))
            placed.append((b["x"], b["y"]))

    o = []
    add = o.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Animated threat radar of {escape(USER)} repositories">')
    try:
        with open(DESC_FILE) as f:
            desc = f.read().strip()
    except OSError:
        desc = ""
    add(f"<title>THREAT RADAR // {escape(USER)}</title>")
    add(f"<desc>{desc}</desc>")
    add(f"""<defs>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<radialGradient id="disc"><stop offset="0" stop-color="#06210f"/><stop offset="1" stop-color="#050b08"/></radialGradient>
<style>text{{font-family:'Fira Code','Cascadia Code',Consolas,monospace}}</style>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="{BG}" stroke="{GRID}"/>
<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#disc)" stroke="{GREEN}" stroke-opacity=".55"/>""")

    # range rings + labels
    for frac, lab in ((0.14 + 0.82 * math.log1p(d) / math.log1p(365), t) for d, t in ((7, "7d"), (30, "30d"), (90, "90d"))):
        add(f'<circle cx="{CX}" cy="{CY}" r="{R*frac:.1f}" fill="none" stroke="{GRID}" stroke-dasharray="3 5"/>')
        add(f'<text x="{CX+4}" y="{CY-R*frac-3:.1f}" font-size="9" fill="{GREEN}" fill-opacity=".45">{lab}</text>')
    for a in range(0, 360, 30):
        x2, y2 = polar(a, R)
        add(f'<line x1="{CX}" y1="{CY}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{GRID}" stroke-opacity=".6"/>')
    # sector boundaries + arc labels
    for k in order:
        a0, span = sector[k]
        x1, y1 = polar(a0, R)
        x2, y2 = polar(a0, R + 6)
        add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{LANG_COLOR[k]}"/>')

    # sweep arm: trailing wedge of stacked slices, rotates about the centre
    add(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" to="360 {CX} {CY}" dur="{PERIOD}s" repeatCount="indefinite"/>')
    slices = 14
    step = 4.0
    for i in range(slices):
        a_hi, a_lo = -i * step, -(i + 1) * step
        p1, p2 = polar(a_hi, R), polar(a_lo, R)
        op = 0.32 * (1 - i / slices) ** 2
        add(f'<path d="M{CX},{CY} L{p1[0]:.1f},{p1[1]:.1f} A{R},{R} 0 0 0 {p2[0]:.1f},{p2[1]:.1f} Z" fill="{GREEN}" fill-opacity="{op:.3f}"/>')
    tip = polar(0, R)
    add(f'<line x1="{CX}" y1="{CY}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" stroke="{GREEN}" stroke-width="1.6" filter="url(#glow)"/></g>')

    # blips: each one flashes when the arm crosses its bearing
    for b in blips:
        begin = b["bearing"] / 360 * PERIOD - PERIOD
        flash = (f'<animate attributeName="opacity" values="1;.6;.3;.3" keyTimes="0;.12;.7;1" '
                 f'dur="{PERIOD}s" begin="{begin:.2f}s" repeatCount="indefinite"/>')
        add(f'<g opacity=".3">{flash}')
        add(f'<circle cx="{b["x"]:.1f}" cy="{b["y"]:.1f}" r="{b["size"]:.1f}" fill="{b["color"]}" filter="url(#glow)"/>')
        if id(b) in labelled:
            right = b["x"] < CX + 90
            tx = b["x"] + (b["size"] + 5 if right else -(b["size"] + 5))
            anchor = "start" if right else "end"
            add(f'<text x="{tx:.1f}" y="{b["y"]+3:.1f}" font-size="11" fill="{b["color"]}" text-anchor="{anchor}">{escape(b["r"]["name"][:18])}</text>')
        add("</g>")

    # centre marker
    add(f'<circle cx="{CX}" cy="{CY}" r="4" fill="{GREEN}" filter="url(#glow)"/>')
    add(f'<text x="{CX}" y="{CY+18}" font-size="9" fill="{GREEN}" text-anchor="middle" fill-opacity=".8">YOU</text>')
    add(f'<text x="{CX}" y="{CY-R-8}" font-size="9" fill="{GREEN}" text-anchor="middle" fill-opacity=".6">N</text>')

    # ---- readout panel ----
    px = 452
    langs_n = len(order)
    newest = min(blips, key=lambda b: b["r"]["days"])["r"] if blips else None
    stars = sum(b["r"]["stargazers_count"] for b in blips)
    add(f'<text x="{px}" y="46" font-size="19" fill="{GREEN}" font-weight="bold">THREAT RADAR // {escape(USER.upper())}</text>')
    add(f'<text x="{px}" y="64" font-size="12" fill="#7d8590">live scan · auto-rebuilt · {now:%m-%d %H:%M} UTC</text>')
    add(f'<line x1="{px}" y1="76" x2="{W-30}" y2="76" stroke="{GRID}"/>')
    stats = [("CONTACTS", str(len(blips))), ("LANGUAGES", str(langs_n)), ("STARS EARNED", str(stars)),
             ("HOT (30d)", str(sum(1 for b in blips if b["r"]["days"] <= 30))),
             ("LAST CONTACT", f'{newest["name"][:20]} ({newest["days"]}d)' if newest else "-")]
    for i, (k, v) in enumerate(stats):
        y = 100 + i * 21
        add(f'<text x="{px}" y="{y}" font-size="13" fill="#7d8590">{k}</text>')
        add(f'<text x="{px+150}" y="{y}" font-size="13" fill="#e6edf3">{escape(v)}</text>')
    add(f'<line x1="{px}" y1="214" x2="{W-30}" y2="214" stroke="{GRID}"/>')
    add(f'<text x="{px}" y="234" font-size="12" fill="{GREEN}" fill-opacity=".8">SECTORS</text>')
    for i, k in enumerate(order):
        col, row = i % 2, i // 2
        x, y = px + col * 190, 254 + row * 20
        add(f'<circle cx="{x+4}" cy="{y-3}" r="4" fill="{LANG_COLOR[k]}"/>')
        add(f'<text x="{x+18}" y="{y}" font-size="13" fill="#e6edf3">{k} <tspan fill="#7d8590">x{len(groups[k])}</tspan></text>')
    hot = sorted(blips, key=lambda b: b["r"]["days"])[:5]
    add(f'<line x1="{px}" y1="352" x2="{W-30}" y2="352" stroke="{GRID}"/>')
    add(f'<text x="{px}" y="372" font-size="12" fill="{GREEN}" fill-opacity=".8">LATEST ACTIVITY</text>')
    for i, b in enumerate(hot):
        y = 392 + i * 20
        d = b["r"]["days"]
        add(f'<circle cx="{px+4}" cy="{y-3}" r="3.5" fill="{b["color"]}"/>')
        add(f'<text x="{px+18}" y="{y}" font-size="13" fill="#e6edf3">{escape(b["r"]["name"][:24])}</text>')
        add(f'<text x="{W-30}" y="{y}" font-size="13" fill="#7d8590" text-anchor="end">{"today" if d == 0 else f"{d}d ago"}</text>')
    add("</svg>")

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: {len(blips)} blips, {langs_n} sectors")


if __name__ == "__main__":
    main()
