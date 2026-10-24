"""Video in and out. Every input is normalised to a 1080x1920 portrait canvas at 30 fps."""
import json, subprocess, os
from PIL import Image

W, H, FPS = 1080, 1920, 30
FILL = f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}'


def probe(path):
    """Duration in seconds, source width and height."""
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height:format=duration', '-of', 'json', path], capture_output=True, text=True).stdout
    j = json.loads(out)
    st = j['streams'][0]
    return float(j['format']['duration']), st['width'], st['height']


def frames(path, size=(W, H)):
    """Yield every frame as an RGB image, normalised to portrait and scaled to `size`."""
    w, h = size
    vf = FILL + (f',scale={w}:{h}' if (w, h) != (W, H) else '')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield Image.frombytes('RGB', (w, h), b)
    p.wait()


def grab(path, t0, dur, size, crop=None):
    """A short run of frames from `t0`, optionally cropped (x, y, w, h on the 1080x1920 canvas) then scaled to `size`."""
    vf = FILL
    if crop:
        vf += ',crop={2}:{3}:{0}:{1}'.format(*crop)
    vf += f',scale={size[0]}:{size[1]}'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{max(0, t0):.3f}', '-i', path, '-t', f'{dur:.3f}', '-vf', vf,
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    n = size[0] * size[1] * 3
    return [Image.frombytes('RGB', size, raw[i * n:(i + 1) * n]) for i in range(len(raw) // n)]


def still(path, t):
    """One frame at time t on the 1080x1920 canvas."""
    got = grab(path, t, 1 / FPS, (W, H))
    return got[0] if got else None


class Encoder:
    """Pipe rendered frames to an H.264 file, carrying the source audio.

    speed:   playback speed (0.95 = 5 percent slower, pitch kept)
    cut:     (a, b) seconds of source to remove from the audio (the renderer skips those frames itself)
    pad:     keep audio running (silence) if the video runs longer than the source
    """

    def __init__(self, out, audio_src, speed=1.0, cut=None, pad=False):
        af = []
        if cut:
            af.append(f"aselect='not(between(t,{cut[0]},{cut[1]}))',asetpts=N/SR/TB")
        if abs(speed - 1) > 1e-3:
            af.append(f'atempo={speed}')
        if pad:
            af.append('apad')
        vf = f'setpts=PTS/{speed},fps={FPS}' if abs(speed - 1) > 1e-3 else 'null'
        fc = f"[0:v]{vf}[v];[1:a]{','.join(af) or 'anull'}[a]"
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                   '-r', str(FPS), '-i', '-', '-i', audio_src, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                                   '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                                   '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', out],
                                  stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def write(self, img):
        self.p.stdin.write(img.convert('RGB').tobytes())

    def close(self):
        self.p.stdin.close()
        err = self.p.stderr.read().decode(errors='ignore')
        self.p.wait()
        # ffmpeg reports a harmless "No space left on device" when -shortest stops an apad stream; ignore that one
        real = [l for l in err.splitlines() if l.strip() and 'No space left on device' not in l]
        if real:
            print('\n'.join(real[-5:]))


def contact_sheet(path, times, out, width=270):
    """Frames at `times` side by side, for a quick visual check."""
    ims = [still(path, t) for t in times]
    ims = [im.resize((width, int(width * 16 / 9))) for im in ims if im]
    sheet = Image.new('RGB', (width * len(ims), int(width * 16 / 9)))
    for i, im in enumerate(ims):
        sheet.paste(im, (i * width, 0))
    sheet.save(out, quality=88)
    return out
