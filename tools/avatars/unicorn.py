"""Unicorn: a chubby pastel unicorn sitting front-on, with a rainbow mane, a gold spiral horn and lilac hooves."""

import math
import random
from PIL import Image, ImageChops, ImageFilter

from ink import GROUND, SS, Canvas, capsule, ellipse, rotate, scale, wobble

ID = 'unicorn'
NAME = 'Unicorn'

INK = (44, 38, 66)
COAT = (255, 254, 252)
COAT_HATCH = ((214, 208, 238), (255, 255, 255))
SHADE = (226, 222, 244)
MUZZLE = (255, 226, 234)
NOSTRIL = (226, 128, 162)
MOUTH = (236, 110, 146)
TONGUE = (255, 190, 206)
IRIS = (112, 82, 168)
BLUSH = (255, 146, 178)
BLUSH_MARK = (255, 236, 242)
EAR = (252, 178, 204)
HOOF = (180, 152, 230)
SOLE = (148, 118, 208)
HOOF_SHINE = (214, 198, 248)
GOLD = (252, 212, 122)
GOLD_SHADE = (228, 166, 78)
GROOVE = (204, 136, 56)
GOLD_SHINE = (255, 240, 192)
YELLOW = (255, 220, 126)
PINK = (252, 164, 196)
LILAC = (190, 160, 240)
TEAL = (122, 214, 204)
SPARK = (198, 170, 248)
HEART = (252, 150, 186)
WHITE = (255, 255, 255)

OUTER, LOCK, DETAIL, SILHOUETTE = 2.1, 1.7, 1.5, 2.5
SIZE = .87
CX = 64
HEAD = (64, 50)
NECK = (64, 82)
SHOULDER, FOOT = 84, 109.5

TAIL = (
    ([(86, 104), (100, 106), (110, 104), (116, 99)], 5.2, LILAC),
    ([(86, 101), (99, 101), (109, 95), (113, 86), (110, 80), (106, 82)], 6.2, PINK),
    ([(85, 98), (95, 96), (103, 89), (105, 80), (101, 75), (97, 78)], 5.4, TEAL),
)
MANE = (
    ([(43, 27), (34, 37), (28, 52), (26, 66), (23, 77), (17, 80), (14, 75), (18, 71)], 7.6, YELLOW),
    ([(45, 31), (37, 43), (32, 58), (31, 72), (28, 83), (22, 87), (19, 82), (22, 79)], 7.4, PINK),
    ([(46, 37), (40, 51), (37, 65), (37, 77), (35, 86), (31, 90)], 6.4, LILAC),
    ([(47, 43), (42, 55), (41, 65), (42, 72), (45, 75)], 4.6, TEAL),
    ([(86, 31), (93, 40), (97, 52), (98, 60), (101, 65), (105, 63), (104, 59)], 6.2, LILAC),
    ([(84, 37), (89, 47), (91, 57), (90, 63)], 4.4, TEAL),
)
FORELOCK = (
    ([(60, 27), (53, 29), (47, 33), (45, 38), (47, 41)], 5.6, LILAC),
    ([(62, 29), (70, 32), (77, 37), (80, 43)], 5, TEAL),
    ([(58, 26), (66, 26), (75, 29), (83, 34), (87, 41), (86, 47), (82, 48)], 7.4, PINK),
    ([(70, 25), (78, 27), (85, 31)], 4.4, YELLOW),
)
SPARKLES = (
    ((104, 26, 4.4, SPARK), (115, 40, 2.4, WHITE), (95, 14, 2.4, WHITE), (24, 24, 3.2, WHITE), (15, 38, 2.2, WHITE)),
    ((104, 26, 3, WHITE), (115, 40, 3.4, SPARK), (95, 14, 2, WHITE), (24, 24, 4, SPARK), (15, 38, 2.8, WHITE)),
)
HEARTS = ((107, 34, 4.2), (20, 36, 3.6), (97, 21, 3))


