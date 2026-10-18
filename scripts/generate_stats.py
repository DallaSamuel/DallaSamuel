#!/usr/bin/env python3
"""Generate profile/stats.svg: the CyberJKD live terminal (borderless, transparent).

Runs inside GitHub Actions (stdlib only). Every number comes straight from
your GitHub account via the GraphQL API, using the workflow's own token.
No third-party widget servers, nothing to rate-limit or go down.

Card contents (all real data):
  * 4 headline numbers (repos, 12-month contributions, active days, streak)
  * Latest activity feed: your most recent commit message per repo
  * 26-week contribution heatmap
  * Rotating status line + LIVE badge + animation (pure SVG/CSS, no JS)

Safety: the headline query is strict (failure keeps the previous card). The
activity feed is a separate, lenient query: if it ever fails, the card still
renders with a weekly bar chart instead. Nothing is written on a hard failure.

Usage:
  GITHUB_TOKEN=... python scripts/generate_stats.py
  python scripts/generate_stats.py --demo      # fake data, for previewing
  python scripts/generate_stats.py --demo --nofeed   # preview the fallback
"""
import base64, datetime as dt, html, json, os, sys, time, urllib.request

USER = os.environ.get("STATS_USER", "DallaSamuel")
OUT = "profile/stats.svg"
SANS = "Segoe UI,Helvetica,Arial,sans-serif"
MONO = "Consolas,Menlo,Monaco,monospace"

STATS_QUERY = """
query($login:String!){ user(login:$login){
  repositories(privacy:PUBLIC, ownerAffiliations:OWNER){ totalCount }
  contributionsCollection{
    contributionCalendar{ totalContributions
      weeks{ contributionDays{ date contributionCount } } }
  }
}}"""

FEED_QUERY = """
query($login:String!){ user(login:$login){
  repositories(first:8, privacy:PUBLIC, ownerAffiliations:OWNER,
               orderBy:{field:PUSHED_AT, direction:DESC}){
    nodes{ name defaultBranchRef{ target{ ... on Commit{
      history(first:10){ nodes{ messageHeadline committedDate author{ user{ login } } } }
    } } } }
  }
}}"""

STATS_QUERY = """
query($login:String!){ user(login:$login){
  repositories(privacy:PUBLIC, ownerAffiliations:OWNER){ totalCount }
  contributionsCollection{
    contributionCalendar{ totalContributions
      weeks{ contributionDays{ date contributionCount } } }
  }
}}"""

FEED_QUERY = """
query($login:String!){ user(login:$login){
  repositories(first:8, privacy:PUBLIC, ownerAffiliations:OWNER,
               orderBy:{field:PUSHED_AT, direction:DESC}){
    nodes{ name defaultBranchRef{ target{ ... on Commit{
      history(first:10){ nodes{ messageHeadline committedDate author{ user{ login } } } }
    } } } }
  }
}}"""

def gql(query, strict=True):
    body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
        "Content-Type": "application/json", "User-Agent": "cyberjkd-stats"})
    last = None
    for attempt in range(4 if strict else 2):     # retry so a blip never leaves a gap
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            if d.get("errors") and not d.get("data"):
                last = d["errors"]
                break                              # query problem: retrying won't help
            if not (d.get("data") or {}).get("user"):
                raise RuntimeError(d.get("errors") or "no user in response")
            return d["data"]["user"]
        except Exception as e:                     # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    if strict:
        raise SystemExit(f"GitHub API failed, keeping the previous card: {last}")
    print(f"warning: optional query failed, using fallback layout: {last}")
    return None


def parse_feed(u, me):
    items = []
    for repo in u["repositories"]["nodes"]:
        tgt = (repo.get("defaultBranchRef") or {}).get("target") or {}
        for c in (tgt.get("history") or {}).get("nodes", []):
            login = ((c.get("author") or {}).get("user") or {}).get("login")
            if login and login.lower() == me.lower():     # skip bot commits
                items.append({"repo": repo["name"], "msg": c["messageHeadline"], "when": c["committedDate"]})
                break
    items.sort(key=lambda x: x["when"], reverse=True)
    return items[:4]


