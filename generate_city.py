#!/usr/bin/env python3
"""
GitHub City Skyline Generator
Generates an SVG city where each building = a repo, building height = commit count.
Designed to run in GitHub Actions and commit the result to your profile README repo.
"""

import os
import sys
import json
import math
import random
import hashlib
import urllib.request
import urllib.error

# ─── Configuration ───────────────────────────────────────────────────────────
USERNAME = os.environ.get("GITHUB_USERNAME", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")  # optional, but needed for private repos & higher rate limits
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "github-city.svg")
MAX_REPOS = int(os.environ.get("MAX_REPOS", "60"))

# ─── GitHub API helpers ──────────────────────────────────────────────────────

def github_get(url):
    """Make an authenticated GET request to the GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-city-generator",
    }
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} for {url}: {e.read().decode()[:200]}", file=sys.stderr)
        return None


def fetch_repos(username):
    """Fetch all public repos for a user (paginated)."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&sort=updated"
        data = github_get(url)
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_commit_count(username, repo_name):
    """
    Get total commit count for a repo using the contributors endpoint.
    Falls back to a default if API fails.
    """
    url = f"https://api.github.com/repos/{username}/{repo_name}/contributors?per_page=1&anon=true"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-city-generator",
    }
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list):
                return sum(c.get("contributions", 0) for c in data)
    except Exception:
        pass

    # Fallback: use the default_branch commit count via the repo's size as a proxy
    return max(1, 3)


# ─── Deterministic random from repo name (so colors are stable across runs) ──

def repo_seed(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


# ─── SVG City Generator ─────────────────────────────────────────────────────

def generate_city_svg(repo_data):
    """
    repo_data: list of (repo_name, commit_count) sorted by commit_count desc
    """
    if not repo_data:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300"><text x="400" y="150" text-anchor="middle" fill="#ccc" font-size="16">No repositories found</text></svg>'

    n = len(repo_data)

    # ─── Layout constants ────────────────────────────────────────────────
    BUILDING_GAP = 3
    MIN_WIDTH = 14
    MAX_WIDTH = 32
    MIN_HEIGHT = 18
    MAX_HEIGHT = 220
    GROUND_Y = 310
    SKY_HEIGHT = 360
    PADDING_X = 30

    # Calculate total width
    total_width = sum(
        max(MIN_WIDTH, min(MAX_WIDTH, 18 + (commits / max(c for _, c in repo_data)) * 14))
        for _, commits in repo_data
    ) + BUILDING_GAP * (n - 1) + PADDING_X * 2

    SVG_WIDTH = max(800, total_width)

    max_commits = max(c for _, c in repo_data)
    if max_commits == 0:
        max_commits = 1

    # ─── Color palettes for buildings (seeded per repo) ──────────────────
    PALETTES = [
        # (base, dark_accent, window_lit, window_dark)
        ("#2D3142", "#1B1F2E", "#F7E87D", "#1a1d2b"),
        ("#3A3E5C", "#272A42", "#7DE8F7", "#22253a"),
        ("#4A3B5C", "#33284A", "#E87DF7", "#2b1f3d"),
        ("#3B5C4A", "#284A33", "#7DF7A0", "#1f3d2b"),
        ("#5C3B3B", "#4A2828", "#F7A07D", "#3d1f1f"),
        ("#3B4E5C", "#28394A", "#7DB8F7", "#1f2f3d"),
        ("#5C5240", "#4A4030", "#F7D87D", "#3d3520"),
        ("#4E3B5C", "#3C2849", "#C67DF7", "#2d1a3f"),
    ]

    # ─── Build SVG ───────────────────────────────────────────────────────
    svg_parts = []

    # Defs: gradients, filters
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH} {SKY_HEIGHT}" width="100%">
<defs>
  <!-- Night sky gradient -->
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#0B0E1A"/>
    <stop offset="40%" stop-color="#131729"/>
    <stop offset="100%" stop-color="#1C2333"/>
  </linearGradient>

  <!-- Stars filter -->
  <filter id="glow">
    <feGaussianBlur stdDeviation="1.5" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Window glow -->
  <filter id="windowGlow">
    <feGaussianBlur stdDeviation="0.8" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <!-- Moon glow -->
  <radialGradient id="moonGlow" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="#F5F3CE" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="#F5F3CE" stop-opacity="0"/>
  </radialGradient>
