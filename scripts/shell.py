#!/usr/bin/env python3
"""kaushik.sh: a terminal anyone can type into, through GitHub issues.

A visitor opens an issue titled "[SH] <command>". .github/workflows/shell.yml runs this
script: it answers the command, replies in the issue, appends the exchange to the shared
session in shell/history.json and redraws assets/shell.svg and the README block.

Nothing is ever executed. Every command is a lookup in this file or data/projects.json.
Untrusted input: the issue title (whitelisted characters, 60 max) and the login (format-checked).

Local use:  python scripts/shell.py --render
            python scripts/shell.py --try "cat IntentGuard"
"""
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme as t  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "shell" / "history.json"
PROJECTS = ROOT / "data" / "projects.json"
README = ROOT / "README.md"
OUT = ROOT / "assets" / "shell.svg"
REPO = os.environ.get("GH_REPO", "Kaushik2210/Kaushik2210")
OWNER = REPO.split("/")[0]
START, END = "<!--SHELL_START-->", "<!--SHELL_END-->"
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
TITLE_RE = re.compile(r"^\[SH\]\s*(.*)$", re.I)
IST = timezone(timedelta(hours=5, minutes=30))
KEEP = 60
BLOCK = ["fuck", "shit", "bitch", "cunt", "nigg", "fagg", "retard", "rape", "nazi", "hitler", "slut", "whore",
         "dick", "cock", "pussy", "porn", "sex", "kys", "killyourself", "suicide", "asshole", "bastard", "twat"]
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})

LINKS = {"portfolio": "https://portfolio-general-ten.vercel.app",
         "linkedin": "https://www.linkedin.com/in/sodagum-venkata-kaushik-3497a4248/",
         "x": "https://x.com/svKaushik2210"}
FORTUNES = [
    "it works on my machine. so we ship the machine.",
    "every security tool starts as a script that annoyed someone.",
    "the best detection rule is the one that explains itself.",
    "a demo you can click beats a slide you can't.",
    "commit early, commit often, commit before chai gets cold.",
    "there are two hard things: cache invalidation, naming things, and off-by-one errors.",
    "AI agents need guardrails. so do the people building them.",
]
CHIPS = ["help", "whoami", "ping kaushik", "git log", "weather", "cat IntentGuard", "fortune", "sudo hire kaushik"]


# ---------------------------------------------------------------- live lookups (read-only GitHub + weather)


def _latest_repo():
    import common
    rs = [r for r in common.repos(OWNER) if r["name"].lower() != OWNER.lower() and not r.get("private")]
    return max(rs, key=lambda r: r["pushed_at"])


