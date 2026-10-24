---
name: prompt-cards-reel
description: Edits a vertical talking-head clip into a "you write this, you get this" reel. AI prompt cards type out and tuck behind the speaker's head, and result cards pop up in front, timed to their words. Use when someone attaches a talking-head video and asks for prompt cards, depth UI cards, a "write this get this" reel, or types /prompt-cards-reel.
---

# Prompt cards reel

Raw talking-head clip in, finished reel out. Each time the speaker says "write this", a chat-style
**You write** card types out just above their head, with its bottom edge tucked behind their hair.
When they say "get this", a **You get** result card pops up in front of their chest. Optional extras:
a hook pill at the start and a Follow card at the end.

`SK` below means this skill's folder (the one holding this SKILL.md).

## 1. Setup (first run downloads about 370 MB)

Run `python3 SK/scripts/reelkit/setup.py`. It checks ffmpeg, makes a private Python environment
and downloads two models (speech-to-text and person cutout). Use the `PYTHON=` path it prints for
every command below (written `$PY`). If it prints NOT READY, give the user the fix from the STATUS
line and stop.

## 2. Project folder

Make a working folder, copy the user's clip into it as `raw.mp4`, and never edit the original.
Any aspect ratio works: everything is fitted to a 1080x1920 portrait canvas.

## 3. Start the cutout in the background, then transcribe

```
$PY SK/scripts/reelkit/segment.py raw.mp4 masks        # background: ~1-2 frames/second, resumable
$PY SK/scripts/reelkit/transcribe.py raw.mp4 transcript.json
```

The transcript gives phrases with start and end times, an estimated time for every word, and
`bursts` (short sound islands, roughly one word each). The speech model is small and mishears
some words. Fix them from context ("I should write" in a "write this / get this" script is
"if you write this"), and ask the user when a word matters and you're unsure.

## 4. Plan the edit

Ask only what you can't work out. Usually that's:
- **What each prompt and result should say.** If the user hasn't said, offer to write them for
  their niche, and show the list before rendering.
- **Brand colour.** A hex code, or a page or screenshot to take it from. Default `#5840DC`.

Then write `plan.json` in the project folder (full format in `references/plan.md`):
- `prompt_in` about 0.2 s before the word "this" in "write this", so typing starts as they say it.
- `result_in` about 0.05 s before "this" in "get this".
- `out` about 0.4 s before the next "write this" (or before the outro).
- A hook pill only if the opening line works as a headline. A Follow card from the outro line.
- Keep prompts under about 70 characters (two lines) and result items under about 32 characters.
- Result kinds: `checklist` (numbered items), `chips` (tags plus an optional quote), `steps`
  (a row of ticked labels, e.g. days), `bars` (labels with values).
- `speed`: 1.0 by default. Use 0.95 if the user says it feels rushed.

## 5. Preview, look, fix

Once the masks for those moments exist, render stills and look at every one before the full run:

```
$PY SK/scripts/render.py plan.json --preview 1.5 3.9 6.1
```

Check that no card covers the face or mouth, no text is cut off or overflows its card, and the
prompt card's bottom edge tucks behind the hair (that overlap is the depth effect). Cards are
placed from the measured head position. If the head sits unusually high or low, say so.

## 6. Render and deliver

```
$PY SK/scripts/render.py plan.json
```

This writes the video and a `_check.jpg` contact sheet. Look at the sheet, then send the video
with one line on what's in it. Render time depends on the machine; longer clips take proportionally longer.

## Filming tips to pass on when asked

Tripod, a plain wall with about 30 cm between the speaker and anything behind them, a hand's width
of space above the head, and a short pause between lines.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
