"""Jobs that need no football API key: RSS news, daily quiz, question of the day."""
import calendar, hashlib, html, json, os, random, re, time
from datetime import datetime, timedelta, timezone

import feedparser

from mdu import config, discord, state

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
IST = timezone(timedelta(minutes=config.IST_OFFSET_MIN))
PERSONA_COLOUR = {"news": config.BLUE, "transfers": config.TEAL, "womens": config.PURPLE}


def _clean(text, n=280):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def _key(entry):
    base = entry.get("id") or entry.get("link") or entry.get("title", "")
    return hashlib.sha1(base.encode()).hexdigest()[:16]


def _norm_title(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower())[:80]


# ── NEWS: RSS → #football-news, #transfer-hq, #womens-football ────────────────────────────────────
NB = "news_v2"            # bucket of headlines actually posted (marked only after Discord accepts them)
NOT_FOOTBALL = re.compile(r"\b(rugby|tennis|cricket|nfl|nba|golf|boxing|cycling|formula one|f1|motogp|atp|wta|"
                          r"athletics|snooker|darts|horse racing|ufc|mma|olympics?)\b", re.I)


def news(s, feeds=None):
    feeds = feeds or config.FEEDS
    force = os.environ.get("FORCE") == "1"
    first_run = NB not in s and not force           # scheduled first run: remember what exists, post nothing
    s.setdefault(NB, {})
    posted = {}
    cutoff = time.time() - config.NEWS_MAX_AGE_HOURS * 3600
    queue = {}
    for f in feeds:
        try:
            parsed = feedparser.parse(f["url"], agent="MatchdayUnitedFeeds/1.0 (+independent fan community)")
        except Exception as e:                      # one bad feed never stops the rest
            print("feed error", f["url"], e)
            continue
        for e in parsed.entries[:30]:
            title = _clean(e.get("title"), 240)
            if not title or NOT_FOOTBALL.search(title):
                continue
            if f.get("keywords") and not any(k in title.lower() for k in f["keywords"]):
                continue
            ts = e.get("published_parsed") or e.get("updated_parsed")
            ts = calendar.timegm(ts) if ts else time.time()
            if ts < cutoff:
                continue
            k = f["persona"] + ":" + _key(e)
            tk = f["persona"] + ":t:" + _norm_title(title)   # same story from two feeds → post once
            if state.seen(s, NB, k) or state.seen(s, NB, tk):
                continue
            if first_run:
                state.mark(s, NB, k)
                state.mark(s, NB, tk)
                continue
            q = queue.setdefault(f["persona"], {})
            q.setdefault(tk, (ts, title, e, f["name"], k))

    for persona, items in queue.items():
        items = sorted(items.items(), key=lambda kv: -kv[1][0])[:config.NEWS_MAX_PER_RUN][::-1]
        for tk, (ts, title, e, src, k) in items:
            img = None
            for mk in ("media_thumbnail", "media_content"):
                if e.get(mk):
                    img = e[mk][0].get("url")
                    break
            em = discord.embed(title, _clean(e.get("summary")), PERSONA_COLOUR.get(persona, config.BLUE),
                               url=e.get("link"), thumbnail=img, footer=f"{src} · via RSS · MATCHDAY UNITED",
                               timestamp=datetime.fromtimestamp(ts, timezone.utc).isoformat())
            try:
                discord.send(persona, embeds=[em], silent=True)
            except discord.NotConfigured:                       # that channel's webhook isn't added yet
                print(f"news: {persona} skipped — webhook not set")
                break
            state.mark(s, NB, k)
            state.mark(s, NB, tk)
            posted[persona] = posted.get(persona, 0) + 1
    return "news: " + (", ".join(f"{p} {n}" for p, n in posted.items()) or ("seeded" if first_run else "nothing new"))


# ── QUIZ: one question a day, answer hidden behind a spoiler ─────────────────────────────────────
def quiz(s):
    day = datetime.now(IST).date()
    if state.seen(s, "quiz", day):
        return "quiz already done"
    bank = json.load(open(os.path.join(DATA, "quiz.json")))
    used = s.setdefault("quiz_used", [])
    left = [i for i in range(len(bank)) if i not in used] or list(range(len(bank)))
    if len(left) == len(bank):
        used.clear()
    i = random.Random(str(day)).choice(left)
    q = bank[i]
    ans = q["options"][q["answer"]]
    discord.send("quiz", content=f"🧠 **Daily quiz · {day.strftime('%d %b')}** — vote below, answer in the spoiler.",
                 poll=discord.poll(q["q"], q["options"], 24))
    discord.send("quiz", embeds=[discord.embed("Answer", f"||**{ans}** — {q.get('why', '')}||", config.PURPLE)],
                 silent=True)
    used.append(i)
    state.mark(s, "quiz", day)
    return f"quiz: #{i}"


# ── QUESTION OF THE DAY: a debate starter in #general-football ───────────────────────────────────
def talking_point(s):
    day = datetime.now(IST).date()
    if state.seen(s, "qotd", day):
        return "qotd already done"
    bank = json.load(open(os.path.join(DATA, "talking_points.json")))
    used = s.setdefault("qotd_used", [])
    left = [i for i in range(len(bank)) if i not in used]
    if not left:
        used.clear()
        left = list(range(len(bank)))
    i = random.Random("qotd" + str(day)).choice(left)
    p = bank[i]
    if p.get("options"):
        discord.send("daily", content=f"💬 **Question of the day** — {p.get('nudge', 'vote, then make your case below 👇')}",
                     poll=discord.poll(p["q"], p["options"], 24))
    else:
        discord.send("daily", embeds=[discord.embed("💬 Question of the day",
                                                    f"**{p['q']}**\n\n{p.get('nudge', 'Make your case below 👇')}",
                                                    config.BLUE)])
    used.append(i)
    state.mark(s, "qotd", day)
    return f"qotd: #{i}"
