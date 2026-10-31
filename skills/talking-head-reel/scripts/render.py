"""Talking-head reel: dead air cut, punch zoom on every caption line, bold captions with a sliding
highlight box, a big hook line with a boom, light grade + background blur, centred subject, sound
effects, everything inside the YouTube Shorts / Reels / TikTok safe zone.

Usage:
  python render.py PLAN.json --preview 0.5 3.0 8.0      (source-time stills, safe area outlined)
  python render.py PLAN.json
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from reelkit import ui, fx
from reelkit.video import frames, still, W, H, FPS, contact_sheet

F = ui.font


def eo(x): return ui.ease_out(x)
def eb(x, k=1.7): return ui.ease_back(x, k)
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))


class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        p = self.p = json.load(open(plan_path))
        rel = lambda x: os.path.join(self.base, x) if x else None
        self.video, self.out = rel(p['video']), rel(p.get('out', 'out.mp4'))
        self.masks = rel(p.get('masks')) if p.get('masks') else None
        self.accent = ui.hex_rgb(p.get('accent', '#D97757'))
        self.lines = p['lines']
        self.keep = p['keep'] if p.get('cut_dead_air', True) and p.get('keep') else None
        head = p.get('head') or {}
        self.cx = head.get('center', W // 2)
        self.dx = (self.cx - W // 2) if p.get('center_subject', True) else 0
        top = head.get('top_typical', 600)
        chin = head.get('chin', 1200)
        self.face = (W // 2, int((top + chin) / 2), int((chin - top) * 0.75))
        # captions sit below the chin, inside the safe zone
        self.cap_y = int(min(fx.SAFE_B - 90, max(chin + 110, 1180)))
        self.hook_y = int(max(fx.SAFE_T + 90, min(top - 120, 480)))
        self.starts = [ln['words'][0][1] for ln in self.lines]
        self.cut_points = [b[0] for b in self.keep[1:]] if self.keep else []

    def kept(self, t):
        return self.keep is None or any(a <= t < b for a, b in self.keep)

    def line_at(self, t):
        i = max([k for k, s in enumerate(self.starts) if s <= t + 0.03], default=-1)
        if i >= 0 and t > self.lines[i]['end'] + 0.25:
            return -1
        return i

    def zoom(self, t, i):
        if i < 0:
            return 1.0
        q = t - self.starts[i]
        base = (1.0, 1.12, 1.05, 1.15)[i % 4]
        return base + 0.06 * math.exp(-q * 10)

    def draw_line(self, c, t, i, hook):
        ln = self.lines[i]
        words = ln['words']
        hi = set(ln.get('hi', []))
        txt = ' '.join(w for w, _ in words)
        size = 96 if hook else 64
        f = ui.fit_font('InterDisplay-Black', txt.upper(), fx.SAFE_R - fx.SAFE_L - 60, size)
        sp = ui.text_width(' ', f)
        boxes, x = [], (fx.SAFE_L + fx.SAFE_R) / 2 - ui.text_width(txt.upper(), f) / 2
        for w, ws in words:
            ww = ui.text_width(w.upper(), f); boxes.append((x, ww, ws)); x += ww + sp
        y = self.hook_y if hook else self.cap_y
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        act = max([k for k, (_, _, ws) in enumerate(boxes) if ws <= t], default=0)
        if not hook:  # sliding highlight box behind the spoken word
            bx, bw, bws = boxes[act]
            if act > 0:
                px, pw, _ = boxes[act - 1]
                s = eo(cl((t - bws) / 0.1))
                bx, bw = px + (bx - px) * s, pw + (bw - pw) * s
            pad = int(f.size * 0.18)
            d.rounded_rectangle([bx - pad, y - f.size * 0.62, bx + bw + pad, y + f.size * 0.62], int(f.size * 0.2), fill=self.accent + (255,))
        for k, (wx, ww, ws) in enumerate(boxes):
            if ws > t + 0.02:
                continue
            p = eb(cl((t - ws + 0.02) / 0.18), 2.3)
            word = words[k][0].upper()
            col = (246, 226, 96) if (hook and k in hi) else (255, 255, 255)
            wl = Image.new('RGBA', (int(ww + 60), int(f.size * 1.8)), (0, 0, 0, 0))
            wd = ImageDraw.Draw(wl)
            wd.text((wl.width / 2, wl.height / 2 + 5), word, font=f, fill=(0, 0, 0, 170), anchor='mm')
            wl.alpha_composite(wl.filter(ImageFilter.GaussianBlur(6)))
            ImageDraw.Draw(wl).text((wl.width / 2, wl.height / 2), word, font=f, fill=col, anchor='mm')
            ui.place(lay, wl, wx + ww / 2, y + 14 * (1 - cl(p)), scale=0.65 + 0.35 * p)
        c.alpha_composite(lay)

    def cta(self, c, t):
        cta = self.p.get('cta')
        if not cta or t < cta['from']:
            return
        p = eb(cl((t - cta['from']) / 0.35), 1.8)
        f = ui.fit_font('InterDisplay-Black', cta['text'], fx.SAFE_R - fx.SAFE_L - 120, 54)
        tw = ui.text_width(cta['text'], f)
        pill = ui.panel(int(tw + 70), int(f.size * 1.7), int(f.size * 0.85), self.accent + (255,))
        ImageDraw.Draw(pill).text((pill.width / 2, pill.height / 2), cta['text'], font=f, fill=(255, 255, 255), anchor='mm')
        ui.place(c, pill, (fx.SAFE_L + fx.SAFE_R) / 2, self.hook_y, scale=0.6 + 0.4 * p, alpha=cl(p))

    def frame(self, t, src, n, safe=False):
        m = fx.subject_mask(self.masks, n)
        g = fx.center_shift(fx.grade(src, m, face=(self.cx, self.face[1], self.face[2])), self.dx)
        i = self.line_at(t)
        c = fx.camera(g, self.zoom(t, i), cx=W // 2, cy=self.face[1]).convert('RGBA')
        hook = i == 0 and self.p.get('hook', True)
        if i >= 0 and not (self.p.get('cta') and t >= self.p['cta']['from'] and self.p['cta'].get('replace_captions')):
            self.draw_line(c, t, i, hook)
        if hook and t - self.starts[0] < 0.07:
            c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(90 * (1 - (t - self.starts[0]) / 0.07)))))
        if any(0 <= t - cp < 0.034 for cp in self.cut_points):  # one bright frame hides each jump cut
            c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, 60)))
        self.cta(c, t)
        if safe:
            fx.draw_safe(c)
        return c.convert('RGB')

    def out_time(self, t):
        if not self.keep:
            return t
        acc = 0.0
        for a, b in self.keep:
            if t >= b:
                acc += b - a
            elif t >= a:
                return acc + t - a
            else:
                break
        return acc

    def sfx_events(self):
        ev = []
        if self.lines:
            ev.append((self.starts[0], 'boom', 0.8, 1)); ev.append((self.starts[0], 'pop', 0.5, 2))
        for k, s in enumerate(self.starts[1:]):
            ev.append((s, 'tick', 0.28, 10 + k))
        for k, cp in enumerate(self.cut_points):
            ev.append((cp, 'swish', 0.45, 100 + k))
        if self.p.get('cta'):
            ev.append((self.p['cta']['from'], 'ding', 0.7, 0))
        return [(self.out_time(t), kind, g, s) for t, kind, g, s in ev if self.kept(t)]

    def render(self):
        silent = self.out + '.video.mp4'
        wr = fx.SilentWriter(silent)
        for i, src in enumerate(frames(self.video)):
            t = i / FPS
            if self.kept(t):
                wr.write(self.frame(t, src, i + 1))
            if i % 90 == 0:
                print('frame', i, flush=True)
        wr.close()
        total = sum(b - a for a, b in self.keep) if self.keep else None
        wav = self.out + '.sfx.wav'
        from reelkit.video import probe
        fx.mix_track(self.sfx_events(), total or probe(self.video)[0], wav)
        fx.finish(silent, self.video, wav, self.out, keep=self.keep)
        os.remove(silent); os.remove(wav)
        dur = probe(self.out)[0]
        sheet = contact_sheet(self.out, [dur * k / 6 for k in range(1, 6)], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        for t in times:
            n = int(round(t * FPS)) + 1
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg')
            self.frame(t, still(self.video, t), n, safe=True).save(p, quality=88); print(p)


if __name__ == '__main__':
    r = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        r.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        r.render()
