"""Animated mission scenes: each featured project acts out what it does, in the art area of its card.

Every scene draws inside (0, 0, W, A) with pure SMIL (works in GitHub's image proxy, no JS).
posters.py picks a scene by repo name and falls back to the generic motif.
"""
import theme as t

W, A = 405, 150
RED = t.BEACON[0]
OK = t.GREEN


def _txt(x, y, s, fill, size=10, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" class="mono" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>'


def _blink(values, dur, times=None):
    kt = f' keyTimes="{times}"' if times else ""
    return f'<animate attributeName="opacity" values="{values}"{kt} dur="{dur}s" repeatCount="indefinite"/>'


# ---------------------------------------------------------------- security


def net_sentinel():
    nodes = [(60, 70), (140, 50), (150, 120), (240, 80), (320, 55), (330, 125)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (3, 5), (1, 2)]
    o = []
    for a, b in edges:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{t.HAIRLINE}" stroke-width="1.5"/>')
    # packets on every edge
    for k, (a, b) in enumerate(edges):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        o.append(f'<circle r="2.6" fill="{t.A2}"><animateMotion path="M{x1},{y1} L{x2},{y2}" dur="{1.6 + k * .3:.1f}s" '
                 f'repeatCount="indefinite"/></circle>')
    # the attack path lights up: 0 -> 1 -> 3 -> 4
    path = "M60,70 L140,50 L240,80 L320,55"
    o.append(f'<path d="{path}" fill="none" stroke="{RED}" stroke-width="2.4" stroke-dasharray="320" stroke-dashoffset="320">'
             f'<animate attributeName="stroke-dashoffset" values="320;320;0;0;320" keyTimes="0;.35;.6;.9;1" dur="6s" repeatCount="indefinite"/></path>')
    for i, (x, y) in enumerate(nodes):
        hit = i in (0, 1, 3, 4)
        o.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{t.SURFACE}" stroke="{t.A1}" stroke-width="1.6">'
                 + (f'<animate attributeName="stroke" values="{t.A1};{t.A1};{RED};{RED};{t.A1}" keyTimes="0;.4;.55;.9;1" dur="6s" repeatCount="indefinite"/>' if hit else "")
                 + "</circle>")
    o.append(f'<g opacity="0">{_blink("0;0;1;1;0", 6, "0;.6;.62;.9;1")}'
             f'<rect x="232" y="94" width="150" height="20" rx="4" fill="{t.SURFACE}" stroke="{RED}"/>'
             + _txt(240, 108, "ATT&amp;CK T1021 · lateral move", RED, 9.5) + "</g>")
    return "".join(o)


def orbital_sentinel():
    o = [f'<circle cx="330" cy="190" r="110" fill="{t.RAISED}" stroke="{t.A1}" stroke-opacity=".5"/>',
         f'<ellipse cx="330" cy="150" rx="150" ry="62" fill="none" stroke="{t.HAIRLINE}" stroke-dasharray="3 5"/>',
         f'<g><animateMotion path="M180,150 A150,62 0 1,1 480,150 A150,62 0 1,1 180,150" dur="9s" repeatCount="indefinite" rotate="auto"/>'
         f'<rect x="-6" y="-4" width="12" height="8" rx="1.5" fill="{t.A3}"/><rect x="-18" y="-2.5" width="10" height="5" fill="{t.A1}"/>'
         f'<rect x="8" y="-2.5" width="10" height="5" fill="{t.A1}"/></g>']
    # telemetry sparkline with a spike
    pts = [(20 + i * 9, 110 - (12 if i == 12 else 0) - (i * 7 % 9)) for i in range(18)]
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    o.append(f'<path d="{d}" fill="none" stroke="{t.A2}" stroke-width="1.6"/>')
    o.append(f'<circle cx="{pts[12][0]}" cy="{pts[12][1]}" r="4" fill="{RED}">{_blink("1;.2;1", 1.2)}</circle>')
    o.append(_txt(20, 64, "TELEMETRY · BUS VOLTAGE", t.TEXT3, 9))
    for i, (lab, col) in enumerate((("SENSOR FAULT?", t.A3), ("CYBERATTACK!", RED), ("SOLAR WEATHER?", t.A2))):
        a, b = i / 3, (i + 1) / 3
        o.append(f'<g opacity="0">{_blink("0;0;1;1;0;0", 6, f"0;{a:.3f};{a + .01:.3f};{b - .01:.3f};{b:.3f};1")}'
                 + _txt(20, 136, f"attributing anomaly → {lab}", col, 10.5, extra=' font-weight="700"') + "</g>")
    return "".join(o)


