#!/usr/bin/env python3
"""assets/div-*.svg: the section dividers (the hero lives in hero.py)."""
import sys
from xml.sax.saxutils import escape

import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "assets"
W = 830
NAME = "Kaushik"
ROLES = ["Full-stack developer.", "Security tinkerer.", "I build things, then I break them."]

DIVIDERS = [  # (file, number, label, act)
    ("div-pillars", "01", "What I build", "WORK"),
    ("div-builds", "02", "Featured builds", "WORK"),
    ("div-dossier", "03", "Operator dossier", "ACTIVITY"),
    ("div-launch", "04", "Launch log", "ACTIVITY"),
    ("div-vote", "05", "You decide: what I build next", "INTERACTIVE"),
    ("div-galaxy", "06", "Contribution galaxy", "INTERACTIVE"),
    ("div-badge", "07", "My badge", "INTERACTIVE"),
    ("div-ctf", "08", "Intercepted transmission", "INTERACTIVE"),
]


def divider(num, label, act=""):
    H = 44
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(label)}">',
        f"<title>{escape(label)}</title>",
        t.defs('<clipPath id="bar"><rect width="830" height="44" rx="12"/></clipPath>'),
        f'<g clip-path="url(#bar)"><rect width="{W}" height="{H}" fill="{t.SURFACE}"/>',
        f'<rect width="{W}" height="{H}" fill="url(#aurora)" opacity=".07"/>',
        f'<rect width="4" height="{H}" fill="url(#auroraV)"/>',
        f'<rect x="-120" width="120" height="{H}" fill="url(#aurora)" opacity=".16"><animate attributeName="x" values="-120;{W};{W}" keyTimes="0;.55;1" dur="9s" repeatCount="indefinite"/></rect></g>',
        f'<text x="24" y="27" class="mono" font-size="12" fill="{t.A2}">{num}</text>',
        f'<text x="54" y="28" font-size="{t.T_HEAD + 2}" font-weight="600" fill="{t.TEXT}">{escape(label)}</text>',
        f'<text x="{W - 22}" y="27" class="label" text-anchor="end" style="fill:{t.TEXT3}">{escape(act)}</text>' if act else "",
        t.card_border(W, H, 12),
        "</svg>"])


def main():
    for fn, num, label, act in DIVIDERS:
        with open(f"{OUTDIR}/{fn}.svg", "w", encoding="utf-8") as f:
            f.write(divider(num, label, act))
    print(f"wrote {len(DIVIDERS)} dividers")


if __name__ == "__main__":
    main()
