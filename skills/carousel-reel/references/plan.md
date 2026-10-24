# plan.json for carousel-reel

Times are seconds on the original clip; paths are relative to the plan file.

| Key | Required | Meaning |
| --- | --- | --- |
| `video` | yes | The clip |
| `masks` | no | Cutout folder (default `masks`). Without it, cards sit in front of the speaker |
| `out` | no | Output file (default `out.mp4`) |
| `speed` | no | Playback speed (default `1.0`) |
| `cut` | no | `[a, b]`: drop this stretch of the source (dead air), video and audio |
| `caption_color` | no | Yellow line colour (default `#FFDE3C`) |
| `pairs` | yes | One per "type this / for this carousel" beat (below) |
| `follow` | no | `{"t", "headline"?, "sub"?}`: dimmed closing title from time `t` |

Each pair: `type_t`, `get_t`, `end_t`, `cmd`, `thumbs` (0-2 image paths), `carousel` (image path),
`line1` (default "Type this:"), `line2` (default "FOR THIS CAROUSEL"), and optionally `line1_at` +
`line1_early` for a lead-in shown before `type_t` ("And lastly...").

## Example

```json
{
  "video": "raw.mov",
  "cut": [13.55, 14.70],
  "pairs": [
    {"type_t": 0.83, "get_t": 1.90, "end_t": 3.22, "cmd": "/carouselmoodboard",
     "thumbs": ["photos/a1.png", "photos/b1.png"], "carousel": "c1_moodboard.jpg"},
    {"type_t": 11.09, "get_t": 12.24, "end_t": 13.45, "line1_at": 10.28, "line1_early": "And lastly...",
     "line1": "And lastly, type this:", "cmd": "/carouselpolaroid",
     "thumbs": ["photos/a2.png"], "carousel": "c4_polaroids.jpg"}
  ],
  "follow": {"t": 14.93, "headline": "FOLLOW FOR MORE", "sub": "carousel ideas you can steal"}
}
```
