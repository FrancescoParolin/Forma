import sys
from PIL import Image, ImageChops, ImageFilter

art_path, back_path, front_path, out_dir = sys.argv[1:5]

art = Image.open(art_path).convert("RGB")
# Tight crop on the non-black pixels (artwork sits on pure black)
mask = art.convert("L").point(lambda v: 255 if v > 18 else 0)
art = art.crop(mask.getbbox())

def place(base, art, cx, top, width):
    h = round(art.height * width / art.width)
    a = art.resize((width, h), Image.LANCZOS).filter(ImageFilter.SMOOTH)
    layer = Image.new("RGB", base.size, (0, 0, 0))
    layer.paste(a, (round(cx - width / 2), round(top)))
    # Lighten blend: black artwork background disappears into the black fabric
    return ImageChops.lighter(base, layer)

back = Image.open(back_path).convert("RGB")
# "0123456789" on the back spans x≈333–770, y≈685–745
back = place(back, art, cx=551, top=770, width=520)
back.save(f"{out_dir}/mockup_back_real.jpg", quality=95)

front = Image.open(front_path).convert("RGB")
# Chest "0123456789" sits at x≈632–696, y≈675–684 (body centre x≈534);
# mirror it on the other chest, vertically centred on the same line
w = 88
front = place(front, art, cx=2 * 534 - 664, top=680 - art.height * w / art.width * 0.45, width=w)
front.save(f"{out_dir}/mockup_front_real.jpg", quality=95)
