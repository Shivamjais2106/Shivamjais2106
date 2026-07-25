# """
# generate_profile.py
# --------------------
# Builds a neofetch-style terminal SVG (dark.svg + light.svg) using:
#   - config.json      -> personal info, stack, projects, links
#   - portrait.txt      -> pixel-color grid (from photo_to_ascii.py)
#   - GitHub public API -> total contributions + current/longest streak

# Then injects <picture> markup into README.md between:
#   <!--START_SECTION:profile--> ... <!--END_SECTION:profile-->

# Usage:
#     python generate_profile.py
# """

# import json
# import datetime
# import urllib.request

# CONFIG_FILE = "config.json"
# PORTRAIT_FILE = "portrait.txt"
# README_FILE = "README.md"
# START_MARKER = "<!--START_SECTION:profile-->"
# END_MARKER = "<!--END_SECTION:profile-->"

# CELL = 4          # px size of each pixel-art cell
# PANEL_W = 900
# FONT = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"


# # ---------- data loading ----------

# def load_config():
#     with open(CONFIG_FILE) as f:
#         return json.load(f)


# def load_portrait():
#     with open(PORTRAIT_FILE) as f:
#         lines = [l.strip() for l in f if l.strip()]
#     return [line.split(",") for line in lines]


# def fetch_contribution_stats(username):
#     """Uses the free github-contributions-api (no auth needed) to get a
#     daily contribution list, then derives total / current / longest streak."""
#     url = f"https://github-contributions-api.jogruber.de/v4/{username}?y=all"
#     try:
#         with urllib.request.urlopen(url, timeout=10) as resp:
#             data = json.loads(resp.read().decode())
#         days = data.get("contributions", [])
#         days.sort(key=lambda d: d["date"])
#     except Exception as e:
#         print(f"warning: could not fetch contribution stats ({e}); using zeros")
#         return {"total": 0, "current_streak": 0, "current_range": "-",
#                 "longest_streak": 0, "longest_range": "-"}

#     total = sum(d["count"] for d in days)

#     # current streak: walk back from today/most recent day
#     today = datetime.date.today()
#     by_date = {d["date"]: d["count"] for d in days}
#     cur_streak = 0
#     cur_end = None
#     cursor = today
#     while True:
#         key = cursor.isoformat()
#         if by_date.get(key, 0) > 0:
#             if cur_end is None:
#                 cur_end = cursor
#             cur_streak += 1
#             cursor -= datetime.timedelta(days=1)
#         else:
#             if cursor == today:
#                 # today has no contribution yet; check yesterday onward
#                 cursor -= datetime.timedelta(days=1)
#                 today = cursor  # shift window start
#                 continue
#             break
#     cur_start = cursor + datetime.timedelta(days=1) if cur_streak else None

#     # longest streak
#     longest = 0
#     longest_start = longest_end = None
#     run = 0
#     run_start = None
#     for d in days:
#         if d["count"] > 0:
#             if run == 0:
#                 run_start = d["date"]
#             run += 1
#             if run > longest:
#                 longest = run
#                 longest_start = run_start
#                 longest_end = d["date"]
#         else:
#             run = 0

#     def fmt(d):
#         if isinstance(d, str):
#             d = datetime.date.fromisoformat(d)
#         return d.strftime("%b %d")

#     return {
#         "total": total,
#         "current_streak": cur_streak,
#         "current_range": f"{fmt(cur_start)} - {fmt(cur_end)}" if cur_streak else "-",
#         "longest_streak": longest,
#         "longest_range": f"{fmt(longest_start)} - {fmt(longest_end)}" if longest else "-",
#     }


# # ---------- svg building ----------

# def esc(s):
#     return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# def build_pixel_art(grid, x, y):
#     """Returns list of <rect> strings for the portrait grid at offset x,y."""
#     out = []
#     for ry, row in enumerate(grid):
#         for rx, color in enumerate(row):
#             out.append(
#                 f'<rect x="{x + rx * CELL}" y="{y + ry * CELL}" '
#                 f'width="{CELL}" height="{CELL}" fill="{color}"/>'
#             )
#     return "".join(out)


