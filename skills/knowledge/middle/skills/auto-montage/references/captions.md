# Captions

Captions are timed text over the finished timeline. The render burns them in
as the very last picture step, so they sit above every segment, fade and
reframe.

## Sources

The script reads an `.srt` file named in `captions.src`. Where it comes from:

1. **the planner voiceover — word timings.** A finished voiceover generation lists
   each spoken word with its start and end (`words` on the voiceover asset).
   Save the generation JSON (CLI `--json`, or the MCP status result) and build
   the captions from it; cues break on sentence ends, pauses and line width:

   ```bash
   python3 <skill>/scripts/montage.py srt --words montage/voice.json \
     --start <voice track start> --out montage/captions.srt --json
   ```

   If the result has no `words`, fall back to proportional timing from the
   script you wrote (`montage/script.txt`):

   ```bash
   python3 <skill>/scripts/montage.py srt --text montage/script.txt \
     --audio montage/assets/<voice file> --start <voice track start> \
     --out montage/captions.srt --json
   ```

   Proportional timing spreads chunks by text length, drifts inside long
   sentences and is right at sentence boundaries; `--lead-in`/`--tail` cover
   silence at the head or end of the voice file.
2. **User-supplied SRT.** Use it as is; check the times are timeline times,
   not source-clip times. Shift them by the segment start if needed.
3. **Speech in user footage.** Optional: if a local speech-to-text tool such
   as whisper is installed, transcribe the trimmed segment audio to SRT and
   offset by the segment start. Otherwise skip captions for that part or ask
   the user for the text.

Always proofread names, brand spelling and numbers against the brief.

## Chunking

- Vertical: 1–2 lines, ~20–28 characters per line; one short clause per cue.
- Landscape: up to 2 lines, ~38–42 characters per line.
- Break at punctuation or between phrases, never between a preposition and
  its noun or inside a name.
- Minimum on screen ~0.8 s; aim for ≤ 17 characters per second of reading.
- The script wraps long cues to `style.max_chars` and keeps at most 3 lines.

## Placement and Safe Zones

The render converts SRT to an ASS script in real frame pixels. Margins come
from the preset safe zone so text avoids platform UI:

| Preset | Bottom clear | Side clear (left / right) |
| --- | --- | --- |
| reels | 22 % | 7 % / 14 % |
| shorts | 20 % | 7 % / 14 % |
| tiktok | 24 % | 7 % / 16 % |
| square | 12 % | 7 % / 7 % |
| landscape | 10 % | 6 % / 6 % |

The right margin on vertical presets is wider because of the like/comment
rail. `style.position` can be `bottom` (default), `middle` or `top`; use
`middle` for short punchy captions in vertical edits when the bottom third
holds important picture.

## Fonts

Burned captions use libass and a system font by name (`style.font`, default
Arial). For Cyrillic text pick a font with full Cyrillic coverage: Arial,
PT Sans, Noto Sans, Roboto, Inter, Montserrat, Open Sans. To use a font file
that is not installed, set `style.font_file` (path to .ttf/.otf) and the family
name in `style.font`. Missing glyphs show as boxes — check the contact sheet.

## Burned vs Soft

`doctor` reports `captions_burn_supported`; when it is false, doctor's `fix`
already covers it. If captions still cannot be burned (the fix was declined or
has no command), the render attaches them as a soft subtitle track and writes a
sidecar `.srt` next to the output. Most social platforms ignore soft tracks, so
tell the user to upload the `.srt` in the platform's caption field.
