"""One-time setup for the reel skills.

Checks ffmpeg, creates a private Python environment, installs the few packages the
renderers need, and downloads the two models (speech-to-text and person cutout).
Safe to run every time: it only repairs what is missing.

Prints STATUS lines, then `PYTHON=<path>` and READY (or NOT READY).
"""
import os, sys, shutil, subprocess, tarfile, urllib.request, platform

HOME = os.path.expanduser('~/.cache/reelkit')
VENV = os.path.join(HOME, 'venv')
MODELS = os.path.join(HOME, 'models')
PACKAGES = ['numpy', 'pillow', 'onnxruntime', 'sherpa-onnx']

CUTOUT_URL = 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx'
WHISPER_URL = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.en.tar.bz2'
WHISPER_FILES = ['base.en-encoder.int8.onnx', 'base.en-decoder.int8.onnx', 'base.en-tokens.txt']

FIXES = {
    'ffmpeg': {'Darwin': 'brew install ffmpeg', 'Linux': 'sudo apt install ffmpeg', 'Windows': 'winget install --id Gyan.FFmpeg -e'},
}


def say(msg):
    print(msg, flush=True)


def venv_python():
    sub = 'Scripts' if os.name == 'nt' else 'bin'
    exe = 'python.exe' if os.name == 'nt' else 'python'
    return os.path.join(VENV, sub, exe)


def packages_ok(py):
    probe = 'import numpy, PIL, onnxruntime, sherpa_onnx'
    return subprocess.run([py, '-c', probe], capture_output=True).returncode == 0


def ensure_python():
    """Prefer a private venv; fall back to the current interpreter if venvs are unavailable."""
    py = venv_python()
    if os.path.exists(py) and packages_ok(py):
        return py
    if not os.path.exists(py):
        r = subprocess.run([sys.executable, '-m', 'venv', VENV], capture_output=True, text=True)
        if r.returncode != 0:
            say('STATUS venv UNAVAILABLE -> installing into the current Python instead')
            py = sys.executable
    if py != sys.executable:
        subprocess.run([py, '-m', 'pip', 'install', '-q', '--upgrade', 'pip'], capture_output=True)
        r = subprocess.run([py, '-m', 'pip', 'install', '-q'] + PACKAGES, capture_output=True, text=True)
    else:
        r = subprocess.run([py, '-m', 'pip', 'install', '-q', '--break-system-packages'] + PACKAGES, capture_output=True, text=True)
        if r.returncode != 0:
            r = subprocess.run([py, '-m', 'pip', 'install', '-q', '--user'] + PACKAGES, capture_output=True, text=True)
    if r.returncode != 0 or not packages_ok(py):
        last = (r.stderr or '').strip().splitlines()
        say('STATUS packages FAILED' + (f' -> {last[-1]}' if last else ''))
        return None
    return py


def download(url, dest):
    tmp = dest + '.part'
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(tmp, 'wb') as f:
            shutil.copyfileobj(r, f, 1 << 20)
    except Exception:
        curl = shutil.which('curl')
        if not curl or subprocess.run([curl, '-fsSL', url, '-o', tmp]).returncode != 0:
            return False
    os.replace(tmp, dest)
    return True


def ensure_models():
    os.makedirs(MODELS, exist_ok=True)
    ok = True
    cut = os.path.join(MODELS, 'u2net_human_seg.onnx')
    if not os.path.exists(cut):
        say('STATUS cutout model downloading (about 170 MB)...')
        ok &= download(CUTOUT_URL, cut)
    say(f"STATUS cutout model {'OK' if os.path.exists(cut) else 'MISSING'}")
    wdir = os.path.join(MODELS, 'whisper')
    if not all(os.path.exists(os.path.join(wdir, f)) for f in WHISPER_FILES):
        os.makedirs(wdir, exist_ok=True)
        say('STATUS speech model downloading (about 200 MB)...')
        tarp = os.path.join(MODELS, 'whisper.tar.bz2')
        if download(WHISPER_URL, tarp):
            with tarfile.open(tarp) as t:
                for m in t.getmembers():
                    name = os.path.basename(m.name)
                    if name in WHISPER_FILES:
                        with t.extractfile(m) as src, open(os.path.join(wdir, name), 'wb') as dst:
                            shutil.copyfileobj(src, dst)
            os.remove(tarp)
    have = all(os.path.exists(os.path.join(wdir, f)) for f in WHISPER_FILES)
    say(f"STATUS speech model {'OK' if have else 'MISSING'}")
    return ok and have and os.path.exists(cut)


def main():
    system = platform.system()
    ready = True
    for tool in ('ffmpeg', 'ffprobe'):
        if shutil.which(tool):
            say(f'STATUS {tool} OK')
        else:
            say(f"STATUS {tool} MISSING -> {FIXES['ffmpeg'].get(system, 'install ffmpeg')}")
            ready = False
    os.makedirs(HOME, exist_ok=True)
    py = ensure_python()
    say(f"STATUS python packages {'OK' if py else 'FAILED'}")
    ready &= bool(py)
    ready &= ensure_models()
    if py:
        say(f'PYTHON={py}')
    say('READY' if ready else 'NOT READY')


if __name__ == '__main__':
    main()
