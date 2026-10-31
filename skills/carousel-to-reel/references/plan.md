# plan.json for carousel-to-reel

Paths are relative to the plan file. `scripts/plan.py` writes a draft from a folder of slides.

| Key | Required | Meaning |
| --- | --- | --- |
| `slides` | yes | `[{"image": path, "duration": seconds}, ...]` in order (a bare path also works) |
| `duration` | no | Default seconds per slide (default 2.2) |
| `voice` | no | Voiceover audio or video file; its audio plays under the slides |
| `out` | no | Output file (default `out.mp4`) |
| `accent` | no | Brand hex for the CTA pill (default `#D97757`) |
| `hook` | no | Short line in a dark pill over the first slide |
| `cta` | no | Short line in an accent pill on the last slide |
| `tail` | no | Seconds held on the last slide before the fade (default 0.4) |

## Example

```json
{
  "accent": "#D97757",
  "voice": "voiceover.m4a",
  "hook": "5 tools I use every day",
  "cta": "Follow for more",
  "slides": [
    {"image": "slides/slide-01.png", "duration": 2.4},
    {"image": "slides/slide-02.png", "duration": 3.1},
    {"image": "slides/slide-03.png", "duration": 2.8}
  ]
}
```
