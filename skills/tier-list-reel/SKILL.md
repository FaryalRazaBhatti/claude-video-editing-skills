---
name: tier-list-reel
description: Edits a talking-head ranking video into a tier-list reel. A tier board above the speaker's head fills up as each item is named, and a card in front explains the item, its badge flipping from "?" to the tier letter as they say it. Use when someone attaches a video where they rank things (S tier, A tier...), asks for a tier list edit, or types /tier-list-reel.
---

# Tier list reel

Raw ranking video in, finished reel out. A white tier board (S down to F) sits above the speaker's
head, with its bottom edge tucked behind their hair. When they name an item, a card pops up in front
of their chest with the item's name, a one-line summary of what they said, and a "?" badge. When they
say the tier, the badge flips to the letter and the item drops into its row on the board. An optional
comment-prompt card closes it.

`SK` below means this skill's folder (the one holding this SKILL.md).

## 1. Setup

Run `python3 SK/scripts/reelkit/setup.py` and use the `PYTHON=` path it prints (written `$PY`).
The first run downloads about 370 MB of models and packages. If it prints NOT READY, pass on the fix from the STATUS line and stop.

## 2. Project folder, cutout, transcript

Copy the clip into a new working folder as `raw.mp4` (never edit the original). Then:

```
$PY SK/scripts/reelkit/segment.py raw.mp4 masks        # background: ~1-2 frames/second, resumable
$PY SK/scripts/reelkit/transcribe.py raw.mp4 transcript.json
```

Cutting out a one-minute clip can take 10-20 minutes, so start it first and plan while it runs. The
transcript has phrase times, estimated word times and `bursts` (roughly one word each). The speech
model mishears tier letters: "F tier" can come out as "after", "B tier" as "beat here", "A tier" as
"8 here". Read them from context, since rankings usually run in order.

## 3. Plan the edit

Write `plan.json` (full format in `references/plan.md`). For each item:
- `t_name`: when they start naming it. The card appears.
- `t_tier`: when they say the tier letter. The badge flips and the chip drops onto the board.
- `t_out`: just before the next item's `t_name`.
- `line`: one short sentence summarising their point, in their words, under about 60 characters.
  Never add claims they didn't make.

Board `title` comes from their opening line ("Ranking marketing channels for 2026" becomes
"Marketing channels 2026"). The `tag` is optional ("B2C edition"). Use the default tiers S, A, B,
C, D, F unless they use others. Add a `cta` card when they end with a question to the audience.

If they repeat a closing line (two takes), point it out and offer to trim with ffmpeg before
rendering. Ask for a brand colour hex (default `#5840DC`), which is used for the accents.

## 4. Preview, render, check

```
$PY SK/scripts/render.py plan.json --preview 6 30 55     # stills: look at each
$PY SK/scripts/render.py plan.json                       # full video + _check.jpg sheet
```

Check that the board doesn't cover the eyes, chips don't overflow their row, and card text fits. The
board scales itself to the space above the head. If the speaker sits very high in frame, the board
gets small, so suggest reframing next time. Look at the check sheet before sending the video.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
