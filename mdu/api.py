"""Tiny football-data.org v4 client (free tier: 10 requests/minute, needs a free API key)."""
import json, os, time
from datetime import datetime, timedelta, timezone
import requests

BASE = "https://api.football-data.org/v4"
SAMPLES = os.environ.get("FD_SAMPLES")          # folder of saved JSON responses for offline tests
_last = [0.0]


def _get(path, **params):
    if SAMPLES:
        key = path.strip("/").replace("/", "_") + ".json"
        with open(os.path.join(SAMPLES, key)) as f:
            return json.load(f)
    token = os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        from .discord import NotConfigured
        raise NotConfigured("FOOTBALL_DATA_TOKEN is not set — get a free key at football-data.org/client/register")
    wait = 6.5 - (time.time() - _last[0])           # ≤ 10 calls/min
    if wait > 0:
        time.sleep(wait)
    for attempt in range(3):
        r = requests.get(BASE + path, params=params, headers={"X-Auth-Token": token}, timeout=30)
        _last[0] = time.time()
        if r.status_code == 429:
            time.sleep(61)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"football-data.org rate limit on {path}")


def matches(date_from, date_to, competitions=None):
    """All matches across your subscribed competitions between two dates (inclusive). ONE request."""
    p = {"dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat()}
    if competitions:
        p["competitions"] = ",".join(competitions)
    return _get("/matches", **p).get("matches", [])


def standings(code):
    return _get(f"/competitions/{code}/standings")


def scorers(code, limit=10):
    return _get(f"/competitions/{code}/scorers", limit=limit)


# ── helpers ─────────────────────────────────────────────────────────────────
def kickoff(m):
    return datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))


def ist(dt):
    return dt.astimezone(timezone(timedelta(minutes=330)))


def team(m, side):
    t = m[side + "Team"]
    return t.get("shortName") or t.get("name") or "TBC"


def score(m):
    ft = m.get("score", {}).get("fullTime", {})
    return ft.get("home"), ft.get("away")