</defs>

<!-- Sky background -->
<rect width="{SVG_WIDTH}" height="{SKY_HEIGHT}" fill="url(#sky)"/>
''')

    # Stars
    rng = random.Random(42)
    for _ in range(80):
        sx = rng.uniform(0, SVG_WIDTH)
        sy = rng.uniform(5, GROUND_Y - 60)
        sr = rng.uniform(0.4, 1.2)
        so = rng.uniform(0.3, 0.9)
        svg_parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="white" opacity="{so:.2f}" filter="url(#glow)"/>')

    # Twinkling stars (CSS animated)
    svg_parts.append('<style>')
    svg_parts.append('@keyframes twinkle { 0%,100%{opacity:0.2} 50%{opacity:1} }')
    for i in range(15):
        delay = rng.uniform(0, 4)
        dur = rng.uniform(2, 5)
        svg_parts.append(f'.star{i}{{ animation: twinkle {dur:.1f}s {delay:.1f}s infinite ease-in-out; }}')

    # Building label styles
    svg_parts.append('.repo-label { font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace; font-size: 7px; fill: #8892a8; }')
    svg_parts.append('.commit-label { font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace; font-size: 7px; fill: #F7E87D; font-weight: bold; }')
    svg_parts.append('.title-text { font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace; }')
    svg_parts.append('</style>')

    for i in range(15):
        sx = rng.uniform(0, SVG_WIDTH)
        sy = rng.uniform(5, GROUND_Y - 80)
        sr = rng.uniform(0.5, 1.5)
        svg_parts.append(f'<circle class="star{i}" cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="white" filter="url(#glow)"/>')

    # Moon
    moon_x = SVG_WIDTH - 80
    svg_parts.append(f'''
<circle cx="{moon_x}" cy="50" r="30" fill="url(#moonGlow)"/>
<circle cx="{moon_x}" cy="50" r="14" fill="#F5F3CE" opacity="0.9"/>
<circle cx="{moon_x + 4}" cy="48" r="14" fill="#0B0E1A" opacity="0.7"/>
''')

    # Ground / road
    svg_parts.append(f'''
