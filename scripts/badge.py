#!/usr/bin/env python3
"""Render a conference-style photo pass and its playable reverse insert."""
import os
from pathlib import Path
import sys
from xml.sax.saxutils import escape

import qrcode

import common
import theme


DEFS = """<defs>
  <radialGradient id="table" cx=".3" cy=".15" r="1">
    <stop stop-color="#45474b"/><stop offset=".57" stop-color="#2b2e33"/><stop offset="1" stop-color="#191b20"/>
  </radialGradient>
  <pattern id="tablecloth" width="4" height="4" patternUnits="userSpaceOnUse">
    <path d="M0 1h4" stroke="#fff" opacity=".03"/><path d="M1 0v4" stroke="#090b11" opacity=".09"/>
  </pattern>
  <linearGradient id="steel" x1="0" y1="0" x2=".86" y2="1">
    <stop stop-color="#555955"/><stop offset=".16" stop-color="#f9f4df"/><stop offset=".34" stop-color="#9b9d95"/>
    <stop offset=".5" stop-color="#545a59"/><stop offset=".68" stop-color="#efeddf"/><stop offset="1" stop-color="#797d78"/>
  </linearGradient>
  <linearGradient id="vinyl" x2="1" y2=".9">
    <stop stop-color="#f5fbff" stop-opacity=".25"/><stop offset=".18" stop-color="#cedfe8" stop-opacity=".07"/>
    <stop offset=".70" stop-color="#dbe8f3" stop-opacity=".12"/><stop offset="1" stop-color="#eef8ff" stop-opacity=".36"/>
  </linearGradient>
  <linearGradient id="paper" x2=".85" y2="1">
    <stop stop-color="#fbf6e8"/><stop offset=".68" stop-color="#f4edde"/><stop offset="1" stop-color="#e9dfcb"/>
  </linearGradient>
  <pattern id="webbing" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(16)">
    <rect width="5" height="5" fill="#353d63"/><path d="M0 1h5" stroke="#7784a2" opacity=".54"/>
    <path d="M1 0v5" stroke="#1b213b" stroke-width="1.6" opacity=".65"/>
  </pattern>
  <filter id="shadow" x="-30%" y="-20%" width="166%" height="165%" color-interpolation-filters="sRGB">
    <feGaussianBlur stdDeviation="6"/>
  </filter>
  <pattern id="foilLines" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(42)">
    <rect width="4" height="4" fill="#9ca5aa"/><path d="M0 0v4" stroke="#eff2dd" stroke-width="2"/>
  </pattern>
  <style>
    text{font-family:'Segoe UI',Arial,sans-serif;fill:#252a37}
    .head{font-weight:750;letter-spacing:-1px}.mono,.light,.tag{font-family:Consolas,'Liberation Mono',monospace}
    .tag{fill:#54565c;letter-spacing:1.2px}.light{fill:#faf4e7;letter-spacing:.6px}
    @media(prefers-reduced-motion:no-preference){
      .settle{transform-origin:150px -94px;animation:arrive 2.6s ease-out both}
      @keyframes arrive{0%{transform:rotate(1.5deg)}40%{transform:rotate(-.65deg)}75%{transform:rotate(.2deg)}100%{transform:rotate(0)}}
    }
  </style>
</defs>"""


def text(x, y, value, size, style=""):
    return f'<text x="{x}" y="{y}" class="{style}" font-size="{size}">{escape(str(value))}</text>'


def qr_print(url, x, y, size):
    qr = qrcode.QRCode(border=4)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    modules = "".join(f"M{c} {r}h1v1h-1z" for r, row in enumerate(matrix)
                      for c, dark in enumerate(row) if dark)
    return f"""<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 {len(matrix)} {len(matrix)}">
      <rect width="100%" height="100%" fill="#fffaf0"/><path d="{modules}" fill="#1d2330"/>
    </svg>"""


