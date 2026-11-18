#!/usr/bin/env python3
"""assets/ctf.svg: the intercepted-transmission panel above the CTF.

A radio scanner hunts the band and locks onto a signal; the decryption pipeline shows
three stages, only the first one public; the flag sits redacted, its letters churning.
The solver count and first blood come from ctf/solvers.json, so the panel updates when
someone cracks it. Holds no part of stages 2-3 or the flag. No network. Pure SMIL.
Usage: ctf_panel.py [out]
"""
import json
import math
import os
import random
import sys
from xml.sax.saxutils import escape

import theme as t

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "ctf.svg")
W, H = 830, 300
RED, GOLD, OK = t.BEACON[0], t.A3, t.GREEN


def main():
    try:
        solvers = json.load(open(os.path.join(HERE, "..", "ctf", "solvers.json"), encoding="utf-8"))
    except (OSError, ValueError):
        solvers = []
    n = len(solvers)
    rnd = random.Random(1337)
    alt = (f"Intercepted transmission: a radio scanner locks onto a signal, and a three-stage decryption pipeline leads to a redacted flag. "
           f"{n} operator{'s have' if n != 1 else ' has'} cracked it so far.")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
         "<title>Intercepted transmission</title>",
         t.defs(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
                '<clipPath id="scope"><rect x="28" y="64" width="330" height="150" rx="10"/></clipPath>'
                '<pattern id="sgrid" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#5af0c0" stroke-opacity=".08"/></pattern>'
                '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".3"/></pattern>'),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="{t.CANVAS}"/>']

    # background: faint hex noise drifting down
    for c in range(26):
        x = 12 + c * 32
        col = "".join(f'<tspan x="{x}" dy="14">{rnd.choice("0123456789abcdef")}{rnd.choice("0123456789abcdef")}</tspan>' for _ in range(40))
        dur = rnd.uniform(14, 30)
        o.append(f'<text class="mono" font-size="9" fill="{OK}" opacity=".07" y="-560">{col}'
                 f'<animateTransform attributeName="transform" type="translate" values="0 0;0 560" dur="{dur:.0f}s" begin="-{rnd.uniform(0, dur):.0f}s" repeatCount="indefinite"/></text>')

    # header
    o.append(f'<circle cx="30" cy="32" r="4" fill="{RED}"><animate attributeName="opacity" values="1;.15;1" dur="1s" repeatCount="indefinite"/></circle>'
             f'<text x="42" y="36" class="mono" font-size="11" font-weight="700" letter-spacing="2" fill="{t.TEXT}">SIGNAL INTERCEPTED</text>'
             f'<text x="{W - 28}" y="36" class="mono" font-size="10" fill="{t.TEXT3}" text-anchor="end">origin: this profile · encryption: 3 layers · status: UNSOLVED by you</text>'
             f'<line x1="28" y1="48" x2="{W - 28}" y2="48" stroke="{t.HAIRLINE}"/>')

    # ---------- left: the scanner ----------
    sx, sy, sw, sh = 28, 64, 330, 150
    mid = sy + sh / 2
    CYC = 10
    o.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="10" fill="#03110c" stroke="{OK}" stroke-opacity=".35"/>'
             f'<g clip-path="url(#scope)"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#sgrid)"/>')

    def wave(amp, period, jitter, phase=0.0):
        pts = []
        for i in range(0, sw * 2 + period, 3):
            y = mid + amp * math.sin(2 * math.pi * (i / period) + phase) + rnd.uniform(-jitter, jitter)
            pts.append(f"{sx + i - sw},{y:.1f}")
        return "M" + " L".join(pts)
    # noise while scanning, a clean carrier once locked
    o.append(f'<path d="{wave(10, 18, 22)}" fill="none" stroke="{OK}" stroke-width="1.2" opacity=".8">'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;{sw} 0" dur="1.2s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".8;.8;0;0;.8" keyTimes="0;.45;.5;.95;1" dur="{CYC}s" repeatCount="indefinite"/></path>')
    o.append(f'<path d="{wave(34, 66, 1.5)}" fill="none" stroke="{OK}" stroke-width="2" opacity="0">'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;{66 * 5} 0" dur="2.2s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.45;.5;.95;1" dur="{CYC}s" repeatCount="indefinite"/></path>')
    o.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#scan)"/></g>')
    # frequency readout: tunes through the band, then locks
    freqs = ["088.40", "101.25", "117.90", "126.05", "133.70", "144.21"]
    for i, f in enumerate(freqs):
        a = i * .08
        b = a + .08 if i < len(freqs) - 1 else .95
        locked = i == len(freqs) - 1
        o.append(f'<text x="{sx + 14}" y="{sy + sh + 26}" class="mono" font-size="14" font-weight="700" fill="{OK if locked else t.TEXT2}" opacity="0">{f} MHz'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{a:.3f};{a + .001:.3f};{b:.3f};{b + .001:.3f};1" dur="{CYC}s" repeatCount="indefinite"/></text>')
    o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.45;.46;.95;1" dur="{CYC}s" repeatCount="indefinite"/>'
             f'<rect x="{sx + 140}" y="{sy + sh + 12}" width="84" height="20" rx="10" fill="none" stroke="{OK}"/>'
             f'<text x="{sx + 182}" y="{sy + sh + 26}" class="mono" font-size="10.5" font-weight="700" fill="{OK}" text-anchor="middle">LOCKED</text></g>'
             f'<g><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;.45;.46;.95;1" dur="{CYC}s" repeatCount="indefinite"/>'
             f'<text x="{sx + 140}" y="{sy + sh + 26}" class="mono" font-size="10.5" fill="{GOLD}">scanning<tspan>...<animate attributeName="opacity" values="1;0;1" dur=".8s" repeatCount="indefinite"/></tspan></text></g>')
    # signal-strength bars
    for i in range(6):
        h = 4 + i * 3
        o.append(f'<rect x="{sx + sw - 70 + i * 10}" y="{sy + sh + 30 - h}" width="6" height="{h}" rx="1" fill="{OK}" opacity=".2">'
                 f'<animate attributeName="opacity" values=".2;{.2 + .15 * (i % 3)};1;1;.2" keyTimes="0;.3;.5;.95;1" dur="{CYC}s" repeatCount="indefinite"/></rect>')

    # ---------- right: the decryption pipeline ----------
    px = 400
    stages = [("STAGE 1", "base64", "public · in the README", OK, True),
              ("STAGE 2", "? ? ?", "find it to know it", GOLD, False),
              ("STAGE 3", "? ? ?", "the last lock", RED, False)]
    ny = 96
    for i, (lab, enc, sub, col, open_) in enumerate(stages):
        x = px + i * 140
        o.append(f'<rect x="{x}" y="{ny - 30}" width="124" height="72" rx="10" fill="{t.SURFACE}" stroke="{col}" stroke-opacity="{.9 if open_ else .5}"'
                 + (' stroke-dasharray="4 4"' if not open_ else "") + '/>'
                 f'<text x="{x + 12}" y="{ny - 12}" class="mono" font-size="9.5" letter-spacing="1.5" fill="{col}">{lab}</text>'
                 f'<text x="{x + 12}" y="{ny + 10}" class="mono" font-size="15" font-weight="700" fill="{t.TEXT}">{enc}</text>'
                 f'<text x="{x + 12}" y="{ny + 30}" font-size="9.5" fill="{t.TEXT3}">{sub}</text>')
        if open_:
            o.append(f'<text x="{x + 112}" y="{ny - 11}" font-size="11" fill="{OK}" text-anchor="end">✓</text>')
        else:  # padlock
            lx, ly = x + 104, ny - 22
            o.append(f'<path d="M{lx} {ly + 6} v-3 a4 4 0 0 1 8 0 v3" fill="none" stroke="{col}" stroke-width="1.5"/>'
                     f'<rect x="{lx - 2}" y="{ly + 6}" width="12" height="9" rx="2" fill="{col}"/>')
        if i < 2:
            o.append(f'<line x1="{x + 124}" y1="{ny + 6}" x2="{x + 140}" y2="{ny + 6}" stroke="{t.HAIRLINE}" stroke-width="2"/>')
    # a packet that travels the pipeline and bounces off each lock
    path = f"M{px + 10},{ny + 46} H{px + 400}"
    o.append(f'<path d="{path}" stroke="{t.HAIRLINE}" stroke-dasharray="2 5"/>'
             f'<circle r="4" fill="{OK}"><animateMotion path="{path}" keyPoints="0;.33;.3;.33;.66;.63;.66;1;1" keyTimes="0;.2;.25;.3;.5;.55;.6;.85;1" dur="7s" repeatCount="indefinite"/>'
             f'<animate attributeName="fill" values="{OK};{OK};{GOLD};{GOLD};{RED};{RED}" keyTimes="0;.3;.31;.6;.61;1" dur="7s" repeatCount="indefinite"/></circle>')

    # the flag: shape known, contents churning
    fy = ny + 92
    o.append(f'<text x="{px}" y="{fy - 16}" class="mono" font-size="9.5" letter-spacing="1.5" fill="{t.TEXT3}">PAYLOAD</text>'
             f'<rect x="{px}" y="{fy - 8}" width="404" height="38" rx="8" fill="{t.SURFACE}" stroke="{GOLD}" stroke-opacity=".5"/>'
             f'<text x="{px + 14}" y="{fy + 17}" class="mono" font-size="16" font-weight="700" fill="{GOLD}">KAUSHIK{{</text>')
    glyph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789#$%&"
    for j in range(14):
        frames = ";".join(str(k) for k in range(4))
        cx = px + 104 + j * 15
        for k in range(4):
            o.append(f'<text x="{cx}" y="{fy + 17}" class="mono" font-size="16" font-weight="700" fill="{t.TEXT2}" opacity="0">{escape(rnd.choice(glyph))}'
                     f'<animate attributeName="opacity" values="{";".join("1" if q == k else "0" for q in range(4))}" calcMode="discrete" dur="{.4 + j % 3 * .1:.1f}s" repeatCount="indefinite"/></text>')
    o.append(f'<text x="{px + 104 + 14 * 15}" y="{fy + 17}" class="mono" font-size="16" font-weight="700" fill="{GOLD}">}}</text>'
             f'<rect x="{px + 104 + 14 * 15 + 14}" y="{fy + 3}" width="9" height="16" fill="{GOLD}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect>')

    # footer: the scoreboard
    first = solvers[0] if solvers else None
    score = (f"{n} operator{'s' if n != 1 else ''} cracked it" + (f" · first blood @{first['login']} ({first['date']})" if first else " · first blood is still up for grabs"))
    o.append(f'<line x1="28" y1="{H - 34}" x2="{W - 28}" y2="{H - 34}" stroke="{t.HAIRLINE}"/>'
             f'<text x="28" y="{H - 14}" class="mono" font-size="10.5" fill="{t.TEXT2}"><tspan fill="{GOLD}">◆</tspan> {escape(score)}</text>'
             f'<text x="{W - 28}" y="{H - 14}" class="mono" font-size="10.5" font-weight="700" fill="{OK}" text-anchor="end">YOUR MOVE ▶'
             f'<animate attributeName="opacity" values="1;.35;1" dur="1.4s" repeatCount="indefinite"/></text>')
    o += ["</g>", t.card_border(W, H), "</svg>"]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("".join(o))
    print(f"wrote {OUT}: {n} solvers")


if __name__ == "__main__":
    main()
