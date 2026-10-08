#!/usr/bin/env python3
"""Builds the images used by the profile README.

  assets/hero-{dark,light}.svg      static: name and one-line introduction
  assets/journey-{dark,light}.svg   static: career route drawn as a climb
  assets/stats-{dark,light}.svg     live: contributions, streaks, calendar, languages

Usage:
  GH_TOKEN=... GH_USER=missionshrestha python3 scripts/build_profile.py
  python3 scripts/build_profile.py --mock      # fake stats, for local previews

Standard library only, so the GitHub Action needs no installs.
"""
import base64
import datetime as dt
import html
import json
import os
import random
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = os.path.join(ASSETS, "fonts")
W = 880  # matches the width GitHub gives a profile README on desktop

PALETTE = {
    "dark": dict(ink="#E6EDF3", sub="#9198A1", line="#3D444D", faint="#21262D",
                 accent="#EE6D92", accent2="#B8476A", hill="#E6EDF3",
                 ramp=["#1C2128", "#4A1E2E", "#7A2945", "#B8476A", "#EE6D92"],
                 langs=["#EE6D92", "#B8476A", "#7A2945", "#9198A1", "#57606A", "#3D444D"]),
    "light": dict(ink="#1F2328", sub="#59636E", line="#D1D9E0", faint="#EFF2F5",
                  accent="#B0275A", accent2="#D9608A", hill="#1F2328",
                  ramp=["#EFF2F5", "#F6C9D6", "#E68AA6", "#C8466F", "#8E1D44"],
                  langs=["#8E1D44", "#C8466F", "#E68AA6", "#59636E", "#8C959F", "#D1D9E0"]),
}

DISPLAY = "'D', Georgia, 'Times New Roman', serif"
SANS = "'S', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

with open(os.path.join(FONTS, "widths.json")) as fh:
    WIDTHS = json.load(fh)


def text_width(s, size, face="sans"):
    table = WIDTHS[face]
    return sum(table.get(ch, 550) for ch in s) * size / 1000


def font_css(*faces):
    files = {"display": ("D", 600, "display-600.woff"),
             "sans": ("S", 400, "sans-400.woff"),
             "sansbold": ("S", 700, "sans-700.woff")}
    css = ""
    for f in faces:
        fam, weight, name = files[f]
        with open(os.path.join(FONTS, name), "rb") as fh:
            data = base64.b64encode(fh.read()).decode()
        css += (f"@font-face{{font-family:'{fam}';font-weight:{weight};"
                f"src:url(data:font/woff;base64,{data}) format('woff');}}")
    return css


def svg(width, height, label, body, css="", fonts=("sans",)):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(label)}">'
            f'<style>{font_css(*fonts)}{css}</style>{body}</svg>\n')


def write(name, content):
    path = os.path.join(ASSETS, name)
    with open(path, "w") as fh:
        fh.write(content)
    print("wrote", os.path.relpath(path, ROOT), f"{len(content)//1024} KB")


# ---------------------------------------------------------------- hero

RIDGE = [(0, 240), (80, 236), (150, 230), (210, 233), (280, 224), (340, 228), (410, 216),
         (460, 221), (520, 206), (565, 213), (610, 196), (645, 204), (690, 184), (716, 192),
         (750, 172), (772, 180), (800, 160), (818, 171), (836, 166), (858, 182), (880, 190)]


def ridge_path(points, dy=0, scale=1.0, base=250, dx=0):
    pts = [(x + dx, base - (base - y) * scale + dy) for x, y in points]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


PEAKS = [(440, 250), (472, 238), (500, 242), (540, 222), (570, 230), (602, 206), (630, 214),
         (664, 184), (690, 194), (714, 160), (736, 172), (754, 120), (772, 136), (800, 64),
         (814, 82), (830, 74), (850, 112), (866, 100), (880, 118), (880, 250)]


