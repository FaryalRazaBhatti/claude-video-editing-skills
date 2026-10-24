"""Build carousel cover images from the user's own photos.

Usage:
  python make_carousel.py SPEC.json          one cover per entry in SPEC["covers"]
  python make_carousel.py --stills VIDEO OUT_DIR t1 t2 ...   grab stills from a clip (1080x1920)

Templates: moodboard, magazine, bold, polaroids (see references/carousels.md).
"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from reelkit import ui

random.seed(7)


def paper(w, h, col):
    base = np.full((h, w, 3), col, np.float32) + np.random.default_rng(1).normal(0, 6, (h, w, 1))
    return Image.fromarray(base.clip(0, 255).astype('uint8')).convert('RGBA')


def drop(canvas, img, xy, rot=0, shadow=True):
    img = img.convert('RGBA')
    if rot:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
    if shadow:
        sh = Image.new('RGBA', (img.width + 60, img.height + 60), (0, 0, 0, 0))
        blk = Image.new('RGBA', img.size, (30, 20, 10, 255)); blk.putalpha(img.getchannel('A').point(lambda v: int(v * 0.35)))
        sh.alpha_composite(blk, (30, 38))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (xy[0] - 30, xy[1] - 30))
    canvas.alpha_composite(img, xy)


def photo(path, aspect=4 / 5, focus_top=0.14):
    """Crop a photo to `aspect` (w/h), keeping the top part (where faces usually are)."""
    im = Image.open(path).convert('RGB')
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect); x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = int(w / aspect); y = int(min(max(0, h * focus_top), h - nh))
    return im.crop((0, y, w, y + nh))


def framed(img, w, border=14, bottom=None):
    img = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS)
    b = border if bottom is None else bottom
    f = Image.new('RGB', (w + border * 2, img.height + border + b), (255, 255, 255))
    f.paste(img, (border, border))
    return f


def tape(canvas, cx, cy, rot):
    drop(canvas, Image.new('RGBA', (130, 38), (238, 228, 196, 190)), (cx - 65, cy - 19), rot, shadow=False)


def cutout(path, clear=()):
    """Person cut out of a photo (uses the cutout model). `clear`: boxes [x0,y0,x1,y1] to erase stray bits."""
    from reelkit.segment import session, mask
    im = Image.open(path).convert('RGB')
    m = np.asarray(mask(session(), im)).copy()
    for x0, y0, x1, y1 in clear:
        m[y0:y1, x0:x1] = 0
    m[m < 40] = 0
    m = (m * largest_region(m > 128)).astype(np.uint8)
    out = im.convert('RGBA'); out.putalpha(Image.fromarray(m))
    return out.crop(out.getbbox())


def largest_region(solid, scale=4):
    """Keep only the biggest connected blob (the person); drops furniture the model picked up."""
    small = np.asarray(Image.fromarray(solid.astype(np.uint8) * 255).resize(
        (solid.shape[1] // scale, solid.shape[0] // scale), Image.NEAREST)) > 0
    h, w = small.shape
    label = np.zeros((h, w), np.int32)
    sizes, cur = {}, 0
    for y0, x0 in zip(*np.nonzero(small)):
        if label[y0, x0]:
            continue
        cur += 1; stack = [(y0, x0)]; label[y0, x0] = cur; n = 0
        while stack:
            y, x = stack.pop(); n += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and small[yy, xx] and not label[yy, xx]:
                    label[yy, xx] = cur; stack.append((yy, xx))
        sizes[cur] = n
    if not sizes:
        return np.ones_like(solid, np.float32)
    keep = (label == max(sizes, key=sizes.get)).astype(np.uint8) * 255
    keep = Image.fromarray(keep).resize((solid.shape[1], solid.shape[0]), Image.NEAREST).filter(ImageFilter.MaxFilter(9))
    return np.asarray(keep, np.float32) / 255


# ---------- templates ----------
def moodboard(c):
    W = H = 1080
    cv = paper(W, H, (232, 226, 214))
    d = ImageDraw.Draw(cv)
    d.text((60, 46), c.get('title', ''), font=ui.font('Caveat-Bold', 58), fill=(40, 34, 28))
    spots = [(60, 140, -3), (400, 120, 2), (735, 150, -2), (70, 590, 2), (410, 610, -3), (745, 590, 3)]
    for ph, (x, y, r) in zip(c['photos'][:6], spots):
        im = framed(photo(ph['img']), 270, 10, 10)
        drop(cv, im, (x, y), r)
        tape(cv, x + 150, y + 6, random.choice([-8, 6, -4]))
        if ph.get('note'):
            ImageDraw.Draw(cv).text((x + 20, y + im.height + 18), ph['note'], font=ui.font('Caveat-Bold', 40), fill=(60, 50, 40))
    for i, col in enumerate(c.get('swatches', ['#624A52', '#B08C78', '#E2C8AA', '#3A3432'])):
        ImageDraw.Draw(cv).rectangle([790 + i * 62, 50, 840 + i * 62, 100], fill=ui.hex_rgb(col))
    return cv


def magazine(c):
    W, H = 1080, 1350
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array(ui.hex_rgb(c.get('bg_top', '#3E281C'))), np.array(ui.hex_rgb(c.get('bg_bottom', '#16100E')))
    cv = Image.fromarray(((top * (1 - y) + bot * y) * np.ones((1, W, 1))).astype('uint8')).convert('RGBA')
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([200, 250, 1100, 1150], fill=(255, 170, 90, 70))
    cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(cv)
    yel, light = ui.hex_rgb(c.get('accent', '#F7CC40')), (240, 230, 210)
    d.text((40, 40), c.get('top_left', 'VOL. 01'), font=ui.font('Inter-Bold', 28), fill=light)
    d.text((W - 40, 40), c.get('top_right', 'A VISUAL GUIDE'), font=ui.font('Inter-Bold', 28), fill=light, anchor='ra')
    mast = c.get('masthead', 'CREATOR')
    d.text((W / 2, 200), mast, font=ui.fit_font('Playfair-Black', mast, W - 70, 230), fill=yel, anchor='mm')
    cut = cutout(c['cutout'], c.get('cutout_clear', []))
    s = min(1.0, 1180 / cut.height, 1000 / cut.width)
    cut = cut.resize((int(cut.width * s), int(cut.height * s)), Image.LANCZOS)
    cv.alpha_composite(cut, (W - cut.width + 40 if cut.width > 700 else W - cut.width - 20, H - cut.height + 20))
    d = ImageDraw.Draw(cv)
    for i, l in enumerate(c.get('headline', [])[:5]):
        d.text((44, 420 + i * 60), l, font=ui.font('Playfair-Black', 54), fill=(255, 255, 255))
    y0 = 420 + len(c.get('headline', [])[:5]) * 60 + 60
    for i, l in enumerate(c.get('list', [])[:5]):
        d.text((44, y0 + i * 46), l, font=ui.font('Playfair-Italic', 34), fill=(235, 220, 200))
    for i, l in enumerate(c.get('script', [])[:2]):
        d.text((50, 1000 + i * 66), l, font=ui.font('Caveat-Bold', 64), fill=yel)
    bx, by = 44, 1200
    d.rectangle([bx, by, bx + 150, by + 100], fill=(250, 250, 245))
    x = bx + 10
    while x < bx + 140:
        w = random.choice([2, 3, 5]); d.rectangle([x, by + 10, x + w, by + 80], fill=(20, 20, 20)); x += w + random.choice([2, 3])
    return cv


def bold(c):
    W, H = 1080, 1350
    bg = ui.hex_rgb(c.get('bg', '#5840DC'))
    cv = Image.new('RGBA', (W, H), bg + (255,))
    d = ImageDraw.Draw(cv)
    lines = c.get('lines', [])[:4]
    f = ui.font('InterDisplay-Black', 112)
    for l in lines:
        f = min(f, ui.fit_font('InterDisplay-Black', l, W - 128, 112), key=lambda x: x.size)
    for i, l in enumerate(lines):
        d.text((64, 90 + i * int(f.size * 1.09)), l, font=f, fill=(255, 255, 255))
    by = 90 + len(lines) * int(f.size * 1.09) + 40
    if c.get('button'):
        bf = ui.font('Inter-Bold', 34)
        bw = ui.text_width(c['button'], bf) + 64
        d.rounded_rectangle([64, by, 64 + bw, by + 70], 35, fill=ui.hex_rgb(c.get('button_color', '#FFD60A')))
        d.text((64 + bw / 2, by + 35), c['button'], font=bf, fill=(30, 24, 10), anchor='mm')
    if c.get('cutout'):
        cut = cutout(c['cutout'], c.get('cutout_clear', []))
        s = min(0.75, (H - by - 140) / cut.height * 1.25)
        cut = cut.resize((int(cut.width * s), int(cut.height * s)), Image.LANCZOS)
        cv.alpha_composite(cut, (W - cut.width + 60, H - cut.height))
    ImageDraw.Draw(cv).text((64, H - 90), c.get('footer', 'Swipe  →'), font=ui.font('Inter-Bold', 40), fill=(255, 255, 255))
    return cv


def polaroids(c):
    W = H = 1080
    cv = paper(W, H, (240, 232, 220))
    d = ImageDraw.Draw(cv)
    d.text((W / 2, 95), c.get('title', ''), font=ui.font('Caveat-Bold', 84), fill=(40, 34, 28), anchor='mm')
    for ph, (x, y, r) in zip(c['photos'][:3], [(20, 300, 7), (350, 250, -3), (690, 320, 6)]):
        pol = framed(photo(ph['img'], 1.0, 0.16), 340, 18, 96)
        if ph.get('caption'):
            ImageDraw.Draw(pol).text((pol.width / 2, pol.height - 48), ph['caption'], font=ui.font('Caveat-Bold', 46), fill=(50, 44, 40), anchor='mm')
        drop(cv, pol, (x, y), r)
    if c.get('footer'):
        ImageDraw.Draw(cv).text((W / 2, 960), c['footer'], font=ui.font('Inter-SemiBold', 34), fill=(110, 100, 90), anchor='mm')
    return cv


TEMPLATES = {'moodboard': moodboard, 'magazine': magazine, 'bold': bold, 'polaroids': polaroids}


def main(spec_path):
    base = os.path.dirname(os.path.abspath(spec_path))
    spec = json.load(open(spec_path))
    os.chdir(base)
    for c in spec['covers']:
        img = TEMPLATES[c['template']](c).convert('RGB')
        img.save(c['out'], quality=92)
        print('made', os.path.join(base, c['out']))


def stills(video, out_dir, times):
    from reelkit.video import still
    os.makedirs(out_dir, exist_ok=True)
    for t in times:
        p = os.path.join(out_dir, f'still_{float(t):06.2f}.png')
        still(video, float(t)).save(p); print(p)


if __name__ == '__main__':
    if sys.argv[1] == '--stills':
        stills(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        main(sys.argv[1])