def demo_data(nofeed=False):
    today, weeks = dt.date.today(), []
    for w in range(52):
        weeks.append({"contributionDays": [
            {"date": (today - dt.timedelta(days=(51 - w) * 7 + (6 - d))).isoformat(),
             "contributionCount": ((w * 3 + d * 5) % 6 if (w + d) % 3 else 0)} for d in range(7)]})
    n = sum(x["contributionCount"] for w in weeks for x in w["contributionDays"])
    stats = {"repositories": {"totalCount": 9}, "contributionsCollection": {
        "contributionCalendar": {"totalContributions": n, "weeks": weeks}}}
    now = dt.datetime.now(dt.timezone.utc)
    feed = [] if nofeed else [
        {"repo": "DallaSamuel", "msg": "Update README.md", "when": (now - dt.timedelta(hours=2)).isoformat()},
        {"repo": "CyberJKD-Roadmap", "msg": "Mark Phase 06 lab 03 complete", "when": (now - dt.timedelta(hours=30)).isoformat()},
        {"repo": "CyberJKD-Labs", "msg": "Add Hardened NTFS File Server write-up", "when": (now - dt.timedelta(days=4)).isoformat()},
        {"repo": "linux-hardening-script", "msg": "Fix port audit report formatting", "when": (now - dt.timedelta(days=9)).isoformat()}]
    return stats, feed


def summarize(u, feed):
    cal = u["contributionsCollection"]["contributionCalendar"]
    today = dt.date.today().isoformat()
    days = [x for w in cal["weeks"] for x in w["contributionDays"] if x["date"] <= today]
    longest = run = 0
    for x in days:
        run = run + 1 if x["contributionCount"] > 0 else 0
        longest = max(longest, run)
    last = max((x["date"] for x in days if x["contributionCount"] > 0), default=None)
    heat = [[x["contributionCount"] for x in w["contributionDays"] if x["date"] <= today] for w in cal["weeks"][-26:]]
    weekly = [(w["contributionDays"][0]["date"], sum(x["contributionCount"] for x in w["contributionDays"] if x["date"] <= today))
              for w in cal["weeks"][-8:]]
    return {"repos": u["repositories"]["totalCount"], "contribs": cal["totalContributions"],
            "active": sum(1 for x in days if x["contributionCount"] > 0), "longest": longest,
            "last": last, "heat": heat, "weekly": weekly, "feed": feed}


def ago(iso):
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = (dt.datetime.now(dt.timezone.utc) - t).total_seconds()
    if s < 3600:
        return f"{max(1, int(s // 60))}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return t.strftime("%b %-d")


def day(iso):
    """Absolute date (never goes stale between 6-hourly refreshes)."""
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %-d")


