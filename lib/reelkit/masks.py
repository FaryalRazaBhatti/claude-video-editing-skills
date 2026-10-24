"""Read person masks and measure where the head sits, so graphics can be placed around it.

Usage:  python masks.py MASK_DIR    -> prints the head layout as JSON
"""
import sys, os, json, glob
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920


def load(mask_dir, frame_no, blur=1.5):
    """Mask for frame `frame_no` (1-based) at full size. A missing mask means 'no cutout' (all background)."""
    p = os.path.join(mask_dir, f'{frame_no:05d}.png')
    if not os.path.exists(p):
        return Image.new('L', (W, H), 0)
    m = Image.open(p).convert('L').resize((W, H), Image.BILINEAR)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


def head_layout(mask_dir, step=5):
    """Typical head position across the clip, on the 1080x1920 canvas.

    top_typical: usual y of the top of the hair; top_highest: the highest it gets (leaning in)
    left/right/center: horizontal extent of the head; chin: rough bottom of the face.
    """
    files = sorted(glob.glob(os.path.join(mask_dir, '*.png')))[::step]
    tops, lefts, rights = [], [], []
    for f in files:
        m = np.asarray(Image.open(f).convert('L')) > 128
        rows = np.where(m.sum(1) > 6)[0]
        if not len(rows):
            continue
        top = rows[0]
        band = m[top:top + 120]  # first ~240 px of head at full size
        cols = np.where(band.sum(0) > 3)[0]
        if not len(cols):
            continue
        tops.append(top * 2); lefts.append(cols[0] * 2); rights.append(cols[-1] * 2)
    if not tops:
        return None
    top, left, right = np.median(tops), np.median(lefts), np.median(rights)
    return {'top_typical': int(top), 'top_highest': int(np.percentile(tops, 5)), 'left': int(left), 'right': int(right),
            'center': int((left + right) / 2), 'chin': int(top + (right - left) * 1.45), 'frames_measured': len(tops)}


if __name__ == '__main__':
    print(json.dumps(head_layout(sys.argv[1]), indent=1))
