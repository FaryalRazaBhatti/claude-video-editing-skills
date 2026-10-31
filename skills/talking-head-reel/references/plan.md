# plan.json for talking-head-reel

Times are seconds on the original clip; paths are relative to the plan file. `scripts/plan.py`
writes a draft with every key filled in.

| Key | Required | Meaning |
| --- | --- | --- |
| `video` | yes | The raw clip (picture and audio) |
| `masks` | no | Cutout folder from `segment.py` (enables background blur and head placement) |
| `out` | no | Output file (default `out.mp4`) |
| `accent` | no | Brand hex for the caption highlight box and CTA pill (default `#D97757`) |
| `cut_dead_air` | no | `true` to drop silences (default `true`) |
| `keep` | no | `[[start, end], ...]` source ranges to keep when cutting dead air |
| `head` | no | Head layout from the masks: `center`, `top_typical`, `chin` (px on 1080x1920) |
| `center_subject` | no | Shift the shot so the head is centred (default `true`) |
| `hook` | no | Show the first line big above the head with a boom (default `true`) |
| `lines` | yes | Caption lines: `{"words": [[word, time], ...], "end": time, "hi": [index, ...]}` |
| `cta` | no | `{"text", "from", "replace_captions"?}`: a pill in the top band from that time |

## Example

```json
{
  "video": "raw.mp4",
  "masks": "masks",
  "accent": "#2F6FEB",
  "cut_dead_air": true,
  "keep": [[0.3, 9.7], [10.5, 24.4]],
  "head": {"center": 590, "top_typical": 620, "chin": 1230},
  "lines": [
    {"words": [["Stop", 0.48], ["scrolling", 0.7]], "end": 1.2, "hi": [1]},
    {"words": [["this", 1.2], ["changes", 1.4], ["everything", 1.8]], "end": 2.4, "hi": [2]}
  ],
  "cta": {"text": "Follow for more", "from": 22.7, "replace_captions": true}
}
```

## Safe zone

All text and graphics stay inside x 108-940, y 260-1440 on the 1080x1920 frame: the strictest
common area across YouTube Shorts, Instagram Reels and TikTok (their top bar, bottom captions and
right-hand buttons sit outside it).
