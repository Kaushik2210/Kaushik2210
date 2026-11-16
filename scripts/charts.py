"""Activity charts drawn from real commits: commits per month, when I code, top projects, languages."""

import datetime as dt
import math
from collections import Counter
from html import escape

import palette as P
from build import OWNER, TODAY, rest, svg

IST = dt.timedelta(hours=5, minutes=30)
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def panel(w, h, title, sub, body, css="", label=""):
    head = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{P.PANEL}" stroke="{P.BORDER}"/>'
            f'<text x="28" y="40" font-size="18" font-weight="700" fill="{P.TEXT}">{escape(title)}</text>'
            f'<text x="28" y="62" font-size="13" fill="{P.FAINT}">{escape(sub)}</text>')
    css += "@keyframes in{from{opacity:0}to{opacity:1}}.in{animation:in .6s ease-out both}"
    return svg(w, h, head + body, label or f"{title}. {sub}", css)


# ---------------------------------------------------------------- data


def fetch_activity(data):
    """Commit timestamps per repo for the last 12 months, my commits only."""
    since = (TODAY - dt.timedelta(days=365)).isoformat() + "T00:00:00Z"
    repos, times = Counter(), []
    for r in data["repo_list"]:
        if (r.get("pushed_at") or "") < since or r.get("size", 0) == 0:
            continue
        commits = rest(f"/repos/{OWNER}/{r['name']}/commits?author={OWNER}&since={since}&per_page=100")
        for c in commits if isinstance(commits, list) else []:
            stamp = c["commit"]["author"]["date"]
            times.append(dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")) + IST)
            repos[r["name"]] += 1
    langs = {r["name"]: r.get("language") for r in data["repo_list"]}
    return {"repos": repos, "times": times, "langs": langs}


# ---------------------------------------------------------------- commits per month


def monthly(data):
    counts = Counter()
    for w in data["weeks"]:
        for d, n, _ in w:
            counts[(d.year, d.month)] += n
    months = []
    y, m = TODAY.year, TODAY.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    vals = [counts.get(k, 0) for k in months]
    hi = max(vals) or 1
    peak = vals.index(hi)
    W, H = 1000, 340
    left, right, top, bottom = 70, 30, 96, 290
    ch = bottom - top
    step = (W - left - right) / 12
    bw = step * 0.62
    nice = 10 ** int(math.log10(hi)) if hi >= 10 else 1
    ceil = math.ceil(hi / nice) * nice
    out = []
    for i in range(5):  # gridlines
        v = ceil * i / 4
        y = bottom - ch * v / ceil
        out.append(f'<path d="M{left} {y:.1f}H{W - right}" stroke="{P.BORDER}" stroke-dasharray="{"" if i == 0 else "3 5"}"/>'
                   f'<text x="{left - 10}" y="{y + 4:.1f}" font-size="11" fill="{P.FAINT}" text-anchor="end">{int(v):,}</text>')
    for i, ((yy, mm), v) in enumerate(zip(months, vals)):
        x = left + i * step + (step - bw) / 2
        h = ch * v / ceil
        col = P.GOLD if i == peak else P.BLUE
        out.append(f'<rect class="bar" x="{x:.1f}" y="{bottom - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="4" '
                   f'fill="{col}" style="animation-delay:{i * 0.05:.2f}s"/>')
        if v:
            out.append(f'<text class="in" x="{x + bw / 2:.1f}" y="{bottom - h - 8:.1f}" font-size="12" font-weight="600" '
                       f'fill="{P.GOLD if i == peak else P.MUTED}" text-anchor="middle" '
                       f'style="animation-delay:{0.5 + i * 0.05:.2f}s">{v:,}</text>')
        lab = dt.date(yy, mm, 1).strftime("%b")
        out.append(f'<text x="{x + bw / 2:.1f}" y="{bottom + 22}" font-size="12" fill="{P.MUTED}" text-anchor="middle">{lab}</text>')
    total = sum(vals)
    pm = dt.date(*months[peak], 1).strftime("%B %Y")
    css = ("@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
           ".bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow .8s cubic-bezier(.2,.8,.2,1) both}")
    return panel(W, H, "Contributions per month", f"{total:,} in the last 12 months · busiest: {pm} ({hi:,}) · {TODAY.strftime('%b')} so far",
                 "".join(out), css)


# ---------------------------------------------------------------- when I code


def punchcard(act):
    grid = Counter((t.weekday(), t.hour) for t in act["times"])
    hi = max(grid.values(), default=1)
    W, H = 1000, 330
    left, top, cw, rh = 70, 96, 37, 30
    out = []
    for r, name in enumerate(DAYS):
        y = top + r * rh
        out.append(f'<text x="{left - 14}" y="{y + 4}" font-size="12" fill="{P.MUTED}" text-anchor="end">{name}</text>')
        out.append(f'<path d="M{left} {y}H{left + 23 * cw}" stroke="{P.BORDER}" stroke-opacity=".6"/>')
        for h in range(24):
            n = grid.get((r, h), 0)
            if not n:
                continue
            rad = 2.5 + 10.5 * math.sqrt(n / hi)
            col = P.GOLD if n >= hi * 0.75 else (P.SKY if n >= hi * 0.35 else P.BLUE)
            out.append(f'<circle class="dot" cx="{left + h * cw}" cy="{y}" r="{rad:.1f}" fill="{col}" '
                       f'fill-opacity="{0.55 + 0.45 * n / hi:.2f}" style="animation-delay:{h * 0.02 + r * 0.03:.2f}s"/>')
    for h in range(0, 24, 3):
        lab = f"{h:02d}:00"
        out.append(f'<text x="{left + h * cw}" y="{top + 7 * rh + 6}" font-size="11" fill="{P.FAINT}" text-anchor="middle">{lab}</text>')
    if grid:
        (pd, ph), _ = grid.most_common(1)[0]
        by_hour = Counter(t.hour for t in act["times"])
        night = sum(v for k, v in by_hour.items() if k >= 21 or k < 5)
        share = 100 * night // max(1, len(act["times"]))
        sub = f"{len(act['times']):,} commits by hour, IST · peak {DAYS[pd]} {ph:02d}:00 · {share}% after 9 pm"
    else:
        sub = "no commits found"
    css = ("@keyframes pop{from{transform:scale(0)}to{transform:scale(1)}}"
           ".dot{transform-box:fill-box;transform-origin:center;animation:pop .5s ease-out both}")
    return panel(W, H, "When I code", sub, "".join(out), css)


# ---------------------------------------------------------------- top projects


def top_projects(act):
    top = act["repos"].most_common(8)
    W, H = 600, 380
    left, top_y, rh = 28, 92, 34
    hi = top[0][1] if top else 1
    out = []
    for i, (name, n) in enumerate(top):
        y = top_y + i * rh
        lang = act["langs"].get(name)
        out.append(f'<circle cx="{left + 5}" cy="{y + 5}" r="4.5" fill="{P.LANG.get(lang, P.FAINT)}"/>'
                   f'<text x="{left + 16}" y="{y + 10}" font-size="13" fill="{P.TEXT}">{escape(name[:22])}</text>')
        bx, bwmax = 220, W - 220 - 80
        bw = max(4, bwmax * n / hi)
        out.append(f'<rect x="{bx}" y="{y - 2}" width="{bwmax}" height="14" rx="7" fill="{P.RAISED}"/>'
                   f'<rect class="bar" x="{bx}" y="{y - 2}" width="{bw:.1f}" height="14" rx="7" '
                   f'fill="{P.GOLD if i == 0 else P.BLUE}" style="animation-delay:{i * 0.07:.2f}s"/>'
                   f'<text x="{W - 28}" y="{y + 10}" font-size="13" font-weight="600" fill="{P.MUTED}" '
                   f'text-anchor="end">{n:,}</text>')
    css = ("@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
           ".bar{transform-box:fill-box;transform-origin:0 50%;animation:grow .8s cubic-bezier(.2,.8,.2,1) both}")
    total = sum(act["repos"].values())
    return panel(W, H, "Top projects", f"by my commits, last 12 months · {total:,} total", "".join(out), css,
                 "Top projects by commits: " + ", ".join(f"{n} {c}" for n, c in top))


# ---------------------------------------------------------------- languages donut


def donut(data):
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])
    total = sum(n for _, n in langs) or 1
    main = langs[:6]
    other = total - sum(n for _, n in main)
    if other > 0:
        main.append(("Other", other))
    W, H = 600, 380
    cx, cy, r, sw = 160, 220, 92, 30
    circ = 2 * math.pi * r
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{P.RAISED}" stroke-width="{sw}"/>']
    offset = 0
    for i, (lang, n) in enumerate(main):
        frac = n / total
        col = P.LANG.get(lang, P.FAINT)
        seg = max(0, circ * frac - 2)
        out.append(f'<circle class="seg" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" '
                   f'stroke-dasharray="{seg:.1f} {circ:.1f}" stroke-dashoffset="{-offset:.1f}" '
                   f'transform="rotate(-90 {cx} {cy})" style="animation-delay:{i * 0.08:.2f}s"/>')
        offset += circ * frac
        ly = 112 + i * 34
        out.append(f'<rect x="330" y="{ly - 10}" width="12" height="12" rx="3" fill="{col}"/>'
                   f'<text x="352" y="{ly}" font-size="14" fill="{P.TEXT}">{escape(lang)}</text>'
                   f'<text x="{W - 28}" y="{ly}" font-size="14" font-weight="600" fill="{P.MUTED}" '
                   f'text-anchor="end">{100 * frac:.1f}%</text>')
    top_lang, top_n = langs[0] if langs else ("-", 0)
    out.append(f'<text x="{cx}" y="{cy - 2}" font-size="26" font-weight="700" fill="{P.TEXT}" text-anchor="middle">'
               f'{100 * top_n / total:.0f}%</text>'
               f'<text x="{cx}" y="{cy + 20}" font-size="12" fill="{P.MUTED}" text-anchor="middle">{escape(top_lang)}</text>')
    css = ("@keyframes seg{from{opacity:0}to{opacity:1}}.seg{animation:seg .6s ease-out both}")
    return panel(W, H, "Languages", f"code by bytes across {data['repos']} public repos", "".join(out), css,
                 "Languages: " + ", ".join(f"{l} {100 * n / total:.0f}%" for l, n in main))
