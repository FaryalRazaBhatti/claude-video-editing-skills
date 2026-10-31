# plan.json for explainer-reel

Times are seconds on the original clip; paths are relative to the plan file. `scripts/plan.py`
writes a draft; fill in `chart`.

| Key | Required | Meaning |
| --- | --- | --- |
| `video` | yes | The raw clip |
| `masks` | no | Cutout folder (background blur, head placement) |
| `out` | no | Output file (default `out.mp4`) |
| `accent` | no | Brand hex (chip, line, bars, divider, CTA) |
| `theme` | no | Panel theme: `dark` or `light` (default `dark`) |
| `head` | no | Head layout from the masks: `center`, `top_typical`, `chin` |
| `center_subject` | no | Centre the speaker (default `true`) |
| `hook_until` | no | Seconds of full-screen hook before the panel drops in (0 = no hook) |
| `lines` | no | Caption lines: `{"words": [[word, time], ...], "end", "hi": [index, ...]}` |
| `chart` | yes | See below |
| `cta` | no | `{"text", "from"}`: a pill at the bottom of the safe zone |

`chart` keys: `label` (chip text, default `TIP`), `title`, `type` (`line`, `bar`, `steps`),
`points` (`[[label, value], ...]`; for `steps` the label is the step text and the value is ignored),
`unit` (e.g. `" min"`, `"%"`), `max` (top of the scale; default 110% of the largest value),
`in` (when drawing starts), `duration` (seconds to draw, default 2.2), `badge` (short text or null),
`badge_at` (default: when drawing ends), `step_times` (for `steps`: when each step appears).

## Example

```json
{
  "video": "raw.mp4",
  "masks": "masks",
  "accent": "#D97757",
  "theme": "dark",
  "hook_until": 2.6,
  "chart": {"label": "TIP", "title": "Edit time per reel", "type": "line", "unit": " min",
            "points": [["Mon", 60], ["Tue", 45], ["Wed", 25], ["Thu", 10]],
            "in": 3.4, "duration": 2.4, "badge": "6x faster"},
  "lines": [{"words": [["Here's", 0.4], ["the", 0.7], ["trick", 0.9]], "end": 1.5, "hi": [2]}]
}
```
