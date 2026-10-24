"""Prompt-cards reel: 'you write this' cards tucked behind the head, 'you get this' result cards in front.

Usage:
  python render.py PLAN.json                 render the full video
  python render.py PLAN.json --preview 2.0 3.9 ...   save preview frames (no video)

The plan format is documented in references/plan.md.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from reelkit import ui
from reelkit.video import frames, still, Encoder, contact_sheet, W, H, FPS
from reelkit import masks as M

INK, MUTED, LINE_BG = (20, 18, 28), (110, 106, 122), (248, 246, 251)
CARD_W = 900
SS = ui.SS


class Theme:
    def __init__(self, accent):
        self.accent = ui.hex_rgb(accent)
        self.soft = ui.mix(self.accent, (255, 255, 255), 0.88)


# ---------- cards ----------
def card_base(w, h, r=40):
    img = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=(255, 255, 255, 255))
    return img, d


def down(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def label(d, x, y, text, color):
    d.text((x * SS, y * SS), text.upper(), font=ui.font('Inter-SemiBold', 22 * SS), fill=color)


_cache = {}


def prompt_card(th, text, n):
    """Chat-style 'You write' card with `n` characters typed."""
    key = ('p', text, n)
    if key in _cache:
        return _cache[key]
    f = ui.font('Inter-Medium', 40 * SS)
    lines = ui.wrap(text, f, (CARD_W - 64 - 130) * SS)
    h = 92 + len(lines) * 54 + 96
    img, d = card_base(CARD_W, h)
    label(d, 40, 34, 'You write', MUTED)
    y, left = 82, n
    for i, ln in enumerate(lines):
        part = ln[:max(0, left)]
        d.text((40 * SS, y * SS), part, font=f, fill=INK)
        typing_here = 0 <= left < len(ln) or (left >= len(ln) and i == len(lines) - 1)
        if typing_here and n < len(text) + 1:
            cx = 40 * SS + d.textlength(part, font=f) + 4 * SS
            d.rectangle([cx, (y + 4) * SS, cx + 4 * SS, (y + 48) * SS], fill=th.accent)
        left -= len(ln) + 1
        y += 54
    bx = CARD_W - 40 - 36
    by = 82 + (len(lines) * 54) // 2
    ui.send_button(d, bx, by, 36, th.accent if n >= len(text) else (210, 206, 222), SS)
    out = down(img)
    if n >= len(text) or n == 0:
        _cache[key] = out
    return out


def header(d, th, title):
    ui.sparkle(d, 52, 52, 16, th.accent, SS)
    label(d, 80, 40, 'You get', th.accent)
    d.text((40 * SS, 82 * SS), title, font=ui.fit_font('Inter-Bold', title, (CARD_W - 80) * SS, 44 * SS), fill=INK)


def result_checklist(th, r):
    items = r['items']
    h = 160 + len(items) * 82 + 24
    img, d = card_base(CARD_W, h)
    header(d, th, r['title'])
    y = 160
    for i, it in enumerate(items):
        d.rounded_rectangle([40 * SS, y * SS, (CARD_W - 40) * SS, (y + 66) * SS], 18 * SS, fill=LINE_BG)
        d.ellipse([60 * SS, (y + 17) * SS, 92 * SS, (y + 49) * SS], fill=th.accent)
        d.text((76 * SS, (y + 33) * SS), str(i + 1), font=ui.font('Inter-Bold', 20 * SS), fill='white', anchor='mm')
        d.text((112 * SS, (y + 33) * SS), it, font=ui.fit_font('Inter-Medium', it, (CARD_W - 170) * SS, 32 * SS), fill=INK, anchor='lm')
        y += 82
    return down(img)


def result_chips(th, r):
    chips, quote = r['items'], r.get('quote', '')
    fc = ui.font('Inter-SemiBold', 28 * SS)
    rows, x, row = [], 40, []
    for c in chips:
        w = ui.text_width(c, fc) / SS + 44
        if x + w > CARD_W - 40 and row:
            rows.append(row); row, x = [], 40
        row.append((c, x, w)); x += w + 12
    rows.append(row)
    fs = ui.font('Inter-Medium', 34 * SS)
    qlines = ui.wrap(quote, fs, (CARD_W - 120) * SS) if quote else []
    h = 160 + len(rows) * 70 + (20 + len(qlines) * 46 + 40 if qlines else 10)
    img, d = card_base(CARD_W, h)
    header(d, th, r['title'])
    y = 160
    for rr in rows:
        for c, cx, w in rr:
            first = c == chips[0]
            d.rounded_rectangle([cx * SS, y * SS, (cx + w) * SS, (y + 56) * SS], 28 * SS, fill=th.accent if first else th.soft)
            d.text(((cx + w / 2) * SS, (y + 28) * SS), c, font=fc, fill='white' if first else th.accent, anchor='mm')
        y += 70
    if qlines:
        y += 14
        d.rounded_rectangle([40 * SS, y * SS, 46 * SS, (y + len(qlines) * 46 - 6) * SS], 3 * SS, fill=th.accent)
        for ln in qlines:
            d.text((66 * SS, y * SS), ln, font=fs, fill=INK); y += 46
    return down(img)


def result_steps(th, r):
    labels = r['items']
    n, gap = len(labels), 12
    cw = (CARD_W - 80 - gap * (n - 1)) / n
    img, d = card_base(CARD_W, 160 + 150 + 30)
    header(d, th, r['title'])
    y = 160
    for i, lab in enumerate(labels):
        x = 40 + i * (cw + gap)
        d.rounded_rectangle([x * SS, y * SS, (x + cw) * SS, (y + 150) * SS], 20 * SS, fill=LINE_BG)
        d.text(((x + cw / 2) * SS, (y + 38) * SS), lab, font=ui.fit_font('Inter-SemiBold', lab, (cw - 10) * SS, 24 * SS), fill=MUTED, anchor='mm')
        cx, cy = x + cw / 2, y + 100
        d.ellipse([(cx - 24) * SS, (cy - 24) * SS, (cx + 24) * SS, (cy + 24) * SS], fill=th.accent)
        d.line([((cx - 10) * SS, cy * SS), ((cx - 3) * SS, (cy + 8) * SS), ((cx + 11) * SS, (cy - 8) * SS)], fill='white', width=5 * SS, joint='curve')
    return down(img)


def result_bars(th, r):
    bars = r['items']  # [[label, value], ...]
    h = 160 + len(bars) * 92 + 20
    img, d = card_base(CARD_W, h)
    header(d, th, r['title'])
    y = 160
    mx = max(v for _, v in bars) or 1
    unit = r.get('unit', '%')
    for name, v in bars:
        d.text((40 * SS, (y + 4) * SS), name, font=ui.font('Inter-Medium', 30 * SS), fill=INK)
        d.text(((CARD_W - 40) * SS, (y + 4) * SS), f'{v}{unit}', font=ui.font('Inter-Bold', 30 * SS), fill=th.accent, anchor='ra')
        d.rounded_rectangle([40 * SS, (y + 50) * SS, (CARD_W - 40) * SS, (y + 68) * SS], 9 * SS, fill=th.soft)
        d.rounded_rectangle([40 * SS, (y + 50) * SS, (40 + (CARD_W - 80) * v / mx) * SS, (y + 68) * SS], 9 * SS, fill=th.accent)
        y += 92
    return down(img)


RESULTS = {'checklist': result_checklist, 'chips': result_chips, 'steps': result_steps, 'bars': result_bars}


def hook_pill(th, text):
    f = ui.fit_font('Inter-Bold', text, (W - 220) * SS, 46 * SS)
    w = int(ui.text_width(text, f) / SS) + 120
    img, d = card_base(w, 104, 52)
    ui.sparkle(d, 50, 52, 16, th.accent, SS)
    d.text((80 * SS, 52 * SS), text, font=f, fill=INK, anchor='lm')
    return down(img)


def follow_card(th, title, subtitle, pressed):
    w, h = 760, 150
    img, d = card_base(w, h, 75)
    d.ellipse([22 * SS, 22 * SS, 128 * SS, 128 * SS], fill=th.accent)
    ui.sparkle(d, 75, 75, 26, (255, 255, 255), SS)
    d.text((150 * SS, 50 * SS), title, font=ui.fit_font('Inter-Bold', title, 360 * SS, 36 * SS), fill=INK, anchor='lm')
    d.text((150 * SS, 98 * SS), subtitle, font=ui.fit_font('Inter-Medium', subtitle, 360 * SS, 28 * SS), fill=MUTED, anchor='lm')
    bw, bx = 190, w - 24 - 190
    if pressed:
        d.rounded_rectangle([bx * SS, 37 * SS, (bx + bw) * SS, 113 * SS], 38 * SS, fill=th.soft)
        d.text(((bx + bw / 2) * SS, 75 * SS), 'Following', font=ui.font('Inter-Bold', 30 * SS), fill=th.accent, anchor='mm')
    else:
        d.rounded_rectangle([bx * SS, 37 * SS, (bx + bw) * SS, 113 * SS], 38 * SS, fill=th.accent)
        d.text(((bx + bw / 2) * SS, 75 * SS), 'Follow', font=ui.font('Inter-Bold', 30 * SS), fill='white', anchor='mm')
    return down(img)


# ---------- layout + frame ----------
class Reel:
    def __init__(self, plan_path):
        self.base = os.path.dirname(os.path.abspath(plan_path))
        self.p = json.load(open(plan_path))
        rel = lambda k, d=None: os.path.join(self.base, self.p.get(k, d)) if self.p.get(k, d) else None
        self.video, self.mask_dir, self.out = rel('video'), rel('masks', 'masks'), rel('out', 'out.mp4')
        self.th = Theme(self.p.get('accent', '#5840DC'))
        lay = M.head_layout(self.mask_dir) or {'top_typical': 560, 'top_highest': 500, 'chin': 1180}
        self.lay = lay
        # prompt cards sit just above the head with their bottom edge tucked behind the hair
        self.prompt_bottom = max(330, lay['top_typical'] + 40)
        self.hook_cy = max(170, lay['top_highest'] - 70)
        self.result_top = min(max(lay['chin'] + 40, 1050), 1250)
        self.shadow = {}
        self.results = [RESULTS[pr['result']['kind']](self.th, pr['result']) for pr in self.p['pairs']]
        self.hook = hook_pill(self.th, self.p['hook']['text']) if self.p.get('hook') else None

    def sh(self, key, img, strength):
        if key is None:
            return ui.with_shadow(img, strength)
        if key not in self.shadow:
            self.shadow[key] = ui.with_shadow(img, strength)
        return self.shadow[key]

    def frame(self, t, src, mask):
        bob = lambda ph: 6 * math.sin(2 * math.pi * 0.55 * t + ph)
        behind = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        front = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        hk = self.p.get('hook')
        if hk:
            a = ui.anim(t, hk['in'], hk['out'])
            if a:
                s, al, dy = a
                img, pad = self.sh('hook', self.hook, 0.35)
                ui.place(behind, img, W / 2, self.hook_cy + dy + bob(0), s, al)
        for k, pr in enumerate(self.p['pairs']):
            a = ui.anim(t, pr['prompt_in'], pr['out'])
            if a:
                s, al, dy = a
                txt = pr['prompt']
                n = int(len(txt) * min(1, max(0, (t - pr['prompt_in'] - 0.08) / pr.get('type_secs', 0.6))))
                card = prompt_card(self.th, txt, n)
                img, pad = self.sh(('p', k) if n >= len(txt) else None, card, 0.35)
                ui.place(behind, img, W / 2, self.prompt_bottom - card.height / 2 + dy + bob(1), s, al, -1.5)
            a = ui.anim(t, pr['result_in'], pr['out'])
            if a:
                s, al, dy = a
                r = self.results[k]
                img, pad = self.sh(('r', k), r, 0.55)
                ui.place(front, img, W / 2 - 15, self.result_top + r.height / 2 + dy + bob(2.5), s, al, 1.5)
        fo = self.p.get('follow')
        if fo:
            a = ui.anim(t, fo['in'], 1e9)
            if a:
                s, al, dy = a
                press = fo.get('button_at', fo['in'] + 0.8)
                pressed = t >= press
                pulse = 1 - 0.06 * math.sin(math.pi * min(1, max(0, (t - press + 0.15) / 0.25))) if press - 0.15 <= t <= press + 0.1 else 1
                card = follow_card(self.th, fo.get('title', 'Follow for more'), fo.get('subtitle', ''), pressed)
                img, pad = self.sh(('f', pressed), card, 0.55)
                ui.place(front, img, W / 2, self.result_top + 60 + dy + bob(2.5), s * pulse, al)
        out = src.convert('RGBA')
        out.alpha_composite(behind)
        out.alpha_composite(ui.person_layer(src, mask))
        out.alpha_composite(front)
        return out.convert('RGB')

    def render(self):
        enc = Encoder(self.out, self.video, speed=self.p.get('speed', 1.0))
        for i, src in enumerate(frames(self.video), start=1):
            enc.write(self.frame((i - 1) / FPS, src, M.load(self.mask_dir, i)))
        enc.close()
        times = [pr['result_in'] + 0.4 for pr in self.p['pairs']][:5]
        sheet = contact_sheet(self.out, [x / self.p.get('speed', 1.0) for x in times], os.path.splitext(self.out)[0] + '_check.jpg')
        print('rendered', self.out, '\ncheck sheet', sheet)

    def preview(self, times):
        outs = []
        for t in times:
            src = still(self.video, t)
            img = self.frame(t, src, M.load(self.mask_dir, int(round(t * FPS)) + 1))
            p = os.path.join(self.base, f'preview_{t:05.2f}.jpg')
            img.save(p, quality=88); outs.append(p)
        print('\n'.join(outs))


if __name__ == '__main__':
    reel = Reel(sys.argv[1])
    if '--preview' in sys.argv:
        reel.preview([float(x) for x in sys.argv[sys.argv.index('--preview') + 1:]])
    else:
        reel.render()
