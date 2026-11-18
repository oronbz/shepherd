"""Butter Stick: a squishy stick of butter with a kawaii face on its long side and a blue BUTTER wrapper print on top.

Like Squishy it is shaded smooth and glossy instead of hatched, so it reads as soft foam.
"""

import math
import random
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from ink import SS, Canvas, ellipse, rotate

ID = 'butter-stick'
NAME = 'Butter Stick'

FRONT = (252, 234, 132)
TOP = (255, 246, 182)
END = (238, 212, 104)
SHADE = (232, 196, 88)
LABEL = (104, 146, 206)
OUTLINE = (84, 78, 86)
EDGE = (176, 160, 96)
EYE = (40, 34, 40)
PINK = (246, 150, 160)
MOUTH = (226, 112, 130)
WHITE = (255, 255, 255)
HEART = (240, 132, 150)
ACCENT = (203, 166, 247)
DRIP = (255, 242, 168)

GROUND = (63, 104)
LINE = 2.6

FRONT_FACE = [(12, 70), (98, 70), (98, 104), (12, 104)]
DEPTH = (16, -16)


def pose(**changes):
    values = dict(lift=0, rise=0, sx=1, sy=1, tilt=0, melt=0, eyes='open', mouth='smile', extras=())
    values.update(changes)
    return values


def smooth(pts, rounds=3):
    for _ in range(rounds):
        out = []
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            out += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        pts = out
    return pts


def arc(cx, cy, rx, ry, start, end, steps=24):
    return [(cx + rx * math.cos(math.radians(start + (end - start) * k / steps)),
             cy + ry * math.sin(math.radians(start + (end - start) * k / steps))) for k in range(steps + 1)]


def heart(cx, cy, size):
    return [(cx + size * 16 * math.sin(t) ** 3 / 17,
             cy - size * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17)
            for t in (math.tau * k / 60 for k in range(60))]


def accent(canvas, pts, width, rng, colour=ACCENT):
    canvas.line(pts, width + 1.8, rng)
    canvas.line(pts, width, rng, colour)