# def build_svg(cfg, grid, stats, theme="dark"):
#     colors = {
#         "dark": dict(bg="#0d1117", panel="#161b22", border="#30363d",
#                      text="#c9d1d9", dim="#8b949e", accent="#7ee787",
#                      accent2="#58a6ff", warn="#f0883e", title="#e6edf3"),
#         "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de",
#                       text="#24292f", dim="#57606a", accent="#116329",
#                       accent2="#0969da", warn="#9a6700", title="#1f2328"),
#     }[theme]

#     grid_h = len(grid)
#     grid_w = len(grid[0]) if grid_h else 0
#     art_w = grid_w * CELL
#     art_h = grid_h * CELL

#     top_bar_h = 34
#     content_y = top_bar_h + 30
#     art_x = 24
#     text_x = art_x + art_w + 40

#     lines = []  # (label, value) or ("__section__", title) or ("__raw__", text)
#     lines.append(("__raw__", f'{cfg["name"]}'))
#     lines.append(("__gap__", ""))
#     lines.append(("Role", cfg["role"]))
#     lines.append(("Edu", cfg["edu"]))
#     lines.append(("Focus", cfg["focus"]))
#     lines.append(("__gap__", ""))
#     lines.append(("__section__", "~/stack"))
#     for k, v in cfg["stack"].items():
#         lines.append((k, v))
#     lines.append(("__gap__", ""))
#     lines.append(("__section__", "~/projects"))
#     for k, v in cfg["projects"].items():
#         lines.append((k, v))
#     lines.append(("__gap__", ""))
#     lines.append(("__section__", "~/highlights"))
#     for k, v in cfg["highlights"].items():
#         lines.append((k, v))
#     lines.append(("__gap__", ""))
#     lines.append(("__section__", "~/reach"))
#     for k, v in cfg["reach"].items():
#         lines.append((k, v))

#     line_h = 21
#     label_col_w = 100
#     text_elems = []
#     ty = content_y + 8
#     for kind, val in lines:
#         if kind == "__gap__":
#             ty += line_h * 0.5
#             continue
#         if kind == "__section__":
#             text_elems.append(
#                 f'<text x="{text_x}" y="{ty}" fill="{colors["accent2"]}" '
#                 f'font-family="{FONT}" font-size="13" font-weight="600">{esc(val)}</text>'
#             )
#             ty += line_h
#             continue
#         if kind == "__raw__":
#             text_elems.append(
#                 f'<text x="{text_x}" y="{ty}" fill="{colors["title"]}" '
#                 f'font-family="{FONT}" font-size="16" font-weight="700">{esc(val)}</text>'
#             )
#             ty += line_h + 6
#             continue
#         label, value = kind, val
#         text_elems.append(
#             f'<text x="{text_x}" y="{ty}" fill="{colors["dim"]}" '
#             f'font-family="{FONT}" font-size="12.5">{esc(label)}</text>'
#         )
#         text_elems.append(
#             f'<text x="{text_x + label_col_w}" y="{ty}" fill="{colors["text"]}" '
#             f'font-family="{FONT}" font-size="12.5">{esc(value)}</text>'
#         )
#         ty += line_h

#     panel_content_h = max(art_h, ty - content_y) + 40
#     panel_h = top_bar_h + panel_content_h

#     stats_gap = 24
#     stats_h = 110
#     total_h = panel_h + stats_gap + stats_h + 10

#     now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")

