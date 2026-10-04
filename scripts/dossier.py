#!/usr/bin/env python3
"""assets/dossier.svg: avatar rendered as animated colour-ASCII + a live neofetch readout.

The portrait is rebuilt from the real avatar on every run (Pillow). Rows
"decrypt" in top to bottom under a scan line, hold, fade, and re-scan every
CYCLE seconds. Stats come from the GitHub API, so nothing here is third-party.
"""
import colorsys
import io
import sys
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/dossier.svg"
CROP = (0.20, 0.40, 0.82, 1.0)  # fractions of the avatar: head + shoulders
COLS, FS, CW, LH = 88, 8.0, 4.8, 8.0  # glyph grid: cols, font size, char width, line height
RAMP = " .:-=+*#%@"
CYCLE = 26.0  # seconds per scan loop
GREEN = "#00ff41"


def portrait():
    raw = urllib.request.urlopen(urllib.request.Request(
        f"https://github.com/{USER}.png?size=460", headers={"User-Agent": "profile-gen"}), timeout=30).read()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    im = im.crop((int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h)))
    rows = round(COLS * (im.height / im.width) * (CW / LH))
    im = im.resize((COLS, rows), Image.LANCZOS)
    # local contrast normalisation: each cell is judged against its neighbourhood,
    # so a dark face in front of a bright wall still gets full-range glyphs
    im = ImageOps.autocontrast(im, cutoff=1)
    lum = im.convert("L")
    blur = lum.filter(ImageFilter.GaussianBlur(5))
    px, lp, bp = im.load(), lum.load(), blur.load()
    for y in range(im.height):
        for x in range(im.width):
            l, b = lp[x, y] / 255, bp[x, y] / 255
            adj = max(0.0, min(1.0, 0.35 * l + 0.65 * (0.5 + 2.4 * (l - b))))
            k = adj / l if l > 0.02 else 1.0
            r, g, bl = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(bl * k)))
    return im, rows


