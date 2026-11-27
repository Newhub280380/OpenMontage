# EDL Schema (version 1)

`montage/edl.json` is the single source of truth for an edit. The timeline is
the `segments` list played back to back with hard cuts; `audio` tracks are laid
over it by absolute start time. Times are seconds (numbers). Relative paths
resolve against the directory holding the EDL file, so user files outside
`montage/` are referenced as `../clip.mp4`.

## Top Level

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `version` | `1` | required | Schema version. |
| `title` | string | — | Free text for the report. |
| `fps` | number | `30` | Output frame rate; every segment is normalized to it. |
| `fit` | `crop`/`pad`/`blur` | preset default | Default framing for segments without their own `fit`. |
| `segments` | list | required | The picture timeline, in order. |
| `audio` | list | `[]` | Voice, music and effect tracks over the timeline. |
| `captions` | object | — | Caption source and style. |
| `mix` | object | — | Ducking and loudness targets. |

## Segments

Common fields: `id` (unique string, required), `kind` (`video`, `image` or
`color`; default `video`), `fit`, `fade_in`, `fade_out` (seconds, picture and
sound from/to black), `note` (free text: why this shot, prompt used).

- `video`: `src`, `in` (default 0), `out` (default end of source), or
  `duration` instead of `out`. `audio`: `keep` (default) or `mute`. `gain_db`
  adjusts the clip's own sound.
- `image`: `src`, `duration`, `motion`: `none` (default), `zoom-in`,
  `zoom-out`.
- `color`: `duration`, `color` (ffmpeg color name or `#RRGGBB`; default
  black). Use for a beat of rest or an end card; text on cards is not drawn —
  put words in captions.

### Gaps

While planning, a segment may have no `src` and a `generate` block instead,
plus the target `duration`:

```json
{"id": "s3", "kind": "video", "duration": 4,
 "generate": {"type": "video", "model": "<catalog id>", "prompt": "...",
              "aspect": "9:16"}}
```

`generate` is free-form for your own bookkeeping (what to quote and run);
the script only counts it. `validate --plan` accepts gaps and `
sources and lists gaps; plain `validate` and `render` reject them. After
generation, set `src` to the result URL, drop `generate`, run `fetch`.

## Audio Tracks

| Field | Meaning |
| --- | --- |
| `role` | `voice`, `music` or `sfx` (required). |
| `src` | File or ` URL (or a `generate` block while planning). |
| `start` | Timeline second where the track begins (default 0). |
| `in`, `out` | Trim inside the source file. |
| `gain_db` | Level. Defaults: voice 0, sfx −6, music −16. |
| `fade_in`, `fade_out` | Seconds; music `fade_out` ends at the timeline end. |
| `loop` | Music only: repeat a short bed to fill the timeline. |

Everything is cut at the timeline end.

## Captions

```json
"captions": {"src": "captions.srt", "mode": "auto", "language": "rus",
             "style": {"font": "Arial", "size": 0.045, "position": "bottom",
                       "max_chars": 28, "font_file": "fonts/PTSans-Bold.ttf"}}
```

`mode`: `auto` (burn when ffmpeg has libass, else soft track), `burn` (same,
with a warning on fallback), `soft`, `off`. `size` is a fraction of frame
height. `language` is an ISO 639-2 code for the soft track.

## Mix

```json
"mix": {"duck": true, "target_lufs": -14, "true_peak": -1}
```

`duck` lowers music while voice tracks speak (sidechain compression).

## Example

```json
{
  "version": 1,
  "title": "Coffee shop opening, reels",
  "fps": 30,
  "segments": [
    {"id": "hook", "kind": "video", "src": "../raw/IMG_0412.MOV", "in": 3.2, "out": 5.0},
    {"id": "pour", "kind": "video", "src": "assets/3f1c9a0b2d4e_shot.mp4", "in": 0.4, "out": 3.4,
     "audio": "mute", "note": "generated: slow pour, top-down"},
    {"id": "menu", "kind": "image", "src": "../raw/menu.jpg", "duration": 2.0, "motion": "zoom-in"},
    {"id": "team", "kind": "video", "src": "../raw/team.mp4", "in": 10.0, "out": 13.5, "fit": "blur",
     "fade_out": 0.4},
    {"id": "end", "kind": "color", "color": "#101010", "duration": 1.0}
  ],
  "audio": [
    {"role": "voice", "src": "assets/9ab01c33de10_voice.mp3", "start": 0.3},
    {"role": "music", "src": "assets/77d0e1f2a3b4_bed.mp3", "gain_db": -18, "fade_out": 1.5}
  ],
  "captions": {"src": "captions.srt", "mode": "auto", "language": "rus"},
  "mix": {"duck": true, "target_lufs": -14, "true_peak": -1}
}
```

Total: 1.8 + 3.0 + 2.0 + 3.5 + 1.0 = 11.3 s, rounded to whole frames.
