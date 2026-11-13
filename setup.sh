#!/usr/bin/env bash
# One-command setup for MATCHDAY UNITED auto-feeds (macOS / Linux).
#   1. installs the GitHub CLI if missing (Homebrew)   2. logs you in to GitHub
#   3. creates a PUBLIC repo and pushes this folder    4. asks you to paste the API key + each webhook URL
#   5. starts the first run.        Re-run any time: it skips what is already done.
set -euo pipefail
cd "$(dirname "$0")"
REPO="${REPO:-matchday-feeds}"

say() { printf "\n\033[1;33m▶ %s\033[0m\n" "$*"; }

if ! command -v gh >/dev/null; then
  say "Installing GitHub CLI"
  if command -v brew >/dev/null; then brew install gh
  else echo "Install Homebrew first (https://brew.sh) or the GitHub CLI (https://cli.github.com), then re-run."; exit 1; fi
fi

if ! gh auth status >/dev/null 2>&1; then
  say "Log in to GitHub (a browser window opens — approve it)"
  gh auth login --web --git-protocol https --scopes "repo,workflow"
fi
USER_LOGIN=$(gh api user -q .login)

if [ ! -d .git ]; then
  git init -q -b main
  git add -A
  git -c user.name="$USER_LOGIN" -c user.email="$USER_LOGIN@users.noreply.github.com" commit -qm "MATCHDAY UNITED auto-feeds"
fi
if ! gh repo view "$USER_LOGIN/$REPO" >/dev/null 2>&1; then
  say "Creating public repo $USER_LOGIN/$REPO and pushing the code"
  gh repo create "$REPO" --public --source . --remote origin --push \
     --description "Automatic football fixtures, results, tables, news & polls for the MATCHDAY UNITED Discord"
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$USER_LOGIN/$REPO.git"
  git push -q -u origin main || true
fi

say "Secrets. Paste each value and press Enter (input is hidden). Press Enter on an empty line to skip one."
echo "Webhook URL: Discord → channel ⚙ Edit Channel → Integrations → Webhooks → click it → Copy Webhook URL"
existing=$(gh secret list -R "$USER_LOGIN/$REPO" 2>/dev/null | cut -f1 || true)
while IFS='|' read -r name label; do
  if grep -qx "$name" <<<"$existing"; then echo "  ✓ $name already set"; continue; fi
  read -r -s -p "  $label  [$name]: " val </dev/tty; echo
  [ -z "$val" ] && { echo "    skipped"; continue; }
  if [[ "$name" == WH_* && "$val" != https://discord.com/api/webhooks/* && "$val" != https://discordapp.com/api/webhooks/* ]]; then
    echo "    ⚠ that doesn't look like a Discord webhook URL — skipped"; continue; fi
  printf '%s' "$val" | gh secret set "$name" -R "$USER_LOGIN/$REPO"
  echo "    ✓ saved"
done <<'EOF'
FOOTBALL_DATA_TOKEN|football-data.org API key (from the registration email)
WH_NEWS|#football-news → MATCHDAY News
WH_HQ|#announcements → MATCHDAY HQ
WH_MATCHDAY|#matchday-hub → Matchday Live
WH_DAILY|#general-football → Matchday Daily
WH_TRANSFERS|#transfer-hq → Transfer Desk
WH_PREDICTIONS|#predictions → Prediction Desk
WH_RATINGS|#player-ratings → Ratings Desk
WH_LEADERBOARD|#prediction-leaderboard → League Table
WH_PL|#premier-league → Premier League Desk
WH_LALIGA|#la-liga → La Liga Desk
WH_SERIEA|#serie-a → Serie A Desk
WH_UCL|#champions-league → Champions League Desk
WH_WOMENS|#womens-football → Women's Football Desk
WH_INTL|#international-football → International Desk
WH_OTHER|#other-leagues → World Leagues Desk
WH_QUIZ|#football-quiz → Quiz Master
WH_MODLOG|#mod-log → Feed Monitor
EOF

say "Starting the first run (records what already exists, then posts only new things)"
gh workflow enable feeds.yml -R "$USER_LOGIN/$REPO" >/dev/null 2>&1 || true
sleep 3
gh workflow run feeds.yml -R "$USER_LOGIN/$REPO" -f jobs="tick news quiz qotd" && \
  echo "  Running — watch it at https://github.com/$USER_LOGIN/$REPO/actions"
say "Done. From now on it runs by itself every 30 minutes, every morning at 08:01 IST, Mondays and Fridays."
