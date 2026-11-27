---
name: identity-middle-layer
description: Plan a person into an existing clip. Character sheet, edit versus motion-reference, frame-first stills, mannequin pass, prompt compile, trend templates, and a launch card. Does not call a provider.
---

# Identity middle layer

Read `skills/knowledge/middle/README.md` before planning. The tool `identity_middle_layer` only plans.

1. Character sheet: 1 to 16 photo ids, three plates, eight views, alias `@name`. Approve the sheet before stills.
2. Mode: `edit` writes `sourceVideo` and keeps frames. `reference` writes `referenceVideo` and keeps motion and camera only.
3. Frame-first: stills at first, key, and last. Approve them before animation.
4. Edit mode plans two passes: actor to a green mannequin, then the mannequin to `@name`.
5. Compile preserve, then replace, then integrate. Follow the model card for aliases, language, and duration. Timeline uses measured hundredths of a second.
6. Trends are settings templates. Do not paste a third-party prompt body.
7. Launch card: model, prompt, settings, catalog estimate, 15-minute expiry. Record it with `CostTracker`. No paid call from this tool.
8. Draft is 480p in chunks of about 15 seconds, then `video_stitch`, then `upscale` for the final. QA uses ffmpeg: duration, black frames, frozen frames, silence, loudness near -14 LUFS.
9. If the face is wrong, add a close still, shorten the chunk, or keep one person. Do not only rewrite adjectives.

`render_started` stays false until a configured provider tool is called under an approved, unexpired card.
