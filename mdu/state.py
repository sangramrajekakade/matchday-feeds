"""Remembers what has already been posted (committed back to the repo by the workflow)."""
import json, os, time

PATH = os.environ.get("STATE_FILE", "data/state.json")
KEEP_DAYS = 21


def load():
    try:
        with open(PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(s):
    cut = time.time() - KEEP_DAYS * 86400
    for k in list(s):
        if isinstance(s[k], dict):
            s[k] = {i: t for i, t in s[k].items() if t > cut}
    os.makedirs(os.path.dirname(PATH) or ".", exist_ok=True)
    with open(PATH, "w") as f:
        json.dump(s, f, indent=0, sort_keys=True)


FORCE_BUCKETS = {"morning", "weekly", "weekend", "quiz", "qotd"}


def seen(s, bucket, key):
    """On-demand runs (FORCE=1) re-post daily/weekly items; results, reminders and news are never duplicated."""
    if os.environ.get("FORCE") == "1" and bucket in FORCE_BUCKETS:
        return False
    return str(key) in s.get(bucket, {})


def mark(s, bucket, key):
    s.setdefault(bucket, {})[str(key)] = time.time()
