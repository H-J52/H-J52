import os
import json
import urllib.request
import urllib.error
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("PAT_1") or os.environ.get("GITHUB_TOKEN", "")
USERNAME = "H-J52"

LANG_COLORS = {
    "C#":          "#9b4993",
    "Python":      "#3572A5",
    "JavaScript":  "#f1e05a",
    "TypeScript":  "#2b7489",
    "Java":        "#b07219",
    "C++":         "#f34b7d",
    "C":           "#555555",
    "HTML":        "#e34c26",
    "CSS":         "#563d7c",
    "Shell":       "#89e051",
    "Go":          "#00ADD8",
    "Rust":        "#dea584",
    "Ruby":        "#701516",
    "Swift":       "#ffac45",
    "Kotlin":      "#A97BFF",
    "Dart":        "#00B4AB",
    "PHP":         "#4F5D95",
    "Lua":         "#000080",
    "GDScript":    "#355570",
    "HLSL":        "#aace60",
    "ShaderLab":   "#8c2c7e",
}
DEFAULT_COLOR = "#858585"

BG_COLOR     = "#0d0f1a"
BORDER_COLOR = "#f882a1"
TITLE_COLOR  = "#f882a1"
VALUE_COLOR  = "#ffe066"
TEXT_COLOR   = "#cdd6f4"
TRACK_COLOR  = "#1e2035"
FONT         = "Courier New, Courier, monospace"


def github_request(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("User-Agent", "lang-stats-bot")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_all_repos():
    repos, page = [], 1
    base = (
        "https://api.github.com/user/repos?affiliation=owner&per_page=100&page="
        if os.environ.get("PAT_1")
        else f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page="
    )
    while True:
        data = github_request(f"{base}{page}")
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
        try:
            langs = github_request(
                f"https://api.github.com/repos/{repo['full_name']}/languages"
            )
            for lang, b in langs.items():
                totals[lang] += b
        except urllib.error.HTTPError:
            continue
    return totals


def make_svg(top_langs):
    total = sum(v for _, v in top_langs)
    if total == 0:
        return ""

    card_w  = 320
    pad     = 20
    inner_w = card_w - pad * 2
    title_h = 52
    row_h   = 44
    card_h  = title_h + len(top_langs) * row_h + pad + 4

    # 언어 행 생성
    rows = []
    for i, (lang, count) in enumerate(top_langs):
        color   = LANG_COLORS.get(lang, DEFAULT_COLOR)
        pct     = round((count / total) * 100, 1)
        fill_w  = max(round((pct / 100) * inner_w), 4)
        ry      = title_h + i * row_h

        # 순위 뱃지
        rank_x = pad
        rows.append(
            # 언어 이름 + 퍼센트
            f'<text x="{rank_x}" y="{ry + 14}" fill="{color}" '
            f'font-size="12" font-weight="bold" font-family="{FONT}">▶ {lang}</text>'
            f'<text x="{card_w - pad}" y="{ry + 14}" fill="{VALUE_COLOR}" '
            f'font-size="12" font-family="{FONT}" text-anchor="end">{pct}%</text>'
            # 트랙 (배경)
            f'<rect x="{pad}" y="{ry + 20}" width="{inner_w}" height="6" '
            f'fill="{TRACK_COLOR}" rx="3"/>'
            # 채워진 바
            f'<rect x="{pad}" y="{ry + 20}" width="{fill_w}" height="6" '
            f'fill="{color}" rx="3"/>'
        )

    # 코너 장식
    cs = 6  # corner size
    corners = (
        f'<rect x="0"            y="0"            width="{cs}" height="{cs}" fill="{BORDER_COLOR}"/>'
        f'<rect x="{card_w-cs}"  y="0"            width="{cs}" height="{cs}" fill="{BORDER_COLOR}"/>'
        f'<rect x="0"            y="{card_h-cs}"  width="{cs}" height="{cs}" fill="{BORDER_COLOR}"/>'
        f'<rect x="{card_w-cs}"  y="{card_h-cs}"  width="{cs}" height="{cs}" fill="{BORDER_COLOR}"/>'
    )

    svg = f'''<svg width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}"
  xmlns="http://www.w3.org/2000/svg">

  <!-- 배경 + 테두리 -->
  <rect width="{card_w}" height="{card_h}" rx="6" fill="{BG_COLOR}"
    stroke="{BORDER_COLOR}" stroke-width="1" stroke-opacity="0.7"/>
  {corners}

  <!-- 타이틀 -->
  <text x="{pad}" y="22" fill="{TITLE_COLOR}" font-size="13" font-weight="bold"
    font-family="{FONT}">◈ SKILL MASTERY</text>
  <text x="{card_w - pad}" y="22" fill="{TITLE_COLOR}" font-size="11"
    font-family="{FONT}" text-anchor="end">[ {USERNAME} ]</text>

  <!-- 구분선 -->
  <line x1="{pad}" y1="34" x2="{card_w - pad}" y2="34"
    stroke="{BORDER_COLOR}" stroke-width="1" stroke-opacity="0.4"
    stroke-dasharray="4,3"/>

  <!-- 언어 행 -->
  {''.join(rows)}
</svg>'''
    return svg


def main():
    print("Fetching repos...")
    repos = get_all_repos()
    print(f"Found {len(repos)} repos (private included: {bool(os.environ.get('PAT_1'))})")

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
