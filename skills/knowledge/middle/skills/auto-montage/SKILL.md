Adapted for OpenMontage. Sales copy and third-party product calls were removed. This file does not authorize a paid provider call.

# Assembly and QA

Assemble approved chunks locally. Do not copy a third-party montage script.

1. Probe local files with `ffprobe`. Do not download stand-in videos.
2. Write an edit decision list: user media in order, each missing shot marked as a planned generation with its own launch card.
3. Stitch approved files with `video_stitch`.
4. Run `identity_middle_layer` action `qa`: duration, black frames, frozen frames, silence, loudness near -14 LUFS.
5. One quoted launch card per missing shot. A folder of footage is not a blanket approval to spend.
