#!/usr/bin/env python3
"""
Render GitHub contributions as an isometric skyscraper city card (city.svg).

- Data: contributionCalendar via GraphQL (last 26 weeks), STATS_TOKEN or
  GITHUB_TOKEN. Any failure -> exit nonzero WITHOUT overwriting city.svg,
  so the workflow keeps the previous card.
- Empty days: flat light-gray lots. Contribution days: 3D buildings whose
  height scales with the count, GitHub-green faces, window grids on both
  visible sides (some lit, deterministic per date), antenna on tallest.
- Right panel: current streak (days) and average commits/day.
- No new third-party dependencies: requests + stdlib only.
"""
import os
import random
import requests
import sys
from datetime import datetime, timedelta, timezone

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "brenandapamudya1")
TOKEN = os.environ.get("STATS_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")

WEEKS = 26
TW, TH = 34, 17          # tile full width / height (2:1 dimetric)
HW, HH = TW // 2, TH / 2
MAX_H = 85               # tallest building, px
LOT_FILL = "#c9d1d9"     # empty-day lots
BG, BORDER = "#0d1117", "#30363d"
BLUE, GRAY, WHITE = "#58a6ff", "#8b949e", "#e6edf3"
MONO = ("font-family=\"'JetBrains Mono', 'Cascadia Code', 'Fira Code', "
        "'SF Mono', Consolas, monospace\"")


def _hex(rgb_hex):
    return tuple(int(rgb_hex[i:i + 2], 16) for i in (1, 3, 5))


def _rgb(t):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in t)


def shade(rgb_hex, f):
    """f > 0 lightens toward white, f < 0 darkens toward black."""
    r, g, b = _hex(rgb_hex)
    if f >= 0:
        t = tuple(v + (255 - v) * f for v in (r, g, b))
    else:
        t = tuple(v * (1 + f) for v in (r, g, b))
    return _rgb(t)


def fetch_days():
    """Return (grid_weeks, all_days). grid_weeks: last 26 Sun-Sat weeks,
    each a list of 7 (date, count, color). all_days: flat ascending list
    over the whole fetched range (used for streak)."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=29 * 7)
    q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
        user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
                contributionCalendar {
                    weeks { contributionDays { date contributionCount color } }
                }
            }
        }
    }"""
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": q, "variables": {
            "login": GITHUB_USERNAME,
            "from": f"{start}T00:00:00Z",
            "to": f"{today}T23:59:59Z"}},
        headers={"Authorization": f"bearer {TOKEN}"},  # never printed
        timeout=60,
    )
    body = r.json()
    user = (body.get("data") or {}).get("user")
    if r.status_code != 200 or not user:
        raise RuntimeError(f"status={r.status_code} errors={body.get('errors')}")
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = weeks[-WEEKS:]
    all_days = [(d["date"], d["contributionCount"])
                for w in weeks for d in w["contributionDays"]]
    cells = [[(d["date"], d["contributionCount"], d["color"]) for d in w["contributionDays"]]
             for w in grid]
    return cells, all_days


def current_streak(all_days):
    """Consecutive days with >=1 contribution ending today (or yesterday
    if today is still empty)."""
    days = sorted(all_days)
    idx = len(days) - 1
    if days and days[idx][1] == 0:
        idx -= 1  # today empty: streak counts back from yesterday
    streak = 0
    while idx >= 0 and days[idx][1] > 0:
        streak += 1
        idx -= 1
    return streak


def diamond(cx, cy):
    hw, hh = HW, HH
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


def poly(points, fill, opacity=None):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<polygon points="{p}" fill="{fill}"{op}/>'


