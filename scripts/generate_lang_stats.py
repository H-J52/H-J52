import os
import json
import urllib.request
import urllib.error
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "H-J52"

LANG_COLORS = {
    "C#": "#178600",
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Swift": "#ffac45",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "PHP": "#4F5D95",
    "Lua": "#000080",
    "GDScript": "#355570",
    "HLSL": "#aace60",
    "ShaderLab": "#222c37",
}
DEFAULT_COLOR = "#858585"


def github_request(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("User-Agent", "lang-stats-bot")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_all_repos():
    repos = []
    page = 1
    while True:
        data = github_request(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&type=owner"
        )
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_lang_totals(repos):
    totals = defaultdict(int)
    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo["name"]
        try:
            langs = github_request(
                f"https://api.github.com/repos/{USERNAME}/{name}/languages"
            )
            for lang, bytes_count in langs.items():
                totals[lang] += bytes_count
        except urllib.error.HTTPError:
            continue
    return totals


def make_svg(top_langs):
    total = sum(v for _, v in top_langs)
    if total == 0:
        return ""

    card_w = 340
    bar_h = 10
    bar_y = 130
    pad = 24
    row_h = 28

    legend_h = len(top_langs) * row_h + 16
    card_h = bar_y + bar_h + 20 + legend_h + pad

    # build bar segments
    bar_segments = []
    x = pad
    bar_w = card_w - pad * 2
    for lang, count in top_langs:
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        w = round((count / total) * bar_w, 2)
        if w < 1:
            w = 1
        bar_segments.append(f'<rect x="{x}" y="{bar_y}" width="{w}" height="{bar_h}" fill="{color}" rx="2"/>')
        x += w

    # build legend rows
    legend_items = []
    ly = bar_y + bar_h + 24
    for lang, count in top_langs:
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        pct = round((count / total) * 100, 1)
        legend_items.append(
            f'<circle cx="{pad + 6}" cy="{ly + 1}" r="6" fill="{color}"/>'
            f'<text x="{pad + 18}" y="{ly + 5}" fill="#cdd6f4" font-size="13" font-family="Segoe UI,sans-serif">'
            f'{lang}</text>'
            f'<text x="{card_w - pad}" y="{ly + 5}" fill="#a6adc8" font-size="12" font-family="Segoe UI,sans-serif" '
            f'text-anchor="end">{pct}%</text>'
        )
        ly += row_h

    svg = f'''<svg width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}"
  xmlns="http://www.w3.org/2000/svg">
  <rect width="{card_w}" height="{card_h}" rx="12" fill="#2b2d3f"/>
  <text x="{pad}" y="36" fill="#cdd6f4" font-size="15" font-weight="bold"
    font-family="Segoe UI,sans-serif">Most Used Languages</text>
  <line x1="{pad}" y1="48" x2="{card_w - pad}" y2="48" stroke="#414356" stroke-width="1"/>
  <rect x="{pad}" y="60" width="{card_w - pad * 2}" height="{bar_h + 56}" rx="8" fill="#1e1e2e"/>
  <text x="{pad + 12}" y="88" fill="#a6adc8" font-size="11" font-family="Segoe UI,sans-serif">Language Breakdown</text>
  {''.join(bar_segments)}
  {''.join(legend_items)}
</svg>'''
    return svg


def main():
    print("Fetching repos...")
    repos = get_all_repos()
    print(f"Found {len(repos)} repos")

    print("Fetching language data...")
    totals = get_lang_totals(repos)

    if not totals:
        print("No language data found.")
        return

    top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:6]
    print("Top languages:", [(k, v) for k, v in top])

    svg = make_svg(top)

    out_path = os.path.join(os.path.dirname(__file__), "..", "lang-stats.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG written to {out_path}")


if __name__ == "__main__":
    main()
