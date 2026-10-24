"""Transcribe a clip into timed phrases.

Usage:  python transcribe.py VIDEO OUT.json

Speech is split on short pauses, and each phrase is transcribed on its own, so every
phrase carries its own start and end time. `bursts` are smaller sound islands (roughly
words or word pairs) for placing an effect on a single word.
"""
import sys, os, json, subprocess, wave
import numpy as np

MODELS = os.path.expanduser('~/.cache/reelkit/models/whisper')


def load_audio(path):
    tmp = path + '.16k.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', '16000', tmp], check=True)
    with wave.open(tmp) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    os.remove(tmp)
    return a


def islands(a, merge_gap, min_len=0.05, drop_db=28):
    """Stretches louder than (95th percentile - drop_db), joined across gaps shorter than merge_gap."""
    hop, win = 160, 320
    e = np.array([np.sqrt((a[i:i + win] ** 2).mean()) for i in range(0, max(1, len(a) - win), hop)])
    db = 20 * np.log10(e + 1e-6)
    on = db > np.percentile(db, 95) - drop_db
    segs, start = [], None
    for i, v in enumerate(on):
        t = i * 0.01
        if v and start is None:
            start = t
        if not v and start is not None:
            segs.append([start, t]); start = None
    if start is not None:
        segs.append([start, len(on) * 0.01])
    merged = []
    for s, e2 in segs:
        if merged and s - merged[-1][1] < merge_gap:
            merged[-1][1] = e2
        else:
            merged.append([s, e2])
    return [[round(s, 2), round(e2, 2)] for s, e2 in merged if e2 - s >= min_len]


def group_phrases(bursts, max_gap=0.18, max_len=3.0):
    """Join word-sized bursts into phrases: a new phrase starts after a pause or once a phrase gets long."""
    phrases = []
    for s, e in bursts:
        if phrases and s - phrases[-1][-1][1] <= max_gap and e - phrases[-1][0][0] <= max_len:
            phrases[-1].append([s, e])
        else:
            phrases.append([[s, e]])
    return phrases


def word_times(text, bursts):
    """Estimated start/end per word: spread the words over the voiced parts in proportion to their length."""
    words = text.split()
    voiced = sum(e - s for s, e in bursts)
    weights = [len(w.strip('.,!?')) + 2 for w in words]
    total = sum(weights) or 1
    out, k, acc = [], 0, 0.0
    spans = [(s, e) for s, e in bursts]
    def at(v):  # map voiced-time offset -> clock time
        for s, e in spans:
            if v <= e - s:
                return s + v
            v -= e - s
        return spans[-1][1]
    for w, wt in zip(words, weights):
        d = voiced * wt / total
        out.append({'word': w, 'start': round(at(acc), 2), 'end': round(at(acc + d), 2)})
        acc += d
    return out


def main(video, out):
    import sherpa_onnx
    a = load_audio(video)
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(MODELS, 'base.en-encoder.int8.onnx'), decoder=os.path.join(MODELS, 'base.en-decoder.int8.onnx'),
        tokens=os.path.join(MODELS, 'base.en-tokens.txt'), language='en', task='transcribe')
    bursts = islands(a, merge_gap=0.06)
    phrases = []
    for group in group_phrases(bursts):
        s, e = group[0][0], group[-1][1]
        if e - s < 0.12:
            continue
        st = rec.create_stream()
        st.accept_waveform(16000, a[int(max(0, s - 0.05) * 16000):int((e + 0.05) * 16000)])
        rec.decode_stream(st)
        text = st.result.text.strip()
        if text and not text.startswith(('[', '(')):
            phrases.append({'start': s, 'end': e, 'text': text, 'words': word_times(text, group)})
    result = {'duration': round(len(a) / 16000, 2), 'phrases': phrases, 'bursts': bursts}
    with open(out, 'w') as f:
        json.dump(result, f, indent=1)
    for p in phrases:
        print(f"{p['start']:6.2f}-{p['end']:6.2f}  {p['text']}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
