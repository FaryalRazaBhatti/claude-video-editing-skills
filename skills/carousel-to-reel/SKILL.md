---
name: carousel-to-reel
description: Turns carousel slides (PNG or JPG images) into a vertical reel. Each slide sits on a soft blurred copy of itself with story-style progress bars, a slow push-in and push transitions with depth, plus optional hook and CTA pills, an optional voiceover and sound effects on every transition. Everything stays inside the YouTube Shorts, Instagram Reels and TikTok safe zones. Use when someone uploads carousel slides and wants them as a video or reel, or types /carousel-to-reel.
---

# Carousel to reel

Slides in, reel out. Every slide is shown whole (nothing cropped) on a blurred, darkened copy of
itself, with progress bars along the top, a slow push-in while it is on screen, and a push
transition to the next (the old slide falls back, the new one slides in with a shadow). A whoosh
and tick mark each change. 1080x1920, 30 fps.

`SK` below means this skill's folder.

## 1. Setup

Run `python3 SK/scripts/reelkit/setup.py` and use its `PYTHON=` path (`$PY`). If it prints NOT
READY, pass on the fix and stop. (This skill does not need the speech or cutout models; the
packages are enough.)

## 2. Slides

Put the slide images in a folder named so they sort in order (`slide-01.png`, `slide-02.png`...).
Any aspect ratio works; 4:5 (1080x1350) carousels fit best. If the user sends a PDF carousel, export
each page to PNG first.

## 3. Plan

```
$PY SK/scripts/plan.py slides plan.json                         # 2.2 s per slide
$PY SK/scripts/plan.py slides plan.json --voice voiceover.mp4   # spread over a voiceover
```

Open `plan.json` (`references/plan.md`) and set:
- `hook`: a short line shown over the first slide (or null).
- `cta`: a short line on the last slide, e.g. "Follow for more" (or null).
- `accent`: brand hex for the CTA pill.
- With a voiceover, transcribe it (`$PY SK/scripts/reelkit/transcribe.py voiceover.mp4 t.json`) and set
  each slide's `duration` so the slide changes when they start talking about it.
- Text-heavy slides need more time: about 1 second per 8 words, at least 1.8 s.

## 4. Preview, render, check

```
$PY SK/scripts/render.py plan.json --preview 0.6 2.4 6.0
$PY SK/scripts/render.py plan.json
```

The stills show the safe area as a blue box; the slide, pills and progress bars must sit inside it.
Look at the `_check.jpg` sheet before sending.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
