"""Nightfall: the one design system every generated asset shares.

Deep indigo-black surfaces with a violet -> pink -> orange sunset gradient as the
single brand accent. Cool surfaces against warm highlights make data pop on
GitHub's blue-black page. Semantic tokens (not per-card colours), one type scale,
one 8-pt spacing grid. Cards are self-contained dark surfaces, so they read the
same on GitHub's light and dark page themes.

Colour rules (HIG): one colour, one meaning. Green = live/ok only. Language
colours are reserved for languages. The sunset gradient is brand + intensity.
"""

# --- surfaces (elevation: canvas < surface < raised) ---
CANVAS = "#07050f"
SURFACE = "#0f0b21"
RAISED = "#1a1436"
HAIRLINE = "#2c2455"

# --- text (all >= 4.5:1 on SURFACE) ---
TEXT = "#f3efff"
TEXT2 = "#bdb4de"
TEXT3 = "#948ac0"

# --- brand gradient ---
VIOLET = "#9d7bff"
PINK = "#ff4fa3"
ORANGE = "#ff9a3c"
AMBER = "#ffc247"
PEACH = "#ffd9b8"

# --- semantic ---
GREEN = "#34d399"   # live / ok only
SKY = "#38bdf8"     # cool contrast (daytime, TypeScript)
ROSE = "#fb7185"

# intensity ramp for anything that encodes "how much" (quiet -> busy)
RAMP = ["#1c1740", "#5b34c9", "#c43fa0", "#ff7a3d", "#fff1d6"]

# --- type: system stacks so it renders in the viewer's native font (HIG: SF Pro / SF Mono) ---
SANS = "system-ui,-apple-system,'SF Pro Text','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
# scale: title 20 / headline 14 / body 13 / caption 11 / label 10 (caps, tracked)
T_TITLE, T_HEAD, T_BODY, T_CAP, T_LABEL = 20, 14, 13, 11, 10

GRADIENT_STOPS = ((0, VIOLET), (52, PINK), (100, ORANGE))

# language -> colour (one place, so every chart agrees)
LANG = {"Python": GREEN, "TypeScript": SKY, "JavaScript": AMBER, "Java": ROSE,
        "HTML": ORANGE, "C": VIOLET, "Other": TEXT3}


def lang_color(name):
    return LANG.get(name, LANG["Other"])


def defs(extra=""):
    """Shared <defs>: gradients, glow, fonts. Include once per SVG."""
    stops = "".join(f'<stop offset="{o}%" stop-color="{c}"/>' for o, c in GRADIENT_STOPS)
    return f"""<defs>
<linearGradient id="aurora" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>
<linearGradient id="auroraV" x1="0" y1="1" x2="0" y2="0">{stops}</linearGradient>
<linearGradient id="bdr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".55"/><stop offset=".5" stop-color="{PINK}" stop-opacity=".28"/><stop offset="1" stop-color="{ORANGE}" stop-opacity=".55"/></linearGradient>
<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
text{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
.label{{font-family:{MONO};font-size:{T_LABEL}px;letter-spacing:.14em;text-transform:uppercase;fill:{TEXT3}}}
</style>{extra}</defs>"""


def card_open(w, h, title, meta="", r=16):
    """Standard card chrome: surface, header row with a live (green) dot."""
    return (f'<rect width="{w}" height="{h}" rx="{r}" fill="{SURFACE}"/>'
            f'<circle cx="28" cy="30" r="3.5" fill="{GREEN}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>'
            f'<text x="40" y="34" class="label" style="fill:{TEXT2}">{title}</text>'
            + (f'<text x="{w - 28}" y="34" class="label" text-anchor="end">{meta}</text>' if meta else "")
            + f'<line x1="28" y1="48" x2="{w - 28}" y2="48" stroke="{HAIRLINE}"/>')


def card_border(w, h, r=16):
    """Gradient hairline so cards separate from the page."""
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none" stroke="url(#bdr)" stroke-width="1.2"/>'
