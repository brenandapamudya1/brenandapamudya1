#!/usr/bin/env python3
"""
Generate neofetch-style SVG for GitHub Profile README.
Uses native SVG <text> + <tspan> elements for reliable GitHub rendering.
GitHub sanitizes foreignObject, so we use pure SVG text instead.
"""

def escape(text):
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))

def generate():
    # === ASCII ART (left side) ===
    # Shiro (No Game No Life) - symbol charset, 55x35, no-background
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

    # === INFO LINES (right side) ===
    # Each line is rendered as a single <text> with colored <tspan>s
    # Format: list of (color, bold, text) segments per line
    
    C = {
        "cyan":   "#58a6ff",
        "green":  "#3fb950",
        "yellow": "#d29922",
        "white":  "#e6edf3",
        "gray":   "#8b949e",
        "orange": "#f0883e",
    }

    info_lines = [
        # Line 0: header
        [(C["green"], True, "brenandapamudya1"), (C["white"], True, "@"), (C["green"], True, "github")],
        # Line 1: separator
        [(C["gray"], False, "——————————————————————————————————————————————")],
        # Line 2-6: System info
        [(C["green"], True, "OS: "), (C["white"], False, ".................. [placeholder]")],
        [(C["green"], True, "Uptime: "), (C["white"], False, "................ [placeholder]")],
        [(C["green"], True, "Host: "), (C["white"], False, ".................. [placeholder]")],
        [(C["green"], True, "Kernel: "), (C["white"], False, "................ [placeholder]")],
        [(C["green"], True, "IDE: "), (C["white"], False, "................... [placeholder]")],
        # Line 7: empty
        [],
        # Line 8-10: Languages
        [(C["yellow"], True, "Languages.Programming: "), (C["white"], False, ".. [placeholder]")],
        [(C["yellow"], True, "Languages.Computer: "), (C["white"], False, "..... [placeholder]")],
        [(C["yellow"], True, "Languages.Real: "), (C["white"], False, "......... [placeholder]")],
        # Line 11: empty
        [],
        # Line 12-13: Hobbies
        [(C["yellow"], True, "Hobbies.Software: "), (C["white"], False, "....... [placeholder]")],
        [(C["yellow"], True, "Hobbies.Hardware: "), (C["white"], False, "....... [placeholder]")],
        # Line 14: empty
        [],
        # Line 15: Contact section header
        [(C["yellow"], True, "— Contact —————————————————————————————————")],
        # Line 16-19: Contact info
        [(C["green"], True, "Email.Personal: "), (C["white"], False, "......... [placeholder]")],
        [(C["green"], True, "Email.Work: "), (C["white"], False, "............. [placeholder]")],
        [(C["green"], True, "LinkedIn: "), (C["white"], False, "............... [placeholder]")],
        [(C["green"], True, "Discord: "), (C["white"], False, "................ [placeholder]")],
        # Line 20: empty
        [],
        # Line 21: GitHub Stats section header
        [(C["yellow"], True, "— GitHub Stats ————————————————————————————")],
        # Line 22-26: Stats
        [(C["green"], True, "Repos: "), (C["white"], False, "................ [placeholder]")],
        [(C["green"], True, "Commits: "), (C["white"], False, ".............. [placeholder]")],
        [(C["green"], True, "Stars: "), (C["white"], False, "................ [placeholder]")],
        [(C["green"], True, "Followers: "), (C["white"], False, "............ [placeholder]")],
        [(C["green"], True, "Lines of Code: "), (C["white"], False, "........ [placeholder]")],
        # Line 27: empty
        [],
    ]

    # === SVG CONFIG ===
    font_size = 13
    line_height = 17
    ascii_font_size = 11.5
    ascii_line_height = 15.5
    padding_x = 20
    padding_top = 45  # space for title bar
    padding_bottom = 15
    ascii_col_width = 420  # px width for ascii art column (55 cols)
    gap = 20  # px gap between columns

    total_lines = max(len(ascii_art), len(info_lines))
    content_height = max(len(ascii_art) * ascii_line_height, len(info_lines) * line_height)
    svg_height = int(padding_top + content_height + padding_bottom)
    svg_width = 1000

    bg_color = "#0d1117"
    border_color = "#30363d"

    # === BUILD SVG ===
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">')
    
    # Background
    parts.append(f'  <rect width="{svg_width}" height="{svg_height}" rx="12" ry="12" fill="{bg_color}" stroke="{border_color}" stroke-width="1"/>')
    
    # Title bar dots
    parts.append(f'  <circle cx="25" cy="18" r="6" fill="#ff5f57"/>')
    parts.append(f'  <circle cx="45" cy="18" r="6" fill="#febc2e"/>')
    parts.append(f'  <circle cx="65" cy="18" r="6" fill="#28c840"/>')
    
    # Title bar label
    parts.append(f'  <text x="{svg_width // 2}" y="21" text-anchor="middle" font-family="\'SF Mono\', Consolas, monospace" font-size="12" fill="{C["gray"]}">brenandapamudya1 — README.md</text>')

    # ASCII art
    for i, line in enumerate(ascii_art):
        y = padding_top + i * ascii_line_height + ascii_font_size
        parts.append(f'  <text x="{padding_x}" y="{y:.1f}" xml:space="preserve" font-family="\'JetBrains Mono\', \'Cascadia Code\', \'Fira Code\', \'SF Mono\', Consolas, monospace" font-size="{ascii_font_size}" fill="{C["cyan"]}">{escape(line)}</text>')

    # Info lines
    info_x = padding_x + ascii_col_width + gap
    for i, segments in enumerate(info_lines):
        if not segments:
            continue
        y = padding_top + i * line_height + font_size
        
        # Build text element with tspan children
        text_elem = f'  <text x="{info_x}" y="{y:.1f}" xml:space="preserve" font-family="\'JetBrains Mono\', \'Cascadia Code\', \'Fira Code\', \'SF Mono\', Consolas, monospace" font-size="{font_size}">'
        
        for color, bold, content in segments:
            weight = ' font-weight="700"' if bold else ''
            text_elem += f'<tspan fill="{color}"{weight}>{escape(content)}</tspan>'
        
        text_elem += '</text>'
        parts.append(text_elem)

    parts.append('</svg>')
    return '\n'.join(parts)


if __name__ == "__main__":
    svg = generate()
    output = "/home/brenandacaesa/PROJECT/GithubReadme/neofetch.svg"
    with open(output, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✅ SVG written to {output}")
    print(f"   File size: {len(svg):,} bytes")
