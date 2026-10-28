"""ASAPROJECT archive/military hoodie: print-ready artwork at 300 dpi.

All sizes are in millimetres at print scale and converted with MM (px per mm).
Every plate is built as a hard-edged mask so it can go straight to film.
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree

DPI = 300
MM = DPI / 25.4          # 11.81 px per mm
INCH = DPI

HERE = os.path.dirname(os.path.abspath(__file__))
INTER_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
BARLOW_XBOLD = os.path.join(HERE, "fonts", "barlow-condensed-latin-800-normal.woff")   # SIL OFL 1.1
BARLOW_BOLD = os.path.join(HERE, "fonts", "barlow-condensed-latin-700-normal.woff")

BONE = (232, 226, 210)    # match to a Pantone drawdown on the washed-black fleece
NEON = (255, 46, 136)     # fluorescent pink, Pantone 806 C


def px(mm):
    return max(1, round(mm * MM))


def hard(mask):
    """Threshold an anti-aliased mask at 50%: film can't hold soft alpha."""
    return np.asarray(mask) >= 128


def to_img(a):
    return Image.fromarray(np.where(a, 255, 0).astype(np.uint8))


def grow(a, r):
    return ndimage.distance_transform_edt(~a) <= r


def shrink(a, r):
    return ndimage.distance_transform_edt(a) > r


def opening(a, r):
    return grow(shrink(a, r), r) & a


def closing(a, r):
    return shrink(grow(a, r), r) | a


def drop_specks(a, min_mm2=0.5):
    lbl, n = ndimage.label(a)
    if not n:
        return a
    sizes = ndimage.sum(a, lbl, index=np.arange(1, n + 1))
    tiny = np.zeros(n + 1, bool)
    tiny[1:] = sizes < min_mm2 * MM * MM
    return a & ~tiny[lbl]


def _font(path, cap_h):
    probe = ImageFont.truetype(path, 1000)
    b = probe.getbbox("H")
    return ImageFont.truetype(path, round(cap_h * 1000 / (b[3] - b[1])))


# ---------------------------------------------------------------- type

def glyph(ch, cap_h, font_path=INTER_BLACK, squeeze=0.8):
    f = _font(font_path, cap_h)
    bb = f.getbbox(ch)
    im = Image.new("L", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), 0)
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), ch, font=f, fill=255)
    im = im.resize((max(1, round(im.width * squeeze)), im.height), Image.LANCZOS)
    return im.crop(im.getbbox())


def _ink_runs(col):
    runs, y, h = [], 0, len(col)
    while y < h:
        if col[y]:
            y0 = y
            while y < h and col[y]:
                y += 1
            runs.append((y0, y))
        y += 1
    return runs


def _stem_end(a, row):
    xs = np.where(a[row])[0]
    x = xs[0]
    while x + 1 < a.shape[1] and a[row, x + 1]:
        x += 1
    return x


