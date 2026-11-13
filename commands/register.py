"""Registers the slash commands with Discord (run once, and again only if commands change).
Needs DISCORD_BOT_TOKEN (GitHub secret) and DISCORD_APP_ID."""
import json, os, sys
import requests

APP_ID = os.environ.get("DISCORD_APP_ID", "1570719261222117466")
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
LEAGUE = {"name": "league", "description": "Which league", "type": 3, "required": False,
          "choices": [{"name": "Premier League", "value": "PL"}, {"name": "La Liga", "value": "PD"},
                      {"name": "Serie A", "value": "SA"}, {"name": "Bundesliga", "value": "BL1"},
                      {"name": "Ligue 1", "value": "FL1"}, {"name": "Champions League", "value": "CL"}]}
COMMANDS = [
    {"name": "scores", "description": "Today's scores, live games and latest results"},
    {"name": "fixtures", "description": "Upcoming matches (all times IST)", "options": [LEAGUE]},
    {"name": "table", "description": "League table", "options": [LEAGUE]},
    {"name": "scorers", "description": "Top scorers for a league", "options": [LEAGUE]},
    {"name": "news", "description": "Latest football headlines", "options": [
        {"name": "type", "description": "What kind of news", "type": 3, "required": False,
         "choices": [{"name": "All football", "value": "all"}, {"name": "Transfers", "value": "transfers"},
                     {"name": "Women's football", "value": "womens"}]}]},
    {"name": "quiz", "description": "A random football quiz question"},
    {"name": "help", "description": "What MATCHDAY UNITED can do"},
]
for c in COMMANDS:
    c["type"] = 1
    c["integration_types"] = [0]   # guild install
    c["contexts"] = [0]            # usable in servers

if __name__ == "__main__":
    if not TOKEN:
        sys.exit("DISCORD_BOT_TOKEN is not set")
    r = requests.put(f"https://discord.com/api/v10/applications/{APP_ID}/commands",
                     headers={"Authorization": f"Bot {TOKEN}"}, json=COMMANDS, timeout=30)
    print(r.status_code, r.text[:500])
    r.raise_for_status()
    print("Registered:", ", ".join("/" + c["name"] for c in r.json()))