def scam_khel():
    o = [f'<g><animateTransform attributeName="transform" type="translate" values="0 0;-2 0;2 0;-2 0;0 0;0 0" keyTimes="0;.05;.1;.15;.2;1" dur="3s" repeatCount="indefinite"/>'
         f'<rect x="150" y="44" width="70" height="100" rx="10" fill="{t.SURFACE}" stroke="{t.A1}" stroke-width="1.6"/>'
         f'<circle cx="185" cy="72" r="10" fill="{t.RAISED}"/>'
         + _txt(185, 98, "UNKNOWN", t.TEXT, 8.5, "middle") + _txt(185, 110, '"CBI officer"', t.TEXT3, 8, "middle")
         + f'<circle cx="170" cy="128" r="6" fill="{OK}"/><circle cx="200" cy="128" r="6" fill="{RED}"/></g>']
    for k in range(3):  # ring waves
        o.append(f'<circle cx="185" cy="94" r="40" fill="none" stroke="{t.A2}" stroke-opacity=".5">'
                 f'<animate attributeName="r" values="40;80" dur="2.4s" begin="{k * .8}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="stroke-opacity" values=".5;0" dur="2.4s" begin="{k * .8}s" repeatCount="indefinite"/></circle>')
    o.append(f'<g opacity="0">{_blink("0;0;1;1;0", 5, "0;.45;.5;.92;1")}'
             f'<rect x="232" y="70" width="152" height="46" rx="8" fill="{t.SURFACE}" stroke="{RED}" stroke-width="1.6"/>'
             + _txt(244, 89, "⚠ DIGITAL-ARREST SCAM", RED, 10, extra=' font-weight="700"')
             + _txt(244, 106, "family alerted · honeypot on", t.TEXT2, 9) + "</g>")
    o.append(f'<g opacity="0">{_blink("0;0;1;1;0", 5, "0;.5;.55;.92;1")}'
             f'<path d="M60 60 L90 50 L120 60 L120 92 Q120 118 90 130 Q60 118 60 92 Z" fill="{t.SURFACE}" stroke="{OK}" stroke-width="2"/>'
             + _txt(90, 98, "SAFE", OK, 11, "middle", ' font-weight="700"') + "</g>")
    return "".join(o)


