"""Carousel to reel: turns carousel slides (images) into a vertical video. Each slide sits on a soft
blurred copy of itself, inside the YouTube Shorts / Reels / TikTok safe zone, with story-style progress
bars, a slow push-in, push transitions with depth, optional hook and CTA pills, optional voiceover,
and sound effects on every transition.

Usage:
  python render.py PLAN.json --preview 0.5 2.4 5.0
  python render.py PLAN.json
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from reelkit import ui, fx
from reelkit.video import W, H, FPS, probe, contact_sheet

F = ui.font
TRANS = 0.34


def eo(x): return ui.ease_out(x)
def eb(x, k=1.7): return ui.ease_back(x, k)
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))


class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        p = self.p = json.load(open(plan_path))
        rel = lambda x: os.path.join(self.base, x) if x else None
        self.out = rel(p.get('out', 'out.mp4'))
        self.voice = rel(p.get('voice')) if p.get('voice') else None
        self.accent = ui.hex_rgb(p.get('accent', '#D97757'))
        self.slides = [s if isinstance(s, dict) else {'image': s} for s in p['slides']]
        self.durs = [s.get('duration', p.get('duration', 2.2)) for s in self.slides]
        self.starts = [sum(self.durs[:i]) for i in range(len(self.durs))]
        self.total = sum(self.durs) + p.get('tail', 0.4)
        # fit the card inside the safe zone
        mw, mh = fx.SAFE_R - fx.SAFE_L - 72, fx.SAFE_B - fx.SAFE_T - 220   # room for progress, hook and CTA
        self.cards, self.bgs = [], []
        for s in self.slides:
            im = Image.open(rel(s['image'])).convert('RGB')
            sc = min(mw / im.width, mh / im.height)
            cw, ch = int(im.width * sc), int(im.height * sc)
            big = im.resize((int(cw * 1.08), int(ch * 1.08)), Image.LANCZOS)  # headroom for the push-in
            self.cards.append((big, cw, ch))
            bg = im.resize((W // 8, int(W / 8 * im.height / im.width)), Image.BILINEAR)
            r = max(W / bg.width, H / bg.height) * 8
            bg = bg.resize((int(bg.width * r / 8 * 1.1), int(bg.height * r / 8 * 1.1)), Image.BILINEAR)
            bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
            bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.55)
            self.bgs.append(bg)
        self.cy = fx.SAFE_T + 120 + mh / 2

    def card(self, k, u):
        big, cw, ch = self.cards[k]
        z = 1.0 + 0.05 * cl(u / max(self.durs[k], 0.1))
        w, h = big.width / 1.08 * 1.08 / z, big.height / 1.08 * 1.08 / z
        x0, y0 = (big.width - w) / 2, (big.height - h) / 2
        img = big.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((cw, ch), Image.LANCZOS)
        img = ui.rounded(img, 28)
        sh, pad = ui.with_shadow(img, 0.55, 30, 20, (0, 0, 0))
        return sh

    def slide_at(self, t):
        return max([i for i, s in enumerate(self.starts) if s <= t], default=0)

    def frame(self, t, safe=False):
        k = self.slide_at(t)
        u = t - self.starts[k]
        q = cl(u / TRANS) if k > 0 else 1.0
        e = eo(q)
        c = self.bgs[k].copy().convert('RGBA')
        if q < 1:
            prev = self.bgs[k - 1].copy().convert('RGBA')
            prev.putalpha(int(255 * (1 - e)))
            c.alpha_composite(prev)
        cx = (fx.SAFE_L + fx.SAFE_R) / 2
        if k == 0:
            p = eb(cl(t / 0.45), 1.4)
            ui.place(c, self.card(0, u), cx, self.cy + 120 * (1 - cl(p)), scale=0.9 + 0.1 * p, alpha=cl(t / 0.15))
        else:
            if q < 1:
                ui.place(c, self.card(k - 1, self.durs[k - 1] + u), cx - 420 * e, self.cy, scale=1 - 0.14 * e, alpha=1 - 0.7 * e, rot=4 * e)
            ui.place(c, self.card(k, u), cx + (W * 0.9) * (1 - e), self.cy, rot=-5 * (1 - e))
        # story progress bars, inside the safe zone
        d = ImageDraw.Draw(c)
        n = len(self.slides)
        L, R, y = fx.SAFE_L, fx.SAFE_R, fx.SAFE_T + 8
        seg = (R - L - (n - 1) * 8) / n
        for j in range(n):
            x = L + j * (seg + 8)
            d.rounded_rectangle([x, y, x + seg, y + 7], 4, fill=(255, 255, 255, 90))
            fw = seg if j < k else (seg * cl(u / self.durs[k]) if j == k else 0)
            if fw > 1:
                d.rounded_rectangle([x, y, x + fw, y + 7], 4, fill=(255, 255, 255, 255))
        hook = self.p.get('hook')
        if hook and k == 0:
            self.pill(c, hook, fx.SAFE_T + 64, eb(cl((t - 0.2) / 0.35), 1.8), dark=True)
        cta = self.p.get('cta')
        if cta and t >= self.starts[-1] + 0.3:
            self.pill(c, cta, fx.SAFE_B - 46, eb(cl((t - self.starts[-1] - 0.3) / 0.35), 1.8))
        if t > self.total - 0.45:
            c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(230 * cl((t - (self.total - 0.45)) / 0.45)))))
        if safe:
            fx.draw_safe(c)
        return c.convert('RGB')

    def pill(self, c, text, y, p, dark=False):
        if p <= 0:
            return
        f = ui.fit_font('InterDisplay-Black', text, fx.SAFE_R - fx.SAFE_L - 100, 42)
        pl = ui.panel(int(ui.text_width(text, f) + 64), int(f.size * 1.7), int(f.size * 0.85),
                      (16, 14, 14, 230) if dark else self.accent + (255,))
        ImageDraw.Draw(pl).text((pl.width / 2, pl.height / 2), text, font=f, fill='white', anchor='mm')
        ui.place(c, pl, (fx.SAFE_L + fx.SAFE_R) / 2, y, scale=0.6 + 0.4 * p, alpha=cl(p))

    def sfx_events(self):
        ev = [(0.0, 'whoosh', 0.6, 1), (0.25, 'pop', 0.45, 2)]
        for k, s in enumerate(self.starts[1:]):
            ev += [(s - 0.03, 'whoosh', 0.55, 10 + k), (s + TRANS * 0.8, 'tick', 0.3, 30 + k)]
        if self.p.get('cta'):
            ev.append((self.starts[-1] + 0.3, 'ding', 0.6, 0))
        return ev

    def render(self):
        silent = self.out + '.video.mp4'
        wr = fx.SilentWriter(silent)
        n = int(self.total * FPS)
        for i in range(n):
            wr.write(self.frame(i / FPS))
        wr.close()
        wav = self.out + '.sfx.wav'
        fx.mix_track(self.sfx_events(), self.total, wav)
        fx.finish(silent, self.voice, wav, self.out, speech=bool(self.voice), sfx_db=-5 if self.voice else -2)
        os.remove(silent); os.remove(wav)
        d = probe(self.out)[0]
        sheet = contact_sheet(self.out, [d * k / 6 for k in range(1, 6)], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        for t in times:
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg')
            self.frame(t, safe=True).save(p, quality=88); print(p)


if __name__ == '__main__':
    r = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        r.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        r.render()
