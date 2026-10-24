---
name: carousel-reel
description: Edits a "type this, for this carousel" talking-head clip into a reel. A chat card top-right shows attached photos and a typed command, the finished carousel cover pops in top-left, and two-line captions run underneath (a handwritten line plus a heavy yellow line), ending on Follow for more. Also makes the carousel covers (moodboard, magazine cover, bold text slide, polaroids) from the user's own photos. Use when someone wants a carousel showcase reel or carousel covers made from their photos, or types /carousel-reel.
---

# Carousel reel

For each "type this" line, a white chat card appears top-right with one or two of the user's photos
attached and a command typing out. On "for this carousel", the finished carousel cover pops in
top-left and a heavy yellow caption drops in under a handwritten "Type this:". With a cutout, both
cards tuck behind the speaker's head. A dimmed "FOLLOW FOR MORE" closes it. Dead air before the
outro can be cut.

`SK` below means this skill's folder.

## 1. Setup

Run `python3 SK/scripts/reelkit/setup.py` and use its `PYTHON=` path (`$PY`). If it prints NOT
READY, pass on the fix and stop.

## 2. Clip, cutout, transcript

Copy the clip into a working folder (never edit the original), then:

```
$PY SK/scripts/reelkit/segment.py raw.mp4 masks         # background, resumable
$PY SK/scripts/reelkit/transcribe.py raw.mp4 transcript.json
```

If the user misspeaks a line ("cut this" for "type this"), caption what they meant and tell them.

## 3. Carousel covers

Each pair needs a cover image. Use the user's own covers if they have them. Otherwise make them
from their photos, or grab stills from their clips:

```
$PY SK/scripts/make_carousel.py --stills raw.mp4 photos 2.0 6.5 12.6
$PY SK/scripts/make_carousel.py covers.json
```

Templates are `moodboard` (six taped photos with handwritten notes), `magazine` (a big masthead
with the person cut out in front), `bold` (big text slide in a brand colour, with the person cut
out), and `polaroids` (three polaroids with captions). Every option is in `references/carousels.md`.
Ask for a brand colour hex for `bold`.

Open each cover and look at it. Cutouts can keep furniture that touches the person (a chair beside
the neck, a shelf by the head). Erase it with `cutout_clear` boxes, then remake. Photos taken
against a plain wall cut out cleanly.

## 4. Plan the reel

Write `plan.json` (`references/plan.md`):
- `type_t`: start of each "type this". `get_t`: start of "for this carousel". `end_t`: just before
  the next line.
- `cmd`: the command shown (keep it under about 20 characters). `thumbs`: one or two photos shown
  as attachments. `carousel`: the cover image.
- `line2`: the yellow caption, usually "FOR THIS CAROUSEL" (match their words, e.g. "FOR THAT
  CAROUSEL"). For an "And lastly" lead-in, set `line1_at`, `line1_early` and `line1`.
- `follow.t`: when they say "Follow for more". Use `cut: [a, b]` to drop a silent gap before it.

## 5. Preview, render, check

```
$PY SK/scripts/render.py plan.json --preview 1.5 2.4 15.3
$PY SK/scripts/render.py plan.json
```

Check that captions don't cover the mouth, the chat card text fits, and covers are readable. Look at
the `_check.jpg` sheet, then send the video. Only use photos the user owns.

---

Part of **Faryal Raza Bhatti Claude Video Editing Skills**, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk).
