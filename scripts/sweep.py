#!/usr/bin/env python3
"""BUGSWEEPER: a community Minesweeper played on my README through issues.

Every square on the board is a link that opens an issue titled "[SWEEP] C7".
.github/workflows/sweep.yml runs this script on that issue: it reveals the square,
redraws the board in README.md, comments the result and closes the issue.

Untrusted input: only the issue title (regex-matched to a coordinate) and the
author's login (format-checked) are read. Nothing reaches a shell unquoted.

Local use:
  python scripts/sweep.py --render          redraw the README board from game/state.json
  python scripts/sweep.py --move C7 --as me play a move without GitHub (testing)
"""
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "game" / "state.json"
README = ROOT / "README.md"
CELLS = ROOT / "assets" / "sweep"
REPO = os.environ.get("GH_REPO", "Kaushik2210/Kaushik2210")
ROWS, COLS, BUGS = 8, 16, 20
LETTERS = "ABCDEFGHIJKLMNOP"
START, END = "<!--SWEEP_START-->", "<!--SWEEP_END-->"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
MOVE_RE = re.compile(r"^\[SWEEP\]\s*([A-Pa-p])\s*([1-8])\s*$")

HEAT = ["#0e4429", "#006d32", "#26a641", "#39d353"]


# ---------------------------------------------------------------- state


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def fresh(game_no):
    return {"game": game_no, "status": "playing", "bugs": None, "open": [], "boom": None,
            "moves": [], "started": now()}


def load():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"current": fresh(1), "history": [], "players": {}}


def save(db):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(db, indent=1), encoding="utf-8")


def label(r, c):
    return f"{LETTERS[c]}{r + 1}"


def neighbours(r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < ROWS and 0 <= c + dc < COLS:
                yield r + dr, c + dc


def count(bugs, r, c):
    return sum(1 for n in neighbours(r, c) if n in bugs)


# ---------------------------------------------------------------- moves


def play(db, login, r, c):
    """Apply a move. Returns a short message for the issue comment."""
    g = db["current"]
    if g["status"] != "playing":
        db["current"] = g = fresh(g["game"] + 1)
    if g["bugs"] is None:  # first click is always safe: bugs avoid its 3x3
        safe = {(r, c), *neighbours(r, c)}
        spots = [(i, j) for i in range(ROWS) for j in range(COLS) if (i, j) not in safe]
        g["bugs"] = [list(p) for p in random.SystemRandom().sample(spots, BUGS)]

    bugs = {tuple(b) for b in g["bugs"]}
    opened = {tuple(o) for o in g["open"]}
    p = db["players"].setdefault(login, {"moves": 0, "wins": 0, "booms": 0})
    sq = label(r, c)

    if (r, c) in opened:
        return f"**{sq}** is already open. Pick a dark square."

    p["moves"] += 1
    g["moves"].append({"by": login, "sq": sq, "at": now()})

    if (r, c) in bugs:
        g["status"], g["boom"] = "lost", [r, c]
        p["booms"] += 1
        db["history"].append({"game": g["game"], "result": "lost", "by": login,
                              "moves": len(g["moves"]), "at": now()})
        return (f"\U0001F4A5 **{sq} was a bug.** Game {g['game']} is over after {len(g['moves'])} moves. "
                "Click any square on the board to start the next game.")

    stack = [(r, c)]  # flood-fill zeros
    while stack:
        cur = stack.pop()
        if cur in opened:
            continue
        opened.add(cur)
        if count(bugs, *cur) == 0:
            stack.extend(n for n in neighbours(*cur) if n not in opened and n not in bugs)
    g["open"] = sorted([list(o) for o in opened])

    left = ROWS * COLS - BUGS - len(opened)
    if left == 0:
        g["status"] = "won"
        team = sorted({m["by"] for m in g["moves"]})
        for who in team:
            db["players"].setdefault(who, {"moves": 0, "wins": 0, "booms": 0})["wins"] += 1
        db["history"].append({"game": g["game"], "result": "won", "by": login,
                              "moves": len(g["moves"]), "at": now()})
        return (f"\U0001F3C6 **Board cleared!** {sq} was the last safe square. Everyone who played game "
                f"{g['game']} gets a win: " + ", ".join(f"@{t}" for t in team))
    n = count(bugs, r, c)
    return f"\U0001F7E9 **{sq} is safe** ({n} bug{'s' if n != 1 else ''} next to it). {left} safe squares left."


# ---------------------------------------------------------------- rendering


def cell_svg(fill, text="", text_fill="#ffffff", stroke=None, extra=""):
    s = f' stroke="{stroke}" stroke-width="1.5"' if stroke else ""
    t = (f'<text x="20" y="25.5" font-family="ui-monospace,Menlo,Consolas,monospace" font-size="14" '
         f'font-weight="700" fill="{text_fill}" text-anchor="middle">{text}</text>') if text else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">'
            f'<rect x="2" y="2" width="36" height="36" rx="5" fill="{fill}"{s}/>{t}{extra}</svg>')


BUG_ART = ["..#..#..", "...##...", ".######.", "#.####.#", ".######.", "#.####.#", ".######.", "..#..#.."]


def bug_art(color):
    return "".join(f'<rect x="{8 + c * 3}" y="{8 + r * 3}" width="3" height="3" fill="{color}"/>'
                   for r, row in enumerate(BUG_ART) for c, ch in enumerate(row) if ch == "#")


