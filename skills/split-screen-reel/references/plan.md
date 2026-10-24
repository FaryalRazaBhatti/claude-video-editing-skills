# plan.json for split-screen-reel

Times are seconds on the speaker's original clip; paths are relative to the plan file.

| Key | Required | Meaning |
| --- | --- | --- |
| `video` | yes | The speaker's clip (face cam and audio) |
| `masks` | no | Cutout folder, used only to centre the face cam crop (default `masks`) |
| `out` | no | Output file (default `out.mp4`) |
| `theme` | no | `light` or `dark` (default `light`) |
| `accent` | no | Brand hex for the send button, commands and pill (default `#D97757`) |
| `speed` | no | Playback speed, e.g. `0.95` |
| `model_label` | no | Small label inside the chat box (e.g. a model name) |
| `placeholder` | no | Chat box hint before the first command (default "Reply to Claude...") |
| `intro` | no | `{"text", "in"?}`: a line shown in the top panel before the first pair |
| `pairs` | yes | `{"start", "get", "cmd", "before": {"video", "t0", "crop_y"?}, "after": {"video", "t0"}}` |
| `end` | no | End card and logo ending (below) |

`before.crop_y` is the top of a 4:5 crop on the 1080x1920 canvas (default 270). Raise it if the face
sits low.

`end` keys: `in` (hard cut to the end card), `headline`, `headline_font` (e.g. `Playfair-Black` for a
serif, default `InterDisplay-Bold`), `pill`, `sub`, `handle`, `captions` (`[[word, time], ...]`
shown on the inset), `logo_at` (hard cut to the dimmed logo), `total` (video length in source
seconds; the video runs past the speech with silence).

Fonts available: Inter-Regular/Medium/SemiBold/Bold/Black, InterDisplay-SemiBold/Bold/Black, Anton,
Caveat-Bold, Playfair-Black, Playfair-Italic.

## Example

```json
{
  "video": "raw.mp4",
  "theme": "dark",
  "accent": "#AE5F42",
  "speed": 0.95,
  "intro": {"text": "No one's gonna tell you this"},
  "pairs": [
    {"start": 2.36, "get": 3.52, "cmd": "/prompt-cards-reel",
     "before": {"video": "raw.mp4", "t0": 0.9, "crop_y": 250}, "after": {"video": "prompt-cards.mp4", "t0": 3.7}},
    {"start": 4.40, "get": 5.76, "cmd": "/tier-list-reel",
     "before": {"video": "ranking_raw.mp4", "t0": 44.0}, "after": {"video": "tier-list.mp4", "t0": 45.95}}
  ],
  "end": {"in": 11.62, "headline": "Follow for more", "headline_font": "Playfair-Black",
          "pill": "AI reel edits, one command each", "sub": "+ follow for more edits",
          "handle": "@yourhandle", "captions": [["Follow", 11.77], ["for", 12.02], ["more!", 12.16]],
          "logo_at": 13.25, "total": 15.0}
}
```
