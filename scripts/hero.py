#!/usr/bin/env python3
"""assets/header.svg: the Night Shift. Your contribution year as a city skyline at night.

  one building per week     height = that week's commits
  lit windows               = days you were active that week
  cars on the street        = your recent pushes
  neon sign                 = the name, flickering
  wet-street reflection     = the whole city mirrored and faded

The skyline grows toward "now": quiet early weeks are low, recent weeks are towers.
Everything is built from the GitHub API on each run. Pure SMIL, no JavaScript.
"""
import math
import random
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/header.svg"
W, H = 830, 392
STREET = 322            # top of the street == baseline of the buildings
NAME = "Kaushik"
ROLES = ["Full-stack developer.", "Security tinkerer.", "I build things, then I break them."]


def chronotype(hist):
    tot = sum(hist) or 1
    night = sum(hist[h] for h in list(range(18, 24)) + list(range(0, 5)))
    morn = sum(hist[h] for h in range(5, 12))
    label = "night owl" if night / tot > 0.45 else "early bird" if morn / tot > 0.45 else "all-day builder"
    return label, max(range(24), key=lambda h: hist[h])


def ago(td):
    h = td.total_seconds() / 3600
    return "just now" if h < 1 else f"{int(h)}h ago" if h < 24 else f"{int(h // 24)}d ago"


def main():
    u = common.user_graph(USER)
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    nw = len(weeks)
    tot = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    act = [sum(1 for d in w["contributionDays"] if d["contributionCount"]) for w in weeks]
    mx = max(tot) or 1
    cur, longest = common.streaks(common.days(u))
    streak_txt = f"{cur}-day streak" if cur >= 5 else f"best streak {longest} days"
    # the profile repo is excluded: the rebuild itself pushes there every few hours, so it would always read "just now"
    rp = sorted((r for r in common.repos(USER) if r["name"].lower() != USER.lower()), key=lambda r: r["pushed_at"], reverse=True)
    now = datetime.now(timezone.utc)
    last = rp[0]
    last_ago = ago(now - datetime.fromisoformat(last["pushed_at"].replace("Z", "+00:00")))
    hist, npush = common.push_hours(USER)
    chrono, peak = chronotype(hist)

    rnd = random.Random(2210)
    pitch = (W - 20) / nw
    bw = pitch - 2.4
    heights = [14 + 168 * (v / mx) ** 0.55 if v else 11 for v in tot]
    tallest = sorted(range(nw), key=lambda i: heights[i], reverse=True)[:3]

    alt = (f"A night-time city skyline built from my last {nw} weeks of GitHub activity: one building per week, "
           f"taller means more commits, lit windows are active days. {streak_txt}, {chrono}, last push {last['name']} {last_ago}.")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
         f"<title>{escape(USER)}: the night shift</title>",
         t.defs(f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t.SKY_GRAD[0]}"/><stop offset=".6" stop-color="{t.SKY_GRAD[1]}"/><stop offset="1" stop-color="{t.SKY_GRAD[2]}"/></linearGradient>
