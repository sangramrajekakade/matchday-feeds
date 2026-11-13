"""Jobs that use live football data: morning fixtures, results, kick-off reminders, polls, tables."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from mdu import api, cards, config, discord, state

CH_PREDICTIONS = "<#1570732278546440203>"
CH_RATINGS = "<#1570732275782393857>"
CH_MATCHDAY = "<#1570732272754102378>"
IST = timezone(timedelta(minutes=config.IST_OFFSET_MIN))


def comp_code(m):
    return m.get("competition", {}).get("code", "")


def comp_name(m):
    return config.COMPETITIONS.get(comp_code(m), (m.get("competition", {}).get("name", "Football"),))[0]


def bigness(m):
    names = (api.team(m, "home") + " | " + api.team(m, "away") + " | " + m["homeTeam"].get("name", "") + " | "
             + m["awayTeam"].get("name", ""))
    big = sum(1 for t in config.BIG_TEAMS if t.lower() in names.lower())
    return config.COMP_WEIGHT.get(comp_code(m), 1) + 3 * min(big, 2)


def is_big(m, threshold=9):
    """9+ = marquee (two big clubs, or a big club in the UCL). 7+ = notable (a big club in a top league)."""
    return bigness(m) >= threshold


def fixture_line(m):
    t = api.ist(api.kickoff(m)).strftime("%I:%M %p").lstrip("0")
    return f"`{t}` **{api.team(m, 'home')}** v **{api.team(m, 'away')}**"


def today_ist():
    return datetime.now(IST).date()


def ist_day_matches(day):
    """Matches whose IST kick-off falls on `day` (an IST date)."""
    ms = api.matches(day - timedelta(days=1), day + timedelta(days=1), config.DIGEST_COMPS)
    return sorted([m for m in ms if api.ist(api.kickoff(m)).date() == day], key=api.kickoff)


# ── MORNING: fixtures digest + per-league lists + auto prediction poll ────────────────────────────
def morning(s):
    day = today_ist()
    if state.seen(s, "morning", day):
        return "morning already done"
    ms = [m for m in ist_day_matches(day) if m.get("status") not in ("POSTPONED", "CANCELLED")]
    by_comp = defaultdict(list)
    for m in ms:
        by_comp[comp_code(m)].append(m)

    rows = [(api.ist(api.kickoff(m)).strftime("%I:%M %p").lstrip("0"), api.team(m, "home"), api.team(m, "away"),
             comp_name(m)) for m in sorted(ms, key=lambda m: (-bigness(m), api.kickoff(m)))[:14]]
    rows.sort(key=lambda r: datetime.strptime(r[0], "%I:%M %p").time() if r[0] else 0)
    if ms:
        desc = "\n".join(f"**{config.COMPETITIONS.get(c, (c,))[0]}**\n" + "\n".join(fixture_line(m) for m in lst)
                         for c, lst in sorted(by_comp.items(), key=lambda kv: -config.COMP_WEIGHT.get(kv[0], 0)))
        card = cards.fixtures_card(rows, f"TODAY'S FIXTURES", day.strftime("%A %d %B %Y") + " · all times IST")
        discord.send("matchday", embeds=[discord.embed(
            f"⚽ Today's fixtures — {day.strftime('%a %d %b')}", desc[:3900], config.RED,
            image="attachment://fixtures.png")], files=[("fixtures.png", card)])
        by_persona = defaultdict(list)                        # one message per desk (World desk merges leagues)
        for c, lst in by_comp.items():
            name, persona, colour, _ = config.COMPETITIONS.get(c, (c, "world", config.GREEN, 0))
            by_persona[persona].append((name, colour, lst))
        for persona, groups in by_persona.items():
            if len(groups) == 1:
                name, colour, lst = groups[0]
                e = discord.embed(f"{name} today", "\n".join(fixture_line(m) for m in lst), colour)
            else:
                e = discord.embed("Around the leagues today", None, groups[0][1],
                                  fields=[(n, "\n".join(fixture_line(m) for m in l), False) for n, _, l in groups])
            discord.send(persona, embeds=[e], silent=True)
        big = max(ms, key=bigness)
        h, a = api.team(big, "home"), api.team(big, "away")
        kt = api.ist(api.kickoff(big)).strftime("%I:%M %p IST").lstrip("0")
        discord.send("predictions", content=f"🔮 **Prediction of the day** · {comp_name(big)} · kick-off {kt}",
                     poll=discord.poll(f"{h} v {a} — how does it end?", [f"{h} win", "Draw", f"{a} win"],
                                       config.POLL_HOURS))
        state.mark(s, "polled", big["id"])
    else:
        discord.send("matchday", embeds=[discord.embed("No top-flight football today",
                                                       "Rest day. Catch up in the league channels.", config.GREY)],
                     silent=True)
    state.mark(s, "morning", day)
    return f"morning: {len(ms)} matches"


# ── TICK (every 30 min): results, kick-off reminders ──────────────────────────────────────────────
def tick(s):
    now = datetime.now(timezone.utc)
    ms = api.matches((now - timedelta(days=1)).date(), (now + timedelta(days=1)).date(), config.DIGEST_COMPS)
    done = reminded = 0
    fresh_ft = []
    if "result" not in s:                                     # first ever run: don't flood old results
        for m in ms:
            if m.get("status") == "FINISHED":
                state.mark(s, "result", m["id"])
        s.setdefault("result", {})
    for m in sorted(ms, key=api.kickoff):
        st = m.get("status")
        if st == "FINISHED" and not state.seen(s, "result", m["id"]):
            fresh_ft.append(m)
            state.mark(s, "result", m["id"])
        elif st in ("SCHEDULED", "TIMED") and is_big(m) and not state.seen(s, "reminder", m["id"]):
            mins = (api.kickoff(m) - now).total_seconds() / 60
            if 0 < mins <= config.KICKOFF_REMINDER_MIN:
                kt = api.ist(api.kickoff(m)).strftime("%I:%M %p IST").lstrip("0")
                discord.send("matchday", embeds=[discord.embed(
                    f"⏰ Kick-off in {int(mins)} min: {api.team(m, 'home')} v {api.team(m, 'away')}",
                    f"{comp_name(m)} · {kt}\nLast call for predictions in {CH_PREDICTIONS} — then join the "
                    f"watch-along voice channel and react live in {CH_MATCHDAY}.", config.RED)])
                state.mark(s, "reminder", m["id"])
                reminded += 1

    # results: a card per big match to its league desk, a compact round-up to #matchday-hub
    for m in fresh_ft:
        code = comp_code(m)
        name, persona, colour, _ = config.COMPETITIONS.get(code, (comp_name(m), "world", config.GREEN, 0))
        hs, as_ = api.score(m)
        title = f"FT · {api.team(m, 'home')} {hs}–{as_} {api.team(m, 'away')}"
        if is_big(m, 7):
            discord.send(persona, embeds=[discord.embed(title, f"{name} · full time", colour,
                                                        image="attachment://result.png")],
                         files=[("result.png", cards.result_card(m, name))])
        else:
            discord.send(persona, embeds=[discord.embed(title, name, colour)], silent=True)
        if is_big(m):
            discord.send("ratings", content=f"⭐ **Player ratings open:** {api.team(m, 'home')} {hs}–{as_} "
                                            f"{api.team(m, 'away')}. Reply with your ratings out of 10 and your "
                                            f"player of the match.",
                         poll=discord.poll("How good was that match?",
                                           ["🔥🔥🔥 Classic", "🔥🔥 Entertaining", "🔥 Decent", "😴 Forgettable"], 24))
        done += 1
    if fresh_ft:
        lines = []
        for m in fresh_ft:
            hs, as_ = api.score(m)
            lines.append(f"**{api.team(m, 'home')} {hs}–{as_} {api.team(m, 'away')}** · {comp_name(m)}")
        discord.send("matchday", embeds=[discord.embed("🏁 Full-time results", "\n".join(lines)[:3900], config.GOLD)],
                     silent=len(fresh_ft) < 2)
    return f"tick: {done} results, {reminded} reminders"


# ── WEEKLY (Monday): tables, top scorers, title-race snapshot ─────────────────────────────────────
def weekly(s):
    wk = today_ist().isocalendar()
    key = f"{wk[0]}-W{wk[1]}"
    if state.seen(s, "weekly", key):
        return "weekly already done"
    snapshot = []
    for code in config.TABLE_COMPS:
        name, persona, colour, n = config.COMPETITIONS[code]
        st = api.standings(code)
        total = next((t for t in st.get("standings", []) if t.get("type") == "TOTAL"), None)
        if not total:
            continue
        table = total["table"]
        md = st.get("season", {}).get("currentMatchday")
        discord.send(persona, embeds=[discord.embed(f"📊 {name} table · matchday {md}", None, colour,
                                                    image="attachment://table.png")],
                     files=[("table.png", cards.table_card(name, table, min(n, 20)))])
        sc = api.scorers(code, 10).get("scorers", [])
        if sc:
            lines = [f"`{i + 1:>2}` **{p['player']['name']}** ({p['team'].get('shortName') or p['team']['name']}) — "
                     f"{p.get('goals', 0)} ⚽" + (f" · {p['assists']} 🅰️" if p.get("assists") else "")
                     for i, p in enumerate(sc)]
            discord.send(persona, embeds=[discord.embed(f"👟 {name} top scorers", "\n".join(lines), colour)],
                         silent=True)
        top = table[:3]
        snapshot.append((name, " · ".join(f"{r['position']}. {r['team'].get('shortName') or r['team']['name']} "
                                          f"({r['points']})" for r in top)))
    if snapshot:
        discord.send("table", embeds=[discord.embed("🏆 Title races this week", None, config.PURPLE,
                                                    fields=[(n, v, False) for n, v in snapshot])])
    state.mark(s, "weekly", key)
    return f"weekly: {len(snapshot)} leagues"


# ── FRIDAY: weekend preview ───────────────────────────────────────────────────────────────────────
def weekend(s):
    day = today_ist()
    if state.seen(s, "weekend", day):
        return "weekend already done"
    ms = api.matches(day, day + timedelta(days=3), config.DIGEST_COMPS)
    big = sorted([m for m in ms if is_big(m, 7) and m.get("status") in ("SCHEDULED", "TIMED")], key=api.kickoff)[:12]
    if big:
        lines = [f"`{api.ist(api.kickoff(m)).strftime('%a %I:%M %p').replace(' 0', ' ')}` **{api.team(m, 'home')}** v "
                 f"**{api.team(m, 'away')}** · {comp_name(m)}" for m in big]
        rows = [(api.ist(api.kickoff(m)).strftime("%a %I%p").replace(" 0", " "), api.team(m, "home"),
                 api.team(m, "away"), comp_name(m)) for m in big]
        discord.send("daily", embeds=[discord.embed(
            "📅 This weekend's biggest games", "\n".join(lines) + f"\n\nWatch-alongs are in the Events tab. "
                                                                    f"Predictions open daily in {CH_PREDICTIONS}.",
            config.BLUE, image="attachment://weekend.png")],
            files=[("weekend.png", cards.fixtures_card(rows, "THE WEEKEND'S BIG GAMES", "all times IST"))])
    state.mark(s, "weekend", day)
    return f"weekend: {len(big)} big games"
