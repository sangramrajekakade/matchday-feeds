"""Branded PNG cards (original art: generic two-tone shields with team initials, never club crests)."""
import hashlib, io
from . import api
from .brand import *

GREEN, RED_G = (60, 170, 110), (217, 75, 66)
PALETTE = [(196, 52, 52), (36, 84, 168), (24, 128, 84), (110, 60, 160), (210, 120, 30), (30, 140, 150),
           (150, 30, 70), (60, 60, 70), (200, 170, 40), (90, 140, 210)]


def _cols(name):
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    a = PALETTE[h % len(PALETTE)]
    b = PALETTE[(h // 7) % len(PALETTE)]
    return a, (b if b != a else WHITE)


def _initials(t):
    tla = t.get("tla")
    if tla:
        return tla
    words = [w for w in (t.get("shortName") or t.get("name") or "?").split() if w[0].isalnum()]
    return "".join(w[0] for w in words[:3]).upper() or "?"


def _png(img, w, h):
    buf = io.BytesIO()
    img.resize((w, h), Image.LANCZOS).convert("RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _brand_footer(img, s):
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    em = emblem(int(56 * s))
    paste(img, em, (40 * s, h - 36 * s - em.height))
    d.text((40 * s + em.width + 14 * s, h - 36 * s - em.height / 2), "MATCHDAY UNITED", font=font("head", 30 * s),
           fill=WHITE, anchor="lm")
    d.text((w - 40 * s, h - 36 * s - em.height / 2), "INDEPENDENT FAN COMMUNITY", font=font("body", 13 * s, 700),
           fill=MUTE, anchor="rm")


def result_card(m, comp_name, label="FULL TIME"):
    W, H, s = 1200, 630, 2
    w, h = W * s, H * s
    img = background(w, h, glow=GOLD)
    d = ImageDraw.Draw(img, "RGBA")
    chip(d, w / 2, 52 * s, comp_name.upper(), size=17 * s, anchor="c")
    headline(d, (w / 2, 150 * s), label, 64 * s, col=GOLD_L, anchor="mm")
    hs, as_ = api.score(m)
    for side, x in (("home", .22), ("away", .78)):
        t = m[side + "Team"]
        c1, c2 = _cols(t.get("name", "x"))
        sh = shield(int(170 * s), c1, c2, _initials(t))
        paste(img, sh, (w * x - sh.width / 2, 200 * s))
        nm = api.team(m, side).upper()
        headline(d, (w * x, 410 * s), nm, 46 * s, anchor="mm", maxw=w * .34)
    sc = f"{'' if hs is None else hs}  –  {'' if as_ is None else as_}"
    d.rounded_rectangle([w / 2 - 150 * s, 235 * s, w / 2 + 150 * s, 355 * s], radius=24 * s, fill=(8, 12, 22, 220),
                        outline=GOLD, width=3 * s)
    headline(d, (w / 2, 297 * s), sc, 110 * s, anchor="mm")
    when = api.ist(api.kickoff(m)).strftime("%a %d %b %Y · %I:%M %p IST")
    d.text((w / 2, 470 * s), when, font=font("body", 20 * s, 600), fill=MUTE, anchor="mm")
    corners(img, 22 * s, 50 * s, 4 * s)
    _brand_footer(img, s)
    return _png(img, W, H)


def fixtures_card(rows, title, subtitle):
    """rows: list of (time_str, home, away, comp_short)."""
    rows = rows[:14]
    W, s = 1200, 2
    H = 250 + 62 * max(1, len(rows)) + 110
    w, h = W * s, H * s
    img = background(w, h, glow=RED, pitch=False)
    d = ImageDraw.Draw(img, "RGBA")
    chip(d, 48 * s, 44 * s, "MATCHDAY", size=17 * s)
    headline(d, (48 * s, 140 * s), title, 72 * s, maxw=w - 96 * s)
    d.text((48 * s, 200 * s), subtitle, font=font("body", 22 * s, 600), fill=MUTE, anchor="lm")
    y = 250 * s
    for i, (t, a, b, c) in enumerate(rows):
        if i % 2 == 0:
            d.rounded_rectangle([40 * s, y, w - 40 * s, y + 54 * s], radius=10 * s, fill=(255, 255, 255, 12))
        cy = y + 27 * s
        d.text((60 * s, cy), t, font=font("body", 22 * s, 800), fill=GOLD, anchor="lm")
        mid = 0.55 * w
        d.text((mid - 30 * s, cy), a, font=fit(d, a, "body", w * .3, 24 * s, 700), fill=WHITE, anchor="rm")
        d.text((mid, cy), "v", font=font("body", 20 * s, 600), fill=MUTE, anchor="mm")
        d.text((mid + 30 * s, cy), b, font=fit(d, b, "body", w * .3, 24 * s, 700), fill=WHITE, anchor="lm")
        d.text((w - 60 * s, cy), c, font=font("body", 16 * s, 800), fill=MUTE, anchor="rm")
        y += 62 * s
    if not rows:
        d.text((w / 2, y + 27 * s), "No matches in our tracked competitions today", font=font("body", 24 * s, 600),
               fill=MUTE, anchor="mm")
    corners(img, 22 * s, 50 * s, 4 * s)
    _brand_footer(img, s)
    return _png(img, W, H)


def table_card(comp_name, table, n=10):
    """table: football-data standings 'table' list."""
    rows = table[:n]
    W, s = 1200, 2
    H = 260 + 52 * len(rows) + 110
    w, h = W * s, H * s
    img = background(w, h, glow=GREEN, pitch=False)
    d = ImageDraw.Draw(img, "RGBA")
    chip(d, 48 * s, 44 * s, "LEAGUE TABLE", size=17 * s)
    headline(d, (48 * s, 140 * s), comp_name.upper(), 72 * s, maxw=w - 96 * s)
    cols = [("P", .62), ("W", .68), ("D", .74), ("L", .80), ("GD", .87), ("PTS", .95)]
    y = 210 * s
    for lab, x in cols:
        d.text((w * x, y), lab, font=font("body", 17 * s, 800), fill=MUTE, anchor="mm")
    y = 240 * s
    for i, r in enumerate(rows):
        if i % 2 == 0:
            d.rounded_rectangle([40 * s, y, w - 40 * s, y + 46 * s], radius=8 * s, fill=(255, 255, 255, 12))
        cy = y + 23 * s
        d.text((70 * s, cy), str(r["position"]), font=font("body", 22 * s, 800), fill=GOLD if i < 4 else WHITE,
               anchor="mm")
        nm = r["team"].get("shortName") or r["team"]["name"]
        d.text((110 * s, cy), nm, font=fit(d, nm, "body", w * .45, 23 * s, 700), fill=WHITE, anchor="lm")
        vals = [r["playedGames"], r["won"], r["draw"], r["lost"], f'{r["goalDifference"]:+d}', r["points"]]
        for (lab, x), v in zip(cols, vals):
            d.text((w * x, cy), str(v), font=font("body", 22 * s, 800 if lab == "PTS" else 600),
                   fill=GOLD_L if lab == "PTS" else WHITE, anchor="mm")
        y += 52 * s
    corners(img, 22 * s, 50 * s, 4 * s)
    _brand_footer(img, s)
    return _png(img, W, H)