def pose(**changes):
    values = dict(lift=0, sx=1, sy=1, head=0, bob=0, eyes='content', mouth='smile', wave=0, tail=0,
                  phase=0, extras=('sparkle',))
    values.update(changes)
    return values


def union(canvas, shapes):
    region = Image.new('L', canvas.image.size, 0)
    for pts in shapes:
        region = ImageChops.lighter(region, canvas.mask(pts))
    return region


def shade(colour, k):
    return tuple(int(c * k) for c in colour)


def lighten(colour, k):
    return tuple(int(c + (255 - c) * k) for c in colour)


def soft(canvas, pts, blur):
    return canvas.mask(pts).filter(ImageFilter.GaussianBlur(blur * SS))


def clip(mask, region):
    return ImageChops.multiply(mask, region)


def glaze(canvas, colour, mask, alpha=255):
    layer = Image.new('RGBA', canvas.image.size, colour + (0,))
    layer.putalpha(mask.point(lambda v: v * alpha // 255))
    canvas.image.alpha_composite(layer)


def ring(canvas, region, width):
    blurred = region.filter(ImageFilter.GaussianBlur(width * SS * .37))
    canvas.paint(canvas.ink, ImageChops.subtract(blurred.point(lambda v: 255 if v > 22 else 0),
                                                 blurred.point(lambda v: 255 if v > 233 else 0)))


def coat(canvas, rng, region, shadow):
    canvas.paint(COAT, region)
    shadow = clip(shadow, region)
    glaze(canvas, SHADE, shadow, 235)
    canvas.hatch_colours = COAT_HATCH
    canvas.hatch(shadow, rng, spacing=2.8)


def tinted(canvas, rng, region, colour, spacing=3.4):
    canvas.paint(colour, region)
    canvas.hatch_colours = shade(colour, .86), lighten(colour, .35)
    canvas.hatch(region, rng, spacing=spacing)


def squircle(cx, cy, w, h, n=2.4, flare=0, steps=180):
    pts = []
    for k in range(steps):
        t = math.tau * k / steps
        c, s = math.cos(t), math.sin(t)
        x = w / 2 * math.copysign(abs(c) ** (2 / n), c)
        y = h / 2 * math.copysign(abs(s) ** (2 / n), s)
        pts.append((cx + x * (1 + flare * y / (h / 2)), cy + y))
    return pts


def smooth(pts, rounds=3):
    for _ in range(rounds):
        out = []
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            out += [(p[0] * .75 + q[0] * .25, p[1] * .75 + q[1] * .25),
                    (p[0] * .25 + q[0] * .75, p[1] * .25 + q[1] * .75)]
        pts = out
    return pts


def spline(pts, per=16):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1:i + 3]
        for k in range(per):
            t = k / per
            out.append(tuple(.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                   + (3 * b - a - 3 * c + d) * t ** 3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-2])
    return out


def strand(pts, root, tip=.5, taper=.8):
    line = spline(pts)
    n = len(line) - 1
    centre = []
    for k, (x, y) in enumerate(line):
        px, py = line[max(k - 1, 0)]
        qx, qy = line[min(k + 1, n)]
        centre.append((x, y, math.atan2(qy - py, qx - px), root * (1 - k / n) ** taper + tip))
    return centre


def side(centre, lo, hi, start=0, end=None):
    centre = centre[start:end]
    left = [(x - math.sin(a) * r * lo, y + math.cos(a) * r * lo) for x, y, a, r in centre]
    right = [(x - math.sin(a) * r * hi, y + math.cos(a) * r * hi) for x, y, a, r in centre]
    return left + right[::-1]


def outline_of(centre):
    x, y, a, r = centre[0]
    cap = [(x + r * math.cos(a + math.pi / 2 + math.pi * k / 16), y + r * math.sin(a + math.pi / 2 + math.pi * k / 16))
           for k in range(1, 16)]
    return side(centre, -1, 1) + cap


def lock(canvas, rng, pts, root, colour, place):
    centre = strand(pts, root)
    n = len(centre)
    shape = place(wobble(outline_of(centre), rng, .04))
    region = canvas.mask(shape)
    tinted(canvas, rng, region, colour, 3.8)
    shine = canvas.mask(place(side(centre, -.61, -.29, int(n * .1), int(n * .62))))
    canvas.paint(lighten(colour, .55), clip(shine, region))
    shadow = canvas.mask(place(side(centre, .55, 1.1, 0, int(n * .8))))
    glaze(canvas, shade(colour, .82), clip(shadow, region), 150)
    canvas.paint(canvas.ink, canvas.stroke_mask(shape, LOCK, rng))


def horn(canvas, rng, place, lit=False):
    base_y, tip_y, width = 28, 7.5, 14

    def half(t):
        return width / 2 * (1 - t) ** .85

    def at(t):
        return base_y + (tip_y - base_y) * t

    ts = [k / 40 for k in range(41)]
    cone = smooth([(CX - half(t), at(t)) for t in ts] + [(CX + half(t), at(t)) for t in ts[::-1]]
                  + [(CX + 3, base_y + 1.6), (CX - 3, base_y + 1.6)], 2)
    shape = place(wobble(cone, rng, .03))
    region = canvas.mask(shape)
    canvas.paint(GOLD, region)
    shadow = soft(canvas, place([(CX + 1.5, base_y + 2), (CX + width / 2 + 2, base_y + 2), (CX + 1, tip_y)]), 1.4)
    glaze(canvas, GOLD_SHADE, clip(shadow, region), 150)
    for t in (.16, .38, .58, .76):
        a = (CX - half(t) - 1, at(t))
        b = (CX + half(t + .1) + 1, at(t + .1))
        groove = [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 1.4 * (1 - t)), b]
        canvas.paint(GROOVE, clip(canvas.stroke_mask(place(spline(groove, 8)), 1.7, rng, closed=False), region))
    shine = [(CX - half(.08) * .55, at(.08)), (CX - half(.6) * .5, at(.6))]
    canvas.paint(GOLD_SHINE, clip(canvas.stroke_mask(place(shine), 1.3, rng, closed=False), region))
    if lit:
        glaze(canvas, GOLD_SHINE, region, 150)
    canvas.paint(canvas.ink, canvas.stroke_mask(shape, LOCK, rng))