def _ago(iso):
    mins = (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() / 60
    return mins, ("just now" if mins < 2 else f"{int(mins)} min ago" if mins < 90 else
                  f"{int(mins // 60)}h ago" if mins < 48 * 60 else f"{int(mins // 1440)} days ago")


def live(head):
    try:
        if head == "weather":
            import sky
            st = sky.state()
            return [sky.label(st).lower(), f"sky over my skyline: {st['phase']}, clouds {st['cloud']}%"]
        if head == "ping":
            r = _latest_repo()
            mins, ago = _ago(r["pushed_at"])
            mood = ("he's coding right now" if mins < 90 else "probably in class or asleep" if mins < 16 * 60
                    else "quiet for a bit. send a nudge: `hire`")
            return [f"PING kaushik: 64 bytes from github.com/{OWNER}: last push {ago} ({r['name']})", f"→ {mood}"]
        if head == "git":
            import common
            r = _latest_repo()
            cs = json.loads(common._req(f"https://api.github.com/repos/{OWNER}/{r['name']}/commits?per_page=3"))
            return [f"on {r['name']}:"] + [f"{c['sha'][:7]}  {c['commit']['message'].splitlines()[0][:80]}" for c in cs]
    except Exception:
        return ["network is quiet right now. try again in a bit."]
    return []


# ---------------------------------------------------------------- commands


def projects():
    cfg = json.loads(PROJECTS.read_text(encoding="utf-8"))
    private = {"ember-line"}  # featured on the profile but private on GitHub, so links would 404
    return {f["repo"].lower(): f for f in cfg.get("featured", []) if f["repo"].lower() not in private}


def clean(text):
    text = re.sub(r"[^A-Za-z0-9 ._/\-!?']", "", text or "")
    return re.sub(r"\s+", " ", text).strip()[:60]


def blocked(text):
    flat = re.sub(r"[^a-z]", "", text.lower().translate(LEET))
    return any(w in flat for w in BLOCK)


def answer(cmd):
    """Return the output lines for a command. Pure lookups, nothing runs."""
    words = cmd.split()
    if not words:
        return ["type a command. try `help`."]
    head, rest = words[0].lower(), " ".join(words[1:])
    pr = projects()
    if head in ("help", "man", "?"):
        return ["commands: whoami · ls · cat <project> · open <project> · stack · contact",
                "live:     ping kaushik · git log · weather · date · uptime",
                "fun:      fortune · echo <text> · sudo hire kaushik"]
    if head == "whoami":
        return ["kaushik · full-stack + security engineer · bangalore, IN",
                "builds detection systems and AI-agent tooling, ships them as live demos"]
    if head in ("ls", "dir", "tree"):
        names = [f["repo"] for f in pr.values()]
        return ["  ".join(names[:5]), "  ".join(names[5:])] if len(names) > 5 else ["  ".join(names)]
    if head in ("cat", "open", "less", "more"):
        if not rest:
            return [f"usage: {head} <project>. try `ls` for names."]
        f = pr.get(rest.lower().strip("/ "))
        if not f:
            return [f"{head}: {rest}: no such project. try `ls`."]
        url = f"https://github.com/{OWNER}/{f['repo']}"
        if head == "open":
            return [f"opening {url}"]
        return [f"{f['repo']} [{f['category']}]", f["blurb"][:96], url]
    if head in ("weather", "ping") or (head == "git" and rest.lower().startswith("log")):
        return live(head)
    if head == "git":
        return ["git: try `git log`. this shell is read-only, so no pushing."]
    if head == "stack":
        return ["Python · TypeScript · JavaScript · Java", "React · Next.js · FastAPI · Supabase · Docker · Zeek · Suricata"]
    if head in ("contact", "mail"):
        return [f"portfolio  {LINKS['portfolio']}", f"linkedin   {LINKS['linkedin']}", f"x          {LINKS['x']}"]
    if head == "uptime":
        days = (datetime.now(timezone.utc).date() - datetime(2021, 5, 9).date()).days
        return [f"up {days // 365} years, {days % 365 // 30} months on GitHub · load average: always shipping"]
    if head == "date":
        return [datetime.now(IST).strftime("%a %d %b %Y %H:%M IST · bangalore")]
    if head == "fortune":
        return [random.choice(FORTUNES)]
    if head == "echo":
        return [rest or ""]
    if head == "hire" or cmd.lower().startswith("sudo hire"):
        return ["[sudo] permission granted. good call.", f"→ {LINKS['linkedin']}"]
    if head == "sudo":
        return ["you are not in the sudoers file. this incident will be reported (to nobody)."]
    if head == "rm":
        return ["nice try. this shell is read-only. so is my patience 🙂"]
    if head in ("clear", "cls"):
        return ["clear: this terminal belongs to everyone. try `help` instead."]
    if head in ("exit", "logout", "quit"):
        return ["there is no exit. only `hire`."]
    if head in ("vim", "nano", "emacs"):
        return [f"{head}: opening... just kidding. you'd never get out."]
    return [f"{head}: command not found. try `help`."]


# ---------------------------------------------------------------- state + drawing


def load():
    return json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []


def save(hist):
    HISTORY.parent.mkdir(exist_ok=True)
    HISTORY.write_text(json.dumps(hist[-KEEP:], indent=1, ensure_ascii=False), encoding="utf-8")


def draw(hist):
    W, pad, lh = 830, 26, 19
    shown, lines = [], 0
    for e in reversed(hist):  # newest entries that fit in ~20 lines
        need = 1 + len(e["out"])
        if lines + need > 20 and shown:
            break
        shown.insert(0, e)
        lines += need
    H = 70 + (lines + 1) * lh + 22
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="kaushik.sh: the last commands visitors typed into my profile terminal">',
         "<title>kaushik.sh</title>",
         t.defs('<style>@keyframes cur{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:cur 1.05s steps(1) infinite}'
                '@keyframes fade{from{opacity:0}to{opacity:1}}.ln{animation:fade .4s ease-out both}'
                '@media (prefers-reduced-motion: reduce){*{animation:none!important}}</style>'),
         f'<rect width="{W}" height="{H}" rx="14" fill="{t.CANVAS}"/>',
         f'<path d="M0 14a14 14 0 0 1 14-14h{W - 28}a14 14 0 0 1 14 14v22H0z" fill="{t.RAISED}"/>']
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        o.append(f'<circle cx="{24 + i * 20}" cy="18" r="6" fill="{col}" opacity=".9"/>')
    o.append(f'<text x="{W / 2}" y="22" class="mono" font-size="12" fill="{t.TEXT3}" text-anchor="middle">'
             f'kaushik.sh — shared session · {len(hist)} command{"s" if len(hist) != 1 else ""} typed</text>')
    y, k = 66, 0
    for e in shown:
        who = e["login"]
        d = f' style="animation-delay:{k * 0.08:.2f}s"'
        o.append(f'<text class="mono ln" x="{pad}" y="{y}" font-size="13.5"{d}><tspan fill="{t.A2}">{escape(who)}</tspan>'
                 f'<tspan fill="{t.TEXT3}"> ~ </tspan><tspan fill="{t.A1}">$ </tspan>'
                 f'<tspan fill="{t.TEXT}">{escape(e["cmd"])}</tspan></text>')
        y += lh
        k += 1
        for line in e["out"]:
            o.append(f'<text class="mono ln" x="{pad}" y="{y}" font-size="13" fill="{t.TEXT2}"{d}>{escape(line[:98])}</text>')
            y += lh
    o.append(f'<text class="mono" x="{pad}" y="{y}" font-size="13.5"><tspan fill="{t.A3}">you</tspan>'
             f'<tspan fill="{t.TEXT3}"> ~ </tspan><tspan fill="{t.A1}">$ </tspan></text>'
             f'<rect class="cur" x="{pad + 66}" y="{y - 13}" width="8" height="16" fill="{t.A3}"/>')
    o.append(f'<text class="mono" x="{pad + 84}" y="{y}" font-size="12" fill="{t.TEXT3}">← click a command below, or type your own</text>')
    o += [t.card_border(W, H, 14), "</svg>"]
    OUT.write_text("".join(o), encoding="utf-8")


