#!/usr/bin/env python3
"""Daily DSA stats updater for this GitHub profile README.
Fetches live solved counts from LeetCode (public GraphQL) and GeeksforGeeks
(public profile page), then rewrites the numbers in README.md and in
assets/hl-dsa.svg / assets/hl-rank.svg. Exits quietly if a source fails:
no change is better than a wrong number."""
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
    return solved, score

def sub(path, pattern, repl, count=0):
    s = open(path, encoding="utf-8").read()
    s2 = re.sub(pattern, repl, s, count=count)
    if s2 != s:
        open(path, "w", encoding="utf-8").write(s2)
        return True
    return False

def main():
    try:
        lc_total, lc_e, lc_m, lc_h = leetcode()
        gfg_total, gfg_score = geeksforgeeks()
    except Exception as e:
        print("stats fetch failed, leaving files unchanged:", e)
        return 0
    combined = lc_total + gfg_total
    changed = False
    changed |= sub("README.md", r"LeetCode-Aryanmouli%20%C2%B7%20\d+%20solved",
                   f"LeetCode-Aryanmouli%20%C2%B7%20{lc_total}%20solved")
    changed |= sub("README.md", r"GeeksforGeeks-aryanmov1z0%20%C2%B7%20\d+%20solved",
                   f"GeeksforGeeks-aryanmov1z0%20%C2%B7%20{gfg_total}%20solved")
    changed |= sub("README.md", r"LeetCode \(\d+\) and GeeksforGeeks \(\d+\)",
                   f"LeetCode ({lc_total}) and GeeksforGeeks ({gfg_total})")
    changed |= sub("README.md", r"\*\*LeetCode:\*\* \d+ solved \(\d+ Easy · \d+ Medium · \d+ Hard\)",
                   f"**LeetCode:** {lc_total} solved ({lc_e} Easy · {lc_m} Medium · {lc_h} Hard)")
    changed |= sub("README.md", r"\*\*GeeksforGeeks:\*\* \d+ solved · Coding Score \d+",
                   f"**GeeksforGeeks:** {gfg_total} solved · Coding Score {gfg_score}")
    changed |= sub("assets/hl-dsa.svg", r'(<text id="dsaTotal"[^>]*>)[^<]*(</text>)',
                   rf"\g<1>{combined:,}\g<2>")
    changed |= sub("assets/hl-dsa.svg", r'(<text id="dsaSplit"[^>]*>)[^<]*(</text>)',
                   rf"\g<1>LeetCode {lc_total} &#183; GFG {gfg_total}\g<2>")
    changed |= sub("assets/hl-rank.svg", r'(<text id="gfgScore"[^>]*>)[^<]*(</text>)',
                   rf"\g<1>Coding Score {gfg_score}\g<2>")
    print(f"LeetCode {lc_total} (E{lc_e}/M{lc_m}/H{lc_h}), GFG {gfg_total} (score {gfg_score}), combined {combined}, changed={changed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
