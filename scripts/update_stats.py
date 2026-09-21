#!/usr/bin/env python3
"""
Fetch GitHub stats via API and regenerate the neofetch SVG.
Called by GitHub Actions workflow.
"""
import os
import json
import requests
from datetime import datetime, timezone

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

    # Manual baselines: true values including private repos, which the
    # public API can't see. Kept unless a full-accuracy refresh succeeds.
    stats["lines_of_code"] = 70654
    stats["commits"] = 388
    stats["repos_total"] = 25
    stats["repos_contrib"] = 9

    # Full-accuracy refresh via GraphQL, only with STATS_TOKEN (a PAT that
    # can see private repos). GITHUB_TOKEN can't, so without STATS_TOKEN we
    # keep the manual baselines instead of trusting incomplete data.
    # Note: totalContributions counts all contribution types (commits + PRs
    # + issues + reviews), so it may read slightly above pure commits.
    pat = os.environ.get("STATS_TOKEN", "").strip()
    if pat:
        api = "https://api.github.com/graphql"
        gql_headers = {"Authorization": f"bearer {pat}"}  # never printed/logged

        def gql(query, variables):
            # Raises RuntimeError with the API's own error message.
            # Never logs the token itself.
            r = requests.post(api, json={"query": query, "variables": variables}, headers=gql_headers, timeout=30)
            body = r.json()
            if r.status_code != 200 or not body.get("data"):
                raise RuntimeError(f"status={r.status_code} errors={body.get('errors', body)}")
            return body["data"]

        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            commits_q = """
            query($login: String!, $from: DateTime!, $to: DateTime!) {
                user(login: $login) {
                    contributionsCollection(from: $from, to: $to) {
                        contributionCalendar { totalContributions }
                    }
                }
            }"""
            data = gql(commits_q, {"login": GITHUB_USERNAME, "from": "2008-01-01T00:00:00Z", "to": now})
            total = data["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
            stats["commits"] = int(total)
            print(f"   commits refresh ok: {stats['commits']}")
        except Exception as e:
            print(f"   commits refresh failed ({e}), keeping baseline {stats['commits']}")

        try:
            repos_q = """
            query($login: String!) {
                user(login: $login) {
                    owned: repositories(ownerAffiliations: [OWNER]) { totalCount }
                    involved: repositories(ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) { totalCount }
                }
            }"""
            data = gql(repos_q, {"login": GITHUB_USERNAME})
            owned = int(data["user"]["owned"]["totalCount"])
            involved = int(data["user"]["involved"]["totalCount"])
            stats["repos_total"] = owned
            stats["repos_contrib"] = involved - owned
            print(f"   repos refresh ok: {owned} (contrib {stats['repos_contrib']})")
        except Exception as e:
            print(f"   repos refresh failed ({e}), keeping baselines")

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
    # Fixed repos count (manual count, includes private repos
    # invisible to the public API). Daily Action keeps this value.
    repos_str = f"{stats['repos_total']:,} (Contributed: {stats['repos_contrib']:,})"
    
    # Dynamic info lines
    info_lines = [
        [(C["green"], True, "brenandapamudya1"), (C["white"], True, "@"), (C["green"], True, "github")],
        [(C["gray"], False, "——————————————————————————————————————————————")],
        [(C["green"], True, "OS: "), (C["white"], False, "Ubuntu 22.04, Windows 11")],
        [(C["green"], True, "Uptime: "), (C["white"], False, f"{uptime_str}")],
        [(C["green"], True, "Host: "), (C["white"], False, "Institut Teknologi Sepuluh Nopember, Surabaya")],
        [(C["green"], True, "Kernel: "), (C["white"], False, "Linux x86_64")],
        [(C["green"], True, "IDE: "), (C["white"], False, "VSCode 1.125.0")],
        [],
        [(C["yellow"], True, "Languages.Programming: "), (C["white"], False, "Python, C++, R")],
        [(C["yellow"], True, "Languages.Computer: "), (C["white"], False, "HTML, CSS, JSON, YAML")],
        [(C["yellow"], True, "Languages.Real: "), (C["white"], False, "English, Indonesia")],
        [],
        [(C["yellow"], True, "Hobbies.Software: "), (C["white"], False, "Robotics, Computer Vision, Web-Dev")],
        [(C["yellow"], True, "Hobbies.Personal: "), (C["white"], False, "Reading, Watching Anime")],
        [],
        [(C["yellow"], True, "— Contact —————————————————————————————————")],
        [(C["green"], True, "Email.Personal: "), (C["white"], False, "brenandapamudya178@gmail.com")],
        [(C["green"], True, "Email.Work: "), (C["white"], False, "5003251085@student.its.ac.id")],
        [(C["green"], True, "LinkedIn: "), (C["white"], False, "Brenanda Caesa Pamudya")],
        [],
        [(C["yellow"], True, "— GitHub Stats ————————————————————————————")],
        [(C["green"], True, "Repos: "), (C["white"], False, f"{repos_str}")],
        [(C["green"], True, "Commits: "), (C["white"], False, f"{stats['commits']:,}")],
        [(C["green"], True, "Lines of Code: "), (C["white"], False, f"{stats['lines_of_code']:,}")],
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

    # Info: label + dot leaders + value, fixed total width so all
    # values end at the same column (technique adapted from
    # references.py::justify_format).
    info_x = padding_x + ascii_col_width + gap
    FIELD_WIDTH = 66
    for i, segments in enumerate(info_lines):
        if not segments:
            continue
        y = padding_top + i * line_height + font_size

        # Label: value lines -> label + dots + value, values end aligned
        if len(segments) == 2:
            (lc, lb, label), (vc, vb, value) = segments
            dots = '.' * max(1, FIELD_WIDTH - len(label) - len(value))
            lw = ' font-weight="700"' if lb else ''
            vw = ' font-weight="700"' if vb else ''
            parts.append(
                f'  <text x="{info_x}" y="{y:.1f}" xml:space="preserve" {font_attr} font-size="{font_size}">'
                f'<tspan fill="{lc}"{lw}>{escape(label)}</tspan>'
                f'<tspan fill="{C["gray"]}">{dots}</tspan>'
                f'<tspan fill="{vc}"{vw}>{escape(value)}</tspan></text>'
            )
            continue

        # Header / separator / section titles -> single left-anchored text
        text_elem = f'  <text x="{info_x}" y="{y:.1f}" xml:space="preserve" {font_attr} font-size="{font_size}">'
        for color, bold, content in segments:
            weight = ' font-weight="700"' if bold else ''
            text_elem += f'<tspan fill="{color}"{weight}>{escape(content)}</tspan>'
        text_elem += '</text>'
        parts.append(text_elem)

    parts.append('</svg>')
    return '\n'.join(parts)


if __name__ == "__main__":
    print("Fetching GitHub stats...")
    stats = fetch_github_stats()
    print(f"   Repos: {stats['repos']}, Stars: {stats['stars']}, Followers: {stats['followers']}, LoC: {stats['lines_of_code']:,}, Commits: {stats['commits']:,}, Owned: {stats['repos_total']} (contrib {stats['repos_contrib']})")
    
    print("Generating SVG...")
    svg = generate_svg(stats)
    
    output = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "neofetch.svg")
    with open(output, "w", encoding="utf-8") as f:
        f.write(svg)
    
    print(f"SVG written to {output}")
