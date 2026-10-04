"""Shared GitHub data helpers (stdlib only)."""
import json
import os
import urllib.request

QUERY = """query($login:String!){user(login:$login){
 createdAt followers{totalCount} following{totalCount}
 contributionsCollection{totalCommitContributions totalPullRequestContributions
  totalIssueContributions restrictedContributionsCount
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def _req(url, data=None):
    h = {"User-Agent": "profile-gen", "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    r = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(r, timeout=30) as f:
        return f.read()


def user_graph(login):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    out = json.loads(_req("https://api.github.com/graphql", body))
    if "errors" in out:
        raise SystemExit(f"graphql: {out['errors']}")
    return out["data"]["user"]


def days(user):
    """Flat chronological list of (date, count)."""
    wk = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(d["date"], d["contributionCount"]) for w in wk for d in w["contributionDays"]]


def streaks(ds):
    """(current, longest). Today with 0 contributions does not break a streak."""
    longest = run = 0
    for _, c in ds:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur = 0
    for i, (_, c) in enumerate(reversed(ds)):
        if c:
            cur += 1
        elif i != 0:
            break
    return cur, longest


def repos(login):
    out, page = [], 1
    while True:
        b = json.loads(_req(f"https://api.github.com/users/{login}/repos?per_page=100&page={page}"))
        out += b
        if len(b) < 100:
            return [r for r in out if not r["fork"]]
        page += 1