def star(canvas, rng, x, y, r, colour):
    pts = smooth([(x + (r if k % 2 == 0 else r * .28) * math.cos(math.pi / 4 * k - math.pi / 2),
                   y + (r if k % 2 == 0 else r * .28) * math.sin(math.pi / 4 * k - math.pi / 2)) for k in range(8)], 2)
    canvas.paint(canvas.ink, canvas.stroke_mask(pts, 2.1, rng))
    canvas.paint(colour, canvas.mask(pts))


def heart(cx, cy, size):
    return [(cx + size * 16 * math.sin(t) ** 3 / 17,
             cy - size * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17)
            for t in (math.tau * k / 60 for k in range(60))]


def accent(canvas, rng, pts, colour, width=1.8):
    canvas.line(pts, width + 1.8, rng)
    canvas.line(pts, width, rng, colour)


def draw_eyes(canvas, rng, kind, face):
    for s in (-1, 1):
        ex, ey = CX + s * 14.5, HEAD[1] + 1
        if kind == 'content':
            canvas.line(face([(ex - 5.6, ey + 1.4), (ex - 2.8, ey - 2.2), (ex + 2.8, ey - 2.2), (ex + 5.6, ey + 1.4)]),
                        2.5, rng)
            lx, ly = ex + s * 5.6, ey + 1.4
            canvas.line(face([(lx, ly), (lx + s * 2.6, ly - 1.6)]), 1.4, rng)
            canvas.line(face([(lx - s * 1, ly - 1.6), (lx + s * 1.2, ly - 3.8)]), 1.3, rng)
        elif kind == 'closed':
            canvas.line(face([(ex - 5.6, ey - .6), (ex - 2.8, ey + 2), (ex + 2.8, ey + 2), (ex + 5.6, ey - .6)]),
                        2.4, rng)
            lx, ly = ex + s * 5.6, ey - .6
            canvas.line(face([(lx, ly), (lx + s * 2.2, ly + 1.2)]), 1.3, rng)
        else:
            w, h = {'open': (10, 12.5), 'wide': (11, 14), 'shine': (11, 13.5), 'focus': (10, 10)}[kind]
            dy = 1.2 if kind == 'focus' else 0
            canvas.paint(canvas.ink, canvas.mask(face(wobble(ellipse(ex, ey + dy, w, h), rng, .05))))
            canvas.paint(IRIS, canvas.mask(face(ellipse(ex, ey + dy + h * .24, w * .64, h * .4))))
            if kind == 'shine':
                sx, sy, r = ex - w * .12, ey - h * .14, w * .34
                glint = smooth([(sx + (r if k % 2 == 0 else r * .3) * math.cos(math.pi / 4 * k),
                                 sy + (r if k % 2 == 0 else r * .3) * math.sin(math.pi / 4 * k)) for k in range(8)], 2)
                canvas.paint(WHITE, canvas.mask(face(glint)))
            else:
                canvas.paint(WHITE, canvas.mask(face(ellipse(ex - w * .18, ey + dy - h * .18, w * .5, h * .42))))
            canvas.paint(WHITE, canvas.mask(face(ellipse(ex + w * .22, ey + dy + h * .2, w * .2, w * .2))))
            lx, ly = ex + s * w * .42, ey + dy - h * .32
            canvas.line(face([(lx, ly), (lx + s * 2.6, ly - 2)]), 1.4, rng)


