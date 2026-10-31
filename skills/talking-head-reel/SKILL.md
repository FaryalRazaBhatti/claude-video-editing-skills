---
name: talking-head-reel
description: Edits a raw vertical talking-head clip into a finished reel. Cuts dead air, punch-zooms on every caption line, adds bold captions with a highlight box that slides word to word and a big hook line with a boom, grades the lighting, lightly blurs the real background, centres the speaker and adds sound effects. Everything stays inside the YouTube Shorts, Instagram Reels and TikTok safe zones. Use when someone uploads a raw talking-head clip and wants it edited, captioned or turned into a reel, or types /talking-head-reel.
---

# Talking-head reel

One raw clip in, one finished reel out: dead air removed, a punch zoom and one bright frame on every
jump cut, captions below the chin (never on the face), the first line as a big hook above the head,
a gentle grade that keeps the real room, and sound effects. 1080x1920, 30 fps, HD.

`SK` below means this skill's folder.

## 1. Setup

Run `python3 SK/scripts/reelkit/setup.py` and use its `PYTHON=` path (written `$PY`). If it prints
NOT READY, pass on the fix and stop.

## 2. Clip, cutout, transcript

Copy the clip into a working folder as `raw.mp4` (never edit the original), then:

```
$PY SK/scripts/reelkit/segment.py raw.mp4 masks 2        # every 2nd frame; run in the background
$PY SK/scripts/reelkit/transcribe.py raw.mp4 transcript.json
```

The cutout lets the background blur without touching the person and tells the renderer where the
head is. It is optional; without it the grade still runs and captions use a default position.

## 3. Plan

```
$PY SK/scripts/plan.py raw.mp4 transcript.json plan.json --masks masks
```

Then open `plan.json` (`references/plan.md` has every key) and:
- Fix misheard words in `lines` (the speech model is small). Keep each line to 1-3 words.
- Set `hi` per line to the word(s) to emphasise (yellow on the hook line).
- Ask for a brand colour and set `accent` (default `#D97757`).
- Set `cta` if they end on a call to action, e.g. `{"text": "Follow for more", "from": 21.4}`.
- `cut_dead_air` is on; `keep` lists the ranges kept. Tighten or loosen them if a cut feels abrupt.

## 4. Preview, render, check

```
$PY SK/scripts/render.py plan.json --preview 0.6 3.0 8.0
$PY SK/scripts/render.py plan.json
```

Preview times are source times. The stills show the safe area as a blue box; every caption and
graphic must sit inside it and never on the face. Look at the `_check.jpg` sheet before sending.
Rendering runs at roughly one to two frames a second, so tell the user it takes a few minutes.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
