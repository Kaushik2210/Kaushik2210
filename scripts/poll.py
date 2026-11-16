#!/usr/bin/env python3
"""Community vote: "What should I build next?"

Each idea card in the README is a link that opens an issue titled "[VOTE] <id>".
.github/workflows/poll.yml runs this on that issue: it records one vote per login
(voting again switches it), redraws the cards and the README block, comments, closes.

Untrusted input: only the issue title (matched against the known option ids) and the
author's login (format-checked) are read. Nothing reaches a shell unquoted.

Local use:  python scripts/poll.py --render
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme as t  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OPTIONS = ROOT / "data" / "poll.json"
VOTES = ROOT / "poll" / "votes.json"
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
REPO = os.environ.get("GH_REPO", "Kaushik2210/Kaushik2210")
START, END = "<!--POLL_START-->", "<!--POLL_END-->"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
VOTE_RE = re.compile(r"^\[VOTE\]\s*([a-z0-9-]{1,40})\s*$")


def load():
    poll = json.loads(OPTIONS.read_text(encoding="utf-8"))
    votes = json.loads(VOTES.read_text(encoding="utf-8")) if VOTES.exists() else {}
    return poll, votes


def tally(poll, votes):
    counts = {o["id"]: 0 for o in poll["options"]}
    for v in votes.values():
        if v["opt"] in counts:
            counts[v["opt"]] += 1
    return counts


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


# ---------------------------------------------------------------- drawing


def card(i, opt, n, total, leader):
    W, H = 405, 178
    pct = 100 * n / total if total else 0
    lead = leader and n > 0
    bar_w = (W - 56) * pct / 100
    fill = t.A3 if lead else "url(#aurora)"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="{escape(opt["title"])}: {n} votes. Click to vote.">',
        f'<title>{escape(opt["title"])}: {n} vote{"s" if n != 1 else ""} ({pct:.0f}%). Click to vote.</title>',
        t.defs('<style>@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}'
               '.bar{transform-box:fill-box;transform-origin:0 50%;animation:grow 1s cubic-bezier(.2,.8,.2,1) both}'
               '@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}.cta{animation:pulse 2.6s ease-in-out infinite}'
               '@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>'),
        f'<rect width="{W}" height="{H}" rx="14" fill="{t.SURFACE}"/>',
        f'<rect width="4" height="{H}" rx="2" fill="{t.A3 if lead else t.A1}" opacity="{1 if lead else .7}"/>',
        f'<text x="28" y="32" class="label">IDEA {i + 1:02d}</text>',
    ]
    if lead:
        out.append(f'<text x="{W - 28}" y="32" class="label" text-anchor="end" style="fill:{t.A3}">★ LEADING</text>')
    out.append(f'<text x="28" y="62" font-size="{t.T_TITLE}" font-weight="700" fill="{t.TEXT}">{escape(opt["title"])}</text>')
    for k, line in enumerate(wrap(opt["desc"], 52)[:2]):
        out.append(f'<text x="28" y="{88 + k * 18}" font-size="{t.T_BODY}" fill="{t.TEXT2}">{escape(line)}</text>')
    y = 128
    out.append(f'<rect x="28" y="{y}" width="{W - 56}" height="8" rx="4" fill="{t.RAISED}"/>')
    if n:
        glow = ' filter="url(#glow)"' if lead else ""
        out.append(f'<rect class="bar" x="28" y="{y}" width="{bar_w:.1f}" height="8" rx="4" fill="{fill}"{glow}/>')
    out.append(f'<text x="28" y="{y + 30}" class="mono" font-size="{t.T_CAP + 1}" fill="{t.TEXT}">'
               f'<tspan font-weight="700">{n}</tspan><tspan fill="{t.TEXT3}"> vote{"s" if n != 1 else ""} · {pct:.0f}%</tspan></text>')
    out.append(f'<text class="cta mono" x="{W - 28}" y="{y + 30}" font-size="{t.T_CAP + 1}" fill="{t.A2}" '
               f'text-anchor="end">click to vote →</text>')
    out += [t.card_border(W, H, 14), "</svg>"]
    return "".join(out)


def vote_link(opt):
    title = quote(f"[VOTE] {opt['id']}")
    body = quote(f"Voting for **{opt['title']}**. Just press **Create**; a bot counts it and replies within a minute. "
                 "Vote again any time to switch.")
    return f"https://github.com/{REPO}/issues/new?title={title}&body={body}"


def render(poll, votes):
    counts = tally(poll, votes)
    total = sum(counts.values())
    top = max(counts.values()) if counts else 0
    ASSETS.mkdir(exist_ok=True)
    cells = []
    for i, o in enumerate(poll["options"]):
        (ASSETS / f"vote-{o['id']}.svg").write_text(
            card(i, o, counts[o["id"]], total, counts[o["id"]] == top), encoding="utf-8")
        cells.append(f'<a href="{vote_link(o)}"><img src="assets/vote-{o["id"]}.svg" '
                     f'alt="{escape(o["title"])}: {counts[o["id"]]} votes. Click to vote." width="49%"></a>')
    rows = [" ".join(cells[k:k + 2]) for k in range(0, len(cells), 2)]
    recent = sorted(votes.items(), key=lambda kv: kv[1]["at"], reverse=True)[:6]
    names = {o["id"]: o["title"] for o in poll["options"]}
    who = " · ".join(f"[@{l}](https://github.com/{l}) → {names.get(v['opt'], v['opt'])}" for l, v in recent) \
        or "_no votes yet. yours could be the first._"
    block = f"""
