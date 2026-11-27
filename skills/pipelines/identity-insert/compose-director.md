# Compose Director — Identity Insert

Compose stitches and checks. It does not invent a new performance.

## Draft, then final

- Draft resolution is 480p.
- Split the clip into chunks of about 15 seconds. A tail shorter than 4 seconds merges into the previous chunk.
- Each chunk has its own compiled prompt and, after the launch card, its own provider call under the same approved model.
- Stitch with `video_stitch` in chunk order.
- Final resolution uses `upscale` on that stitched draft. Do not regenerate the motion at 1080p. A second generation drifts the face.

## QA

Action `qa` on the local file runs ffmpeg:

- duration against the plan
- black frames
- frozen frames
- silence
- loudness near -14 LUFS

If ffmpeg is missing, say so and stop. Do not mark QA as run.

Write `render_report` only when a local file exists. `outputs[].path` is that file. If the run stopped at the plan, leave the stage awaiting approval and do not invent an output path.

## Runtime

`render_runtime` is the value locked at proposal. Read it from `proposal_packet.production_plan.render_runtime`.

- `ffmpeg`: `video_stitch` plus the QA probe. This is the path for a face clip with no titles.
- `remotion`: only for an approved overlay, via `video_compose`.
- `hyperframes`: only for an approved HTML overlay, via `video_compose`.

If the locked runtime is unavailable, stop and ask. Do not swap Remotion and HyperFrames. A change requires a new `render_runtime_selection` decision.

A graphic overlay that covers the face fails review. The face stays visible.
