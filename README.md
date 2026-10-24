# Claude Video Editing Skills

Four skills for Claude that edit a vertical talking-head clip into a reel format. You attach a clip,
type the command, and Claude transcribes it, plans the timing, shows preview stills and renders the
video.

By Faryal Raza Bhatti, [faryalrazabhatti.co.uk](https://www.faryalrazabhatti.co.uk)

| Skill | Command | What it makes |
| --- | --- | --- |
| prompt-cards-reel | `/prompt-cards-reel` | "You write" prompt cards that tuck behind the speaker's head and "You get" result cards in front, timed to the words |
| tier-list-reel | `/tier-list-reel` | A tier board above the head that fills up as items are ranked, with a card per item whose badge flips to the tier letter |
| split-screen-reel | `/split-screen-reel` | A chat panel on top (typed command, before and after clips), face cam below, then an end card |
| carousel-reel | `/carousel-reel` | A "type this / for this carousel" reel, plus carousel cover templates made from your own photos |

## Install

Uploading skills needs a Claude plan that supports skills (Pro, Max, Team or Enterprise at the time of
writing) and code execution turned on.

1. Download a skill zip. Don't unzip it.
   - [prompt-cards-reel.zip](downloads/prompt-cards-reel.zip)
   - [tier-list-reel.zip](downloads/tier-list-reel.zip)
   - [split-screen-reel.zip](downloads/split-screen-reel.zip)
   - [carousel-reel.zip](downloads/carousel-reel.zip)
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

- `skills/`: the four skills (instructions, plan formats, renderers)
- `lib/`: the shared engine (setup, transcription, cutout, drawing, video I/O) and fonts
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