def lanyard():
    # Fabric sits behind the swivel; its folded end passes through the metal ring.
    return """<g stroke-linejoin="round">
      <path d="M32 -162L143 -43l14 -12L57 -173z" fill="#1e253d" stroke="#141a2b"/>
      <path d="M28 -167L139 -43l15 -12L50 -175z" fill="url(#webbing)" stroke="#707891"/>
      <path d="M40 -165L147 -48" stroke="#d4ba99" stroke-width="1.2" stroke-dasharray="3 3"/>
      <path d="M258 -174L157 -42l-17 -12L234 -184z" fill="url(#webbing)" stroke="#7b8296"/>
      <path d="M247 -173L149 -48" stroke="#d4ba99" stroke-width="1.2" stroke-dasharray="3 3"/>
      <path d="M134 -60l27 1 -2 21q-11 8 -23 -1z" fill="#343b55" stroke="#202633"/>
      <path d="M137 -56l19 14m1 -14l-19 14" stroke="#b3a99b" stroke-width="1" stroke-dasharray="2 1.5"/>
      <path d="M136 -39q13 8 24 0q-2 17 -12 17t-12 -17z" fill="none" stroke="#1a1d23" stroke-width="5"/>
      <path d="M136 -40q13 8 24 0q-2 17 -12 17t-12 -17z" fill="none" stroke="url(#steel)" stroke-width="3"/>
    </g>"""


def front(login, photo, joined, accent):
    owner = login.lower() == "kaushik2210"
    name = "Kaushik" if owner else login
    name_size = min(50, 405 / len(name))
    focus = (text(187, 141, "FOCUS", 11, "tag") +
             text(187, 165, "Security", 18, "head") +
             text(187, 187, "& AI tools", 18, "head") +
             text(187, 218, "BASED IN", 11, "tag") +
             text(187, 241, "Bangalore", 17, "head")) if owner else (
             text(187, 149, "ON GITHUB", 11, "tag") + text(187, 177, f"Since {joined}", 18))
    return f"""{lanyard()}
    <rect x="8" y="10" width="301" height="385" rx="14" fill="#080a0e" opacity=".72" filter="url(#shadow)"/>
    <rect width="300" height="385" rx="13" fill="url(#vinyl)" stroke="#b7c0c4" stroke-opacity=".8"/>
    <rect x="4" y="4" width="292" height="377" rx="10" fill="none" stroke="#edf4ee" stroke-opacity=".42" stroke-dasharray="2 2"/>
    <rect x="9" y="30" width="282" height="346" rx="4" fill="#161b22" opacity=".7"/>
    <rect x="9" y="29" width="282" height="345" rx="3" fill="url(#paper)"/>
    <path d="M9 32q0 -3 3 -3h276q3 0 3 3v65H9z" fill="#242c45"/>
    <path d="M29 77l17 -29h8L37 77zm12 0l17 -29h8L49 77z" fill="{accent}"/>
    <text x="78" y="72" font-size="28" font-weight="700" style="fill:#fff9eb">Builder pass</text>
    <rect x="24" y="111" width="145" height="148" fill="#c7bdab"/>
    <svg x="25" y="112" width="143" height="146" viewBox="100 183 248 253" preserveAspectRatio="xMidYMid slice">
      <image width="460" height="460" xlink:href="{photo}"/>
    </svg>
    {focus}
    {text(24, 309, name, round(name_size, 1), "head")}
    {text(26, 331, "@" + login, min(16, 405 / (len(login) + 1)), "mono")}
    <rect x="9" y="344" width="282" height="30" fill="{accent}"/>
    {text(24, 364, "DEVELOPER", 13, "mono")}
    <text x="277" y="364" text-anchor="end" class="mono" font-size="12">GITHUB / {joined}</text>
    <path d="M6 365V15q0 -9 9 -9h104M293 41v323q0 14 -14 14h-55" fill="none" stroke="#fff" stroke-opacity=".48"/>
    <rect x="126" y="11" width="48" height="8" rx="4" fill="#272a2e" stroke="#c5cdca"/>
    <g stroke-linecap="round" stroke-linejoin="round">
      <path d="M147 -21v7m-3 1h9" fill="none" stroke="url(#steel)" stroke-width="5"/>
      <path d="M148 -13c-6 4 -7 10 -8 17l-1 7q0 8 8 8 11 -1 11 -11l-1 -10 -5 2 1 11q-1 4 -5 4 -4 0 -3 -5l6 -18z"
            fill="url(#steel)" stroke="#4c5152"/>
      <path d="M152 -8l5 11" fill="none" stroke="#e1e0d4" stroke-width="2"/>
    </g>"""