#     def stat_box(cx, value, label, sub, ring_color=None):
#         w = 270
#         h = stats_h
#         parts = [
#             f'<rect x="{cx}" y="{panel_h + stats_gap}" width="{w}" height="{h}" rx="10" '
#             f'fill="{colors["panel"]}" stroke="{colors["border"]}"/>',
#             f'<text x="{cx + w/2}" y="{panel_h + stats_gap + 46}" text-anchor="middle" '
#             f'fill="{ring_color or colors["title"]}" font-family="{FONT}" '
#             f'font-size="26" font-weight="700">{value}</text>',
#             f'<text x="{cx + w/2}" y="{panel_h + stats_gap + 68}" text-anchor="middle" '
#             f'fill="{colors["dim"]}" font-family="{FONT}" font-size="11">{esc(label)}</text>',
#             f'<text x="{cx + w/2}" y="{panel_h + stats_gap + 88}" text-anchor="middle" '
#             f'fill="{colors["dim"]}" font-family="{FONT}" font-size="10">{esc(sub)}</text>',
#         ]
#         return "".join(parts)

#     box_gap = 20
#     box_w = 270
#     start_x = (PANEL_W - (box_w * 3 + box_gap * 2)) / 2
#     stats_svg = (
#         stat_box(start_x, stats["total"], "Total Contributions",
#                   f"Oct 2024 - Present", colors["accent2"])
#         + stat_box(start_x + box_w + box_gap, stats["current_streak"],
#                     "Current Streak", stats["current_range"], colors["warn"])
#         + stat_box(start_x + (box_w + box_gap) * 2, stats["longest_streak"],
#                     "Longest Streak", stats["longest_range"], colors["accent"])
#     )

#     svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{PANEL_W}" height="{total_h}" viewBox="0 0 {PANEL_W} {total_h}">
#   <rect width="{PANEL_W}" height="{total_h}" fill="{colors["bg"]}"/>
#   <rect x="0" y="0" width="{PANEL_W}" height="{panel_h}" rx="12" fill="{colors["panel"]}" stroke="{colors["border"]}"/>
#   <rect x="0" y="0" width="{PANEL_W}" height="{top_bar_h}" rx="12" fill="{colors["panel"]}"/>
#   <circle cx="20" cy="{top_bar_h/2}" r="6" fill="#ff5f56"/>
#   <circle cx="40" cy="{top_bar_h/2}" r="6" fill="#ffbd2e"/>
#   <circle cx="60" cy="{top_bar_h/2}" r="6" fill="#27c93f"/>
#   <text x="{PANEL_W/2}" y="{top_bar_h/2 + 4}" text-anchor="middle" fill="{colors["dim"]}"
#         font-family="{FONT}" font-size="12">{esc(cfg["github_username"])} - zsh - 90x26</text>

#   <text x="{art_x}" y="{content_y - 6}" fill="{colors["accent"]}" font-family="{FONT}" font-size="13">
#     &#8594;  ~ neofetch --profile
#   </text>

#   <g transform="translate(0,{content_y})">
#     {build_pixel_art(grid, art_x, 8)}
#   </g>
#   {"".join(text_elems)}

#   <text x="{art_x}" y="{panel_h - 14}" fill="{colors["accent"]}" font-family="{FONT}" font-size="12">
#     &#8594;  ~ {esc(cfg["role"])}
#   </text>
#   <text x="{PANEL_W - 24}" y="{panel_h - 14}" text-anchor="end" fill="{colors["dim"]}"
#         font-family="{FONT}" font-size="11">Last updated {esc(now)}</text>

#   {stats_svg}
# </svg>'''
#     return svg


# # ---------- readme injection ----------

# def update_readme(username):
#     block = (
#         f"{START_MARKER}\n"
#         f"<picture>\n"
#         f'  <source media="(prefers-color-scheme: dark)" srcset="dark.svg">\n'
#         f'  <source media="(prefers-color-scheme: light)" srcset="light.svg">\n'
#         f'  <img alt="{username} profile" src="dark.svg">\n'
#         f"</picture>\n"
#         f"{END_MARKER}"
#     )
#     try:
#         with open(README_FILE) as f:
#             content = f.read()
#     except FileNotFoundError:
#         content = f"{START_MARKER}\n{END_MARKER}\n"

#     if START_MARKER in content and END_MARKER in content:
#         pre = content.split(START_MARKER)[0]
#         post = content.split(END_MARKER)[1]
#         content = pre + block + post
#     else:
#         content = content.rstrip() + "\n\n" + block + "\n"

