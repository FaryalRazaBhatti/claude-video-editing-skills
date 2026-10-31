"""Cut the person out of every frame.

Usage:  python segment.py VIDEO MASK_DIR [STEP]

STEP 2 cuts every 2nd frame only (half the time); fx.subject_mask blends the frames in between.

Writes MASK_DIR/00001.png ... (540x960 greyscale, white = person). Resumable: frames
already done are skipped, so it can be re-run after an interruption. About 1-2 frames
per second on a laptop CPU; start it in the background while you plan the edit.
"""
import sys, os
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reelkit.video import frames  # noqa: E402

MODEL = os.path.expanduser('~/.cache/reelkit/models/u2net_human_seg.onnx')
MEAN, STD = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])


def session():
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = os.cpu_count() or 2
    return ort.InferenceSession(MODEL, opts, providers=['CPUExecutionProvider'])


def mask(sess, img):
    """Person mask for one RGB frame, same size as the frame."""
    x = np.asarray(img.resize((320, 320), Image.LANCZOS), np.float32)
    x = x / max(x.max(), 1e-6)
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    pred = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    pred = (pred - pred.min()) / max(pred.max() - pred.min(), 1e-6)
    return Image.fromarray((pred * 255).astype(np.uint8)).resize(img.size, Image.LANCZOS)


def main(video, out_dir, step=1):
    os.makedirs(out_dir, exist_ok=True)
    sess = session()
    for i, frame in enumerate(frames(video, (540, 960)), start=1):
        path = os.path.join(out_dir, f'{i:05d}.png')
        if (i - 1) % step or os.path.exists(path):
            continue
        mask(sess, frame).save(path + '.tmp.png')
        os.replace(path + '.tmp.png', path)  # never leave a half-written mask behind
        if i % 50 == 0:
            print('frames', i, flush=True)
    print('done', i, flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1)
