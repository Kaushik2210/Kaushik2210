"""Draws every image on the profile out of GitHub contribution squares.

Standard library only. Needs GITHUB_TOKEN (or GH_TOKEN) in the environment.
Usage: python scripts/build.py [owner]
"""

import base64
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.error
import urllib.request
from html import escape
from pathlib import Path

import palette as P

OWNER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
TODAY = dt.date.today()

_SYNTH = {
    "bg": P.BG, "panel": P.PANEL, "border": P.BORDER,
    "text": P.TEXT, "muted": P.MUTED, "faint": P.FAINT,
    "lv": P.LV, "tip_bg": P.CYAN, "tip_fg": P.BG,
}
# Synthwave is a night look, so both GitHub themes get the same palette.
THEMES = {"dark": _SYNTH, "light": _SYNTH}

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

FEATURED = [
    ("IntentGuard", "AI security", "https://kaushik2210.github.io/IntentGuard/",
     "Runtime authorization for autonomous AI agents: checks intent and behaviour before a tool call runs."),
    ("Net-Sentinel", "Security", None,
     "Explainable network digital twin. Detects threats, rebuilds attacks and maps them to MITRE ATT&CK."),
    ("ORBITAL-SENTINEL", "Security", None,
     "Tells cyberattacks apart from sensor faults and solar weather in real NASA spacecraft telemetry."),
    ("Deepfake-Detector", "AI security", None,
     "Synthetic-media detection with calibrated probabilities and visual evidence, never a yes/no verdict."),
    ("tapwire", "Dev tool", "https://tapwire-xi.vercel.app",
     "Turns each mistake an AI coding agent makes into an enforced rule, then measures repeats."),
    ("gitVisualise", "Dev tool", "https://kaushik2210.github.io/gitVisualise/",
     "Paste a GitHub link, get a narrated architecture tour. Website, CLI and GitHub Action."),
    ("HireOS", "Product", "https://hireos-beryl.vercel.app",
     "Job-search workspace that shows its evidence: fit scoring, honest tailoring, tracking."),
    ("AlgoVerse", "Product", "https://algoverse-lovat-seven.vercel.app",
     "DSA visualiser and interview prep: 25 modules, 13 pattern guides, 635+ explained solutions."),
    ("scam-khel", "Security", None,
     "Family shield against Indian digital-arrest scams: live detection, honeypot, family alerts."),
    ("aiforge", "Learning", None,
     "Open-source, gamified academy for becoming a production-ready AI engineer."),
]

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Java": "#b07219",
    "HTML": "#e34c26", "CSS": "#663399", "MDX": "#fcb32c", "Shell": "#89e051", "C": "#555555",
}

# ---------------------------------------------------------------- GitHub API


def _request(url, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-heatmap"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null"), r.headers.get("Link", "")


def rest(path):
    url = path if path.startswith("http") else f"https://api.github.com{path}"
    out = []
    while url:
        try:
            page, link = _request(url)
        except urllib.error.HTTPError as e:
            if e.code in (404, 409):  # missing or empty repo
                return out
            raise
        if not isinstance(page, list):
            return page
        out += page
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part[part.find("<") + 1: part.find(">")]
    return out


