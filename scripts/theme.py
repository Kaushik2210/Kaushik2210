"""Aurora: the one design system every generated asset shares.

Semantic tokens (not per-card colours), one type scale, one 8-pt spacing grid.
Cards are self-contained dark surfaces, so they read the same on GitHub's light
and dark page themes.
"""

# --- surfaces (elevation: canvas < surface < raised) ---
CANVAS = "#070b14"
SURFACE = "#0c1322"
RAISED = "#131c33"
HAIRLINE = "#1d2845"

# --- text (all >= 4.5:1 on SURFACE) ---
TEXT = "#e8edf7"
TEXT2 = "#a3b0cc"
TEXT3 = "#8493b8"

# --- accents ---
MINT = "#3dffb5"
CYAN = "#38d9ff"
VIOLET = "#8b7bff"
PINK = "#ff5fd0"
AMBER = "#ffc94d"
ROSE = "#ff6b8b"

# intensity ramp for anything that encodes "how much" (quiet -> busy)
RAMP = ["#16233b", "#1a6f8f", "#2bb6d1", MINT, "#eafff6"]

# --- type: system stacks so it renders in the viewer's native font (HIG: SF Pro / SF Mono) ---
SANS = "system-ui,-apple-system,'SF Pro Text','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
# scale: title 20 / headline 14 / body 13 / caption 11 / label 10 (caps, tracked)
T_TITLE, T_HEAD, T_BODY, T_CAP, T_LABEL = 20, 14, 13, 11, 10

GRADIENT_STOPS = ((0, MINT), (50, CYAN), (100, VIOLET))


def defs(extra=""):
    """Shared <defs>: gradients, glow, fonts. Include once per SVG."""
    stops = "".join(f'<stop offset="{o}%" stop-color="{c}"/>' for o, c in GRADIENT_STOPS)
    return f"""<defs>
<linearGradient id="aurora" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>
<linearGradient id="auroraV" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>
<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
text{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
.label{{font-family:{MONO};font-size:{T_LABEL}px;letter-spacing:.14em;text-transform:uppercase;fill:{TEXT3}}}
</style>{extra}</defs>"""


def card_open(w, h, title, meta="", r=16):
    """Standard card chrome: surface, hairline border, header row with live dot."""
    return (f'<rect width="{w}" height="{h}" rx="{r}" fill="{SURFACE}"/>'
            f'<circle cx="28" cy="30" r="3.5" fill="{MINT}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>'
            f'<text x="40" y="34" class="label" style="fill:{TEXT2}">{title}</text>'
            + (f'<text x="{w - 28}" y="34" class="label" text-anchor="end">{meta}</text>' if meta else "")
            + f'<line x1="28" y1="48" x2="{w - 28}" y2="48" stroke="{HAIRLINE}"/>')


def card_border(w, h, r=16):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none" stroke="{HAIRLINE}"/>'
