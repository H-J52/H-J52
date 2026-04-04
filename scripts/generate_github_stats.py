import os
import json
import urllib.request
import urllib.error
import urllib.parse

GITHUB_TOKEN = os.environ.get("PAT_1") or os.environ.get("GITHUB_TOKEN", "")
USERNAME     = "H-J52"

BG_COLOR     = "#0d0f1a"
BORDER_COLOR = "#f882a1"
TITLE_COLOR  = "#f882a1"
VALUE_COLOR  = "#ffe066"
LABEL_COLOR  = "#a4b1cd"
DOT_COLOR    = "#2a2d45"
FONT         = "Courier New, Courier, monospace"


def github_request(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("User-Agent", "github-stats-bot")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_stars_and_repos():
    stars, count, page = 0, 0, 1
    base = (
        "https://api.github.com/user/repos?affiliation=owner&per_page=100&page="
        if os.environ.get("PAT_1")
        else f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page="
    )
    while True:
        data = github_request(f"{base}{page}")
        if not data:
            break
        for r in data:
            if not r.get("fork"):
                stars += r.get("stargazers_count", 0)
                count += 1
        if len(data) < 100:
            break
        page += 1
    return stars, count


def search_count(query):
    q = urllib.parse.quote(query)
    data = github_request(f"https://api.github.com/search/commits?q={q}&per_page=1")
    return data.get("total_count", 0)


def search_issues_count(query):
    q = urllib.parse.quote(query)
    data = github_request(f"https://api.github.com/search/issues?q={q}&per_page=1")
    return data.get("total_count", 0)


def dot_fill(label_len, value_len, total=28):
    """라벨과 숫자 사이 점 채우기"""
    dots = total - label_len - value_len
    return "." * max(dots, 3)


def make_svg(stars, repos, commits, prs, issues):
    card_w  = 320
    pad     = 20
    inner_w = card_w - pad * 2
    title_h = 52
    row_h   = 36
    footer_h = 24

    # 스탯 항목: (아이콘, 게임라벨, 값)
    stats = [
        ("⚔", "COMMITS",  f"{commits:,}"),
        ("★", "STARS",    f"{stars:,}"),
        ("⊕", "PULL REQ", f"{prs:,}"),
        ("◎", "ISSUES",   f"{issues:,}"),
        ("▣", "REPOS",    f"{repos:,}"),
    ]

    card_h = title_h + len(stats) * row_h + footer_h + pad

    rows = []
    for i, (icon, label, value) in enumerate(stats):
        ry = title_h + i * row_h + 16

        # 점 개수 계산 (고정폭 폰트 기준 맞춤)
        pad_dots = "·" * max(1, 22 - len(label) - len(value))

        rows.append(
            # 아이콘
            f'<text x="{pad}" y="{ry}" fill="{TITLE_COLOR}" '
            f'font-size="13" font-family="{FONT}">{icon}</text>'
            # 라벨
            f'<text x="{pad + 20}" y="{ry}" fill="{LABEL_COLOR}" '
            f'font-size="12" font-family="{FONT}">{label}</text>'
            # 점선
            f'<text x="{pad + 20 + len(label) * 8 + 6}" y="{ry}" fill="{DOT_COLOR}" '
            f'font-size="12" font-family="{FONT}">{pad_dots}</text>'
            # 값 (우측 정렬)
            f'<text x="{card_w - pad}" y="{ry}" fill="{VALUE_COLOR}" '
            f'font-size="13" font-weight="bold" font-family="{FONT}" text-anchor="end">{value}</text>'
            # 하단 구분선
            f'<line x1="{pad}" y1="{ry + 10}" x2="{card_w - pad}" y2="{ry + 10}" '
            f'stroke="{BORDER_COLOR}" stroke-width="0.4" stroke-opacity="0.2"/>'
        )

    # 하단 합계 라인
    total_commits_label = f"TOTAL CODE COMMITS : {commits:,}"
    footer_y = title_h + len(stats) * row_h + 16

    # 코너 장식
    cs = 6
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
    font-family="{FONT}">◈ PLAYER STATUS</text>
  <text x="{card_w - pad}" y="22" fill="{TITLE_COLOR}" font-size="11"
    font-family="{FONT}" text-anchor="end">[ {USERNAME} ]</text>

  <!-- 구분선 -->
  <line x1="{pad}" y1="34" x2="{card_w - pad}" y2="34"
    stroke="{BORDER_COLOR}" stroke-width="1" stroke-opacity="0.4"
    stroke-dasharray="4,3"/>

  <!-- 스탯 행 -->
  {''.join(rows)}

  <!-- 하단 구분선 -->
  <line x1="{pad}" y1="{footer_y - 10}" x2="{card_w - pad}" y2="{footer_y - 10}"
    stroke="{BORDER_COLOR}" stroke-width="1" stroke-opacity="0.4"
    stroke-dasharray="4,3"/>

  <!-- 하단 요약 -->
  <text x="{card_w // 2}" y="{footer_y + 6}" fill="{LABEL_COLOR}" font-size="10"
    font-family="{FONT}" text-anchor="middle">★ {USERNAME}'s GitHub Adventure ★</text>
</svg>'''
    return svg


def main():
    print("Fetching stars and repo count...")
    stars, repos = get_stars_and_repos()

    print("Fetching commit count...")
    commits = search_count(f"author:{USERNAME}")

    print("Fetching PR count...")
    prs = search_issues_count(f"author:{USERNAME} type:pr")

    print("Fetching issue count...")
    issues = search_issues_count(f"author:{USERNAME} type:issue")

    print(f"Stars={stars}, Repos={repos}, Commits={commits}, PRs={prs}, Issues={issues}")

    svg = make_svg(stars, repos, commits, prs, issues)

    out_path = os.path.join(os.path.dirname(__file__), "..", "github-stats.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG written to {out_path}")


if __name__ == "__main__":
    main()