def graphql(query):
    data, _ = _request("https://api.github.com/graphql", {"query": query})
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch():
    q = """query{user(login:"%s"){name createdAt avatarUrl followers{totalCount}
      contributionsCollection{contributionCalendar{totalContributions
        weeks{contributionDays{date contributionCount contributionLevel}}}}}}""" % OWNER
    user = graphql(q)["user"]
    levels = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
              "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    weeks = [[(dt.date.fromisoformat(d["date"]), d["contributionCount"], levels[d["contributionLevel"]])
              for d in w["contributionDays"]]
             for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]]

    repos = [r for r in rest(f"/users/{OWNER}/repos?per_page=100&type=owner") if not r["fork"]]
    by_name = {r["name"]: r for r in repos}

    since = (TODAY - dt.timedelta(weeks=26)).isoformat() + "T00:00:00Z"
    projects = []
    for name, tag, live, blurb in FEATURED:
        meta = by_name.get(name, {})
        commits = rest(f"/repos/{OWNER}/{name}/commits?since={since}&per_page=100")
        days = {}
        for c in commits if isinstance(commits, list) else []:
            d = dt.date.fromisoformat(c["commit"]["author"]["date"][:10])
            days[d] = days.get(d, 0) + 1
        projects.append({
            "name": name, "tag": tag, "live": live, "blurb": blurb, "days": days,
            "lang": meta.get("language"), "stars": meta.get("stargazers_count", 0),
            "pushed": meta.get("pushed_at", "")[:10],
        })

    langs = {}
    for r in repos:
        if r["name"] == OWNER or r.get("size", 0) == 0:
            continue
        for lang, n in (rest(f"/repos/{OWNER}/{r['name']}/languages") or {}).items():
            if lang in ("Jupyter Notebook",):
                continue
            langs[lang] = langs.get(lang, 0) + n
    return {"weeks": weeks, "total": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
            "followers": user["followers"]["totalCount"], "repos": len(repos),
            "projects": projects, "langs": langs, "created": user["createdAt"], "avatar": user["avatarUrl"],
            "stars": sum(r.get("stargazers_count", 0) for r in repos),
            "live": sum(1 for f in FEATURED if f[2]),
            "latest": max((r for r in repos if r["name"] != OWNER and not r.get("private")),
                          key=lambda r: r.get("pushed_at") or "")}


# ---------------------------------------------------------------- helpers


def svg(w, h, body, title, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>'
            f"<style>text{{font-family:{SANS}}} .m{{font-family:{MONO}}}"
            f"{extra_css}"
            "@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>"
            f"{body}</svg>")


