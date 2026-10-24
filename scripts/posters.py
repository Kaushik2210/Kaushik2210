#!/usr/bin/env python3
"""assets/p-<repo>.svg + the FEATURED BUILDS block of README.md.

One poster per featured repo (curated in data/projects.json). Each has generative
cover art seeded from the repo name (so no two look alike), with a motif per
category, plus live data from the GitHub API: language, stars, last push, and a
pill that says where a click goes (LIVE demo or REPO).

Also rewrites the collapsed "more builds" list. Pure SMIL, no JavaScript.
Usage: posters.py [user] [README.md]
"""
import json
import math
import os
import random
import re
import sys
import zlib
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
README = sys.argv[2] if len(sys.argv) > 2 else "README.md"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "data", "projects.json")
ASSETS = os.path.join(HERE, "..", "assets")
START, END = "<!--BUILDS_START-->", "<!--BUILDS_END-->"
W, H, ART = 405, 264, 112
SKIP_TOPICS = {"hackathon", "hacktoberfest", "good-first-issue", "typescript", "python", "javascript", "java"}
CATS = {  # label, art colour
    "security": ("SECURITY", t.A1),
    "devtool": ("DEV TOOL", t.A3),
    "product": ("PRODUCT", t.RINGS[2]),
    "learning": ("LEARNING", t.CLOCK[3]),
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wrap(text, width, lines):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = f"{cur} {w}".strip()
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: max(0, width - 1)].rstrip(" ,.;:-") + "…"
    return out


def ago(days):
    return "today" if days == 0 else "yesterday" if days == 1 else f"{days}d ago" if days < 60 else f"{days // 30}mo ago"


# ---------------- generative cover art ----------------
def art_security(rnd, col):
    cx, cy = 262 + rnd.uniform(-50, 50), 62 + rnd.uniform(-6, 6)
    o = []
    for r in (14, 30, 46, 62, 80):
        o.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="none" stroke="{col}" stroke-opacity=".28"/>')
    for a in range(0, 360, 45):
        x, y = cx + 80 * math.cos(math.radians(a)), cy + 80 * math.sin(math.radians(a))
        o.append(f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="{col}" stroke-opacity=".14"/>')
    o.append(f'<g transform="translate({cx:.0f},{cy:.0f})"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{rnd.uniform(5, 8):.1f}s" repeatCount="indefinite"/>'
             f'<path d="M0,0 L80,0 A80,80 0 0 0 {80 * math.cos(math.radians(-38)):.0f},{80 * math.sin(math.radians(-38)):.0f} Z" fill="{col}" fill-opacity=".22"/>'
             f'<line x1="0" y1="0" x2="80" y2="0" stroke="{col}" stroke-width="1.4"/></g></g>')
    for _ in range(6):
        a, r = rnd.uniform(0, 6.283), rnd.uniform(14, 74)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{t.A2}"><animate attributeName="opacity" values=".2;1;.2" dur="{rnd.uniform(2, 4):.1f}s" begin="-{rnd.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(o)


def art_devtool(rnd, col):
    pts = [(rnd.uniform(150, 388), rnd.uniform(16, ART - 16)) for _ in range(15)]
    edges = set()
    for i, p in enumerate(pts):
        near = sorted((j for j in range(len(pts)) if j != i), key=lambda j: (pts[j][0] - p[0]) ** 2 + (pts[j][1] - p[1]) ** 2)[:2]
        for j in near:
            edges.add((min(i, j), max(i, j)))
    o = [f'<line x1="{pts[i][0]:.0f}" y1="{pts[i][1]:.0f}" x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}" stroke="{col}" stroke-opacity=".34"/>' for i, j in edges]
    for n, (i, j) in enumerate(sorted(edges)[:7]):
        d = rnd.uniform(2.2, 4.5)
        o.append(f'<circle r="2" fill="{t.A2}" opacity="0"><animateMotion path="M{pts[i][0]:.0f},{pts[i][1]:.0f} L{pts[j][0]:.0f},{pts[j][1]:.0f}" dur="{d:.1f}s" begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.85;1" dur="{d:.1f}s" repeatCount="indefinite"/></circle>')
    for x, y in pts:
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([2.4, 3, 4])}" fill="{col}"/>')
    return "".join(o)


def art_product(rnd, col):
    o = []
    for k in range(3):
        x, y = 190 + k * 52 + rnd.uniform(-8, 8), 18 + k * 12 + rnd.uniform(-5, 5)
        rot = rnd.uniform(-9, 9)
        o.append(f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})"><rect width="116" height="76" rx="9" fill="{t.SURFACE}" stroke="{col}" stroke-opacity="{.35 + k * .2:.2f}"/>'
                 f'<rect x="10" y="10" width="{rnd.randint(34, 70)}" height="6" rx="3" fill="{col}" opacity=".8"/>'
                 + "".join(f'<rect x="10" y="{26 + n * 11}" width="{rnd.randint(50, 96)}" height="4" rx="2" fill="{t.TEXT3}" opacity=".45"/>' for n in range(3))
                 + f'<circle cx="100" cy="62" r="6" fill="{t.A3}" opacity=".9"/></g>')
    return "".join(o)


