#!/usr/bin/env python3
"""assets/header.svg + assets/div-*.svg: the profile header and section dividers.

Header: glyph rain, a glitching name, cycling role lines, a live "last seen"
readout and an ECG pulse. Everything is SMIL, so it animates inside <img>.
"""
import random
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "assets"
W = 830
GREEN, CYAN, MAG = "#00ff41", "#19f9ff", "#ff2bd6"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
GLYPHS = "01ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ{}<>/\\|=+*#$%&"

DIVIDERS = [  # (file, number, label)
    ("div-dossier", "01", "OPERATOR.DOSSIER"),
    ("div-radar", "02", "THREAT.RADAR"),
    ("div-galaxy", "03", "CONTRIBUTION.GALAXY"),
    ("div-ctf", "04", "INTERCEPTED.TRANSMISSION"),
    ("div-arsenal", "05", "ARSENAL"),
]


def header(last):
    H = 300
    rnd = random.Random(2210)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="{escape(USER)}: developer and security tinkerer">',
         f"<title>{escape(USER)}</title>",
         f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#050a07"/><stop offset=".55" stop-color="#06180d"/><stop offset="1" stop-color="#050a07"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#050a07" stop-opacity="1"/><stop offset=".35" stop-color="#050a07" stop-opacity="0"/><stop offset=".7" stop-color="#050a07" stop-opacity="0"/><stop offset="1" stop-color="#050a07" stop-opacity="1"/></linearGradient>
