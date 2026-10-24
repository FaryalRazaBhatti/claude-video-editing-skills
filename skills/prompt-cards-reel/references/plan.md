# plan.json for prompt-cards-reel

All times are in seconds on the original clip. Paths are relative to the plan file.

| Key | Required | Meaning |
| --- | --- | --- |
| `video` | yes | The clip, e.g. `raw.mp4` |
| `masks` | no | Cutout folder from segment.py (default `masks`). Without it, cards still render but nothing tucks behind the head |
| `out` | no | Output file (default `out.mp4`) |
| `accent` | no | Brand colour as hex (default `#5840DC`) |
| `speed` | no | Playback speed, e.g. `0.95` (default `1.0`) |
| `hook` | no | `{"text", "in", "out"}`: a pill above the head for the opening line |
| `pairs` | yes | One entry per "write this / get this" beat (below) |
| `follow` | no | `{"in", "title", "subtitle", "button_at"}`: a Follow card; the button flips to "Following" at `button_at` |

Each pair:

| Key | Meaning |
| --- | --- |
| `prompt` | Text that types out in the You write card |
| `prompt_in` | When the prompt card appears and starts typing |
| `type_secs` | Optional typing duration (default 0.6) |
| `result_in` | When the result card pops in |
| `out` | When both cards leave |
| `result` | `{"kind", "title", "items", ...}` with kind `checklist`, `chips` (+ optional `quote`), `steps` or `bars` (items are `[label, value]`, optional `unit`, default `%`) |

## Example

```json
{
  "video": "raw.mp4",
  "accent": "#AE5F42",
  "hook": {"text": "No one's gonna tell you this", "in": 1.1, "out": 2.3},
  "pairs": [
    {"prompt": "Audit my landing page like a CRO expert. Give me the top 3 leaks.",
     "prompt_in": 2.75, "result_in": 3.85, "out": 4.40,
     "result": {"kind": "checklist", "title": "3 conversion leaks found",
                "items": ["Headline hides the outcome", "CTA sits below the fold", "No proof near the form"]}},
    {"prompt": "Write 5 ad hooks, one for each buyer emotion.",
     "prompt_in": 4.80, "result_in": 6.05, "out": 6.58,
     "result": {"kind": "chips", "title": "5 hooks, ready to test",
                "items": ["Fear", "Status", "Ease", "Savings", "Curiosity"],
                "quote": "“Still paying for leads that never pick up?”"}},
    {"prompt": "Rank my customers' objections from these 50 reviews.",
     "prompt_in": 9.30, "result_in": 10.55, "out": 11.55,
     "result": {"kind": "bars", "title": "Top objections, ranked",
                "items": [["Price", 42], ["Setup time", 27], ["Support", 18]]}}
  ],
  "follow": {"in": 11.7, "title": "More AI prompts", "subtitle": "that do the work for you", "button_at": 12.45}
}
```
