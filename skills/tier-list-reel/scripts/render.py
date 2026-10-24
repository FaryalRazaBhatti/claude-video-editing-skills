"""Tier-list reel: a ranking board above the head fills up as each item is named, and a card in
front explains the current item, its badge flipping from '?' to the tier letter on cue.

Usage:
  python render.py PLAN.json
  python render.py PLAN.json --preview 5.5 30 60
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from reelkit import ui
from reelkit.video import frames, still, Encoder, contact_sheet, W, H, FPS
from reelkit import masks as M

SS = ui.SS
INK, MUTED = (20, 18, 28), (110, 106, 122)
TIER_COLORS = {'S': (229, 72, 77), 'A': (247, 107, 21), 'B': (255, 197, 61), 'C': (70, 167, 88), 'D': (62, 99, 221),
               'E': (120, 120, 140), 'F': (142, 78, 198)}
BW, HDR, ROW, LBL = 960, 100, 68, 92


def tier_fill(t):
    return TIER_COLORS.get(t, (120, 120, 140))


def tier_text(t):
    return (40, 28, 0) if t == 'B' else (255, 255, 255)


def down(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        p = self.p = json.load(open(plan_path))
        rel = lambda k, d=None: os.path.join(self.base, p.get(k, d)) if p.get(k, d) else None
        self.video, self.mask_dir, self.out = rel('video'), rel('masks', 'masks'), rel('out', 'out.mp4')
        self.accent = ui.hex_rgb(p.get('accent', '#5840DC'))
        self.soft = ui.mix(self.accent, (255, 255, 255), 0.88)
        b = p['board']
        self.tiers = b.get('tiers', ['S', 'A', 'B', 'C', 'D', 'F'])
        self.items = p['items']
        lay = M.head_layout(self.mask_dir) or {'top_typical': 640, 'top_highest': 600, 'chin': 1150}
        self.BH = HDR + ROW * len(self.tiers) + 16
        bottom = lay['top_typical'] + 28  # bottom edge tucks behind the hair
        self.scale = min(1.0, (bottom - 90) / self.BH)
        self.board_cy = bottom - self.BH * self.scale / 2
        self.card_top = min(max(lay['chin'] + 60, 1150), 1300)
        self.chips = [self.chip(it['name']) for it in self.items]
        self.slots = self.layout_chips()
        self.board_bg = self.board_base(b.get('title', 'My ranking'), b.get('tag', ''))
        self.shadow = {}

    # ----- pieces -----
    def chip(self, name, size=27):
        f = ui.font('Inter-SemiBold', size * SS)
        w = int(ui.text_width(name, f) / SS) + 40
        img = Image.new('RGBA', (w * SS, 52 * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, w * SS - 1, 52 * SS - 1], 26 * SS, fill=(246, 244, 250), outline=(225, 221, 234), width=2 * SS)
        d.text((w / 2 * SS, 26 * SS), name, font=f, fill=INK, anchor='mm')
        return down(img)

    def layout_chips(self):
        nxt = {t: LBL + 26 for t in self.tiers}
        slots = []
        for it, c in zip(self.items, self.chips):
            r = self.tiers.index(it['tier'])
            x = nxt[it['tier']]
            if x + c.width > BW - 20:  # row full: shrink this chip to fit what is left
                room = max(80, BW - 20 - x)
                c = c.resize((room, int(c.height * room / c.width)), Image.LANCZOS)
                self.chips[self.items.index(it)] = c
            nxt[it['tier']] += c.width + 12
            slots.append((x, HDR + r * ROW + (ROW - c.height) // 2))
        return slots

    def board_base(self, title, tag):
        img = Image.new('RGBA', (BW * SS, self.BH * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, BW * SS - 1, self.BH * SS - 1], 40 * SS, fill=(255, 255, 255, 255))
        ui.sparkle(d, 46, 52, 16, self.accent, SS)
        tag_w = 0
        if tag:
            pf = ui.font('Inter-Bold', 24 * SS)
            tag_w = ui.text_width(tag.upper(), pf) / SS + 36
            d.rounded_rectangle([(BW - 32 - tag_w) * SS, 32 * SS, (BW - 32) * SS, 72 * SS], 20 * SS, fill=self.soft)
            d.text(((BW - 32 - tag_w / 2) * SS, 52 * SS), tag.upper(), font=pf, fill=self.accent, anchor='mm')
        tf = ui.fit_font('Inter-Bold', title, (BW - 120 - tag_w - 20) * SS, 40 * SS)
        d.text((74 * SS, 52 * SS), title, font=tf, fill=INK, anchor='lm')
        for r, t in enumerate(self.tiers):
            y = HDR + r * ROW
            d.rounded_rectangle([16 * SS, (y + 4) * SS, (16 + LBL - 10) * SS, (y + ROW - 4) * SS], 16 * SS, fill=tier_fill(t))
            d.text(((16 + (LBL - 10) / 2) * SS, (y + ROW / 2) * SS), t, font=ui.font('Inter-Black', 38 * SS), fill=tier_text(t), anchor='mm')
            d.rounded_rectangle([(LBL + 14) * SS, (y + 4) * SS, (BW - 16) * SS, (y + ROW - 4) * SS], 16 * SS, fill=(250, 249, 252))
        return down(img)

    def board(self, t):
        b = self.board_bg.copy()
        for it, c, (x, y) in zip(self.items, self.chips, self.slots):
            if t < it['t_tier']:
                continue
            p = (t - it['t_tier']) / 0.32
            glow = max(0.0, 1 - (t - it['t_tier']) / 0.9)
            if glow > 0:
                g = Image.new('RGBA', (c.width + 24, c.height + 24), (0, 0, 0, 0))
                ImageDraw.Draw(g).rounded_rectangle([0, 0, g.width - 1, g.height - 1], g.height // 2, fill=tier_fill(it['tier']) + (int(150 * glow),))
                b.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)), (x - 12, y - 12))
            ui.place(b, c, x + c.width / 2, y + c.height / 2 - 30 * (1 - ui.ease_out(p)), 0.6 + 0.4 * ui.ease_back(p), ui.ease_out(p * 1.8))
        return b

    def item_card(self, k, revealed):
        key = ('c', k, revealed)
        if key in self.shadow:
            return self.shadow[key]
        it = self.items[k]
        cw = 900
        fl = ui.font('Inter-Medium', 36 * SS)
        lines = ui.wrap(it.get('line', ''), fl, (cw - 64 - 150) * SS) if it.get('line') else []
        h = max(190, 108 + len(lines) * 48 + 36)
        img = Image.new('RGBA', (cw * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, cw * SS - 1, h * SS - 1], 40 * SS, fill=(255, 255, 255, 255))
        bs, bx, by = 118, 32, (h - 118) // 2
        t = it['tier']
        if revealed:
            d.rounded_rectangle([bx * SS, by * SS, (bx + bs) * SS, (by + bs) * SS], 28 * SS, fill=tier_fill(t))
            d.text(((bx + bs / 2) * SS, (by + bs / 2 - 2) * SS), t, font=ui.font('Inter-Black', 70 * SS), fill=tier_text(t), anchor='mm')
        else:
            d.rounded_rectangle([bx * SS, by * SS, (bx + bs) * SS, (by + bs) * SS], 28 * SS, fill=(240, 238, 245))
            d.text(((bx + bs / 2) * SS, (by + bs / 2 - 2) * SS), '?', font=ui.font('Inter-Black', 64 * SS), fill=(190, 186, 202), anchor='mm')
        x = bx + bs + 30
        y = (h - (48 + 14 + len(lines) * 48)) // 2
        d.text((x * SS, y * SS), it['name'], font=ui.fit_font('Inter-Bold', it['name'], (cw - x - 40) * SS, 44 * SS), fill=INK)
        y += 62
        for ln in lines:
            d.text((x * SS, y * SS), ln, font=fl, fill=MUTED); y += 48
        self.shadow[key] = ui.with_shadow(down(img), 0.5)
        return self.shadow[key]

    def cta_card(self, n):
        c = self.p['cta']
        head, prompt = c.get('headline', "That's my list. What would you move?"), c.get('prompt', 'Tell me in the comments')
        w, h = 900, 250
        img = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], 40 * SS, fill=(255, 255, 255, 255))
        ui.sparkle(d, 50, 54, 16, self.accent, SS)
        d.text((78 * SS, 54 * SS), head, font=ui.fit_font('Inter-Bold', head, (w - 110) * SS, 40 * SS), fill=INK, anchor='lm')
        d.rounded_rectangle([32 * SS, 112 * SS, (w - 32) * SS, 212 * SS], 50 * SS, fill=(246, 244, 250))
        f = ui.font('Inter-Medium', 34 * SS)
        txt = prompt[:n]
        d.text((70 * SS, 162 * SS), txt or 'Add a comment...', font=f, fill=INK if txt else (170, 166, 182), anchor='lm')
        cx = 70 * SS + (d.textlength(txt, font=f) if txt else 0) + 4 * SS
        d.rectangle([cx, 140 * SS, cx + 4 * SS, 184 * SS], fill=self.accent)
        ui.send_button(d, w - 32 - 50, 162, 38, self.accent if n >= len(prompt) else (210, 206, 222), SS)
        return down(img), len(prompt)

    # ----- frame -----
    def frame(self, t, src, mask):
        bob = lambda ph: 5 * math.sin(2 * math.pi * 0.45 * t + ph)
        behind = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        front = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        a = ui.anim(t, self.p['board'].get('in', 0.4), 1e9, dur_in=0.45)
        if a:
            s, al, dy = a
            img, pad = ui.with_shadow(self.board(t), 0.30)
            ui.place(behind, img, W / 2, self.board_cy + dy + bob(0), s * self.scale, al)
        for k, it in enumerate(self.items):
            a = ui.anim(t, it['t_name'], it['t_out'])
            if a:
                s, al, dy = a
                img, pad = self.item_card(k, t >= it['t_tier'])
                pop = 1 + 0.07 * math.sin(math.pi * min(1, max(0, (t - it['t_tier']) / 0.25))) if it['t_tier'] <= t <= it['t_tier'] + 0.25 else 1
                ui.place(front, img, W / 2, self.card_top + (img.height - 2 * pad) / 2 + dy + bob(2), s * pop, al)
        c = self.p.get('cta')
        if c:
            a = ui.anim(t, c['in'], 1e9)
            if a:
                s, al, dy = a
                n_total = len(c.get('prompt', 'Tell me in the comments'))
                n = int(n_total * min(1, max(0, (t - c['in'] - 1.0) / 0.9)))
                card, _ = self.cta_card(n)
                img, pad = ui.with_shadow(card, 0.5)
                ui.place(front, img, W / 2, self.card_top + 20 + card.height / 2 + dy + bob(2), s, al)
        out = src.convert('RGBA')
        out.alpha_composite(behind)
        out.alpha_composite(ui.person_layer(src, mask))
        out.alpha_composite(front)
        return out.convert('RGB')

    def render(self):
        sp = self.p.get('speed', 1.0)
        enc = Encoder(self.out, self.video, speed=sp)
        for i, src in enumerate(frames(self.video), start=1):
            enc.write(self.frame((i - 1) / FPS, src, M.load(self.mask_dir, i)))
            if i % 300 == 0:
                print('frames', i, flush=True)
        enc.close()
        times = [it['t_tier'] + 0.6 for it in self.items][::max(1, len(self.items) // 5)][:5]
        sheet = contact_sheet(self.out, [x / sp for x in times], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        for t in times:
            img = self.frame(t, still(self.video, t), M.load(self.mask_dir, int(round(t * FPS)) + 1))
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg'); img.save(p, quality=88); print(p)


if __name__ == '__main__':
    reel = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        reel.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        reel.render()
