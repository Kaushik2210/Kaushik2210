#!/usr/bin/env python3
"""assets/run.svg: your contribution graph as an auto-playing platformer.

The heatmap becomes the level: each week is a tower of blocks (heatmap colours),
tall = lots of commits, a zero-commit week is a pit. A hero wearing your own
face sprints across the year, hops the steps, leaps the pits, grabs coins
sitting on your biggest weeks and plants a flag at "today". Then it loops.
Pure SMIL, so it animates inside <img> on a GitHub README. Needs Pillow.
"""
import base64
import io
import math
import random
import sys
import urllib.request
from datetime import date, datetime, timezone
from xml.sax.saxutils import escape

from PIL import Image

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/run.svg"
W, H = 830, 350
GY = 292  # ground line
BS, BP = 12, 14  # block size, block pitch
CW = 14  # column width
X0 = 46
DUR = 22.0
T0, T1 = 1.6, 15.6  # run start / end (s)
CELEB = 19.6  # celebration ends
GREEN = "#00ff41"
RAMP = ["#12261b", "#0e6b2f", "#13a846", "#22e062", "#9bffb8"]
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"


def face_uri():
    raw = urllib.request.urlopen(urllib.request.Request(
        f"https://github.com/{USER}.png?size=460", headers={"User-Agent": "profile-gen"}), timeout=30).read()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    box = (int(.37 * w), int(.44 * h), int(.67 * w), int(.74 * h))  # the face
    im = im.crop(box).resize((48, 48), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def burst(cx, cy, t, n, colors, spread=34, life=0.7, up=22):
    """Confetti: n particles flying out from (cx,cy) starting at t seconds."""
    rnd = random.Random(int(t * 100) + n)
    out = []
    a = t / DUR
    b = (t + life) / DUR
    for i in range(n):
        ang = rnd.uniform(-math.pi, 0)
        d = rnd.uniform(spread * .5, spread)
        dx, dy = math.cos(ang) * d, math.sin(ang) * d - up * .3
        col = rnd.choice(colors)
        out.append(
            f'<rect x="-3" y="-3" width="6" height="6" rx="1" fill="{col}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" additive="sum" '
            f'values="{cx:.1f} {cy:.1f};{cx:.1f} {cy:.1f};{cx + dx:.1f} {cy + dy:.1f};{cx + dx:.1f} {cy + dy + 18:.1f};{cx + dx:.1f} {cy + dy + 18:.1f}" '
            f'keyTimes="0;{a:.4f};{(a + b) / 2:.4f};{b:.4f};1" dur="{DUR}s" repeatCount="indefinite" calcMode="linear"/>'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{a:.4f};{(a + b) / 2:.4f};{b:.4f};1" '
            f'dur="{DUR}s" repeatCount="indefinite"/></rect>')
    return "\n".join(out)


def main():
    u = common.user_graph(USER)
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    nw = len(weeks)
    tot = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    mx = max(tot) or 1
    nz = sorted(t for t in tot if t)
    q = [nz[int(len(nz) * p)] for p in (0.25, 0.5, 0.8)] if nz else [1, 2, 3]

    def lvl(t):
        return 0 if t == 0 else 1 + sum(t > x for x in q)

    hts = [0 if t == 0 else 1 + round(7 * math.log1p(t) / math.log1p(mx)) for t in tot]
    xs = [X0 + i * CW + CW / 2 for i in range(nw)]
    top = [GY - h * BP for h in hts]
    tcol = lambda i: T0 + i / (nw - 1) * (T1 - T0)  # time the hero reaches column i

    # feet position at each station; pits borrow the higher neighbour
    feet = []
    for i in range(nw):
        if hts[i]:
            feet.append(top[i])
        else:
            nb = [top[j] for j in (i - 1, i + 1) if 0 <= j < nw and hts[j]]
            feet.append(min(nb) if nb else GY)

    # path samples
    S = 7
    pts, kts = [], []
    for i in range(nw - 1):
        pit = (hts[i] == 0 or hts[i + 1] == 0)
        drow = abs(feet[i + 1] - feet[i]) / BP
        J = 5 + 2.4 * drow + (16 if pit else 0)
        for k in range(S):
            s = k / S
            se = s * s * (3 - 2 * s) if feet[i] != feet[i + 1] else s
            y = feet[i] + (feet[i + 1] - feet[i]) * se - J * math.sin(math.pi * s)
            pts.append((xs[i] + CW * s, y))
            kts.append((tcol(i) + (tcol(i + 1) - tcol(i)) * s) / DUR)
    pts.append((xs[-1], feet[-1]))
    kts.append(T1 / DUR)
    vals = [pts[0]] + pts + [pts[-1]]
    kt = [0.0] + kts + [1.0]
    run_vals = ";".join(f"{x:.1f} {y:.1f}" for x, y in vals)
    run_kt = ";".join(f"{k:.4f}" for k in kt)

    face = face_uri()
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="A platformer where my contribution graph is the level and a character with my face runs across it">',
         f"<title>CONTRIBUTION RUN // {escape(USER)}</title>",
         f"""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a0f24"/><stop offset=".7" stop-color="#141a3a"/><stop offset="1" stop-color="#1d1840"/></linearGradient>
<clipPath id="face"><circle cx="0" cy="-39" r="14"/></clipPath>
<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<filter id="gs" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>text{{font-family:{FONT}}}</style></defs>
<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="url(#sky)"/>"""]

    rnd = random.Random(7)
    for i in range(70):  # stars
        o.append(f'<circle cx="{rnd.randint(0, W)}" cy="{rnd.randint(0, 200)}" r="{rnd.choice([.6, .9, 1.2])}" fill="#cfd8ff" opacity="{rnd.uniform(.2, .8):.2f}">'
                 f'<animate attributeName="opacity" values=".15;.9;.15" dur="{rnd.uniform(2, 6):.1f}s" begin="-{rnd.uniform(0, 5):.1f}s" repeatCount="indefinite"/></circle>')
    o.append('<circle cx="740" cy="86" r="22" fill="#e8ecff" opacity=".9"/><circle cx="750" cy="80" r="20" fill="#141a3a"/>')
    # distant hills (parallax-less silhouette from the real weekly profile)
    hill = " ".join(f"{xs[i]:.0f},{GY - 20 - hts[i] * 9 - (i % 3) * 3}" for i in range(nw))
    o.append(f'<polygon points="{X0},{GY} {hill} {xs[-1]:.0f},{GY}" fill="#1a2250" opacity=".55"/>')

    o.append(f'<text x="{X0}" y="36" font-size="13" fill="{GREEN}">&#9654; RUN.exe</text>')
    o.append(f'<text x="{W - 24}" y="36" font-size="11" fill="#8892c8" text-anchor="end">level = your last {nw} weeks &#183; tall = busy &#183; gap = no commits</text>')

    # month ticks along the ground
    last = None
    for i, w in enumerate(weeks):
        d = date.fromisoformat(w["contributionDays"][0]["date"])
        if d.month != last:
            o.append(f'<text x="{xs[i] - 6:.0f}" y="{GY + 15}" font-size="9" fill="#8892c8">{MONTHS[d.month - 1]}</text>')
            last = d.month

    # terrain: columns grow up just ahead of the hero
    for i in range(nw):
        if not hts[i]:
            o.append(f'<path d="M{xs[i] - 4:.0f},{GY} l4,-9 l4,9 z" fill="#ff3b6b" opacity=".75"/>')  # spikes in pits
            continue
        a = max(0.0, tcol(i) - 2.0) / DUR
        b = (tcol(i) - 1.2) / DUR
        blocks = []
        L = lvl(tot[i])
        for k in range(hts[i]):
            cap = k == hts[i] - 1
            col = RAMP[min(4, L + 1)] if cap else RAMP[max(1, L)]
            blocks.append(f'<rect x="{-BS / 2}" y="{-(k + 1) * BP + 2}" width="{BS}" height="{BS}" rx="2.5" fill="{col}"/>')
        kt2 = f"0;{a:.4f};{max(b, a + .004):.4f};{(CELEB + 1.2) / DUR:.4f};{(CELEB + 1.8) / DUR:.4f};1"
        o.append(f'<g transform="translate({xs[i]:.1f},{GY})"><g transform="scale(1,0)">'
                 f'<animateTransform attributeName="transform" type="scale" values="1 0;1 0;1 1;1 1;1 0;1 0" keyTimes="{kt2}" '
                 f'dur="{DUR}s" repeatCount="indefinite"/>{"".join(blocks)}</g></g>')
    o.append(f'<line x1="{X0 - 6}" y1="{GY + 1}" x2="{xs[-1] + 10:.0f}" y2="{GY + 1}" stroke="{GREEN}" stroke-opacity=".5"/>')

    # coins on the heaviest weeks
    cutoff = sorted(tot)[-max(1, min(9, sum(1 for t in tot if t)))] if any(tot) else 1
    coins = [i for i in range(nw) if tot[i] >= cutoff and hts[i] >= 2]
    for i in coins:
        cy = top[i] - 62
        t = tcol(i)
        a, b = (t - .05) / DUR, (t + .35) / DUR
        ca = max(0.0, tcol(i) - 2.0) / DUR
        o.append(f'<g transform="translate({xs[i]:.1f},{cy:.1f})" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0;1" '
                 f'keyTimes="0;{ca:.4f};{ca + .01:.4f};{a:.4f};{b:.4f};{(CELEB + 1.8) / DUR:.4f};1" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/>'
                 f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="1.3s" begin="-{(i % 7) * .2:.1f}s" repeatCount="indefinite"/>'
                 f'<ellipse rx="6" ry="7" fill="#ffd43b" stroke="#fff3a0" stroke-width="1.2" filter="url(#gs)">'
                 f'<animate attributeName="rx" values="6;1.5;6" dur=".8s" repeatCount="indefinite"/></ellipse></g></g>')
        o.append(burst(xs[i], cy, t, 7, ["#ffd43b", "#fff3a0", "#ffffff", GREEN]))

    # flag at today
    fx = xs[-1] + 4
    ft = top[-1] if hts[-1] else feet[-1]
    o.append(f'<line x1="{fx}" y1="{ft}" x2="{fx}" y2="{ft - 50}" stroke="#e6edf3" stroke-width="2"/>')
    o.append(f'<polygon points="{fx},{ft - 50} {fx + 22},{ft - 43} {fx},{ft - 36}" fill="{GREEN}"><animate attributeName="points" '
             f'values="{fx},{ft - 50} {fx + 22},{ft - 43} {fx},{ft - 36};{fx},{ft - 50} {fx + 18},{ft - 45} {fx},{ft - 36};{fx},{ft - 50} {fx + 22},{ft - 43} {fx},{ft - 36}" '
             f'dur="1.1s" repeatCount="indefinite"/></polygon>')
    o.append(f'<text x="{fx - 10}" y="{ft - 58}" font-size="10" fill="{GREEN}" text-anchor="middle">TODAY</text>')

    # fireworks at the finish
    for k, (dx, dy, dt) in enumerate(((-30, -90, 0), (24, -118, .5), (-4, -70, 1.0))):
        o.append(burst(fx + dx, ft + dy, T1 + .1 + dt, 26, ["#ff2bd6", "#19f9ff", "#ffd43b", GREEN, "#ffffff"], spread=46, life=1.0))

    # hero: legs/arms swing, your face on top, translated along the path
    hero = f"""<g><animateTransform attributeName="transform" type="translate" values="{run_vals}" keyTimes="{run_kt}" dur="{DUR}s" repeatCount="indefinite" calcMode="linear"/>
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{(T0 - .4) / DUR:.4f};{(T0 - .2) / DUR:.4f};{(CELEB + .6) / DUR:.4f};{(CELEB + 1.2) / DUR:.4f};1" dur="{DUR}s" repeatCount="indefinite"/>
<ellipse cx="0" cy="0" rx="9" ry="2.2" fill="#000" opacity=".35"/>
<g stroke="{GREEN}" stroke-width="3.4" stroke-linecap="round">
<line x1="0" y1="-12" x2="0" y2="-1"><animateTransform attributeName="transform" type="rotate" values="38 0 -12;-38 0 -12;38 0 -12" dur=".32s" repeatCount="indefinite"/></line>
<line x1="0" y1="-12" x2="0" y2="-1" stroke-opacity=".6"><animateTransform attributeName="transform" type="rotate" values="-38 0 -12;38 0 -12;-38 0 -12" dur=".32s" repeatCount="indefinite"/></line>
</g>
<rect x="-5" y="-26" width="10" height="15" rx="3" fill="#13a846" stroke="{GREEN}"/>
<g stroke="#9bffb8" stroke-width="3" stroke-linecap="round"><line x1="0" y1="-23" x2="0" y2="-14"><animateTransform attributeName="transform" type="rotate" values="-50 0 -23;50 0 -23;-50 0 -23" dur=".32s" repeatCount="indefinite"/></line></g>
<circle cx="0" cy="-39" r="15.5" fill="{GREEN}"/>
<image href="{face}" x="-14" y="-53" width="28" height="28" clip-path="url(#face)" preserveAspectRatio="xMidYMid slice"/>
</g>"""
    o.append(hero)

    # HUD: coins + date + running commit total
    ncoins = len(coins)
    for n in range(ncoins + 1):
        ta = (tcol(coins[n - 1]) if n else 0.0)
        tb = (tcol(coins[n]) if n < ncoins else DUR + 1)
        if n == 0:
            kt3 = f"0;{tb / DUR:.4f};1" if tb < DUR else "0;1;1"
            vv = "1;0;0"
        else:
            kt3 = f"0;{ta / DUR:.4f};{min(tb, DUR) / DUR:.4f};1" if tb < DUR else f"0;{ta / DUR:.4f};{(CELEB + 1.8) / DUR:.4f};1"
            vv = "0;1;0;0" if tb < DUR else "0;1;0;1" if False else "0;1;0;0"
        o.append(f'<text x="{W - 24}" y="62" font-size="14" fill="#ffd43b" text-anchor="end" opacity="0">&#9679; COINS {n}/{ncoins}'
                 f'<animate attributeName="opacity" values="{vv}" keyTimes="{kt3}" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/></text>')
    cum = 0
    by = H - 16
    o.append(f'<rect x="0" y="{H - 40}" width="{W}" height="40" fill="#0a0f1f" opacity=".85"/>'
             f'<line x1="0" y1="{H - 40}" x2="{W}" y2="{H - 40}" stroke="#262e5c"/>')
    for i, w in enumerate(weeks):
        cum += tot[i]
        d0 = date.fromisoformat(w["contributionDays"][0]["date"])
        ta = tcol(i) - ((T1 - T0) / (nw - 1)) / 2 if i else 0.0
        tb = tcol(i) + ((T1 - T0) / (nw - 1)) / 2 if i < nw - 1 else CELEB + 1.2
        keys = [0.0, ta / DUR, tb / DUR, 1.0]
        if i == 0:
            keys = [0.0, 0.0, tb / DUR, 1.0]
        kts = ";".join(f"{max(0.0, min(1.0, k)):.4f}" for k in keys)
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;0;0" keyTimes="{kts}" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/>'
                 f'<text x="{X0}" y="{by}" font-size="13" fill="#c9d1d9">{d0.day:02d} {MONTHS[d0.month - 1]} {d0.year}</text>'
                 f'<text x="{W - 24}" y="{by}" font-size="16" font-weight="bold" fill="{GREEN}" text-anchor="end">{cum}'
                 f'<tspan font-size="11" fill="#7d8590" font-weight="normal"> commits collected</tspan></text></g>')
    o.append("</g>")
    o.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#262e5c"/>')
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: {nw} columns, {sum(1 for h in hts if not h)} pits, {ncoins} coins, tallest {max(hts)} blocks")


if __name__ == "__main__":
    main()