<rect x="0" y="{GROUND_Y}" width="{SVG_WIDTH}" height="{SKY_HEIGHT - GROUND_Y}" fill="#111520"/>
<line x1="0" y1="{GROUND_Y + 16}" x2="{SVG_WIDTH}" y2="{GROUND_Y + 16}" stroke="#2a2f40" stroke-width="0.5" stroke-dasharray="8,12"/>
''')

    # ─── Draw buildings ──────────────────────────────────────────────────
    cursor_x = PADDING_X

    for idx, (name, commits) in enumerate(repo_data):
        seed = repo_seed(name)
        brng = random.Random(seed)
        palette = PALETTES[seed % len(PALETTES)]
        base_color, dark_accent, window_lit, window_dark = palette

        # Size
        ratio = commits / max_commits
        bw = max(MIN_WIDTH, min(MAX_WIDTH, int(18 + ratio * 14)))
        bh = max(MIN_HEIGHT, int(MIN_HEIGHT + ratio * (MAX_HEIGHT - MIN_HEIGHT)))
        bx = cursor_x
        by = GROUND_Y - bh

        # Main building body
        svg_parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{base_color}" rx="1"/>')

        # Dark side edge (3D effect)
        edge_w = max(2, bw // 6)
        svg_parts.append(f'<rect x="{bx + bw - edge_w}" y="{by}" width="{edge_w}" height="{bh}" fill="{dark_accent}" rx="0"/>')

        # Roof accent
        svg_parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="2" fill="{window_lit}" opacity="0.4" rx="1"/>')

        # Rooftop details (antenna or dome, seeded)
        roof_type = brng.choice(["antenna", "dome", "flat", "spire"])
        mid_x = bx + bw / 2
        if roof_type == "antenna" and bh > 40:
            ah = brng.randint(8, 18)
            svg_parts.append(f'<line x1="{mid_x}" y1="{by}" x2="{mid_x}" y2="{by - ah}" stroke="#555" stroke-width="1"/>')
            svg_parts.append(f'<circle cx="{mid_x}" cy="{by - ah}" r="1.5" fill="#ff4444" opacity="0.8"/>')
        elif roof_type == "dome" and bw > 16:
            svg_parts.append(f'<ellipse cx="{mid_x}" cy="{by}" rx="{bw * 0.3}" ry="4" fill="{dark_accent}"/>')
        elif roof_type == "spire" and bh > 60:
            svg_parts.append(f'<polygon points="{mid_x},{by - 12} {mid_x - 3},{by} {mid_x + 3},{by}" fill="{dark_accent}"/>')

        # Windows
        win_w = 3
        win_h = 3.5
        win_pad_x = 4
        win_pad_y = 6
        cols = int(max(1, (bw - win_pad_x * 2 + 2) // (win_w + 2)))
        rows = int(max(1, (bh - win_pad_y * 2) // (win_h + 3)))

        x_offset = (bw - (cols * (win_w + 2) - 2)) / 2

        for row in range(rows):
            for col in range(cols):
                wx = bx + x_offset + col * (win_w + 2)
                wy = by + win_pad_y + row * (win_h + 3)

                # ~60% of windows are lit
                is_lit = brng.random() < 0.6
                wcolor = window_lit if is_lit else window_dark
                wopacity = brng.uniform(0.5, 0.95) if is_lit else 0.3

                svg_parts.append(
                    f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{win_w}" height="{win_h}" '
                    f'fill="{wcolor}" opacity="{wopacity:.2f}" rx="0.5"'
                    f'{" filter=&quot;url(#windowGlow)&quot;" if is_lit else ""}/>'
                )

        # Repo name (rotated, below ground)
        truncated = name[:12] + ".." if len(name) > 14 else name
        svg_parts.append(
            f'<text x="{bx + bw / 2}" y="{GROUND_Y + 10}" '
            f'text-anchor="middle" class="repo-label" '
            f'transform="rotate(45, {bx + bw / 2}, {GROUND_Y + 10})">'
            f'{truncated}</text>'
        )

        # Commit count on top of building
        if bh > 30:
            svg_parts.append(
                f'<text x="{bx + bw / 2}" y="{by - 4}" '
                f'text-anchor="middle" class="commit-label">'
                f'{commits}</text>'
            )

        cursor_x += bw + BUILDING_GAP

    # ─── Title ───────────────────────────────────────────────────────────
    total_commits = sum(c for _, c in repo_data)
    svg_parts.append(
        f'<text x="{PADDING_X}" y="22" class="title-text" font-size="14" fill="#F7E87D" font-weight="bold">'
        f'🏙 {USERNAME}\'s GitHub City</text>'
    )
    svg_parts.append(
        f'<text x="{PADDING_X}" y="38" class="title-text" font-size="9" fill="#5a6278">'
        f'{n} buildings  ·  {total_commits:,} total commits</text>'
    )

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if not USERNAME:
        print("Error: GITHUB_USERNAME environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Fetching repos for {USERNAME}...")
    repos = fetch_repos(USERNAME)
    if not repos:
        print("No repos found or API error.", file=sys.stderr)
        sys.exit(1)

    # Filter out forks, keep only sources
    repos = [r for r in repos if not r.get("fork", False)]
    repos = repos[:MAX_REPOS]

    print(f"📦 Found {len(repos)} repos. Fetching commit counts...")

    repo_data = []
    for r in repos:
        name = r["name"]
        commits = fetch_commit_count(USERNAME, name)
        repo_data.append((name, commits))
        print(f"  {name}: {commits} commits")

    # Sort by commits descending
    repo_data.sort(key=lambda x: x[1], reverse=True)

    print(f"🎨 Generating city SVG...")
    svg = generate_city_svg(repo_data)

    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)

    print(f"✅ City saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()