def reverse(stats, compact, url):
    width, height = (368, 170) if compact else (278, 342)
    if compact:
        title_x, title_y, qr_x, qr_y, qr_size = 19, 69, 226, 17, 128
        stats_x, stats_y, column = 19, 127, 68
    else:
        title_x, title_y, qr_x, qr_y, qr_size = 23, 81, 62, 98, 154
        stats_x, stats_y, column = 19, 300, 83
    artwork = [f'<rect x="6" y="8" width="{width}" height="{height}" rx="7" fill="#080b11" opacity=".68" filter="url(#shadow)"/>',
               f'<rect x="1" y="2" width="{width}" height="{height}" rx="7" fill="#999384"/>',
               f'<rect width="{width}" height="{height}" rx="7" fill="url(#paper)" stroke="#e5dfcf"/>',
               f'<path d="M8 2H{width-8}" stroke="#fffaf0"/>',
               text(title_x, title_y - 33, "VIRTUAL BADGE", 12, "tag"),
               text(title_x-1, title_y, "Play DOOM", 30, "head"),
               qr_print(url, qr_x, qr_y, qr_size)]
    if compact:
        artwork.append(text(title_x, title_y + 22, "Tap the pass or scan.", 14))
    else:
        artwork.extend([f'<rect x="226" y="25" width="25" height="25" rx="4" fill="url(#foilLines)" stroke="#a3a39a"/>',
                        '<text x="139" y="268" font-size="13" text-anchor="middle">Tap the pass or scan.</text>'])
    artwork.append(f'<path d="M{stats_x} {stats_y-17}h{3*column-6}" stroke="#b6ae9e"/>')
    for i, (value, caption) in enumerate(stats):
        artwork.append(text(stats_x + column*i, stats_y + 6, value, 17 if compact else 19, "head"))
        artwork.append(text(stats_x + column*i, stats_y + 23, caption, 10, "mono"))
    return "".join(artwork)


def render(login, user, repos, photo, compact=False):
    width, height = (410, 718) if compact else (830, 526)
    fx, fy = (51, 86) if compact else (92, 92)
    back_position = "translate(20 529) rotate(1 184 85)" if compact else "translate(454 120) rotate(5 139 171)"
    current, longest = common.streaks(common.days(user))
    streak = (f"{current}d", "STREAK") if current >= 5 else (f"{longest}d", "BEST STREAK")
    commits = user["contributionsCollection"]["totalCommitContributions"]
    stats = [(f"{len(repos):,}", "REPOS"), (f"{commits:,}", "COMMITS/YR"), streak]
    joined = user["createdAt"][:4]
    palette = theme.PALETTES[os.environ.get("BADGE_THEME", "ember")]
    accent = palette["A3"]
    url = f"https://badger.github.io/virtual/?u={login}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(login)} · Builder pass</title>
  <desc id="desc">A printed conference-style pass with the original GitHub portrait in a clear holder.
  Scan the reverse or open the badge to play DOOM. {len(repos)} public non-fork repositories and {commits} commit contributions over the past year.</desc>
  {DEFS}
  <clipPath id="scene"><rect width="{width}" height="{height}" rx="14"/></clipPath>
  <g clip-path="url(#scene)">
    <rect width="{width}" height="{height}" fill="url(#table)"/>
    <rect width="{width}" height="{height}" fill="url(#tablecloth)"/>
    <g transform="{back_position}">{reverse(stats, compact, url)}</g>
    <g transform="translate({fx} {fy}) rotate(-5 150 15)"><g class="settle">{front(login, photo, joined, accent)}</g></g>
  </g>
</svg>
"""


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "Kaushik2210"
    target = Path(sys.argv[2] if len(sys.argv) > 2 else "assets/badge.svg")
    photo = common.avatar_data_uri(login)
    user = common.user_graph(login)
    repos = common.repos(login)
    for compact, path in [(False, target), (True, target.with_name(f"{target.stem}-mobile.svg"))]:
        path.write_text(render(login, user, repos, photo, compact), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