<div align="center">

**{escape(poll["question"])}** Click an idea to vote. One vote each; vote again to switch.

{"<br>".join(rows)}

<sub>{total} vote{"s" if total != 1 else ""} so far · latest: {who}</sub>

</div>
"""
    text = README.read_text(encoding="utf-8")
    a, b = text.index(START) + len(START), text.index(END)
    README.write_text(text[:a] + block + text[b:], encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- issue handler


def gh(*args):
    if os.environ.get("DRY_RUN"):
        print("gh", *args)
        return
    subprocess.run(["gh", *args], check=False)


def from_issue():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    issue = event["issue"]
    num, login = str(issue["number"]), issue["user"]["login"]
    if not LOGIN_RE.match(login):
        sys.exit("unexpected login format")
    poll, votes = load()
    ids = {o["id"]: o for o in poll["options"]}
    m = VOTE_RE.match(issue.get("title") or "")
    if not m or m.group(1) not in ids:
        gh("issue", "comment", num, "--body", "Couldn't find that idea. Click one of the cards on the profile to vote.")
        gh("issue", "close", num, "--reason", "not planned")
        return
    opt = ids[m.group(1)]
    before = votes.get(login, {}).get("opt")
    votes[login] = {"opt": opt["id"], "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}
    VOTES.parent.mkdir(exist_ok=True)
    VOTES.write_text(json.dumps(votes, indent=1, sort_keys=True), encoding="utf-8")
    render(poll, votes)
    counts = tally(poll, votes)
    lead_id = max(counts, key=counts.get)
    switched = f" (switched from **{ids[before]['title']}**)" if before and before != opt["id"] else ""
    gh("issue", "comment", num, "--body",
       f"\U0001F5F3 **Vote counted for {opt['title']}**{switched}, @{login}. "
       f"It has {counts[opt['id']]} vote{'s' if counts[opt['id']] != 1 else ''} now. "
       f"Currently leading: **{ids[lead_id]['title']}** ({counts[lead_id]}).\n\n"
       f"[See the results](https://github.com/{REPO.split('/')[0]}#vote)")
    gh("issue", "close", num, "--reason", "completed")
    print(login, "->", opt["id"])


if __name__ == "__main__":
    if "--render" in sys.argv:
        render(*load())
    elif "GITHUB_EVENT_PATH" in os.environ:
        from_issue()
