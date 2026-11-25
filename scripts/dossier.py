"""Render a mounted GitHub portrait and a tear-off contribution record."""
from collections import Counter
from datetime import date
from pathlib import Path
import sys
from xml.sax.saxutils import escape

import common


def label(x, y, value, size=16, style="body", anchor="start"):
    return (f'<text x="{x}" y="{y}" class="{style}" font-size="{size}" '
            f'text-anchor="{anchor}">{escape(str(value))}</text>')


DEFS = """<defs>
<linearGradient id="cloth" x2=".85" y2="1">
  <stop stop-color="#373b40"/><stop offset=".55" stop-color="#24282d"/><stop offset="1" stop-color="#191d22"/>
</linearGradient>
<linearGradient id="mount" x2=".3" y2="1">
  <stop stop-color="#faf4e8"/><stop offset=".78" stop-color="#e7decb"/><stop offset="1" stop-color="#c6bca7"/>
</linearGradient>
<linearGradient id="paper" x2="1" y2=".3">
  <stop stop-color="#dcd4c3"/><stop offset=".08" stop-color="#f0e9d9"/><stop offset=".8" stop-color="#e9e2d4"/><stop offset="1" stop-color="#dad2bf"/>
</linearGradient>
<linearGradient id="clip" x1="0" y1="0" x2="1" y2=".4">
  <stop stop-color="#604b34"/><stop offset=".24" stop-color="#ddbb83"/><stop offset=".48" stop-color="#fff1cb"/><stop offset=".78" stop-color="#a18559"/><stop offset="1" stop-color="#534332"/>
</linearGradient>
<pattern id="weave" width="5" height="5" patternUnits="userSpaceOnUse">
  <path d="M0 1h5" stroke="#fff" opacity=".035"/><path d="M2 0v5" stroke="#000" opacity=".09"/>
</pattern>
<pattern id="ruling" width="14" height="14" patternUnits="userSpaceOnUse">
  <path d="M0 0h14M0 0v14" fill="none" stroke="#797369" stroke-opacity=".19"/>
</pattern>
<style>
text{font-family:'Segoe UI',Arial,sans-serif;fill:#f5f1e9}
.name,.number{font-family:Georgia,'Times New Roman',serif}
.number{fill:#2a3134}
.meta,.ink,.pencil,.caps{font-family:Consolas,'Liberation Mono',monospace}
.meta{fill:#c6cad0}.caps{fill:#dbbf90;letter-spacing:1.3px}
.ink{fill:#343a3c}.pencil{fill:#534d43}.soft{fill:#cbd0d6}
@media(prefers-reduced-motion:no-preference){.trace{animation:develop 1.1s ease-out both}
@keyframes develop{from{opacity:.4}to{opacity:1}}}
</style></defs>"""


def mounted_photo(uri, x, y, scale):
    # The original portrait includes the illuminated map above the subject.
    # Keep some of that setting in the print, and retain the original colours.
    return f"""<g transform="translate({x} {y}) scale({scale}) rotate(-3 113 133)">
<rect x="4" y="7" width="228" height="268" rx="2" fill="#080a0d" opacity=".50"/>
<rect x="2" y="3" width="228" height="268" rx="2" fill="#111318" opacity=".72"/>
<rect width="228" height="268" rx="2" fill="url(#mount)" stroke="#ede6d8"/>
<svg x="10" y="10" width="208" height="219" viewBox="48 85 365 375" preserveAspectRatio="xMidYMid slice">
  <image width="460" height="460" xlink:href="{uri}"/>
</svg>
<rect x="10" y="10" width="208" height="219" fill="none" stroke="#27221d" stroke-opacity=".3"/>
{label(14, 252, "GitHub portrait", 14, "pencil")}
<path d="M180 246h32" stroke="#8a8170"/>
<g transform="translate(164 -12) rotate(14)" fill="none" stroke-linecap="round">
  <path id="wire" d="M2 8v36a6 6 0 0 0 12 0V5a9 9 0 0 0-18 0v34" />
  <use xlink:href="#wire" transform="translate(1.3 2)" stroke="#13110f" stroke-width="4" opacity=".5"/>
  <use xlink:href="#wire" stroke="url(#clip)" stroke-width="3"/>
</g></g>"""


def record(x, y, width, rows):
    parts = []
    for i, (title, value) in enumerate(rows):
        baseline = y + i * 33
        parts += [f'<path d="M{x} {baseline + 10}h{width}" stroke="#555a60"/>',
                  label(x, baseline, title, 15, "soft"),
                  label(x + width, baseline, value, 16, "body", "end")]
    return "".join(parts)


