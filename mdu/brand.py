"""MATCHDAY UNITED brand graphics — 20 original assets (no club crests, no real players)."""
import io, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
OUT = "out"

NAVY, NAVY2, NAVY3 = (16, 24, 39), (27, 38, 56), (42, 56, 82)
GOLD, GOLD_L, WHITE, RED = (213, 168, 59), (232, 199, 106), (244, 245, 247), (217, 75, 66)
MUTE = (160, 172, 192)
SS = 2
INVITE = "discord.gg/sxMHp5S5sC"
TAG = "ONE GAME. MILLIONS OF FANS. ONE COMMUNITY."


def font(kind, size, weight=400):
    if kind == "head":
        return ImageFont.truetype(f"{FD}/BebasNeue-Regular.ttf", int(size))
    f = ImageFont.truetype(f"{FD}/Inter.ttf", int(size))
    try:
        f.set_variation_by_axes([max(14, min(32, size)), weight])
    except Exception:
        pass
    return f


def fit(d, text, kind, maxw, size, weight=400, minsize=10):
    while size > minsize and d.textlength(text, font=font(kind, size, weight)) > maxw:
        size -= 2
    return font(kind, size, weight)


def paste(img, im, xy):
    img.paste(im, (int(xy[0]), int(xy[1])), im)


def blur_layer(size, draw_fn, radius):
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    return lay.filter(ImageFilter.GaussianBlur(radius))


