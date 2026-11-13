"""MATCHDAY UNITED auto-poster.  Usage:  python main.py <job> [<job> ...]
Jobs: morning, tick, weekly, weekend, news, quiz, qotd, all-daily.  Set DRY_RUN=1 to print instead of posting."""
import os, sys, traceback

if os.path.exists(".env"):                       # local runs: read KEY=value lines (never commit .env)
    for line in open(".env"):
        k, _, v = line.strip().partition("=")
        if k and not k.startswith("#") and v:
            os.environ.setdefault(k, v.strip().strip('"'))
from mdu import discord, state  # noqa: E402
from jobs import community, football  # noqa: E402

JOBS = {
    "morning": football.morning,     # 08:00 IST  fixtures digest + league desks + prediction poll
    "tick": football.tick,           # every 30m  full-time results, cards, ratings polls, kick-off reminders
    "weekly": football.weekly,       # Mon        tables, top scorers, title-race snapshot
    "weekend": football.weekend,     # Fri        weekend big-games preview
    "news": community.news,          # hourly     RSS → news / transfers / women's football
    "quiz": community.quiz,          # daily      quiz poll + spoiler answer
    "qotd": community.talking_point, # daily      question of the day in #general-football
}
GROUPS = {"all-daily": ["morning", "quiz", "qotd"]}


def main(names):
    s = state.load()
    failed = []
    for n in [j for name in names for j in GROUPS.get(name, [name])]:
        try:
            print(JOBS[n](s))
        except discord.NotConfigured as e:          # secret not added yet: skip quietly, don't fail the run
            print(f"{n}: skipped — {e}")
        except Exception as e:
            traceback.print_exc()
            failed.append(f"`{n}`: {type(e).__name__}: {str(e)[:300]}")
        finally:
            state.save(s)                       # save progress even if a later job fails
    if failed:
        try:
            discord.send("monitor", embeds=[discord.embed("⚠️ Feed job failed", "\n".join(failed), 0xD94B42)],
                         silent=True)
        except Exception:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2 or any(a not in JOBS and a not in GROUPS for a in sys.argv[1:]):
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1:])
