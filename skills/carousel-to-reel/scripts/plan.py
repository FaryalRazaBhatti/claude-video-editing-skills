"""Draft plan.json for a carousel-to-reel video from a folder of slide images.

Usage:  python plan.py SLIDES_DIR plan.json [--voice voiceover.mp4] [--duration 2.2]

Slides are taken in name order (1.png, 2.png ... or slide-01.jpg ...). With --voice, the slide
durations are spread evenly over the voiceover; adjust them to match what is said on each slide.
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reelkit.video import probe

EXT = ('.png', '.jpg', '.jpeg', '.webp')


def natural(s):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', s)]


def main():
    sdir, out = sys.argv[1], sys.argv[2]
    voice = sys.argv[sys.argv.index('--voice') + 1] if '--voice' in sys.argv else None
    dur = float(sys.argv[sys.argv.index('--duration') + 1]) if '--duration' in sys.argv else 2.2
    files = sorted([f for f in os.listdir(sdir) if f.lower().endswith(EXT)], key=natural)
    if not files:
        sys.exit('no slide images found in ' + sdir)
    base = os.path.dirname(os.path.abspath(out))
    if voice:
        dur = round(probe(voice)[0] / len(files), 2)
    plan = {
        'out': 'out.mp4',
        'accent': '#D97757',
        'voice': os.path.relpath(voice, base) if voice else None,
        'duration': dur,
        'slides': [{'image': os.path.relpath(os.path.join(sdir, f), base), 'duration': dur} for f in files],
        'hook': None,
        'cta': None,
    }
    json.dump(plan, open(out, 'w'), indent=1)
    print('wrote', out, '|', len(files), 'slides |', dur, 's each')


if __name__ == '__main__':
    main()