def art_learning(rnd, col):
    n, o, pts = 14, [], []
    for i in range(n):
        h = 14 + (ART - 46) * ((i + 1) / n) ** 1.2 * rnd.uniform(.72, 1)
        x = 168 + i * 16.5
        o.append(f'<rect x="{x:.0f}" y="{ART - 10 - h:.0f}" width="11" height="{h:.0f}" rx="3" fill="{col}" opacity="{.32 + .6 * i / n:.2f}"/>')
        pts.append((x + 5.5, ART - 10 - h))
    o.append('<polyline points="' + " ".join(f"{x:.0f},{y - 7:.0f}" for x, y in pts) + f'" fill="none" stroke="{t.A2}" stroke-width="1.6" stroke-linejoin="round" stroke-opacity=".9"/>')
    o.append(f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1] - 7:.0f}" r="3.4" fill="{t.A3}"><animate attributeName="r" values="3;6;3" dur="2.2s" repeatCount="indefinite"/></circle>')
    return "".join(o)


MOTIFS = {"security": art_security, "devtool": art_devtool, "product": art_product, "learning": art_learning}


def poster(cfg, r, now):
    name = r["name"]
    cat = cfg.get("category", "product")
    label, col = CATS[cat]
    rnd = random.Random(zlib.crc32(name.encode()))
    blurb = cfg.get("blurb") or (r.get("description") or "No description yet.")
    days = max(0, (now - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days)
    lang = r["language"] or "misc"
    live = bool(r.get("homepage"))
    topics = [x for x in (r.get("topics") or []) if x not in SKIP_TOPICS][:3]
    title = name.rstrip("-_")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(f"{title}: {blurb}")}">',
         f"<title>{escape(title)}</title>",
         t.defs(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
                f'<linearGradient id="art" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t.RAISED}"/><stop offset="1" stop-color="{t.SURFACE}"/></linearGradient>'
                f'<radialGradient id="wash"><stop offset="0" stop-color="{col}" stop-opacity=".42"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="{t.SURFACE}"/>',
         f'<rect width="{W}" height="{ART}" fill="url(#art)"/>',
         f'<ellipse cx="{rnd.uniform(230, 340):.0f}" cy="{rnd.uniform(30, 70):.0f}" rx="170" ry="90" fill="url(#wash)"/>',
         MOTIFS[cat](rnd, col),
         f'<rect y="{ART}" width="{W}" height="1" fill="{t.HAIRLINE}"/>']
    # category + destination pills (over the art)
    cw = 18 + 6.9 * len(label)
    o.append(f'<rect x="16" y="16" width="{cw:.0f}" height="22" rx="11" fill="{t.SURFACE}" fill-opacity=".78" stroke="{col}" stroke-opacity=".6"/>'
             f'<text x="{16 + cw / 2:.0f}" y="31" class="label" text-anchor="middle" style="fill:{col}">{label}</text>')
    dest = "LIVE &#8599;" if live else "REPO &#8599;"
    dc = t.GREEN if live else t.TEXT2
    o.append(f'<rect x="{W - 84}" y="16" width="68" height="22" rx="11" fill="{t.SURFACE}" fill-opacity=".78" stroke="{dc}" stroke-opacity=".6"/>'
             f'<text x="{W - 50}" y="31" class="label" text-anchor="middle" style="fill:{dc}">{dest}</text>')
    # text
    o.append(f'<text x="20" y="{ART + 30}" font-size="18" font-weight="700" fill="{t.TEXT}">{escape(title)}</text>')
    for i, line in enumerate(wrap(blurb, 60, 3)):
        o.append(f'<text x="20" y="{ART + 51 + i * 16}" font-size="12" fill="{t.TEXT2}">{escape(line)}</text>')
    # chips
    x = 20
    for tp in topics:
        w = 14 + 6.1 * len(tp)
        o.append(f'<rect x="{x:.0f}" y="{H - 54}" width="{w:.0f}" height="20" rx="10" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
                 f'<text x="{x + w / 2:.0f}" y="{H - 40}" class="mono" font-size="10" fill="{t.TEXT3}" text-anchor="middle">{escape(tp)}</text>')
        x += w + 6
    # footer: language, stars, last push
    lc = t.lang_color(lang if lang in t.LANG else "Other")
    stars = r["stargazers_count"]
    o.append(f'<circle cx="26" cy="{H - 17}" r="4" fill="{lc}"/>'
             f'<text x="38" y="{H - 13}" font-size="11" fill="{t.TEXT2}">{escape(lang)}'
             f'<tspan fill="{t.TEXT3}">  &#183;  &#9733; {stars}  &#183;  pushed {ago(days)}</tspan></text>')
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    alt = (f"{title}, a {label.lower()} project in {lang}: {blurb} "
           f"{'Opens the live demo.' if live else 'Opens the repository.'}")
    return "\n".join(o), alt, (r["homepage"] if live else r["html_url"])