def deepfake_detector():
    o = [f'<g stroke="{t.A2}" stroke-width="2" fill="none">'
         '<path d="M130 50 h-14 v14"/><path d="M230 50 h14 v14"/><path d="M130 140 h-14 v-14"/><path d="M230 140 h14 v-14"/></g>',
         f'<circle cx="180" cy="82" r="22" fill="{t.RAISED}"/><path d="M140 140 Q180 100 220 140 Z" fill="{t.RAISED}"/>']
    for x, y in ((172, 78), (188, 78), (180, 90), (166, 96), (194, 96), (180, 70)):  # landmark dots
        o.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="{t.A3}">{_blink(".3;1;.3", 1.4)}</circle>')
    o.append(f'<rect x="118" y="50" width="124" height="3" fill="{t.A1}" opacity=".85">'
             f'<animate attributeName="y" values="50;137;50" dur="2.6s" repeatCount="indefinite"/></rect>')
    # probability meter
    o.append(f'<rect x="270" y="78" width="110" height="10" rx="5" fill="{t.RAISED}"/>'
             f'<rect x="270" y="78" width="0" height="10" rx="5" fill="{RED}"><animate attributeName="width" values="0;96;96;0" keyTimes="0;.6;.95;1" dur="5s" repeatCount="indefinite"/></rect>')
    o.append(_txt(270, 70, "P(synthetic)", t.TEXT3, 9))
    vals = ["0.12", "0.38", "0.61", "0.79", "0.87", "0.87"]
    for i, v in enumerate(vals):
        a, b = i / len(vals), (i + 1) / len(vals)
        o.append(f'<g opacity="0">{_blink("0;0;1;1;0;0", 5, f"0;{a:.3f};{a + .005:.3f};{b - .005:.3f};{b:.3f};1")}'
                 + _txt(270, 108, f"{v}  calibrated", RED if float(v) > .7 else t.TEXT, 12, extra=' font-weight="700"') + "</g>")
    o.append(_txt(270, 126, "evidence: seams + eye gaze", t.TEXT3, 8.5))
    return "".join(o)


def intentguard():
    o = [f'<rect x="38" y="70" width="40" height="40" rx="8" fill="{t.RAISED}" stroke="{t.A1}"/>'
         f'<circle cx="52" cy="86" r="4" fill="{t.A3}"/><circle cx="66" cy="86" r="4" fill="{t.A3}"/>'
         f'<line x1="58" y1="70" x2="58" y2="60" stroke="{t.A1}"/><circle cx="58" cy="58" r="3" fill="{t.A1}"/>',
         _txt(58, 126, "AI agent", t.TEXT3, 9, "middle"),
         f'<rect x="318" y="66" width="56" height="50" rx="6" fill="{t.RAISED}" stroke="{t.HAIRLINE}"/>'
         f'<line x1="326" y1="80" x2="366" y2="80" stroke="{t.HAIRLINE}"/><line x1="326" y1="92" x2="366" y2="92" stroke="{t.HAIRLINE}"/>',
         _txt(346, 130, "your systems", t.TEXT3, 9, "middle"),
         f'<path d="M190 52 L214 44 L238 52 L238 86 Q238 112 214 124 Q190 112 190 86 Z" fill="{t.SURFACE}" stroke="{t.A2}" stroke-width="2"/>',
         _txt(214, 92, "INTENT", t.A2, 8, "middle", ' font-weight="700"')]
    calls = [("read_file", OK, True), ("rm -rf /", RED, False), ("send_email", OK, True), ("exfil keys", RED, False)]
    cyc = 8.0
    for i, (name, col, allowed) in enumerate(calls):
        s0, s1 = i * 2 / cyc, (i * 2 + 1.4) / cyc       # flight window inside the 8 s loop
        s2 = (i * 2 + 1.9) / cyc
        end = 318 if allowed else 186
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{s0:.3f};{s0 + .01:.3f};{s2:.3f};{s2 + .01:.3f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="80 0;80 0;{end - 70} 0;{end - 70} 0" keyTimes="0;{s0:.3f};{s1:.3f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 f'<rect x="0" y="82" width="68" height="16" rx="8" fill="{t.SURFACE}" stroke="{col}"/>'
                 + _txt(34, 93.5, name, col, 8.5, "middle") + "</g>")
        verdict = "ALLOW" if allowed else "DENY"
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{s1:.3f};{s1 + .01:.3f};{s2:.3f};{s2 + .01:.3f};1" dur="{cyc}s" repeatCount="indefinite"/>'
                 + _txt(214, 142, f"{verdict} · {name}", col, 10, "middle", ' font-weight="700"') + "</g>")
    return "".join(o)


# ---------------------------------------------------------------- dev tools & products