def draw_mouth(canvas, rng, kind, face):
    mx, my = CX, HEAD[1] + 20
    if kind == 'smile':
        canvas.line(face([(mx - 4.4, my), (mx - 1.8, my + 2), (mx + 1.8, my + 2), (mx + 4.4, my)]), DETAIL + .1, rng)
    elif kind == 'flat':
        canvas.line(face([(mx - 3, my + 1), (mx + 3, my + 1.2)]), DETAIL + .1, rng)
    elif kind in ('open', 'o'):
        if kind == 'open':
            shape = face([(mx - 4.8, my - .4)] + [(mx + 4.8 * math.cos(math.radians(a)),
                                                   my - .4 + 5.2 * math.sin(math.radians(a))) for a in range(0, 181, 10)])
        else:
            shape = face(ellipse(mx, my + 1.8, 4.6, 5.4))
        canvas.paint(MOUTH, canvas.mask(shape))
        canvas.paint(TONGUE, clip(canvas.mask(face(ellipse(mx, my + 3.6, 4.8, 2.8))), canvas.mask(shape)))
        canvas.paint(canvas.ink, canvas.stroke_mask(shape, DETAIL + .1, rng))


def draw_leg(canvas, rng, x, place):
    mid = (SHOULDER + FOOT) / 2
    leg = place(wobble(squircle(x, mid, 14.5, FOOT - SHOULDER, 2.9), rng, .06))
    region = canvas.mask(leg)
    coat(canvas, rng, region, soft(canvas, place(ellipse(x + 6, mid, 8, FOOT - SHOULDER)), 1.8))
    cuff = clip(canvas.mask(place([(x - 10, FOOT - 8), (x + 10, FOOT - 8), (x + 10, FOOT + 6), (x - 10, FOOT + 6)])),
                region)
    tinted(canvas, rng, cuff, HOOF)
    rim = canvas.stroke_mask(place([(x - 6, FOOT - 6.5), (x + 5, FOOT - 6.5)]), 1.2, rng, closed=False)
    canvas.paint(HOOF_SHINE, clip(rim, cuff))
    seam = canvas.stroke_mask(place([(x - 8, FOOT - 8), (x + 8, FOOT - 8)]), DETAIL, rng, closed=False)
    canvas.paint(canvas.ink, clip(seam, region))
    canvas.paint(canvas.ink, canvas.stroke_mask(leg, OUTER - .3, rng))


