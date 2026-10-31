"""Finishing tools shared by the newer formats: a gentle grade that keeps the real room, subject masks,
camera moves, safe zones, synthesized sound effects and the final audio mix.

No extra packages: numpy + Pillow only.
"""
import os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 30
SR = 48000

# Strictest common safe area for YouTube Shorts, Instagram Reels and TikTok on 1080x1920:
# 260 px top, 480 px bottom (captions, names, audio), 108 px left, 140 px right (like/comment rail).
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 108, 940, 260, 1440


def draw_safe(img):
    """Outline the safe area (for preview stills only)."""
    from PIL import ImageDraw
    ImageDraw.Draw(img).rectangle([SAFE_L, SAFE_T, SAFE_R, SAFE_B], outline=(0, 200, 255), width=4)
    return img


# ---------------- masks ----------------
def _load(mask_dir, n):
    p = os.path.join(mask_dir, f'{n:05d}.png')
    return np.asarray(Image.open(p).convert('L'), np.float32) if os.path.exists(p) else None


def subject_mask(mask_dir, n, size=(540, 960)):
    """Soft subject mask for frame n (1-based). Missing frames blend their neighbours, so masks can be
    made for every 2nd frame to halve the cutout time. Returns None when there are no masks."""
    if not mask_dir or not os.path.isdir(mask_dir):
        return None
    m = _load(mask_dir, n)
    if m is None:
        a = b = None
        for k in range(1, 8):
            a = a if a is not None else _load(mask_dir, n - k)
            b = b if b is not None else _load(mask_dir, n + k)
            if a is not None and b is not None:
                break
        m = a if b is None else (b if a is None else (a + b) / 2)
    if m is None:
        return None
    img = Image.fromarray(m.clip(0, 255).astype(np.uint8)).resize(size, Image.BILINEAR)
    img = img.point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 1.25)))
    return img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.4))


# ---------------- grade ----------------
_cache = {}