#     with open(README_FILE, "w") as f:
#         f.write(content)


# def main():
#     cfg = load_config()
#     grid = load_portrait()
#     stats = fetch_contribution_stats(cfg["github_username"])

#     for theme in ("dark", "light"):
#         svg = build_svg(cfg, grid, stats, theme=theme)
#         with open(f"{theme}.svg", "w") as f:
#             f.write(svg)

#     update_readme(cfg["github_username"])
#     print("Generated dark.svg, light.svg and updated README.md")
#     print(f"Stats: {stats}")


# if __name__ == "__main__":
#     main()

"""
generate_profile.py
--------------------
Builds a neofetch-style terminal SVG (dark.svg + light.svg) using:
  - config.json      -> personal info, stack, projects, links
  - portrait.txt      -> pixel-color grid (from photo_to_ascii.py)
  - GitHub public API -> total contributions + current/longest streak

Then injects <picture> markup into README.md between:
  <!--START_SECTION:profile--> ... <!--END_SECTION:profile-->

Usage:
    python generate_profile.py
"""

import json
import datetime
import urllib.request

CONFIG_FILE = "config.json"
PORTRAIT_FILE = "portrait.txt"
README_FILE = "README.md"
START_MARKER = "<!--START_SECTION:profile-->"
END_MARKER = "<!--END_SECTION:profile-->"

CELL = 4          # px size of each pixel-art cell
PANEL_W = 900
FONT = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"


# ---------- data loading ----------

