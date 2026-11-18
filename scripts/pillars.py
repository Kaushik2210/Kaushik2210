#!/usr/bin/env python3
"""assets/pillar-*.svg: the three "What I build" panels, each a small animated scene.

  security  a shield takes hits from incoming threats; each one is caught, labelled and explained
  agents    an AI agent drives down a lane; when it drifts, a guardrail bounces it back and a rule is written
  products  app windows launch one by one and go live
The counts come from data/projects.json and the GitHub API. Pure SMIL.
Usage: pillars.py [user] [assets_dir]
"""
import json
import math
import os
import random
import sys
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
W, H = 400, 250
SH = 150                       # scene height
RED = t.BEACON[0]


def frame(key, title, kicker, stat, col, scene, alt):
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
        f"<title>{escape(title)}</title>",
        t.defs(f'<clipPath id="c_{key}"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
               f'<radialGradient id="g_{key}" cx=".5" cy=".45" r=".6"><stop offset="0" stop-color="{col}" stop-opacity=".28"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
               '<pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".8" fill="#fff" fill-opacity=".06"/></pattern>'),
        f'<g clip-path="url(#c_{key})"><rect width="{W}" height="{H}" fill="{t.SURFACE}"/>',
        f'<rect width="{W}" height="{SH}" fill="{t.CANVAS}"/><rect width="{W}" height="{SH}" fill="url(#dots)"/><rect width="{W}" height="{SH}" fill="url(#g_{key})"/>',
        scene,
        f'<rect y="{SH}" width="{W}" height="1.5" fill="{col}" opacity=".6"/>',
        f'<text x="20" y="{SH + 26}" class="mono" font-size="10" letter-spacing="1.6" fill="{col}">{escape(kicker)}</text>',
        f'<text x="20" y="{SH + 52}" font-size="21" font-weight="800" letter-spacing="-.4" fill="{t.TEXT}">{escape(title)}</text>',
        f'<text x="20" y="{SH + 78}" class="mono" font-size="11" fill="{t.TEXT2}">{stat}</text>',
        "</g>", t.card_border(W, H, 16), "</svg>"])