def tapwire():
    o = [f'<path d="M20 100 C 90 60, 150 140, 210 100" fill="none" stroke="{t.A1}" stroke-width="2"/>',
         f'<circle cx="210" cy="100" r="10" fill="{t.SURFACE}" stroke="{t.A3}" stroke-width="2"/>']
    for k in range(3):
        o.append(f'<g><animateMotion path="M20 100 C 90 60, 150 140, 210 100" dur="2.4s" begin="{k * .8}s" repeatCount="indefinite"/>'
                 + _txt(0, 4, "✗", RED, 13, "middle", ' font-weight="700"') + "</g>")
    for i in range(4):
        y = 128 - i * 22
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{.15 + i * .18:.2f};{.2 + i * .18:.2f};.95;1" dur="8s" repeatCount="indefinite"/>'
                 f'<rect x="246" y="{y - 14}" width="140" height="18" rx="4" fill="{t.SURFACE}" stroke="{OK}" stroke-opacity=".7"/>'
                 + _txt(254, y - 1, f"rule #{12 + i} enforced ✓", OK, 9) + "</g>")
    o.append(_txt(20, 64, "agent mistakes →", t.TEXT3, 9) + _txt(380, 140, "repeats: 0", t.A3, 9, "end", ' font-weight="700"'))
    return "".join(o)


def gitvisualise():
    o = []
    for i, (name, ind) in enumerate((("src/", 0), ("auth.ts", 1), ("api/", 1), ("routes.ts", 2), ("db.ts", 1))):
        o.append(_txt(24 + ind * 12, 62 + i * 16, name, t.TEXT2 if "/" in name else t.TEXT3, 10))
    boxes = [(200, 56, "auth"), (290, 56, "api"), (245, 112, "db")]
    for i, (x, y, lab) in enumerate(boxes):
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{.1 + i * .15:.2f};{.18 + i * .15:.2f};.92;1" dur="6s" repeatCount="indefinite"/>'
                 f'<rect x="{x}" y="{y}" width="70" height="28" rx="6" fill="{t.SURFACE}" stroke="{t.A3}"/>'
                 + _txt(x + 35, y + 18, lab, t.A3, 10, "middle", ' font-weight="700"') + "</g>")
    for i, (x1, y1, x2, y2) in enumerate(((270, 70, 290, 70), (325, 84, 290, 112), (235, 84, 260, 112))):
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{t.A2}" stroke-width="1.6" stroke-dasharray="40" stroke-dashoffset="40">'
                 f'<animate attributeName="stroke-dashoffset" values="40;40;0;0;40" keyTimes="0;{.5 + i * .1:.2f};{.6 + i * .1:.2f};.92;1" dur="6s" repeatCount="indefinite"/></line>')
    o.append(f'<path d="M120 96 h50" stroke="{t.A1}" stroke-width="2" marker-end="url(#arr)"/>'
             f'<path d="M164 90 l8 6 -8 6" fill="none" stroke="{t.A1}" stroke-width="2"/>')
    o.append(f'<g opacity="0">{_blink("0;0;1;1;0", 6, "0;.7;.75;.92;1")}' + _txt(200, 158 - 10, "▶ narrating: login → auth → api → db", t.TEXT2, 9) + "</g>")
    return "".join(o)