def write_cells():
    CELLS.mkdir(parents=True, exist_ok=True)
    for r in range(ROWS):
        for c in range(COLS):
            (CELLS / f"h-{label(r, c)}.svg").write_text(
                cell_svg("#161b22", label(r, c), "#3d444d", "#30363d"), encoding="utf-8")
    for n in range(9):
        fill = HEAT[min(3, (n + 1) // 2)] if n else "#0e4429"
        (CELLS / f"o{n}.svg").write_text(cell_svg(fill, str(n) if n else "", "#ffffff" if n < 3 else "#0d1117"),
                                         encoding="utf-8")
    (CELLS / "bug.svg").write_text(cell_svg("#161b22", stroke="#30363d", extra=bug_art("#8b949e")), encoding="utf-8")
    (CELLS / "boom.svg").write_text(cell_svg("#f85149", extra=bug_art("#0d1117")), encoding="utf-8")


def move_link(r, c):
    title = quote(f"[SWEEP] {label(r, c)}")
    body = quote("Just press **Create** (or Submit new issue). A bot makes your move and replies here within a minute.")
    return f"https://github.com/{REPO}/issues/new?title={title}&body={body}"


def board_html(g):
    bugs = {tuple(b) for b in (g["bugs"] or [])}
    opened = {tuple(o) for o in g["open"]}
    over = g["status"] != "playing"
    rows = []
    for r in range(ROWS):
        cells = []
        for c in range(COLS):
            sq = label(r, c)
            if (r, c) in opened:
                img, alt = f"o{count(bugs, r, c)}.svg", f"{sq}: open, {count(bugs, r, c)} bugs near"
            elif over and (r, c) in bugs:
                img = "boom.svg" if g["boom"] == [r, c] else "bug.svg"
                alt = f"{sq}: bug"
            else:
                img, alt = f"h-{sq}.svg", f"{sq}: hidden, click to reveal"
            cells.append(f'<a href="{move_link(r, c)}"><img src="assets/sweep/{img}" width="40" alt="{alt}"></a>')
        rows.append("".join(cells))
    return '<p align="center">' + "<br>".join(rows) + "</p>"


def render(db):
    g = db["current"]
    opened = len(g["open"])
    left = ROWS * COLS - BUGS - opened
    if g["status"] == "playing":
        head = (f"**Game {g['game']}** · {BUGS} bugs hidden · **{left}** safe squares left · "
                f"{len(g['moves'])} moves so far")
        if not g["moves"]:
            head += " · _first click is always safe_"
    elif g["status"] == "won":
        head = f"🏆 **Game {g['game']} cleared** in {len(g['moves'])} moves. Click any square to start game {g['game'] + 1}."
    else:
        last = g["moves"][-1]["by"]
        head = (f"💥 **Game {g['game']} lost** when @{last} hit a bug on move {len(g['moves'])}. "
                f"Click any square to start game {g['game'] + 1}.")

    recent = list(reversed(g["moves"][-5:]))
    moves = " · ".join(f"[@{m['by']}](https://github.com/{m['by']}) {m['sq']}" for m in recent) or "_no moves yet. be first._"

    top = sorted(db["players"].items(), key=lambda kv: (-kv[1]["wins"], -kv[1]["moves"], kv[1]["booms"]))[:8]
    board = ["| # | player | moves | boards cleared | bugs hit |", "|:-:|:--|:-:|:-:|:-:|"]
    medals = ["🥇", "🥈", "🥉"]
    for i, (who, s) in enumerate(top):
        board.append(f"| {medals[i] if i < 3 else i + 1} | [@{who}](https://github.com/{who}) | {s['moves']} | "
                     f"{s['wins']} | {s['booms']} |")
    if not top:
        board.append("| – | _you?_ | 0 | 0 | 0 |")

    games = len(db["history"])
    won = sum(1 for h in db["history"] if h["result"] == "won")
    block = f"""
<div align="center">

{head}

{board_html(g)}

<sub>Last moves: {moves}</sub>

</div>

<details>
<summary><b>How to play · leaderboard</b> ({games} games finished, {won} cleared)</summary>

<br>

1. Click any dark square. GitHub opens a new issue with the move already in the title.
2. Press **Create**. A bot reveals the square, redraws this board and replies to you, usually within a minute.
3. Numbers count the bugs touching that square. Clear every safe square to win. Hit a bug and the game resets.
4. Everyone who played a cleared board gets a win. Play as often as you like.

{chr(10).join(board)}

</details>
"""
    text = README.read_text(encoding="utf-8")
    a, b = text.index(START) + len(START), text.index(END)
    README.write_text(text[:a] + block + text[b:], encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- entry points


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
    m = MOVE_RE.match(issue.get("title") or "")
    if not m:
        gh("issue", "comment", num, "--body", "Couldn't read a square in that title. Click a square on the board to play.")
        gh("issue", "close", num, "--reason", "not planned")
        return
    r, c = int(m.group(2)) - 1, LETTERS.index(m.group(1).upper())
    db = load()
    msg = play(db, login, r, c)
    save(db)
    render(db)
    gh("issue", "comment", num, "--body",
       msg + f"\n\n[Back to the board](https://github.com/{REPO.split('/')[0]}#bugsweeper)")
    gh("issue", "close", num, "--reason", "completed")
    print(login, "->", label(r, c), "|", msg)


def main():
    if "--cells" in sys.argv:
        write_cells()
    if "--move" in sys.argv:
        sq = sys.argv[sys.argv.index("--move") + 1]
        who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "tester"
        db = load()
        print(play(db, who, int(sq[1:]) - 1, LETTERS.index(sq[0].upper())))
        save(db)
        render(db)
    elif "--render" in sys.argv:
        render(load())
    elif "GITHUB_EVENT_PATH" in os.environ:
        from_issue()


if __name__ == "__main__":
    main()
