#!/usr/bin/env python3
"""assets/dossier.svg: avatar rendered as an animated colour halftone + live readout.

The portrait is rebuilt from the real avatar on every run (Pillow). Each cell
becomes a dot sized by local brightness and tinted with the photo's own hue.
Rows pop in under a scan line, hold, fade and re-scan. Stats come straight from
the GitHub API, so there is nothing third-party to break.
"""
import colorsys
import collections
import io
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/dossier.svg"
CROP = (0.20, 0.40, 0.82, 1.0)  # head + shoulders
COLS, PITCH = 58, 6.6
W = 830
CYCLE = 24.0
GREEN = "#00ff41"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"


def portrait():
    raw = urllib.request.urlopen(urllib.request.Request(
        f"https://github.com/{USER}.png?size=460", headers={"User-Agent": "profile-gen"}), timeout=30).read()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    im = im.crop((int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h)))
    rows = round(COLS * im.height / im.width)
    im = im.resize((COLS, rows), Image.LANCZOS)
    # local contrast: judge each cell against its neighbourhood so a dark face
    # in front of a bright wall still gets the full dot-size range
    im = ImageOps.autocontrast(im, cutoff=1)
    lum = im.convert("L")
    blur = lum.filter(ImageFilter.GaussianBlur(4))
    px, lp, bp = im.load(), lum.load(), blur.load()
    for y in range(rows):
        for x in range(COLS):
            l, b = lp[x, y] / 255, bp[x, y] / 255
            adj = max(0.0, min(1.0, 0.4 * l + 0.6 * (0.5 + 2.2 * (l - b))))
            k = adj / l if l > 0.02 else 1.0
            r, g, bl = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(bl * k)))
    return im, rows


def dot(rgb):
    r, g, b = (v / 255 for v in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if lum < 0.10:
        return None
    rad = PITCH * 0.52 * min(1.0, (lum * 1.1) ** 0.6)
    r2, g2, b2 = colorsys.hsv_to_rgb(h, min(1, s * 1.3 + 0.08), 0.45 + 0.55 * min(1, lum * 1.2))
    return rad, "#%02x%02x%02x" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))


def portrait_svg(im, rows, x0, y0):
    out = []
    for y in range(rows):
        cells = []
        for x in range(COLS):
            d = dot(im.getpixel((x, y)))
            if d:
                cells.append(f'<circle cx="{x0 + x * PITCH + PITCH / 2:.1f}" cy="{y0 + y * PITCH + PITCH / 2:.1f}" '
                             f'r="{d[0]:.2f}" fill="{d[1]}"/>')
        a = (y * 0.06) / CYCLE
        out.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;.8;1;1;0;0" '
                   f'keyTimes="0;{a:.4f};{a + .005:.4f};{a + .03:.4f};{a + .05:.4f};.93;.97;1" '
                   f'dur="{CYCLE}s" repeatCount="indefinite"/>{"".join(cells)}</g>')
    return "\n".join(out)


def bar(frac, n=14):
    k = max(1, round(frac * n))
    return "█" * k + "░" * (n - k)