def draw_wave(canvas, rng, angle, place):
    shoulder = (CX - 8, SHOULDER + 1)
    a = math.radians(angle + 90)
    end = (shoulder[0] + 21 * math.cos(a), shoulder[1] + 21 * math.sin(a))
    arm = place(wobble(capsule(*shoulder, *end, 7.4, 6.6), rng, .06))
    region = canvas.mask(arm)
    underside = [(shoulder[0] + 4, shoulder[1] + 3), (end[0] + 4, end[1] + 3), (end[0] + 1, end[1] + 6)]
    coat(canvas, rng, region, soft(canvas, place(underside), 2.4))
    canvas.paint(canvas.ink, canvas.stroke_mask(arm, OUTER - .3, rng))
    hx, hy = end[0] + 3.2 * math.cos(a), end[1] + 3.2 * math.sin(a)
    hoof = place(wobble(rotate(ellipse(hx, hy, 15.5, 12.5), (hx, hy), angle), rng, .05))
    tinted(canvas, rng, canvas.mask(hoof), HOOF)
    sx, sy = hx + 1.4 * math.cos(a), hy + 1.4 * math.sin(a)
    canvas.paint(SOLE, canvas.mask(place(rotate(ellipse(sx, sy, 10, 7.4), (sx, sy), angle))))
    canvas.paint(canvas.ink, canvas.stroke_mask(hoof, LOCK, rng))


