---
name: explainer-reel
description: Turns a talking-head tip into a split-screen explainer reel. A full-screen hook with a big caption, then a panel drops in on top with a TIP chip, a title and an animated chart (line, bar or numbered steps) with a rolling counter and a badge, short captions under it, and the speaker's face cam below. Graded lighting, lightly blurred background, centred speaker, sound effects, all inside the YouTube Shorts, Instagram Reels and TikTok safe zones. Use when someone wants a tip, stat or how-to explained with a graph or steps, or types /explainer-reel.
---

# Explainer reel

The first line plays full screen with a big caption and a punch zoom. Then a panel slides down over
the top half: a TIP chip, a title, and a chart that draws itself (a glowing line with a counter
rolling to the final number, growing bars, or numbered steps popping in one by one), with a badge
for the key result. Short captions run under the chart; the face cam sits below. 1080x1920, 30 fps.

`SK` below means this skill's folder.

## 1. Setup

Run `python3 SK/scripts/reelkit/setup.py` and use its `PYTHON=` path (`$PY`). If it prints NOT
READY, pass on the fix and stop.

## 2. Clip, cutout, transcript

Copy the clip into a working folder as `raw.mp4`, then:

```
$PY SK/scripts/reelkit/segment.py raw.mp4 masks 2        # background
$PY SK/scripts/reelkit/transcribe.py raw.mp4 transcript.json
```

## 3. Plan

```
$PY SK/scripts/plan.py raw.mp4 transcript.json plan.json --masks masks
```

Open `plan.json` (`references/plan.md` has every key) and fill in:
- `chart`: `title` (short, from what they say), `type` (`line` for a trend, `bar` for a comparison,
  `steps` for a how-to), `points`, `unit`, `badge` (e.g. "6x faster"), and `in` (when the chart
  starts drawing, usually as they start explaining). Only use numbers the speaker says or the user
  gives you; ask if there are none rather than inventing them.
- `hook_until`: when the panel drops in (end of the hook line).
- Fix misheard words in `lines`; set `hi` for words to colour.
- `accent` (brand hex) and `theme` (`dark` or `light`). Optional `cta`.

## 4. Preview, render, check

```
$PY SK/scripts/render.py plan.json --preview 1.0 4.0 9.0
$PY SK/scripts/render.py plan.json
```

The stills show the safe area as a blue box. Check the title and chart fit, the face is clear of
all text, and look at the `_check.jpg` sheet before sending.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