def main():
    u = common.user_graph(USER)
    ds = common.days(u)
    cur, longest = common.streaks(ds)
    rp = common.repos(USER)
    stars = sum(r["stargazers_count"] for r in rp)
    langs = collections.Counter(r["language"] for r in rp if r["language"])
    top = langs.most_common(4)
    tot = sum(langs.values()) or 1
    cc = u["contributionsCollection"]
    joined = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    years = (datetime.now(timezone.utc) - joined).days / 365.25

    im, rows = portrait()
    px0, py0 = 30, 62
    ph = rows * PITCH
    H = max(int(py0 + ph + 46), 530)
    tx = 452
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Halftone portrait of {escape(USER)} with live GitHub stats">',
         f"<title>OPERATOR DOSSIER // {escape(USER)}</title>",
         f"""<defs><filter id="g" x="-20%" y="-300%" width="140%" height="700%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>text{{font-family:{FONT}}}</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="#0b1015" stroke="#0f5d2c"/>
<text x="{px0}" y="36" font-size="13" fill="{GREEN}">&#9608; SUBJECT.render()</text>"""]
    # corner brackets around the portrait
    bx0, by0, bx1, by1 = px0 - 8, py0 - 8, px0 + COLS * PITCH + 8, py0 + ph + 8
    for (x, y, sx, sy) in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        o.append(f'<path d="M{x},{y + 16 * sy} L{x},{y} L{x + 16 * sx},{y}" fill="none" stroke="{GREEN}" stroke-width="2"/>')
    o.append(portrait_svg(im, rows, px0, py0))
    o.append(f'<text x="{px0}" y="{py0 + ph + 34:.0f}" font-size="12" fill="#7d8590">SUBJECT_ID <tspan fill="#c9d1d9">{u["id"] if "id" in u else "83902056"}</tspan>'
             f' &#183; MATCH <tspan fill="{GREEN}">99.7%</tspan> &#183; STATUS <tspan fill="{GREEN}">ONLINE</tspan></text>')
    f = (rows * 0.06) / CYCLE
    o.append(f'<rect x="{px0 - 4}" y="{py0}" width="{COLS * PITCH + 8:.0f}" height="3" fill="{GREEN}" opacity="0" filter="url(#g)">'
             f'<animate attributeName="y" values="{py0};{py0 + ph:.0f};{py0 + ph:.0f}" keyTimes="0;{f:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".95;.95;0;0" keyTimes="0;{f:.4f};{f + .004:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/></rect>')
    o.append(f'<line x1="{tx - 22}" y1="24" x2="{tx - 22}" y2="{H - 24}" stroke="#0f3d22"/>')

    lines = [
        ("h", f"{USER.lower()}@github"),
        ("r", "─" * 26),
        ("kv", ("ROLE", "Developer / Security")),
        ("kv", ("BASE", "Bangalore, IN")),
        ("kv", ("UPTIME", f"{years:.1f} yrs on GitHub")),
        ("kv", ("REPOS", f"{len(rp)} public  ·  {stars}★")),
        ("kv", ("NETWORK", f"{u['followers']['totalCount']} followers · {u['following']['totalCount']} following")),
        ("kv", ("COMMITS", f"{cc['totalCommitContributions']} this year")),
        ("kv", ("PR / ISSUES", f"{cc['totalPullRequestContributions']} / {cc['totalIssueContributions']}")),
        ("kv", ("STREAK", f"{cur}d now · {longest}d best")),
        ("r", ""),
        ("s", "LANGUAGE.MIX"),
    ] + [("bar", (lang, cnt / tot)) for lang, cnt in top]

    y = 70
    t0 = rows * 0.06 * 0.5
    for i, (kind, val) in enumerate(lines):
        a = (t0 + i * 0.18) / CYCLE
        anim = (f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{a:.4f};{a + .004:.4f};.93;.97;1" '
                f'dur="{CYCLE}s" repeatCount="indefinite"/>')
        if kind == "h":
            o.append(f'<text x="{tx}" y="{y}" font-size="21" fill="{GREEN}" font-weight="bold" opacity="0">{escape(val)}{anim}</text>')
        elif kind == "r":
            if val:
                o.append(f'<text x="{tx}" y="{y}" font-size="14" fill="#0f5d2c" opacity="0">{val}{anim}</text>')
        elif kind == "s":
            o.append(f'<text x="{tx}" y="{y}" font-size="13" fill="{GREEN}" opacity="0">&#9656; {val}{anim}</text>')
        elif kind == "kv":
            k, v = val
            o.append(f'<text x="{tx}" y="{y}" font-size="14" opacity="0"><tspan fill="{GREEN}">{k}</tspan>'
                     f'<tspan x="{tx + 118}" fill="#e6edf3">{escape(v)}</tspan>{anim}</text>')
        else:
            lang, fr = val
            o.append(f'<text x="{tx}" y="{y}" font-size="14" opacity="0"><tspan fill="#c9d1d9">{escape(lang)}</tspan>'
                     f'<tspan x="{tx + 118}" fill="{GREEN}">{bar(fr)}</tspan>'
                     f'<tspan fill="#7d8590"> {fr * 100:.0f}%</tspan>{anim}</text>')
        y += 14 if kind == "r" else 26 if kind != "h" else 30
    o.append(f'<rect x="{tx}" y="{y - 4}" width="10" height="17" fill="{GREEN}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect>')
    o.append(f'<text x="{W - 24}" y="{H - 16}" font-size="10" fill="#7d8590" text-anchor="end">rendered {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC &#183; scripts/dossier.py</text>')
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o))
    print(f"wrote {OUT}: {COLS}x{rows} halftone, {len(rp)} repos, {stars} stars, H={H}")


if __name__ == "__main__":
    main()
