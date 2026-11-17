"""Bangalore's real sky right now, for the header skyline.

Time of day comes from the real sunrise/sunset; weather from Open-Meteo (free, no key).
If the weather call fails the header still renders: clear sky, default sun times.
"""
import json
import random
import urllib.request
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
URL = ("https://api.open-meteo.com/v1/forecast?latitude=12.97&longitude=77.59"
       "&current=temperature_2m,weather_code,cloud_cover&daily=sunrise,sunset"
       "&timezone=Asia/Kolkata&forecast_days=1")

WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
       51: "drizzle", 53: "drizzle", 55: "drizzle", 56: "drizzle", 57: "drizzle",
       61: "light rain", 63: "rain", 65: "heavy rain", 66: "rain", 67: "heavy rain",
       80: "showers", 81: "showers", 82: "heavy showers", 95: "thunderstorm", 96: "thunderstorm", 99: "thunderstorm"}

# sky gradients (top, middle, horizon). Night uses the theme's own sky.
SKIES = {"dawn": ("#05081c", "#211a4d", "#6b3a5c"),          # always a dark sky: warm glow low on the horizon
         "day": ("#040b22", "#0b2257", "#1d4690"),           # deep blue, still a dark card
         "day_overcast": ("#070d1f", "#17223d", "#34425f"),
         "dusk": ("#04061a", "#26163f", "#7a3540")}


def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def state(now=None):
    now = now or datetime.now(IST)
    w = None
    try:
        with urllib.request.urlopen(URL, timeout=15) as r:
            w = json.loads(r.read())
    except Exception:
        pass
    sr, ss = 6 * 60 + 15, 18 * 60
    code, cc, temp = 0, 0, None
    if w:
        try:
            sr = _minutes(w["daily"]["sunrise"][0][11:16])
            ss = _minutes(w["daily"]["sunset"][0][11:16])
            code = int(w["current"]["weather_code"])
            cc = int(w["current"]["cloud_cover"])
            temp = round(float(w["current"]["temperature_2m"]))
        except (KeyError, IndexError, TypeError, ValueError):
            pass
    m = now.hour * 60 + now.minute
    if sr - 40 <= m < sr + 40:
        phase = "dawn"
    elif sr + 40 <= m < ss - 40:
        phase = "day"
    elif ss - 40 <= m < ss + 40:
        phase = "dusk"
    else:
        phase = "night"
    rain = 51 <= code <= 67 or 80 <= code <= 82 or code >= 95
    return {"phase": phase, "time": now.strftime("%H:%M"), "temp": temp, "code": code, "cloud": cc,
            "desc": WMO.get(code, "clear"), "rain": rain, "storm": code >= 95, "fog": code in (45, 48),
            "clouds": cc >= 35 or code in (2, 3) or rain, "live": w is not None}


def gradient(s, night):
    if s["phase"] == "day" and s["cloud"] >= 80:
        return SKIES["day_overcast"]
    return SKIES.get(s["phase"], night)


def clouds(s, W, top=20, bottom=200):
    """Drifting cloud banks; count follows real cloud cover."""
    if not s["clouds"]:
        return ""
    rnd = random.Random(s["cloud"] + 7)
    col, op = {"day": ("#5a6f9e", .55), "dawn": ("#8a5f7d", .45), "dusk": ("#8a4f68", .45)}.get(s["phase"], ("#3a4778", .6))
    if s["phase"] == "day" and s["cloud"] >= 80:
        col, op = "#56627e", .6
    out = []
    for k in range(max(2, min(9, s["cloud"] // 11))):
        y = rnd.uniform(top, bottom)
        sc = rnd.uniform(.7, 1.5)
        dur = rnd.uniform(70, 140)
        puffs = "".join(f'<ellipse cx="{dx}" cy="{dy}" rx="{rx}" ry="{ry}"/>'
                        for dx, dy, rx, ry in ((0, 0, 46, 16), (30, -10, 34, 18), (-28, -6, 30, 14), (58, 2, 30, 12)))
        out.append(f'<g fill="{col}" opacity="{op * rnd.uniform(.7, 1):.2f}">'
                   f'<animateTransform attributeName="transform" type="translate" from="-120 {y:.0f}" to="{W + 120} {y:.0f}" '
                   f'dur="{dur:.0f}s" begin="-{rnd.uniform(0, dur):.0f}s" repeatCount="indefinite"/>'
                   f'<g transform="scale({sc:.2f})">{puffs}</g></g>')
    return "".join(out)


def rain(s, W, H):
    if not s["rain"]:
        return ""
    rnd = random.Random(3)
    n = 120 if "heavy" in s["desc"] or s["storm"] else 70
    out = []
    for _ in range(n):
        x, y0 = rnd.uniform(-40, W), rnd.uniform(-H, 0)
        dur = rnd.uniform(.55, .9)
        out.append(f'<line x1="{x:.0f}" y1="{y0:.0f}" x2="{x - 5:.0f}" y2="{y0 + 16:.0f}" stroke="#bcd3ff" stroke-width="1" '
                   f'stroke-linecap="round" opacity=".45"><animateTransform attributeName="transform" type="translate" '
                   f'from="0 0" to="-30 {H + 40}" dur="{dur:.2f}s" begin="-{rnd.uniform(0, dur):.2f}s" repeatCount="indefinite"/></line>')
    if s["storm"]:
        out.append(f'<rect width="{W}" height="{H}" fill="#e8f0ff" opacity="0"><animate attributeName="opacity" '
                   'values="0;0;.55;0;.35;0;0" keyTimes="0;.6;.62;.64;.66;.69;1" dur="7s" repeatCount="indefinite"/></rect>')
    return "".join(out)


def fog(s, W, street):
    if not s["fog"]:
        return ""
    return (f'<rect x="0" y="{street - 120}" width="{W}" height="150" fill="#c9d4e8" opacity=".22">'
            f'<animate attributeName="opacity" values=".16;.28;.16" dur="12s" repeatCount="indefinite"/></rect>')


def label(s):
    t = f" · {s['temp']}°C" if s["temp"] is not None else ""
    return f"BANGALORE NOW · {s['time']} IST{t} · {s['desc'].upper()}"
