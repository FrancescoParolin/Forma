import sys
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageFont

art_path, back_path, out_dir = sys.argv[1:4]

art = Image.open(art_path).convert("RGB")
art = art.crop(art.convert("L").point(lambda v: 255 if v > 18 else 0).getbbox())

def pink_layer(width):
    """Artwork resized, with alpha keyed from its pure-black background."""
    h = round(art.height * width / art.width)
    a = art.resize((width, h), Image.LANCZOS).filter(ImageFilter.SMOOTH)
    # Opaque inside the letters, translucent only on the fuzzy dark fringe
    alpha = a.split()[0].point(lambda v: max(0, min(255, (v - 12) * 255 // 90)))
    rgba = a.convert("RGBA")
    rgba.putalpha(alpha)
    return rgba

back = Image.open(back_path).convert("RGB")
# "0123456789" on the back: x 335–741, y 698–743
NUM_BOX = (320, 685, 760, 758)
NUM_CX, NUM_CY = 538, 720
lum = back.convert("L")
num_mask = Image.new("L", back.size, 0)
num_mask.paste(lum.crop(NUM_BOX).point(lambda v: max(0, min(255, (v - 40) * 255 // 160))), NUM_BOX[:2])

def render(name, width, dy, numbers_on_top, shadow=0, stroke=0, weave=None):
    layer = pink_layer(width)
    canvas = back.convert("RGBA")
    pos = (round(NUM_CX - width / 2), round(NUM_CY + dy - layer.height / 2))
    canvas.alpha_composite(layer, pos)
    out = canvas.convert("RGB")
    if numbers_on_top:
        mask = num_mask
        if stroke:
            ring = mask.filter(ImageFilter.MaxFilter(stroke * 2 + 1))
            out = Image.composite(Image.new("RGB", out.size, (0, 0, 0)), out, ring)
        if shadow:
            halo = num_mask.filter(ImageFilter.MaxFilter(shadow * 2 + 1)).filter(ImageFilter.GaussianBlur(shadow))
            out = Image.composite(Image.new("RGB", out.size, (0, 0, 0)), out, halo.point(lambda v: v * 9 // 10))
        out = Image.composite(back, out, mask)
        if weave:
            # Interlock: narrow pink strokes that cross the whole numbers line
            # pass back over the numbers, so the two marks weave together
            pa = Image.new("L", back.size, 0)
            pa.paste(layer.split()[3], pos)
            px = pa.load()
            band = range(698, 744)
            cols = [x for x in range(330, 750)
                    if sum(px[x, y] > 200 for y in band) >= len(band) * 0.97]
            runs, start, prev = [], None, None
            for x in cols + [None]:
                if start is not None and (x is None or x != prev + 1):
                    runs.append((start, prev))
                    start = None
                if x is not None and start is None:
                    start = x
                prev = x
            # thin strokes only, and never over the first digit: each digit stays legible
            runs = [r for r in runs if 6 <= r[1] - r[0] <= 26 and (r[0] + r[1]) / 2 > 380]
            # the `weave` most prominent strokes, spread along the line
            runs = sorted(sorted(runs, key=lambda r: r[0] - r[1])[:weave])
            print(name, "pink over numbers at x", runs)
            slices = Image.new("L", back.size, 0)
            sd = ImageDraw.Draw(slices)
            for x0, x1 in runs:
                sd.rectangle((x0, 0, x1, back.height), fill=255)
            over = Image.new("RGBA", back.size, (0, 0, 0, 0))
            over.alpha_composite(layer, pos)
            over.putalpha(ImageChops.multiply(over.split()[3], slices.filter(ImageFilter.GaussianBlur(1))))
            out = out.convert("RGBA")
            out.alpha_composite(over)
            out = out.convert("RGB")
    out.save(f"{out_dir}/{name}.jpg", quality=95)
    return out

variants = [
    # name, pink width, vertical offset of pink centre vs numbers centre, numbers on top, shadow, stroke, weave
    ("B_numeri_sopra_centrata", 560, 0, True, 0, 0),
    ("D_numeri_sopra_sfalsata", 560, 55, True, 0, 0),
    ("G_numeri_sopra_gocce", 560, -40, True, 0, 0),
    ("I_intreccio_senza_bordo", 560, 20, True, 0, 0, 3),
]
crops = []
for v in variants:
    img = render(*v[:4], *v[4:])
    crops.append((v[0], img.crop((180, 520, 900, 1000))))

# Contact sheet of the back area of every variant
cw, ch = crops[0][1].size
cols = 2
rows = (len(crops) + cols - 1) // cols
sheet = Image.new("RGB", (cw * cols, (ch + 40) * rows), (237, 237, 237))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
for i, (name, c) in enumerate(crops):
    x, y = (i % cols) * cw, (i // cols) * (ch + 40)
    d.text((x + 12, y + 8), name, fill=(0, 0, 0), font=font)
    sheet.paste(c, (x, y + 40))
sheet.save(f"{out_dir}/contact_sheet_senza_bordo.jpg", quality=92)