def clip(t, n):
    t = " ".join(t.split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def esc(t):
    return html.escape(t, quote=True)



# ---------------------------------------------------------------- terminal
# Borderless + transparent: the text sits directly on the README page.
# Mid-tone colors so it stays readable on both GitHub's light and dark themes.
T = 24.0            # seconds per loop
CW = 7.8            # px per monospace char at 13px (each typed char is placed absolutely)
GREEN, BLUE, TEAL, AMBER = "#2da44e", "#388bfd", "#12a594", "#d29922"
TXT, DIM = "#768390", "#8b949e"
SPARK = "▁▂▃▄▅▆▇█"
W, H = 620, 372


def spark(counts):
    mx = max(counts + [1])
    return "".join(SPARK[0 if c == 0 else min(7, max(1, round(c / mx * 7)))] for c in counts)


def build_terminal(s):
    P = lambda t: f"{t / T * 100:.3f}"
    kf, els = [], []
    n_id = [0]

    def nid():
        n_id[0] += 1
        return n_id[0]

    def fade(content, t):                      # appears at t, fades near loop end
        i = nid()
        kf.append(f"@keyframes o{i}{{0%,{P(t)}%{{opacity:0}}{P(t+.2)}%,{P(T-2.4)}%{{opacity:1}}{P(T-1.8)}%,100%{{opacity:0}}}}")
        els.append(f'<g style="animation:o{i} {T}s linear infinite">{content}</g>')

    def prompt_text(y):
        return (f'<text x="24" y="{y}" textLength="{18*CW:.1f}" font-family="{MONO}" font-size="13" xml:space="preserve">'
                f'<tspan fill="{GREEN}" font-weight="700">dalla@cyberjkd</tspan><tspan fill="{TXT}">:</tspan>'
                f'<tspan fill="{BLUE}" font-weight="700">~</tspan><tspan fill="{TXT}">$ </tspan></text>')

    def typed(y, t0, cmd):
        n, x0 = len(cmd), 24 + 18 * CW
        ts, step = t0 + .3, .065
        fade(prompt_text(y), t0)
        for k, ch in enumerate(cmd):               # one element per char: reveal without any cover/frame
            if ch == " ":
                continue
            i = nid()
            tc = ts + k * step
            kf.append(f"@keyframes k{i}{{0%,{P(tc)}%{{opacity:0}}{P(tc+.012)}%,{P(T-2.4)}%{{opacity:1}}{P(T-1.8)}%,100%{{opacity:0}}}}")
            els.append(f'<text style="animation:k{i} {T}s linear infinite" x="{x0 + k*CW:.1f}" y="{y}" font-family="{MONO}" '
                       f'font-size="13" font-weight="600" fill="{TXT}">{esc(ch)}</text>')
        te = ts + n * step
        i = nid()                                  # cursor that follows the typing
        kf.append(f"@keyframes t{i}{{0%,{P(ts)}%{{transform:translateX(0);animation-timing-function:steps({n},end)}}{P(te)}%,100%{{transform:translateX({n*CW:.1f}px)}}}}")
        kf.append(f"@keyframes c{i}{{0%,{P(ts-.05)}%{{opacity:0}}{P(ts)}%,{P(te+.45)}%{{opacity:1}}{P(te+.5)}%,100%{{opacity:0}}}}")
        els.append(f'<g style="animation:t{i} {T}s linear infinite"><rect class="cur" style="animation:c{i} {T}s linear infinite" '
                   f'x="{x0:.1f}" y="{y-12}" width="7" height="15" fill="{TEAL}"/></g>')
        return te

    t = 0.6
    te = typed(58, t, "whoami")                                         # 1
    t = te + .35
    fade(f'<text x="46" y="78" font-family="{MONO}" font-size="13" font-weight="600" fill="{TXT}">CyberJKD  ·  IT Support  ·  Windows &amp; Active Directory  ·  Azure</text>', t)
    t += .9
    te = typed(108, t, "stats --last 12mo")                              # 2
    t = te + .4
    last = dt.date.fromisoformat(s["last"]).strftime("%b %-d") if s["last"] else "n/a"
    rows = [("public_repos", f'{s["repos"]}', TEAL, ""),
            ("contributions", f'{s["contribs"]:,}', BLUE, "last 12 months"),
            ("active_days", f'{s["active"]}', GREEN, f"last contribution {last}"),
            ("longest_streak", f'{s["longest"]}', AMBER, "days"),
            ("weekly_activity", "", TEAL, "last 26 weeks")]
    for k, (lab, val, col, note) in enumerate(rows):
        y = 128 + k * 20
        if lab == "weekly_activity":              # thin pencil lines, one per week
            counts = [sum(w) for w in s["heat"]]
            mxw = max(counts + [1])
            pitch = 5.6                           # distance between lines (smaller = closer)
            parts = [f'<line x1="213" x2="{213 + len(counts) * pitch:.1f}" y1="{y+3}" y2="{y+3}" stroke="{DIM}" stroke-opacity=".3" stroke-width="1"/>']
            for j, c in enumerate(counts):
                x = 214 + j * pitch + 1.2
                if c == 0:
                    parts.append(f'<circle cx="{x:.1f}" cy="{y+1.5}" r="0.9" fill="{DIM}" fill-opacity=".55"/>')
                else:
                    h = max(4, round(c / mxw * 16))
                    op = 0.45 + 0.55 * c / mxw    # busier weeks are brighter
                    parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y+2}" y2="{y+2-h}" stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="2" stroke-linecap="round"/>')
            valel, valw = "".join(parts), len(counts) * pitch
        else:
            valel = f'<text x="214" y="{y}" font-family="{MONO}" font-size="13" font-weight="800" fill="{col}">{esc(val)}</text>'
            valw = max(len(val), 3) * CW
        extra = (f'<text x="{214 + valw + 14:.0f}" y="{y}" font-family="{MONO}" font-size="12" fill="{DIM}">{esc(note)}</text>') if note else ""
        fade(f'<text x="46" y="{y}" font-family="{MONO}" font-size="13" fill="{DIM}">{lab}</text>{valel}{extra}', t)
        t += .35
    t += .6
    if s["feed"]:                                                       # 3
        te = typed(238, t, "git log --oneline -4")
        t = te + .4
        for k, it in enumerate(s["feed"]):
            y = 258 + k * 20
            fade(f'<text x="46" y="{y}" font-family="{MONO}" font-size="12" fill="{DIM}">[{esc(day(it["when"]))}]</text>'
                 f'<text x="118" y="{y}" font-family="{MONO}" font-size="13" font-weight="800" fill="{TEAL}">{esc(clip(it["repo"], 22))}</text>'
                 f'<text x="308" y="{y}" font-family="{MONO}" font-size="13" font-weight="600" fill="{TXT}">{esc(clip(it["msg"], 36))}</text>', t)
            t += .35
    else:
        te = typed(238, t, "activity --weeks 4")
        t = te + .4
        wk = s["weekly"][-4:]
        mx = max([c for _, c in wk] + [1])
        for k, (date, c) in enumerate(wk):
            y = 258 + k * 20
            bar = "█" * max(1, round(c / mx * 24)) if c else "·"
            fade(f'<text x="46" y="{y}" font-family="{MONO}" font-size="12" fill="{DIM}">{dt.date.fromisoformat(date).strftime("%b %-d")}</text>'
                 f'<text x="124" y="{y}" font-family="{MONO}" font-size="13" fill="{BLUE}">{bar}</text>'
                 f'<text x="{124 + 26 * CW:.0f}" y="{y}" font-family="{MONO}" font-size="13" font-weight="800" fill="{TXT}">{c}</text>', t)
            t += .35
    t += .6                                                             # 4: idle prompt + blinking cursor
    fade(prompt_text(348) + f'<rect class="blink" x="{24 + 18 * CW:.1f}" y="336" width="8" height="15" fill="{TEAL}"/>', t)
    return "\n".join(els), "\n".join(kf)