<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="clip"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<style>text{{font-family:{FONT}}}</style></defs>
<g clip-path="url(#clip)"><rect width="{W}" height="{H}" fill="url(#bg)"/>"""]

    # faint grid
    for x in range(0, W, 40):
        o.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#0f3d22" stroke-opacity=".35"/>')
    for y in range(0, H, 40):
        o.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#0f3d22" stroke-opacity=".35"/>')

    # glyph rain: one falling column per slot
    for i in range(0, W, 18):
        n = rnd.randint(8, 16)
        dur = rnd.uniform(5, 11)
        off = rnd.uniform(0, dur)
        chars = [rnd.choice(GLYPHS) for _ in range(n)]
        tsp = "".join(
            f'<tspan x="{i + 6}" dy="14" fill="{"#d6ffe0" if k == n - 1 else GREEN}" '
            f'fill-opacity="{0.08 + 0.55 * (k / n) ** 2:.2f}">{escape(c)}</tspan>' for k, c in enumerate(chars))
        o.append(f'<text font-size="13" y="-{n * 14}">{tsp}'
                 f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {H + n * 14 + 20}" '
                 f'dur="{dur:.1f}s" begin="-{off:.1f}s" repeatCount="indefinite"/></text>')
    o.append(f'<rect width="{W}" height="{H}" fill="url(#fade)"/>')

    # name with chromatic glitch
    name = USER.upper().rstrip("0123456789")
    cx, y = W / 2, 150
    for col, dx, delay, op in ((MAG, 4, "0", .8), (CYAN, -4, ".15", .8)):
        o.append(f'<text x="{cx}" y="{y}" font-size="92" font-weight="bold" fill="{col}" fill-opacity="{op}" '
                 f'text-anchor="middle" textLength="560" lengthAdjust="spacingAndGlyphs">{name}'
                 f'<animateTransform attributeName="transform" type="translate" '
                 f'values="0 0;0 0;{dx} 0;{-dx} -2;{dx*2} 1;0 0;0 0" keyTimes="0;.88;.89;.91;.93;.95;1" dur="6s" '
                 f'begin="{delay}s" repeatCount="indefinite"/></text>')
    o.append(f'<text x="{cx}" y="{y}" font-size="92" font-weight="bold" fill="#eafff0" text-anchor="middle" '
             f'textLength="560" lengthAdjust="spacingAndGlyphs" filter="url(#glow)">{name}</text>')
    o.append(f'<text x="{cx + 290}" y="{y - 56}" font-size="20" fill="{GREEN}" font-weight="bold">2210</text>')

    # cycling roles
    roles = ["FULL-STACK DEVELOPER", "SECURITY TINKERER", "I BUILD THINGS. THEN I BREAK THEM."]
    cyc = 4.0 * len(roles)
    for i, r in enumerate(roles):
        a, b = i / len(roles), (i + 1) / len(roles)
        kt = f"0;{a:.3f};{a + .02:.3f};{b - .03:.3f};{b - .01:.3f};1" if i else f"0;0;.02;{b - .03:.3f};{b - .01:.3f};1"
        o.append(f'<text x="{cx}" y="198" font-size="19" fill="{GREEN}" text-anchor="middle" letter-spacing="4" opacity="0">'
                 f'&#9656; {escape(r)} <tspan fill="#eafff0">_</tspan>'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" dur="{cyc}s" repeatCount="indefinite"/></text>')

    # ECG pulse along the bottom
    ecg = "M0,252 L220,252 L240,252 L252,230 L264,276 L278,214 L292,252 L330,252 L560,252 L580,252 L592,236 L604,268 L616,252 L830,252"
    o.append(f'<path d="{ecg}" fill="none" stroke="#0f5d2c" stroke-width="1.5"/>')
    o.append(f'<path d="{ecg}" fill="none" stroke="{GREEN}" stroke-width="2" filter="url(#glow)" pathLength="100" '
             f'stroke-dasharray="9 91" stroke-linecap="round"><animate attributeName="stroke-dashoffset" '
             f'from="100" to="0" dur="3.2s" repeatCount="indefinite"/></path>')

    # status bar
    o.append(f'<rect x="0" y="268" width="{W}" height="32" fill="#04120a" fill-opacity=".9"/>')
    o.append(f'<line x1="0" y1="268" x2="{W}" y2="268" stroke="#0f5d2c"/>')
    o.append(f'<circle cx="24" cy="284" r="4" fill="{GREEN}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    o.append(f'<text x="38" y="288" font-size="12" fill="#c9d1d9">ONLINE &#183; <tspan fill="{GREEN}">@{escape(USER)}</tspan> &#183; Bangalore, IN</text>')
    o.append(f'<text x="{W - 20}" y="288" font-size="12" fill="#7d8590" text-anchor="end">LAST SEEN: '
             f'<tspan fill="#c9d1d9">{escape(last)}</tspan></text>')
    o.append("</g>")
    o.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="#0f5d2c"/>')
    o.append("</svg>")
    return "\n".join(o)


def divider(num, label):
    H = 56
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(label)}">',
         f"<title>{escape(label)}</title>",
         f'<defs><filter id="g" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/>'
         f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><style>text{{font-family:{FONT}}}</style></defs>',
         f'<text x="2" y="26" font-size="13" fill="#0f8f3f">{num} //</text>',
         f'<text x="40" y="27" font-size="21" font-weight="bold" fill="{GREEN}" filter="url(#g)">{escape(label)}</text>',
         f'<line x1="0" y1="42" x2="{W}" y2="42" stroke="#0f3d22"/>',
         f'<line x1="0" y1="42" x2="{W}" y2="42" stroke="{GREEN}" stroke-width="2" stroke-dasharray="60 {W}" filter="url(#g)">'
         f'<animate attributeName="stroke-dashoffset" from="60" to="{-W}" dur="4s" repeatCount="indefinite"/></line>',
         f'<rect x="0" y="39" width="6" height="6" fill="{GREEN}"/><rect x="{W - 6}" y="39" width="6" height="6" fill="{GREEN}"/>',
         "</svg>"]
    return "\n".join(o)


def main():
    rp = sorted(common.repos(USER), key=lambda r: r["pushed_at"], reverse=True)
    now = datetime.now(timezone.utc)
    d = (now - datetime.fromisoformat(rp[0]["pushed_at"].replace("Z", "+00:00"))).days
    last = f'{rp[0]["name"][:22]} ({"today" if d == 0 else f"{d}d ago"})'
    with open(f"{OUTDIR}/header.svg", "w", encoding="utf-8") as f:
        f.write(header(last))
    for fn, num, label in DIVIDERS:
        with open(f"{OUTDIR}/{fn}.svg", "w", encoding="utf-8") as f:
            f.write(divider(num, label))
    print("wrote header + dividers; last seen:", last)


if __name__ == "__main__":
    main()
