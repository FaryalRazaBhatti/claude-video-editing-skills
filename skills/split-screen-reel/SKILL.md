---
name: split-screen-reel
description: Edits a "write this, get this" talking-head clip into a split-screen reel. A chat panel sits on top, where a command types out, a "before" clip shows on the left and the finished reel pops in on the right. The speaker's face cam runs below, and the reel ends on an end card plus a social logo. Light or dark theme, any brand colour. Use when someone wants to show off commands, prompts or edits with before/after clips, or types /split-screen-reel.
---

# Split-screen reel

The top half is a chat panel (light or dark). Each time the speaker starts a "write this" line, a
command types into the chat box, starting with "/" and running at about 15 characters a second, and a
"before" clip plays in a card on the left. On "get this", the "after" clip fades in on the right over
two frames. Each new pair is a hard cut. The bottom half is the speaker's face cam, cropped around
their head. It ends with a hard cut to an end card (headline, brand-colour pill, a line underneath,
an inset of the speaker with captions), then a dimmed screen with a social logo and their handle.

`SK` below means this skill's folder.

## 1. Setup

Run `python3 SK/scripts/reelkit/setup.py` and use its `PYTHON=` path (written `$PY`). If it prints
NOT READY, pass on the fix and stop.

## 2. Collect the clips

You need:
- **The speaker's clip**: copy it into a working folder as `raw.mp4`.
- **For every pair, a "before" and an "after" clip**: a raw clip and the finished edit made from
  it. Ask the user for these. Finished reels from other skills (prompt-cards-reel,
  tier-list-reel...) work well. Only use clips the user owns or has permission to use; never another
  creator's footage.

Optional but better: run `$PY SK/scripts/reelkit/segment.py raw.mp4 masks` in the background. The
face cam then crops around the head. Without it, a centred crop is used.

## 3. Transcribe and plan

`$PY SK/scripts/reelkit/transcribe.py raw.mp4 transcript.json`, then write `plan.json`
(`references/plan.md` has every key):
- `start`: when the speaker starts each "write this" line.
- `get`: the word "this" in "get this".
- `end.in`: when the outro line starts. `end.captions`: its words with times, from the transcript.
- `end.logo_at`: about 0.8 s after the last word. `end.total`: about 1.7 s after that, so the logo
  has time to settle.
- Ask for: `theme` (light or dark), `accent` (brand hex; read it off their website or a screenshot
  if they point you there), and `handle` (their social handle, shown under the logo).
- `model_label` is optional text inside the chat box, like a model name. Leave it out if unsure.
- `speed` 0.95 if they say the pace feels rushed.

## 4. Preview, render, check

```
$PY SK/scripts/render.py plan.json --preview 1 3.6 12.2 13.8
$PY SK/scripts/render.py plan.json
```

In the stills, check that commands fit in the chat box (keep them under about 24 characters), the
"before" crop shows the speaker's face, and the end card text fits. Look at the `_check.jpg` sheet
before sending the video.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