def windows_face(p0, p1, hgt, seed, lit_prob=0.45):
    """Window grid on one wall, as parallelograms following the wall slant.

    p0 -> p1 runs along the TOP edge of the wall (e.g. upper-left to
    upper-right corner); windows hang straight down from it, so vertical
    edges stay perpendicular while horizontal edges stay parallel to the
    wall slant. 3.5px side margins, 4px top/bottom margins; faces too
    short for one full window row are left plain so nothing overflows.
    Deterministic per seed. Window ratio ~1:1.5 (wider than tall is
    avoided: ww x wh below).
    """
    import math
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    edge = math.hypot(ux, uy)
    ux, uy = ux / edge, uy / edge
    m, gap, wh, vgap = 3.5, 2.0, 7.5, 4.0
    usable_w, usable_h = edge - 2 * m, hgt - 2 * 4
    cols = 2
    ww = (usable_w - gap) / cols
    rows = int((usable_h + vgap) // (wh + vgap))
    if ww < 3 or rows < 1:
        return ""  # too small: keep the wall plain, never overflow
    used_h = rows * wh + (rows - 1) * vgap
    y0 = 4 + (usable_h - used_h) / 2
    rng = random.Random(seed)
    out = []
    for rr in range(rows):
        for cc in range(cols):
            bx = p0[0] + m * ux + cc * (ww + gap) * ux
            by = p0[1] + m * uy + cc * (ww + gap) * uy + y0 + rr * (wh + vgap)
            tl = (bx, by)
            tr = (bx + ww * ux, by + ww * uy)
            br = (tr[0], tr[1] + wh)
            bl = (bx, by + wh)
            if rng.random() < lit_prob:
                fill = "#ffd76a" if rng.random() < 0.7 else "#7ee787"
                out.append("  " + poly([tl, tr, br, bl], fill))
            else:
                out.append("  " + poly([tl, tr, br, bl], "#0d1117", 0.5))
    return "".join(out)


def render(cells, streak, avg, total):
    max_count = max((c for w in cells for _, c, _ in w), default=0)

    def height(count):
        if count <= 0 or max_count == 0:
            return 0
        return max(7, round(count / max_count * MAX_H))

    # Pass 1: bounds (ground diamonds + tops + antenna space).
    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    def track(x, y):
        nonlocal minx, miny, maxx, maxy
        minx, miny, maxx, maxy = min(minx, x), min(miny, y), max(maxx, x), max(maxy, y)

    Hs = [[height(c) for _, c, _ in w] for w in cells]
    tallest = None  # (count, week_idx, day_idx); first max wins
    for wi, w in enumerate(cells):
        for di, (_, c, _) in enumerate(w):
            cx, cy = (wi - di) * HW, (wi + di) * HH
            h = Hs[wi][di]
            for x, y in diamond(cx, cy):
                track(x, y)
            if h:
                track(cx, cy - HH - h)
                if c > 0 and (tallest is None or c > tallest[0]):
                    tallest = (c, wi, di)
                    track(cx, cy - HH - h - 18)  # antenna tip

    pad, title_h = 24, 46
    ox, oy = pad - minx, title_h + pad - miny
    left_w = maxx - minx
    svg_w = 1000
    svg_h = int(title_h + pad + (maxy - miny) + pad)
    stats_x = pad + left_w + 40

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">']
    parts.append(f'  <rect width="{svg_w}" height="{svg_h}" rx="12" fill="{BG}" stroke="{BORDER}"/>')
    parts.append('  <circle cx="25" cy="18" r="6" fill="#ff5f57"/>')
    parts.append('  <circle cx="45" cy="18" r="6" fill="#febc2e"/>')
    parts.append('  <circle cx="65" cy="18" r="6" fill="#28c840"/>')

    # Title: calendar icon + blue link-style text.
    parts.append(f'  <g transform="translate({pad},33)">'
                 f'<rect x="0" y="0" width="15" height="14" rx="2.5" fill="none" stroke="{BLUE}" stroke-width="1.6"/>'
                 f'<line x1="4" y1="-2" x2="4" y2="3" stroke="{BLUE}" stroke-width="1.6"/>'
                 f'<line x1="11" y1="-2" x2="11" y2="3" stroke="{BLUE}" stroke-width="1.6"/>'
                 f'<line x1="0" y1="5" x2="15" y2="5" stroke="{BLUE}" stroke-width="1.4"/>'
                 f'<text x="21" y="12" {MONO} font-size="15" fill="{BLUE}">Contributions calendar</text></g>')

    # Pass 2: back-to-front cells. Weeks may be ragged (partial edge
    # weeks from the API), so iterate actual cells sorted by depth key.
    antennas = []
    order = sorted(
        ((wi, di) for wi, w in enumerate(cells) for di in range(len(w))),
        key=lambda t: t[0] + t[1],
    )
    for wi, di in order:
        date, count, color = cells[wi][di]
        h = Hs[wi][di]
        cx, cy = ox + (wi - di) * HW, oy + (wi + di) * HH
        n, e, ss, ww = (cx, cy - HH), (cx + HW, cy), (cx, cy + HH), (cx - HW, cy)
        if not h:
            parts.append("  " + poly([n, e, ss, ww], LOT_FILL))
            continue
        top = shade(color, 0.35)
        parts.append("  " + poly([(cx, cy - HH - h), (cx + HW, cy - h),
                                  (cx, cy + HH - h), (cx - HW, cy - h)], top))
        parts.append("  " + poly([ww, ss, (cx, cy + HH - h), (cx - HW, cy - h)], color))
        parts.append("  " + poly([e, ss, (cx, cy + HH - h), (cx + HW, cy - h)], shade(color, -0.25)))
        parts.append("  " + windows_face((cx - HW, cy - h), (cx, cy + HH - h), h, f"{date}|L"))
        parts.append("  " + windows_face((cx + HW, cy - h), (cx, cy + HH - h), h, f"{date}|R"))
        if tallest is not None and (wi, di) == (tallest[1], tallest[2]):
            tx, ty = cx, cy - HH - h
            antennas.append(f'  <line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx:.1f}" y2="{ty - 15:.1f}" stroke="{GRAY}" stroke-width="2"/>'
                            f'<circle cx="{tx:.1f}" cy="{ty - 16:.1f}" r="2.5" fill="#f85149"/>')
    parts.extend(antennas)

    # Right stats panel.
    my = oy + (maxy - miny) / 2
    parts.append(
        f'  <g transform="translate({stats_x:.1f},{my - 22:.1f})">'
        f'<path d="M8 0.5C6 3 3.5 5.5 3.5 9.5C3.5 13 5.8 15.5 8.5 15.5C11.5 15.5 13.5 13.2 13.5 10C13.5 7 11 5 10 2.5C9.3 4.5 8.5 5 8 5C8.3 3.5 8.3 2 8 0.5Z" fill="#f0883e"/>'
        f'<text x="22" y="13" {MONO} font-size="14" fill="#c9d1d9">Current streak <tspan font-weight="700" fill="{WHITE}">{streak} days</tspan></text></g>')
    parts.append(
        f'  <g transform="translate({stats_x:.1f},{my + 14:.1f})">'
        f'<polyline points="1,15 1,1 15,1" fill="none" stroke="{GRAY}" stroke-width="1.5"/>'
        f'<polyline points="2,11 6,8 10,9 14,4" fill="none" stroke="#3fb950" stroke-width="1.8"/>'
        f'<circle cx="14" cy="4" r="2" fill="#3fb950"/>'
        f'<text x="22" y="13" {MONO} font-size="14" fill="#c9d1d9">~<tspan font-weight="700" fill="{WHITE}">{avg:.2f}</tspan> commits per day</text></g>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not TOKEN:
        print("No token (STATS_TOKEN/GITHUB_TOKEN); keeping previous city.svg")
        sys.exit(1)
    cells, all_days = fetch_days()
    shown = WEEKS * 7
    flat = [(d, c) for w in cells for d, c, _ in w][-shown:]
    total = sum(c for _, c in flat)
    svg = render(cells, current_streak(all_days), total / max(1, len(flat)), total)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "city.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"city.svg written to {out} ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