def hero(theme):
    c = PALETTE[theme]
    peaks_d = "M" + " L".join(f"{x},{y}" for x, y in PEAKS) + " Z"
    bands = "".join(f'<line x1="420" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(66, 250, 12))
    body = (
        f'<defs><clipPath id="p"><path d="{peaks_d}"/></clipPath></defs>'
        f'<path d="{peaks_d}" fill="{c["hill"]}" fill-opacity=".035"/>'
        f'<g clip-path="url(#p)" stroke="{c["line"]}" stroke-width="1" opacity=".55">{bands}</g>'
        f'<path d="M' + " L".join(f"{x},{y}" for x, y in PEAKS[:-1]) + f'" fill="none" stroke="{c["accent"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<text x="0" y="66" font-family="{DISPLAY}" font-weight="600" font-size="58" fill="{c["ink"]}">Mission Shrestha</text>'
        f'<text x="2" y="108" font-family="{SANS}" font-size="18" fill="{c["sub"]}">Software engineer in Kathmandu, Nepal.</text>'
        f'<text x="2" y="134" font-family="{SANS}" font-size="18" fill="{c["ink"]}">I build products end to end: the interface, the APIs, the data and the cloud underneath.</text>'
        f'<text x="2" y="186" font-family="{SANS}" font-weight="700" font-size="14" fill="{c["accent"]}">Open to new roles, in Kathmandu or remote</text>'
    )
    return svg(W, 250, "Mission Shrestha. Software engineer in Kathmandu, Nepal. I build products end to end: "
               "the interface, the APIs, the data and the cloud underneath. Open to new roles, in Kathmandu or remote.",
               body, fonts=("display", "sans", "sansbold"))


# ---------------------------------------------------------------- journey

STOPS = [
    ("2019", "B.E. Computer Engineering", "Kathmandu University"),
    ("2023", "Junior Full-Stack Developer", "Remote, with an Australian team"),
    ("2024", "Data Engineering Intern", "LIS Nepal"),
    ("2024", "Associate Software Engineer", "Azminds Services"),
    ("2025", "Software Engineer", "Azminds Services"),
    ("2025", "Tech Lead, Product Engineer", "Azminds Services, team of 9"),
]


def journey(theme):
    c = PALETTE[theme]
    H = 460
    pts = [(250, 404), (372, 344), (474, 292), (580, 238), (684, 184), (780, 122)]
    summit = (852, 54)
    between = [[(300, 370), (330, 380)], [(420, 318), (446, 324)], [(522, 268), (548, 276)],
               [(620, 212), (644, 222)], [(722, 158), (742, 168)], [(808, 98), (826, 106)]]
    ridge = []
    for i, p in enumerate(pts):
        ridge.append(p)
        ridge += between[i]
    sil = [(0, 448), (70, 440), (140, 428), (200, 418)] + ridge + [summit, (868, 82), (880, 98), (880, H), (0, H)]
    sil_d = "M" + " L".join(f"{x},{y}" for x, y in sil) + " Z"
    bands = "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(70, H, 16))
    trail = ridge[:ridge.index(pts[-1]) + 1]
    route = "M" + " L".join(f"{x},{y}" for x, y in trail)
    length = sum(((trail[i+1][0]-trail[i][0])**2 + (trail[i+1][1]-trail[i][1])**2) ** .5 for i in range(len(trail)-1))
    body = (f'<defs><clipPath id="m"><path d="{sil_d}"/></clipPath></defs>'
            f'<path d="{sil_d}" fill="{c["hill"]}" fill-opacity=".035"/>'
            f'<g clip-path="url(#m)" stroke="{c["line"]}" stroke-width="1" opacity=".55">{bands}</g>'
            f'<path d="{route}" fill="none" stroke="{c["accent"]}" stroke-width="2.2" stroke-linejoin="round" '
            f'stroke-linecap="round" class="route" style="stroke-dasharray:{length:.0f};stroke-dashoffset:{length:.0f}"/>'
            f'<path d="M{pts[-1][0]},{pts[-1][1]} L{between[-1][0][0]},{between[-1][0][1]} L{between[-1][1][0]},{between[-1][1][1]} L{summit[0]},{summit[1]}" fill="none" stroke="{c["sub"]}" '
            f'stroke-width="1.6" stroke-dasharray="3 5"/>')
    for i, ((yr, role, org), (x, y)) in enumerate(zip(STOPS, pts)):
        right = x - 14
        body += (f'<circle cx="{x}" cy="{y}" r="5.5" fill="{c["accent"]}"/>'
                 f'<circle cx="{x}" cy="{y}" r="2.2" fill="{c["faint"]}"/>'
                 f'<text text-anchor="end" font-family="{SANS}" fill="{c["sub"]}">'
                 f'<tspan x="{right}" y="{y-50}" font-weight="700" font-size="12.5" fill="{c["accent"]}">{yr}</tspan>'
                 f'<tspan x="{right}" y="{y-31}" font-family="{DISPLAY}" font-weight="600" font-size="16" fill="{c["ink"]}">{html.escape(role)}</tspan>'
                 f'<tspan x="{right}" y="{y-13}" font-size="13">{html.escape(org)}</tspan></text>')
    sx, sy = summit
    body += (f'<path d="M{sx-7},{sy+6} L{sx},{sy-6} L{sx+7},{sy+6} Z" fill="none" stroke="{c["sub"]}" stroke-width="1.4" stroke-linejoin="round"/>'
             f'<text x="{sx-16}" y="{sy-6}" text-anchor="end" font-family="{SANS}" font-size="13" fill="{c["sub"]}">'
             f'<tspan font-weight="700" fill="{c["ink"]}">Next:</tspan> open to new roles</text>')
    css = (".route{animation:climb 2.4s cubic-bezier(.4,0,.2,1) .2s forwards}"
           "@keyframes climb{to{stroke-dashoffset:0}}"
           "@media (prefers-reduced-motion:reduce){.route{animation:none;stroke-dashoffset:0!important}}")
    label = "Career route: " + "; ".join(f"{y} {r}, {o}" for y, r, o in STOPS) + "; next, open to new roles."
    return svg(W, H, label, body, css, fonts=("display", "sans", "sansbold"))


# ---------------------------------------------------------------- stats

def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-builder",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        sys.exit("GitHub API error: " + json.dumps(payload["errors"], indent=2))
    return payload["data"]


CAL = "contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }"


def fetch(token, login):
    q1 = f"""query($login: String!) {{ user(login: $login) {{
      createdAt
      repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {{
        totalCount nodes {{ stargazerCount
          languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{ edges {{ size node {{ name }} }} }} }} }}
      recent: contributionsCollection {{ {CAL} }} }} }}"""
    d = gql(token, q1, {"login": login})["user"]
    first = int(d["createdAt"][:4])
    now = dt.datetime.now(dt.timezone.utc)
    parts = []
    for y in range(first, now.year + 1):
        end = f"{y}-12-31T23:59:59Z" if y < now.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")
        parts.append(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{end}") {{ {CAL} }}')
    q2 = "query($login: String!) { user(login: $login) { " + " ".join(parts) + " } }"
    years = gql(token, q2, {"login": login})["user"]
    return d, years, first


def summarise(d, years, first):
    days = {}
    total = 0
    for key, coll in years.items():
        cal = coll["contributionCalendar"]
        total += cal["totalContributions"]
        for w in cal["weeks"]:
            for day in w["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
    recent = d["recent"]["contributionCalendar"]
    for w in recent["weeks"]:
        for day in w["contributionDays"]:
            days[day["date"]] = day["contributionCount"]
    longest = run = 0
    for date in sorted(days):
        run = run + 1 if days[date] > 0 else 0
        longest = max(longest, run)
    today = dt.date.today()
    cur, probe = 0, today
    if days.get(probe.isoformat(), 0) == 0:
        probe -= dt.timedelta(days=1)
    while days.get(probe.isoformat(), 0) > 0:
        cur += 1
        probe -= dt.timedelta(days=1)
    langs = {}
    skip = {"HTML", "CSS", "SCSS", "Less", "MDX"}
    for repo in d["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            if n not in skip:
                langs[n] = langs.get(n, 0) + e["size"]
    weeks = [[(x["date"], x["contributionCount"]) for x in w["contributionDays"]] for w in recent["weeks"]]
    return dict(total=total, since=first, year=recent["totalContributions"], longest=longest,
                current=cur, repos=d["repositories"]["totalCount"], langs=langs, weeks=weeks)


def mock():
    random.seed(7)
    start = dt.date.today() - dt.timedelta(days=dt.date.today().weekday() + 1 + 52 * 7)
    weeks = []
    for w in range(53):
        week = []
        for i in range(7):
            day = start + dt.timedelta(days=w * 7 + i)
            if day > dt.date.today():
                continue
            busy = 0.35 + 0.5 * (w > 44)
            week.append((day.isoformat(), random.choice([0, 0, 1, 2, 3, 5, 8, 12]) if random.random() < busy else 0))
        weeks.append(week)
    return dict(total=3676, since=2020, year=1938, longest=13, current=4, repos=41, weeks=weeks,
                langs={"Python": 504, "JavaScript": 209, "TypeScript": 153, "Astro": 58, "Shell": 57, "C++": 20})


def stats(theme, s):
    c = PALETTE[theme]
    body = ""
    figures = [(f"{s['total']:,}", f"contributions since {s['since']}"),
               (f"{s['year']:,}", "in the last twelve months"),
               (f"{s['longest']}", "days, longest streak"),
               (f"{s['repos']}", "public repositories")]
    for i, (num, lab) in enumerate(figures):
        x = i * 222
        body += (f'<text x="{x}" y="38" font-family="{DISPLAY}" font-weight="600" font-size="34" fill="{c["ink"]}">{num}</text>'
                 f'<text x="{x+1}" y="62" font-family="{SANS}" font-size="13.5" fill="{c["sub"]}">{lab}</text>')
    # calendar
    top, cell, gap = 112, 13, 3
    counts = sorted(v for wk in s["weeks"] for _, v in wk if v > 0)
    def q(p):
        return counts[min(len(counts) - 1, int(p * len(counts)))] if counts else 1
    cuts = [q(.25), q(.5), q(.75)]
    def level(v):
        if v <= 0:
            return 0
        return 1 + sum(v > t for t in cuts)
    last_label = -9
    for wi, wk in enumerate(s["weeks"]):
        x = wi * (cell + gap)
        if wk:
            d0 = dt.date.fromisoformat(wk[0][0])
            if (wi == 0 or d0.day <= 7) and wi - last_label >= 3:
                body += (f'<text x="{x}" y="{top-10}" font-family="{SANS}" font-size="11.5" '
                         f'fill="{c["sub"]}">{d0.strftime("%b")}</text>')
                last_label = wi
        for date, v in wk:
            row = (dt.date.fromisoformat(date).weekday() + 1) % 7
            body += (f'<rect x="{x}" y="{top + row*(cell+gap)}" width="{cell}" height="{cell}" rx="2.5" '
                     f'fill="{c["ramp"][level(v)]}"><title>{v} on {date}</title></rect>')
    cal_bottom = top + 7 * (cell + gap)
    lx = W - 5 * (cell + gap) - 40
    body += f'<text x="{lx-8}" y="{cal_bottom+20}" text-anchor="end" font-family="{SANS}" font-size="11.5" fill="{c["sub"]}">Less</text>'
    for i in range(5):
        body += f'<rect x="{lx + i*(cell+gap)}" y="{cal_bottom+9}" width="{cell}" height="{cell}" rx="2.5" fill="{c["ramp"][i]}"/>'
    body += f'<text x="{lx + 5*(cell+gap) + 4}" y="{cal_bottom+20}" font-family="{SANS}" font-size="11.5" fill="{c["sub"]}">More</text>'
    cur = s["current"]
    note = f"Current streak: {cur} day{'s' if cur != 1 else ''}" if cur else "No current streak"
    body += f'<text x="0" y="{cal_bottom+20}" font-family="{SANS}" font-size="11.5" fill="{c["sub"]}">{note}</text>'
    # languages
    ly = cal_bottom + 58
    total = sum(s["langs"].values()) or 1
    top_langs = sorted(s["langs"].items(), key=lambda kv: -kv[1])[:5]
    other = total - sum(v for _, v in top_langs)
    items = top_langs + ([("Other", other)] if other / total > 0.005 else [])
    x = 0
    body += f'<clipPath id="bar"><rect x="0" y="{ly}" width="{W}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">'
    for i, (name, v) in enumerate(items):
        w = W * v / total
        body += f'<rect x="{x:.1f}" y="{ly}" width="{w+0.5:.1f}" height="8" fill="{c["langs"][i]}"/>'
        x += w
    body += "</g>"
    x = 0
    for i, (name, v) in enumerate(items):
        pct = f"{100*v/total:.0f}%"
        label = f"{name} {pct}"
        body += (f'<circle cx="{x+5}" cy="{ly+31}" r="4.5" fill="{c["langs"][i]}"/>'
                 f'<text x="{x+15}" y="{ly+36}" font-family="{SANS}" font-size="13.5" fill="{c["ink"]}">{html.escape(name)}'
                 f'<tspan fill="{c["sub"]}"> {pct}</tspan></text>')
        x += 15 + text_width(label, 13.5) + 26
    H = ly + 64
    stamp = dt.date.today().strftime("%-d %b %Y")
    body += (f'<text x="{W}" y="{H-6}" text-anchor="end" font-family="{SANS}" font-size="11" '
             f'fill="{c["sub"]}">Public repositories, by code size. Updated {stamp}.</text>')
    label = (f"{s['total']} contributions since {s['since']}, {s['year']} in the last twelve months, "
             f"longest streak {s['longest']} days, {s['repos']} public repositories. Top languages: "
             + ", ".join(f"{n} {100*v/total:.0f}%" for n, v in items))
    return svg(W, H, label, body, fonts=("display", "sans"))


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for t in PALETTE:
        write(f"hero-{t}.svg", hero(t))
        write(f"journey-{t}.svg", journey(t))
    if "--mock" in sys.argv:
        s = mock()
    else:
        token, login = os.environ.get("GH_TOKEN"), os.environ.get("GH_USER", "missionshrestha")
        if not token:
            print("GH_TOKEN not set; skipping live stats (use --mock for a preview).")
            return
        s = summarise(*fetch(token, login))
    for t in PALETTE:
        write(f"stats-{t}.svg", stats(t, s))


if __name__ == "__main__":
    main()
