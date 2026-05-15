#!/usr/bin/env python3
"""
Master generator — produces all SVG components for the GitHub profile README.
  1. header.svg   — terminal-style identity card
  2. stats-bar.svg — compact repo/star/language stats
  3. github-city.svg — dynamic city skyline (buildings = repos, height = commits)
  4. footer.svg — terminal prompt with links

Run locally:  GITHUB_USERNAME=yourname python3 generate_all.py
In Actions:   env vars are set automatically.
"""

import os
import sys
import json
import math
import random
import hashlib
import urllib.request
import urllib.error

USERNAME = os.environ.get("GITHUB_USERNAME", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_REPOS = int(os.environ.get("MAX_REPOS", "50"))

# ═══════════════════════════════════════════════════════════════════════════════
# GitHub API
# ═══════════════════════════════════════════════════════════════════════════════

def github_get(url):
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "github-city"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  ⚠ HTTP {e.code} for {url}", file=sys.stderr)
        return None

def fetch_repos(username):
    repos = []
    page = 1
    while True:
        data = github_get(f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&sort=updated")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos

def fetch_commit_count(username, repo_name):
    url = f"https://api.github.com/repos/{username}/{repo_name}/contributors?per_page=100&anon=true"
    data = github_get(url)
    if isinstance(data, list):
        return sum(c.get("contributions", 0) for c in data)
    return 1

def repo_seed(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


# ═══════════════════════════════════════════════════════════════════════════════
# 1) HEADER SVG
# ═══════════════════════════════════════════════════════════════════════════════

def generate_header_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 200" width="100%">
  <defs>
    <linearGradient id="termBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0e17"/>
      <stop offset="100%" stop-color="#0d1220"/>
    </linearGradient>
    <filter id="textGlow">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="roundedClip"><rect width="840" height="200" rx="8"/></clipPath>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <rect width="20" height="20" fill="none" stroke="#1a2235" stroke-width="0.3"/>
    </pattern>
  </defs>
  <g clip-path="url(#roundedClip)">
    <rect width="840" height="200" fill="url(#termBg)"/>
    <rect width="840" height="200" fill="url(#grid)" opacity="0.5"/>

    <rect width="840" height="28" fill="#0f1623"/>
    <circle cx="16" cy="14" r="5" fill="#ff5f57"/>
    <circle cx="34" cy="14" r="5" fill="#febc2e"/>
    <circle cx="52" cy="14" r="5" fill="#28c840"/>
    <text x="420" y="18" text-anchor="middle" font-family="JetBrains Mono,Fira Code,monospace" font-size="11" fill="#4a5568">princy@github ~ % whoami</text>

    <text x="30" y="62" font-family="JetBrains Mono,Fira Code,monospace" font-size="10" fill="#3b82f6" opacity="0.4">&#9484;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9488;</text>
    <text x="30" y="87" font-family="JetBrains Mono,Fira Code,monospace" font-size="24" font-weight="bold" filter="url(#textGlow)">
      <tspan fill="#3b82f6">&#10095;</tspan><tspan fill="#e2e8f0"> Princy</tspan>
    </text>
    <text x="190" y="87" font-family="JetBrains Mono,Fira Code,monospace" font-size="12" fill="#64748b">// undergraduate researcher</text>
    <text x="30" y="107" font-family="JetBrains Mono,Fira Code,monospace" font-size="10" fill="#3b82f6" opacity="0.4">&#9492;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9472;&#9496;</text>

    <text x="30" y="132" font-family="JetBrains Mono,Fira Code,monospace" font-size="11">
      <tspan fill="#f59e0b">&#9889; FOCUS</tspan><tspan fill="#64748b" dx="8">SEP Detection &#183; Deep Learning &#183; Physics-Informed Systems</tspan>
    </text>
    <text x="30" y="152" font-family="JetBrains Mono,Fira Code,monospace" font-size="11">
      <tspan fill="#10b981">&#11042; STACK</tspan><tspan fill="#64748b" dx="8">Python &#183; NumPy &#183; Pandas &#183; scikit-learn &#183; FastAPI &#183; PyTorch &#183; TensorFlow</tspan>
    </text>
    <text x="30" y="172" font-family="JetBrains Mono,Fira Code,monospace" font-size="11">
      <tspan fill="#8b5cf6">&#9672; BASE</tspan><tspan fill="#64748b" dx="10">Georgia State University &#183; Atlanta, GA</tspan>
    </text>

    <rect x="610" y="40" width="210" height="148" rx="4" fill="#0c101c" stroke="#1e293b" stroke-width="1"/>
    <text x="625" y="60" font-family="JetBrains Mono,Fira Code,monospace" font-size="9" fill="#475569">SYSTEM STATUS</text>
    <line x1="625" y1="66" x2="805" y2="66" stroke="#1e293b" stroke-width="0.5"/>
    <text x="625" y="86" font-family="JetBrains Mono,Fira Code,monospace" font-size="10"><tspan fill="#10b981">&#9679;</tspan><tspan fill="#94a3b8" dx="4">SEP Research</tspan><tspan fill="#10b981" dx="6">ACTIVE</tspan></text>
    <text x="625" y="104" font-family="JetBrains Mono,Fira Code,monospace" font-size="10"><tspan fill="#f59e0b">&#9679;</tspan><tspan fill="#94a3b8" dx="4">DL Coursera</tspan><tspan fill="#f59e0b" dx="6">IN PROG</tspan></text>
    <text x="625" y="122" font-family="JetBrains Mono,Fira Code,monospace" font-size="10"><tspan fill="#10b981">&#9679;</tspan><tspan fill="#94a3b8" dx="4">Open to Collab</tspan><tspan fill="#10b981" dx="6">YES</tspan></text>
    <text x="625" y="140" font-family="JetBrains Mono,Fira Code,monospace" font-size="10"><tspan fill="#3b82f6">&#9679;</tspan><tspan fill="#94a3b8" dx="4">AI Infrastructure</tspan><tspan fill="#3b82f6" dx="6">EXPLORING</tspan></text>
    <text x="625" y="166" font-family="JetBrains Mono,Fira Code,monospace" font-size="9" fill="#334155">ATL</text>
    <text x="625" y="178" font-family="JetBrains Mono,Fira Code,monospace" font-size="9" fill="#334155">ping: always reachable</text>

    <rect width="840" height="200" rx="8" fill="none" stroke="#1e293b" stroke-width="1.5"/>
  </g>
</svg>'''


# ═══════════════════════════════════════════════════════════════════════════════
# 2) STATS BAR SVG
# ═══════════════════════════════════════════════════════════════════════════════

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "C": "#555555", "C++": "#f34b7d", "Java": "#b07219", "Rust": "#dea584",
    "Go": "#00ADD8", "Ruby": "#701516", "Shell": "#89e051", "HTML": "#e34c26",
    "CSS": "#563d7c", "Jupyter Notebook": "#DA5B0B", "R": "#198CE7",
}

def generate_stats_svg(repos):
    non_forks = [r for r in repos if not r.get("fork")]
    total_stars = sum(r.get("stargazers_count", 0) for r in non_forks)
    lang_count = {}
    for r in non_forks:
        lang = r.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1
    top_langs = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)[:5]
    total = sum(c for _, c in top_langs) if top_langs else 1

    W, H = 840, 52
    bar_x, bar_w = 250, 280

    lang_bar = []
    cx = bar_x
    for lang, count in top_langs:
        seg_w = (count / total) * bar_w
        color = LANG_COLORS.get(lang, "#8b949e")
        lang_bar.append(f'<rect x="{cx:.1f}" y="15" width="{seg_w:.1f}" height="8" fill="{color}"/>')
        cx += seg_w

    lang_labels = []
    lx = bar_x
    for lang, count in top_langs:
        pct = int((count / total) * 100)
        color = LANG_COLORS.get(lang, "#8b949e")
        lang_labels.append(f'<circle cx="{lx}" cy="38" r="3" fill="{color}"/>')
        lang_labels.append(f'<text x="{lx + 7}" y="41" font-family="JetBrains Mono,Fira Code,monospace" font-size="8" fill="#64748b">{lang} {pct}%</text>')
        lx += len(lang) * 5 + 38

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%">
  <defs><clipPath id="sClip"><rect width="{W}" height="{H}" rx="6"/></clipPath></defs>
  <g clip-path="url(#sClip)">
    <rect width="{W}" height="{H}" fill="#0a0e17" stroke="#1e293b" stroke-width="1" rx="6"/>
    <text x="20" y="22" font-family="JetBrains Mono,Fira Code,monospace" font-size="16" fill="#e2e8f0" font-weight="bold">{len(non_forks)}</text>
    <text x="20" y="38" font-family="JetBrains Mono,Fira Code,monospace" font-size="8" fill="#475569">REPOS</text>
    <text x="80" y="22" font-family="JetBrains Mono,Fira Code,monospace" font-size="16" fill="#f59e0b" font-weight="bold">{total_stars}</text>
    <text x="80" y="38" font-family="JetBrains Mono,Fira Code,monospace" font-size="8" fill="#475569">STARS</text>
    <line x1="140" y1="8" x2="140" y2="44" stroke="#1e293b" stroke-width="1"/>
    <text x="160" y="26" font-family="JetBrains Mono,Fira Code,monospace" font-size="9" fill="#475569">LANGUAGES &#9654;</text>
    <rect x="{bar_x}" y="15" width="{bar_w}" height="8" fill="#1e293b" rx="4"/>
    {''.join(lang_bar)}
    <rect x="{bar_x}" y="15" width="{bar_w}" height="8" fill="none" rx="4" stroke="#0a0e17" stroke-width="0.5"/>
    {''.join(lang_labels)}
  </g>
</svg>'''


# ═══════════════════════════════════════════════════════════════════════════════
# 3) CITY SKYLINE SVG
# ═══════════════════════════════════════════════════════════════════════════════

def generate_city_svg(repo_data):
    if not repo_data:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 200"><rect width="840" height="200" fill="#0a0e17" rx="6"/><text x="420" y="100" text-anchor="middle" fill="#475569" font-family="JetBrains Mono,monospace" font-size="12">No repos yet — start building!</text></svg>'

    n = len(repo_data)
    BUILDING_GAP = 3
    MIN_W, MAX_W = 14, 30
    MIN_H, MAX_H = 20, 175
    GROUND_Y = 225
    # Extra height below skyline so angled repo labels don't crowd building bases (keep modest).
    TOTAL_H = 272
    LABEL_ANCHOR_Y = GROUND_Y + 17
    PAD_X = 20

    max_commits = max(c for _, c in repo_data) or 1

    total_w = sum(max(MIN_W, min(MAX_W, int(16 + (c / max_commits) * 14))) for _, c in repo_data) + BUILDING_GAP * (n - 1) + PAD_X * 2
    SVG_W = max(840, total_w)

    PALETTES = [
        ("#2D3142", "#1B1F2E", "#F7E87D", "#1a1d2b"),
        ("#3A3E5C", "#272A42", "#7DE8F7", "#22253a"),
        ("#4A3B5C", "#33284A", "#E87DF7", "#2b1f3d"),
        ("#3B5C4A", "#284A33", "#7DF7A0", "#1f3d2b"),
        ("#5C3B3B", "#4A2828", "#F7A07D", "#3d1f1f"),
        ("#3B4E5C", "#28394A", "#7DB8F7", "#1f2f3d"),
        ("#5C5240", "#4A4030", "#F7D87D", "#3d3520"),
        ("#4E3B5C", "#3C2849", "#C67DF7", "#2d1a3f"),
    ]

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {TOTAL_H}" width="100%">
<defs>
  <linearGradient id="cSky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#0a0e17"/><stop offset="100%" stop-color="#0d1220"/>
  </linearGradient>
  <filter id="wGlow"><feGaussianBlur stdDeviation="0.8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="sGlow"><feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="cClip"><rect width="{SVG_W}" height="{TOTAL_H}" rx="6"/></clipPath>
  <pattern id="cGrid" width="20" height="20" patternUnits="userSpaceOnUse">
    <rect width="20" height="20" fill="none" stroke="#1a2235" stroke-width="0.2"/>
  </pattern>
</defs>
<g clip-path="url(#cClip)">
<rect width="{SVG_W}" height="{TOTAL_H}" fill="url(#cSky)"/>
<rect width="{SVG_W}" height="{TOTAL_H}" fill="url(#cGrid)" opacity="0.3"/>''']

    # Stars
    rng = random.Random(42)
    for _ in range(50):
        sx, sy = rng.uniform(0, SVG_W), rng.uniform(5, GROUND_Y - 50)
        sr, so = rng.uniform(0.3, 1.0), rng.uniform(0.3, 0.8)
        parts.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr:.1f}" fill="white" opacity="{so:.2f}" filter="url(#sGlow)"/>')

    # Twinkling
    parts.append('<style>')
    parts.append('@keyframes tw{0%,100%{opacity:0.2}50%{opacity:1}}')
    for i in range(8):
        d, dur = rng.uniform(0, 4), rng.uniform(2, 5)
        parts.append(f'.t{i}{{animation:tw {dur:.1f}s {d:.1f}s infinite ease-in-out}}')
    parts.append('.rl{font-family:JetBrains Mono,Fira Code,monospace;font-size:6.5px;fill:#4a5568}')
    parts.append('.cl{font-family:JetBrains Mono,Fira Code,monospace;font-size:7px;fill:#F7E87D;font-weight:bold}')
    parts.append('</style>')

    for i in range(8):
        sx, sy = rng.uniform(0, SVG_W), rng.uniform(5, GROUND_Y - 60)
        parts.append(f'<circle class="t{i}" cx="{sx:.0f}" cy="{sy:.0f}" r="{rng.uniform(0.5, 1.2):.1f}" fill="white" filter="url(#sGlow)"/>')

    # Moon
    mx = SVG_W - 60
    parts.append(f'<circle cx="{mx}" cy="35" r="10" fill="#F5F3CE" opacity="0.85"/>')
    parts.append(f'<circle cx="{mx + 3}" cy="33" r="10" fill="#0a0e17" opacity="0.7"/>')

    # Ground
    parts.append(f'<rect x="0" y="{GROUND_Y}" width="{SVG_W}" height="{TOTAL_H - GROUND_Y}" fill="#080b14"/>')
    parts.append(f'<line x1="0" y1="{GROUND_Y}" x2="{SVG_W}" y2="{GROUND_Y}" stroke="#1e293b" stroke-width="0.5"/>')

    # Title
    total_commits = sum(c for _, c in repo_data)
    parts.append(f'<text x="{PAD_X}" y="16" font-family="JetBrains Mono,Fira Code,monospace" font-size="9" fill="#475569">&#9608; CITY SKYLINE &#183; {n} repos &#183; {total_commits:,} commits</text>')

    # Buildings
    cursor = PAD_X
    for idx, (name, commits) in enumerate(repo_data):
        seed = repo_seed(name)
        brng = random.Random(seed)
        base, dark, lit, unlit = PALETTES[seed % len(PALETTES)]

        ratio = commits / max_commits
        bw = max(MIN_W, min(MAX_W, int(16 + ratio * 14)))
        bh = max(MIN_H, int(MIN_H + ratio * (MAX_H - MIN_H)))
        bx, by = cursor, GROUND_Y - bh

        parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{base}" rx="1"/>')
        ew = max(2, bw // 6)
        parts.append(f'<rect x="{bx + bw - ew}" y="{by}" width="{ew}" height="{bh}" fill="{dark}"/>')
        parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="2" fill="{lit}" opacity="0.35" rx="1"/>')

        # Roof
        mid = bx + bw / 2
        rt = brng.choice(["ant", "dome", "spire", "flat"])
        if rt == "ant" and bh > 40:
            ah = brng.randint(6, 14)
            parts.append(f'<line x1="{mid}" y1="{by}" x2="{mid}" y2="{by - ah}" stroke="#555" stroke-width="0.8"/>')
            parts.append(f'<circle cx="{mid}" cy="{by - ah}" r="1.2" fill="#ff4444" opacity="0.7"/>')
        elif rt == "spire" and bh > 50:
            parts.append(f'<polygon points="{mid},{by - 10} {mid - 2.5},{by} {mid + 2.5},{by}" fill="{dark}"/>')

        # Windows
        ww, wh = 2.5, 3
        cols = int(max(1, (bw - 6) // (ww + 2)))
        rows = int(max(1, (bh - 10) // (wh + 3)))
        xo = (bw - (cols * (ww + 2) - 2)) / 2
        for r in range(rows):
            for c in range(cols):
                wx = bx + xo + c * (ww + 2)
                wy = by + 5 + r * (wh + 3)
                is_lit = brng.random() < 0.55
                wc = lit if is_lit else unlit
                wo = brng.uniform(0.4, 0.9) if is_lit else 0.25
                filt = ' filter="url(#wGlow)"' if is_lit else ''
                parts.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww}" height="{wh}" fill="{wc}" opacity="{wo:.2f}" rx="0.3"{filt}/>')

        # Labels
        trunc = name[:10] + ".." if len(name) > 12 else name
        parts.append(f'<text x="{bx + bw / 2}" y="{LABEL_ANCHOR_Y}" text-anchor="middle" class="rl" transform="rotate(46,{bx + bw / 2},{LABEL_ANCHOR_Y})">{trunc}</text>')
        if bh > 30:
            parts.append(f'<text x="{bx + bw / 2}" y="{by - 3}" text-anchor="middle" class="cl">{commits}</text>')

        cursor += bw + BUILDING_GAP

    parts.append('<rect width="' + str(SVG_W) + '" height="' + str(TOTAL_H) + '" rx="6" fill="none" stroke="#1e293b" stroke-width="1"/>')
    parts.append('</g></svg>')
    return '\n'.join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# 4) FOOTER SVG
# ═══════════════════════════════════════════════════════════════════════════════

def generate_footer_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 50" width="100%">
  <defs><clipPath id="fClip"><rect width="840" height="50" rx="6"/></clipPath></defs>
  <g clip-path="url(#fClip)">
    <rect width="840" height="50" fill="#0a0e17" stroke="#1e293b" stroke-width="1" rx="6"/>
    <text x="20" y="20" font-family="JetBrains Mono,Fira Code,monospace" font-size="11">
      <tspan fill="#10b981">princy</tspan><tspan fill="#475569">@</tspan><tspan fill="#3b82f6">github</tspan><tspan fill="#475569"> ~ % </tspan><tspan fill="#94a3b8">echo $CONNECT</tspan>
    </text>
    <text x="20" y="38" font-family="JetBrains Mono,Fira Code,monospace" font-size="10">
      <tspan fill="#64748b">&#9654; </tspan><tspan fill="#f59e0b">linkedin/princy-maheshwari1</tspan><tspan fill="#475569"> &#183; </tspan><tspan fill="#f59e0b">princymaheshwari.me</tspan>
    </text>
    <text x="20" y="38" font-family="JetBrains Mono,Fira Code,monospace" font-size="7" fill="#334155" dy="0" dx="0"></text>
    <rect x="345" y="28" width="7" height="14" fill="#10b981" opacity="0.8">
      <animate attributeName="opacity" values="0.8;0;0.8" dur="1.2s" repeatCount="indefinite"/>
    </rect>
    <text x="820" y="32" text-anchor="end" font-family="JetBrains Mono,Fira Code,monospace" font-size="8" fill="#1e293b">auto-generated via GitHub Actions</text>
  </g>
</svg>'''


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if not USERNAME:
        print("Error: set GITHUB_USERNAME env var", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Fetching repos for {USERNAME}...")
    repos = fetch_repos(USERNAME)
    if not repos:
        print("No repos found.", file=sys.stderr)
        sys.exit(1)

    non_forks = [r for r in repos if not r.get("fork")][:MAX_REPOS]
    print(f"📦 {len(non_forks)} repos. Fetching commits...")

    repo_data = []
    for r in non_forks:
        name = r["name"]
        commits = fetch_commit_count(USERNAME, name)
        repo_data.append((name, commits))
        print(f"  {name}: {commits}")
    repo_data.sort(key=lambda x: x[1], reverse=True)

    print("🎨 Generating SVGs...")

    with open("header.svg", "w") as f:
        f.write(generate_header_svg())
    print("  ✅ header.svg")

    with open("stats-bar.svg", "w") as f:
        f.write(generate_stats_svg(repos))
    print("  ✅ stats-bar.svg")

    with open("github-city.svg", "w") as f:
        f.write(generate_city_svg(repo_data))
    print("  ✅ github-city.svg")

    with open("footer.svg", "w") as f:
        f.write(generate_footer_svg())
    print("  ✅ footer.svg")

    print("🏙️ All done!")


if __name__ == "__main__":
    main()