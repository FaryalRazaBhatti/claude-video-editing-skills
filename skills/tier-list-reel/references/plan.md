# plan.json for tier-list-reel

Times are seconds on the original clip; paths are relative to the plan file.

| Key | Required | Meaning |
| --- | --- | --- |
| `video` | yes | The clip |
| `masks` | no | Cutout folder (default `masks`) |
| `out` | no | Output file (default `out.mp4`) |
| `accent` | no | Brand colour hex (default `#5840DC`) |
| `speed` | no | Playback speed (default `1.0`) |
| `board` | yes | `{"title", "tag"?, "tiers"?, "in"?}`: tiers default to `["S","A","B","C","D","F"]`; `in` is when the board appears (default 0.4) |
| `items` | yes | One per ranked item: `{"tier", "name", "t_name", "t_tier", "t_out", "line"}` |
| `cta` | no | `{"in", "headline", "prompt"}`: closing card; `prompt` types into a comment box |

Items are listed in the order they are spoken. Several items can share a tier; chips sit side by side
in that row and shrink if the row fills up.

## Example

```json
{
  "video": "raw.mp4",
  "accent": "#AE5F42",
  "board": {"title": "Marketing channels 2026", "tag": "B2C edition"},
  "items": [
    {"tier": "F", "name": "Buying followers", "t_name": 4.45, "t_tier": 5.30, "t_out": 9.25,
     "line": "Fake followers don't buy. They kill your reach."},
    {"tier": "A", "name": "Email", "t_name": 27.95, "t_tier": 29.00, "t_out": 33.20,
     "line": "You own the list. No algorithm decides who sees it."},
    {"tier": "S", "name": "SEO + AI search", "t_name": 45.15, "t_tier": 46.30, "t_out": 53.50,
     "line": "If ChatGPT can't find you, you're invisible."}
  ],
  "cta": {"in": 53.9, "headline": "That's my list. What would you move?", "prompt": "Tell me in the comments"}
}
```