def stencil_glyph(ch, cap_h, bridge=0.10, squeeze=0.8):
    """Glyph with military-stencil bridges. Returns (bool mask, [bridge rects])."""
    a = hard(glyph(ch, cap_h, squeeze=squeeze)).copy()
    h, w = a.shape
    gap = max(2, round(cap_h * bridge))
    rects = []
    if ch == "A":
        # bridge through the crossbar; the apex stays solid
        cx = w // 2
        runs = _ink_runs(a[:, cx])
        y0, y1 = runs[1] if len(runs) > 1 else runs[0]
        rects.append((cx - gap // 2, y0, cx - gap // 2 + gap, y1))
    elif ch == "O":
        cx = w // 2
        rects.append((cx - gap // 2, 0, cx - gap // 2 + gap, h))
    elif ch in "PR":
        x = _stem_end(a, h // 4)
        ys = np.where(a[:, min(w - 1, x + gap + 2)])[0]
        bowl_bottom = ys[ys < h * 0.75].max()
        rects.append((x + 1, 0, x + 1 + gap, bowl_bottom + 1))
    elif ch == "E":
        x = _stem_end(a, h // 3)
        rects.append((x + 1, 0, x + 1 + gap, h))
    for x0, y0, x1, y1 in rects:
        a[y0:y1, x0:x1] = False
    return a, rects


def stencil_word(text, cap_h, tracking=0.13, bridge=0.10):
    """Stencil word. Letter gaps (tracking) stay ~30% wider than the bridges so each
    letter's pieces group together. Returns (mask, bridge rects, letter x-extents)."""
    parts = [stencil_glyph(c, cap_h, bridge) for c in text]
    track = round(cap_h * tracking)
    W = sum(p[0].shape[1] for p in parts) + track * (len(parts) - 1)
    H = max(p[0].shape[0] for p in parts)
    out = np.zeros((H, W), bool)
    rects, letters, x = [], [], 0
    for m, rs in parts:
        y = (H - m.shape[0]) // 2   # round letters overshoot equally top and bottom
        out[y:y + m.shape[0], x:x + m.shape[1]] |= m
        rects += [(x0 + x, y0 + y, x1 + x, y1 + y) for x0, y0, x1, y1 in rs]
        letters.append((x, x + m.shape[1]))
        x += m.shape[1] + track
    return out, rects, letters


def text_line(text, cap_h, font_path, tracking=0.0):
    """Caps at the font's natural width on one shared baseline (never squeezed)."""
    f = _font(font_path, cap_h)
    track = cap_h * tracking
    width = sum(f.getlength(c) for c in text) + track * (len(text) - 1)
    im = Image.new("L", (round(width) + 8, round(cap_h * 2)), 0)
    d = ImageDraw.Draw(im)
    x = 4.0
    for c in text:
        d.text((x, 4), c, font=f, fill=255)
        x += f.getlength(c) + track
    return hard(im.crop(im.getbbox()))


def fit_width(mask, width):
    im = to_img(mask)
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    return hard(im)


def scale_rects(rects, k):
    return [tuple(round(v * k) for v in r) for r in rects]


# ---------------------------------------------------------------- emblem

def _spike(d, cx, cy, ang, length, base):
    """Tapered barb spike from the wire axis to a sharp tip."""
    tx, ty = cx + length * math.cos(ang), cy + length * math.sin(ang)
    nx, ny = -math.sin(ang) * base / 2, math.cos(ang) * base / 2
    d.polygon([(cx + nx, cy + ny), (tx, ty), (cx - nx, cy - ny)], fill=255)


def _ring(d, c, r, w):
    d.ellipse((c - r - w / 2, c - r - w / 2, c + r + w / 2, c + r + w / 2), fill=255)
    d.ellipse((c - r + w / 2, c - r + w / 2, c + r - w / 2, c + r - w / 2), fill=0)


def _arm(d, c, t, r0, r1, w):
    ct, st = math.cos(t), math.sin(t)
    nx, ny = -st * w / 2, ct * w / 2
    p0 = (c + r0 * ct, c + r0 * st)
    p1 = (c + r1 * ct, c + r1 * st)
    d.polygon([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
               (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)], fill=255)


def _angdist(a, b):
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


def back_emblem(diameter_mm=235):
    """Barbed-wire reticle for the back (9.25 in). Returns (bone, neon, bridge rects)."""
    D = px(diameter_mm)
    ss = 2
    S = D * ss
    c = S / 2
    mm = lambda v: v * MM * ss

    # ---- barbed wire: two 2.5 mm strands, one crossing every ~25 mm, cut at 1 o'clock
    barb_ang = math.radians(65)
    barb_reach = 9.0                                     # tips 9 mm from the wire axis
    barb_len = barb_reach / math.sin(barb_ang)
    R = S / 2 - mm(barb_reach) - mm(0.3)
    A, strand = mm(2.9), mm(2.5)
    n = round(2 * math.pi * R / mm(25) / 2)
    brk = math.radians(-60)

    def strand_img(phase):
        # stamp overlapping discs along the path: wide PIL polylines made of tiny
        # segments leave saw-tooth notches along the edges
        im = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(im)
        rr = strand / 2
        steps = int(2 * math.pi * R / (rr * 0.25))
        for i in range(steps):
            t = 2 * math.pi * i / steps
            r = R + A * math.sin(n * t + phase)
            x, y = c + r * math.cos(t), c + r * math.sin(t)
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
        return hard(im.resize((D, D), Image.LANCZOS))

    s0, s1 = strand_img(0), strand_img(math.pi)
    # over/under: at each crossing one strand passes over and the other is cut 1.2 mm clear
    cross0 = np.zeros((D, D), bool)   # crossings where strand 0 is on top
    cross1 = np.zeros((D, D), bool)
    win = Image.new("L", (D, D), 0), Image.new("L", (D, D), 0)
    dws = ImageDraw.Draw(win[0]), ImageDraw.Draw(win[1])
    cR = R / ss
    for k in range(2 * n):
        t = k * math.pi / n
        x, y = D / 2 + cR * math.cos(t), D / 2 + cR * math.sin(t)
        rr = 7 * MM
        dws[k % 2].ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
    cross0, cross1 = np.asarray(win[0]) > 0, np.asarray(win[1]) > 0
    s1 &= ~(cross0 & grow(s0, 1.2 * MM))
    s0 &= ~(cross1 & grow(s1, 1.2 * MM))
    wire = s0 | s1

    # 16 four-point barbs spread over the arc outside the break, clear of the crosshair axes
    gap_ang = mm(10) / R
    span = 2 * math.pi - 2 * gap_ang
    best = None
    for off in np.linspace(0, 1, 41):
        ts = [brk + gap_ang + (j + off) * span / 16 for j in range(16)]
        clear = min(_angdist(t, ax) for t in ts for ax in (0, math.pi / 2, math.pi, -math.pi / 2))
        if best is None or clear > best[0]:
            best = (clear, ts)
    barbs = Image.new("L", (S, S), 0)
    db2 = ImageDraw.Draw(barbs)
    for t in best[1]:
        bx, by = c + R * math.cos(t), c + R * math.sin(t)
        tang = t + math.pi / 2
        for sgn in (1, -1):
            for flip in (0, math.pi):
                _spike(db2, bx, by, tang + sgn * barb_ang + flip, mm(barb_len), mm(2.5))
        r0 = mm(2.6)
        db2.ellipse((bx - r0, by - r0, bx + r0, by + r0), fill=255)
    wire |= hard(barbs.resize((D, D), Image.LANCZOS))

    # the break: a short angled snip through both strands
    snip = Image.new("L", (D, D), 0)
    bx, by = D / 2 + cR * math.cos(brk), D / 2 + cR * math.sin(brk)
    tang = brk + math.pi / 2
    ang = tang + math.radians(60)                         # cut at 60 deg to the wire
    hw, hl = 6.25 * MM, 12 * MM                           # 12.5 mm gap along the wire
    ux, uy = math.cos(tang), math.sin(tang)
    vx, vy = math.cos(ang), math.sin(ang)
    ImageDraw.Draw(snip).polygon([
        (bx - hw * ux - hl * vx, by - hw * uy - hl * vy), (bx + hw * ux - hl * vx, by + hw * uy - hl * vy),
        (bx + hw * ux + hl * vx, by + hw * uy + hl * vy), (bx - hw * ux + hl * vx, by - hw * uy + hl * vy)], fill=255)
    wire &= ~(np.asarray(snip) > 0)

    # ---- reticle
    bone = Image.new("L", (S, S), 0)
    db = ImageDraw.Draw(bone)
    r_out = R - mm(barb_reach) - mm(4.0) - mm(3)          # 4 mm clear of the barb tips
    _ring(db, c, r_out, mm(6))
    r_in = r_out * 0.66
    _ring(db, c, r_in, mm(3))
    for deg in range(0, 360, 10):
        if deg % 90 == 0:
            continue
        t = math.radians(deg)
        major = deg % 30 == 0
        L, w = (mm(12), mm(2.5)) if major else (mm(7), mm(1.5))
        _arm(db, c, t, r_out - mm(3) - L, r_out - mm(2), w)
    for t in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        _arm(db, c, t, r_in, R - A - strand / 2 - mm(2.5), mm(5))

    # pink ASA: 65% of the inner ring, stencil bridges at 10% of cap height
    asa_w = round(2 * (r_in / ss) * 0.65)
    asa, asa_rects, _ = stencil_word("ASA", 400, tracking=0.13)
    sc = asa_w / asa.shape[1]
    asa = fit_width(asa, asa_w)
    asa_rects = scale_rects(asa_rects, sc)
    ah, aw = asa.shape
    clear = mm(4)
    for t, half in ((0, aw / 2), (math.pi, aw / 2), (math.pi / 2, ah / 2), (3 * math.pi / 2, ah / 2)):
        r0 = half * ss + clear
        _arm(db, c, t, r0, r_in, mm(1.5))
        dots = (0.35, 0.75) if t in (0, math.pi) else (0.3, 0.55, 0.8)
        for f in dots:
            r = r0 + (r_in - mm(1.5) - r0) * f
            x, y = c + r * math.cos(t), c + r * math.sin(t)
            db.ellipse((x - mm(1.5), y - mm(1.5), x + mm(1.5), y + mm(1.5)), fill=255)

    bone = hard(bone.resize((D, D), Image.LANCZOS)) | wire
    neon = np.zeros((D, D), bool)
    oy, ox = (D - ah) // 2, (D - aw) // 2
    neon[oy:oy + ah, ox:ox + aw] = asa
    bone &= ndimage.distance_transform_edt(~neon) > px(4)   # clear fabric around the pink
    rects = [(x0 + ox, y0 + oy, x1 + ox, y1 + oy) for x0, y0, x1, y1 in asa_rects]
    return bone, neon, rects


def chest_emblem(width_mm=89):
    """Puff-specific chest mark: heavy strokes, >= 2 mm gaps, flat pink ASA."""
    D = px(width_mm)
    ss = 3
    S = D * ss
    c = S / 2
    mm = lambda v: v * MM * ss
    bone = Image.new("L", (S, S), 0)
    db = ImageDraw.Draw(bone)

    barb_len, barb_ang = mm(4.5), math.radians(50)
    R = S / 2 - barb_len * math.sin(barb_ang) - mm(0.6)
    _ring(db, c, R, mm(2.0))                                 # single wire strand
    for kk in range(8):
        t = math.radians(22.5 + 45 * kk)
        bx, by = c + R * math.cos(t), c + R * math.sin(t)
        tang = t + math.pi / 2
        # puff can't hold sharp tips: barbs are 1.6 mm bars with round ends
        for sgn in (1, -1):
            a = tang + sgn * barb_ang
            L = barb_len - mm(0.8)
            p0 = (bx - L * math.cos(a), by - L * math.sin(a))
            p1 = (bx + L * math.cos(a), by + L * math.sin(a))
            db.line([p0, p1], fill=255, width=round(mm(1.6)))
            for x, y in (p0, p1):
                db.ellipse((x - mm(0.8), y - mm(0.8), x + mm(0.8), y + mm(0.8)), fill=255)
    wire_in = R - mm(1.0) - barb_len * math.sin(barb_ang)
    r_out = wire_in - mm(2.4) - mm(1.25)
    _ring(db, c, r_out, mm(2.5))
    r_in = r_out - mm(1.25) - mm(2.6) - mm(0.9)
    _ring(db, c, r_in, mm(1.8))

    # pink ASA, 12 mm cap height, flat print; a 0.8 mm bridge keeps the A's crossbar legible
    asa, _, _ = stencil_word("ASA", 400, tracking=0.13, bridge=0.067)
    cap = px(12)
    asa = hard(to_img(asa).resize((round(asa.shape[1] * cap / asa.shape[0]), cap), Image.LANCZOS))
    ah, aw = asa.shape
    for t, half in ((0, aw / 2), (math.pi, aw / 2), (math.pi / 2, ah / 2), (3 * math.pi / 2, ah / 2)):
        _arm(db, c, t, half * ss + mm(2.5), r_out + mm(1.25), mm(2.5))

    bone = hard(bone.resize((D, D), Image.LANCZOS))
    neon = np.zeros((D, D), bool)
    oy, ox = (D - ah) // 2, (D - aw) // 2
    neon[oy:oy + ah, ox:ox + aw] = asa
    # keep 2.5 mm of clear fabric between puff and the flat pink
    bone &= ndimage.distance_transform_edt(~neon) > px(2.5)
    return bone, neon


# ---------------------------------------------------------------- crack

def _lowfreq(rng, w, h, step):
    n = rng.random((max(2, h // step + 2), max(2, w // step + 2))).astype(np.float32)
    return np.asarray(Image.fromarray(n).resize((w, h), Image.BICUBIC), dtype=np.float32) - 0.5


def crack(ink, keep_out, seed=11):
    """Cracked plastisol that holds on press.

    Cells 4-10 mm; crack widths 0.5-0.8 mm, tapering to 0.5 mm (never thinner)
    at the ends; irregular polygonal chips of 0.8-2 mm along edges. No cracks on
    strokes of 3.2 mm or less, on small marks, or inside `keep_out`. Afterwards
    no ink sliver narrower than ~0.42 mm, no crack nibble narrower than ~0.34 mm
    and no ink island under 0.5 mm^2 survive."""
    rng = np.random.default_rng(seed)
    h, w = ink.shape
    sc = 0.5
    sw, sh = int(w * sc), int(h * sc)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    cell = 7 * MM * sc
    xx += _lowfreq(rng, sw, sh, int(cell * 1.6)) * cell * 0.6
    yy += _lowfreq(rng, sw, sh, int(cell * 1.6)) * cell * 0.6
    dens = _lowfreq(rng, sw, sh, int(cell * 5)) + 0.5
    n = int(sw * sh / (cell * cell) * 1.6)
    cand = rng.random((n, 2)) * [sw, sh]
    p = dens[cand[:, 1].astype(int), cand[:, 0].astype(int)]
    pts = cand[rng.random(n) < 0.35 + 0.65 * p]
    _, lab = cKDTree(pts).query(np.column_stack([xx.ravel(), yy.ravel()]), k=1, workers=-1)
    lab = np.asarray(Image.fromarray(lab.reshape(sh, sw).astype(np.int32)).resize((w, h), Image.NEAREST))
    edge = np.zeros((h, w), bool)
    edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]
    edge[1:, :] |= lab[1:, :] != lab[:-1, :]
    gate = _lowfreq(rng, w, h, int(7 * MM * 0.9))
    thr = -0.22
    edge &= gate > thr                                         # not every border has cracked
    dist = ndimage.distance_transform_edt(~edge)
    # width 0.8 mm in the middle of a crack, tapering to 0.5 mm where it dies out
    taper = np.clip((gate - thr) / 0.12, 0, 1) * (_lowfreq(rng, w, h, int(12 * MM)) + 0.5)
    cracks = dist <= (0.25 + 0.15 * taper) * MM

    # only strokes thicker than 3.2 mm crack; thin lines and small marks stay whole
    inside = ndimage.distance_transform_edt(ink)
    thick = grow(inside > 1.6 * MM, 1.6 * MM) & ink
    lbl, nlab = ndimage.label(thick)
    if nlab:
        area = ndimage.sum(thick, lbl, index=np.arange(1, nlab + 1))
        tiny = np.zeros(nlab + 1, bool)
        tiny[1:] = area < 15 * MM * MM
        thick &= ~tiny[lbl]
    allowed = thick & ~keep_out
    out = ink & ~(cracks & allowed)

    # chips: irregular 3-6 sided bites, 0.8-2 mm, along the edges of thick strokes
    border = allowed & (inside <= 1.5)
    ys, xs = np.nonzero(border)
    if len(xs):
        chips = Image.new("L", (w, h), 0)
        dc = ImageDraw.Draw(chips)
        for i in rng.choice(len(xs), size=max(1, len(xs) // 1500), replace=False):
            cx, cy = xs[i], ys[i]
            r = rng.uniform(0.4, 1.0) * MM
            k = rng.integers(3, 7)
            a0 = rng.uniform(0, 2 * math.pi)
            poly = [(cx + r * rng.uniform(0.6, 1.0) * math.cos(a0 + 2 * math.pi * j / k),
                     cy + r * rng.uniform(0.6, 1.0) * math.sin(a0 + 2 * math.pi * j / k)) for j in range(k)]
            dc.polygon(poly, fill=255)
        out &= ~(np.asarray(chips) > 0)

    # press-ready clean-up: drop ink slivers < ~0.42 mm and crack nibbles < ~0.34 mm
    out = opening(out, 2.5) | (ink & ~allowed)      # never touch the uncracked art
    out = closing(out, 2.0) & ink
    return drop_specks(out)


def keep_out_mask(shape, rects, margin_mm=3.0):
    m = np.zeros(shape, bool)
    for x0, y0, x1, y1 in rects:
        m[max(0, y0):y1, max(0, x0):x1] = True
    return grow(m, margin_mm * MM)


# ---------------------------------------------------------------- layouts

def back_art(width_in=14.0):
    """Back statement: wordmark 14 in, emblem 9.25 in, slogan 8 in. Returns plates dict."""
    W = round(width_in * INCH)
    wm, wm_rects, letters = stencil_word("ASAPROJECT", 600)
    k = W / wm.shape[1]
    wm, wm_rects = fit_width(wm, W), scale_rects(wm_rects, k)
    letters = [(round(a * k), round(b * k)) for a, b in letters]
    eb, en, e_rects = back_emblem(235)
    sl = text_line("NOBODY GAVE US PERMISSION", 400, BARLOW_XBOLD, tracking=0.04)
    sl = fit_width(sl, round(8.0 * INCH))
    g1, g2 = round(1.25 * INCH), round(0.5 * INCH)
    H = wm.shape[0] + g1 + eb.shape[0] + g2 + sl.shape[0]
    bone = np.zeros((H, W), bool)
    neon = np.zeros((H, W), bool)
    rects = list(wm_rects)
    bone[: wm.shape[0], :] |= wm
    y = wm.shape[0] + g1
    x = (W - eb.shape[1]) // 2
    bone[y:y + eb.shape[0], x:x + eb.shape[1]] |= eb
    neon[y:y + en.shape[0], x:x + en.shape[1]] |= en
    emblem_box = (x, y, x + eb.shape[1], y + eb.shape[0])
    rects += [(x0 + x, y0 + y, x1 + x, y1 + y) for x0, y0, x1, y1 in e_rects]
    y += eb.shape[0] + g2
    x = (W - sl.shape[1]) // 2
    bone[y:y + sl.shape[0], x:x + sl.shape[1]] |= sl
    ko = keep_out_mask((H, W), rects)
    # press-ready: no ink feature (barb tip, acute corner, crack sliver) under ~0.42 mm
    bone_c = drop_specks(opening(crack(bone, ko, seed=11), 2.5))
    neon_c = drop_specks(opening(crack(neon, ko, seed=12), 2.5))
    return {"bone": bone_c, "neon": neon_c,
            "bone_raw": bone, "neon_raw": neon, "letters": letters, "wordmark_h": wm.shape[0],
            "emblem_box": emblem_box,
            "cap_wordmark_in": wm.shape[0] / INCH, "cap_slogan_in": sl.shape[0] / INCH}


def hem_code(text="ASA-001 · EST. 2026"):
    return {"bone": text_line(text, px(10), BARLOW_BOLD, tracking=0.10)}


def chest_art():
    bone, neon = chest_emblem(89)
    return {"bone": bone, "neon": neon}


# ---------------------------------------------------------------- output

def underbase(*plates, choke_mm=0.17):
    """White underbase, choked ~2 px under the top colours; no specks under 0.5 mm^2."""
    u = np.zeros_like(plates[0])
    for p in plates:
        u |= p
    return drop_specks(opening(shrink(u, choke_mm * MM), 2.5))


def composite(plates):
    """RGBA preview built from the hard plates (top colours only)."""
    h, w = plates["bone"].shape
    out = np.zeros((h, w, 4), np.uint8)
    for key, col in (("bone", BONE), ("neon", NEON)):
        if key in plates:
            m = plates[key]
            out[m, :3] = col
            out[m, 3] = 255
    return Image.fromarray(out, "RGBA")


def save_plate(mask, path):
    """Film positive: black = ink on white, 1-bit, 300 dpi."""
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).convert("1").save(path, dpi=(DPI, DPI))