def cell(x, y, size, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2" fill="{fill}"{extra}/>'


def ago(iso):
    if not iso:
        return "no pushes yet"
    days = (TODAY - dt.date.fromisoformat(iso)).days
    if days <= 0:
        return "pushed today"
    if days == 1:
        return "pushed yesterday"
    if days < 30:
        return f"pushed {days}d ago"
    return f"pushed {days // 30}mo ago"


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def streaks(weeks):
    days = [d for w in weeks for d in w if d[0] <= TODAY]
    best = run = 0
    for _, n, _ in days:
        run = run + 1 if n else 0
        best = max(best, run)
    cur = 0
    for i, (d, n, _) in enumerate(reversed(days)):
        if n:
            cur += 1
        elif i == 0:  # today can still be empty
            continue
        else:
            break
    active = sum(1 for d in days if d[1])
    top = max(days, key=lambda d: d[1])
    return best, cur, active, top


# ---------------------------------------------------------------- hero

FONT = {
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
}



# ---------------------------------------------------------------- project cards


def project_card(t, p):
    w, h = 480, 250
    pad = 22
    out = [f'<defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{P.PINK}"/>'
           f'<stop offset=".5" stop-color="{P.PURPLE}" stop-opacity=".5"/><stop offset="1" stop-color="{P.CYAN}"/>'
           '</linearGradient></defs>',
           f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="10" fill="{t["panel"]}" stroke="url(#cg)" stroke-width="1.5"/>']
    out.append(f'<text class="m" x="{pad}" y="{pad + 10}" font-size="11" letter-spacing="1.2" fill="{t["lv"][3]}">'
               f"{escape(p['tag'].upper())}</text>")
    if p["live"]:
        lx = pad + len(p["tag"]) * 7.9 + 14
        out.append(f'<g class="live"><rect x="{lx}" y="{pad}" width="46" height="14" rx="7" fill="{t["lv"][4]}"/>'
                   f'<text class="m" x="{lx + 23}" y="{pad + 10.5}" font-size="9" font-weight="700" fill="{t["bg"]}" '
                   'text-anchor="middle" letter-spacing="1">● LIVE</text></g>')
    out.append(f'<rect class="scan" x="1" y="0" width="{w - 2}" height="2" fill="{t["lv"][4]}" opacity=".18"/>')
    out.append(f'<text x="{pad}" y="{pad + 38}" font-size="22" font-weight="700" fill="{t["text"]}">{escape(p["name"])}</text>')
    if p["lang"]:
        lc = LANG_COLORS.get(p["lang"], t["muted"])
        out.append(f'<circle cx="{w - pad - len(p["lang"]) * 7.2 - 10}" cy="{pad + 6}" r="5" fill="{lc}"/>'
                   f'<text x="{w - pad}" y="{pad + 10}" font-size="12" fill="{t["muted"]}" text-anchor="end">{p["lang"]}</text>')
    for i, line in enumerate(wrap(p["blurb"], 60)[:3]):
        out.append(f'<text x="{pad}" y="{pad + 66 + i * 20}" font-size="14" fill="{t["muted"]}">{escape(line)}</text>')

    # 26-week heatmap of this repo's commits.
    start = TODAY - dt.timedelta(days=TODAY.weekday() + 1 + 25 * 7)  # a Sunday, 26 columns ago
    counts = list(p["days"].values())
    hi = max(counts) if counts else 1
    pitch, size, gx, gy = 10.5, 8, pad, h - pad - 7 * 10.5 + 2
    for c in range(26):
        for r in range(7):
            d = start + dt.timedelta(days=c * 7 + r)
            if d > TODAY:
                continue
            n = p["days"].get(d, 0)
            lv = 0 if n == 0 else min(4, 1 + int(3 * math.log1p(n) / math.log1p(hi)))
            out.append(f'<rect x="{gx + c * pitch:.1f}" y="{gy + r * pitch:.1f}" width="{size}" height="{size}" '
                       f'rx="1.5" fill="{t["lv"][lv]}" class="c" style="animation-delay:{c * 0.025:.2f}s,{c * 0.07:.2f}s"/>')

    total = sum(counts)
    sx = w - pad
    out.append(f'<text x="{sx}" y="{h - pad - 46}" font-size="30" font-weight="700" fill="{t["text"]}" text-anchor="end">{total}</text>')
    out.append(f'<text x="{sx}" y="{h - pad - 28}" font-size="12" fill="{t["muted"]}" text-anchor="end">commits in 26 weeks</text>')
    link = "live demo" if p["live"] else "source"
    out.append(f'<text class="m" x="{sx}" y="{h - pad - 2}" font-size="12" font-weight="600" fill="{t["lv"][3]}" text-anchor="end">'
               f"{ago(p['pushed'])}  ·  {link} ↗</text>")
    css = ("@keyframes in{from{opacity:0}to{opacity:1}}"
           "@keyframes wave{0%,80%,100%{opacity:1}88%{opacity:.35}}"
           "@keyframes scan{from{transform:translateY(0)}to{transform:translateY(" + str(h) + "px)}}"
           "@keyframes blink{0%,100%{opacity:1}50%{opacity:.45}}"
           ".c{animation:in .4s ease-out both,wave 3.6s ease-in-out infinite}"
           ".scan{animation:scan 4.5s linear infinite}.live{animation:blink 1.4s steps(2) infinite}")
    return svg(w, h, "".join(out), f"{p['name']}: {p['blurb']} {total} commits in the last 26 weeks.", css)


# ---------------------------------------------------------------- the year, alive


def life_frames(grid, gens):
    rows, cols = len(grid), len(grid[0])
    frames = [grid]
    for _ in range(gens):
        g, nxt = frames[-1], []
        for r in range(rows):
            row = []
            for c in range(cols):
                n = sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                        if (dr or dc) and g[(r + dr) % rows][(c + dc) % cols])
                alive = g[r][c]
                if alive and n in (2, 3):
                    row.append(min(4, alive + 1) if n == 3 else alive)  # survivors grow brighter
                elif not alive and n == 3:
                    row.append(1)  # newborn starts dim
                else:
                    row.append(0)
            nxt.append(row)
        frames.append(nxt)
    return frames


def year(t, data):
    weeks = data["weeks"]
    cols, rows = len(weeks), 7
    grid = [[0] * cols for _ in range(rows)]
    for c, w in enumerate(weeks):
        for d, _, lv in w:
            grid[(d.weekday() + 1) % 7][c] = lv
    gens = 16
    frames = life_frames(grid, gens)
    seq = [0, 0, 0, 0] + list(range(1, gens + 1)) + [gens, gens]  # hold the real year, then evolve
    dur = len(seq) * 0.7

    pitch, size, ox, oy = 15, 12, 46, 118
    w = ox + cols * pitch + 24
    out = [f'<rect width="{w}" height="300" rx="12" fill="{t["bg"]}"/>']

    best, cur, active, top = streaks(weeks)
    stats = [(f"{data['total']:,}", "contributions"), (f"{active}", "active days"),
             (f"{best}d", "longest streak"), (f"{cur}d", "current streak"),
             (f"{top[1]}", f"best day · {top[0].strftime('%d %b')}")]
    for i, (big, small) in enumerate(stats):
        x = ox + i * (cols * pitch / 5)
        out.append(f'<text x="{x:.0f}" y="44" font-size="24" font-weight="700" fill="{t["text"]}">{big}</text>'
                   f'<text x="{x:.0f}" y="64" font-size="12" fill="{t["muted"]}">{small}</text>')

    last_month = None
    for c, wk in enumerate(weeks):
        m = wk[0][0].month
        if m != last_month and wk[0][0].day <= 7:
            out.append(f'<text x="{ox + c * pitch}" y="{oy - 10}" font-size="11" fill="{t["muted"]}">'
                       f"{wk[0][0].strftime('%b')}</text>")
        last_month = m
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{ox - 8}" y="{oy + r * pitch + 10}" font-size="11" fill="{t["muted"]}" text-anchor="end">{name}</text>')

    for r in range(rows):
        for c in range(cols):
            vals = [t["lv"][frames[i][r][c]] for i in seq]
            x, y = ox + c * pitch, oy + r * pitch
            if len(set(vals)) == 1:
                out.append(cell(x, y, size, vals[0]))
            else:
                out.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2" fill="{vals[0]}">'
                           f'<animate attributeName="fill" dur="{dur:.1f}s" repeatCount="indefinite" '
                           f'calcMode="discrete" values="{";".join(vals)}"/></rect>')

    # Caption that follows the animation.
    ly = oy + rows * pitch + 30
    n = len(seq)
    for i, g in enumerate(seq):
        label = "generation 0: my real last 12 months" if g == 0 else f"generation {g}: Conway's rules take over"
        if i and seq[i - 1] == g:
            continue
        span = sum(1 for j in seq if j == g)
        vis = ["0"] * n
        for j in range(i, i + span):
            vis[j] = "1"
        out.append(f'<text class="m" x="{ox}" y="{ly}" font-size="12" fill="{t["lv"][3] if g else t["muted"]}" opacity="{vis[0]}">'
                   f'{label}<animate attributeName="opacity" dur="{dur:.1f}s" repeatCount="indefinite" '
                   f'calcMode="discrete" values="{";".join(vis)}"/></text>')
    lx = w - 24 - 5 * 15 - 40
    out.append(f'<text class="m" x="{lx - 8}" y="{ly}" font-size="11" fill="{t["muted"]}" text-anchor="end">Less</text>')
    for i in range(5):
        out.append(cell(lx + i * 15, ly - 10, 12, t["lv"][i]))
    out.append(f'<text class="m" x="{lx + 5 * 15 + 4}" y="{ly}" font-size="11" fill="{t["muted"]}">More</text>')
    h = ly + 26
    out[0] = f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}"/>'
    return svg(w, h, "".join(out),
               f"My contribution calendar: {data['total']:,} contributions, longest streak {best} days. "
               "It then evolves under Conway's Game of Life and loops.")


