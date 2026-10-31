"""Explainer reel: a tip turned into a split screen. Full-screen hook first, then a panel drops in on top
with a title chip, an animated chart (line, bar or steps) with a rolling counter and a badge, short captions
under the chart, and the speaker's face cam below. Light grade + background blur, centred subject,
sound effects, everything inside the YouTube Shorts / Reels / TikTok safe zone.

Usage:
  python render.py PLAN.json --preview 1.0 4.0 9.0
  python render.py PLAN.json
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from reelkit import ui, fx
from reelkit.video import frames, still, probe, W, H, FPS, contact_sheet

F = ui.font
TOP_H = 870
YEL = (246, 226, 96)
THEMES = {'dark': dict(bg=(20, 18, 17), ink=(255, 255, 255), sub=(170, 162, 156), grid=(255, 255, 255, 28)),
          'light': dict(bg=(244, 240, 233), ink=(28, 24, 22), sub=(110, 104, 98), grid=(0, 0, 0, 26))}


def eo(x): return ui.ease_out(x)
def eb(x, k=1.7): return ui.ease_back(x, k)
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))


def shadow_text(img, xy, s, f, fill, anchor='mm'):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((xy[0], xy[1] + 5), s, font=f, fill=(0, 0, 0, 170), anchor=anchor)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(img).text(xy, s, font=f, fill=fill, anchor=anchor)


class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        p = self.p = json.load(open(plan_path))
        rel = lambda x: os.path.join(self.base, x) if x else None
        self.video, self.out = rel(p['video']), rel(p.get('out', 'out.mp4'))
        self.masks = rel(p.get('masks')) if p.get('masks') else None
        self.accent = ui.hex_rgb(p.get('accent', '#D97757'))
        self.th = THEMES[p.get('theme', 'dark')]
        self.dur = probe(self.video)[0]
        head = p.get('head') or {}
        self.cx = head.get('center', W // 2)
        self.dx = self.cx - W // 2 if p.get('center_subject', True) else 0
        self.top, self.chin = head.get('top_typical', 600), head.get('chin', 1200)
        self.face = (self.cx, int((self.top + self.chin) / 2), int((self.chin - self.top) * 0.75))
        self.hook_until = p.get('hook_until', 0)
        self.lines = p.get('lines', [])
        self.starts = [ln['words'][0][1] for ln in self.lines]
        ch = p['chart']
        self.chart = ch
        self.chart_in = ch.get('in', self.hook_until + 0.5)
        self.chart_dur = ch.get('duration', 2.2)
        self.badge_at = ch.get('badge_at', self.chart_in + self.chart_dur)
        # face cam crop: full width, head near the top of the bottom area
        y0 = int(min(max(self.top - 40, 0), H - (H - TOP_H)))
        self.face_box = (0, y0, W, y0 + H - TOP_H)

    # ---------- pieces ----------
    def panel_bg(self, t):
        c = Image.new('RGBA', (W, TOP_H), self.th['bg'] + (255,))
        gl = Image.new('RGBA', (W // 4, TOP_H // 4), (0, 0, 0, 0))
        x = W // 4 * 0.78 + 8 * math.sin(t * 0.4)
        ImageDraw.Draw(gl).ellipse([x - 40, 40, x + 40, 110], fill=self.accent + (70,))
        c.alpha_composite(gl.filter(ImageFilter.GaussianBlur(16)).resize((W, TOP_H), Image.BILINEAR))
        return c

    def chart_layer(self, c, t):
        ch, th = self.chart, self.th
        d = ImageDraw.Draw(c)
        L, R, T, B = fx.SAFE_L + 10, fx.SAFE_R - 10, 400, 700
        u = t - self.chart_in
        # chip + title
        p = eb(cl((t - self.hook_until) / 0.3), 2)
        label = ch.get('label', 'TIP')
        cf = F('Inter-Black', 24)
        cw = int(ui.text_width(label, cf) + 36)
        chip = ui.panel(cw, 44, 22, self.accent + (255,))
        ImageDraw.Draw(chip).text((cw / 2, 22), label, font=cf, fill='white', anchor='mm')
        ui.place(c, chip, L + cw / 2, fx.SAFE_T + 30, scale=0.6 + 0.4 * p, alpha=cl(p))
        title = ch.get('title', '')
        tf = ui.fit_font('InterDisplay-Black', title, R - L, 52)
        tq = eo(cl((t - self.hook_until - 0.12) / 0.4))
        d.text((L, fx.SAFE_T + 98 + 14 * (1 - tq)), title, font=tf, fill=th['ink'] + (int(255 * tq),), anchor='lm')
        pts = ch['points']
        vals = [v for _, v in pts]
        vmax = ch.get('max', max(vals) * 1.1 or 1)
        prog = eo(cl(u / self.chart_dur))
        kind = ch.get('type', 'line')
        sub = th['sub']
        unit = ch.get('unit', '')
        if kind in ('line', 'bar'):
            for gy in range(4):
                yy = T + gy * (B - T) / 3
                d.line([(L, yy), (R, yy)], fill=th['grid'], width=1)
            for k, (lab, v) in enumerate(pts):
                x = L + (k + 0.5) * (R - L) / len(pts) if kind == 'bar' else L + k * (R - L) / max(1, len(pts) - 1)
                d.text((x, B + 26), str(lab), font=F('Inter-Medium', 20), fill=sub, anchor='mm')
        if kind == 'line' and u > 0:
            P = [(L + k * (R - L) / max(1, len(pts) - 1), B - v / vmax * (B - T)) for k, (_, v) in enumerate(pts)]
            k = prog * (len(P) - 1)
            line = P[:int(k) + 1]
            if int(k) < len(P) - 1:
                a, b = P[int(k)], P[int(k) + 1]; fr = k - int(k)
                line = line + [(a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr)]
            if len(line) > 1:
                glow = Image.new('RGBA', c.size, (0, 0, 0, 0))
                ImageDraw.Draw(glow).line(line, fill=self.accent + (200,), width=14, joint='curve')
                c.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
                area = Image.new('RGBA', c.size, (0, 0, 0, 0))
                ImageDraw.Draw(area).polygon([(line[0][0], B)] + line + [(line[-1][0], B)], fill=self.accent + (60,))
                c.alpha_composite(area)
                d = ImageDraw.Draw(c)
                d.line(line, fill=self.accent, width=6, joint='curve')
                hx, hy = line[-1]
                d.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], fill='white', outline=self.accent, width=4)
                seg = min(int(k), len(vals) - 2) if len(vals) > 1 else 0
                cur = vals[seg] + (vals[min(seg + 1, len(vals) - 1)] - vals[seg]) * (k - seg) if len(vals) > 1 else vals[0]
                self.counter(c, cur, unit)
        elif kind == 'bar' and u > 0:
            n = len(pts)
            bw = (R - L) / n * 0.6
            for k, (_, v) in enumerate(pts):
                q = eo(cl((u - k * 0.12) / (self.chart_dur * 0.6)))
                x = L + (k + 0.5) * (R - L) / n
                hgt = v / vmax * (B - T) * q
                col = self.accent if k == len(pts) - 1 else tuple(int(a * 0.55 + b * 0.45) for a, b in zip(sub, th['bg']))
                if hgt > 2:
                    d.rounded_rectangle([x - bw / 2, B - hgt, x + bw / 2, B], 10, fill=col)
                if q > 0.7:
                    d.text((x, B - hgt - 22), f'{v:g}{unit}', font=F('Inter-Bold', 24), fill=th['ink'], anchor='mm')
        elif kind == 'steps':
            for k, (lab, _) in enumerate(pts):
                at = ch.get('step_times', [self.chart_in + k * 0.6 for k in range(len(pts))])[k]
                q = eb(cl((t - at) / 0.3), 1.8)
                if q <= 0:
                    continue
                y = T - 20 + k * 78
                ui.place(c, self.step_row(k + 1, str(lab)), L + (R - L) / 2 + 40 * (1 - cl(q)), y, alpha=cl(q))
        if ch.get('badge') and t >= self.badge_at:
            q = eb(cl((t - self.badge_at) / 0.3), 2.2)
            bf = F('Inter-Black', 28)
            bwid = int(ui.text_width(ch['badge'], bf) + 44)
            badge = ui.panel(bwid, 54, 27, YEL + (255,))
            ImageDraw.Draw(badge).text((bwid / 2, 27), ch['badge'], font=bf, fill=(24, 20, 14), anchor='mm')
            ui.place(c, badge, L + bwid / 2 + 10, T + 10, scale=0.6 + 0.4 * q, alpha=cl(q), rot=-4)

    def counter(self, c, v, unit):
        d = ImageDraw.Draw(c)
        R = fx.SAFE_R - 10
        d.text((R, 420), f'{v:.0f}', font=F('InterDisplay-Black', 70), fill=self.th['ink'], anchor='rm')
        if unit:
            d.text((R, 470), unit.strip(), font=F('Inter-SemiBold', 24), fill=self.th['sub'], anchor='rm')

    def step_row(self, n, text):
        w = fx.SAFE_R - fx.SAFE_L - 20
        row = ui.panel(w, 64, 18, (255, 255, 255, 22) if self.p.get('theme', 'dark') == 'dark' else (255, 255, 255, 255))
        d = ImageDraw.Draw(row)
        d.ellipse([12, 12, 52, 52], fill=self.accent)
        d.text((32, 32), str(n), font=F('Inter-Black', 22), fill='white', anchor='mm')
        d.text((68, 32), text, font=ui.fit_font('Inter-SemiBold', text, w - 90, 30), fill=self.th['ink'], anchor='lm')
        return row

    def caption(self, c, t, y, size, hook=False):
        i = max([k for k, s in enumerate(self.starts) if s <= t + 0.03], default=-1)
        if i < 0 or t > self.lines[i].get('end', 1e9) + 0.25:
            return
        words = self.lines[i]['words']
        hi = set(self.lines[i].get('hi', []))
        txt = ' '.join(w for w, _ in words)
        f = ui.fit_font('InterDisplay-Black', txt, fx.SAFE_R - fx.SAFE_L - 40, size)
        sp = ui.text_width(' ', f)
        x = (fx.SAFE_L + fx.SAFE_R) / 2 - ui.text_width(txt, f) / 2
        for k, (w, ws) in enumerate(words):
            ww = ui.text_width(w, f)
            if ws <= t + 0.02:
                p = eb(cl((t - ws + 0.02) / 0.18), 2.3)
                col = (YEL if hook else self.accent) if k in hi else (255, 255, 255) if hook else self.th['ink']
                wl = Image.new('RGBA', (int(ww + 60), int(f.size * 1.8)), (0, 0, 0, 0))
                if hook:
                    shadow_text(wl, (wl.width / 2, wl.height / 2), w, f, col)
                else:
                    ImageDraw.Draw(wl).text((wl.width / 2, wl.height / 2), w, font=f, fill=col, anchor='mm')
                ui.place(c, wl, x + ww / 2, y + 12 * (1 - cl(p)), scale=0.65 + 0.35 * p)
            x += ww + sp

    # ---------- frame ----------
    def frame(self, t, src, n, safe=False):
        m = fx.subject_mask(self.masks, n)
        g = fx.center_shift(fx.grade(src, m, face=self.face), self.dx)
        if t < self.hook_until:
            z = 1.0 + 0.08 * math.exp(-max(0, t - (self.starts[0] if self.starts else 0)) * 4)
            c = fx.camera(g, z, cx=W // 2, cy=self.face[1]).convert('RGBA')
            self.caption(c, t, max(fx.SAFE_T + 90, min(self.top - 110, 480)), 96, hook=True)
            if safe:
                fx.draw_safe(c)
            return c.convert('RGB')
        sp = eo(cl((t - self.hook_until) / 0.32))
        x0, y0, x1, y1 = self.face_box
        z = 1.0 + 0.04 * cl((t - self.hook_until) / 8)
        cw, chh = W / z, (y1 - y0) / z
        face = g.crop((int((W - cw) / 2), int(y0), int((W + cw) / 2), int(y0 + chh))).resize((W, H - TOP_H), Image.LANCZOS)
        out = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        out.paste(face, (0, TOP_H))
        top = self.panel_bg(t)
        self.chart_layer(top, t)
        self.caption(top, t, 800, 44)
        if sp < 1:
            back = g.resize((W // 4, H // 4)).crop((0, 0, W // 4, TOP_H // 4)).filter(ImageFilter.GaussianBlur(6)).resize((W, TOP_H))
            out.paste(back, (0, 0))
        out.alpha_composite(top, (0, int(-TOP_H * (1 - sp))))
        ImageDraw.Draw(out).rectangle([0, TOP_H - 3, W * eo(cl((t - self.hook_until) / 0.5)), TOP_H + 3], fill=self.accent)
        cta = self.p.get('cta')
        if cta and t >= cta['from']:
            q = eb(cl((t - cta['from']) / 0.35), 1.8)
            f = ui.fit_font('InterDisplay-Black', cta['text'], fx.SAFE_R - fx.SAFE_L - 120, 50)
            pill = ui.panel(int(ui.text_width(cta['text'], f) + 70), int(f.size * 1.7), int(f.size * 0.85), self.accent + (255,))
            ImageDraw.Draw(pill).text((pill.width / 2, pill.height / 2), cta['text'], font=f, fill='white', anchor='mm')
            ui.place(out, pill, (fx.SAFE_L + fx.SAFE_R) / 2, fx.SAFE_B - 60, scale=0.6 + 0.4 * q, alpha=cl(q))
        if safe:
            fx.draw_safe(out)
        return out.convert('RGB')

    def sfx_events(self):
        ev = []
        if self.starts:
            ev += [(self.starts[0], 'boom', 0.75, 1), (self.starts[0], 'pop', 0.45, 2)]
        if self.hook_until:
            ev.append((self.hook_until - 0.05, 'whoosh', 0.85, 3))
        ev.append((self.chart_in, 'riser', 0.4, 4))
        npts = len(self.chart['points'])
        for k in range(npts):
            ev.append((self.chart_in + self.chart_dur * (k + 1) / max(1, npts) * 0.85, 'tick', 0.25, 20 + k))
        if self.chart.get('badge'):
            ev += [(self.badge_at, 'pop', 0.55, 5), (self.badge_at + 0.02, 'sparkle', 1.0, 0)]
        for k, s in enumerate(self.starts[1:]):
            ev.append((s, 'tick', 0.2, 40 + k))
        if self.p.get('cta'):
            ev.append((self.p['cta']['from'], 'ding', 0.7, 0))
        return ev

    def render(self):
        silent = self.out + '.video.mp4'
        wr = fx.SilentWriter(silent)
        for i, src in enumerate(frames(self.video)):
            wr.write(self.frame(i / FPS, src, i + 1))
            if i % 90 == 0:
                print('frame', i, flush=True)
        wr.close()
        wav = self.out + '.sfx.wav'
        fx.mix_track(self.sfx_events(), self.dur, wav)
        fx.finish(silent, self.video, wav, self.out)
        os.remove(silent); os.remove(wav)
        d = probe(self.out)[0]
        sheet = contact_sheet(self.out, [d * k / 6 for k in range(1, 6)], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        for t in times:
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg')
            self.frame(t, still(self.video, t), int(round(t * FPS)) + 1, safe=True).save(p, quality=88); print(p)


if __name__ == '__main__':
    r = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        r.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        r.render()
