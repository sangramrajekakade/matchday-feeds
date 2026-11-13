"""Post to Discord webhooks: embeds, polls and image files, posting as a branded persona."""
import json, os, time
import requests
from . import config

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
DRY_LOG = []          # filled in dry-run mode so tests can inspect what would be sent


class NotConfigured(Exception):
    """A secret (webhook URL or API key) has not been added yet — the job is skipped, not failed."""


WebhookMissing = NotConfigured


def has_own(persona):
    """True when this persona's own channel webhook is configured (or in dry-run tests)."""
    return DRY_RUN or bool(os.environ.get(config.PERSONAS[persona][0]))


def _avatar(file):
    return f"{config.ASSET_BASE}/avatars/{file}" if config.ASSET_BASE else None


def send(persona, content=None, embeds=None, poll=None, files=None, silent=False):
    """files: list of (filename, bytes). Returns the created message dict (or a dry-run stub)."""
    env, name, avatar_file = config.PERSONAS[persona]
    payload = {"username": name, "allowed_mentions": {"parse": []}}
    if (a := _avatar(avatar_file)):
        payload["avatar_url"] = a
    if content:
        payload["content"] = content[:2000]
    if embeds:
        payload["embeds"] = embeds[:10]
    if poll:
        payload["poll"] = poll
    if silent:
        payload["flags"] = 1 << 12           # SUPPRESS_NOTIFICATIONS
    if files:
        payload["attachments"] = [{"id": i, "filename": fn} for i, (fn, _) in enumerate(files)]

    if DRY_RUN:
        DRY_LOG.append({"persona": persona, "payload": payload, "files": [fn for fn, _ in files or []]})
        if os.environ.get("DRY_PRINT", "1") == "1":
            print(f"\n── would post as {name} ({env}) ──")
            print(json.dumps(payload, indent=1, ensure_ascii=False)[:1800])
            for fn, data in files or []:
                os.makedirs("out", exist_ok=True)
                open(f"out/{fn}", "wb").write(data)
                print(f"   + file out/{fn} ({len(data)//1024} KB)")
        return {"id": "dry"}

    url = os.environ.get(env)
    if not url:                                   # channel key not added yet → post via a fallback channel
        for fb in config.FALLBACK.get(persona, []):
            url = os.environ.get(fb)
            if url:
                print(f"{persona}: {env} not set, posting via {fb}")
                break
    if not url:
        raise WebhookMissing(f"{env} is not set — add it as a GitHub secret")
    for attempt in range(4):
        if files:
            r = requests.post(url, params={"wait": "true"},
                              data={"payload_json": json.dumps(payload)},
                              files={f"files[{i}]": (fn, data, "image/png") for i, (fn, data) in enumerate(files)},
                              timeout=30)
        else:
            r = requests.post(url, params={"wait": "true"}, json=payload, timeout=30)
        if r.status_code == 429:                       # rate limited: wait as told and retry
            time.sleep(float(r.json().get("retry_after", 2)) + .5)
            continue
        r.raise_for_status()
        time.sleep(1.2)                                # stay well under webhook limits
        return r.json()
    raise RuntimeError(f"Discord kept rate-limiting {name}")


def embed(title, description=None, colour=config.GOLD, url=None, fields=None, image=None,
          thumbnail=None, footer=config.FOOTER, timestamp=None):
    e = {"title": title[:256], "color": colour, "footer": {"text": footer}}
    if description:
        e["description"] = description[:4000]
    if url:
        e["url"] = url
    if fields:
        e["fields"] = [{"name": n[:256], "value": (v or "—")[:1024], "inline": inl} for n, v, inl in fields][:25]
    if image:
        e["image"] = {"url": image}
    if thumbnail:
        e["thumbnail"] = {"url": thumbnail}
    if timestamp:
        e["timestamp"] = timestamp
    return e


def poll(question, answers, hours=24, multi=False):
    return {"question": {"text": question[:300]},
            "answers": [{"poll_media": {"text": a[:55]}} for a in answers[:10]],
            "duration": hours, "allow_multiselect": multi}
