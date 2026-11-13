# MATCHDAY UNITED · auto-feeds

Live football data posted automatically into the MATCHDAY UNITED Discord through **webhooks**. There's no bot, nothing to install in the server, and it costs nothing to run.

| When (IST) | Job | Posts to | What |
|---|---|---|---|
| every 30 min | `tick` | league desks, #matchday-hub, #player-ratings | Full-time result cards (big matches), round-up of all results, kick-off reminders 75 min before marquee games, "rate the match" poll |
| every 30 min | `news` | #football-news, #transfer-hq, #womens-football | Headlines from BBC Sport and The Guardian RSS (deduped, max 4 per channel per run) |
| 08:01 daily | `morning` | #matchday-hub + every league desk | Today's fixtures card, plus each league's list |
| 08:01 daily | `morning` | #predictions | **Automatic prediction poll** on the day's biggest match |
| 08:01 daily | `quiz` | #football-quiz | Quiz poll with the answer hidden behind a spoiler (60-question bank) |
| 08:01 daily | `qotd` | #general-football | Question of the day: a debate poll |
| Mon 08:43 | `weekly` | PL, La Liga, Serie A, World desks, #prediction-leaderboard | League table cards, top scorers, title-race snapshot |
| Fri 17:17 | `weekend` | #general-football | Weekend's biggest games preview card |
| on any error | | #mod-log | "Feed job failed" alert |

Data comes from [football-data.org](https://www.football-data.org). Its free tier covers PL, La Liga, Serie A, Bundesliga, Ligue 1, UCL, Eredivisie, Primeira Liga, Championship, Brasileirão, World Cup and Euros. Free-tier scores aren't real-time, so **results** post within about 30–60 min of full time, not minute-by-minute.

## Quick start on a Mac (one command)
1. Register for a free key at football-data.org/client/register (it arrives by email).
2. Unzip this folder, open Terminal, and run:
   ```bash
   cd ~/Downloads/matchday-feeds && ./setup.sh
   ```
   The script installs the GitHub CLI and logs you in through your browser. It creates the repo and pushes the code, then asks you to paste the key and each webhook URL. Input is hidden, and each value is stored only as a GitHub secret. Finally it starts the first run.

## Manual setup (≈15 minutes, one time)

1. **Get a free API key.** Register at football-data.org/client/register; the key arrives by email.
2. **Create a GitHub repo** called `matchday-feeds` and upload this folder.
   - Make it **public** so Discord can load the branded avatars from `assets/`.
   - Your webhook URLs and API key stay private as secrets.
   - Public repos also get unlimited free Actions minutes.
3. **Copy each webhook URL** in Discord: open the channel → ⚙ Edit Channel → Integrations → Webhooks → click the webhook → **Copy Webhook URL**.
4. **Add each URL as a secret** in GitHub: repo → Settings → Secrets and variables → Actions → **New repository secret**.

| Secret name | Channel | Webhook |
|---|---|---|
| `FOOTBALL_DATA_TOKEN` | (API key) | |
| `WH_NEWS` | #football-news | MATCHDAY News |
| `WH_HQ` | #announcements | MATCHDAY HQ |
| `WH_MATCHDAY` | #matchday-hub | Matchday Live |
| `WH_DAILY` | #general-football | Matchday Daily |
| `WH_TRANSFERS` | #transfer-hq | Transfer Desk |
| `WH_PREDICTIONS` | #predictions | Prediction Desk |
| `WH_RATINGS` | #player-ratings | Ratings Desk |
| `WH_LEADERBOARD` | #prediction-leaderboard | League Table |
| `WH_PL` | #premier-league | Premier League Desk |
| `WH_LALIGA` | #la-liga | La Liga Desk |
| `WH_SERIEA` | #serie-a | Serie A Desk |
| `WH_UCL` | #champions-league | Champions League Desk |
| `WH_WOMENS` | #womens-football | Women's Football Desk |
| `WH_INTL` | #international-football | International Desk |
| `WH_OTHER` | #other-leagues | World Leagues Desk |
| `WH_QUIZ` | #football-quiz | Quiz Master |
| `WH_MODLOG` | #mod-log | Feed Monitor |

   With the GitHub CLI you can add them faster: `gh secret set WH_NEWS` (then paste).

5. **Run it once by hand** to check: Actions tab → *MATCHDAY UNITED feeds* → **Run workflow** → `tick news`. The first run quietly records what already exists, so nothing old floods in. Then try `all-daily`.

After that it runs on its own.

> 🔒 Treat webhook URLs like passwords. Anyone who has one can post in that channel. If one leaks: Discord → delete that webhook → create a new one → update the secret.

## Running on your Mac instead
```bash
pip install -r requirements.txt
cp .env.example .env        # fill in the values
python main.py tick news    # or: morning, weekly, weekend, quiz, qotd, all-daily
```
For a schedule, add a `crontab -e` line such as `*/30 * * * * cd ~/matchday-feeds && python3 main.py tick news`.

## Testing without posting anything
```bash
python tests/run_dry.py               # full offline test on realistic sample data (24 checks)
DRY_PRINT=1 python tests/run_dry.py   # also print every payload that would be sent
DRY_RUN=1 python main.py news         # real RSS, prints instead of posting
```
Card previews are written to `out/`.

## Customising
Everything is in `mdu/config.py`:
- `BIG_TEAMS` and `COMP_WEIGHT` decide what counts as a big match.
- `FEEDS` lists the RSS sources and keyword filters.
- `COMPETITIONS` maps each league to a channel.
- `TABLE_COMPS` sets which leagues get weekly tables.

Edit `data/quiz.json` and `data/talking_points.json` to add questions.

## Ground rules this follows
- No bot: webhooks can only post. They can't read messages or members.
- Original art only: the shields are generic two-tone badges with team initials, never club crests.
- Independent: there is no affiliation with FIFA, UEFA, leagues or clubs.
- Data is credited to football-data.org, and news links back to the source.
- Posting limits: at most 4 news items per channel per run. Routine posts are sent silently, with no notification ping.