def activity(x, y, width, days, compact):
    height = 158
    # A continuous cut edge and two punched ends give the chart the feel of
    # a recorder slip without laying any texture across its labels.
    bottom = " ".join(f"L{i} {height - (i // 5 % 2) * 2}" for i in range(width, -1, -5))
    paper = f"M0 0H{width}V{height} {bottom} H0Z"
    parts = [f'<g transform="translate({x} {y})">',
             f'<path d="{paper}" transform="translate(2 4)" fill="#0d1013" opacity=".7"/>',
             f'<path d="{paper}" fill="url(#paper)"/>']
    pad = 20 if compact else 30
    for edge in (8, width - 8):
        for row in range(16, height - 4, 20):
            parts.append(f'<circle cx="{edge}" cy="{row}" r="2.6" fill="#303438"/>')
    parts.append(label(pad, 27, "Contribution record", 20, "number"))
    if not days:
        parts += [label(pad, 83, "No calendar data available", 15, "ink"), "</g>"]
        return "".join(parts)
    count = sum(value for _, value in days)
    parts.append(label(width - pad, 27, f"{count:,} total", 14, "ink", "end"))
    peak = max(value for _, value in days)
    scale_space = max(25, 8 * len(f"{peak:,}") + 7)
    chart_x, chart_width, base = pad + scale_space, width - 2 * pad - scale_space, 118
    parts.append(f'<rect x="{chart_x}" y="43" width="{chart_width}" height="75" fill="url(#ruling)"/>')
    parts.append(f'<path d="M{chart_x} {base}h{chart_width}" stroke="#807a70"/>')
    parts.append(label(chart_x - 6, base, "0", 12, "pencil", "end"))
    if peak:
        parts.append(label(chart_x - 6, 50, f"{peak:,}", 12, "pencil", "end"))
    step = chart_width / len(days)
    for i, (_, value) in enumerate(days):
        if value:
            h = 73 * value / peak
            parts.append(f'<rect class="trace" x="{chart_x + (i + .15) * step:.2f}" y="{base - h:.2f}" '
                         f'width="{step * .70:.2f}" height="{h:.2f}" fill="#36576a"/>')
    def day_stamp(value):
        return date.fromisoformat(value).strftime("%d %b").lstrip("0")
    parts.extend([label(chart_x, 142, day_stamp(days[0][0]), 13, "pencil"),
                  label(width / 2, 142, "Daily contributions", 13, "pencil", "middle"),
                  label(width - pad, 142, day_stamp(days[-1][0]), 13, "pencil", "end"),
                  "</g>"])
    return "".join(parts)


def render(login, user, repos, uri, compact):
    days = common.days(user)
    current, best = common.streaks(days)
    commits = user["contributionsCollection"]["totalCommitContributions"]
    stars = sum(repo["stargazers_count"] for repo in repos)
    languages = Counter(repo["language"] for repo in repos if repo["language"])
    lead = languages.most_common(1)
    rows = [("Non-fork repos", f"{len(repos):,} repos  /  {stars:,} stars"),
            ("Commits · past year", f"{commits:,}"),
            ("Streak · now / best", f"{current}d  /  {best}d"),
            ("Top repo language", lead[0][0] if lead else "Unlisted")]
    year = date.fromisoformat(user["createdAt"][:10]).year
    width, height = (430, 635) if compact else (830, 524)
    x, y = (209, 103) if compact else (330, 92)
    title = "Kaushik" if login.lower() == "kaushik2210" else login
    name_size = min(61 if not compact else 37, (width - x - 22) * 1.55 / len(title))
    chart_y = 453 if compact else 344
    cc = user["contributionsCollection"]
    description = (f"{login} joined GitHub in {year}. {len(repos)} public non-fork repositories, "
                   f"{stars} stars and {commits} commit contributions in the past year. "
                   f"{cc['totalPullRequestContributions']} pull requests and {cc['totalIssueContributions']} issues "
                   f"in that period. {user['followers']['totalCount']} followers. "
                   f"{sum(v for _, v in days[-60:])} contributions in the latest {len(days[-60:])} calendar days.")
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(title)} · Operator dossier</title><desc id="desc">{escape(description)}</desc>',
             DEFS,
             f'<rect width="{width}" height="{height}" rx="12" fill="#111419"/>',
             f'<rect x="3" y="4" width="{width-6}" height="{height-8}" rx="10" fill="url(#cloth)" stroke="#4f5357"/>',
             f'<rect x="4" y="5" width="{width-8}" height="{height-10}" rx="10" fill="url(#weave)"/>',
             f'<rect x="11" y="12" width="{width-22}" height="{height-24}" rx="6" fill="none" '
             f'stroke="#9a978c" stroke-opacity=".34" stroke-dasharray="3 4"/>',
             mounted_photo(uri, 34 if compact else 55, 64 if compact else 43, .68 if compact else 1),
             label(x, y-27, "FIELD NOTES", 13, "caps"),
             label(x, y + 26, title, round(name_size, 1), "name"),
             label(x, y + 55, "@" + login, min(17, (width-x-18)*1.52/(len(login)+1)), "meta"),
             label(x, y + 85, f"On GitHub since {year}", 15, "soft")]
    if login.lower() == "kaushik2210":
        if compact:
            parts.extend([label(x, y + 112, "Security tooling", 16),
                          label(x, y + 132, "& developer tools", 16)])
        else:
            parts.append(label(x + 160, y + 85, "Security & developer tools", 15, "soft"))
    if compact:
        parts.append(record(30, 289, width - 60, rows))
    else:
        parts.append(record(x, 215, width - x - 43, rows))
    parts.append(activity(21 if compact else 27, chart_y, width - (42 if compact else 54), days[-60:], compact))
    return "\n".join(parts + ["</svg>"])


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
    target = Path(sys.argv[2] if len(sys.argv) > 2 else "assets/dossier.svg")
    user = common.user_graph(login)
    repos = common.repos(login)
    uri = common.avatar_data_uri(login)
    for compact, path in [(False, target), (True, target.with_name(f"{target.stem}-mobile.svg"))]:
        path.write_text(render(login, user, repos, uri, compact), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