def glaze(canvas, colour, mask, alpha):
    """Like Canvas.tint, but a soft mask fades the colour out instead of blending it toward black."""
    layer = Image.new('RGBA', canvas.image.size, colour + (0,))
    layer.putalpha(mask.point(lambda v: v * alpha // 255))
    canvas.image.alpha_composite(layer)


def shift(pts, d):
    return [(x + d[0], y + d[1]) for x, y in pts]


def faces():
    """The front, top and end faces of the stick, before rounding."""
    (fl, ft), (fr, _), (_, fb), _ = FRONT_FACE
    front = FRONT_FACE
    top = [(fl, ft), (fr, ft)] + shift([(fr, ft), (fl, ft)], DEPTH)
    end = [(fr, ft), (fr, fb)] + shift([(fr, fb), (fr, ft)], DEPTH)
    return front, top, end


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def on_top(u, v):
    """A point on the top face: u runs along the stick, v from the front edge back."""
    (fl, ft), (fr, _) = FRONT_FACE[0], FRONT_FACE[1]
    base = lerp((fl, ft), (fr, ft), u)
    return (base[0] + DEPTH[0] * v, base[1] + DEPTH[1] * v)


def solve_affine(src, dst):
    """The six coefficients mapping each dst point to its src point, for Image.transform(AFFINE)."""
    (x0, y0), (x1, y1), (x2, y2) = dst
    det = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    coeffs = []
    for k in (0, 1):
        s0, s1, s2 = src[0][k], src[1][k], src[2][k]
        a = ((s1 - s0) * (y2 - y0) - (s2 - s0) * (y1 - y0)) / det
        b = ((s2 - s0) * (x1 - x0) - (s1 - s0) * (x2 - x0)) / det
        coeffs += [a, b, s0 - a * x0 - b * y0]
    return coeffs


BASE_LINE = 103.6


def puddle(level):
    """An amorphous melted puddle around the base, with lobes that flow as it grows (level 0 to 1).

    Returns the puddle and a few loose droplets; nothing reaches below the stick's own base line.
    """
    phase = level * 1.4
    pts = []
    for k in range(96):
        a = math.tau * k / 96
        wave = (1 + .16 * math.sin(2 * a + .4 + phase) + .1 * math.sin(3 * a + 1.7 - phase)
                + .07 * math.sin(5 * a + .3 + phase * .6) + .04 * math.sin(8 * a + 2))
        rx, ry = (34 + 14 * level) * wave, (6 + 9 * level) * wave
        pts.append((rx * math.cos(a), ry * math.sin(a)))
    reach = max(abs(x) for x, _ in pts)
    squeeze = min(1, 52 / reach)
    bottom = max(y for _, y in pts)
    pool = smooth([(62 + x * squeeze, y - bottom + BASE_LINE) for x, y in pts], 1)
    drops = []
    for x, y, r in ((12, 100, 2.6), (112, 97, 2.2), (104, 102, 1.5)):
        size = r * min(1, level * 1.6)
        if size > 1:
            drops.append(ellipse(x, y, size * 2.2, size * 1.4))
    return pool, drops


def print_label(canvas, place, clip):
    """Draws the wrapper print flat onto the top face: 4oz. over a bar, then BUTTER under a bar."""
    w, h = int(76 * SS), int(18 * SS)
    label = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(label)

    def word(text, size, centre_x):
        font = ImageFont.load_default(int(size * SS))
        box = draw.textbbox((0, 0), text, font=font)
        tw, th = box[2] - box[0], box[3] - box[1]
        draw.text((centre_x - tw / 2 - box[0], (h - th) / 2 - box[1]), text, font=font, fill=255)
        return tw

    small = word('4oz.', 8.8, w * .19)
    big = word('BUTTER', 9.5, w * .64)
    draw.rounded_rectangle((w * .19 - small / 2, h * .84, w * .19 + small / 2 + w * .04, h * .96), radius=h * .06, fill=255)
    draw.rounded_rectangle((w * .64 - big * .3, h * .02, w * .64 + big * .5, h * .14), radius=h * .06, fill=255)
    corners = [on_top(.08, .9), on_top(.92, .9), on_top(.08, .1)]
    dst = [(x * SS, y * SS) for x, y in place(corners)]
    src = [(0, 0), (w, 0), (0, h)]
    warped = label.transform(canvas.image.size, Image.AFFINE, solve_affine(src, dst), resample=Image.BICUBIC)
    canvas.paint(LABEL, ImageChops.multiply(warped, clip))


def draw_stick(canvas, rng, place, front, top, end, region, soft, inside):
    """The solid stick: faces, wrapper print, edges, outline and shine."""
    canvas.paint(FRONT, region)
    canvas.paint(TOP, inside(canvas.mask(place(top))))
    canvas.paint(END, inside(canvas.mask(place(end))))
    glaze(canvas, SHADE, inside(soft(canvas.mask(place(ellipse(56, 112, 110, 22))), 4)), 150)
    glaze(canvas, WHITE, inside(soft(canvas.mask(place(ellipse(44, 58, 66, 9))), 3)), 110)
    print_label(canvas, place, inside(canvas.mask(place(top))))

    for a, b in ((front[0], front[1]), (front[1], front[2]), (front[1], top[2])):
        crease = canvas.stroke_mask(place([lerp(a, b, t) for t in (.16, .5, .84)]), 2.6, rng, closed=False)
        glaze(canvas, EDGE, inside(soft(crease, 1.1)), 120)

    blurred = soft(region, LINE * .37)
    ring = ImageChops.subtract(blurred.point(lambda v: 255 if v > 22 else 0), blurred.point(lambda v: 255 if v > 233 else 0))
    canvas.paint(OUTLINE, ring)

    canvas.line(place([(17, 76), (17.6, 88)]), 2.6, rng, WHITE)
    canvas.paint(WHITE, canvas.mask(place(ellipse(17.8, 94, 2.4, 3))))
    canvas.line(place([(101.5, 71), (104, 68.5)]), 1.6, rng, WHITE)


def draw_face(canvas, rng, fplace, p):
    cx, cy = 55, 86
    eyes, mouth = p['eyes'], p['mouth']
    for side in (-1, 1):
        ex, ey = cx + side * 16, cy
        if eyes in ('open', 'wide'):
            r = 3.4 if eyes == 'open' else 4.2
            canvas.paint(EYE, canvas.mask(fplace(ellipse(ex, ey, r * 2, r * 2.2))))
            canvas.paint(WHITE, canvas.mask(fplace(ellipse(ex - 1, ey - 1.2, 1.8, 1.8))))
        elif eyes == 'happy':
            canvas.line(fplace([(ex - 4, ey + 1.6), (ex - 2, ey - 1.6), (ex, ey - 2.4), (ex + 2, ey - 1.6), (ex + 4, ey + 1.6)]), 2.2, rng, EYE)
        elif eyes in ('closed', 'blink'):
            canvas.line(fplace([(ex - 4, ey), (ex - 2, ey + 2.2), (ex, ey + 2.6), (ex + 2, ey + 2.2), (ex + 4, ey)]), 2.2, rng, EYE)
        elif eyes == 'squeeze':
            for dy in (-2.6, 2.6):
                canvas.line(fplace([(ex - side * 4.2, ey + dy), (ex + side * 3, ey)]), 2.2, rng, EYE)
        canvas.paint(PINK, canvas.mask(fplace(ellipse(cx + side * 27, cy + 6, 11, 7))))
    my = cy + 5
    if mouth == 'smile':
        jaw = arc(cx, my, 5, 5.6, 0, 180)
        canvas.paint(EYE, canvas.mask(fplace(arc(cx, my, 6.4, 7, 0, 180))))
        canvas.paint(MOUTH, canvas.mask(fplace(jaw)))
    elif mouth == 'flat':
        canvas.line(fplace([(cx - 3.5, my + 2), (cx + 3.5, my + 2)]), 1.8, rng, EYE)
    elif mouth == 'o':
        canvas.paint(EYE, canvas.mask(fplace(ellipse(cx, my + 2.4, 6.4, 7.4))))
        canvas.paint(MOUTH, canvas.mask(fplace(ellipse(cx, my + 2.4, 4.2, 5))))
    elif mouth == 'w':
        canvas.line(fplace([(cx - 4.4, my), (cx - 2.2, my + 2.4), (cx, my), (cx + 2.2, my + 2.4), (cx + 4.4, my)]), 1.7, rng, EYE)


def render(p, seed):
    rng = random.Random(seed)
    canvas = Canvas(FRONT, FRONT, OUTLINE)
    tilt = p['tilt']

    def placer(sx, sy):
        def place(pts):
            pts = [(GROUND[0] + (x - GROUND[0]) * sx, GROUND[1] + (y - GROUND[1]) * sy - p['rise']) for x, y in pts]
            return rotate(pts, (GROUND[0], GROUND[1] - p['rise']), tilt) if tilt else pts
        return place

    # Melting leaves less of him: the stick shrinks into the puddle spreading around it.
    melt = p['melt']
    shrunk = placer(p['sx'] * (1 - .14 * melt), p['sy'] * (1 - .22 * melt))
    # He sits in the middle of his puddle, so its front edge shows below him.
    wade = (6 + 9 * melt) * .75 if melt else 0

    def place(pts):
        return [(x, y - wade) for x, y in shrunk(pts)]

    front, top, end = faces()
    corners = [front[0], top[3], top[2], end[2], front[2], front[3]]
    outline = smooth([pt for i, c in enumerate(corners)
                      for pt in (lerp(c, corners[i - 1], .22), c, lerp(c, corners[(i + 1) % 6], .22))], 4)
    region = canvas.mask(place(outline))
    soft = lambda m, r: m.filter(ImageFilter.GaussianBlur(r * SS))
    inside = lambda m: ImageChops.multiply(m, region)

    if melt:
        flat = placer(p['sx'], p['sy'])
        shape, drops = puddle(melt)
        pool = flat(shape)
        top_y = min(y for _, y in shape)
        mask = canvas.mask(pool)
        canvas.paint(DRIP, mask)
        glaze(canvas, SHADE, ImageChops.multiply(mask, soft(canvas.mask(flat(ellipse(62, BASE_LINE + 6, 120, 10))), 2)), 120)
        glaze(canvas, WHITE, ImageChops.multiply(mask, soft(canvas.mask(flat(ellipse(44, top_y + 3, 40, 5))), 1.5)), 150)
        canvas.paint(OUTLINE, canvas.stroke_mask(pool, 2.4, rng, jitter=.04))
        for drop in drops:
            drop = flat(drop)
            canvas.paint(DRIP, canvas.mask(drop))
            canvas.paint(OUTLINE, canvas.stroke_mask(drop, 1.8, rng, jitter=.03))
        canvas.line(flat([(28, top_y + 4), (36, top_y + 2.6)]), 1.5, rng, WHITE)
        canvas.line(flat([(92, BASE_LINE - 2.4), (98, BASE_LINE - 3)]), 1.3, rng, WHITE)

    draw_stick(canvas, rng, place, front, top, end, region, soft, inside)
    draw_face(canvas, rng, place, p)

    extras = p['extras']
    if 'sweat' in extras:
        drop = [(110, 36), (107, 43), (108, 47), (112, 47), (113, 43)]
        canvas.paint(OUTLINE, canvas.mask([(110 + (x - 110) * 1.4, 43 + (y - 43) * 1.3) for x, y in drop]))
        canvas.paint((196, 222, 250), canvas.mask(drop))
    if 'bang' in extras:
        bx, by = 104, 22
        accent(canvas, [(bx, by - 8), (bx + .4, by)], 2.4, rng)
        canvas.paint(OUTLINE, canvas.mask(ellipse(bx + .5, by + 4.2, 4.8, 4.8)))
        canvas.paint(ACCENT, canvas.mask(ellipse(bx + .5, by + 4.2, 3, 3)))
    if 'zzz' in extras:
        for zx, zy, zs in ((96, 44, 6.5), (106, 33, 5)):
            accent(canvas, [(zx, zy), (zx + zs, zy), (zx, zy + zs), (zx + zs, zy + zs)], 1.7, rng)
    if 'sparkle' in extras:
        for sx_, sy_, r in ((14, 30, 4.6), (112, 24, 3.8)):
            cross = ([(sx_ - r, sy_), (sx_ + r, sy_)], [(sx_, sy_ - r), (sx_, sy_ + r)])
            for stroke in cross:
                canvas.line(stroke, 3.6, rng)
            for stroke in cross:
                canvas.line(stroke, 1.8, rng, ACCENT)
    if 'hearts' in extras:
        for hx, hy, s in ((16, 30, 5.2), (30, 18, 3.6), (40, 32, 3.2)):
            canvas.paint(OUTLINE, canvas.mask(heart(hx, hy, s + .9)))
            canvas.paint(HEART, canvas.mask(heart(hx, hy, s)))
    return canvas.downsample()


NEUTRAL = pose()


def rise_back(start, steps, **face):
    """A slow-rise foam recovery: each step closes most of the remaining squash and lingers longer."""
    frames = []
    sx, sy = start
    for i in range(steps):
        sx, sy = 1 + (sx - 1) * .55, 1 + (sy - 1) * .55
        frames.append((pose(sx=round(sx, 3), sy=round(sy, 3), **face), 150 + 70 * i))
    return frames


ANIMATIONS = {
    'idle': ('loop', [
        (NEUTRAL, 900), (pose(sx=1.02, sy=.98), 500), (pose(sx=1.03, sy=.97), 600), (pose(sx=1.02, sy=.98), 500),
        (NEUTRAL, 700), (pose(eyes='blink'), 120), (NEUTRAL, 800),
        (pose(sx=1.08, sy=.9, eyes='happy'), 160), *rise_back((1.08, .9), 3, eyes='happy'), (NEUTRAL, 600),
    ]),
    'working': ('loop', [
        (pose(mouth='flat'), 260),
        *[(pose(lift=1, mouth='flat', melt=m), 240) for m in (.25, .45, .65, .85, 1, .85, .65, .45, .25)],
    ]),
    'finished': ('once', [
        (pose(sx=1.08, sy=.86, eyes='squeeze'), 160),
        (pose(lift=1, rise=8, sx=.94, sy=1.08, eyes='happy', mouth='smile'), 100),
        (pose(lift=1, rise=14, eyes='happy', mouth='smile', extras=('sparkle',)), 200),
        (pose(lift=1, rise=6, sx=.96, sy=1.05, eyes='happy', mouth='smile'), 90),
        (pose(sx=1.08, sy=.84, eyes='happy', mouth='smile'), 140),
        *rise_back((1.08, .84), 3, eyes='happy', mouth='smile'),
        (pose(eyes='happy', mouth='smile', extras=('hearts',)), 600),
    ]),
    'needs-you': ('hold', [
        (pose(sx=1.06, sy=.93, eyes='wide', mouth='o'), 100),
        (pose(lift=1, rise=6, eyes='wide', mouth='o', extras=('bang',)), 160),
        (pose(sx=1.05, sy=.95, eyes='wide', mouth='o', extras=('bang',)), 120),
        (pose(lift=1, rise=4, tilt=3, eyes='wide', mouth='o', extras=('bang',)), 160),
        (pose(eyes='wide', mouth='w', tilt=-3, extras=('bang', 'sweat')), 600),
    ]),
    'resting': ('hold', [
        (pose(eyes='closed', mouth='w', melt=1, extras=('zzz',)), 1000),
    ]),
    'hover': ('loop', [
        (pose(sx=1.08, sy=.84, eyes='squeeze', mouth='o'), 160),
        *rise_back((1.08, .84), 3, eyes='happy', mouth='smile', extras=('hearts',)),
        (pose(eyes='happy', mouth='smile', extras=('hearts',)), 500),
    ]),
}