def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_portrait():
    with open(PORTRAIT_FILE, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return [line.split(",") for line in lines]


def fetch_contribution_stats(username):
    """Uses the free github-contributions-api (no auth needed) to get a
    daily contribution list, then derives total / current / longest streak."""
    url = f"https://github-contributions-api.jogruber.de/v4/{username}?y=all"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        days = data.get("contributions", [])
        days.sort(key=lambda d: d["date"])
    except Exception as e:
        print(f"warning: could not fetch contribution stats ({e}); using zeros")
        return {"total": 0, "current_streak": 0, "current_range": "-",
                "longest_streak": 0, "longest_range": "-"}

    total = sum(d["count"] for d in days)

    # current streak: walk back from today/most recent day
    today = datetime.date.today()
    by_date = {d["date"]: d["count"] for d in days}
    cur_streak = 0
    cur_end = None
    cursor = today
    while True:
        key = cursor.isoformat()
        if by_date.get(key, 0) > 0:
            if cur_end is None:
                cur_end = cursor
            cur_streak += 1
            cursor -= datetime.timedelta(days=1)
        else:
            if cursor == today:
                # today has no contribution yet; check yesterday onward
                cursor -= datetime.timedelta(days=1)
                today = cursor  # shift window start
                continue
            break
    cur_start = cursor + datetime.timedelta(days=1) if cur_streak else None

    # longest streak
    longest = 0
    longest_start = longest_end = None
    run = 0
    run_start = None
    for d in days:
        if d["count"] > 0:
            if run == 0:
                run_start = d["date"]
            run += 1
            if run > longest:
                longest = run
                longest_start = run_start
                longest_end = d["date"]
        else:
            run = 0

    def fmt(d):
        if isinstance(d, str):
            d = datetime.date.fromisoformat(d)
        return d.strftime("%b %d")

    return {
        "total": total,
        "current_streak": cur_streak,
        "current_range": f"{fmt(cur_start)} - {fmt(cur_end)}" if cur_streak else "-",
        "longest_streak": longest,
        "longest_range": f"{fmt(longest_start)} - {fmt(longest_end)}" if longest else "-",
    }


# ---------- svg building ----------

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_pixel_art(grid, x, y):
    """Returns list of <rect> strings for the portrait grid at offset x,y."""
    out = []
    for ry, row in enumerate(grid):
        for rx, color in enumerate(row):
            out.append(
                f'<rect x="{x + rx * CELL}" y="{y + ry * CELL}" '
                f'width="{CELL}" height="{CELL}" fill="{color}"/>'
            )
    return "".join(out)


def build_svg(cfg, grid, stats, theme="dark"):
    colors = {
        "dark": dict(bg="#0d1117", panel="#161b22", border="#30363d",
                     text="#c9d1d9", dim="#8b949e", accent="#7ee787",
                     accent2="#58a6ff", warn="#f0883e", title="#e6edf3"),
        "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de",
                      text="#24292f", dim="#57606a", accent="#116329",
                      accent2="#0969da", warn="#9a6700", title="#1f2328"),
    }[theme]

    grid_h = len(grid)
    grid_w = len(grid[0]) if grid_h else 0
    art_w = grid_w * CELL
    art_h = grid_h * CELL

    top_bar_h = 34
    content_y = top_bar_h + 30
    art_x = 24
    text_x = art_x + art_w + 40

    lines = []  # (label, value) or ("__section__", title) or ("__raw__", text)
    lines.append(("__raw__", f'{cfg["name"]}'))
    lines.append(("__gap__", ""))
    lines.append(("Role", cfg["role"]))
    lines.append(("Edu", cfg["edu"]))
    lines.append(("Focus", cfg["focus"]))
    lines.append(("__gap__", ""))
    lines.append(("__section__", "~/stack"))
    for k, v in cfg["stack"].items():
        lines.append((k, v))
    lines.append(("__gap__", ""))
    lines.append(("__section__", "~/projects"))
    for k, v in cfg["projects"].items():
        lines.append((k, v))
    lines.append(("__gap__", ""))
    lines.append(("__section__", "~/highlights"))
    for k, v in cfg["highlights"].items():
        lines.append((k, v))
    lines.append(("__gap__", ""))
    lines.append(("__section__", "~/reach"))
    for k, v in cfg["reach"].items():
        lines.append((k, v))

    line_h = 21
    label_col_w = 155
    text_elems = []
    ty = content_y + 8
    for kind, val in lines:
        if kind == "__gap__":
            ty += line_h * 0.5
            continue
        if kind == "__section__":
            text_elems.append(
                f'<text x="{text_x}" y="{ty}" fill="{colors["accent2"]}" '
                f'font-family="{FONT}" font-size="13" font-weight="600">{esc(val)}</text>'
            )
            ty += line_h
            continue
        if kind == "__raw__":
            text_elems.append(
                f'<text x="{text_x}" y="{ty}" fill="{colors["title"]}" '
                f'font-family="{FONT}" font-size="16" font-weight="700">{esc(val)}</text>'
            )
            ty += line_h + 6
            continue
        label, value = kind, val
        text_elems.append(
            f'<text x="{text_x}" y="{ty}" fill="{colors["dim"]}" '
            f'font-family="{FONT}" font-size="12.5">{esc(label)}</text>'
        )
        text_elems.append(
            f'<text x="{text_x + label_col_w}" y="{ty}" fill="{colors["text"]}" '
            f'font-family="{FONT}" font-size="12.5">{esc(value)}</text>'
        )
        ty += line_h

    panel_content_h = max(art_h, ty - content_y) + 40
    panel_h = top_bar_h + panel_content_h

    stats_gap = 24
    stats_h = 110
    total_h = panel_h + stats_gap + stats_h + 10

    now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")

    def stat_box(cx, value, label, sub, ring_color=None):
        w = 270
        h = stats_h
        parts = [
            f'<rect x="{cx}" y="{panel_h + stats_gap}" width="{w}" height="{h}" rx="10" '
            f'fill="{colors["panel"]}" stroke="{colors["border"]}"/>',
            f'<text x="{cx + w/2}" y="{panel_h + stats_gap + 46}" text-anchor="middle" '
            f'fill="{ring_color or colors["title"]}" font-family="{FONT}" '
            f'font-size="26" font-weight="700">{value}</text>',
            f'<text x="{cx + w/2}" y="{panel_h + stats_gap + 68}" text-anchor="middle" '
            f'fill="{colors["dim"]}" font-family="{FONT}" font-size="11">{esc(label)}</text>',
            f'<text x="{cx + w/2}" y="{panel_h + stats_gap + 88}" text-anchor="middle" '
            f'fill="{colors["dim"]}" font-family="{FONT}" font-size="10">{esc(sub)}</text>',
        ]
        return "".join(parts)

    box_gap = 20
    box_w = 270
    start_x = (PANEL_W - (box_w * 3 + box_gap * 2)) / 2
    stats_svg = (
        stat_box(start_x, stats["total"], "Total Contributions",
                  f"Oct 2024 - Present", colors["accent2"])
        + stat_box(start_x + box_w + box_gap, stats["current_streak"],
                    "Current Streak", stats["current_range"], colors["warn"])
        + stat_box(start_x + (box_w + box_gap) * 2, stats["longest_streak"],
                    "Longest Streak", stats["longest_range"], colors["accent"])
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{PANEL_W}" height="{total_h}" viewBox="0 0 {PANEL_W} {total_h}">
  <rect width="{PANEL_W}" height="{total_h}" fill="{colors["bg"]}"/>
  <rect x="0" y="0" width="{PANEL_W}" height="{panel_h}" rx="12" fill="{colors["panel"]}" stroke="{colors["border"]}"/>
  <rect x="0" y="0" width="{PANEL_W}" height="{top_bar_h}" rx="12" fill="{colors["panel"]}"/>
  <circle cx="20" cy="{top_bar_h/2}" r="6" fill="#ff5f56"/>
  <circle cx="40" cy="{top_bar_h/2}" r="6" fill="#ffbd2e"/>
  <circle cx="60" cy="{top_bar_h/2}" r="6" fill="#27c93f"/>
  <text x="{PANEL_W/2}" y="{top_bar_h/2 + 4}" text-anchor="middle" fill="{colors["dim"]}"
        font-family="{FONT}" font-size="12">{esc(cfg["github_username"])} - zsh - 90x26</text>

  <text x="{art_x}" y="{content_y - 6}" fill="{colors["accent"]}" font-family="{FONT}" font-size="13">
    &#8594;  ~ neofetch --profile
  </text>

  <g transform="translate(0,{content_y})">
    {build_pixel_art(grid, art_x, 8)}
  </g>
  {"".join(text_elems)}

  <text x="{art_x}" y="{panel_h - 14}" fill="{colors["accent"]}" font-family="{FONT}" font-size="12">
    &#8594;  ~ {esc(cfg["role"])}
  </text>
  <text x="{PANEL_W - 24}" y="{panel_h - 14}" text-anchor="end" fill="{colors["dim"]}"
        font-family="{FONT}" font-size="11">Last updated {esc(now)}</text>

  {stats_svg}
</svg>'''
    return svg


# ---------- readme injection ----------

def update_readme(username):
    block = (
        f"{START_MARKER}\n"
        f"<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="dark.svg">\n'
        f'  <source media="(prefers-color-scheme: light)" srcset="light.svg">\n'
        f'  <img alt="{username} profile" src="dark.svg">\n'
        f"</picture>\n"
        f"{END_MARKER}"
    )
    try:
        with open(README_FILE, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = f"{START_MARKER}\n{END_MARKER}\n"

    if START_MARKER in content and END_MARKER in content:
        pre = content.split(START_MARKER)[0]
        post = content.split(END_MARKER)[1]
        content = pre + block + post
    else:
        content = content.rstrip() + "\n\n" + block + "\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    cfg = load_config()
    grid = load_portrait()
    stats = fetch_contribution_stats(cfg["github_username"])

    for theme in ("dark", "light"):
        svg = build_svg(cfg, grid, stats, theme=theme)
        with open(f"{theme}.svg", "w", encoding="utf-8") as f:
            f.write(svg)

    update_readme(cfg["github_username"])
    print("Generated dark.svg, light.svg and updated README.md")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()