<radialGradient id="hz"><stop offset="0" stop-color="{t.GLOW[2]}" stop-opacity=".5"/><stop offset="1" stop-color="{t.GLOW[2]}" stop-opacity="0"/></radialGradient>
<radialGradient id="hb"><stop offset="0" stop-color="{t.GLOW[0]}" stop-opacity=".45"/><stop offset="1" stop-color="{t.GLOW[0]}" stop-opacity="0"/></radialGradient>
<linearGradient id="beam" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{t.BEAM}" stop-opacity=".30"/><stop offset="1" stop-color="{t.BEAM}" stop-opacity="0"/></linearGradient>
<linearGradient id="rf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="rm"><rect x="0" y="{STREET + 28}" width="{W}" height="{H - STREET - 28}" fill="url(#rf)"/></mask>
<mask id="moonm"><rect width="{W}" height="{H}" fill="#fff"/><circle cx="742" cy="62" r="18" fill="#000"/></mask>
<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>"""),
         '<g clip-path="url(#card)">',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<ellipse cx="{W * .62:.0f}" cy="{STREET}" rx="380" ry="150" fill="url(#hz)"/>',
         f'<ellipse cx="170" cy="120" rx="300" ry="170" fill="url(#hb)"><animateTransform attributeName="transform" type="translate" values="0 0;40 14;0 0" dur="22s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></ellipse>']

    # stars + moon + shooting stars
    for _ in range(95):
        o.append(f'<circle cx="{rnd.randint(0, W)}" cy="{rnd.randint(0, 210)}" r="{rnd.choice([.5, .8, 1.1])}" fill="{t.STAR_BG}" opacity="{rnd.uniform(.25, .85):.2f}">'
                 f'<animate attributeName="opacity" values=".2;.95;.2" dur="{rnd.uniform(2.5, 7):.1f}s" begin="-{rnd.uniform(0, 6):.1f}s" repeatCount="indefinite"/></circle>')
    o.append(f'<circle cx="730" cy="68" r="22" fill="#f4f8ff" mask="url(#moonm)" opacity=".95"/>')
    for sx, sy, dly in ((140, 54, 4), (520, 36, 12.5)):
        a = dly / 18
        o.append(f'<line x1="0" y1="0" x2="-34" y2="-12" stroke="#fff" stroke-width="1.4" stroke-linecap="round" opacity="0">'
                 f'<animateTransform attributeName="transform" type="translate" values="{sx} {sy};{sx} {sy};{sx + 160} {sy + 56};{sx + 160} {sy + 56}" keyTimes="0;{a:.4f};{a + .04:.4f};1" dur="18s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{a:.4f};{a + .012:.4f};{a + .04:.4f};1" dur="18s" repeatCount="indefinite"/></line>')

    # ---------------- the city (one group, reused for the reflection) ----------------
    c = [f'<g id="city">']
    for i in range(nw):  # far layer: pale silhouettes between the near buildings
        x = 10 + i * pitch + pitch / 2
        fh = heights[i] * rnd.uniform(.55, .85) + 8
        c.append(f'<rect x="{x:.1f}" y="{STREET - fh:.1f}" width="{bw:.1f}" height="{fh:.1f}" fill="{t.RAISED}" opacity=".85"/>')
    for i in range(nw):
        x = 10 + i * pitch
        h = heights[i]
        top = STREET - h
        c.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{t.SURFACE}"/>')
        c.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="1.6" fill="{t.A1}" opacity=".55"/>')
        if i in tallest:  # antenna + aircraft light
            c.append(f'<line x1="{x + bw / 2:.1f}" y1="{top:.1f}" x2="{x + bw / 2:.1f}" y2="{top - 15:.1f}" stroke="{t.HAIRLINE}" stroke-width="1.2"/>')
            c.append(f'<circle cx="{x + bw / 2:.1f}" cy="{top - 16:.1f}" r="1.8" fill="{t.BEACON[0]}"><animate attributeName="opacity" values="1;.1;1" dur="{1.4 + .3 * tallest.index(i):.1f}s" repeatCount="indefinite"/></circle>')
        rows = min(4, int((h - 10) // 8.5))
        slots = [(cx, r) for r in range(rows) for cx in (2.2, 7.0)]
        rnd.shuffle(slots)
        lit = min(act[i], len(slots))
        for k, (cx, r) in enumerate(slots):
            wx, wy = x + cx, STREET - 9 - r * 8.5 - 4.2
            if k < lit:
                tw = ""
                if rnd.random() < .2:
                    tw = (f'<animate attributeName="opacity" values="1;.25;1" dur="{rnd.uniform(2, 6):.1f}s" begin="-{rnd.uniform(0, 5):.1f}s" repeatCount="indefinite"/>')
                c.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="3.2" height="4.2" fill="{t.A3}">{tw}</rect>')
            else:
                c.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="3.2" height="4.2" fill="{t.HAIRLINE}" opacity=".55"/>')
    c.append("</g>")
    o.append("\n".join(c))

    # searchlight
    bx = 10 + tallest[0] * pitch
    o.append(f'<g transform="translate({bx - 90:.0f},{STREET - 60})"><g><animateTransform attributeName="transform" type="rotate" values="-24;24;-24" dur="9s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>'
             f'<polygon points="0,0 -24,-300 24,-300" fill="url(#beam)"/></g></g>')

    # street, lane marks, cars
    o.append(f'<rect x="0" y="{STREET}" width="{W}" height="28" fill="{t.GROUND[0]}"/>')
    o.append(f'<line x1="0" y1="{STREET}" x2="{W}" y2="{STREET}" stroke="{t.A1}" stroke-opacity=".45"/>')
    o.append(f'<line x1="0" y1="{STREET + 14}" x2="{W}" y2="{STREET + 14}" stroke="{t.GROUND[1]}" stroke-dasharray="10 12"/>')
    ncars = max(6, min(26, npush // 7))
    for k in range(ncars):
        right = k % 2 == 0
        y = STREET + (7 if right else 21)
        dur = rnd.uniform(8, 20)
        f, b = (4, -4) if right else (-4, 4)
        o.append(f'<g><animateTransform attributeName="transform" type="translate" '
                 f'from="{-30 if right else 860} {y}" to="{860 if right else -30} {y}" dur="{dur:.1f}s" begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
                 f'<ellipse cx="{f + (3 if right else -3)}" cy="0" rx="6" ry="1.8" fill="{t.A3}" opacity=".32"/>'
                 f'<circle cx="{f}" cy="0" r="1.7" fill="#fff6d8"/><circle cx="{b}" cy="0" r="1.3" fill="{t.BEACON[0]}"/></g>')

    # reflection (wet street)
    o.append(f'<g mask="url(#rm)"><use href="#city" xlink:href="#city" transform="translate(0,{2 * STREET + 28}) scale(1,-1)" opacity=".34"/></g>')
    o.append(f'<rect x="0" y="{STREET + 28}" width="{W}" height="1" fill="{t.A1}" opacity=".25"/>')

    # neon name + copy
    o.append(f'<text x="50" y="82" class="mono" font-size="12" letter-spacing="3" fill="{t.A3}">FULL-STACK  &#183;  SECURITY  &#183;  BANGALORE</text>')
    o.append(f'<g><text x="44" y="178" font-size="104" font-weight="800" letter-spacing="-4" fill="url(#aurora)" filter="url(#glow)" opacity=".75">{NAME}</text>'
             f'<text x="44" y="178" font-size="104" font-weight="800" letter-spacing="-4" fill="url(#aurora)">{NAME}</text>'
             f'<animate attributeName="opacity" values="1;1;.55;1;.72;1;.9;1" keyTimes="0;.5;.52;.54;.56;.58;.6;1" dur="9s" repeatCount="indefinite"/></g>')
    cyc = 4.2 * len(ROLES)
    for i, r in enumerate(ROLES):
        a, b = i / len(ROLES), (i + 1) / len(ROLES)
        kt = f"0;{a:.3f};{a + .03:.3f};{b - .04:.3f};{b - .01:.3f};1" if i else f"0;0;.03;{b - .04:.3f};{b - .01:.3f};1"
        o.append(f'<text x="50" y="216" font-size="{t.T_TITLE + 2}" fill="{t.TEXT}" opacity="0">{escape(r)}'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" dur="{cyc}s" repeatCount="indefinite"/></text>')

    # status line
    o.append(f'<circle cx="30" cy="{H - 17}" r="3.5" fill="{t.GREEN}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>')
    o.append(f'<text x="42" y="{H - 13}" class="mono" font-size="11" fill="{t.TEXT2}">ONLINE &#183; last push {escape(last["name"] if len(last["name"]) <= 30 else last["name"][:29] + "…")} ({last_ago}) &#183; {streak_txt} &#183; {chrono}, peak {peak:02d}:00</text>')
    o.append("</g>")
    o.append(t.card_border(W, H, 18))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: {nw} buildings, tallest {max(tot)} commits/wk, {ncars} cars, {chrono} peak {peak}h, streak {cur}, {sum(len(x) for x in o) // 1024} KB")


if __name__ == "__main__":
    main()
