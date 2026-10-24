"""Drawing helpers shared by every format: fonts, easing, rounded cards, shadows, placement."""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fonts')
SS = 2  # draw at 2x, then downsample, for smooth edges


def font(name, size):
    """name: e.g. 'Inter-Bold', 'InterDisplay-Black', 'Anton', 'Caveat-Bold', 'Playfair-Black'."""
    for ext in ('.otf', '.ttf'):
        p = os.path.join(FONTS, name + ext)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise FileNotFoundError(name)


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x, overshoot=1.6):
    x = min(max(x, 0.0), 1.0)
    return 1 + (overshoot + 1) * (x - 1) ** 3 + overshoot * (x - 1) ** 2


def wrap(text, fnt, max_w):
    d = ImageDraw.Draw(Image.new('L', (4, 4)))
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def text_width(text, fnt):
    return ImageDraw.Draw(Image.new('L', (4, 4))).textlength(text, font=fnt)


def fit_font(name, text, max_w, start, minimum=20):
    """Largest size of `name` (from `start` down) at which `text` fits in max_w."""
    s = start
    while s > minimum and text_width(text, font(name, s)) > max_w:
        s -= 2
    return font(name, s)


def rounded(img, r):
    """Copy of `img` with rounded corners (transparent outside)."""
    m = Image.new('L', (img.width * SS, img.height * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, m.width - 1, m.height - 1], r * SS, fill=255)
    out = img.convert('RGBA')
    a = m.resize(img.size, Image.LANCZOS)
    if img.mode == 'RGBA':
        from PIL import ImageChops
        a = ImageChops.multiply(a, img.getchannel('A'))
    out.putalpha(a)
    return out


def panel(w, h, r, fill, outline=None, stroke=2):
    """A smooth rounded rectangle as an RGBA image."""
    img = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=fill,
                                          outline=outline, width=stroke * SS if outline else 0)
    return img.resize((w, h), Image.LANCZOS)


def with_shadow(img, strength=0.35, blur=24, dy=20, color=(30, 20, 40)):
    """(image with a soft drop shadow, padding). Pass the pair to `place`."""
    pad = blur * 3
    out = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', img.size, color + (255,))
    sh.putalpha(img.getchannel('A').point(lambda v: int(v * strength)))
    out.alpha_composite(sh, (pad, pad + dy))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out, pad


def place(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """Composite `img` centred at (cx, cy) with optional scale, opacity and rotation (degrees)."""
    if alpha <= 0.01:
        return
    if abs(scale - 1) > 0.002:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.01:
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        img = img.copy()
        img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def anim(t, t_in, t_out, dur_in=0.30, dur_out=0.18):
    """Pop-in / fade-out envelope -> (scale, alpha, dy) or None when hidden."""
    if t < t_in or t > t_out + dur_out:
        return None
    if t < t_out:
        p = (t - t_in) / dur_in
        return 0.82 + 0.18 * ease_back(p), ease_out(p * 1.6), 40 * (1 - ease_out(p))
    q = (t - t_out) / dur_out
    return 1 - 0.06 * q, 1 - q, -20 * q


def sparkle(draw, cx, cy, r, color, ss=1):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.32
        pts.append(((cx + rr * math.cos(a)) * ss, (cy + rr * math.sin(a)) * ss))
    draw.polygon(pts, fill=color)


def send_button(draw, cx, cy, r, fill, ss=1):
    draw.ellipse([(cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss], fill=fill)
    a = r * 0.46
    draw.line([(cx * ss, (cy + a) * ss), (cx * ss, (cy - a) * ss)], fill='white', width=max(2, int(r * 0.13)) * ss)
    draw.line([((cx - a * 0.75) * ss, (cy - a * 0.1) * ss), (cx * ss, (cy - a) * ss), ((cx + a * 0.75) * ss, (cy - a * 0.1) * ss)],
              fill='white', width=max(2, int(r * 0.13)) * ss)


def person_layer(frame, mask):
    p = frame.convert('RGBA')
    p.putalpha(mask)
    return p


def ig_glyph(size, gradient=0.0):
    """Generic camera-style social glyph; gradient 0 = white, 1 = full colour gradient."""
    import numpy as np
    k = size * SS
    m = Image.new('L', (k, k), 0)
    d = ImageDraw.Draw(m)
    sw = int(k * 0.085)
    d.rounded_rectangle([sw, sw, k - sw, k - sw], int(k * 0.28), outline=255, width=sw)
    r, c = k * 0.22, k / 2
    d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=sw)
    dr, dx, dy = k * 0.06, k * 0.74, k * 0.26
    d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    yy, xx = np.mgrid[0:size, 0:size] / size
    tt = np.clip(xx * 0.4 + (1 - yy) * 0.6, 0, 1)
    stops = np.array([[254, 218, 117], [250, 126, 30], [214, 41, 118], [150, 47, 191], [79, 91, 213]], float)
    idx = tt * (len(stops) - 1)
    lo = np.floor(idx).astype(int).clip(0, len(stops) - 2)
    fr = (idx - lo)[..., None]
    grad = stops[lo] * (1 - fr) + stops[lo + 1] * fr
    col = grad * gradient + 255 * (1 - gradient)
    img = Image.fromarray(col.clip(0, 255).astype('uint8')).convert('RGBA')
    img.putalpha(m)
    return img