def render(p, seed):
    rng = random.Random(seed)
    canvas = Canvas(*COAT_HATCH, INK)
    ground = GROUND - p['lift']
    anchor = (CX, ground - 1)

    def body(pts):
        return scale([(x, y - p['lift']) for x, y in pts], anchor, p['sx'] * SIZE, p['sy'] * SIZE)

    neck = body([NECK])[0]

    def head(pts):
        moved = body([(x, y + p['bob']) for x, y in pts])
        return rotate(moved, neck, p['head']) if p['head'] else moved

    for pts, root, colour in TAIL:
        lock(canvas, rng, rotate(pts, (86, 101), p['tail']), root, colour, body)

    haunches = union(canvas, [body(wobble(shape, rng, .1)) for s in (-1, 1)
                              for shape in (ellipse(CX + s * 25, 99, 28, 21), ellipse(CX + s * 20, 83, 32, 32))])
    shadow = ImageChops.lighter(soft(canvas, body(ellipse(CX - 31, 106, 26, 16)), 3),
                                soft(canvas, body(ellipse(CX + 26, 92, 30, 36)), 3))
    coat(canvas, rng, haunches, shadow)
    ring(canvas, haunches, OUTER)
    canvas.paint(HEART, canvas.mask(body(heart(CX - 27, 97, 3.6))))
    for s in (-1, 1):
        cx, cy = CX + s * 37, 102
        hoof = body(wobble(rotate(ellipse(cx, cy, 12.5, 15.5), (cx, cy), s * 12), rng, .05))
        tinted(canvas, rng, canvas.mask(hoof), HOOF)
        canvas.paint(SOLE, canvas.mask(body(rotate(ellipse(cx + s, cy + .6, 7, 10.5), (cx, cy), s * 12))))
        canvas.paint(canvas.ink, canvas.stroke_mask(hoof, LOCK, rng))

    torso = body(wobble(squircle(CX, 89, 44, 40, 2.3, .08), rng, .1))
    shadow = ImageChops.lighter(soft(canvas, body(ellipse(CX, 75, 50, 16)), 3),
                                soft(canvas, body(ellipse(CX + 16, 96, 16, 34)), 3))
    coat(canvas, rng, canvas.mask(torso), shadow)
    canvas.paint(canvas.ink, canvas.stroke_mask(torso, OUTER, rng))

    draw_leg(canvas, rng, CX + 9, body)
    if not p['wave']:
        draw_leg(canvas, rng, CX - 9, body)

    for pts, root, colour in MANE:
        lock(canvas, rng, pts, root, colour, head)

    hx, hy = HEAD
    for s in (-1, 1):
        ear = head(wobble(smooth([(hx + s * 14, hy - 21), (hx + s * 27, hy - 38), (hx + s * 30, hy - 13)]), rng, .04))
        coat(canvas, rng, canvas.mask(ear), soft(canvas, head(ellipse(hx + s * 26, hy - 18, 10, 12)), 2))
        inner = smooth([(hx + s * 18, hy - 20), (hx + s * 26, hy - 33), (hx + s * 27.5, hy - 17)])
        canvas.paint(EAR, canvas.mask(head(inner)))
        canvas.paint(canvas.ink, canvas.stroke_mask(ear, LOCK, rng))

    skull = squircle(hx, hy, 62, 50, 2.25, .05)
    snout = squircle(hx, hy + 16.5, 36, 21, 2.2)
    face = union(canvas, [head(wobble(skull, rng, .14)), head(wobble(snout, rng, .08))])
    shadow = ImageChops.lighter(soft(canvas, head(ellipse(hx + 24, hy + 4, 14, 46)), 3.4),
                                soft(canvas, head(ellipse(hx, hy - 22, 50, 10)), 2.6))
    coat(canvas, rng, face, ImageChops.lighter(shadow, soft(canvas, head(ellipse(hx, hy + 27, 34, 6)), 1.6)))
    glaze(canvas, MUZZLE, clip(soft(canvas, head(ellipse(hx, hy + 16.5, 32, 18)), 1.2), face))
    ring(canvas, face, OUTER)
    for s in (-1, 1):
        nx, ny = hx + s * 6.2, hy + 14.5
        canvas.paint(NOSTRIL, canvas.mask(head(rotate(ellipse(nx, ny, 3.2, 4.4), (nx, ny), s * 28))))
    draw_mouth(canvas, rng, p['mouth'], head)
    draw_eyes(canvas, rng, p['eyes'], head)
    extras = p['extras']
    for s in (-1, 1):
        bx, by = hx + s * 22.5, hy + 9
        canvas.tint(BLUSH, canvas.mask(head(ellipse(bx, by, 9.5, 5.2))), 215 if 'blush' in extras else 150)
        for k in (-1, 0, 1):
            canvas.line(head([(bx + k * 2.4 + .8, by - 1.3), (bx + k * 2.4 - .8, by + 1.3)]), .9, rng, BLUSH_MARK)

    if p['wave']:
        draw_wave(canvas, rng, p['wave'], body)
    for pts, root, colour in FORELOCK:
        lock(canvas, rng, pts, root, colour, head)
    horn(canvas, rng, head, 'glow' in extras)
    ring(canvas, canvas.image.getchannel('A'), SILHOUETTE)

    if 'glow' in extras:
        tip = head([(CX, 7.5)])[0]
        for k in range(5):
            a = math.radians(-90 + (k - 2) * 36)
            inner, outer = (4.5, 5, 4.5)[p['phase'] % 3], (9, 10.5, 9.5)[p['phase'] % 3]
            accent(canvas, rng, [(tip[0] + inner * math.cos(a), tip[1] + inner * math.sin(a)),
                                 (tip[0] + outer * math.cos(a), tip[1] + outer * math.sin(a))], GOLD_SHINE, 1.4)
    if 'magic' in extras:
        for k, (x, y) in enumerate(((20, 46), (23, 33), (26, 20))):
            age = (p['phase'] - k) % 3
            star(canvas, rng, x, y, (2.4, 3.8, 2.8)[age], (WHITE, SPARK, WHITE)[age])
            star(canvas, rng, 128 - x, y + 6, (2.8, 2.4, 3.8)[age], (WHITE, WHITE, SPARK)[age])
    if 'sparkle' in extras:
        for x, y, r, c in SPARKLES[p['phase'] % 2]:
            star(canvas, rng, x, y - p['lift'], r, c)
    if 'hearts' in extras:
        for x, y, size in HEARTS:
            pts = heart(x, y - p['phase'] * 2 - p['lift'], size)
            canvas.paint(canvas.ink, canvas.stroke_mask(pts, 2, rng))
            canvas.paint(HEART, canvas.mask(pts))
    if 'motion' in extras:
        for s in (-1, 1):
            x = CX + s * 34
            canvas.line([(x - 4, GROUND - 1.5), (x + 4, GROUND - 1.5 + rng.uniform(-.3, .3))], 1.6, rng)
    if 'zzz' in extras:
        for zx, zy, zs in ((93, 24, 6.4), (104, 14, 4.8)):
            accent(canvas, rng, [(zx, zy), (zx + zs, zy), (zx, zy + zs), (zx + zs, zy + zs)], SPARK)
    if 'bang' in extras:
        bx, by = 98, 22
        accent(canvas, rng, [(bx, by - 9), (bx + .4, by)], SPARK, 2.5)
        canvas.paint(canvas.ink, canvas.mask(ellipse(bx + .5, by + 4.8, 5.2, 5.2)))
        canvas.paint(SPARK, canvas.mask(ellipse(bx + .5, by + 4.8, 3.2, 3.2)))
    return canvas.downsample()