# ---------------------------------------------------------------- languages


def stack(t, data):
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:8]
    total = sum(n for _, n in data["langs"].items()) or 1
    w, pad, pitch, size, cells = 900, 28, 17, 13, 36
    out = [f'<text x="{pad}" y="40" font-size="18" font-weight="700" fill="{t["text"]}">Code by language</text>'
           f'<text x="{pad}" y="62" font-size="13" fill="{t["muted"]}">Bytes across my {data["repos"]} public repos. '
           "Brighter squares, more code.</text>"]
    top = langs[0][1] if langs else 1
    for i, (lang, n) in enumerate(langs):
        y = 92 + i * 26
        out.append(f'<circle cx="{pad + 5}" cy="{y + 6}" r="5" fill="{LANG_COLORS.get(lang, t["muted"])}"/>'
                   f'<text x="{pad + 18}" y="{y + 11}" font-size="14" fill="{t["text"]}">{escape(lang)}</text>')
        filled = max(1, round(cells * math.sqrt(n / top)))
        for c in range(cells):
            lv = 0 if c >= filled else 1 + min(3, int(4 * c / cells))
            out.append(cell(pad + 140 + c * pitch, y, size, t["lv"][lv],
                            f' class="c" style="animation-delay:{(i * 0.08 + c * 0.015):.2f}s"'))
        out.append(f'<text class="m" x="{w - pad}" y="{y + 11}" font-size="13" fill="{t["muted"]}" text-anchor="end">'
                   f"{100 * n / total:.1f}%</text>")
    h = 92 + len(langs) * 26 + 18
    css = "@keyframes in{from{opacity:0}to{opacity:1}}.c{animation:in .35s ease-out both}"
    summary = ", ".join(f"{lang} {100 * n / total:.0f}%" for lang, n in langs)
    return svg(w, h, f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}"/>' + "".join(out),
               f"Code by language: {summary}.", css)


