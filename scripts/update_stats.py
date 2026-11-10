#!/usr/bin/env python3
"""Daily stats updater for this GitHub profile README.
Pulls live numbers from LeetCode (public GraphQL), GeeksforGeeks (public
profile page) and GitHub (public REST API), then rewrites the numbers in
README.md and the SVG cards in assets/. Each source is independent: if one
fails, the others still update. No change is better than a wrong number."""
import json, os, re, sys, urllib.request

LC_USER = "Aryanmouli"
GFG_USER = "aryanmov1z0"
GH_USER = "Aryanch1"
FONT_S = "'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif"
LANG_COLORS = {"JavaScript": "#f1e05a", "CSS": "#a074c4", "HTML": "#e34c26",
               "Python": "#3572A5", "Java": "#b07219", "Dart": "#00B4AB",
               "TypeScript": "#3178c6", "Other": "#8b949e"}

def fetch(url, data=None):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
               "Content-Type": "application/json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def leetcode():
    q = {"query": 'query { matchedUser(username: "%s") { submitStats { acSubmissionNum { difficulty count } } } }' % LC_USER}
    d = json.loads(fetch("https://leetcode.com/graphql", json.dumps(q).encode()))
    nums = {row["difficulty"]: row["count"] for row in d["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]}
    return nums["All"], nums["Easy"], nums["Medium"], nums["Hard"]

def geeksforgeeks():
    html = fetch("https://www.geeksforgeeks.org/profile/" + GFG_USER)
    solved = int(re.search(r"problems_solved\D{0,4}(\d+)", html).group(1))
    score = int(re.search(r"score\D{0,4}(\d+)", html).group(1))
    rank = int(re.search(r"rank\D{0,4}(\d+)", html).group(1))
    return solved, score, rank

def github():
    user = json.loads(fetch("https://api.github.com/users/" + GH_USER))
    repos = json.loads(fetch("https://api.github.com/users/" + GH_USER + "/repos?per_page=100"))
    stars = sum(r["stargazers_count"] for r in repos)
    langs = {}
    for r in repos:
        try:
            d = json.loads(fetch("https://api.github.com/repos/%s/%s/languages" % (GH_USER, r["name"])))
            for k, v in d.items():
                langs[k] = langs.get(k, 0) + v
        except Exception:
            pass
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:5]
    top = [(k, round(100 * v / total, 1)) for k, v in top]
    return user["public_repos"], stars, user["followers"], top

def sub(path, pattern, repl):
    s = open(path, encoding="utf-8").read()
    s2 = re.sub(pattern, repl, s)
    if s2 != s:
        open(path, "w", encoding="utf-8").write(s2)
        return True
    return False

def by_id(path, el_id, value):
    return sub(path, r'(<text id="%s"[^>]*>)[^<]*(</text>)' % el_id,
               lambda m: m.group(1) + value + m.group(2))

def write_langs_card(top):
    rows = []
    for i, (name, pct) in enumerate(top):
        y = 78 + i * 22
        bw = int(300 * pct / 100)
        color = LANG_COLORS.get(name, "#8b949e")
        rows.append(
            '<text id="lang%dName" x="28" y="%d" font-family="%s" font-size="12.5" fill="#e6edf3">%s</text>\n'
            '  <rect x="140" y="%d" width="300" height="9" rx="4.5" fill="rgba(255,255,255,0.10)"/>\n'
            '  <rect id="lang%dBar" x="140" y="%d" width="%d" height="9" rx="4.5" fill="%s"/>\n'
            '  <text id="lang%dPct" x="452" y="%d" font-family="%s" font-size="12" fill="#a7b3c9">%s%%</text>'
            % (i + 1, y + 4, FONT_S, name, y - 6, i + 1, y - 6, bw, color, i + 1, y + 4, FONT_S, pct))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 190" width="500" height="190">\n'
           '  <defs>\n'
           '    <linearGradient id="lbg" x1="0%" y1="0%" x2="100%" y2="100%">\n'
           '      <stop offset="0%" stop-color="#131a2e"/><stop offset="100%" stop-color="#0d1117"/>\n'
           '    </linearGradient>\n'
           '    <linearGradient id="lgloss" x1="0%" y1="0%" x2="0%" y2="100%">\n'
           '      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.14"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>\n'
           '    </linearGradient>\n'
           '    <clipPath id="lclip"><rect width="500" height="190" rx="14"/></clipPath>\n'
           '  </defs>\n'
           '  <rect width="500" height="190" rx="14" fill="url(#lbg)"/>\n'
           '  <g clip-path="url(#lclip)"><rect width="500" height="86" fill="url(#lgloss)"/></g>\n'
           '  <rect x="1" y="1" width="498" height="188" rx="13" fill="none" stroke="rgba(255,255,255,0.30)" stroke-width="1.4"/>\n'
           '  <text x="28" y="46" font-family="Georgia, \'Times New Roman\', serif" font-size="24" font-weight="700" fill="#ffffff">Top Languages</text>\n'
           '  <text x="28" y="66" font-family="' + FONT_S + '" font-size="12" fill="#8fb0ff">by code volume across my repos</text>\n'
           '  ' + '\n  '.join(rows) + '\n</svg>')
    old = None
    try:
        old = open("assets/gh-langs.svg", encoding="utf-8").read()
    except FileNotFoundError:
        pass
    if old != svg:
        open("assets/gh-langs.svg", "w", encoding="utf-8").write(svg)
        return True
    return False