def grade(frame, mask=None, face=(540, 900, 430), blur=5.0, warm_side='left'):
    """Keep the real room. One colour correction for the whole frame (cleaner whites, gentle contrast,
    lifted shadows), a light background blur that never bleeds the person into it, a soft key on the
    face, a faint warm practical glow and a mild vignette. Without a mask, only the colour work runs."""
    w, h = frame.size
    key = (w, h, face, warm_side)
    if key not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        fx_, fy_, fr = face
        kl = np.exp(-(((xx - fx_) / (fr * 0.9)) ** 2 + ((yy - fy_) / fr) ** 2)).astype(np.float32)
        vg = (1 - 0.2 * np.clip((((xx - w / 2) / (w * 0.75)) ** 2 + ((yy - h * 0.46) / (h * 0.65)) ** 2), 0, 1) ** 1.5).astype(np.float32)
        gx = 0 if warm_side == 'left' else w
        gl = (np.exp(-(((xx - gx) ** 2 + (yy - h * 0.38) ** 2) / (520 ** 2)))[..., None]
              * np.array([1.0, 0.62, 0.36], np.float32) * 0.07).astype(np.float32)
        _cache[key] = (kl, vg, gl)
    kl, vg, gl = _cache[key]
    f = np.asarray(frame, np.float32) * (1 / 255.0)
    f = f * np.array([0.985, 1.0, 1.045], np.float32)
    f = f + np.float32(0.03) * (1 - f) ** 3
    f = np.float32(0.5) + (f - np.float32(0.5)) * np.float32(1.06)
    lum = f.mean(2, keepdims=True)
    f = (lum + (f - lum) * np.float32(1.06)).clip(0, 1)
    if mask is None:
        out = f * (1 + np.float32(0.04) * kl[..., None]) * vg[..., None]
        return Image.fromarray((out.clip(0, 1) * 255).astype(np.uint8))
    m = np.asarray(mask.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)), np.float32) * (1 / 255.0)
    # background blur at half size, weighted so the person never smears into it
    hw, hh = w // 2, h // 2
    fimg = Image.fromarray((f * 255).astype(np.uint8)).resize((hw, hh), Image.BILINEAR)
    wgt = (1 - np.asarray(mask.resize((hw, hh), Image.BILINEAR), np.float32) / 255.0).clip(0.02, 1)
    pre = (np.asarray(fimg, np.float32) * wgt[..., None]).clip(0, 255).astype(np.uint8)
    r = blur / 2
    num = np.asarray(Image.fromarray(pre).filter(ImageFilter.GaussianBlur(r)), np.float32)
    den = np.asarray(Image.fromarray((wgt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)[..., None] / 255.0
    bgs = (num / np.maximum(den, 0.02)).clip(0, 255).astype(np.uint8)
    bg = np.asarray(Image.fromarray(bgs).resize((w, h), Image.BILINEAR), np.float32) * (1 / 255.0)
    bg = bg * np.float32(0.94) + gl
    s = f * (1 + np.float32(0.06) * kl[..., None])
    m3 = m[..., None]
    out = (s * m3 + bg * (1 - m3)) * vg[..., None]
    return Image.fromarray((out.clip(0, 1) * 255).astype(np.uint8))


def center_shift(img, dx):
    """Move the shot sideways by dx px (positive = left) so the person is centred. The exposed edge is a
    soft mirror; it sits under the platform buttons, so it is not noticed."""
    dx = int(round(dx))
    if abs(dx) < 4:
        return img
    w, h = img.size
    out = img.copy()
    if dx > 0:
        out.paste(img.crop((dx, 0, w, h)), (0, 0))
        strip = img.crop((w - dx * 2, 0, w - dx, h)).transpose(Image.FLIP_LEFT_RIGHT).filter(ImageFilter.GaussianBlur(10))
        out.paste(strip, (w - dx, 0))
    else:
        d = -dx
        out.paste(img.crop((0, 0, w - d, h)), (d, 0))
        strip = img.crop((d, 0, d * 2, h)).transpose(Image.FLIP_LEFT_RIGHT).filter(ImageFilter.GaussianBlur(10))
        out.paste(strip, (0, 0))
    return out


def camera(img, z, cx=540, cy=900, dx=0, dy=0):
    """Zoom about (cx, cy) by z (>= 1) with an optional shake offset."""
    if abs(z - 1) < 1e-3 and not dx and not dy:
        return img
    w, h = img.size
    cw, ch = w / z, h / z
    x0 = min(max(cx - cw * (cx / w), 0), w - cw) + dx / z
    y0 = min(max(cy - ch * (cy / h), 0), h - ch) + dy / z
    return img.transform((w, h), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)


# ---------------- sound effects (synthesized, no samples needed) ----------------
def _env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def _noise(n, seed=0):
    return np.random.RandomState(seed).randn(n).astype(np.float32)


def _band(x, lo, hi):
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(X, len(x)).astype(np.float32)


def sfx(kind, seed=0):
    """boom, whoosh, swish, pop, tick, key, enter, ding, riser, shutter, sparkle."""
    if kind == 'boom':
        n = int(0.9 * SR); t = np.arange(n) / SR
        f = 32 + 48 * np.exp(-t * 9)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
        return (x + 0.35 * _band(_noise(n, seed), 40, 400) * np.exp(-t * 14)) * 0.9
    if kind == 'whoosh':
        n = int(0.42 * SR); t = np.arange(n) / SR
        x = _noise(n, seed)
        p = t / t[-1]
        y = (_band(x, 300, 1500) * (1 - p) + _band(x, 1500, 6000) * p) * np.sin(np.pi * p) ** 2
        return y / (np.abs(y).max() + 1e-6) * 0.55
    if kind == 'swish':
        n = int(0.18 * SR); t = np.arange(n) / SR
        y = _band(_noise(n, seed), 1200, 7000) * np.sin(np.pi * t / t[-1]) ** 2
        return y / (np.abs(y).max() + 1e-6) * 0.32
    if kind == 'pop':
        n = int(0.12 * SR); t = np.arange(n) / SR
        f = 260 + 700 * np.exp(-t * 60)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.035) * 0.6
    if kind == 'tick':
        n = int(0.05 * SR)
        return _band(_noise(n, seed), 2500, 9000) * _env(n, 0.0005, 0.008) * 0.6
    if kind == 'key':
        n = int(0.07 * SR); t = np.arange(n) / SR
        r = np.random.RandomState(seed)
        click = _band(_noise(n, seed), 1800 + r.rand() * 1500, 8000) * _env(n, 0.0004, 0.006)
        body = np.sin(2 * np.pi * (180 + r.rand() * 80) * t) * _env(n, 0.001, 0.018) * 0.5
        return (click * 0.9 + body) * (0.42 + r.rand() * 0.15)
    if kind == 'enter':
        return sfx('key', seed + 7) * 1.3
    if kind == 'ding':
        n = int(1.0 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 1318 * t) + 0.45 * np.sin(2 * np.pi * 2637 * t) + 0.2 * np.sin(2 * np.pi * 1976 * t)
        return x * _env(n, 0.002, 0.28) * 0.28
    if kind == 'riser':
        n = int(0.9 * SR); t = np.arange(n) / SR
        p = t / t[-1]
        y = _band(_noise(n, seed), 400, 8000) * p ** 2.2 + 0.25 * np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * p ** 2
        return y / (np.abs(y).max() + 1e-6) * 0.35
    if kind == 'shutter':
        n = int(0.12 * SR)
        a = _band(_noise(n, seed), 1000, 8000) * _env(n, 0.0005, 0.01)
        return (a + np.roll(a, int(0.05 * SR)) * 0.7) * 0.5
    if kind == 'sparkle':
        n = int(0.6 * SR); t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-(t - d).clip(0) * 9) * (t >= d)
                for f, d in [(2093, 0), (2637, 0.05), (3136, 0.1), (4186, 0.15)])
        return x * 0.07
    raise ValueError(kind)