# ---------------------------------------------------------------- work with me


def hire(t, data):
    w, h, pad = 900, 250, 28
    out = [f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}"/>']
    # The empty square: the next contribution.
    s = 92
    out.append(f'<rect class="slot" x="{pad}" y="{pad + 6}" width="{s}" height="{s}" rx="10" fill="none" '
               f'stroke="{t["lv"][3]}" stroke-width="2.5" stroke-dasharray="8 6"/>'
               f'<text x="{pad + s / 2}" y="{pad + s / 2 + 22}" font-size="44" font-weight="300" '
               f'fill="{t["lv"][3]}" text-anchor="middle" class="plus">+</text>')
    out.append(f'<text x="{pad + s + 24}" y="{pad + 36}" font-size="22" font-weight="700" fill="{t["text"]}">'
               "This square is empty. It's for your project.</text>"
               f'<text x="{pad + s + 24}" y="{pad + 62}" font-size="14" fill="{t["muted"]}">'
               "Open to internships, freelance and project-based roles: security tooling,</text>"
               f'<text x="{pad + s + 24}" y="{pad + 82}" font-size="14" fill="{t["muted"]}">'
               "AI-agent infrastructure and full-stack products. Bangalore or remote.</text>")
    steps = [("01", "Scope", "one-page spec,", "clear milestones"),
             ("02", "Build", "small commits,", "tests as I go"),
             ("03", "Ship", "a live demo", "you can click"),
             ("04", "Hand off", "README, docs,", "a walkthrough")]
    col = (w - pad * 2) / 4
    for i, (num, name, a, b) in enumerate(steps):
        x, y = pad + i * col, 156
        out.append(cell(x, y, 18, t["lv"][i + 1], f' class="c" style="animation-delay:{0.3 + i * 0.25:.2f}s"'))
        out.append(f'<text class="m" x="{x + 28}" y="{y + 14}" font-size="12" fill="{t["faint"]}">{num}</text>'
                   f'<text x="{x + 54}" y="{y + 15}" font-size="16" font-weight="700" fill="{t["text"]}">{name}</text>'
                   f'<text x="{x}" y="{y + 44}" font-size="13" fill="{t["muted"]}">{a}</text>'
                   f'<text x="{x}" y="{y + 62}" font-size="13" fill="{t["muted"]}">{b}</text>')
        if i < 3:
            out.append(f'<path d="M{x + col - 34} {y + 9}h18" stroke="{t["border"]}" stroke-width="2"/>')
    css = ("@keyframes dash{to{stroke-dashoffset:-28}}@keyframes in{from{opacity:0}to{opacity:1}}"
           "@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}"
           ".slot{animation:dash 1.6s linear infinite}.plus{animation:blink 2s ease-in-out infinite}"
           ".c{animation:in .5s ease-out both}")
    return svg(w, h, "".join(out), "Open to internships, freelance and project-based roles. "
               "How I work: scope, build, ship a live demo, hand off.", css)


