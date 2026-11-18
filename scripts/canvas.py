#!/usr/bin/env python3
"""The Night Canvas: an r/place-style pixel canvas the whole internet paints on my profile.

Every pixel in the README is its own link. It opens the "Paint a pixel" issue form with the
pixel already in the title ("[PAINT] H7"); the visitor picks a colour and presses Create.
.github/workflows/canvas.yml runs this script: it paints the pixel, redraws the canvas,
the timelapse and the README block, comments and closes the issue.

Untrusted input: only the issue title (regex: one cell) and the colour field (must be a
palette name) are read, plus the login (format-checked). Nothing reaches a shell unquoted.

Local use:  python scripts/canvas.py --render
            python scripts/canvas.py --paint H7 coral --as someone   (testing)
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
STATE = ROOT / "canvas" / "state.json"
README = ROOT / "README.md"
CELLS = ROOT / "assets" / "canvas"
TIMELAPSE = ROOT / "assets" / "canvas-timelapse.svg"
REPO = os.environ.get("GH_REPO", "Kaushik2210/Kaushik2210")
OWNER = REPO.split("/")[0]
COLS, ROWS = 24, 12
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWX"
START, END = "<!--CANVAS_START-->", "<!--CANVAS_END-->"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
TITLE_RE = re.compile(r"^\[PAINT\]\s*([A-Xa-x])\s*([0-9]{1,2})\s*$")
COLOUR_RE = re.compile(r"###\s*Colou?r\s*\n+\s*([A-Za-z]+)", re.I)

PALETTE = {  # name -> hex. "erase" puts the night back.
    "white": "#eceef4", "periwinkle": "#8b9cff", "lavender": "#c4b5fd", "champagne": "#f2c879",
    "yellow": "#fde68a", "orange": "#fdba74", "coral": "#fda4af", "red": "#ff5c6c",
    "mint": "#5eead4", "green": "#34d399", "sky": "#7dd3fc", "erase": None,
}
EMPTY = "#11141b"


def label(r, c):
    return f"{LETTERS[c]}{r + 1}"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def load():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"pixels": [[None] * COLS for _ in range(ROWS)], "history": []}


def save(st):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, separators=(",", ":")), encoding="utf-8")


def paint(st, login, r, c, colour):
    st["pixels"][r][c] = None if colour == "erase" else colour
    st["history"].append({"by": login, "cell": label(r, c), "colour": colour, "at": now()})


# ---------------------------------------------------------------- drawing


def write_cells():
    """One tiny image per colour; the README reuses them for every pixel."""
    CELLS.mkdir(parents=True, exist_ok=True)
    for name, hexv in list(PALETTE.items()) + [("empty", EMPTY)]:
        if name == "erase":
            continue
        glow = (f'<rect x="3" y="3" width="26" height="26" rx="5" fill="{hexv}" opacity=".35" filter="url(#g)"/>'
                if name != "empty" else "")
        stroke = ' stroke="#1d222d" stroke-width="1"' if name == "empty" else ""
        (CELLS / f"{name}.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
            '<defs><filter id="g"><feGaussianBlur stdDeviation="2"/></filter></defs>'
            f'{glow}<rect x="3" y="3" width="26" height="26" rx="5" fill="{hexv}"{stroke}/></svg>', encoding="utf-8")


def timelapse(st):
    """Replays every stroke in order, holds the finished canvas, then loops."""
    W, cell, pad = 830, 32, 31
    H = ROWS * cell + 96
    hist = st["history"][-400:]
    n = max(1, len(hist))
    dur = min(30, max(6, n * 0.25)) + 3          # replay, then a 3 s hold
    play = (dur - 3) / dur
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Timelapse of the Night Canvas: {len(st["history"])} pixels painted by visitors, replayed in order">',
         "<title>The Night Canvas: timelapse</title>",
         t.defs(), f'<rect width="{W}" height="{H}" rx="14" fill="{t.CANVAS}"/>',
         f'<text x="{pad}" y="34" class="label" style="fill:{t.TEXT2}">TIMELAPSE · {len(st["history"])} STROKES</text>']
    for r in range(ROWS):
        for c in range(COLS):
            o.append(f'<rect x="{pad + c * cell + 3}" y="{56 + r * cell + 3}" width="26" height="26" rx="5" fill="{EMPTY}"/>')
    for i, h in enumerate(hist):
        col = PALETTE.get(h["colour"]) or EMPTY
        c, r = LETTERS.index(h["cell"][0]), int(h["cell"][1:]) - 1
        k = play * i / n
        o.append(f'<rect x="{pad + c * cell + 3}" y="{56 + r * cell + 3}" width="26" height="26" rx="5" fill="{col}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{k:.4f};{min(k + .002, .999):.4f};.998;1" '
                 f'dur="{dur:.1f}s" repeatCount="indefinite"/></rect>')
    o.append(f'<text x="{W - pad}" y="34" class="mono" font-size="11" fill="{t.TEXT3}" text-anchor="end">loops every {dur:.0f}s</text>')
    o += [t.card_border(W, H, 14), "</svg>"]
    TIMELAPSE.write_text("".join(o), encoding="utf-8")


def paint_link(r, c):
    return (f"https://github.com/{REPO}/issues/new?template=paint.yml&title=" + quote(f"[PAINT] {label(r, c)}"))


def render(st):
    rows = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            v = st["pixels"][r][c]
            img = v if v in PALETTE else "empty"
            row.append(f'<a href="{paint_link(r, c)}"><img src="assets/canvas/{img}.svg" width="32" '
                       f'alt="{label(r, c)}: {v or "empty"}, click to paint"></a>')
        rows.append("".join(row))
    hist = st["history"]
    painters = {}
    for h in hist:
        if h["by"] != "kaushik":
            painters[h["by"]] = painters.get(h["by"], 0) + 1
    top = sorted(painters.items(), key=lambda kv: -kv[1])[:5]
    lead = " · ".join(f"[@{p}](https://github.com/{p}) {n}" for p, n in top) or "_nobody yet. be the first painter._"
    recent = [h for h in hist if h["by"] != "kaushik"][-4:][::-1]
    strokes = " · ".join(f"@{h['by']} → {h['cell']} {h['colour']}" for h in recent) or "the moon and stars are mine. the rest of the sky is yours"
    filled = sum(1 for row in st["pixels"] for v in row if v)
    swatches = " ".join(f'<img src="assets/canvas/{n}.svg" width="16" alt="{n}"> {n}' for n in PALETTE if n != "erase")
    block = f"""
