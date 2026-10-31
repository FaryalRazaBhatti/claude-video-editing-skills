"""Draft plan.json for an explainer reel from the transcript and (optional) cutout masks.

Usage:  python plan.py raw.mp4 transcript.json plan.json [--masks masks]

It groups words into short caption lines and measures where the head sits. Fill in the chart (title,
type, points, unit, badge) and hook_until before rendering, and fix any misheard words.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reelkit import masks as M
from reelkit.video import probe


def group_words(phrases, max_words=3, max_chars=18):
    lines = []
    for ph in phrases:
        cur = []
        for w in ph['words']:
            word = w['word'].strip()
            if not word:
                continue
            if cur and (len(cur) >= max_words or len(' '.join(x[0] for x in cur + [[word]])) > max_chars):
                lines.append(cur); cur = []
            cur.append([word, round(w['start'], 2)])
        if cur:
            lines.append(cur)
    out = []
    for i, ln in enumerate(lines):
        end = lines[i + 1][0][1] if i + 1 < len(lines) else ln[-1][1] + 0.8
        out.append({'words': ln, 'end': round(end, 2), 'hi': [len(ln) - 1] if len(ln[-1][0]) > 3 else []})
    return out


def _unused_keep_ranges(bursts, duration, min_gap=0.45, pad=0.12):
    """Speech islands padded and merged; silences longer than min_gap are dropped."""
    if not bursts:
        return [[0, duration]]
    segs = []
    for s, e in bursts:
        s, e = max(0, s - pad), min(duration, e + pad)
        if segs and s - segs[-1][1] < min_gap:
            segs[-1][1] = e
        else:
            segs.append([s, e])
    return [[round(a, 2), round(b, 2)] for a, b in segs]


def main():
    video, tx_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    mdir = sys.argv[sys.argv.index('--masks') + 1] if '--masks' in sys.argv else None
    tx = json.load(open(tx_path))
    dur, _, _ = probe(video)
    lay = M.head_layout(mdir, step=2) if mdir and os.path.isdir(mdir) else None
    lines = group_words(tx['phrases'])
    first_end = lines[1]['words'][0][1] if len(lines) > 1 else 2.0
    plan = {
        'video': os.path.relpath(video, os.path.dirname(os.path.abspath(out))),
        'masks': os.path.relpath(mdir, os.path.dirname(os.path.abspath(out))) if mdir else None,
        'out': 'out.mp4',
        'accent': '#D97757',
        'theme': 'dark',
        'head': lay,
        'hook_until': round(max(first_end, 1.5), 2),
        'lines': lines,
        'chart': {'label': 'TIP', 'title': 'FILL IN', 'type': 'line', 'unit': '', 'points': [['A', 10], ['B', 20], ['C', 40]],
                  'duration': 2.2, 'badge': None},
        'cta': None,
    }
    json.dump(plan, open(out, 'w'), indent=1)
    print('wrote', out, '|', len(plan['lines']), 'caption lines')
    if lay:
        print('head centre x', lay['center'], 'top', lay['top_typical'], 'chin', lay['chin'])


if __name__ == '__main__':
    main()