def cell(rgb):
    r, g, b = (v / 255 for v in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    ch = RAMP[min(len(RAMP) - 1, int(lum * len(RAMP) * 0.999))]
    if lum < 0.08:
        return " ", None
    # keep the photo's hue but push it neon: saturate, floor the brightness
    r2, g2, b2 = colorsys.hsv_to_rgb(h, min(1, s * 1.35 + 0.1), 0.38 + 0.62 * min(1, lum * 1.15))
    return ch, "#%x%x%x" % (round(r2 * 15), round(g2 * 15), round(b2 * 15))


def portrait_svg(im, rows, x0, y0):
    out = []
    for y in range(rows):
        runs, cur, buf = [], None, ""
        for x in range(COLS):
            ch, col = cell(im.getpixel((x, y)))
            if col != cur and buf:
                runs.append((cur, buf))
                buf = ""
            cur = col
            buf += ch
        runs.append((cur, buf))
        tspans = "".join(
            f'<tspan fill="{c}">{escape(t)}</tspan>' if c else f"<tspan>{escape(t)}</tspan>" for c, t in runs)
        t0 = y * 0.07
        a = t0 / CYCLE
        out.append(
            f'<text x="{x0}" y="{y0 + y * LH:.1f}" font-size="{FS}" textLength="{COLS * CW:.1f}" '
            f'lengthAdjust="spacing" xml:space="preserve" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;.88;1;1;0;0" '
            f'keyTimes="0;{a:.4f};{a + .006:.4f};{a + .03:.4f};{a + .05:.4f};.93;.97;1" '
            f'dur="{CYCLE}s" repeatCount="indefinite"/>{tspans}</text>')
    return "\n".join(out)


def bar(frac, n=16):
    k = round(frac * n)
    return "█" * k + "░" * (n - k)


def main():
    import collections
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
    W = 960
    px0, py0 = 26, 62
    tx = 520
    n_lines = 12 + len(top) + 2 + 4 + 2
    H = max(int(rows * LH) + 70, 62 + n_lines * 21 + 50)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="ASCII portrait of {escape(USER)} with live GitHub stats">',
         f"<title>OPERATOR DOSSIER // {escape(USER)}</title>",
         f"""<defs><filter id="g" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>text{{font-family:'Fira Code','Cascadia Code',Consolas,'DejaVu Sans Mono',monospace}}</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="#0d1117" stroke="#0f5d2c"/>
<text x="{px0}" y="34" font-size="12" fill="{GREEN}">&#9608; SUBJECT_IMG.render()</text>
<text x="{px0 + 190}" y="34" font-size="10" fill="#7d8590">avatar &#8594; {COLS}x{rows} glyph grid &#183; colour-preserving ASCII</text>"""]
    o.append(portrait_svg(im, rows, px0, py0))
    # scan line
    ph = rows * LH
    sc = 3.0 * rows * 0.07 / 3.0  # seconds the scan takes
    f = (rows * 0.07) / CYCLE
    o.append(f'<rect x="{px0 - 4}" y="{py0 - 8}" width="{COLS * CW + 8:.0f}" height="3" fill="{GREEN}" opacity="0" filter="url(#g)">'
             f'<animate attributeName="y" values="{py0 - 8};{py0 + ph:.0f};{py0 + ph:.0f}" keyTimes="0;{f:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".95;.95;0;0" keyTimes="0;{f:.4f};{f + .004:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/></rect>')
    o.append(f'<line x1="{tx - 24}" y1="22" x2="{tx - 24}" y2="{H - 22}" stroke="#0f5d2c"/>')

    # neofetch-style readout, lines type in after the scan finishes
    lines = [
        ("h", f"{USER.lower()}@github"),
        ("r", "-" * 28),
        ("kv", ("ROLE", "Developer // Security enthusiast")),
        ("kv", ("BASE", "Bangalore, IN")),
        ("kv", ("UPTIME", f"{years:.1f} yrs on GitHub")),
        ("kv", ("REPOS", f"{len(rp)} public  ·  {stars} stars")),
        ("kv", ("NETWORK", f"{u['followers']['totalCount']} followers · {u['following']['totalCount']} following")),
        ("kv", ("COMMITS", f"{cc['totalCommitContributions']} in the last year")),
        ("kv", ("PRS/ISSUES", f"{cc['totalPullRequestContributions']} PRs · {cc['totalIssueContributions']} issues")),
        ("kv", ("STREAK", f"{cur}d now · {longest}d best")),
        ("r", ""),
        ("s", "LANGUAGE.MIX"),
    ]
    for lang, cnt in top:
        lines.append(("bar", (lang, cnt / tot, cnt)))
    lines += [("r", ""), ("s", "ACTIVE.OPS")]
    for r in sorted(rp, key=lambda r: r["pushed_at"], reverse=True)[:4]:
        lines.append(("op", r["name"][:30]))
    lines += [("r", ""), ("pal", None)]

    y = 62
    for i, (kind, val) in enumerate(lines):
        begin = f / 1.0 * 0 + (rows * 0.07 * 0.55) + i * 0.16
        a = begin / CYCLE
        anim = (f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{a:.4f};{a + .004:.4f};.93;.97;1" '
                f'dur="{CYCLE}s" repeatCount="indefinite"/>')
        if kind == "h":
            body = f'<text x="{tx}" y="{y}" font-size="17" fill="{GREEN}" font-weight="bold" opacity="0">{escape(val)}{anim}</text>'
        elif kind == "r":
            body = f'<text x="{tx}" y="{y}" font-size="12" fill="#0f5d2c" opacity="0">{val}{anim}</text>' if val else ""
        elif kind == "s":
            body = f'<text x="{tx}" y="{y}" font-size="11" fill="{GREEN}" opacity="0">&#9656; {val}{anim}</text>'
        elif kind == "kv":
            k, v = val
            body = (f'<text x="{tx}" y="{y}" font-size="12" opacity="0"><tspan fill="{GREEN}">{k}</tspan>'
                    f'<tspan x="{tx + 112}" fill="#e6edf3">{escape(v)}</tspan>{anim}</text>')
        elif kind == "bar":
            lang, fr, cnt = val
            body = (f'<text x="{tx}" y="{y}" font-size="12" opacity="0"><tspan fill="#c9d1d9">{escape(lang)}</tspan>'
                    f'<tspan x="{tx + 112}" fill="{GREEN}">{bar(fr)}</tspan>'
                    f'<tspan fill="#7d8590"> {fr * 100:.0f}%</tspan>{anim}</text>')
        elif kind == "op":
            body = f'<text x="{tx}" y="{y}" font-size="12" fill="#c9d1d9" opacity="0">&#8250; {escape(val)}{anim}</text>'
        else:  # colour palette strip
            sw = "".join(f'<rect x="{tx + j * 26}" y="{y - 10}" width="22" height="12" fill="{c}"/>'
                         for j, c in enumerate(["#00ff41", "#39ff6a", "#ffd43b", "#4aa8ff", "#ff5f87", "#b48cff", "#ff7a45", "#e6edf3"]))
            body = f'<g opacity="0">{sw}{anim}</g>'
        o.append(body)
        y += 22 if kind not in ("r",) else 12
    # blinking cursor
    o.append(f'<rect x="{tx}" y="{y + 6}" width="9" height="15" fill="{GREEN}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect>')
    o.append(f'<text x="{W - 24}" y="{H - 14}" font-size="9" fill="#7d8590" text-anchor="end">rendered {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by scripts/dossier.py</text>')
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o))
    print(f"wrote {OUT}: {COLS}x{rows} portrait, {len(rp)} repos, {stars} stars, {len(o)} nodes")


if __name__ == "__main__":
    main()
