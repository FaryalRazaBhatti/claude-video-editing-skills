# covers.json for make_carousel.py

`{"covers": [ {...}, {...} ]}`. Each cover has `template`, `out` (file name) and the keys below.
Image paths are relative to the spec file.

| Template | Size | Keys |
| --- | --- | --- |
| `moodboard` | 1080x1080 | `title`, `photos`: up to 6 `{"img", "note"}`, `swatches`: 4 hex colours (optional) |
| `magazine` | 1080x1350 | `masthead`, `cutout` (photo of the person), `cutout_clear` (optional boxes), `headline`: up to 5 short lines, `list`: up to 5 italic lines, `script`: up to 2 handwritten lines, `top_left`, `top_right`, `accent` (masthead colour), `bg_top`, `bg_bottom` |
| `bold` | 1080x1350 | `bg` (brand hex), `lines`: up to 4 big lines, `button` (pill text), `button_color`, `cutout` (optional), `cutout_clear`, `footer` (default "Swipe →") |
| `polaroids` | 1080x1080 | `title`, `photos`: 3 `{"img", "caption"}`, `footer` |

`cutout_clear` is a list of `[x0, y0, x1, y1]` boxes in the photo's own pixels, erased from the cutout.
Use it when furniture touching the person is kept. Look at the cover, find the stray bit, box it, and
remake.

Keep text short: masthead one word, headline lines up to about 12 characters, bold lines up to about
16 characters.