# ── backgrounds ────────────────────────────────────────────────────────
def background(w, h, beams=True, pitch=True, dots=True, glow=GOLD, seed=1):
    img = Image.new("RGB", (w, h), NAVY)
    # vertical gradient navy → deeper navy
    grad = Image.linear_gradient("L").resize((w, h))
    img = Image.composite(Image.new("RGB", (w, h), (9, 14, 25)), img, grad)
    if glow:
        paste(img, blur_layer((w, h), lambda d: d.ellipse([w * .1, -h * .55, w * .9, h * .35], fill=glow + (70,)), min(w, h) * .15), (0, 0))
    if beams:
        for x0, a0, a1 in ((w * .12, 35, 75), (w * .88, 105, 145)):
            def bd(d, x0=x0, a0=a0, a1=a1):
                L = h * 1.6
                d.polygon([(x0, -h * .05), (x0 + L * math.cos(math.radians(a0)), -h * .05 + L * math.sin(math.radians(a0))),
                           (x0 + L * math.cos(math.radians(a1)), -h * .05 + L * math.sin(math.radians(a1)))], fill=(255, 244, 214, 30))
            paste(img, blur_layer((w, h), bd, min(w, h) * .03), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    if pitch:
        lw = max(2, w // 500)
        d.ellipse([w / 2 - h * .3, h / 2 - h * .3, w / 2 + h * .3, h / 2 + h * .3], outline=(255, 255, 255, 14), width=lw)
        d.line([0, h / 2, w, h / 2], fill=(255, 255, 255, 12), width=lw)
    if dots:
        step = max(10, w // 90)
        for y in range(0, int(h * .35), step):
            for x in range(int(w * .6), w, step):
                r = step * .28 * ((x - w * .6) / (w * .4)) * (1 - y / (h * .35))
                if r > .5:
                    d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD + (40,))
    # vignette
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([-w * .3, -h * .3, w * 1.3, h * 1.3], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(w, h) * .12))
    return Image.composite(img, Image.new("RGB", (w, h), (5, 8, 14)), m.point(lambda v: 110 + v * 145 // 255))


def corners(img, inset, length, width, col=GOLD):
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    for (x, y, dx, dy) in ((inset, inset, 1, 1), (w - inset, inset, -1, 1), (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)):
        d.line([(x, y + dy * length), (x, y), (x + dx * length, y)], fill=col, width=width, joint="curve")


# ── ball + emblem ──────────────────────────────────────────────────────
def ball(size, panel=(16, 24, 39), base=(246, 246, 248)):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r = S / 2, S / 2 * .96
    d.ellipse([c - r, c - r, c + r, c + r], fill=base)
    pent = lambda cx, cy, rad, rot: [(cx + rad * math.cos(math.radians(rot + 72 * k)), cy + rad * math.sin(math.radians(rot + 72 * k))) for k in range(5)]
    w = int(S * .022)
    core = pent(c, c, r * .3, -90)
    outer = []
    for k in range(5):
        th = math.radians(-90 + 72 * k)
        v = (c + r * .6 * math.cos(th), c + r * .6 * math.sin(th))
        d.line([core[k], v], fill=panel, width=w)
        R = r * .3
        pts = pent(v[0] + R * math.cos(th), v[1] + R * math.sin(th), R, -90 + 72 * k + 180)
        outer.append(pts)
        d.polygon(pts, fill=panel)
    for k in range(5):
        a, b = outer[k], outer[(k + 1) % 5]
        p, q = min(((p, q) for p in a for q in b), key=lambda t: (t[0][0] - t[1][0]) ** 2 + (t[0][1] - t[1][1]) ** 2)
        d.line([p, q], fill=panel, width=w)
    d.polygon(core, fill=panel)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([c - r, c - r, c + r, c + r], fill=255)
    shade = blur_layer((S, S), lambda dd: dd.ellipse([c - r * .2, c - r * .2, c + r * 1.6, c + r * 1.6], fill=(0, 0, 0, 80)), S * .08)
    im = Image.alpha_composite(im, shade)
    hl = blur_layer((S, S), lambda dd: dd.ellipse([c - r * .7, c - r * .8, c - r * .05, c - r * .25], fill=(255, 255, 255, 110)), S * .04)
    im = Image.alpha_composite(im, hl)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    ImageDraw.Draw(out).ellipse([c - r, c - r, c + r, c + r], outline=(20, 28, 44), width=int(S * .012))
    return out.resize((size, size), Image.LANCZOS)


def leaf(d, cx, cy, L, Wd, ang, col):
    pts = []
    for k in range(24):
        u = 2 * math.pi * k / 24
        x, y = L / 2 * math.cos(u), Wd / 2 * math.sin(u) * (1 - .25 * math.cos(u))
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    d.polygon(pts, fill=col)


def laurel(d, cx, cy, R, col, leaves=7, side=1, scale=1.0):
    """One laurel branch from the bottom centre sweeping up one side (side=-1 left, 1 right)."""
    a0, a1 = (100, 235) if side < 0 else (80, -55)
    L, Wd = R * .3 * scale, R * .12 * scale
    stem = [(cx + R * math.cos(math.radians(a0 + (a1 - a0) * t / 40)), cy + R * math.sin(math.radians(a0 + (a1 - a0) * t / 40))) for t in range(41)]
    d.line(stem, fill=col, width=max(2, int(R * .03)))
    for i in range(leaves):
        t = (i + .6) / leaves
        a = math.radians(a0 + (a1 - a0) * t)
        tang = a + (math.pi / 2 if a1 > a0 else -math.pi / 2)        # direction of travel along the branch
        nx, ny = math.cos(a), math.sin(a)                            # outward normal of the ring
        for out in (1, -1):
            px = cx + R * math.cos(a) + out * nx * Wd * .75 + L * .32 * math.cos(tang)
            py = cy + R * math.sin(a) + out * ny * Wd * .75 + L * .32 * math.sin(tang)
            turn = out * (.42 if a1 > a0 else -.42)
            leaf(d, px, py, L, Wd, tang - turn, col)


def emblem(size, ring=True):
    """Gold laurel wreath around a ball on a navy roundel. Original mark."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    if ring:
        d.ellipse([S * .02, S * .02, S * .98, S * .98], fill=NAVY)
        d.ellipse([S * .02, S * .02, S * .98, S * .98], outline=GOLD, width=int(S * .028))
        d.ellipse([S * .07, S * .07, S * .93, S * .93], outline=GOLD + (90,), width=int(S * .008))
    # floodlight rays behind
    for a in (-120, -90, -60):
        L = S * .42
        d.polygon([(c, c), (c + L * math.cos(math.radians(a - 6)), c + L * math.sin(math.radians(a - 6))),
                   (c + L * math.cos(math.radians(a + 6)), c + L * math.sin(math.radians(a + 6)))], fill=GOLD + (45,))
    laurel(d, c, c + S * .02, S * .33, GOLD, side=-1)
    laurel(d, c, c + S * .02, S * .33, GOLD, side=1)
    b = ball(int(S * .4), panel=NAVY)
    paste(im, b, (c - b.width / 2, c - b.height / 2 - S * .02))
    # star on top
    cx, cy, ro, ri = c, S * .14, S * .045, S * .018
    d.polygon([(cx + (ro if k % 2 == 0 else ri) * math.cos(math.radians(-90 + 36 * k)), cy + (ro if k % 2 == 0 else ri) * math.sin(math.radians(-90 + 36 * k))) for k in range(10)], fill=GOLD_L)
    return im.resize((size, size), Image.LANCZOS)


def wordmark(img, x, y, size, anchor="lm", col=WHITE, tag=True, tagcol=GOLD):
    d = ImageDraw.Draw(img, "RGBA")
    f = font("head", size)
    d.text((x, y), "MATCHDAY UNITED", font=f, fill=col, anchor=anchor)
    if tag:
        tf = font("body", size * .2, 700)
        tx = x if anchor[0] == "l" else (x - d.textlength(TAG, font=tf) / 2 if anchor[0] == "m" else x - d.textlength(TAG, font=tf))
        d.text((tx + (0 if anchor[0] != "m" else d.textlength(TAG, font=tf) / 2), y + size * .62), TAG, font=tf, fill=tagcol,
               anchor="lm" if anchor[0] == "l" else ("mm" if anchor[0] == "m" else "rm"))


def footer(img, s=1, url=True):
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    em = emblem(int(64 * s))
    paste(img, em, (48 * s, h - 48 * s - em.height))
    d.text((48 * s + em.width + 14 * s, h - 48 * s - em.height / 2 - 9 * s), "MATCHDAY UNITED", font=font("head", 30 * s), fill=WHITE, anchor="lm")
    d.text((48 * s + em.width + 14 * s, h - 48 * s - em.height / 2 + 15 * s), "INDEPENDENT FAN COMMUNITY", font=font("body", 12 * s, 700), fill=MUTE, anchor="lm")
    if url:
        d.text((w - 48 * s, h - 48 * s - em.height / 2), INVITE, font=font("body", 22 * s, 800), fill=GOLD, anchor="rm")


def shield(size, col1, col2, label):
    """Plain two-tone shield with a text label — generic, not a club crest."""
    S = size * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def pts(i):
        r, t, b = S * .9 - i, S * .05 + i, S * .96 - i
        right = [(S * .5, t), (r, t + S * .06), (r, S * .5)]
        for k in range(1, 25):
            a = k / 24
            right.append((r + (S * .5 - r) * a ** 1.3, S * .5 + (b - S * .5) * (1 - (1 - a) ** 2)))
        return right + [(S - x, y) for x, y in reversed(right[:-1])][:-1]
    d.polygon(pts(0), fill=GOLD)
    d.polygon(pts(S * .04), fill=NAVY)
    fld = Image.new("RGBA", (S, S), col1 + (255,))
    ImageDraw.Draw(fld).rectangle([S / 2, 0, S, S], fill=col2)
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).polygon(pts(S * .065), fill=255)
    im.paste(fld, (0, 0), m)
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([S * .18, S * .38, S * .82, S * .62], radius=S * .05, fill=(10, 14, 24, 225), outline=GOLD, width=int(S * .014))
    d.text((S * .5, S * .505), label, font=fit(d, label, "head", S * .56, S * .22), fill=WHITE, anchor="mm")
    return im.resize((size, size), Image.LANCZOS)


def headline(d, xy, text, size, col=WHITE, anchor="lm", maxw=None, shadow=True):
    f = fit(d, text, "head", maxw, size) if maxw else font("head", size)
    if shadow:
        d.text((xy[0] + size * .03, xy[1] + size * .04), text, font=f, fill=(0, 0, 0, 150), anchor=anchor)
    d.text(xy, text, font=f, fill=col, anchor=anchor)
    return f


def chip(d, x, y, text, size=22, bg=GOLD, fg=NAVY, anchor="l"):
    f = font("body", size, 800)
    tw = d.textlength(text, font=f)
    pad = size * .8
    x0 = x if anchor == "l" else x - tw / 2 - pad
    d.rounded_rectangle([x0, y, x0 + tw + 2 * pad, y + size * 2], radius=size, fill=bg)
    d.text((x0 + pad + tw / 2, y + size), text, font=f, fill=fg, anchor="mm")
    return tw + 2 * pad


def save(img, name):
    img.convert("RGB").save(f"{OUT}/{name}.png", optimize=True)


def crowd(img, y0, rows, seed=3, scarf=True):
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(seed)
    unit = max(7, w // 120)
    for row in range(rows):
        y = y0 + row * unit * 2.1
        for k in range(int(w / unit / 1.25) + 2):
            cx = k * unit * 1.25 + rnd.uniform(-2, 2) + (row % 2) * unit * .6
            r = unit * rnd.uniform(.75, .95)
            sh = 22 + row * 7 + rnd.randint(-5, 5)
            d.ellipse([cx - r, y - r, cx + r, y + r], fill=(sh, sh + 6, sh + 16))
            d.rounded_rectangle([cx - r * 1.3, y + r * .8, cx + r * 1.3, y + r * 3], radius=r, fill=(sh, sh + 6, sh + 16))
            if scarf and rnd.random() < .12:
                col = rnd.choice([GOLD, RED, WHITE, (70, 130, 220), (60, 170, 110)])
                d.rounded_rectangle([cx - r * 1.4, y + r * .9, cx + r * 1.4, y + r * 1.5], radius=r * .3, fill=col)
            if rnd.random() < .05:
                d.line([(cx + r, y + r), (cx + r * 1.8, y - r * 2.4)], fill=(sh + 10, sh + 16, sh + 26), width=int(r * .7))


def player_silhouette(h, col=(8, 12, 22)):
    """Faceless celebrating figure, arms raised, no badge or number."""
    W = int(h * .9)
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = W / 2
    u = h / 100
    d.ellipse([cx - 7 * u, 6 * u, cx + 7 * u, 20 * u], fill=col)                       # head
    d.polygon([(cx - 13 * u, 24 * u), (cx + 13 * u, 24 * u), (cx + 10 * u, 56 * u), (cx - 10 * u, 56 * u)], fill=col)  # torso
    d.line([(cx - 12 * u, 27 * u), (cx - 30 * u, 12 * u), (cx - 36 * u, 0)], fill=col, width=int(7 * u), joint="curve")   # arms up
    d.line([(cx + 12 * u, 27 * u), (cx + 30 * u, 12 * u), (cx + 36 * u, 0)], fill=col, width=int(7 * u), joint="curve")
    d.polygon([(cx - 11 * u, 55 * u), (cx + 11 * u, 55 * u), (cx + 12 * u, 66 * u), (cx - 12 * u, 66 * u)], fill=col)  # shorts
    d.line([(cx - 6 * u, 64 * u), (cx - 14 * u, 82 * u), (cx - 12 * u, 99 * u)], fill=col, width=int(7 * u), joint="curve")  # legs
    d.line([(cx + 6 * u, 64 * u), (cx + 18 * u, 80 * u), (cx + 26 * u, 94 * u)], fill=col, width=int(7 * u), joint="curve")
    return im


def jersey(h, col=GOLD, number="10"):
    W = int(h * 1.05)
    S = 2
    im = Image.new("RGBA", (W * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = h * S / 100
    cx = W * S / 2
    body = [(cx - 18 * u, 4 * u), (cx - 8 * u, 2 * u), (cx, 8 * u), (cx + 8 * u, 2 * u), (cx + 18 * u, 4 * u), (cx + 44 * u, 18 * u),
            (cx + 36 * u, 36 * u), (cx + 26 * u, 31 * u), (cx + 26 * u, 98 * u), (cx - 26 * u, 98 * u), (cx - 26 * u, 31 * u),
            (cx - 36 * u, 36 * u), (cx - 44 * u, 18 * u)]
    d.polygon(body, fill=NAVY2, outline=col, width=int(2.2 * u))
    d.line([(cx - 8 * u, 2 * u), (cx, 8 * u), (cx + 8 * u, 2 * u)], fill=col, width=int(2.2 * u))
    d.line([(cx - 36 * u, 36 * u), (cx - 44 * u, 18 * u)], fill=col, width=int(4 * u))
    d.line([(cx + 36 * u, 36 * u), (cx + 44 * u, 18 * u)], fill=col, width=int(4 * u))
    d.text((cx, 60 * u), number, font=font("head", 46 * u), fill=col, anchor="mm")
    return im.resize((W, h), Image.LANCZOS)


def trophy(size):
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    g, gd = GOLD, (166, 124, 33)
    d.arc([S * .08, S * .12, S * .4, S * .48], 90, 270, fill=g, width=int(S * .05))
    d.arc([S * .6, S * .12, S * .92, S * .48], -90, 90, fill=g, width=int(S * .05))
    d.chord([S * .2, -S * .22, S * .8, S * .6], 0, 180, fill=g)
    d.rectangle([S * .2, S * .06, S * .8, S * .19], fill=g)
    d.ellipse([S * .29, S * .1, S * .42, S * .42], fill=GOLD_L)
    d.polygon([(S * .44, S * .58), (S * .56, S * .58), (S * .6, S * .74), (S * .4, S * .74)], fill=gd)
    d.rounded_rectangle([S * .26, S * .74, S * .74, S * .93], radius=S * .03, fill=NAVY2, outline=g, width=int(S * .012))
    d.rectangle([S * .36, S * .8, S * .64, S * .87], fill=g)
    return im.resize((size, size), Image.LANCZOS)


def qr(size):
    q = Image.open("/home/claude/mkt/assets/qr.png").convert("RGBA").resize((size, size), Image.NEAREST)
    return q
