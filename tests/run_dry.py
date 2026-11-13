"""Offline end-to-end test: builds realistic sample API/RSS data around *now*, runs every job in DRY_RUN
mode and checks what would be posted. No network, no tokens needed.   python tests/run_dry.py"""
import json, os, shutil, sys, tempfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
TMP = tempfile.mkdtemp()
os.environ.update(DRY_RUN="1", FD_SAMPLES=TMP, STATE_FILE=os.path.join(TMP, "state.json"),
                  ASSET_BASE="https://raw.githubusercontent.com/example/matchday-feeds/main/assets",
                  DRY_PRINT=os.environ.get("DRY_PRINT", "0"))
now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
IST = timezone(timedelta(minutes=330))


def team(i, name, short, tla):
    return {"id": i, "name": name, "shortName": short, "tla": tla}


T = {k: team(i, *v) for i, (k, v) in enumerate({
    "LIV": ("Liverpool FC", "Liverpool", "LIV"), "MUN": ("Manchester United FC", "Man United", "MUN"),
    "ARS": ("Arsenal FC", "Arsenal", "ARS"), "NEW": ("Newcastle United FC", "Newcastle", "NEW"),
    "BRE": ("Brentford FC", "Brentford", "BRE"), "FUL": ("Fulham FC", "Fulham", "FUL"),
    "RMA": ("Real Madrid CF", "Real Madrid", "RMA"), "GIR": ("Girona FC", "Girona", "GIR"),
    "INT": ("FC Internazionale Milano", "Inter", "INT"), "LEC": ("US Lecce", "Lecce", "LEC"),
    "BVB": ("Borussia Dortmund", "Dortmund", "BVB"), "FCA": ("FC Augsburg", "Augsburg", "FCA"),
    "LIL": ("Lille OSC", "Lille", "LIL"), "NAN": ("FC Nantes", "Nantes", "NAN"),
}.items(), 1)}
COMP = {"PL": "Premier League", "PD": "Primera Division", "SA": "Serie A", "BL1": "Bundesliga", "FL1": "Ligue 1",
        "CL": "UEFA Champions League"}


def match(mid, comp, h, a, when, status, hs=None, as_=None):
    return {"id": mid, "utcDate": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": status,
            "competition": {"code": comp, "name": COMP[comp]}, "homeTeam": T[h], "awayTeam": T[a],
            "score": {"fullTime": {"home": hs, "away": as_}}}


today_ist = datetime.now(IST).date()
at = lambda h, m=0: datetime(today_ist.year, today_ist.month, today_ist.day, h, m, tzinfo=IST).astimezone(timezone.utc)
M = [
    match(1, "PL", "BRE", "FUL", now - timedelta(hours=26), "FINISHED", 1, 1),          # old: should be seeded
    match(2, "PL", "LIV", "MUN", now - timedelta(hours=3), "FINISHED", 2, 1),           # new big FT
    match(3, "PD", "RMA", "GIR", now - timedelta(hours=2), "FINISHED", 3, 0),           # new FT (big team)
    match(4, "BL1", "BVB", "FCA", now - timedelta(hours=2, minutes=10), "FINISHED", 0, 0),
    match(5, "PL", "NEW", "ARS", now + timedelta(minutes=50), "TIMED"),                 # reminder due
    match(6, "SA", "INT", "LEC", now + timedelta(hours=5), "TIMED"),
    match(7, "FL1", "LIL", "NAN", now + timedelta(hours=6), "TIMED"),
    match(8, "CL", "ARS", "BVB", at(23, 30) if at(23, 30) > now else now + timedelta(hours=8), "TIMED"),
    match(9, "PL", "ARS", "LIV", now + timedelta(days=2), "TIMED"),
]


def write(name, obj):
    json.dump(obj, open(os.path.join(TMP, name), "w"))


def standings(code):
    teams = [t for t in T.values()][:12]
    rows = [{"position": i + 1, "team": t, "playedGames": 12, "won": 9 - i // 2, "draw": 2, "lost": i // 2 + 1,
             "goalDifference": 15 - 2 * i, "points": 29 - 2 * i} for i, t in enumerate(teams)]
    return {"season": {"currentMatchday": 12}, "standings": [{"type": "TOTAL", "table": rows}]}


def scorers(code):
    return {"scorers": [{"player": {"name": f"Player {i}"}, "team": list(T.values())[i], "goals": 12 - i,
                         "assists": i % 3} for i in range(10)]}


# RSS sample
def rss(items):
    xml = ['<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>t</title>']
    for i, (title, hrs) in enumerate(items):
        xml.append(f"<item><title>{title}</title><link>https://example.com/{abs(hash(title))}</link>"
                   f"<guid>{abs(hash(title))}</guid><description>Short summary for {title}.</description>"
                   f"<pubDate>{format_datetime(now - timedelta(hours=hrs))}</pubDate>"
                   f'<media:thumbnail url="https://example.com/img{i}.jpg"/></item>')
    xml.append("</channel></rss>")
    return "".join(xml)


def set_rss(name, items):
    p = os.path.join(TMP, name)
    open(p, "w").write(rss(items))
    return p


from mdu import discord, state  # noqa: E402
from jobs import community, football  # noqa: E402

fails = []