# Per-day problems SOLVED on GeeksforGeeks, read from the Coding Score tab's
# Month-view charts in the signed-in profile on 2026-11-09 (each month sums
# exactly to the total the page states). Per-day GFG data needs a signed-in
# session, so the series is embedded here and the card's heatmap is
# re-rendered from it; the card's stats above still update live.
GFG_SOLVED = {}


def _gfg_fill(year, month, default, overrides=None):
    import calendar
    from datetime import date

    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        GFG_SOLVED[date(year, month, day)] = (overrides or {}).get(day, default)


_gfg_fill(2026, 6, 1, {3: 2})
_gfg_fill(2026, 7, 1, {2: 0, 11: 0, 12: 0, 13: 0, 20: 0, 22: 0})
_gfg_fill(2026, 8, 1)
_gfg_fill(2026, 9, 1, {10: 0, 16: 0})
_gfg_fill(2026, 10, 0, {d: 1 for d in [5, 6, 7, 8, 9, 11, 12, 13, 14, 21, 26, 27, 28]})
for _d in range(1, 10):
    from datetime import date as _date

    GFG_SOLVED[_date(2026, 11, _d)] = {4: 1, 5: 1, 9: 5}.get(_d, 0)


def gfg_heat_cells():
    from datetime import date, timedelta

    def color(n):
        return "#1c2b21" if n == 0 else "#26a641" if n == 1 else "#39d353"

    cells, d = [], date(2026, 6, 21)
    end = date(2026, 11, 9)
    while d <= end:
        col = (d - date(2026, 6, 21)).days // 7
        row = (d.weekday() + 1) % 7
        cells.append('<rect x="%.1f" y="%.1f" width="12" height="12" rx="2.5" fill="%s"/>' % (
            318 + col * 15.4, 52 + row * 15.4, color(GFG_SOLVED.get(d, 0))))
        d += timedelta(days=1)
    return "\n    " + "\n    ".join(cells) + "\n  "

