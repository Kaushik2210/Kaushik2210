#!/usr/bin/env python3
"""assets/proof.svg: the proof strip, five headline numbers straight under the hero.

Live sites, repositories, commits this year, best streak, years on GitHub, all from
the GitHub API. Tiles rise in one by one and a soft shine passes across the strip.
Pure SMIL, no JavaScript.
"""
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/proof.svg"
W, H = 830, 138


def main():
    u = common.user_graph(USER)
    rp = common.repos(USER)
    cc = u["contributionsCollection"]
    _, longest = common.streaks(common.days(u))
    live = sum(1 for r in rp if (r.get("homepage") or "").strip())
    years = (datetime.now(timezone.utc) - datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))).days / 365.25
    tiles = [
        (f"{live}", "LIVE SITES", "deployed and running"),
        (f"{len(rp)}", "REPOSITORIES", "built, not forked"),
        (f"{cc['totalCommitContributions']:,}", "COMMITS THIS YEAR", "last 12 months"),
        (f"{longest}", "BEST STREAK", "days in a row"),
        (f"{years:.1f}", "YEARS BUILDING", "on GitHub"),
    ]
    alt = "Proof strip: " + "; ".join(f"{v} {l.lower()}" for v, l, _ in tiles) + "."
    cw = (W - 32) / len(tiles)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
         f"<title>{escape(USER)}: proof</title>",
         t.defs(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
                f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="{t.SURFACE}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#aurora)" opacity=".05"/>']
    for i, (val, lab, sub) in enumerate(tiles):
        cx = 16 + i * cw + cw / 2
        d = 0.15 + i * 0.12
        grp = (f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".6s" begin="{d:.2f}s" fill="freeze"/>'
               f'<animateTransform attributeName="transform" type="translate" values="0 10;0 0" dur=".6s" begin="{d:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/>'
               f'<text x="{cx:.0f}" y="76" font-size="44" font-weight="800" letter-spacing="-1.5" text-anchor="middle" fill="url(#aurora)">{escape(val)}</text>'
               f'<text x="{cx:.0f}" y="100" class="label" text-anchor="middle" style="fill:{t.TEXT2};font-size:10px">{lab}</text>'
               f'<text x="{cx:.0f}" y="116" font-size="11" text-anchor="middle" fill="{t.TEXT3}">{sub}</text></g>')
        o.append(grp)
        if i:
            o.append(f'<line x1="{16 + i * cw:.0f}" y1="30" x2="{16 + i * cw:.0f}" y2="{H - 30}" stroke="{t.HAIRLINE}"/>')
    o.append(f'<rect x="-160" y="0" width="160" height="{H}" fill="url(#shine)" transform="skewX(-16)"><animate attributeName="x" values="-200;{W + 80};{W + 80}" keyTimes="0;.35;1" dur="9s" begin="1s" repeatCount="indefinite"/></rect>')
    o.append(f'<rect x="0" y="0" width="{W}" height="3" fill="url(#aurora)"/>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: " + ", ".join(f"{v} {l.lower()}" for v, l, _ in tiles))


if __name__ == "__main__":
    main()