def check(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        fails.append(msg)


def run(fn, *a):
    discord.DRY_LOG.clear()
    s = state.load()
    r = fn(s, *a)
    state.save(s)
    print(f"→ {fn.__module__.split('.')[-1]}.{fn.__name__}: {r}")
    return list(discord.DRY_LOG)


write("matches.json", {"matches": M})
for c in ["PL", "PD", "SA", "BL1", "FL1"]:
    write(f"competitions_{c}_standings.json", standings(c))
    write(f"competitions_{c}_scorers.json", scorers(c))

# 1. tick — first run seeds old results but must still post reminders; second sees no duplicates
log = run(football.tick)
check(not any("FT ·" in json.dumps(x) for x in log), "first tick does not flood existing results")
check(any("Kick-off in" in json.dumps(x, ensure_ascii=False) for x in log), "kick-off reminder for Newcastle v Arsenal")
# simulate: new results arrive after first run
for m in M:
    if m["id"] in (2, 3, 4):
        m["id"] += 100
write("matches.json", {"matches": M})
log = run(football.tick)
cards = [x for x in log if x["files"]]
check(len(cards) == 2, f"result cards for big matches (Liverpool, Real Madrid): {len(cards)}")
check(sum(1 for x in log if x["persona"] == "ratings" and "poll" in x["payload"]) == 1, "one ratings poll (Liverpool v Man United only)")
check(any(x["persona"] == "matchday" and "Full-time" in json.dumps(x) for x in log), "round-up in #matchday-hub")
check(not any("Kick-off in" in json.dumps(x, ensure_ascii=False) for x in log), "reminder not repeated")
check(all(x["payload"].get("avatar_url", "").startswith("https://raw.githubusercontent") for x in log), "avatars set")
log = run(football.tick)
check(len(log) == 0, "third tick posts nothing new")

# 2. morning
log = run(football.morning)
check(any(x["persona"] == "matchday" and x["files"] == ["fixtures.png"] for x in log), "fixtures card")
pol = [x for x in log if x["persona"] == "predictions"]
check(len(pol) == 1 and len(pol[0]["payload"]["poll"]["answers"]) == 3, "auto prediction poll with 3 answers")
print("     poll:", pol[0]["payload"]["poll"]["question"]["text"] if pol else "-")
check(len(run(football.morning)) == 0, "morning runs once per day")

# 3. weekly + weekend
log = run(football.weekly)
check(sum(1 for x in log if x["files"] == ["table.png"]) == 5, "5 league table cards")
check(any(x["persona"] == "table" for x in log), "title-race snapshot in #prediction-leaderboard")
write("matches.json", {"matches": M})
log = run(football.weekend)
check(any(x["files"] == ["weekend.png"] for x in log), "weekend preview card")

# 4. news — seeds on first run, then posts only new, dedupes across feeds, keyword filter works
f1 = set_rss("a.xml", [("Old story one", 1), ("Club agrees record transfer fee for striker", 2)])
f2 = set_rss("b.xml", [("Old story one", 1)])
feeds = [{"name": "A", "url": f1, "persona": "news"}, {"name": "B", "url": f2, "persona": "news"},
         {"name": "A", "url": f1, "persona": "transfers", "keywords": ["transfer"]}]
log = run(community.news, feeds)
check(len(log) == 0, "first news run seeds silently")
f1 = set_rss("a.xml", [("Old story one", 1), ("Club agrees record transfer fee for striker", 2),
                       ("Manager praises young midfielder", 0.5), ("Defender signs new transfer deal", 0.2),
                       ("Ancient news", 30)])
f2 = set_rss("b.xml", [("Manager praises young midfielder", 0.5)])
log = run(community.news, feeds)
titles = [(x["persona"], x["payload"]["embeds"][0]["title"]) for x in log]
print("     ", titles)
check(sum(1 for p, t in titles if p == "news") == 2, "2 new news items (cross-feed duplicate removed)")
check([t for p, t in titles if p == "transfers"] == ["Defender signs new transfer deal"], "transfer keyword filter")
check(not any("Ancient" in t for _, t in titles), "stale items skipped")
check(len(run(community.news, feeds)) == 0, "no repeats")

# 5. quiz + qotd
log = run(community.quiz)
check(len(log) == 2 and "poll" in log[0]["payload"] and "||" in json.dumps(log[1], ensure_ascii=False),
      "quiz poll + spoiler answer")
check(len(run(community.quiz)) == 0, "quiz once per day")
log = run(community.talking_point)
check(len(log) == 1, "question of the day")

# 6. payload limits
from mdu import config  # noqa: E402
qz = json.load(open("data/quiz.json"))
check(all(len(o) <= 55 for q in qz for o in q["options"]) and all(len(q["q"]) <= 300 for q in qz), "quiz fits poll limits")
check(all(0 <= q["answer"] < len(q["options"]) for q in qz), "quiz answers valid")

# render previews
os.makedirs("out", exist_ok=True)
from mdu import cards  # noqa: E402
open("out/preview_result.png", "wb").write(cards.result_card(M[1], "Premier League"))
open("out/preview_fixtures.png", "wb").write(cards.fixtures_card(
    [("9:30 PM", "Liverpool", "Man United", "Premier League"), ("11:30 PM", "Inter", "Lecce", "Serie A"),
     ("1:30 AM", "Arsenal", "Dortmund", "Champions League")], "TODAY'S FIXTURES", "Sunday 22 November 2026 · all times IST"))
open("out/preview_table.png", "wb").write(cards.table_card("Premier League", standings("PL")["standings"][0]["table"], 10))

shutil.rmtree(TMP)
print(f"\n{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)
