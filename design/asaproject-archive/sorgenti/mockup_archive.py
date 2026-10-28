"""True-scale mockups and technique close-ups for the ASAPROJECT archive hoodie.

Usage: python3 mockup_archive.py <module_dir> <ref_dir> <out_dir>
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

sys.path.insert(0, sys.argv[1])
import asa_archive as A

ref, out = sys.argv[2], sys.argv[3]

PX_PER_IN = 22          # calibrated on the photo: kangaroo pocket ~13.5 in = 295 px, rib ~3 in = 65 px


# ------------------------------------------------------------ garment prep

def garment_mask(img):
    bg = img.convert("L").point(lambda v: 255 if v > 150 else 0)
    ImageDraw.floodfill(bg, (2, 2), 128)
    return bg.point(lambda v: 0 if v == 128 else 255)


def heal(img, mask, offsets):
    """Cover `mask` with fabric cloned from the best of `offsets`, tone-matched, feathered.

    The clone source whose surroundings best match the hole's surroundings wins,
    and its mean tone is shifted to match, so no lighter/darker band is left."""
    m = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2))
    mk = np.asarray(m) > 0
    a = np.asarray(img, dtype=np.float32)
    # match tone against fabric only: the background next to a hem must not count
    ring = ndimage.binary_dilation(mk, iterations=6) & ~mk & (a.mean(axis=2) < 120)
    best = None
    for dx, dy in offsets:
        src = np.roll(np.roll(a, -dy, 0), -dx, 1)
        ok = ring & (src.mean(axis=2) < 120)
        if not ok.any():
            continue
        diff = np.abs(src[ok] - a[ok]).mean()
        if best is None or diff < best[0]:
            best = (diff, src)
    src = best[1].copy()
    ok = ring & (src.mean(axis=2) < 120)
    src[mk] += a[ok].mean(axis=0) - src[ok].mean(axis=0)
    src = Image.fromarray(np.clip(src, 0, 255).astype(np.uint8))
    return Image.composite(src, img, m)


def erase_print(img, box, offsets):
    lum = img.convert("L")
    m = Image.new("L", img.size, 0)
    # fabric tops out at ~24; anything brighter is print or its anti-aliased halo
    m.paste(lum.crop(box).point(lambda v: 255 if v > 26 else 0), box[:2])
    return heal(img, m.filter(ImageFilter.MaxFilter(7)), offsets)


def washed_black(img, gm, seed):
    a = np.asarray(img, dtype=np.float32)
    rng = np.random.default_rng(seed)
    h, w = a.shape[:2]
    n = Image.fromarray(rng.random((h // 90 + 2, w // 90 + 2)).astype(np.float32)).resize((w, h), Image.BICUBIC)
    mott = (np.asarray(n, dtype=np.float32) - 0.5) * 9
    lum = a.mean(axis=2, keepdims=True)
    faded = 30 + a * 0.82 + mott[..., None]
    faded = faded * 0.85 + (lum * 0.82 + 30) * 0.15
    faded[..., 2] += 1.5
    res = Image.fromarray(np.clip(faded, 0, 255).astype(np.uint8))
    return Image.composite(res, img, gm)


# ------------------------------------------------------------ printing

def layer_from_plates(plates, width_px, puff=False):
    """Scale hard plates down to mockup size as an RGBA layer."""
    rgba = A.composite(plates)
    if puff:
        rgba = puff_render(plates)
    h = round(rgba.height * width_px / rgba.width)
    return rgba.resize((width_px, h), Image.LANCZOS)


def print_on_fabric(base, gm, layer, x, y, disp_px=4, shade_mix=0.6):
    """Ink follows the folds: displacement from the fabric relief + 60% fleece shading."""
    w, h = layer.size
    lum = np.asarray(base.convert("L"), dtype=np.float32)
    relief = ndimage.gaussian_filter(lum, 10)       # folds only, not knit noise
    gy, gx = np.gradient(relief)
    # one scale for the whole garment: the strongest real folds move the ink disp_px,
    # flat panels barely move it
    gmask = np.asarray(gm) > 0
    norm = max(1e-3, np.percentile(np.hypot(gx, gy)[gmask], 99.5))
    reg = (slice(y, y + h), slice(x, x + w))
    dx = np.clip(gx[reg] / norm, -1, 1) * disp_px
    dy = np.clip(gy[reg] / norm, -1, 1) * disp_px
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    coords = [yy - dy, xx - dx]
    arr = np.asarray(layer, dtype=np.float32)
    warped = np.stack([ndimage.map_coordinates(arr[..., c], coords, order=1, mode="nearest") for c in range(4)], -1)
    region = lum[reg]
    shade = np.clip((region + 6) / (np.median(region) + 6), 0.5, 1.3)
    shade = 1 - shade_mix + shade_mix * shade
    warped[..., :3] *= shade[..., None]
    warped[..., 3] *= np.asarray(gm, dtype=np.float32)[reg] / 255 * 0.97
    lay = Image.fromarray(np.clip(warped, 0, 255).astype(np.uint8), "RGBA")
    o = base.convert("RGBA")
    o.alpha_composite(lay, (x, y))
    return o.convert("RGB")


def puff_render(plates, light=(-0.7, -0.7), seed=5):
    """Matte puff: ~1 mm rounded edge, orange-peel surface; pink flat and lower."""
    bone, neon = plates["bone"], plates.get("neon")
    h, w = bone.shape
    edge = A.MM * 1.0
    d = ndimage.distance_transform_edt(bone)
    height = np.sin(np.clip(d / edge, 0, 1) * np.pi / 2)            # rounded shoulder, flat top
    rng = np.random.default_rng(seed)
    peel = ndimage.gaussian_filter(rng.normal(0, 1, (h, w)), 1.6) * 0.06
    height = height + peel * (height > 0.95)
    gy, gx = np.gradient(ndimage.gaussian_filter(height, 1.0))
    shade = 1 + (gx * light[0] + gy * light[1]) * 6.0
    shade = np.clip(shade, 0.78, 1.12)
    rgb = np.zeros((h, w, 3), np.float32)
    rgb[bone] = A.BONE
    rgb *= shade[..., None]
    a = np.where(bone, 255, 0).astype(np.float32)
    if neon is not None:
        flat = ndimage.gaussian_filter(rng.normal(0, 1, (h, w)), 0.8) * 4
        rgb[neon] = (np.array(A.NEON, np.float32) + flat[neon][:, None] * 0.6)
        a[neon] = 255
    # soft contact shadow from the raised bone onto the fabric
    sh = ndimage.gaussian_filter(bone.astype(np.float32), A.MM * 0.6)
    sh = np.roll(np.roll(sh, round(A.MM * 0.5), 0), round(A.MM * 0.5), 1)
    out = np.zeros((h, w, 4), np.float32)
    out[..., 3] = np.maximum(a, sh * 150 * (a == 0))
    out[..., :3] = np.where((a > 0)[..., None], rgb, 0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------ close-up fabric

def jersey(w, h, seed=0):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = np.abs(((xx % 9) - 4.5)) / 4.5 + 0.35 * np.sin((yy + np.abs((xx % 9) - 4.5) * 1.4) * 2 * np.pi / 7)
    grain = ndimage.gaussian_filter(rng.normal(0, 1, (h, w)).astype(np.float32), 0.8)
    lowf = np.asarray(Image.fromarray(rng.random((h // 120 + 2, w // 120 + 2)).astype(np.float32)).resize((w, h), Image.BICUBIC))
    lum = 42 + v * 5 + grain * 5 + (lowf - 0.5) * 14
    return Image.fromarray(np.clip(np.stack([lum, lum, lum + 2.5], -1), 0, 255).astype(np.uint8)), lum


def close_up(rgba, size, seed):
    base, lum = jersey(*size, seed=seed)
    x, y = (size[0] - rgba.width) // 2, (size[1] - rgba.height) // 2
    reg = lum[max(0, y):max(0, y) + rgba.height, max(0, x):max(0, x) + rgba.width]
    arr = np.asarray(rgba, dtype=np.float32).copy()
    shade = np.clip((reg + 4) / (np.median(reg) + 4), 0.8, 1.15)
    arr[: reg.shape[0], : reg.shape[1], :3] *= (0.6 + 0.4 * shade)[..., None]
    arr[..., 3] *= 0.97
    o = base.convert("RGBA")
    o.alpha_composite(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), (x, y))
    return o.convert("RGB")


# ------------------------------------------------------------ build

back = Image.open(f"{ref}/hoodie_back.jpg").convert("RGB")
front = Image.open(f"{ref}/hoodie_front.jpg").convert("RGB")

# remove the previous brand's prints and the side trims
VERT = [(0, d) for d in (-80, -65, 55, 70, 90, 110)]
back = erase_print(back, (320, 685, 760, 758), VERT)
front = erase_print(front, (626, 668, 702, 692), [(0, d) for d in (-30, -22, 22, 30, 40)])
blk = Image.new("L", back.size, 0)
blk.paste(back.convert("L").crop((735, 950, 795, 1125)).point(lambda v: 255 if v < 9 else 0), (735, 950))
back = heal(back, blk, [(-60, 0), (-70, 0), (-50, 10)])
tape = Image.new("L", front.size, 0)
ImageDraw.Draw(tape).polygon([(274, 944), (322, 944), (325, 1111), (294, 1111)], fill=255)
front = heal(front, tape, [(50, 0), (60, 0), (45, -10)])

gb, gf = garment_mask(back), garment_mask(front)
back, front = washed_black(back, gb, 1), washed_black(front, gf, 2)

backp = A.back_art()
chest = A.chest_art()
hem = A.hem_code()

W_back = round(14.0 * PX_PER_IN)
lay = layer_from_plates(backp, W_back)
back = print_on_fabric(back, gb, lay, 535 - W_back // 2, 610)
W_hem = round(hem["bone"].shape[1] / A.DPI * PX_PER_IN)
lay = layer_from_plates(hem, W_hem)
# centre of the code 1.25 in above the rib seam (y≈1115)
back = print_on_fabric(back, gb, lay, 535 - W_hem // 2, 1115 - round(1.25 * PX_PER_IN) - lay.height // 2, disp_px=1)
W_chest = round(3.5 * PX_PER_IN)
lay = layer_from_plates(chest, W_chest, puff=True)
front = print_on_fabric(front, gf, lay, 621 - W_chest // 2, 684 - lay.height // 2, disp_px=1)

back.save(f"{out}/mockup_retro.jpg", quality=95)
front.save(f"{out}/mockup_fronte.jpg", quality=95)

# close-ups at print resolution
rgba = A.composite(backp)
x_end = backp["letters"][4][1] + 60                       # whole "ASAPR", R included
close_up(rgba.crop((0, 0, x_end, backp["wordmark_h"] + 450)), (x_end + 100, backp["wordmark_h"] + 550), 3).save(
    f"{out}/dettaglio_retro_cracked.jpg", quality=93)
ex0, ey0, ex1, ey1 = backp["emblem_box"]
cx, cy = (ex0 + ex1) // 2, (ey0 + ey1) // 2
close_up(rgba.crop((cx - 900, cy - 900, cx + 900, cy + 400)), (1800, 1300), 6).save(f"{out}/dettaglio_mirino.jpg", quality=93)
close_up(rgba.crop((ex1 - 900, ey0, ex1 + 60, ey0 + 900)), (1000, 940), 8).save(f"{out}/dettaglio_filo_spinato.jpg", quality=93)
close_up(puff_render(chest), (1400, 1400), 4).save(f"{out}/dettaglio_petto_puff.jpg", quality=93)
close_up(A.composite(hem), (1600, 420), 7).save(f"{out}/dettaglio_codice_orlo.jpg", quality=93)

# production files: 1-bit separations at 300 dpi + RGBA previews
A.save_plate(backp["bone"], f"{out}/retro_1_bone.png")
A.save_plate(backp["neon"], f"{out}/retro_2_rosa_806C.png")
A.save_plate(A.underbase(backp["bone"], backp["neon"]), f"{out}/retro_0_sottofondo_bianco.png")
A.save_plate(chest["bone"], f"{out}/petto_1_bone_puff.png")
A.save_plate(chest["neon"], f"{out}/petto_2_rosa_806C_piatto.png")
A.save_plate(A.underbase(chest["neon"]), f"{out}/petto_0_sottofondo_bianco_sotto_rosa.png")
A.save_plate(hem["bone"], f"{out}/orlo_1_bone.png")
A.save_plate(A.underbase(hem["bone"]), f"{out}/orlo_0_sottofondo_bianco.png")
A.composite(backp).save(f"{out}/anteprima_stampa_retro.png", dpi=(A.DPI, A.DPI))
A.composite(chest).save(f"{out}/anteprima_stampa_petto.png", dpi=(A.DPI, A.DPI))
A.composite(hem).save(f"{out}/anteprima_stampa_orlo.png", dpi=(A.DPI, A.DPI))
print("back art in:", round(backp["bone"].shape[1] / A.DPI, 2), "x", round(backp["bone"].shape[0] / A.DPI, 2),
      "| chest in:", round(chest["bone"].shape[1] / A.DPI, 2), "| hem in:", round(hem["bone"].shape[1] / A.DPI, 2),
      "x", round(hem["bone"].shape[0] / A.DPI, 2))