def main():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    repos = {r["name"]: r for r in common.repos(USER)}
    now = datetime.now(timezone.utc)
    cells, used = [], set()
    for item in cfg["featured"]:
        r = repos.get(item["repo"])
        if not r:
            print("skip (repo not found):", item["repo"])
            continue
        svg, alt, href = poster(item, r, now)
        fn = f"p-{slug(r['name'])}.svg"
        open(os.path.join(ASSETS, fn), "w", encoding="utf-8").write(svg)
        used.add(r["name"])
        cells.append(f'<a href="{escape(href, {chr(34): "&quot;"})}"><img src="assets/{fn}" alt="{escape(alt, {chr(34): "&quot;"})}" width="49%"/></a>')
    # "more builds": everything else with a description, newest first
    ex, exp = set(cfg.get("exclude_more", [])), tuple(cfg.get("exclude_prefix_more", []))
    more = [r for r in sorted(repos.values(), key=lambda r: r["pushed_at"], reverse=True)
            if r["name"] not in used and r["name"] not in ex and not r["name"].startswith(exp) and (r.get("description") or "").strip()]
    rows = ["| Build | Stack | What it is |", "|:--|:--|:--|"]
    for r in more[:24]:
        d = re.sub(r"\s+", " ", r["description"]).replace("|", "/").strip()
        d = d if len(d) <= 100 else d[:100].rsplit(" ", 1)[0].rstrip(",.;:-") + "…"
        link = f"[**{r['name']}**]({r['html_url']})" + (f" · [live]({r['homepage']})" if r.get("homepage") else "")
        rows.append(f"| {link} | `{r['language'] or 'misc'}` | {d} |")
    caption = ("<sub>Tap a card to open the live demo or the repository. Cover art is generated from each repo's name; "
               "language, stars and last push update automatically.</sub>")
    block = ('<div align="center">\n\n' + " ".join(cells) + f"\n\n{caption}\n\n</div>\n\n"
             f"<details>\n<summary><b>More builds ({len(more[:24])})</b></summary>\n\n" + "\n".join(rows) + "\n\n</details>")
    text = open(README, encoding="utf-8").read()
    a, b = text.index(START) + len(START), text.index(END)
    new = text[:a] + "\n" + block + "\n" + text[b:]
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
    print(f"posters: {len(cells)} featured, {len(more[:24])} in 'more builds'")


if __name__ == "__main__":
    main()
