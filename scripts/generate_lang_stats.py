import os
import json
import urllib.request
import urllib.error
from collections import defaultdict

# PAT_1 우선 사용 (비공개 레포 접근), 없으면 GITHUB_TOKEN fallback
GITHUB_TOKEN = os.environ.get("PAT_1") or os.environ.get("GITHUB_TOKEN", "")
USERNAME = "H-J52"

LANG_COLORS = {
    "C#": "#9b4993",
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

# calm_pink 테마 컬러
BG_COLOR      = "#1d1f33"
BORDER_COLOR  = "#2d3150"
TITLE_COLOR   = "#f882a1"
TEXT_COLOR    = "#cdd6f4"
SUBTEXT_COLOR = "#a4b1cd"
BAR_BG_COLOR  = "#2d3150"


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
    # PAT_1이 있으면 /user/repos (비공개 포함), 없으면 /users/{name}/repos (공개만)
    if os.environ.get("PAT_1"):
        base = "https://api.github.com/user/repos?affiliation=owner&per_page=100&page="
    else:
        base = f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page="

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
        full_name = repo["full_name"]
        try:
            langs = github_request(f"https://api.github.com/repos/{full_name}/languages")
            for lang, bytes_count in langs.items():
                totals[lang] += bytes_count
        except urllib.error.HTTPError:
            continue
    return totals


def make_svg(top_langs):
    total = sum(v for _, v in top_langs)
    if total == 0:
        return ""

    card_w  = 320
    pad     = 25
    inner_w = card_w - pad * 2
    row_h   = 40
    title_h = 55
    bar_section_h = 22
    card_h  = title_h + bar_section_h + len(top_langs) * row_h + pad

    # 상단 색상 바 세그먼트
    bar_y = title_h
    bar_w = inner_w
    bar_segs = []
    x = pad
    # 첫/마지막 rounded 처리용
    for i, (lang, count) in enumerate(top_langs):
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        w = max(round((count / total) * bar_w, 2), 2)
        rx = "3" if i == 0 else ("3" if i == len(top_langs) - 1 else "0")
        bar_segs.append(
            f'<rect x="{x}" y="{bar_y}" width="{w}" height="8" fill="{color}" rx="{rx}"/>'
        )
        x += w

    # 언어별 행 (이름 + 개별 비율바 + 퍼센트)
    rows = []
    ry = title_h + bar_section_h + 8
    for lang, count in top_langs:
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        pct = round((count / total) * 100, 1)
        bar_fill_w = round((pct / 100) * inner_w, 2)

        rows.append(
            # 언어 이름 (dot + text)
            f'<circle cx="{pad + 5}" cy="{ry + 7}" r="5" fill="{color}"/>'
            f'<text x="{pad + 16}" y="{ry + 12}" fill="{TEXT_COLOR}" '
            f'font-size="12" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-weight="600">'
            f'{lang}</text>'
            # 퍼센트 텍스트 (우측)
            f'<text x="{card_w - pad}" y="{ry + 12}" fill="{SUBTEXT_COLOR}" '
            f'font-size="11" font-family="Segoe UI,Helvetica,Arial,sans-serif" text-anchor="end">'
            f'{pct}%</text>'
            # 배경 바
            f'<rect x="{pad}" y="{ry + 18}" width="{inner_w}" height="5" fill="{BAR_BG_COLOR}" rx="3"/>'
            # 채워진 바
            f'<rect x="{pad}" y="{ry + 18}" width="{bar_fill_w}" height="5" fill="{color}" rx="3"/>'
        )
        ry += row_h

    # 타이틀 아이콘 (간단한 코드 아이콘 모양)
    icon = (
        f'<polyline points="{pad},{28} {pad+6},{33} {pad},{38}" '
        f'stroke="{TITLE_COLOR}" stroke-width="2" fill="none" stroke-linecap="round"/>'
        f'<polyline points="{pad+14},{28} {pad+8},{33} {pad+14},{38}" '
        f'stroke="{TITLE_COLOR}" stroke-width="2" fill="none" stroke-linecap="round"/>'
    )

    svg = f'''<svg width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}"
  xmlns="http://www.w3.org/2000/svg">
  <style>
    .fade {{ animation: fadeIn 0.4s ease-in-out forwards; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
  </style>

  <!-- 카드 배경 + 테두리 -->
  <rect width="{card_w}" height="{card_h}" rx="10" fill="{BG_COLOR}"
    stroke="{BORDER_COLOR}" stroke-width="1"/>

  <!-- 타이틀 -->
  {icon}
  <text x="{pad + 20}" y="37" fill="{TITLE_COLOR}"
    font-size="14" font-weight="bold"
    font-family="Segoe UI,Helvetica,Arial,sans-serif">Most Used Languages</text>

  <!-- 구분선 -->
  <line x1="{pad}" y1="{title_h - 6}" x2="{card_w - pad}" y2="{title_h - 6}"
    stroke="{BORDER_COLOR}" stroke-width="1"/>

  <!-- 상단 색상 바 -->
  {''.join(bar_segs)}

  <!-- 언어 행 -->
  <g class="fade">
  {''.join(rows)}
  </g>
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