# ---------------------------------------------------------------- main


def slug(name):
    return name.lower().replace("_", "-")


STAGE1 = base64.b64encode(b"STAGE 1/3 :: nice, you decoded base64. the city is more than a picture: "
                        b"open assets/city.svg as raw text and read its <desc> element. it is hex.").decode()


BANNERS = [
    ("whoami", "WHOAMI", "$ neofetch"),
    ("shipped", "SHIPPED", "10 projects · one neon grid each"),
    ("play", "BUGSWEEPER", "a game you play by opening issues"),
    ("alive", "ALIVE", "my year, run through Conway's rules"),
    ("wall", "THE WALL", "leave a square"),
    ("ctf", "CTF", "three stages · one flag"),
    ("stack", "STACK", "bytes by language"),
    ("hire", "HIRE ME", "the empty square is yours"),
]


def draw_wall():
    import crazy
    visitors = crazy.load_wall()
    for mode, t in THEMES.items():
        (ASSETS / f"wall-{mode}.svg").write_text(crazy.wall(t, visitors), encoding="utf-8")


def main():
    ASSETS.mkdir(exist_ok=True)
    if "--wall" in sys.argv:
        return draw_wall()
    import crazy
    data = fetch()
    (ASSETS / "city.svg").write_text(crazy.city(data), encoding="utf-8")
    import neofetch
    (ASSETS / "neofetch.svg").write_text(neofetch.neofetch(data), encoding="utf-8")
    for slug_, text, sub in BANNERS:
        (ASSETS / f"b-{slug_}.svg").write_text(neofetch.banner(text, sub), encoding="utf-8")
    solvers = ROOT / "ctf" / "solvers.json"
    solved = len(json.loads(solvers.read_text())) if solvers.exists() else 0
    (ASSETS / "ctf.svg").write_text(crazy.ctf_banner(STAGE1, solved), encoding="utf-8")
    draw_wall()
    for mode, t in THEMES.items():
        (ASSETS / f"year-{mode}.svg").write_text(year(t, data), encoding="utf-8")
        (ASSETS / f"stack-{mode}.svg").write_text(stack(t, data), encoding="utf-8")
        (ASSETS / f"hire-{mode}.svg").write_text(hire(t, data), encoding="utf-8")
        for p in data["projects"]:
            (ASSETS / f"p-{slug(p['name'])}-{mode}.svg").write_text(project_card(t, p), encoding="utf-8")
    print(f"drew {len(list(ASSETS.glob('*.svg')))} images, {data['total']} contributions")


if __name__ == "__main__":
    main()