def hireos():
    o = [f'<g><animateTransform attributeName="transform" type="translate" values="-40 0;0 0;0 0;-40 0" keyTimes="0;.15;.9;1" dur="6s" repeatCount="indefinite"/>'
         f'<rect x="60" y="48" width="96" height="92" rx="6" fill="{t.SURFACE}" stroke="{t.HAIRLINE}"/>'
         + "".join(f'<rect x="72" y="{62 + i * 12}" width="{70 - (i % 3) * 14}" height="5" rx="2.5" fill="{t.RAISED}"/>' for i in range(6))
         + "</g>"]
    circ = 2 * 3.14159 * 30
    o.append(f'<circle cx="250" cy="94" r="30" fill="none" stroke="{t.RAISED}" stroke-width="8"/>'
             f'<circle cx="250" cy="94" r="30" fill="none" stroke="{OK}" stroke-width="8" stroke-linecap="round" transform="rotate(-90 250 94)" '
             f'stroke-dasharray="{circ:.0f}" stroke-dashoffset="{circ:.0f}"><animate attributeName="stroke-dashoffset" values="{circ:.0f};{circ * .08:.0f};{circ * .08:.0f};{circ:.0f}" keyTimes="0;.5;.92;1" dur="6s" repeatCount="indefinite"/></circle>')
    o.append(f'<g opacity="0">{_blink("0;0;1;1;0", 6, "0;.45;.5;.92;1")}' + _txt(250, 99, "92%", t.TEXT, 13, "middle", ' font-weight="700"') + "</g>")
    for i, s in enumerate(("✓ skills match", "✓ evidence cited", "✓ nothing invented")):
        o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{.5 + i * .1:.2f};{.55 + i * .1:.2f};.92;1" dur="6s" repeatCount="indefinite"/>'
                 + _txt(296, 74 + i * 18, s, OK, 9.5) + "</g>")
    return "".join(o)


def algoverse():
    vals = [7, 3, 9, 2, 6, 4, 8, 1, 5]
    frames, arr = [list(vals)], list(vals)
    for i in range(len(arr)):  # bubble sort, one frame per swap
        for j in range(len(arr) - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                frames.append(list(arr))
    frames += [frames[-1]] * 6
    n, dur = len(frames), len(frames) * .28
    o = [_txt(24, 60, "bubble sort · live", t.TEXT3, 9)]
    for v in range(1, 10):  # each value is a bar that slides to its slot
        xs = ";".join(str(40 + f.index(v) * 36) for f in frames)
        h = v * 8.5
        col = t.A3 if v == 9 else t.A1
        o.append(f'<rect x="{40 + frames[0].index(v) * 36}" y="{140 - h}" width="26" height="{h}" rx="4" fill="{col}" opacity=".9">'
                 f'<animate attributeName="x" values="{xs}" dur="{dur:.1f}s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    o.append(_txt(380, 60, "O(n²)", t.A2, 10, "end", ' font-weight="700"'))
    return "".join(o)


SCENES = {"net-sentinel": net_sentinel, "orbital-sentinel": orbital_sentinel, "scam-khel": scam_khel,
          "deepfake-detector": deepfake_detector, "intentguard": intentguard, "tapwire": tapwire,
          "gitvisualise": gitvisualise, "hireos": hireos, "algoverse": algoverse}


def scene(name):
    f = SCENES.get(name.lower())
    return f() if f else None


# mission log lines that scroll under each scene (the radio chatter of the mission)
TICKER = {
    "net-sentinel": "ingest 12,408 flows · graph built · path 10.0.0.4 → DC01 flagged · ATT&CK T1021 · analyst paged",
    "orbital-sentinel": "SAT-7 bus voltage -12% · sensor fault ruled out · solar Kp 3, quiet · verdict: cyber · confidence 0.81",
    "scam-khel": "incoming call, unknown number · script match: digital arrest · urgency + authority cues · family notified",
    "deepfake-detector": "frame 0412 · blend seams found · gaze drift · P(synthetic) 0.87, calibrated · evidence report saved",
    "intentguard": "read_file → ALLOW · rm -rf / → DENY · send_email → ALLOW · exfil keys → DENY · incidents today: 0",
    "tapwire": "mistake captured · turned into rule #15 · enforced on the next run · same mistake twice: never",
    "gitvisualise": "clone repo · parse every file · draw the architecture · narrate the tour · onboarding in minutes",
    "hireos": "parse résumé · match skills to the role · cite evidence for every claim · fit 92% · nothing invented",
    "algoverse": "compare · swap · compare · swap · watch the algorithm think · sorted ✓ · next up: quicksort",
}


def ticker(name):
    return TICKER.get(name.lower())