NEUTRAL = pose()
BREATH = pose(sx=.99, sy=1.02, phase=1)
LOOK = pose(eyes='open', extras=())
HAPPY = pose(eyes='content', mouth='open', sy=.97, extras=('hearts', 'blush'))
HOP_LOW = pose(lift=5, sx=.97, sy=1.03, eyes='shine', mouth='open', tail=-10, extras=('motion',))
WAVE_UP = pose(eyes='wide', mouth='o', wave=142, head=-3, extras=('bang',))
WAVE_OUT = pose(eyes='wide', mouth='o', wave=118, head=-3, extras=('bang',))
CAST = pose(eyes='focus', mouth='flat', extras=('glow', 'magic'))

ANIMATIONS = {
    'idle': ('loop', [
        (NEUTRAL, 1100), (BREATH, 900), (NEUTRAL, 500), (LOOK, 1300), (pose(eyes='closed', extras=()), 140),
        (LOOK, 700), (pose(tail=-9), 260), (NEUTRAL, 600), (BREATH, 900),
    ]),
    'working': ('loop', [
        (CAST, 220), (pose(eyes='focus', mouth='flat', bob=.8, phase=1, extras=('glow', 'magic')), 220),
        (pose(eyes='focus', mouth='flat', phase=2, extras=('glow', 'magic')), 220),
    ]),
    'finished': ('once', [
        (pose(sx=1.05, sy=.92, eyes='content', mouth='smile', extras=()), 130),
        (HOP_LOW, 110),
        (pose(lift=8, sx=.98, sy=1.02, eyes='shine', mouth='open', tail=-16, extras=('motion',)), 160),
        (HOP_LOW, 100),
        (pose(sx=1.05, sy=.92, eyes='content', mouth='open', extras=()), 130),
        (pose(eyes='content', mouth='open', sy=.97, extras=('sparkle', 'blush')), 400),
    ]),
    'needs-you': ('hold', [
        (WAVE_UP, 200), (WAVE_OUT, 200), (WAVE_UP, 200), (WAVE_OUT, 200), (WAVE_UP, 200),
        (pose(eyes='wide', mouth='smile', wave=134, head=-5, extras=('bang',)), 600),
    ]),
    'resting': ('hold', [
        (pose(eyes='closed', mouth='smile', sy=.97, head=-7, bob=2.5, tail=6, extras=('zzz',)), 1000),
    ]),
    'hover': ('loop', [
        (HAPPY, 320),
        (pose(eyes='content', mouth='open', sy=.955, sx=1.01, phase=1, tail=8, extras=('hearts', 'blush')), 320),
    ]),
}