def link(cmd):
    body = quote("Just press **Create**. The bot answers in this issue and adds your command to the terminal on the profile "
                 "within a minute. You can also edit the title to type any command after `[SH]`.")
    return f"https://github.com/{REPO}/issues/new?title={quote('[SH] ' + cmd)}&body={body}"


def render(hist):
    draw(hist)
    visitors = sorted({e["login"] for e in hist if e["login"] != "kaushik"})
    chips = " ".join(f'<a href="{link(c)}"><kbd>{escape(c)}</kbd></a>' for c in CHIPS)
    note = (f"{len(visitors)} visitor{' has' if len(visitors) == 1 else 's have'} typed here" if visitors
            else "the first lines are mine. yours come next")
    block = f"""
<div align="center">

**A real shell on my profile that anyone can type into.** Pick a command, press *Create* on the issue that opens, and a bot answers you here within a minute.

<a href="{link('help')}"><img src="assets/shell.svg" alt="kaushik.sh terminal showing the latest commands visitors typed and their output" width="100%"/></a>

{chips}

<sub>Or open an issue titled <code>[SH] anything</code>. Nothing ever executes: it is a sandbox of answers about me. {note}.</sub>

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
    m = TITLE_RE.match(issue.get("title") or "")
    cmd = clean(m.group(1) if m else "")
    if blocked(cmd):
        gh("issue", "comment", num, "--body", "That command didn't pass the filter. Try something friendlier.")
        gh("issue", "close", num, "--reason", "not planned")
        return
    out = answer(cmd)
    hist = load()
    hist.append({"login": login, "cmd": cmd or "(empty)", "out": out,
                 "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")})
    save(hist)
    render(load())
    reply = "\n".join(out)
    gh("issue", "comment", num, "--body",
       f"```console\n{login} ~ $ {cmd}\n{reply}\n```\n\nYour command is now on the terminal: "
       f"[back to kaushik.sh](https://github.com/{OWNER}#shell). Type another any time.")
    gh("issue", "close", num, "--reason", "completed")
    print(login, "$", cmd)


if __name__ == "__main__":
    if "--try" in sys.argv:
        c = clean(sys.argv[sys.argv.index("--try") + 1])
        print(f"$ {c}\n" + "\n".join(answer(c)))
    elif "--render" in sys.argv:
        render(load())
    elif "GITHUB_EVENT_PATH" in os.environ:
        from_issue()
