#!/usr/bin/env python3
"""Generate profile/stats.svg: the CyberJKD live GitHub activity card.

Runs inside GitHub Actions (stdlib only). Every number comes straight from
your GitHub account via the GraphQL API, using the workflow's own token.
No third-party widget servers, nothing to rate-limit or go down.

If the API call fails, the script exits non-zero WITHOUT touching the
existing SVG, so the profile keeps showing the last good card (no gaps).

Usage:
  GITHUB_TOKEN=... python scripts/generate_stats.py
  python scripts/generate_stats.py --demo      # fake numbers, for previewing
"""
import base64, datetime as dt, json, os, sys, time, urllib.request

USER = os.environ.get("STATS_USER", "DallaSamuel")
OUT, LOGO = "profile/stats.svg", "profile/logo.jpg"
SANS = "Segoe UI,Helvetica,Arial,sans-serif"

QUERY = """
query($login:String!){ user(login:$login){
  repositories(privacy:PUBLIC, ownerAffiliation:OWNER){ totalCount }
  contributionsCollection{
    totalCommitContributions
    contributionCalendar{ totalContributions
      weeks{ contributionDays{ date contributionCount } } }
  }
}}"""


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
        "Content-Type": "application/json", "User-Agent": "cyberjkd-stats"})
    last = None
    for attempt in range(4):                       # retry so a blip never leaves a gap
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            u = (d.get("data") or {}).get("user")
            if not u:
                raise RuntimeError(d.get("errors") or "no user in response")
            return u
        except Exception as e:                     # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"GitHub API failed, keeping the previous card: {last}")


def demo():
    today, weeks = dt.date.today(), []
    for w in range(52):
        weeks.append({"contributionDays": [
            {"date": (today - dt.timedelta(days=(51 - w) * 7 + (6 - d))).isoformat(),
             "contributionCount": ((w * 3 + d * 5) % 6 if (w + d) % 3 else 0)} for d in range(7)]})
    n = sum(x["contributionCount"] for w in weeks for x in w["contributionDays"])
    return {"repositories": {"totalCount": 9}, "contributionsCollection": {
        "totalCommitContributions": 180,
        "contributionCalendar": {"totalContributions": n, "weeks": weeks}}}


def summarize(u):
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    today = dt.date.today().isoformat()
    days = [x for w in cal["weeks"] for x in w["contributionDays"] if x["date"] <= today]
    active = sum(1 for x in days if x["contributionCount"] > 0)
    longest = run = 0
    for x in days:
        run = run + 1 if x["contributionCount"] > 0 else 0
        longest = max(longest, run)
    weekly = []
    for w in cal["weeks"][-12:]:
        ds = [x for x in w["contributionDays"] if x["date"] <= today]
        weekly.append((w["contributionDays"][0]["date"], sum(x["contributionCount"] for x in ds)))
    return {"repos": u["repositories"]["totalCount"], "contribs": cal["totalContributions"],
            "commits": cc["totalCommitContributions"], "active": active, "longest": longest, "weekly": weekly}


def svg(s):
    W, H = 840, 306
    logo = base64.b64encode(open(LOGO, "rb").read()).decode()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tiles = [("PUBLIC REPOS", f'{s["repos"]:,}', "#00ffcc"),
             ("CONTRIBUTIONS · 12 MO", f'{s["contribs"]:,}', "#00aaff"),
             ("ACTIVE DAYS · 12 MO", f'{s["active"]:,}', "#00cc66"),
             ("LONGEST STREAK", f'{s["longest"]}d', "#ffcc00")]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="CyberJKD live GitHub activity: {s["contribs"]} contributions in the last 12 months">',
         '<defs><pattern id="g" width="44" height="44" patternUnits="userSpaceOnUse"><path d="M44 0H0V44" fill="none" '
         'stroke="#00aaff" stroke-opacity=".05"/></pattern><clipPath id="c"><circle cx="64" cy="54" r="30"/></clipPath>'
         '<linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="#00aaff" stop-opacity="0"/>'
         '<stop offset=".5" stop-color="#00aaff"/><stop offset="1" stop-color="#00aaff" stop-opacity="0"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="10" fill="#0a1020"/><rect width="{W}" height="{H}" rx="10" fill="url(#g)"/>',
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="#1a2a4a"/>',
         f'<image href="data:image/jpeg;base64,{logo}" x="34" y="24" width="60" height="60" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice"/>',
         '<circle cx="64" cy="54" r="30" fill="none" stroke="#00ffcc" stroke-opacity=".3"/>',
         f'<text x="112" y="40" font-family="{SANS}" font-size="11" font-weight="600" letter-spacing="3" fill="#00aaff">CyberJKD</text>',
         '<text x="112" y="72" font-family="Georgia,Cambria,serif" font-size="28" font-weight="700" fill="#ffffff">Live GitHub Activity</text>',
         f'<text x="{W-24}" y="40" text-anchor="end" font-family="{SANS}" font-size="11" fill="#4a6080">Updated {stamp}</text>',
         f'<rect x="{W/2-90}" y="100" width="180" height="1" fill="url(#hl)"/>']
    tw, gap, x0, y0, th = 189, 14, 24, 114, 70
    for i, (label, val, color) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        o += [f'<rect x="{x}" y="{y0}" width="{tw}" height="{th}" rx="8" fill="#080d1a" stroke="#1a2a4a"/>',
              f'<text x="{x+tw/2}" y="{y0+37}" text-anchor="middle" font-family="{SANS}" font-size="28" font-weight="800" fill="{color}">{val}</text>',
              f'<text x="{x+tw/2}" y="{y0+57}" text-anchor="middle" font-family="{SANS}" font-size="10" letter-spacing="1" fill="#4a6080">{label}</text>']
    o.append(f'<text x="24" y="212" font-family="{SANS}" font-size="11" font-weight="700" letter-spacing="2" fill="#4a6080">LAST 12 WEEKS</text>')
    mx = max([c for _, c in s["weekly"]] + [1])
    n = len(s["weekly"])
    slot = (W - 48) / n
    bw, base, maxh = slot - 14, 290, 38
    for i, (date, c) in enumerate(s["weekly"]):
        x = 24 + i * slot + 7
        h = max(2, round(c / mx * maxh))
        lab = dt.date.fromisoformat(date).strftime("%b %-d")
        o += [f'<rect x="{x:.1f}" y="{base-14-h}" width="{bw:.1f}" height="{h}" rx="3" fill="#00aaff" fill-opacity="{0.3 + 0.7*c/mx:.2f}"/>',
              f'<text x="{x+bw/2:.1f}" y="{base-18-h}" text-anchor="middle" font-family="{SANS}" font-size="10" fill="#c8d8f0">{c}</text>',
              f'<text x="{x+bw/2:.1f}" y="{base}" text-anchor="middle" font-family="{SANS}" font-size="9" fill="#2a4060">{lab}</text>']
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    card = svg(summarize(demo() if "--demo" in sys.argv else fetch()))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(card)
    print("wrote", OUT)
