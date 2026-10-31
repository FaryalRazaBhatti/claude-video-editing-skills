# Claude Video Editing Skills

Seven skills for Claude that edit vertical video into finished reels. You attach a clip (or carousel
slides), type the command, and Claude transcribes it, plans the timing, shows preview stills and
renders the video.

By Faryal Raza Bhatti, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk)

| Skill | Command | What it makes |
| --- | --- | --- |
| prompt-cards-reel | `/prompt-cards-reel` | "You write" prompt cards that tuck behind the speaker's head and "You get" result cards in front, timed to the words |
| tier-list-reel | `/tier-list-reel` | A tier board above the head that fills up as items are ranked, with a card per item whose badge flips to the tier letter |
| split-screen-reel | `/split-screen-reel` | A chat panel on top (typed command, before and after clips), face cam below, then an end card |
| carousel-reel | `/carousel-reel` | A "type this / for this carousel" reel, plus carousel cover templates made from your own photos |
| talking-head-reel | `/talking-head-reel` | A raw clip edited into a reel: dead air cut, punch zooms, word-by-word captions with a sliding highlight, a big hook line, graded lighting, sound effects |
| explainer-reel | `/explainer-reel` | A tip as a split screen: full-screen hook, then an animated chart (line, bar or steps) with a counter and badge above the face cam |
| carousel-to-reel | `/carousel-to-reel` | Carousel slides turned into a video with story bars, push transitions, optional voiceover and sound effects |

The three newer skills keep every caption and graphic inside the YouTube Shorts, Instagram Reels and
TikTok safe zones, never put text on the speaker's face, keep the real background (lightly blurred)
and add synthesized sound effects, so nothing needs licensing.

## Install

Uploading skills needs a Claude plan that supports skills (Pro, Max, Team or Enterprise at the time of
writing) and code execution turned on.

1. Download a skill zip. Don't unzip it.
   - [prompt-cards-reel.zip](downloads/prompt-cards-reel.zip)
   - [tier-list-reel.zip](downloads/tier-list-reel.zip)
   - [split-screen-reel.zip](downloads/split-screen-reel.zip)
   - [carousel-reel.zip](downloads/carousel-reel.zip)
   - [talking-head-reel.zip](downloads/talking-head-reel.zip)
   - [explainer-reel.zip](downloads/explainer-reel.zip)
   - [carousel-to-reel.zip](downloads/carousel-to-reel.zip)
2. In Claude, open **Settings > Capabilities** and turn on **Code execution and file creation**.
3. In the **Skills** section, click **Upload skill** and choose the zip.
4. In a new chat, attach a clip and type the command, for example `/tier-list-reel`.

On first use, each skill sets up a private Python environment and downloads two models and a few
packages (about 370 MB, from github.com and pypi.org). If your network settings block those sites,
setup reports which download failed.

## What the skills do and don't do

- Everything runs inside your own Claude session. Your clips aren't sent to any third-party service by these skills.
- They need ffmpeg. It is usually available in Claude's environment; if not, setup says how to install it.
- Speech recognition uses a small model and can mishear words. Claude is instructed to correct them from context and check with you.
- Cutting the person out works best against a plain background. Furniture touching the person can be picked up.
- Render time depends on the machine and clip length.
- Only use footage and photos you own or have permission to use.

## Filming tips

Phone on a tripod, plain wall behind you with some space between you and it, a hand's width of space
above your head, and a short pause between lines.

## Repository layout

- `skills/`: the seven skills (instructions, plan formats, renderers)
- `lib/`: the shared engine (setup, transcription, cutout, drawing, video I/O, grade, sound effects, safe zones) and fonts
- `downloads/`: ready-to-upload zips, one per skill
- `build.sh`: copies the engine and fonts into each skill and writes the zips to `dist/`

## Other skills

See [CURATED.md](CURATED.md) for other open-source video skills, linked to their own repositories.

## Licence

MIT for the code in this repository (see [LICENSE](LICENSE)). Fonts are under the SIL Open Font
License. Third-party components are listed in [THIRD_PARTY.md](THIRD_PARTY.md).

## Disclaimer

This is an independent project. It is not affiliated with, endorsed by or sponsored by Anthropic.
Claude is a trademark of Anthropic. Other product names are trademarks of their respective owners
and are used only to describe compatibility. The software is provided as is, without warranty.
