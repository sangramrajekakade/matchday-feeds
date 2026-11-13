"""All settings in one place. Webhook URLs are NEVER stored here — they come from environment
variables (GitHub Actions secrets). Edit the lists below to change what gets posted where."""
import os

IST_OFFSET_MIN = 330                       # display times in India Standard Time
TZ_LABEL = "IST"

# Where avatars live once the repo is on GitHub (raw URLs). Set ASSET_BASE in the workflow, e.g.
# https://raw.githubusercontent.com/<github-user>/matchday-feeds/main/assets
ASSET_BASE = os.environ.get("ASSET_BASE", "").rstrip("/")

GOLD = 0xD5A83B
RED = 0xD94B42
GREEN = 0x3CAA6E
BLUE = 0x4678DC
PURPLE = 0x8C5AD2
TEAL = 0x28AAB4
GREY = 0x78829A
FOOTER = "MATCHDAY UNITED · independent fan community · data: football-data.org"

# Each persona = one Discord webhook (env var holds its URL) + the name/avatar it posts as.
PERSONAS = {
    "hq":          ("WH_HQ",          "MATCHDAY HQ",            "hq.png"),
    "news":        ("WH_NEWS",        "MATCHDAY News",          "news.png"),
    "matchday":    ("WH_MATCHDAY",    "Matchday Live",          "matchday.png"),
    "daily":       ("WH_DAILY",       "Matchday Daily",         "daily.png"),
    "transfers":   ("WH_TRANSFERS",   "Transfer Desk",          "transfers.png"),
    "predictions": ("WH_PREDICTIONS", "Prediction Desk",        "predictions.png"),
    "ratings":     ("WH_RATINGS",     "Ratings Desk",           "ratings.png"),
    "table":       ("WH_LEADERBOARD", "League Table",           "table.png"),
    "pl":          ("WH_PL",          "Premier League Desk",    "pl.png"),
    "laliga":      ("WH_LALIGA",      "La Liga Desk",           "laliga.png"),
    "seriea":      ("WH_SERIEA",      "Serie A Desk",           "seriea.png"),
    "ucl":         ("WH_UCL",         "Champions League Desk",  "ucl.png"),
    "womens":      ("WH_WOMENS",      "Women's Football Desk",  "wfc.png"),
    "intl":        ("WH_INTL",        "International Desk",     "intl.png"),
    "world":       ("WH_OTHER",       "World Leagues Desk",     "world.png"),
    "quiz":        ("WH_QUIZ",        "Quiz Master",            "quiz.png"),
    "monitor":     ("WH_MODLOG",      "Feed Monitor",           "monitor.png"),
}

# football-data.org free-tier competitions → (display name, persona, embed colour, table rows to show)
COMPETITIONS = {
    "PL":  ("Premier League",        "pl",     GREEN,  20),
    "PD":  ("La Liga",               "laliga", GREEN,  20),
    "SA":  ("Serie A",               "seriea", GREEN,  20),
    "CL":  ("Champions League",      "ucl",    BLUE,   36),
    "BL1": ("Bundesliga",            "world",  GREEN,  18),
    "FL1": ("Ligue 1",               "world",  GREEN,  18),
    "DED": ("Eredivisie",            "world",  GREEN,  10),
    "PPL": ("Primeira Liga",         "world",  GREEN,  10),
    "ELC": ("Championship",          "world",  GREEN,  10),
    "BSA": ("Brasileirão",           "world",  GREEN,  10),
    "WC":  ("FIFA World Cup",        "intl",   TEAL,   0),
    "EC":  ("European Championship", "intl",   TEAL,   0),
}
TABLE_COMPS = ["PL", "PD", "SA", "BL1", "FL1"]          # weekly standings + top scorers
DIGEST_COMPS = list(COMPETITIONS)                         # included in the morning fixtures digest

# Used to pick "the big match" of the day for the auto poll / reminders / ratings prompt.
BIG_TEAMS = [
    "Arsenal", "Chelsea", "Liverpool", "Man City", "Man United", "Tottenham", "Newcastle", "Aston Villa",
    "Real Madrid", "Barcelona", "Atleti", "Atlético", "Bayern", "Dortmund", "Leverkusen",
    "Inter", "Milan", "Juventus", "Napoli", "Roma", "PSG", "Benfica", "Porto", "Sporting", "Ajax",
]
COMP_WEIGHT = {"CL": 6, "WC": 6, "EC": 6, "PL": 5, "PD": 4, "SA": 3, "BL1": 3, "FL1": 2}

# RSS feeds → persona. Items whose title matches `keywords` (if given) are the only ones posted.
FEEDS = [
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "persona": "news"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/football/rss", "persona": "news"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "persona": "transfers",
     "keywords": ["transfer", "signs", "signing", "deal", "bid", "loan", "contract", "joins", "fee", "agree"]},
    {"name": "The Guardian", "url": "https://www.theguardian.com/football/transfer-window/rss", "persona": "transfers"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/football/womens/rss.xml", "persona": "womens"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/football/womensfootball/rss", "persona": "womens"},
]
NEWS_MAX_PER_RUN = 4          # per persona, so channels never get flooded
NEWS_MAX_AGE_HOURS = 12

KICKOFF_REMINDER_MIN = 75     # remind about big matches starting within this many minutes
POLL_HOURS = 24               # auto prediction poll duration

# Until a channel's own webhook secret is added, its posts go to a channel that already works.
# (Name and avatar stay the same, e.g. "Quiz Master" posting in #matchday-hub.) Add the real secret to move it.
_MATCH = ["WH_MATCHDAY", "WH_NEWS"]
_NEWSY = ["WH_NEWS", "WH_MATCHDAY"]
FALLBACK = {
    "predictions": _MATCH, "ratings": _MATCH, "table": _MATCH, "pl": _MATCH, "laliga": _MATCH, "seriea": _MATCH,
    "ucl": _MATCH, "world": _MATCH, "intl": _MATCH, "quiz": _MATCH, "daily": _MATCH, "hq": _MATCH,
    "transfers": [], "womens": [],          # would only repeat #football-news
    "monitor": _MATCH, "matchday": ["WH_NEWS"], "news": ["WH_MATCHDAY"],
}
