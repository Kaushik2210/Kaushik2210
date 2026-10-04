#!/usr/bin/env python3
"""assets/replay.svg: your contribution heatmap as an animated time-lapse.

The real 53x7 calendar replays your year: a glowing playhead sweeps across the
weeks, every day pops in as it passes, your busiest days fire shockwave rings,
and a counter ticks up the running total. Then it fades and loops. Pure SMIL.
"""
import sys
from datetime import date, datetime, timezone
from xml.sax.saxutils import escape

import common

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/replay.svg"
W, H = 830, 268
CELL, PITCH = 11, 14
X0, Y0 = 46, 86
DUR = 18.0
PLAY_START, PLAY_END = 0.6, 11.4  # seconds the playhead sweeps
HOLD_END, FADE_END = 15.8, 17.4
GREEN = "#00ff41"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
RAMP = ["#12261b", "#0e6b2f", "#13a846", "#22e062", "#9bffb8"]
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def level(c, q):
    if c == 0:
        return 0
    return 1 + sum(c > t for t in q)


def main():
    u = common.user_graph(USER)
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    nw = len(weeks)
    counts = sorted(d["contributionCount"] for w in weeks for d in w["contributionDays"] if d["contributionCount"])
    q = [counts[int(len(counts) * p)] for p in (0.25, 0.5, 0.8)] if counts else [1, 2, 3]
    big = sorted(counts)[-max(1, min(6, len(counts))):][0] if counts else 99
    total = sum(counts)
    per_week = (PLAY_END - PLAY_START) / nw

    def pos(t):  # seconds -> keyTime fraction
        return t / DUR

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Animated replay of my contribution heatmap">',
         f"<title>CONTRIBUTION REPLAY // {escape(USER)}</title>",
         f"""<defs><filter id="g" x="-300%" y="-30%" width="700%" height="160%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="gs" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>text{{font-family:{FONT}}}</style></defs>
<rect width="{W}" height="{H}" rx="14" fill="#0b1015" stroke="#0f5d2c"/>
<text x="{X0}" y="38" font-size="13" fill="{GREEN}">&#9654; REPLAY.exe</text>
<text x="{W - 24}" y="38" font-size="12" fill="#7d8590" text-anchor="end">last {nw} weeks &#183; {total} contributions</text>"""]

    # weekday labels
    for i, lab in ((1, "MON"), (3, "WED"), (5, "FRI")):
        o.append(f'<text x="{X0 - 8}" y="{Y0 + i * PITCH + 10}" font-size="9" fill="#586069" text-anchor="end">{lab}</text>')
    # month labels
    last_m = None
    for wi, w in enumerate(weeks):
        d = date.fromisoformat(w["contributionDays"][0]["date"])
        if d.month != last_m and d.day <= 14 or wi == 0:
            if d.month != last_m:
                o.append(f'<text x="{X0 + wi * PITCH}" y="{Y0 - 10}" font-size="10" fill="#7d8590">{MONTHS[d.month - 1]}</text>')
            last_m = d.month

    rings = []
    for wi, w in enumerate(weeks):
        t = PLAY_START + wi * per_week
        for di, d in enumerate(w["contributionDays"]):
            c = d["contributionCount"]
            lv = level(c, q)
            cx = X0 + wi * PITCH + CELL / 2
            cy = Y0 + di * PITCH + CELL / 2
            a = pos(t + di * 0.012)
            vals = "0 0;0 0;1.45 1.45;1 1;1 1;0 0;0 0"
            kt = f"0;{a:.4f};{a + .006:.4f};{a + .016:.4f};{pos(HOLD_END):.4f};{pos(FADE_END):.4f};1"
            flt = ' filter="url(#gs)"' if lv >= 4 else ""
            o.append(f'<g transform="translate({cx:.1f},{cy:.1f})"><g transform="scale(0)"><animateTransform attributeName="transform" '
                     f'type="scale" values="{vals}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
                     f'<rect x="{-CELL / 2}" y="{-CELL / 2}" width="{CELL}" height="{CELL}" rx="2.5" fill="{RAMP[lv]}"{flt}/></g></g>')
            if c >= big and c > 0:
                rings.append((cx, cy, a))
    for cx, cy, a in rings:  # shockwaves from the biggest days
        k = f"0;{a:.4f};{a + .07:.4f};1"
        o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="0" fill="none" stroke="#ffeb78" stroke-width="2" opacity="0">'
                 f'<animate attributeName="r" values="0;0;30;30" keyTimes="{k}" dur="{DUR}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.95;0;0" keyTimes="{k}" dur="{DUR}s" repeatCount="indefinite"/></circle>')

    # playhead
    gx0, gx1 = X0 - 3, X0 + nw * PITCH
    k = f"0;{pos(PLAY_START):.4f};{pos(PLAY_END):.4f};1"
    o.append(f'<rect x="0" y="{Y0 - 6}" width="3" height="{7 * PITCH + 8}" fill="{GREEN}" filter="url(#g)" opacity="0">'
             f'<animate attributeName="x" values="{gx0};{gx0};{gx1};{gx1}" keyTimes="{k}" dur="{DUR}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;{pos(PLAY_START):.4f};{pos(PLAY_END):.4f};{pos(PLAY_END) + .01:.4f}" '
             f'dur="{DUR}s" repeatCount="indefinite"/></rect>')

    # running counter + date, one text per week shown in its time slice
    cum = 0
    base_y = Y0 + 7 * PITCH + 38
    for wi, w in enumerate(weeks):
        cum += sum(d["contributionCount"] for d in w["contributionDays"])
        d0 = date.fromisoformat(w["contributionDays"][0]["date"])
        t0 = PLAY_START + wi * per_week
        t1 = PLAY_START + (wi + 1) * per_week if wi < nw - 1 else HOLD_END
        kt = f"0;{pos(t0):.4f};{pos(t1):.4f};1"
        vis = '<animate attributeName="opacity" values="0;1;0;0" keyTimes="' + kt + f'" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/>'
        if wi == nw - 1:
            kt = f"0;{pos(t0):.4f};{pos(HOLD_END):.4f};{pos(HOLD_END) + .001:.4f};1"
            vis = '<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="' + kt + f'" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/>'
        o.append(f'<g opacity="0">{vis}'
                 f'<text x="{X0}" y="{base_y}" font-size="14" fill="#c9d1d9">{d0.day:02d} {MONTHS[d0.month - 1]} {d0.year}</text>'
                 f'<text x="{W - 24}" y="{base_y}" font-size="22" font-weight="bold" fill="{GREEN}" text-anchor="end">{cum}'
                 f'<tspan font-size="12" fill="#7d8590" font-weight="normal"> contributions</tspan></text></g>')

    # progress bar
    by = base_y + 16
    o.append(f'<rect x="{X0}" y="{by}" width="{W - 24 - X0}" height="3" rx="1.5" fill="#12261b"/>')
    o.append(f'<rect x="{X0}" y="{by}" width="0" height="3" rx="1.5" fill="{GREEN}" filter="url(#gs)">'
             f'<animate attributeName="width" values="0;0;{W - 24 - X0};{W - 24 - X0};0" '
             f'keyTimes="0;{pos(PLAY_START):.4f};{pos(PLAY_END):.4f};{pos(FADE_END):.4f};1" dur="{DUR}s" repeatCount="indefinite"/></rect>')
    o.append(f'<text x="{W - 24}" y="{H - 8}" font-size="9" fill="#586069" text-anchor="end">'
             f'gold rings = busiest days &#183; {datetime.now(timezone.utc):%Y-%m-%d} UTC</text>')
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: {nw} weeks, {total} contributions, {len(rings)} shockwave days, levels<= {q}")


if __name__ == "__main__":
    main()
