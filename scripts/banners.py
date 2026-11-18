#!/usr/bin/env python3
"""assets/div-*.svg: the section dividers, drawn as level banners (the hero lives in hero.py).

Each banner has its own animated emblem, a title that types itself in, and a level track
on the right that shows where you are on the page (01-06). Pure SMIL + CSS, no JavaScript.
"""
import sys
from xml.sax.saxutils import escape

import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "assets"
W, H = 830, 56
NAME = "Kaushik"
ROLES = ["Full-stack developer.", "Security tinkerer.", "I build things, then I break them."]

DIVIDERS = [  # (file, number, label, act, emblem)
    ("div-pillars", "01", "What I build", "WORK", "pillars"),
    ("div-builds", "02", "Mission select: every project, in action", "WORK", "ship"),
    ("div-dossier", "03", "Operator dossier", "ACTIVITY", "scan"),
    ("div-launch", "04", "Launch log", "ACTIVITY", "rocket"),
    ("div-badge", "05", "My badge", "INTERACTIVE", "badge"),
    ("div-ctf", "06", "Intercepted transmission", "INTERACTIVE", "lock"),
]
ACT_COL = {"WORK": t.A1, "ACTIVITY": t.A2, "INTERACTIVE": t.A3}


def emblem(kind, col, cx, cy):
    """A tiny looping animation that says what the section is."""
    if kind == "pillars":
        return "".join(f'<rect x="{cx - 11 + i * 8}" y="{cy + 10}" width="5" height="0" rx="1" fill="{col}">'
                       f'<animate attributeName="height" values="0;{10 + i * 5};{10 + i * 5};0" keyTimes="0;.3;.85;1" dur="3s" begin="{i * .2}s" repeatCount="indefinite"/>'
                       f'<animate attributeName="y" values="{cy + 10};{cy - i * 5};{cy - i * 5};{cy + 10}" keyTimes="0;.3;.85;1" dur="3s" begin="{i * .2}s" repeatCount="indefinite"/></rect>'
                       for i in range(3))
    if kind == "ship":
        return (f'<g><animateTransform attributeName="transform" type="translate" values="0 2;0 -2;0 2" dur="1.6s" repeatCount="indefinite"/>'
                f'<path d="M{cx + 9} {cy} L{cx - 7} {cy - 7} L{cx - 3} {cy} L{cx - 7} {cy + 7} Z" fill="{t.TEXT}" stroke="{col}" stroke-width="1"/>'
                f'<path d="M{cx - 5} {cy - 2} L{cx - 13} {cy} L{cx - 5} {cy + 2} Z" fill="{t.A3}"><animate attributeName="opacity" values="1;.3;1" dur=".2s" repeatCount="indefinite"/></path></g>'
                + "".join(f'<line x1="{cx + 14}" y1="{cy - 8 + i * 8}" x2="{cx + 18}" y2="{cy - 8 + i * 8}" stroke="{col}" stroke-opacity=".6">'
                          f'<animateTransform attributeName="transform" type="translate" values="0 0;-34 0" dur=".9s" begin="{i * .3}s" repeatCount="indefinite"/></line>' for i in range(3)))
    if kind == "scan":
        rings = "".join(f'<path d="M{cx - r} {cy + 4} a{r} {r + 2} 0 0 1 {2 * r} 0" fill="none" stroke="{col}" stroke-opacity=".7" stroke-width="1.3"/>' for r in (3, 6, 9, 12))
        return (rings + f'<rect x="{cx - 14}" y="{cy - 12}" width="28" height="2" fill="{t.GREEN}" opacity=".9">'
                f'<animate attributeName="y" values="{cy - 12};{cy + 12};{cy - 12}" dur="2s" repeatCount="indefinite"/></rect>')
    if kind == "rocket":
        return (f'<g><animateTransform attributeName="transform" type="translate" values="0 6;0 -3;0 6" dur="2.4s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".4 0 .6 1;.4 0 .6 1"/>'
                f'<path d="M{cx} {cy - 13} C{cx + 6} {cy - 7} {cx + 5} {cy + 3} {cx + 4} {cy + 6} H{cx - 4} C{cx - 5} {cy + 3} {cx - 6} {cy - 7} {cx} {cy - 13} Z" fill="{t.TEXT}"/>'
                f'<circle cx="{cx}" cy="{cy - 4}" r="2" fill="{col}"/>'
                f'<path d="M{cx - 3} {cy + 7} L{cx} {cy + 14} L{cx + 3} {cy + 7} Z" fill="{t.BEACON[0]}"><animate attributeName="opacity" values="1;.4;1" dur=".25s" repeatCount="indefinite"/></path></g>')
    if kind == "badge":
        return (f'<g><animateTransform attributeName="transform" type="rotate" values="-10 {cx} {cy - 14};10 {cx} {cy - 14};-10 {cx} {cy - 14}" dur="2.6s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>'
                f'<line x1="{cx}" y1="{cy - 14}" x2="{cx}" y2="{cy - 8}" stroke="{col}" stroke-width="1.5"/>'
                f'<rect x="{cx - 8}" y="{cy - 8}" width="16" height="20" rx="3" fill="{t.RAISED}" stroke="{col}" stroke-width="1.4"/>'
                f'<circle cx="{cx}" cy="{cy - 1}" r="3.2" fill="{col}"/><rect x="{cx - 5}" y="{cy + 5}" width="10" height="2" rx="1" fill="{t.TEXT3}"/></g>')
    # lock: a padlock whose shackle pops open, then snaps shut
    return (f'<path d="M{cx - 5} {cy - 1} v-4 a5 5 0 0 1 10 0 v4" fill="none" stroke="{col}" stroke-width="2">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 -4;0 -4;0 0" keyTimes="0;.5;.58;.85;1" dur="3s" repeatCount="indefinite"/></path>'
            f'<rect x="{cx - 8}" y="{cy - 1}" width="16" height="12" rx="2.5" fill="{col}"/>'
            f'<circle cx="{cx}" cy="{cy + 5}" r="1.8" fill="{t.CANVAS}"/>')


