#!/usr/bin/env python3
"""assets/missions.svg: a game-style mission map of my featured projects.

A ship flies a route through every project. At each stop the briefing panel shows
that mission: its live animated scene, the objective, and real stats from GitHub
(language, stars, days of work, live demo or repo). Pure SMIL, loops forever.
Usage: missionmap.py [user] [out]
"""
import json
import math
import os
import random
import sys
from xml.sax.saxutils import escape

import common
import scenes
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../assets/missions.svg"
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 830, 330
STOP, MOVE = 2.6, 0.9                        # seconds parked at a mission, seconds flying to the next
CAT = {"security": ("SECURITY", t.A1), "devtool": ("DEV TOOL", t.A3), "product": ("PRODUCT", t.RINGS[2]), "learning": ("LEARNING", t.CLOCK[3])}
OBJ = {
    "net-sentinel": "Catch the attacker moving through the network and name the technique.",
    "orbital-sentinel": "Work out what really hit the satellite: a fault, an attack or the sun.",
    "scam-khel": "Stop the digital-arrest scam call before the family pays.",
    "deepfake-detector": "Unmask the synthetic face, with a calibrated score and evidence.",
    "intentguard": "Let the AI agent work, and block every action it should never take.",
    "tapwire": "Make the coding agent stop repeating the same mistake.",
    "gitvisualise": "Turn any repository into a narrated architecture tour.",
    "hireos": "Land the job with materials that never invent a word.",
    "algoverse": "Watch algorithms think, then walk into the interview ready.",
}


def wrap(text, width):
    out, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > width and cur:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return out + [cur]


