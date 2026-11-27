# Executive Producer — Identity Insert

Use this pipeline when the request is a person's photos, a reference or trend clip, and a short wish, and the face must not drift. Examples: "put my face in this GTA-style clip as the driver."

Do not use it for a rigged cartoon with no source clip. That is `character-animation`. Do not use it for a talking presenter with no reference video. That is `avatar-spokesperson`.

## Stage order

1. `intake` — photo ids, clip id, wish, mode, optional trend template.
2. `proposal` — concepts, scored model, catalog cost, runtime choice. Human approval.
3. `character_sheet` — eight views, alias `@name`. Human approval.
4. `frames` — first, key, and last stills, plus the mannequin plan when mode is edit. Human approval.
5. `prompt_compile` — preserve, replace, integrate, per the model card.
6. `launch` — model, prompt, settings, estimate, expiry. Human approval. Then `CostTracker.reserve`.
7. `compose` — 480p chunks, stitch, upscale, ffmpeg QA.

## Rules

- Read each stage director before that stage.
- Read `skills/knowledge/middle/README.md` and the model card before writing a prompt.
- `identity_middle_layer` never calls a provider. `render_started` stays false.
- A paid provider tool runs only after the launch card is approved and unexpired, and only for the reserved estimate.
- Review with `skills/meta/reviewer.md`. Identity gates below are critical when they fail.
- Do not commit photo bytes. Plans store ids only.

## Send back

- Sheet has fewer or more than eight views, or the alias is missing.
- Edit and motion-reference were collapsed into one mode.
- Animation was planned before the stills were approved.
- The prompt skips preserve, replace, or integrate, or invents a timecode.
- A paid call was described without a launch card.