def main():
    changed = False
    lc = gfg = None
    try:
        lc = leetcode()
    except Exception as e:
        print("leetcode fetch failed:", e)
    try:
        gfg = geeksforgeeks()
    except Exception as e:
        print("gfg fetch failed:", e)
    if lc and gfg:
        lc_total, lc_e, lc_m, lc_h = lc
        gfg_total, gfg_score, gfg_rank = gfg
        combined = lc_total + gfg_total
        changed |= sub("README.md", r"LeetCode-Aryanmouli%20%C2%B7%20\d+%20solved",
                       "LeetCode-Aryanmouli%20%C2%B7%20" + str(lc_total) + "%20solved")
        changed |= sub("README.md", r"GeeksforGeeks-aryanmov1z0%20%C2%B7%20\d+%20solved",
                       "GeeksforGeeks-aryanmov1z0%20%C2%B7%20" + str(gfg_total) + "%20solved")
        changed |= sub("README.md", r"LeetCode \(\d+\) and GeeksforGeeks \(\d+\)",
                       "LeetCode (%d) and GeeksforGeeks (%d)" % (lc_total, gfg_total))
        changed |= sub("README.md", r"\*\*LeetCode:\*\* \d+ solved \(\d+ Easy . \d+ Medium . \d+ Hard\)",
                       "**LeetCode:** %d solved (%d Easy \u00b7 %d Medium \u00b7 %d Hard)" % (lc_total, lc_e, lc_m, lc_h))
        changed |= sub("README.md", r"\*\*GeeksforGeeks:\*\* \d+ solved . Coding Score \d+",
                       "**GeeksforGeeks:** %d solved \u00b7 Coding Score %d" % (gfg_total, gfg_score))
        changed |= by_id("assets/hl-dsa.svg", "dsaTotal", format(combined, ","))
        changed |= by_id("assets/hl-dsa.svg", "dsaSplit", "LeetCode %d &#183; GFG %d" % (lc_total, gfg_total))
        changed |= by_id("assets/hl-rank.svg", "gfgScore", "Coding Score %d" % gfg_score)
        changed |= sub("assets/badge-leetcode.svg", r'(<tspan id="lcBadgeCount">)[^<]*(</tspan>)',
                       lambda m: m.group(1) + str(lc_total) + m.group(2))
        changed |= sub("assets/badge-gfg.svg", r'(<tspan id="gfgBadgeCount">)[^<]*(</tspan>)',
                       lambda m: m.group(1) + str(gfg_total) + m.group(2))
        for el_id, val in (("gfgTotal", str(gfg_total)), ("gfgScore", str(gfg_score)),
                           ("gfgRank", "#" + str(gfg_rank))):
            changed |= sub("assets/gfg-card.svg", r'(<tspan id="%s"[^>]*>)[^<]*(</tspan>)' % el_id,
                           lambda m, v=val: m.group(1) + v + m.group(2))
        changed |= sub("assets/gfg-card.svg", r'(?s)(<g id="gfgHeat">).*?(</g>)',
                       lambda m: m.group(1) + gfg_heat_cells() + m.group(2))
        print("LC %d, GFG %d, combined %d" % (lc_total, gfg_total, combined))
    if lc:
        try:
            lc_total2, lc_e2, lc_m2, lc_h2 = lc
            q = {"query": 'query { matchedUser(username: "%s") { profile { ranking } submissionCalendar } }' % LC_USER}
            req = urllib.request.Request("https://leetcode.com/graphql", data=json.dumps(q).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            mu = json.loads(urllib.request.urlopen(req, timeout=30).read())["data"]["matchedUser"]
            for el_id, val in (("lcTotal", str(lc_total2)), ("lcEasy", str(lc_e2)), ("lcMed", str(lc_m2)),
                               ("lcHard", str(lc_h2)), ("lcRank", format(mu["profile"]["ranking"], ","))):
                changed |= sub("assets/lc-wide.svg", r'(<tspan id="%s"[^>]*>)[^<]*(</tspan>)' % el_id,
                               lambda m, v=val: m.group(1) + v + m.group(2))
            cal = json.loads(mu["submissionCalendar"])
            from datetime import datetime, timezone, timedelta
            colors = ["#232c47", "#0e4429", "#006d32", "#26a641", "#39d353"]
            def lvl(c):
                return 0 if c == 0 else 1 if c <= 2 else 2 if c <= 5 else 3 if c <= 9 else 4
            today = datetime.now(timezone.utc).date()
            cur = today - timedelta(days=139)
            x0, y0, cs, gap = 318, 52, 12, 3.4
            cells, col = [], 0
            while cur <= today:
                dow = (cur.weekday() + 1) % 7
                ts = str(int(datetime(cur.year, cur.month, cur.day, tzinfo=timezone.utc).timestamp()))
                cells.append('<rect x="%.1f" y="%.1f" width="12" height="12" rx="2.5" fill="%s"/>' % (
                    x0 + col * (cs + gap), y0 + dow * (cs + gap), colors[lvl(cal.get(ts, 0))]))
                if dow == 6:
                    col += 1
                cur += timedelta(days=1)
            changed |= sub("assets/lc-wide.svg", r'(?s)(<g id="lcHeat">).*?(</g>)',
                           lambda m: m.group(1) + "\n    " + "\n    ".join(cells) + "\n  " + m.group(2))
            print("lc-wide card + heatmap refreshed")
        except Exception as e:
            print("lc-wide update failed:", e)
    try:
        repos_n, stars, followers, top = github()
        changed |= by_id("assets/gh-stats.svg", "ghRepos", str(repos_n))
        changed |= by_id("assets/gh-stats.svg", "ghStars", str(stars))
        changed |= by_id("assets/gh-stats.svg", "ghFollowers", str(followers))
        changed |= write_langs_card(top)
        print("GitHub: %d repos, %d stars, %d followers, top lang %s" % (repos_n, stars, followers, top[0][0] if top else "-"))
    except Exception as e:
        print("github fetch failed:", e)
    print("changed =", changed)
    return 0

if __name__ == "__main__":
    sys.exit(main())