def when(s):
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    cfg = json.load(open(os.path.join(HERE, "..", "data", "projects.json"), encoding="utf-8"))
    repos = {r["name"]: r for r in common.repos(USER)}
    ms = [(f, repos[f["repo"]]) for f in cfg["featured"] if f["repo"] in repos][:9]
    n = len(ms)
    rnd = random.Random(7)

    # serpentine route: three rows, alternating direction, gently jittered
    pts = []
    for i in range(n):
        row, col = divmod(i, 3)
        if row % 2:
            col = 2 - col
        pts.append((80 + col * 175 + rnd.uniform(-14, 14), 104 + row * 82 + rnd.uniform(-8, 8)))
    loop = pts + [pts[0]]
    seg = [math.dist(loop[i], loop[i + 1]) for i in range(n)]
    total = sum(seg)
    frac = [sum(seg[:i]) / total for i in range(n)] + [1.0]
    cyc = n * (STOP + MOVE)
    route = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in loop)

    def kt(x):
        return f"{x / cyc:.4f}"

    # ship timing: park, fly, park, fly ... back to the start
    kts, kps = [], []
    for i in range(n):
        a = i * (STOP + MOVE)
        kts += [kt(a), kt(a + STOP)]
        kps += [f"{frac[i]:.4f}", f"{frac[i]:.4f}"]
    kts.append("1")
    kps.append("1")
    kts, kps = ";".join(kts), ";".join(kps)

    def window(i, fade=.12):
        a, b = i * (STOP + MOVE), i * (STOP + MOVE) + STOP + .25
        if i == 0:
            return (f'values="1;1;0;0;1" keyTimes="0;{kt(b)};{kt(b + fade)};{kt(cyc - fade)};1"')
        return f'values="0;0;1;1;0;0" keyTimes="0;{kt(a - .05)};{kt(a + fade)};{kt(b)};{kt(b + fade)};1"'

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{escape("Mission map: a ship flies between my " + str(n) + " featured projects and briefs each one: " + ", ".join(r["name"] for _, r in ms) + ".")}">',
         "<title>Mission map</title>",
         t.defs('<clipPath id="thumb"><rect width="405" height="150" rx="10"/></clipPath>'
                f'<radialGradient id="neb1"><stop offset="0" stop-color="{t.A1}" stop-opacity=".22"/><stop offset="1" stop-color="{t.A1}" stop-opacity="0"/></radialGradient>'
                f'<radialGradient id="neb2"><stop offset="0" stop-color="{t.A3}" stop-opacity=".14"/><stop offset="1" stop-color="{t.A3}" stop-opacity="0"/></radialGradient>'
                '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".25"/></pattern>'),
         f'<rect width="{W}" height="{H}" rx="16" fill="{t.CANVAS}"/>',
         '<ellipse cx="160" cy="120" rx="220" ry="130" fill="url(#neb1)"/><ellipse cx="420" cy="260" rx="200" ry="110" fill="url(#neb2)"/>']
    for _ in range(70):  # twinkling starfield
        x, y = rnd.uniform(10, 500), rnd.uniform(40, H - 10)
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([.6, .8, 1.1])}" fill="{t.STAR_BG}" opacity=".5">'
                 f'<animate attributeName="opacity" values=".15;.8;.15" dur="{rnd.uniform(2, 5):.1f}s" begin="-{rnd.uniform(0, 4):.1f}s" repeatCount="indefinite"/></circle>')
    # header
    o.append(f'<text x="28" y="36" class="mono" font-size="12" font-weight="700" fill="{t.TEXT}" letter-spacing="2">SELECT YOUR MISSION</text>'
             f'<text x="200" y="36" class="mono" font-size="11" fill="{t.A3}">▶ <animate attributeName="opacity" values="1;0;1" dur="1s" calcMode="discrete" repeatCount="indefinite"/></text>'
             f'<text x="{W - 28}" y="36" class="mono" font-size="10" fill="{t.TEXT3}" text-anchor="end">{n} missions · stats live from GitHub</text>'
             f'<line x1="28" y1="48" x2="{W - 28}" y2="48" stroke="{t.HAIRLINE}"/>')
    # route: faint dashes, and a bright trail that grows as the ship flies
    o.append(f'<path d="{route}" fill="none" stroke="{t.HAIRLINE}" stroke-width="2" stroke-dasharray="2 6" stroke-linecap="round"/>')
    o.append(f'<path d="{route}" fill="none" stroke="{t.A2}" stroke-opacity=".55" stroke-width="2" stroke-linejoin="round" '
             f'stroke-dasharray="{total:.0f}" stroke-dashoffset="{total:.0f}">'
             f'<animate attributeName="stroke-dashoffset" values="' + ";".join(f"{total * (1 - float(k)):.1f}" for k in kps.split(";")) +
             f'" keyTimes="{kts}" dur="{cyc:.1f}s" repeatCount="indefinite"/></path>')
    # mission planets
    for i, ((f, r), (x, y)) in enumerate(zip(ms, pts)):
        lab, col = CAT.get(f.get("category", "product"), CAT["product"])
        live = bool(r.get("homepage"))
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="none" stroke="{col}" stroke-width="2" opacity="0">'
                 f'<animate attributeName="opacity" {window(i)} dur="{cyc:.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="r" values="16;26;16" dur="1.3s" repeatCount="indefinite"/></circle>')
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="{t.SURFACE}" stroke="{col}" stroke-width="2"/>'
                 f'<circle cx="{x - 3:.1f}" cy="{y - 3:.1f}" r="6" fill="{col}" opacity=".35"/>'
                 + (f'<circle cx="{x + 10:.1f}" cy="{y - 10:.1f}" r="3.5" fill="{t.GREEN}"/>' if live else "")
                 + f'<text x="{x:.1f}" y="{y + 30:.1f}" class="mono" font-size="9" fill="{t.TEXT2}" text-anchor="middle">'
                 f'<tspan fill="{col}" font-weight="700">M{i + 1:02d}</tspan> {escape(r["name"].rstrip("-_"))}</text>')
    # the ship
    o.append(f'<g><animateMotion path="{route}" keyPoints="{kps}" keyTimes="{kts}" calcMode="linear" rotate="auto" dur="{cyc:.1f}s" repeatCount="indefinite"/>'
             f'<path d="M-14 -3 L-24 0 L-14 3 Z" fill="{t.A3}"><animate attributeName="d" values="M-14 -3 L-24 0 L-14 3 Z;M-14 -3 L-19 0 L-14 3 Z;M-14 -3 L-24 0 L-14 3 Z" dur=".25s" repeatCount="indefinite"/></path>'
             f'<path d="M10 0 L-12 -8 L-8 0 L-12 8 Z" fill="{t.TEXT}" stroke="{t.A2}" stroke-width="1.2" filter="url(#glow)"/></g>')

    # briefing panel
    px, py, pw = 520, 60, W - 548
    o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{H - py - 16}" rx="12" fill="{t.SURFACE}" stroke="{t.HAIRLINE}"/>'
             f'<text x="{px + 14}" y="{py + 20}" class="mono" font-size="9.5" fill="{t.TEXT3}" letter-spacing="1.5">BRIEFING</text>'
             f'<circle cx="{px + pw - 18}" cy="{py + 16}" r="3.5" fill="{t.BEACON[0]}"><animate attributeName="opacity" values="1;.2;1" dur="1.2s" repeatCount="indefinite"/></circle>')
    s = (pw - 28) / 405
    for i, (f, r) in enumerate(ms):
        lab, col = CAT.get(f.get("category", "product"), CAT["product"])
        name = r["name"].rstrip("-_")
        live = bool(r.get("homepage"))
        days = max(1, (when(r["pushed_at"]) - when(r["created_at"])).days)
        scene = scenes.scene(r["name"]) or ""
        g = [f'<g opacity="{1 if i == 0 else 0}"><animate attributeName="opacity" {window(i)} dur="{cyc:.1f}s" repeatCount="indefinite"/>',
             f'<g transform="translate({px + 14},{py + 30}) scale({s:.4f})"><g clip-path="url(#thumb)">'
             f'<rect width="405" height="150" fill="{t.RAISED}"/>{scene}<rect width="405" height="150" fill="url(#scan)"/></g>'
             f'<rect width="405" height="150" rx="10" fill="none" stroke="{col}" stroke-opacity=".6" stroke-width="2"/></g>']
        ty = py + 30 + 150 * s + 24
        g.append(f'<text x="{px + 14}" y="{ty}" font-size="17" font-weight="700" fill="{t.TEXT}">{escape(name)}</text>'
                 f'<text x="{px + pw - 14}" y="{ty}" class="mono" font-size="9.5" fill="{col}" text-anchor="end">M{i + 1:02d} · {lab}</text>')
        for k, line in enumerate(wrap(OBJ.get(r["name"].lower(), f.get("blurb", "")), 44)[:2]):
            g.append(f'<text x="{px + 14}" y="{ty + 19 + k * 15}" font-size="11.5" fill="{t.TEXT2}">{escape(line)}</text>')
        g.append(f'<text x="{px + 14}" y="{ty + 58}" class="mono" font-size="10" fill="{t.TEXT3}">'
                 f'{escape(r["language"] or "misc")} · ★ {r["stargazers_count"]} · {days} days of work · '
                 + (f'<tspan fill="{t.GREEN}">LIVE</tspan>' if live else "REPO") + "</text>")
        g.append("</g>")
        o.append("".join(g))
    for i in range(n):  # while flying, the panel shows the jump
        a = i * (STOP + MOVE) + STOP + .3
        b = i * (STOP + MOVE) + STOP + MOVE - .05
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{kt(a)};{kt(a + .05)};{kt(b - .05)};{kt(b)};1" dur="{cyc:.1f}s" repeatCount="indefinite"/>'
                 f'<text x="{px + pw / 2}" y="{py + 120}" class="mono" font-size="12" font-weight="700" fill="{t.A2}" text-anchor="middle" letter-spacing="2">WARPING TO M{(i + 1) % n + 1:02d}</text>'
                 + "".join(f'<rect x="{px + pw / 2 - 60 + k * 26}" y="{py + 134}" width="16" height="4" rx="2" fill="{t.A2}" opacity=".3">'
                           f'<animate attributeName="opacity" values=".2;1;.2" dur=".5s" begin="{k * .1:.1f}s" repeatCount="indefinite"/></rect>' for k in range(5))
                 + "</g>")
    o.append(f'<text x="{px + 14}" y="{H - 26}" class="mono" font-size="10" fill="{t.A3}">▶ tap its card below to launch'
             '<animate attributeName="opacity" values="1;.35;1" dur="1.6s" repeatCount="indefinite"/></text>')
    o.append(t.card_border(W, H, 16) + "</svg>")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("".join(o))
    print(f"wrote {OUT}: {n} missions, {cyc:.0f}s loop")


if __name__ == "__main__":
    main()
