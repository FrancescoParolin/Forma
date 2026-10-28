import sys
from PIL import Image, ImageFilter

art_path, front_path, out_path = sys.argv[1:4]
width, dy, stroke = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])

art = Image.open(art_path).convert("RGB")
art = art.crop(art.convert("L").point(lambda v: 255 if v > 18 else 0).getbbox())
h = round(art.height * width / art.width)
a = art.resize((width, h), Image.LANCZOS)
layer = a.convert("RGBA")
layer.putalpha(a.split()[0].point(lambda v: max(0, min(255, (v - 12) * 255 // 90))))

front = Image.open(front_path).convert("RGB")
# Chest "0123456789": x 632–696, y 675–684
BOX, CX, CY = (626, 668, 702, 692), 664, 680
num_mask = Image.new("L", front.size, 0)
num_mask.paste(front.convert("L").crop(BOX).point(lambda v: max(0, min(255, (v - 40) * 255 // 160))), BOX[:2])

canvas = front.convert("RGBA")
canvas.alpha_composite(layer, (round(CX - width / 2), round(CY + dy - h / 2)))
out = canvas.convert("RGB")
if stroke:
    ring = num_mask.filter(ImageFilter.MaxFilter(stroke * 2 + 1))
    out = Image.composite(Image.new("RGB", out.size, (0, 0, 0)), out, ring)
out = Image.composite(front, out, num_mask)
out.save(out_path, quality=95)
out.crop((520, 600, 800, 760)).resize((840, 480), Image.LANCZOS).save(out_path.replace(".jpg", "_zoom.jpg"))
