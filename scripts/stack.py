#!/usr/bin/env python3
"""assets/stack.svg: the stack, as evidenced by your repositories.

Instead of an icon dump, count what the repos actually use: topics grouped into
Security / AI & ML / Backend / Frontend (bars = number of repos), a language mix
across all repos, and the security toolkit you listed yourself. Built from the
GitHub API on every run. Pure SMIL, no JavaScript.
"""
import collections
import sys
from xml.sax.saxutils import escape

import common
import theme as t

USER = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/stack.svg"
W = 830
TOOLKIT = ["Kali Linux", "Wireshark", "Burp Suite", "Nmap", "Metasploit"]   # listed by the owner on the original profile

GROUPS = {  # group -> {topic: display name}
    "SECURITY": {"cybersecurity": "Cybersecurity", "mitre-attack": "MITRE ATT&CK", "network-security": "Network security",
                 "threat-detection": "Threat detection", "suricata": "Suricata", "zeek": "Zeek", "honeypot": "Honeypots",
                 "fraud-prevention": "Fraud prevention", "scam-detection": "Scam detection", "deepfake-detection": "Deepfake detection",
                 "anomaly-detection": "Anomaly detection", "media-forensics": "Media forensics", "trust-and-safety": "Trust & safety"},
    "AI & ML": {"pytorch": "PyTorch", "onnx": "ONNX", "llm": "LLMs", "nvidia-nemotron": "Nemotron", "computer-vision": "Computer vision",
                "ai-agents": "AI agents", "personal-ai": "Personal AI", "nebius": "Nebius"},
    "BACKEND": {"fastapi": "FastAPI", "supabase": "Supabase", "tavily": "Tavily", "timeseries": "Time series", "ccsds": "CCSDS"},
    "FRONTEND": {"nextjs": "Next.js", "react": "React", "typescript": "TypeScript", "tailwindcss": "Tailwind CSS",
                 "framer-motion": "Framer Motion", "webgl": "WebGL", "canvas": "Canvas", "javascript": "JavaScript"},
}


def main():
    rp = common.repos(USER)
    topics = collections.Counter(tp for r in rp for tp in (r.get("topics") or []))
    langs = collections.Counter(r["language"] for r in rp if r.get("language"))
    cols = []
    for g, mp in GROUPS.items():
        items = sorted(((mp[k], topics[k]) for k in mp if topics.get(k)), key=lambda x: (-x[1], x[0]))[:6]
        cols.append((g, items))
    gcol = (t.A3, t.A1, t.RINGS[2], t.A2)
    rows = max((len(i) for _, i in cols), default=1)
    cw = (W - 56) / 4
    top = 76
    ly = top + rows * 32 + 28          # language strip y
    ty = ly + 76                       # toolkit y
    H = ty + 74
    totlang = sum(langs.values()) or 1

    alt = ("Stack evidenced by my repositories. " + " ".join(f"{g}: " + ", ".join(f"{n} ({c})" for n, c in it) + "." for g, it in cols)
           + " Languages: " + ", ".join(f"{k} {v}" for k, v in langs.most_common(6)) + ". Security toolkit: " + ", ".join(TOOLKIT) + ".")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(alt)}">',
         f"<title>STACK // {escape(USER)}</title>",
         t.defs(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>'),
         '<g clip-path="url(#card)">',
         t.card_open(W, H, "STACK, AS EVIDENCED BY MY REPOS", f"{len(rp)} repos &#183; bar = repos using it")]
    for ci, (g, items) in enumerate(cols):
        x0 = 28 + ci * cw
        col = gcol[ci]
        o.append(f'<circle cx="{x0 + 4:.0f}" cy="{top - 4}" r="4" fill="{col}"/><text x="{x0 + 14:.0f}" y="{top}" class="label" style="fill:{col}">{escape(g)}</text>')
        mx = max((c for _, c in items), default=1)
        for ri, (name, cnt) in enumerate(items):
            y = top + 22 + ri * 32
            bw = (cw - 30) * (0.28 + 0.72 * cnt / mx)
            d = 0.2 + ci * 0.1 + ri * 0.08
            o.append(f'<text x="{x0:.0f}" y="{y}" font-size="12" fill="{t.TEXT}">{escape(name)}</text>'
                     f'<text x="{x0 + cw - 28:.0f}" y="{y}" class="mono" font-size="11" fill="{t.TEXT2}" text-anchor="end">{cnt}</text>'
                     f'<rect x="{x0:.0f}" y="{y + 6}" width="{cw - 28:.0f}" height="5" rx="2.5" fill="{t.RAISED}"/>'
                     f'<rect x="{x0:.0f}" y="{y + 6}" width="0" height="5" rx="2.5" fill="{col}"><animate attributeName="width" values="0;{bw:.0f}" dur=".8s" begin="{d:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></rect>')
    # language mix
    o.append(f'<line x1="28" y1="{ly - 14}" x2="{W - 28}" y2="{ly - 14}" stroke="{t.HAIRLINE}"/>')
    o.append(f'<text x="28" y="{ly + 4}" class="label">LANGUAGES ACROSS {len(rp)} REPOS</text>')
    x = 28.0
    bar_w = W - 56
    for k, v in langs.most_common(6):
        w = bar_w * v / totlang
        o.append(f'<rect x="{x:.1f}" y="{ly + 14}" width="{max(w - 2, 2):.1f}" height="9" rx="4.5" fill="{t.lang_color(k if k in t.LANG else "Other")}"/>')
        x += w
    lx = 28.0
    for k, v in langs.most_common(6):
        o.append(f'<circle cx="{lx + 4:.0f}" cy="{ly + 43}" r="4" fill="{t.lang_color(k if k in t.LANG else "Other")}"/>'
                 f'<text x="{lx + 13:.0f}" y="{ly + 47}" font-size="11" fill="{t.TEXT2}">{escape(k)} <tspan fill="{t.TEXT3}">{v}</tspan></text>')
        lx += 22 + 6.4 * len(k) + 26
    # toolkit
    o.append(f'<line x1="28" y1="{ty - 14}" x2="{W - 28}" y2="{ty - 14}" stroke="{t.HAIRLINE}"/>')
    o.append(f'<text x="28" y="{ty + 4}" class="label">SECURITY TOOLKIT</text>')
    px = 28.0
    for name in TOOLKIT:
        w = 22 + 7.0 * len(name)
        o.append(f'<rect x="{px:.0f}" y="{ty + 16}" width="{w:.0f}" height="26" rx="13" fill="{t.RAISED}" stroke="{t.A3}" stroke-opacity=".45"/>'
                 f'<text x="{px + w / 2:.0f}" y="{ty + 33}" font-size="12" fill="{t.TEXT}" text-anchor="middle">{escape(name)}</text>')
        px += w + 10
    o.append("</g>")
    o.append(t.card_border(W, H))
    o.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"wrote {OUT}: " + " | ".join(f"{g}:{len(i)}" for g, i in cols) + f" | langs {dict(langs.most_common(4))} | H={H}")


if __name__ == "__main__":
    main()