def mix_track(events, total, out_wav):
    """events: [(time_s, kind, gain, seed)] -> stereo wav holding only the sound effects."""
    n = int((total + 1.5) * SR)
    bed = np.zeros(n, np.float32)
    for t, kind, gain, seed in events:
        x = sfx(kind, seed) * gain
        i = int(t * SR)
        if 0 <= i < n:
            j = min(n, i + len(x))
            bed[i:j] += x[:j - i]
    bed = np.tanh(bed * 1.1) * 0.9
    st = (np.stack([bed, bed], 1) * 32767).astype(np.int16)
    with wave.open(out_wav, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(st.tobytes())


def keep_filter(keep):
    """ffmpeg aselect expression that keeps only the given (start, end) source ranges."""
    return '+'.join(f'between(t,{a:.3f},{b:.3f})' for a, b in keep)


def finish(video_silent, speech_src, sfx_wav, out, keep=None, sfx_db=-5, speech=True):
    """Lay the speech (optionally only the `keep` ranges) and the SFX bed under the rendered video,
    with light voice processing and loudness set for social (-14 LUFS)."""
    if speech and speech_src:
        sel = f"aselect='{keep_filter(keep)}',asetpts=N/SR/TB," if keep else ''
        fc = (f"[1:a]{sel}aresample={SR},highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
              f"equalizer=f=3000:t=q:w=1:g=2[sp];[2:a]volume={sfx_db}dB[fx];"
              f"[sp][fx]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        ins = ['-i', video_silent, '-i', speech_src, '-i', sfx_wav]
    else:
        fc = f"[1:a]volume={sfx_db}dB,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        ins = ['-i', video_silent, '-i', sfx_wav]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', fc, '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)


class SilentWriter:
    """Pipe RGB frames to an H.264 file with no audio (audio is added by `finish`)."""

    def __init__(self, path, size=(W, H)):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}',
                                   '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast',
                                   '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)

    def write(self, img):
        self.p.stdin.write(img.convert('RGB').tobytes())

    def close(self):
        self.p.stdin.close(); self.p.wait()