CSS_BASE = """
.blink{animation:blink 1s steps(1) infinite}
.rp{opacity:0;transform-box:fill-box;transform-origin:center;animation:ripple 1.8s ease-out infinite}
.rp2{animation-delay:.6s}.rp3{animation-delay:1.2s}
.halo{transform-box:fill-box;transform-origin:center;animation:halo 1.8s ease-in-out infinite}
.dot{transform-box:fill-box;transform-origin:center;animation:beat 1.8s ease-in-out infinite}
.livetxt{animation:glowtxt 1.8s ease-in-out infinite}
@keyframes ripple{0%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(5.2)}}
@keyframes halo{0%,100%{opacity:.15;transform:scale(1)}50%{opacity:.5;transform:scale(1.7)}}
@keyframes beat{0%,100%{opacity:1;transform:scale(1.15)}50%{opacity:.35;transform:scale(.8)}}
@keyframes glowtxt{0%,100%{opacity:1}50%{opacity:.45}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important}
  .cur,.rp{display:none}
}
"""


def svg(s):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body, kf = build_terminal(s)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="CyberJKD live terminal: {s["contribs"]} contributions in the last 12 months">',
         f'<style>{CSS_BASE}{kf}</style>',
         f'<circle class="rp rp1" cx="30" cy="24" r="4.5" fill="{GREEN}" fill-opacity=".14" stroke="#3fb950" stroke-width="2"/>',
         f'<circle class="rp rp2" cx="30" cy="24" r="4.5" fill="{GREEN}" fill-opacity=".14" stroke="#3fb950" stroke-width="2"/>',
         f'<circle class="rp rp3" cx="30" cy="24" r="4.5" fill="{GREEN}" fill-opacity=".14" stroke="#3fb950" stroke-width="2"/>',
         f'<circle class="halo" cx="30" cy="24" r="6.5" fill="{GREEN}"/>',
         f'<circle class="dot" cx="30" cy="24" r="4.5" fill="{GREEN}"/>',
         f'<text class="livetxt" x="44" y="28.5" font-family="{MONO}" font-size="12" font-weight="800" letter-spacing="2" fill="{GREEN}">LIVE</text>',
         f'<text x="94" y="28" font-family="{MONO}" font-size="11" fill="{DIM}">updated {stamp}  ·  every 6h</text>',
         body, "</svg>"]
    return "\n".join(o)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        stats, feed = demo_data("--nofeed" in sys.argv)
    else:
        stats = gql(STATS_QUERY, strict=True)
        fu = gql(FEED_QUERY, strict=False)
        feed = []
        try:
            feed = parse_feed(fu, USER) if fu else []
        except Exception as e:                      # noqa: BLE001
            print(f"warning: could not parse activity feed: {e}")
    card = svg(summarize(stats, feed))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(card)
    print("wrote", OUT, f"(feed items: {len(feed)})")