def divider(num, label, act, kind):
    col = ACT_COL.get(act, t.A1)
    idx = int(num)
    tw = len(label) * 8.3 + 8               # rough title width, for the typing reveal
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(f"Section {num}: {label}")}">',
         f"<title>{escape(label)}</title>",
         t.defs(f'<clipPath id="bar"><rect width="{W}" height="{H}" rx="12"/></clipPath>'
                f'<clipPath id="type"><rect x="86" y="0" width="0" height="{H}"><animate attributeName="width" values="0;{tw + 60:.0f}" dur="{.9 + len(label) * .025:.2f}s" begin=".2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".3 0 .3 1"/></rect></clipPath>'
                '<pattern id="trace" width="40" height="56" patternUnits="userSpaceOnUse"><path d="M0 14 H14 L20 20 H40 M0 42 H24 L30 36 H40" fill="none" stroke="#fff" stroke-opacity=".035"/></pattern>'),
         f'<g clip-path="url(#bar)"><rect width="{W}" height="{H}" fill="{t.SURFACE}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#trace)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#aurora)" opacity=".06"/>',
         f'<rect width="4" height="{H}" fill="{col}"/>',
         f'<rect x="-140" width="140" height="{H}" fill="url(#aurora)" opacity=".14"><animate attributeName="x" values="-140;{W};{W}" keyTimes="0;.5;1" dur="10s" begin="{idx * .8:.1f}s" repeatCount="indefinite"/></rect>',
         # emblem tile
         f'<rect x="16" y="8" width="40" height="40" rx="10" fill="{t.CANVAS}" stroke="{col}" stroke-opacity=".55"/>',
         emblem(kind, col, 36, 28),
         f'<text x="66" y="33" class="mono" font-size="11" font-weight="700" fill="{col}">{num}</text>']
    # title: types itself in, then a cursor blinks after it
    o.append(f'<g clip-path="url(#type)"><text x="88" y="34" font-size="{t.T_HEAD + 3}" font-weight="700" fill="{t.TEXT}">{escape(label)}</text></g>')
    o.append(f'<rect x="{88 + tw - 6:.0f}" y="20" width="2.5" height="18" fill="{col}" opacity="0">'
             f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.01;.5;.51;1" dur="1s" begin="{1.1 + len(label) * .025:.2f}s" repeatCount="indefinite"/></rect>')
    o.append("</g>")
    # level track: six nodes, the current one lit, a spark running along the done part
    nx0, gap = W - 168, 24
    track_end = nx0 + 5 * gap
    o.append(f'<text x="{nx0 - 16}" y="32" class="label" text-anchor="end" style="fill:{col}">{escape(act)}</text>'
             f'<line x1="{nx0}" y1="28" x2="{track_end}" y2="28" stroke="{t.HAIRLINE}" stroke-width="2"/>'
             f'<line x1="{nx0}" y1="28" x2="{nx0 + (idx - 1) * gap}" y2="28" stroke="{col}" stroke-width="2" stroke-opacity=".7"/>')
    for k in range(6):
        x = nx0 + k * gap
        done, cur = k < idx - 1, k == idx - 1
        c = ACT_COL[DIVIDERS[k][3]]
        if cur:
            o.append(f'<circle cx="{x}" cy="28" r="8" fill="none" stroke="{col}" stroke-width="1.4">'
                     f'<animate attributeName="r" values="6;11;6" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur="1.8s" repeatCount="indefinite"/></circle>'
                     f'<rect x="{x - 5}" y="23" width="10" height="10" fill="{col}" transform="rotate(45 {x} 28)"/>')
        else:
            o.append(f'<rect x="{x - 3.5}" y="24.5" width="7" height="7" fill="{c if done else t.SURFACE}" stroke="{c}" stroke-opacity="{1 if done else .45}" transform="rotate(45 {x} 28)"/>')
    if idx > 1:
        o.append(f'<circle r="2.2" fill="#fff"><animateMotion path="M{nx0},28 H{nx0 + (idx - 1) * gap}" dur="{.5 * idx:.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="{.5 * idx:.1f}s" repeatCount="indefinite"/></circle>')
    o.append(f'<text x="{W - 16}" y="32" class="mono" font-size="9.5" fill="{t.TEXT3}" text-anchor="end">{idx}/6</text>')
    o += [t.card_border(W, H, 12), "</svg>"]
    return "\n".join(o)


def main():
    for fn, num, label, act, kind in DIVIDERS:
        with open(f"{OUTDIR}/{fn}.svg", "w", encoding="utf-8") as f:
            f.write(divider(num, label, act, kind))
    print(f"wrote {len(DIVIDERS)} dividers")


if __name__ == "__main__":
    main()