def security():
    cx, cy = W / 2, 76
    o = []
    for r in (30, 52, 74):
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t.A1}" stroke-opacity=".18" stroke-dasharray="3 5"/>')
    o.append(f'<path d="M{cx} {cy - 30} L{cx + 24} {cy - 21} V{cy + 2} Q{cx + 24} {cy + 24} {cx} {cy + 34} Q{cx - 24} {cy + 24} {cx - 24} {cy + 2} V{cy - 21} Z" '
             f'fill="{t.SURFACE}" stroke="{t.A1}" stroke-width="2.2"/>'
             f'<path d="M{cx - 9} {cy + 2} l6 7 13 -15" fill="none" stroke="{t.GREEN}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    threats = [(-160, -40, "lateral move"), (170, -30, "deepfake"), (-150, 50, "scam call"), (160, 52, "sensor spoof")]
    cyc = 8
    for i, (dx, dy, lab) in enumerate(threats):
        a, b = i * 2 / cyc, (i * 2 + 1) / cyc
        sx, sy = cx + dx, cy + dy
        ang = math.atan2(dy, dx)
        hx, hy = cx + 30 * math.cos(ang), cy + 30 * math.sin(ang)
        o.append(f'<circle r="4" fill="{RED}" opacity="0"><animateMotion path="M{sx:.0f},{sy:.0f} L{hx:.0f},{hy:.0f}" keyPoints="0;0;1;1" keyTimes="0;{a:.3f};{b:.3f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{a:.3f};{a + .01:.3f};{b:.3f};{b + .01:.3f};1" dur="{cyc}s" repeatCount="indefinite"/></circle>')
        # impact ring + explanation label
        o.append(f'<circle cx="{hx:.0f}" cy="{hy:.0f}" r="4" fill="none" stroke="{t.A3}" stroke-width="2" opacity="0">'
                 f'<animate attributeName="r" values="4;4;18;18" keyTimes="0;{b:.3f};{b + .06:.3f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{b:.3f};{b + .005:.3f};{b + .06:.3f};1" dur="{cyc}s" repeatCount="indefinite"/></circle>')
        lx = cx + (dx * .62)
        ly = cy + dy * .9 + (4 if dy > 0 else -2)
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{b:.3f};{b + .01:.3f};{b + .2:.3f};{b + .22:.3f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<rect x="{lx - 46:.0f}" y="{ly - 11:.0f}" width="92" height="17" rx="8.5" fill="{t.SURFACE}" stroke="{t.A3}" stroke-opacity=".7"/>'
                 f'<text x="{lx:.0f}" y="{ly + 1:.0f}" class="mono" font-size="9" fill="{t.A3}" text-anchor="middle">caught: {lab}</text></g>')
    return "".join(o)


def agents():
    o = []
    top, bot = 46, 112
    mid = (top + bot) / 2
    # lane with guardrails
    for y in (top, bot):
        o.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{t.A3}" stroke-width="2.5" stroke-dasharray="14 6"/>')
        o.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{t.A3}" stroke-width="6" stroke-opacity=".12"/>')
    o.append(f'<line x1="0" y1="{mid}" x2="{W}" y2="{mid}" stroke="{t.HAIRLINE}" stroke-dasharray="6 10">'
             f'<animate attributeName="stroke-dashoffset" values="0;-32" dur=".6s" repeatCount="indefinite"/></line>')
    # the agent drifts toward a rail, bumps, gets corrected
    cyc = 6
    vals = f"0 0;0 0;0 -22;0 -22;0 0;0 0;0 22;0 22;0 0;0 0"
    kts = "0;.1;.25;.3;.42;.55;.7;.75;.87;1"
    o.append(f'<g><animateTransform attributeName="transform" type="translate" values="{vals}" keyTimes="{kts}" dur="{cyc}s" repeatCount="indefinite" calcMode="spline" '
             f'keySplines="{";".join([".4 0 .6 1"] * 9)}"/>'
             f'<g transform="translate({W / 2 - 22} {mid - 13})">'
             f'<rect width="44" height="26" rx="8" fill="{t.RAISED}" stroke="{t.A1}" stroke-width="1.6"/>'
             f'<circle cx="14" cy="13" r="3.4" fill="{t.A3}"/><circle cx="30" cy="13" r="3.4" fill="{t.A3}"/>'
             f'<line x1="22" y1="0" x2="22" y2="-6" stroke="{t.A1}"/><circle cx="22" cy="-7" r="2" fill="{t.A1}"/></g></g>')
    for y, kt0 in ((top, .25), (bot, .7)):  # sparks + the rule that gets written
        o.append(f'<circle cx="{W / 2}" cy="{y}" r="3" fill="{t.A3}" opacity="0">'
                 f'<animate attributeName="r" values="3;3;14;14" keyTimes="0;{kt0:.2f};{kt0 + .08:.2f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{kt0:.2f};{kt0 + .01:.2f};{kt0 + .08:.2f};1" dur="{cyc}s" repeatCount="indefinite"/></circle>')
    rules = ["rule #12: never force-push main", "rule #13: run tests before commit"]
    for i, r in enumerate(rules):
        a = .27 + i * .45
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{a:.2f};{a + .02:.2f};{a + .2:.2f};{a + .23:.2f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<rect x="{W / 2 - 96}" y="{(16 if i == 0 else 122)}" width="192" height="19" rx="9.5" fill="{t.SURFACE}" stroke="{t.GREEN}" stroke-opacity=".7"/>'
                 f'<text x="{W / 2}" y="{(29 if i == 0 else 135)}" class="mono" font-size="9.5" fill="{t.GREEN}" text-anchor="middle">✓ {r}</text></g>')
    return "".join(o)


def products(names):
    o = []
    cyc = 9
    rnd = random.Random(4)
    for i, name in enumerate(names[:3]):
        x, y = 40 + i * 92, 20 + i * 14
        a = .05 + i * .18
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{a:.2f};{a + .03:.2f};.92;1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 20;0 20;0 0;0 0" keyTimes="0;{a:.2f};{a + .06:.2f};1" dur="{cyc}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.2 .8 .2 1;0 0 1 1"/>'
                 f'<rect x="{x}" y="{y}" width="150" height="96" rx="9" fill="{t.SURFACE}" stroke="{t.RINGS[2]}" stroke-opacity=".7"/>'
                 f'<rect x="{x}" y="{y}" width="150" height="18" rx="9" fill="{t.RAISED}"/><rect x="{x}" y="{y + 9}" width="150" height="9" fill="{t.RAISED}"/>'
                 + "".join(f'<circle cx="{x + 11 + k * 9}" cy="{y + 9}" r="2.6" fill="{c}"/>' for k, c in enumerate((RED, t.A3, t.GREEN)))
                 + f'<text x="{x + 44}" y="{y + 12.5}" class="mono" font-size="8" fill="{t.TEXT3}">{escape(name.lower())}.app</text>'
                 + "".join(f'<rect x="{x + 12}" y="{y + 28 + k * 12}" width="{rnd.randint(60, 120)}" height="5" rx="2.5" fill="{t.HAIRLINE}"/>' for k in range(3))
                 + f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;{a + .1:.2f};{a + .11:.2f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<rect x="{x + 96}" y="{y + 70}" width="44" height="16" rx="8" fill="{t.GREEN}" fill-opacity=".15" stroke="{t.GREEN}"/>'
                 f'<circle cx="{x + 105}" cy="{y + 78}" r="2.6" fill="{t.GREEN}"><animate attributeName="opacity" values="1;.3;1" dur="1.2s" repeatCount="indefinite"/></circle>'
                 f'<text x="{x + 123}" y="{y + 81.5}" class="mono" font-size="8.5" font-weight="700" fill="{t.GREEN}" text-anchor="middle">LIVE</text></g></g>')
    # a cursor that clicks each launch
    pts = ";".join(f"{40 + i * 92 + 118} {20 + i * 14 + 78}" for i in range(3))
    o.append(f'<g><animateTransform attributeName="transform" type="translate" values="{W - 30} {SH - 20};{pts};{W - 30} {SH - 20}" keyTimes="0;.12;.3;.48;1" dur="{cyc}s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/>'
             f'<path d="M0 0 L0 15 L4 11 L7 18 L10 17 L7 10 L12 10 Z" fill="{t.TEXT}" stroke="{t.CANVAS}"/></g>')
    return "".join(o)


def main():
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.json"), encoding="utf-8"))
    rp = common.repos(USER)
    live = sum(1 for r in rp if (r.get("homepage") or "").strip())
    sec = sum(1 for f in cfg["featured"] if f.get("category") == "security")
    panels = [
        ("security", "Security that shows its work", "01 · DETECTION", f"{sec} featured systems · every alert explained", t.A1, security(),
         "Security that shows its work: a shield catches incoming threats and labels each one, a lateral move, a deepfake, a scam call, a spoofed sensor."),
        ("agents", "Tools for the AI-agent era", "02 · GUARDRAILS", "mistakes become rules · repeats measured", t.A3, agents(),
         "Tools for the AI-agent era: an AI agent drifts toward the edge of its lane, a guardrail bounces it back and a new rule is written."),
        ("products", "Products that ship", "03 · LIVE", f"{live} live sites, open them today", t.RINGS[2], products(["HireOS", "AlgoVerse", "Overrank"]),
         "Products that ship: three app windows, HireOS, AlgoVerse and Overrank, launch one after another and go live."),
    ]
    for key, title, kicker, stat, col, scene, alt in panels:
        with open(os.path.join(OUTDIR, f"pillar-{key}.svg"), "w", encoding="utf-8") as f:
            f.write(frame(key, title, kicker, stat, col, scene, alt))
    print(f"wrote {len(panels)} pillar panels ({live} live sites)")


if __name__ == "__main__":
    main()
