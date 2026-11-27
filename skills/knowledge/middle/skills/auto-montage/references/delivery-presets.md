# Delivery Presets

## Presets

| Preset | Frame | Aspect | Default fit | Use for |
| --- | --- | --- | --- | --- |
| `reels` | 1080×1920 | 9:16 | crop | Instagram Reels, VK Clips |
| `shorts` | 1080×1920 | 9:16 | crop | YouTube Shorts |
| `tiktok` | 1080×1920 | 9:16 | crop | TikTok |
| `square` | 1080×1080 | 1:1 | pad | Feed posts, marketplaces |
| `landscape` | 1920×1080 | 16:9 | pad | YouTube, websites, presentations |

All presets: 30 fps unless the EDL sets `fps`, H.264 yuv420p, AAC 192 kbps
48 kHz, `+faststart`. `--quality draft` renders fast previews;
`--max-height N` shrinks the frame for a quick look.

## Master and Derived

- The **master** is the preset the brief asked for. Generate every gap in the
  master aspect so generated shots are never cropped.
- **Derived** versions are re-rendered from the same EDL with another
  `--preset`, not re-encoded from the master file: each segment is reframed
  from its original source and captions are placed in that preset's safe
  zone. Override the framing with `--fit`, or set `fit` per segment where one
  shot needs different treatment.
- Name outputs `montage/final_<preset>.mp4` (the default). Run `qa` on every
  deliverable.

## Framing Trade-offs

| Fit | What happens | Good for | Watch out |
| --- | --- | --- | --- |
| `crop` | Fills the frame, cuts the overflow | Centered subjects, generated shots in another aspect | Heads, products or text at the edges get cut |
| `pad` | Whole picture with bars | Landscape delivery, screens, documents | Bars waste vertical space; looks lazy in 9:16 |
| `blur` | Whole picture over a blurred, filled copy | Horizontal footage in a vertical edit | Busy backgrounds become mush; costs more render time |

Going 16:9 → 9:16 loses about two thirds of the width with `crop`; prefer
`blur` unless the action is tightly centered. Going 9:16 → 16:9 with `crop`
keeps only a thin band; use `blur` or `pad`.

## Loudness

- Social and web (all presets): integrated −14 LUFS, true peak −1 dBTP. The
  render measures the mix, then normalizes linearly in a second pass.
- Broadcast-style delivery: pass `--lufs -23 --true-peak -1` (EBU R128) or
  `--lufs -24 --true-peak -2` (ATSC A/85) when the user asks.
- Voice is the anchor: music defaults to −16 dB and is ducked under voice.
  If QA reports silence where music should play, raise the music `gain_db`;
  if the voice feels buried, lower it to −20 dB.

QA flags loudness more than 1.5 LU off target as a warning; very short edits
may land slightly off — that is acceptable.
