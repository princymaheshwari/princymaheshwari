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
# CONTENT — edit only this block.
#
# Values are truncated past the row width, so keep them under ~50 characters.
# ═══════════════════════════════════════════════════════════════════════════════

USER, HOST = "princy", "github"

IDENTITY = [
    ("Role",         "Developer building intelligent, compute-heavy systems"),
    ("Host",         "Georgia State University"),
    ("Privileges",   "Presidential Scholar · Honors College"),
    ("Kernel",       "Computer Science + Mathematics"),
    ("Base",         "Atlanta, GA"),
    ("Environment",  "Serverless GPUs · HPC clusters · physical hardware"),
    ("System calls", "perceive() · verify() · orchestrate() · recover()"),
]

# (name, tag, [(key, value), ...])
SYSTEMS = [
    ("ToolFinder", "HACKILLINOIS '26", [
        ("pipeline", "Voice → semantic routing → parallel GPU vision"),
        ("compute",  "Modal A10G/H100 · YOLO/SAM2 · SAM3 fallback"),
        ("output",   "Pixel masks · centroids · physical laser targeting"),
    ]),
    ("Veritas", "NEXHACKS '26", [
        ("pipeline", "GitHub webhook → parsers → AI comparison → issue"),
        ("handles",  "Python/JS/TS/Java · Markdown · OpenAPI"),
        ("result",   "Live GitHub App · analysis cost reduced by 96%"),
    ]),
    ("GeneFamilyConverge", "OPEN SOURCE", [
        ("pipeline", "Portable HPC workflow orchestration"),
        ("handles",  "Slurm arrays · resource constraints · backfill"),
        ("result",   "114 species · multi-node · 2.83× speedup"),
    ]),
    ("SEP Event Pipeline", "VALIDATED", [
        ("pipeline", "30 years · 4 instruments · 3 GOES eras + SOHO"),
        ("handles",  "Fallbacks · format changes · schema drift"),
        ("result",   "100% recall (159/159) · 92.4% precision"),
    ]),
]

DEFAULTS = "portable > machine-bound · measured > assumed · automated > manual"

NETWORK = [
    ("Web",      "princymaheshwari.me"),
    ("LinkedIn", "/in/princy-maheshwari1"),
]

# Live repo/commit/language counts, pulled from the GitHub API. Off by default:
# the card above is entirely static, so nothing is fetched and the daily Action
# is a no-op. Flip to True to give it something to refresh.
SHOW_STATS = False

# ═══════════════════════════════════════════════════════════════════════════════
# Layout + palette
# ═══════════════════════════════════════════════════════════════════════════════

ROW_W = 72          # characters per row in the right-hand column
KEY_W = 18          # key is dot-padded to this width, then the value starts
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
C_HEAD    = "#e8eef7"   # SYSTEMS BUILT / DEFAULTS / NETWORK
C_KEY     = "#f59e0b"   # top-level keys and project names
C_SUBKEY  = "#6b7f9e"   # indented keys, which should recede
C_TAG     = "#10b981"   # right-aligned project tags
C_VAL     = "#c7d2e0"
C_DOT     = "#28344d"
C_RULE    = "#2e4165"
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


# ── line builders ─────────────────────────────────────────────────────────────

def prompt(user, host):
    return [(user, C_ACCENT), ("@", C_RULE), (host, C_LINK)]


def rule():
    return [("─" * ROW_W, C_RULE)]


def header(title):
    return [(title, C_HEAD)]


def plain(text):
    return [(text[:ROW_W], C_VAL)]


def kv(key, value, indent=0):
    """'key.......... value' — dot-padded to KEY_W, value left-aligned after."""
    field = KEY_W - len(key)
    room = ROW_W - indent - KEY_W - 1
    if len(value) > room:
        value = value[:max(0, room - 2)] + ".."
    col = C_SUBKEY if indent else C_KEY
    parts = []
    if indent:
        parts.append((" " * indent, C_DOT))
    parts.append((key, col))
    parts.append(("." * max(1, field) + " ", C_DOT))
    parts.append((value, C_VAL))
    return parts


def titled(name, tag):
    """Project name on the left, tag right-aligned to the row edge."""
    gap = ROW_W - len(name) - len(tag)
    return [(name, C_KEY), (" " * max(1, gap), C_DOT), (tag, C_TAG)]


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

def build_lines(repos, repo_data):
    lines = [prompt(USER, HOST), rule()]
    for k, v in IDENTITY:
        lines.append(kv(k, v))

    lines += [None, header("SYSTEMS BUILT"), rule()]
    for i, (name, tag, rows) in enumerate(SYSTEMS):
        if i:
            lines.append(None)
        lines.append(titled(name, tag))
        for k, v in rows:
            lines.append(kv(k, v, indent=2))

    lines += [None, header("DEFAULTS"), rule(), plain(DEFAULTS)]

    lines += [None, header("NETWORK"), rule()]
    for k, v in NETWORK:
        lines.append(kv(k, v))

    if SHOW_STATS:
        non_forks = [r for r in repos if not r.get("fork")]
        counts = {}
        for r in non_forks:
            if r.get("language"):
                counts[r["language"]] = counts.get(r["language"], 0) + 1
        total = sum(counts.values()) or 1
        mix = " · ".join(f"{k} {round(v / total * 100)}%"
                         for k, v in sorted(counts.items(), key=lambda x: -x[1])[:3])
        lines += [None, header("GITHUB"), rule(),
                  kv("Repos", f"{len(non_forks)}  ·  commits {sum(c for _, c in repo_data):,}"),
                  kv("Languages", mix)]
    return lines


def generate_neofetch_svg(repos, repo_data):
    with open(os.path.join(HERE, "portrait.txt"), encoding="utf-8") as f:
        art = [l.rstrip("\n") for l in f if l.strip("\n")]

    lines = build_lines(repos, repo_data)

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
    out.append('  </g>\n</svg>')
    return "\n".join(out)


def main():
    repos, repo_data = [], []

    if SHOW_STATS:
        if not USERNAME:
            print("Error: set GITHUB_USERNAME", file=sys.stderr)
            sys.exit(1)
        print(f"Fetching {USERNAME}...")
        repos = fetch_repos(USERNAME)
        if not repos:
            print("No repos found.", file=sys.stderr)
            sys.exit(1)

        failed = []
        for r in [x for x in repos if not x.get("fork")][:MAX_REPOS]:
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

    with open(os.path.join(HERE, "neofetch.svg"), "w", encoding="utf-8") as f:
        f.write(generate_neofetch_svg(repos, repo_data))
    print("  wrote neofetch.svg")


if __name__ == "__main__":
    main()
