"""Writes data/snapshot.json — the always-fresh data the /commands answer from (no secrets inside).
Matches every run (1 API call). Tables + scorers every 6 h (2 calls per league). News every run (RSS)."""
import calendar, json, os, re, time
from datetime import datetime, timedelta, timezone

import feedparser

from mdu import api, config
from jobs.community import NOT_FOOTBALL, _clean

PATH = os.environ.get("SNAPSHOT_FILE", "data/snapshot.json")
TABLE_EVERY = 6 * 3600
SNAP_COMPS = ["PL", "PD", "SA", "BL1", "FL1", "CL"]


def _load():
    try:
        with open(PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _match(m):
    hs, as_ = api.score(m)
    ko = api.kickoff(m)
    return {"id": m["id"], "comp": m.get("competition", {}).get("code", ""),
            "compName": config.COMPETITIONS.get(m.get("competition", {}).get("code", ""), (m.get("competition", {}).get("name", ""),))[0],
            "utc": m["utcDate"], "ist": api.ist(ko).strftime("%a %d %b · %I:%M %p").replace(" 0", " "),
            "istDate": api.ist(ko).strftime("%Y-%m-%d"), "status": m.get("status"),
            "home": api.team(m, "home"), "away": api.team(m, "away"), "hs": hs, "as": as_,
            "minute": m.get("minute")}


def snapshot(s):
    snap = _load()
    now = datetime.now(timezone.utc)
    msgs = []

    # matches: 3 days back, 7 days ahead
    if os.environ.get("FOOTBALL_DATA_TOKEN") or os.environ.get("FD_SAMPLES"):
        ms = api.matches((now - timedelta(days=3)).date(), (now + timedelta(days=7)).date(), config.DIGEST_COMPS)
        snap["matches"] = [_match(m) for m in sorted(ms, key=api.kickoff)]
        msgs.append(f"{len(ms)} matches")

        # tables + scorers, at most every 6 hours (or when forced)
        if time.time() - snap.get("tablesAt", 0) > TABLE_EVERY or os.environ.get("FORCE") == "1":
            tables, scorers = snap.get("tables", {}), snap.get("scorers", {})
            for code in SNAP_COMPS:
                try:
                    st = api.standings(code)
                    total = next((t for t in st.get("standings", []) if t.get("type") == "TOTAL"), None)
                    if total:
                        tables[code] = {"name": config.COMPETITIONS[code][0],
                                        "matchday": st.get("season", {}).get("currentMatchday"),
                                        "rows": [{"pos": r["position"], "team": r["team"].get("shortName") or r["team"]["name"],
                                                  "p": r["playedGames"], "w": r["won"], "d": r["draw"], "l": r["lost"],
                                                  "gd": r["goalDifference"], "pts": r["points"]} for r in total["table"]]}
                    sc = api.scorers(code, 10).get("scorers", [])
                    scorers[code] = {"name": config.COMPETITIONS[code][0],
                                     "rows": [{"player": p["player"]["name"],
                                               "team": p["team"].get("shortName") or p["team"]["name"],
                                               "goals": p.get("goals") or 0, "assists": p.get("assists") or 0} for p in sc]}
                except Exception as e:                      # one league failing keeps the old data
                    print("snapshot table error", code, e)
            snap["tables"], snap["scorers"], snap["tablesAt"] = tables, scorers, time.time()
            msgs.append("tables refreshed")

    # news (RSS, no key needed)
    items, seen = [], set()
    for f in config.FEEDS:
        if f.get("keywords") or f["persona"] not in ("news", "transfers", "womens"):
            continue
        try:
            parsed = feedparser.parse(f["url"], agent="MatchdayUnitedFeeds/1.0")
        except Exception:
            continue
        for e in parsed.entries[:25]:
            title = _clean(e.get("title"), 200)
            key = re.sub(r"[^a-z0-9]", "", title.lower())[:60]
            if not title or key in seen or NOT_FOOTBALL.search(title):
                continue
            seen.add(key)
            ts = e.get("published_parsed") or e.get("updated_parsed")
            items.append({"title": title, "url": e.get("link"), "source": f["name"], "kind": f["persona"],
                          "ts": calendar.timegm(ts) if ts else int(time.time())})
    if items:
        snap["news"] = sorted(items, key=lambda x: -x["ts"])[:40]
        msgs.append(f"{len(snap['news'])} headlines")

    snap["updated"] = now.isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(PATH) or ".", exist_ok=True)
    with open(PATH, "w") as f:
        json.dump(snap, f, ensure_ascii=False, separators=(",", ":"))
    return "snapshot: " + ", ".join(msgs)