<div align="center">

**An r/place-style canvas the whole internet paints together.** Click any pixel, pick a colour, press *Create*. A bot paints it within a minute.

<p>{"<br>".join(rows)}</p>

<sub>{swatches}</sub>

<sub>{filled}/{COLS * ROWS} pixels lit · {len(painters)} painter{"s" if len(painters) != 1 else ""} · latest: {escape(strokes)}</sub>

<sub>**Top painters:** {lead}</sub>

</div>

<details>
<summary><b>Watch the timelapse</b>: every stroke, replayed in order</summary>

<br>

<img src="assets/canvas-timelapse.svg" alt="Timelapse of every pixel painted on the Night Canvas" width="100%">

</details>
"""
    text = README.read_text(encoding="utf-8")
    a, b = text.index(START) + len(START), text.index(END)
    README.write_text(text[:a] + block + text[b:], encoding="utf-8", newline="\n")
    timelapse(st)


# ---------------------------------------------------------------- issue handler


def gh(*args):
    if os.environ.get("DRY_RUN"):
        print("gh", *args)
        return
    subprocess.run(["gh", *args], check=False)


def parse(title, body):
    m = TITLE_RE.match(title or "")
    if not m:
        return None
    c, r = LETTERS.index(m.group(1).upper()), int(m.group(2)) - 1
    if not 0 <= r < ROWS:
        return None
    cm = COLOUR_RE.search(body or "")
    colour = cm.group(1).lower() if cm else ""
    return (r, c, colour) if colour in PALETTE else (r, c, None)


def from_issue():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    issue = event["issue"]
    num, login = str(issue["number"]), issue["user"]["login"]
    if not LOGIN_RE.match(login):
        sys.exit("unexpected login format")
    p = parse(issue.get("title"), issue.get("body"))
    if not p or p[2] is None:
        gh("issue", "comment", num, "--body", "Couldn't read a pixel and a colour there. Click a pixel on the profile "
           "canvas and pick a colour from the list.")
        gh("issue", "close", num, "--reason", "not planned")
        return
    r, c, colour = p
    st = load()
    paint(st, login, r, c, colour)
    save(st)
    render(st)
    done = "erased back to night" if colour == "erase" else f"painted {colour}"
    gh("issue", "comment", num, "--body",
       f"\U0001F3A8 **{label(r, c)} {done}**, @{login}. It's on the canvas now, and in the timelapse forever.\n\n"
       f"[See the canvas](https://github.com/{OWNER}#canvas) · paint another any time.")
    gh("issue", "close", num, "--reason", "completed")
    print(login, label(r, c), colour)


def seed():
    """A crescent moon and a few stars so the sky isn't empty on day one."""
    st = {"pixels": [[None] * COLS for _ in range(ROWS)], "history": []}
    moon = [(1, 19), (1, 20), (2, 18), (2, 19), (3, 18), (3, 19), (4, 18), (4, 19), (5, 19), (5, 20)]
    for r, c in moon:
        paint(st, "kaushik", r, c, "champagne")
    for r, c, col in ((1, 3, "white"), (3, 8, "lavender"), (2, 13, "white"), (6, 23, "sky"), (5, 5, "periwinkle")):
        paint(st, "kaushik", r, c, col)
    return st


if __name__ == "__main__":
    if "--cells" in sys.argv:
        write_cells()
    if "--seed" in sys.argv:
        save(seed())
    if "--paint" in sys.argv:
        i = sys.argv.index("--paint")
        cell, colour = sys.argv[i + 1], sys.argv[i + 2]
        who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "tester"
        st = load()
        paint(st, who, int(cell[1:]) - 1, LETTERS.index(cell[0].upper()), colour)
        save(st)
        render(st)
    elif "--render" in sys.argv or "--seed" in sys.argv:
        render(load())
    elif "GITHUB_EVENT_PATH" in os.environ:
        from_issue()
