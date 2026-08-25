#!/usr/bin/env python3
"""Builds neofetch.svg — a neofetch-style profile card: ASCII portrait on the
left, key/value rows on the right.

The portrait comes from portrait.txt (see tools/make_portrait.py); it only
changes when the source photo does, so this script needs no image libraries and
the daily Action stays dependency-free.

Run locally:  GITHUB_USERNAME=princymaheshwari python generate_all.py
In Actions:   env vars are set automatically.
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.error

USERNAME = os.environ.get("GITHUB_USERNAME", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_REPOS = int(os.environ.get("MAX_REPOS", "50"))

HERE = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT — placeholder pending Princy's copy. Edit only this block.
#
# Rows are (key, value). Anything in <angle brackets> is a stub. Values render
# right-aligned against dot leaders, so keep them under ~46 characters.
# ═══════════════════════════════════════════════════════════════════════════════

USER, HOST = "princy", "github"

WHOAMI = [
    ("OS",     "<os>"),
    ("Uptime", None),                 # None -> filled live from account age
    ("Host",   "<school>"),
    ("Kernel", "<role / title>"),
    ("IDE",    "<editors>"),
]

STACK = [
    ("Languages.Programming", "<languages>"),
    ("Languages.ML",          "<ml stack>"),
    ("Languages.Infra",       "<infra>"),
    ("Languages.Real",        "<spoken languages>"),
]

SECTIONS = [
    ("Research", [
        ("Focus",  "<what you research>"),
        ("Data",   "<datasets / instruments>"),
        ("Method", "<approach>"),
    ]),
    ("Recent Builds", [
        ("<repo-name>", "<one-line description>"),
        ("<repo-name>", "<one-line description>"),
        ("<repo-name>", "<one-line description>"),
    ]),
    ("Contact", [
        ("LinkedIn",  "princy-maheshwari1"),
        ("Portfolio", "princymaheshwari.me"),
    ]),
]

# ═══════════════════════════════════════════════════════════════════════════════
# Layout + palette
# ═══════════════════════════════════════════════════════════════════════════════

ROW_W = 72          # characters per info row
FS = 10.5           # font size, both columns
CW = FS * 0.6       # monospace advance width
LH = 15             # line height
PAD = 28
ART_X = 44
GAP = 30

C_BG      = "#080b12"
C_PANEL   = "#0d1220"
C_BORDER  = "#1c2740"
C_TAB     = "#3d4a63"
C_KEY     = "#f59e0b"
C_VAL     = "#c7d2e0"
C_DOT     = "#28344d"
C_RULE    = "#233150"
C_SECTION = "#8296b8"
C_ACCENT  = "#10b981"
C_LINK    = "#60a5fa"

# Portrait tones, darkest ink -> brightest. Index is position along the ramp
# in tools/make_portrait.py.
RAMP = " .':;+*ocbdkhaoOQ0ZmMW8%B@"
TONES = [(8, "#9c8f74"), (16, "#cbbc9c"), (99, "#f5ecd8")]

MONO = "JetBrains Mono,Fira Code,DejaVu Sans Mono,Consolas,monospace"


# ═══════════════════════════════════════════════════════════════════════════════
# GitHub API
# ═══════════════════════════════════════════════════════════════════════════════

def github_get(url):
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "neofetch-readme"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  ! HTTP {e.code} for {url}", file=sys.stderr)
        return None


def fetch_repos(username):
    repos, page = [], 1
    while True:
        data = github_get(f"https://api.github.com/users/{username}/repos"
                          f"?per_page=100&page={page}&sort=updated")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_commit_count(username, repo):
    """Returns None on failure — never a placeholder, since a silent fallback
    would publish an understated commit total."""
    data = github_get(f"https://api.github.com/repos/{username}/{repo}"
                      f"/contributors?per_page=100&anon=true")
    if not isinstance(data, list):
        return None
    return sum(c.get("contributions", 0) for c in data)


def account_uptime(created):
    """neofetch-style uptime, measured from account creation."""
    if not created:
        return "unknown"
    start = datetime.date(int(created[0:4]), int(created[5:7]), int(created[8:10]))
    today = datetime.date.today()
    months = (today.year - start.year) * 12 + today.month - start.month
    if today.day < start.day:
        months -= 1
    months = max(0, months)
    y, m = divmod(months, 12)
    anchor_y = start.year + (start.month - 1 + months) // 12
    anchor_m = (start.month - 1 + months) % 12 + 1
    anchor_d = min(start.day, [31, 29 if anchor_y % 4 == 0 else 28, 31, 30, 31, 30,
                               31, 31, 30, 31, 30, 31][anchor_m - 1])
    days = (today - datetime.date(anchor_y, anchor_m, anchor_d)).days

    bits = []
    if y:
        bits.append(f"{y} year{'s' * (y != 1)}")
    bits.append(f"{m} month{'s' * (m != 1)}")
    bits.append(f"{days} day{'s' * (days != 1)}")
    return ", ".join(bits)


# ═══════════════════════════════════════════════════════════════════════════════
# SVG helpers
# ═══════════════════════════════════════════════════════════════════════════════

def esc(s):
    """Escape for SVG, forcing pure-ASCII output via numeric entities."""
    out = []
    for ch in s:
        if ch == "&":
            out.append("&amp;")
        elif ch == "<":
            out.append("&lt;")
        elif ch == ">":
            out.append("&gt;")
        elif ord(ch) < 128:
            out.append(ch)
        else:
            out.append(f"&#{ord(ch)};")
    return "".join(out)


def tone(ch):
    i = RAMP.find(ch)
    if i <= 0:
        return None
    for limit, col in TONES:
        if i <= limit:
            return col
    return TONES[-1][1]


def row(key, value):
    """'. key: ......... value', padded to exactly ROW_W characters."""
    n = ROW_W - len(key) - len(value) - 5
    if n < 2:
        value = value[:max(0, ROW_W - len(key) - 7)] + ".."
        n = ROW_W - len(key) - len(value) - 5
    return [(". ", C_DOT), (key + ":", C_KEY),
            (" " + "." * n + " ", C_DOT), (value, C_VAL)]


def section(title):
    tail = ROW_W - len(title) - 6
    return [("- ", C_RULE), (title, C_SECTION), (" " + "─" * tail + "·~·", C_RULE)]


def prompt(user, host):
    tail = ROW_W - len(user) - len(host) - 5
    return [(user, C_ACCENT), ("@", C_RULE), (host, C_LINK),
            (" " + "─" * tail + "·~·", C_RULE)]


def spans_for_art(line):
    """Group consecutive same-tone characters so each run is one tspan."""
    out, run, col = [], "", None
    for ch in line:
        c = tone(ch)
        if c != col:
            if run:
                out.append((run, col))
            run, col = ch, c
        else:
            run += ch
    if run:
        out.append((run, col))
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# Panel
# ═══════════════════════════════════════════════════════════════════════════════

def build_lines(repos, repo_data, user_info):
    uptime = account_uptime((user_info or {}).get("created_at"))
    lines = [prompt(USER, HOST)]
    for k, v in WHOAMI:
        lines.append(row(k, uptime if v is None else v))
    lines.append(None)
    for k, v in STACK:
        lines.append(row(k, v))
    for title, rows in SECTIONS:
        lines.append(None)
        lines.append(section(title))
        for k, v in rows:
            lines.append(row(k, v))

    # live stats
    non_forks = [r for r in repos if not r.get("fork")]
    commits = sum(c for _, c in repo_data)
    counts = {}
    for r in non_forks:
        if r.get("language"):
            counts[r["language"]] = counts.get(r["language"], 0) + 1
    total = sum(counts.values()) or 1
    mix = " · ".join(f"{k} {round(v / total * 100)}%"
                          for k, v in sorted(counts.items(), key=lambda x: -x[1])[:3])

    lines.append(None)
    lines.append(section("GitHub Stats"))
    lines.append(row("Repos", f"{len(non_forks)}  |  Commits: {commits:,}"))
    lines.append(row("Top Languages", mix))
    return lines


def generate_neofetch_svg(repos, repo_data, user_info):
    with open(os.path.join(HERE, "portrait.txt"), encoding="utf-8") as f:
        art = [l.rstrip("\n") for l in f if l.strip("\n")]

    lines = build_lines(repos, repo_data, user_info)

    art_cols = max(len(l) for l in art)
    txt_x = ART_X + art_cols * CW + GAP
    W = int(txt_x + ROW_W * CW + ART_X)
    rows = max(len(art), len(lines))
    TAB_H = 36
    panel_h = PAD * 2 + rows * LH
    H = int(TAB_H + panel_h + 18)

    art_off = (rows - len(art)) // 2
    txt_off = (rows - len(lines)) // 2
    top = TAB_H + PAD + 11

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" font-family="{MONO}">',
        '  <defs>',
        f'    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{C_PANEL}"/>'
        f'<stop offset="100%" stop-color="#0a0e19"/></linearGradient>',
        '    <filter id="glow"><feGaussianBlur stdDeviation="0.5" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        f'    <clipPath id="clip"><rect width="{W}" height="{H}" rx="10"/></clipPath>',
        '  </defs>',
        f'  <g clip-path="url(#clip)">',
        f'    <rect width="{W}" height="{H}" fill="{C_BG}"/>',
        f'    <text x="26" y="23" font-size="11" fill="{C_TAB}">{USERNAME or "princymaheshwari"}'
        f'<tspan fill="#26324a"> / </tspan>README<tspan fill="#26324a">.md</tspan></text>',
        f'    <rect x="18" y="{TAB_H}" width="{W - 36}" height="{panel_h}" rx="10" '
        f'fill="url(#bg)" stroke="{C_BORDER}" stroke-width="1"/>',
    ]

    for i, line in enumerate(art):
        if not line.strip():
            continue
        y = top + (i + art_off) * LH
        body = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' if c else esc(t)
                       for t, c in spans_for_art(line))
        out.append(f'    <text x="{ART_X}" y="{y:.0f}" font-size="{FS}" '
                   f'xml:space="preserve" filter="url(#glow)">{body}</text>')

    for i, line in enumerate(lines):
        if line is None:
            continue
        y = top + (i + txt_off) * LH
        body = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in line)
        out.append(f'    <text x="{txt_x:.0f}" y="{y:.0f}" font-size="{FS}" '
                   f'xml:space="preserve">{body}</text>')

    cur_y = top + (len(lines) + txt_off) * LH - 9
    out.append(f'    <rect x="{txt_x:.0f}" y="{cur_y:.0f}" width="{CW:.1f}" height="11" '
               f'fill="{C_ACCENT}" opacity="0.85"><animate attributeName="opacity" '
               f'values="0.85;0;0.85" dur="1.2s" repeatCount="indefinite"/></rect>')
    out.append(f'    <text x="{W - 32}" y="{H - 26}" text-anchor="end" font-size="8" '
               f'fill="#1b2740">auto-generated daily via GitHub Actions</text>')
    out.append('  </g>\n</svg>')
    return "\n".join(out)


def main():
    if not USERNAME:
        print("Error: set GITHUB_USERNAME", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching {USERNAME}...")
    repos = fetch_repos(USERNAME)
    if not repos:
        print("No repos found.", file=sys.stderr)
        sys.exit(1)
    user_info = github_get(f"https://api.github.com/users/{USERNAME}")

    non_forks = [r for r in repos if not r.get("fork")][:MAX_REPOS]
    repo_data, failed = [], []
    for r in non_forks:
        count = fetch_commit_count(USERNAME, r["name"])
        if count is None:
            failed.append(r["name"])
        else:
            repo_data.append((r["name"], count))

    if failed:
        shown = ", ".join(failed[:5]) + ("..." if len(failed) > 5 else "")
        print(f"Error: commit counts unavailable for {len(failed)} repo(s): {shown}\n"
              f"Refusing to publish an understated total. Unauthenticated runs are "
              f"capped at 60 requests/hour — set GITHUB_TOKEN.", file=sys.stderr)
        sys.exit(1)

    repo_data.sort(key=lambda x: x[1], reverse=True)

    with open(os.path.join(HERE, "neofetch.svg"), "w", encoding="utf-8") as f:
        f.write(generate_neofetch_svg(repos, repo_data, user_info))
    print("  wrote neofetch.svg")


if __name__ == "__main__":
    main()
