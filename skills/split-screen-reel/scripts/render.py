"""Split-screen 'write this / get this' reel: a chat panel on top (a command types out, a 'before'
clip on the left, the finished reel pops in on the right), the speaker's face cam below, and a
two-part ending (end card, then a dimmed screen with a social logo and handle).

Usage:
  python render.py PLAN.json
  python render.py PLAN.json --preview 1.0 3.6 12.5
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from reelkit import ui
from reelkit.video import frames, grab, still, Encoder, contact_sheet, W, H, FPS
from reelkit import masks as M

SS = ui.SS
THEMES = {
    'light': dict(bg=(239, 238, 234), box=(255, 255, 255), border=(226, 224, 218), icon=(110, 108, 104), label=(120, 118, 112),
                  hint=(160, 158, 152), cursor=(40, 40, 40), intro=(38, 37, 34), shadow=40),
    'dark': dict(bg=(38, 36, 37), box=(46, 44, 45), border=(66, 63, 64), icon=(170, 166, 160), label=(160, 156, 150),
                 hint=(130, 126, 122), cursor=(235, 232, 228), intro=(240, 237, 232), shadow=90),
}
LW, LH, LX, LY = 400, 500, 105, 315      # 'before' card
RW, RH, RX, RY = 428, 760, 546, 56       # 'after' card
TOP_H = 960


def rmask(w, h, r):
    m = Image.new('L', (w * SS, h * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def soft_shadow(w, h, r, alpha, blur=18):
    pad = 50
    s = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([pad, pad + 8, pad + w, pad + h + 8], r, fill=(0, 0, 0, alpha))
    return s.filter(ImageFilter.GaussianBlur(blur)), pad


class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        p = self.p = json.load(open(plan_path))
        self.rel = lambda x: os.path.join(self.base, x) if x else None
        self.video, self.out = self.rel(p['video']), self.rel(p.get('out', 'out.mp4'))
        self.th = THEMES[p.get('theme', 'light')]
        self.accent = ui.hex_rgb(p.get('accent', '#D97757'))
        self.cmd_color = ui.mix(self.accent, (255, 255, 255), 0.3) if p.get('theme') == 'dark' else self.accent
        self.pairs = p['pairs']
        self.end = p.get('end', {})
        self.end_in = self.end.get('in', 1e9)
        self.total = self.end.get('total')
        # face cam crop, centred on the head when a cutout exists
        lay = M.head_layout(self.rel(p.get('masks', 'masks'))) if os.path.isdir(self.rel(p.get('masks', 'masks'))) else None
        cw, ch = 990, 880
        if lay:
            x0 = min(max(lay['center'] - cw // 2, 0), W - cw)
            y0 = min(max(lay['top_typical'] - 110, 0), H - ch)
        else:
            x0, y0 = 45, 440
        self.face_box = (x0, y0, x0 + cw, y0 + ch)
        self.lmask, self.rmask_ = rmask(LW, LH, 22), rmask(RW, RH, 26)
        self.lsh, self.rsh = soft_shadow(LW, LH, 22, self.th['shadow']), soft_shadow(RW, RH, 26, self.th['shadow'])
        self.csh = soft_shadow(1000, 92, 30, self.th['shadow'] // 2, 14)
        self.left, self.right = [], []
        for i, pr in enumerate(self.pairs):
            nxt = self.pairs[i + 1]['start'] if i + 1 < len(self.pairs) else self.end_in
            b, a = pr['before'], pr['after']
            cy = b.get('crop_y', 270)
            self.left.append(grab(self.rel(b['video']), b.get('t0', 0), nxt - pr['start'] + 0.2, (LW, LH), crop=(0, cy, 1080, 1350)))
            self.right.append(grab(self.rel(a['video']), a.get('t0', 0), nxt - pr['get'] + 0.2, (RW, RH)))
        if self.end:
            dur = (self.total or self.end_in + 3) - self.end_in + 0.3
            self.inset = grab(self.video, self.end_in, dur, (420, 746))
            self.imask = rmask(420, 746, 26)

    # ----- chat box -----
    def composer(self, text, cursor, placeholder=''):
        th, w, h = self.th, 1000, 92
        img = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], 30 * SS, fill=th['box'], outline=th['border'], width=2 * SS)
        cy = h / 2
        d.line([(30 * SS, cy * SS), (56 * SS, cy * SS)], fill=th['icon'], width=3 * SS)
        d.line([(43 * SS, (cy - 13) * SS), (43 * SS, (cy + 13) * SS)], fill=th['icon'], width=3 * SS)
        ft = ui.font('Inter-Regular', 40 * SS)
        if text:
            d.text((90 * SS, cy * SS), text, font=ft, fill=self.cmd_color, anchor='lm')
            tx = 90 * SS + d.textlength(text, font=ft)
        else:
            if placeholder:
                d.text((90 * SS, cy * SS), placeholder, font=ft, fill=th['hint'], anchor='lm')
            tx = 90 * SS
        if cursor:
            d.rectangle([tx + 3 * SS, (cy - 22) * SS, tx + 6 * SS, (cy + 22) * SS], fill=th['cursor'])
        label = self.p.get('model_label', '')
        if label:
            d.text((838 * SS, cy * SS), label, font=ui.font('Inter-Regular', 32 * SS), fill=th['label'], anchor='rm')
            d.line([(846 * SS, (cy - 4) * SS), (853 * SS, (cy + 3) * SS), (860 * SS, (cy - 4) * SS)], fill=th['label'], width=3 * SS)
        mx = 892
        d.rounded_rectangle([(mx - 8) * SS, (cy - 20) * SS, (mx + 8) * SS, (cy + 4) * SS], 8 * SS, outline=th['icon'], width=3 * SS)
        d.arc([(mx - 14) * SS, (cy - 12) * SS, (mx + 14) * SS, (cy + 12) * SS], 0, 180, fill=th['icon'], width=3 * SS)
        d.line([(mx * SS, (cy + 12) * SS), (mx * SS, (cy + 20) * SS)], fill=th['icon'], width=3 * SS)
        ui.send_button(d, 957, cy, 30, self.accent, SS)
        return img.resize((w, h), Image.LANCZOS)

    def card(self, canvas, img, mask, sh, x, y, alpha=1.0):
        s, pad = sh
        if alpha < 1:
            mask = mask.point(lambda v: int(v * alpha))
            s = s.copy(); s.putalpha(s.getchannel('A').point(lambda v: int(v * alpha)))
        canvas.alpha_composite(s, (x - pad, y - pad))
        rgba = img.convert('RGBA'); rgba.putalpha(mask)
        canvas.alpha_composite(rgba, (x, y))

    # ----- frames -----
    def frame(self, t, src):
        if t >= self.end_in:
            return self.end_card(t)
        top = Image.new('RGBA', (W, TOP_H), self.th['bg'] + (255,))
        cur = max([i for i, pr in enumerate(self.pairs) if pr['start'] <= t], default=-1)
        blink = int(t * 2.4) % 2 == 0
        if cur < 0:
            intro = self.p.get('intro')
            if intro:
                p = ui.ease_out((t - intro.get('in', 0.15)) / 0.5)
                if p > 0:
                    lay = Image.new('RGBA', (W, TOP_H), (0, 0, 0, 0))
                    f = ui.fit_font('InterDisplay-SemiBold', intro['text'], W - 120, 66)
                    ImageDraw.Draw(lay).text((W / 2, 450 + 30 * (1 - p)), intro['text'], font=f, fill=self.th['intro'] + (int(255 * p),), anchor='mm')
                    top.alpha_composite(lay)
            comp = self.composer('', blink, self.p.get('placeholder', 'Reply to Claude...'))
        else:
            pr = self.pairs[cur]
            n = min(len(pr['cmd']), 1 + int(max(0.0, t - pr['start']) * 15))  # '/' at once, then ~15 characters a second
            comp = self.composer(pr['cmd'][:n], blink or n < len(pr['cmd']))
            li = min(int((t - pr['start']) * FPS), len(self.left[cur]) - 1)
            if li >= 0 and self.left[cur]:
                self.card(top, self.left[cur][li], self.lmask, self.lsh, LX, LY)
            if t >= pr['get'] and self.right[cur]:
                ri = min(int((t - pr['get']) * FPS), len(self.right[cur]) - 1)
                self.card(top, self.right[cur][ri], self.rmask_, self.rsh, RX, RY, alpha=max(0.35, min(1.0, (t - pr['get']) / 0.067)))
        top.alpha_composite(self.csh[0], (40 - self.csh[1], 849 - self.csh[1]))
        top.alpha_composite(comp, (40, 849))
        out = Image.new('RGB', (W, H))
        out.paste(top.convert('RGB'), (0, 0))
        out.paste(src.crop(self.face_box).resize((W, H - TOP_H), Image.LANCZOS), (0, TOP_H))
        return out

    def end_card(self, t):
        e = self.end
        c = Image.new('RGBA', (W, H), (18, 16, 14, 255) if self.p.get('theme') == 'dark' else (20, 20, 20, 255))
        d = ImageDraw.Draw(c)
        hf = ui.fit_font(e.get('headline_font', 'InterDisplay-Bold'), e.get('headline', 'Follow for more'), W - 120, 92)
        d.text((W / 2, 300), e.get('headline', 'Follow for more'), font=hf, fill=(255, 255, 255), anchor='mm')
        pill = e.get('pill', '')
        if pill:
            pf = ui.fit_font('Inter-Bold', pill, W - 160, 40)
            tw = ui.text_width(pill, pf)
            d.rounded_rectangle([W / 2 - tw / 2 - 22, 372, W / 2 + tw / 2 + 22, 436], 10, fill=self.accent)
            d.text((W / 2, 404), pill, font=pf, fill=(255, 255, 255), anchor='mm')
        if e.get('sub'):
            d.text((W / 2, 478), e['sub'], font=ui.fit_font('Inter-Medium', e['sub'], W - 160, 34), fill=(235, 232, 228), anchor='mm')
        i = min(int((t - self.end_in) * FPS), len(self.inset) - 1)
        ins = self.inset[i].convert('RGBA')
        logo_at = e.get('logo_at', 1e9)
        words = [w for w, ws in e.get('captions', []) if ws <= t]
        if words and t < logo_at:
            idt = ImageDraw.Draw(ins)
            f = ui.font('Inter-Bold', 30)
            idt.text((212, 746 * 0.62 + 2), ' '.join(words), font=f, fill=(0, 0, 0, 160), anchor='mm')
            idt.text((210, 746 * 0.62), ' '.join(words), font=f, fill=(255, 255, 255), anchor='mm')
        ins.putalpha(self.imask)
        c.alpha_composite(ins, ((W - 420) // 2, 540))
        name = e.get('handle', '')
        if name:
            c.alpha_composite(ui.ig_glyph(46, 0), (40, 880))
            ImageDraw.Draw(c).text((40, 946), name, font=ui.font('Inter-Bold', 22), fill=(235, 232, 228))
        if t >= logo_at:  # hard cut to the dimmed logo moment
            c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 185)))
            q = t - logo_at
            c.alpha_composite(ui.ig_glyph(150, min(1.0, max(0.0, (q - 0.25) / 0.6))), ((W - 150) // 2, 850))
            if q > 0.15 and name:
                ImageDraw.Draw(c).text((W / 2, 1050), name, font=ui.font('Inter-Bold', 34), fill=(255, 255, 255), anchor='mm')
        return c.convert('RGB')

    def render(self):
        sp = self.p.get('speed', 1.0)
        enc = Encoder(self.out, self.video, speed=sp, pad=bool(self.total))
        i, src = 0, None
        for src in frames(self.video):
            enc.write(self.frame(i / FPS, src)); i += 1
        while self.total and i / FPS < self.total:  # run past the speech for the logo ending
            enc.write(self.frame(i / FPS, src)); i += 1
        enc.close()
        times = [pr['get'] + 0.3 for pr in self.pairs][:4] + ([self.end_in + 0.6] if self.end else [])
        sheet = contact_sheet(self.out, [x / sp for x in times], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        for t in times:
            src = still(self.video, min(t, self.end_in)) or Image.new('RGB', (W, H))
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg'); self.frame(t, src).save(p, quality=88); print(p)


if __name__ == '__main__':
    reel = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        reel.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        reel.render()
