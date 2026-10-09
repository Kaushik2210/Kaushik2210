#!/usr/bin/env python3
"""Rewrite the ACTIVE.OPS block of README.md: expandable cards for recent repos.

Uses plain <details>/<summary>, the one genuinely interactive element GitHub
READMEs allow. Rebuilt on every showcase run from the live repo list.
Usage: explorer.py [user] [README.md]
"""
import html
import sys
from datetime import datetime, timezone

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
README = sys.argv[2] if len(sys.argv) > 2 else "README.md"
START, END = "<!--OPS_START-->", "<!--OPS_END-->"
LIMIT = 8
ICON = {"Python": "🐍", "TypeScript": "🔷", "JavaScript": "🟨", "Java": "☕", "HTML": "🌐", "C": "⚙️", "Jupyter Notebook": "📓"}


def ago(days):
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 60:
        return f"{days}d ago"
    return f"{days // 30}mo ago"


def card(r, now):
    pushed = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
    days = max(0, (now - pushed).days)
    lang = r["language"] or "misc"
    desc = html.escape((r["description"] or "No description yet. Still cooking.").strip())
    topics = " ".join(f"`{t}`" for t in (r.get("topics") or [])[:6])
    links = [f"[repo]({r['html_url']})"]
    if r.get("homepage"):
        links.append(f"[live]({html.escape(r['homepage'], quote=True)})")
    links.append(f"[commits]({r['html_url']}/commits)")
    stars = r["stargazers_count"]
    return (f"<details>\n<summary>{ICON.get(lang, '📦')} <b>{html.escape(r['name'])}</b> &nbsp;·&nbsp; "
            f"<code>{html.escape(lang)}</code> &nbsp;·&nbsp; ⭐ {stars} &nbsp;·&nbsp; pushed {ago(days)}</summary>\n\n"
            f"> {desc}\n\n{topics + ' &nbsp;·&nbsp; ' if topics else ''}{' · '.join(links)}\n\n</details>")


def main():
    now = datetime.now(timezone.utc)
    rp = [r for r in common.repos(USER) if r["name"].lower() != USER.lower()]
    rp.sort(key=lambda r: r["pushed_at"], reverse=True)
    block = "\n\n".join(card(r, now) for r in rp[:LIMIT])
    text = open(README, encoding="utf-8").read()
    a, b = text.index(START) + len(START), text.index(END)
    new = text[:a] + "\n" + block + "\n" + text[b:]
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
    print(f"explorer: {min(LIMIT, len(rp))} cards, newest {rp[0]['name']} ({ago(max(0, (now - datetime.fromisoformat(rp[0]['pushed_at'].replace('Z', '+00:00'))).days))})")


if __name__ == "__main__":
    main()
