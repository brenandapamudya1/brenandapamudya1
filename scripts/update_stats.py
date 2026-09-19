#!/usr/bin/env python3
"""
Fetch GitHub stats via API and regenerate the neofetch SVG.
Called by GitHub Actions workflow.
"""
import os
import json
import requests

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "brenandapamudya1")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def fetch_github_stats():
    """Fetch stats from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    stats = {
        "repos": 0,
        "contributed_repos": 0,
        "stars": 0,
        "commits": 0,
        "followers": 0,
        "following": 0,
        "lines_added": 0,
        "lines_deleted": 0,
    }

    # Fetch user info
    user_resp = requests.get(
        f"https://api.github.com/users/{GITHUB_USERNAME}",
        headers=headers,
    )
    if user_resp.status_code == 200:
        user_data = user_resp.json()
        stats["repos"] = user_data.get("public_repos", 0)
        stats["followers"] = user_data.get("followers", 0)
        stats["following"] = user_data.get("following", 0)

    # Fetch repos and count stars
    page = 1
    all_repos = []
    while True:
        repos_resp = requests.get(
            f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100&page={page}",
            headers=headers,
        )
        if repos_resp.status_code != 200:
            break
        repos = repos_resp.json()
        if not repos:
            break
        all_repos.extend(repos)
        page += 1

    stats["stars"] = sum(r.get("stargazers_count", 0) for r in all_repos)
    stats["repos"] = len(all_repos)

    # Count contributed repos (forked repos count as contributed)
    stats["contributed_repos"] = sum(1 for r in all_repos if r.get("fork", False))

    # Estimate total commits (from events API - limited to recent 300)
    events_resp = requests.get(
        f"https://api.github.com/users/{GITHUB_USERNAME}/events?per_page=100",
        headers=headers,
    )
    if events_resp.status_code == 200:
        events = events_resp.json()
        push_events = [e for e in events if e.get("type") == "PushEvent"]
        stats["commits"] = sum(
            len(e.get("payload", {}).get("commits", []))
            for e in push_events
        )
    
    # Note: For accurate total commits, you'd need to iterate all repos
    # and sum up contributor stats. This is a simplified version.

    return stats


def escape(text):
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def generate_svg(stats):
    """Generate the neofetch SVG with real stats."""
    
    # ASCII art - Shiro (No Game No Life), symbol charset, 55x35, no-background
    ascii_art = [
        "          .                                   .        ",
        "         .           .                         ...     ",
        "                   ..           .                 :-   ",
        "             .    ..      .:..::                   -:  ",
        "           ..    .:     .--.:-:...     .   .  .   . .  ",
        "          .  .  := .  .-=-.=-. .  ... ::  .=: .    .   ",
        "         .  .. -+: : -==:.=:         .=.  :=:   .-  .  ",
        "        .  . .-++.:===+-.=:.         --  .=+:.   =:    ",
        "       .  . .:+*= =+++=.=:.  ..     .=: .:+-=. . -:  - ",
        "       . . ::=+*::++++:=-        .. -= .:=+.-. . ::  #:",
        "      .. .:-:+**.-+++=--         .. =- --+- :. - .. -=.",
        "      ...=+:=+*-:++++=+--.       :. +.:-=+..:: =  . *.:",
        "      ::.*-:++:::++++#@@@@*:       :=.==#=..:: +- .:* .",
        "     :+=.+.=*==--+++-:#@@@@@*:     =:-=+=.  .: *+  +*  ",
        "    .++*=:-+*==:=++=: +%*=#*=#:    =:++=     :.+=: +*  ",
        "    -*+*--+***-:+++-. :-.    :.   :--++...   -.+: .:*  ",
        "   .+**= -***#+:**+:   -=-:       .:+##%%#* -+:+. *=+::",
        "   =**+ .+*#%#+:**+:   :==.       .:#%%%===+**=+ .@@#@%",
        "  :***. =***%#+:**=. ..           .-*:.   =#*#*= =%%%@#",
        " .+**: -***##*+-*++-             ..=#+:  +#**##= ===*##",
        " :**- :****%#**-*++*-            ..=*-  +%#*###=.-.-*#=",
        ".=#- .+***##*#*-*=+**=.          ..+=  +*##*##+.=+*#+: ",
        ":*=  =#*##%###%-*-****+-       . ..+= +#*%#*##+ ===.   ",
        "++. -####%###%%=+-******+:       ..=*+#*#%#*%#-.       ",
        "+. :*###%%###=+#=-*********-.  :-+:-%#*##%####-.       ",
        "...*###%%#+-.  -=-:=*****%@#*+*#%@=:#%###%##%*:.       ",
        "..*%%#*+-.     .--. :=*##@@@@%##%%*.*%###%##%*:        ",
        ".++-=+=:   .   .--.   :+#%@@*:-+#@%:=%%##%##%*:        ",
        "*@%%*==+=:.  .. :-=     :=:-    .=*+:#%%#%##%#-        ",
        "@@@@@@%**+=: ...:=-=:..    .: .    +-=%%#%%#%#=.       ",
        "@@@@@@@@@#**=....=-:-.::...:-  ....-#-#@%%%%%#+:       ",
        "@@@@@@@@@@@***=..-=.:-....--=-:....-#==@@@%%%%+=       ",
        "@@@@@@@@@@@%++**--+:.:-. =@@@@@#...=#%=#@@%%#**+.      ",
        "@@@@@@@@@@@@++#**#*-..-++@@@@@@@:.:+%@%+@@%%*=#*-.     ",
        "@@@@@@@@@@@@#=@@*+#*-:.+@@@@@@@@:.-##%@#%@%%*-#*=:     ",
    ]

    # Colors
    C = {
        "cyan":   "#58a6ff",
        "green":  "#3fb950",
        "yellow": "#d29922",
        "white":  "#e6edf3",
        "gray":   "#8b949e",
        "orange": "#f0883e",
    }

    # Fixed uptime (7227 days = 19 years, 9 months, 22 days).
    # Hardcoded so the daily Action keeps this value instead of
    # recomputing it from the GitHub account age.
    uptime_str = "19 years, 9 months, 22 days (7227 days)"
    repos_str = f"{stats['repos']} (Contributed: {stats['contributed_repos']})"
    
    # Dynamic info lines
    info_lines = [
        [(C["green"], True, "brenandapamudya1"), (C["white"], True, "@"), (C["green"], True, "github")],
        [(C["gray"], False, "——————————————————————————————————————————————")],
        [(C["green"], True, "OS: "), (C["white"], False, "Ubuntu 22.04, Windows 11")],
        [(C["green"], True, "Uptime: "), (C["white"], False, f"................ {uptime_str}")],
        [(C["green"], True, "Host: "), (C["white"], False, "Institut Teknologi Sepuluh Nopember, Surabaya")],
        [(C["green"], True, "Kernel: "), (C["white"], False, "6.8.0-138-generic")],
        [(C["green"], True, "IDE: "), (C["white"], False, "................... [placeholder]")],
        [],
        [(C["yellow"], True, "Languages.Programming: "), (C["white"], False, ".. [placeholder]")],
        [(C["yellow"], True, "Languages.Computer: "), (C["white"], False, "..... [placeholder]")],
        [(C["yellow"], True, "Languages.Real: "), (C["white"], False, "......... [placeholder]")],
        [],
        [(C["yellow"], True, "Hobbies.Software: "), (C["white"], False, "....... [placeholder]")],
        [(C["yellow"], True, "Hobbies.Hardware: "), (C["white"], False, "....... [placeholder]")],
        [],
        [(C["yellow"], True, "— Contact —————————————————————————————————")],
        [(C["green"], True, "Email.Personal: "), (C["white"], False, "......... [placeholder]")],
        [(C["green"], True, "Email.Work: "), (C["white"], False, "............. [placeholder]")],
        [(C["green"], True, "LinkedIn: "), (C["white"], False, "............... [placeholder]")],
        [(C["green"], True, "Discord: "), (C["white"], False, "................ [placeholder]")],
        [],
        [(C["yellow"], True, "— GitHub Stats ————————————————————————————")],
        [(C["green"], True, "Repos: "), (C["white"], False, f"................ {repos_str}")],
        [(C["green"], True, "Commits: "), (C["white"], False, f".............. {stats['commits']}")],
        [(C["green"], True, "Stars: "), (C["white"], False, f"................ {stats['stars']}")],
        [(C["green"], True, "Followers: "), (C["white"], False, f"............ {stats['followers']}")],
        [(C["green"], True, "Lines of Code: "), (C["white"], False, "........ [placeholder]")],
        [],
    ]

    # SVG dimensions
    font_size = 13
    line_height = 17
    ascii_font_size = 11.5
    ascii_line_height = 15.5
    padding_x = 20
    padding_top = 45
    padding_bottom = 15
    ascii_col_width = 420
    gap = 20

    content_height = max(len(ascii_art) * ascii_line_height, len(info_lines) * line_height)
    svg_height = int(padding_top + content_height + padding_bottom)
    svg_width = 1000
    bg_color = "#0d1117"
    border_color = "#30363d"

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">')
    parts.append(f'  <rect width="{svg_width}" height="{svg_height}" rx="12" ry="12" fill="{bg_color}" stroke="{border_color}" stroke-width="1"/>')
    parts.append(f'  <circle cx="25" cy="18" r="6" fill="#ff5f57"/>')
    parts.append(f'  <circle cx="45" cy="18" r="6" fill="#febc2e"/>')
    parts.append(f'  <circle cx="65" cy="18" r="6" fill="#28c840"/>')
    parts.append(f'  <text x="{svg_width // 2}" y="21" text-anchor="middle" font-family="\'SF Mono\', Consolas, monospace" font-size="12" fill="{C["gray"]}">brenandapamudya1 — README.md</text>')

    font_attr = "font-family=\"'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'SF Mono', Consolas, monospace\""

    # ASCII art
    for i, line in enumerate(ascii_art):
        y = padding_top + i * ascii_line_height + ascii_font_size
        parts.append(f'  <text x="{padding_x}" y="{y:.1f}" xml:space="preserve" {font_attr} font-size="{ascii_font_size}" fill="{C["cyan"]}">{escape(line)}</text>')

    # Info
    info_x = padding_x + ascii_col_width + gap
    for i, segments in enumerate(info_lines):
        if not segments:
            continue
        y = padding_top + i * line_height + font_size
        text_elem = f'  <text x="{info_x}" y="{y:.1f}" xml:space="preserve" {font_attr} font-size="{font_size}">'
        for color, bold, content in segments:
            weight = ' font-weight="700"' if bold else ''
            text_elem += f'<tspan fill="{color}"{weight}>{escape(content)}</tspan>'
        text_elem += '</text>'
        parts.append(text_elem)

    parts.append('</svg>')
    return '\n'.join(parts)


if __name__ == "__main__":
    print("🔍 Fetching GitHub stats...")
    stats = fetch_github_stats()
    print(f"   Repos: {stats['repos']}, Stars: {stats['stars']}, Followers: {stats['followers']}")
    
    print("🎨 Generating SVG...")
    svg = generate_svg(stats)
    
    output = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "neofetch.svg")
    with open(output, "w", encoding="utf-8") as f:
        f.write(svg)
    
    print(f"✅ SVG written to {output}")
