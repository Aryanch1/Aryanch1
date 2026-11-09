#!/usr/bin/env python3
"""Daily DSA stats updater for this GitHub profile README.
Fetches live solved counts from LeetCode (public GraphQL) and GeeksforGeeks
(public profile page), then rewrites the numbers in README.md and in
assets/hl-dsa.svg, assets/hl-rank.svg and assets/gfg-card.svg.
Exits quietly if a source fails: no change is better than a wrong number."""
import json, re, sys, urllib.request

LC_USER = "Aryanmouli"
GFG_USER = "aryanmov1z0"

def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"})
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

def main():
    try:
        lc_total, lc_e, lc_m, lc_h = leetcode()
        gfg_total, gfg_score, gfg_rank = geeksforgeeks()
    except Exception as e:
        print("stats fetch failed, leaving files unchanged:", e)
        return 0
    combined = lc_total + gfg_total
    changed = False
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
    changed |= by_id("assets/gfg-card.svg", "gfgTotal", str(gfg_total))
    changed |= by_id("assets/gfg-card.svg", "gfgScore", str(gfg_score))
    changed |= by_id("assets/gfg-card.svg", "gfgRank", "#" + str(gfg_rank))
    print("LeetCode %d (E%d/M%d/H%d), GFG %d (score %d, rank %d), combined %d, changed=%s"
          % (lc_total, lc_e, lc_m, lc_h, gfg_total, gfg_score, gfg_rank, combined, changed))
    return 0

if __name__ == "__main__":
    sys.exit(main())
