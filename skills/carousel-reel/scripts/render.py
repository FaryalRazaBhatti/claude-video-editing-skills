"""Carousel reel: 'type this' chat card top-right (attached photos + a typed command), the finished
carousel cover pops in top-left on 'for this carousel', with two-line captions (handwritten line +
heavy yellow line) and a 'Follow for more' ending. Cards tuck behind the head when a cutout exists.

Usage:
  python render.py PLAN.json
  python render.py PLAN.json --preview 1.5 2.4 15.3
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from reelkit import ui
from reelkit.video import frames, still, Encoder, contact_sheet, W, H, FPS
from reelkit import masks as M

SS = ui.SS
CARD_X, CARD_W, CARD_H = 560, 560, 350   # chat card runs off the right edge
CAR_X, CAR_W = 52, 380


def shadowed(img, a=60, blur=16, dy=10):
    pad = 40
    out = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 255)); sh.putalpha(img.getchannel('A').point(lambda v: int(v * a / 255)))
    out.alpha_composite(sh, (pad, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out, pad


def put(canvas, img_pad, x, y, s=1.0, alpha=1.0):
    img, pad = img_pad
    if abs(s - 1) > 0.003:
        nw, nh = max(1, int(img.width * s)), max(1, int(img.height * s))
        x += (img.width - nw) / 2; y += (img.height - nh) / 2
        img = img.resize((nw, nh), Image.BICUBIC)
    if alpha < 1:
        img = img.copy(); img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    canvas.alpha_composite(img, (int(x - pad * s), int(y - pad * s)))


class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        p = self.p = json.load(open(plan_path))
        self.rel = lambda x: os.path.join(self.base, x) if x else None
        self.video, self.out = self.rel(p['video']), self.rel(p.get('out', 'out.mp4'))
        self.mask_dir = self.rel(p.get('masks', 'masks'))
        self.has_masks = os.path.isdir(self.mask_dir)
        self.yel = ui.hex_rgb(p.get('caption_color', '#FFDE3C'))
        self.cut = p.get('cut')  # [a, b] seconds of dead air to drop
        lay = M.head_layout(self.mask_dir) if self.has_masks else None
        top = lay['top_typical'] if lay else 560
        self.card_y = max(110, top - 300)        # bottom of the cards lands around the hairline
        self.car_y = self.card_y - 14
        self.cap_y = min(max((lay['chin'] if lay else 1180) - 140, 980), 1200)
        self.thumbs = {}
        self.carousels = []
        for pr in p['pairs']:
            for t in pr.get('thumbs', []):
                if t not in self.thumbs:
                    self.thumbs[t] = self.thumb(self.rel(t))
            im = Image.open(self.rel(pr['carousel'])).convert('RGB')
            im = im.resize((CAR_W, int(im.height * CAR_W / im.width)), Image.LANCZOS)
            self.carousels.append(shadowed(ui.rounded(im, 8), 80, 14, 8))

    def thumb(self, path, size=222):
        im = Image.open(path).convert('RGB')
        w, h = im.size
        side = min(w, h)
        y = int(min(max(0, h * 0.22), h - side)) if h > w else 0
        x = (w - side) // 2
        t = ui.rounded(im.crop((x, y, x + side, y + side)).resize((size, size), Image.LANCZOS), 26)
        d = ImageDraw.Draw(t)
        cx, cy, r = size - 34, 34, 20
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
        d.line([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=(20, 20, 20), width=4)
        d.line([(cx - 7, cy + 7), (cx + 7, cy - 7)], fill=(20, 20, 20), width=4)
        return t

    def composer(self, k, n):
        pr = self.p['pairs'][k]
        c = Image.new('RGBA', (CARD_W * SS, CARD_H * SS), (0, 0, 0, 0))
        ImageDraw.Draw(c).rounded_rectangle([0, 0, CARD_W * SS + 60, CARD_H * SS - 1], 30 * SS, fill=(255, 255, 255, 255))
        c = c.resize((CARD_W, CARD_H), Image.LANCZOS)
        for i, tn in enumerate(pr.get('thumbs', [])[:2]):
            c.alpha_composite(self.thumbs[tn], (18 + i * 238, 18))
        d = ImageDraw.Draw(c)
        y = 290
        d.line([(32, y), (64, y)], fill=(30, 30, 30), width=4); d.line([(48, y - 16), (48, y + 16)], fill=(30, 30, 30), width=4)
        f = ui.fit_font('Inter-Regular', pr['cmd'], CARD_W - 110, 40)
        txt = pr['cmd'][:n]
        d.text((92, y), txt, font=f, fill=(20, 20, 20), anchor='lm')
        cx = 92 + d.textlength(txt, font=f) + 3
        d.rectangle([cx, y - 24, cx + 3, y + 24], fill=(40, 110, 240))
        return c

    def caption(self, canvas, l1, l2, p2):
        lay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        x = 110
        if l1:
            ld.text((x, self.cap_y), l1, font=ui.font('Caveat-Bold', 76), fill=(255, 255, 255), anchor='ls')
        if l2 and p2 > 0:
            sc = 0.85 + 0.15 * ui.ease_back(p2)
            f = ui.fit_font('Anton', l2, W - 2 * x, 104)
            t = Image.new('RGBA', (W, 160), (0, 0, 0, 0))
            ImageDraw.Draw(t).text((0, 140), l2, font=f, fill=self.yel, anchor='ls')
            t = t.resize((int(W * sc), int(160 * sc)), Image.BICUBIC)
            lay.alpha_composite(t, (x, self.cap_y + 10 + int(160 * (1 - sc))))
        blk = Image.new('RGBA', canvas.size, (0, 0, 0, 255)); blk.putalpha(lay.getchannel('A').point(lambda v: int(v * 0.55)))
        sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); sh.alpha_composite(blk, (4, 6))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
        canvas.alpha_composite(lay)

    def frame(self, t, src, mask):
        canvas = src.convert('RGBA')
        behind = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        pairs = self.p['pairs']
        k = max([i for i, pr in enumerate(pairs) if pr.get('line1_at', pr['type_t']) <= t], default=-1)
        l1 = l2 = None; p2 = 0
        if k >= 0:
            pr = pairs[k]
            if t < pr['end_t']:
                l1 = pr.get('line1', 'Type this:') if t >= pr['type_t'] else pr.get('line1_early', pr.get('line1', 'Type this:'))
                if t >= pr['type_t']:
                    n = int(len(pr['cmd']) * min(1, max(0, (t - pr['type_t'] - 0.05) / 0.5)))
                    pc = ui.ease_out((t - pr['type_t']) / 0.18)
                    put(behind, shadowed(self.composer(k, n), 50, 18, 10), CARD_X, self.card_y + 20 * (1 - pc), 0.96 + 0.04 * pc, min(1, pc * 1.5))
                if t >= pr['get_t']:
                    pg = (t - pr['get_t']) / 0.28
                    put(behind, self.carousels[k], CAR_X, self.car_y, 0.7 + 0.3 * ui.ease_back(pg), min(1, pg * 3))
                    l2, p2 = pr.get('line2', 'FOR THIS CAROUSEL'), pg
        canvas.alpha_composite(behind)
        if self.has_masks:
            canvas.alpha_composite(ui.person_layer(src, mask))
        if l1 or l2:
            self.caption(canvas, l1, l2, p2)
        fo = self.p.get('follow')
        if fo and t >= fo['t'] - 0.25:
            q = ui.ease_out((t - fo['t'] + 0.25) / 0.35)
            canvas.alpha_composite(Image.new('RGBA', (W, H), (10, 10, 10, int(170 * q))))
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            sc = 0.85 + 0.15 * ui.ease_back((t - fo['t'] + 0.1) / 0.3)
            head = fo.get('headline', 'FOLLOW FOR MORE')
            d.text((W / 2, 900), head, font=ui.fit_font('Anton', head, int((W - 80) * sc), int(150 * sc)), fill=self.yel + (int(255 * q),), anchor='mm')
            if fo.get('sub'):
                d.text((W / 2, 1010), fo['sub'], font=ui.font('Caveat-Bold', 76), fill=(255, 255, 255, int(255 * q)), anchor='mm')
            canvas.alpha_composite(lay)
        return canvas.convert('RGB')

    def render(self):
        enc = Encoder(self.out, self.video, speed=self.p.get('speed', 1.0), cut=self.cut)
        for i, src in enumerate(frames(self.video), start=1):
            t = (i - 1) / FPS
            if self.cut and self.cut[0] <= t < self.cut[1]:
                continue
            enc.write(self.frame(t, src, M.load(self.mask_dir, i) if self.has_masks else None))
        enc.close()
        shift = lambda x: x - (self.cut[1] - self.cut[0] if self.cut and x >= self.cut[1] else 0)
        times = [shift(pr['get_t'] + 0.4) for pr in self.p['pairs']][:5]
        sheet = contact_sheet(self.out, [x / self.p.get('speed', 1.0) for x in times], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        for t in times:
            src = still(self.video, t)
            img = self.frame(t, src, M.load(self.mask_dir, int(round(t * FPS)) + 1) if self.has_masks else None)
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg'); img.save(p, quality=88); print(p)


if __name__ == '__main__':
    reel = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        reel.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        reel.render()
