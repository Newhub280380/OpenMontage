# Proposal Director — Identity Insert

## Rank the model

The plan's `routing` list is `lib.scoring.rank_providers` over the model cards. Weights stay task fit 30%, quality 20%, control 15%, reliability 15%, cost 10%, speed 5%, continuity 5%.

Copy the top rows into `proposal_packet.production_plan.provider_rankings.video` as `tool_name`, `provider`, and `weighted_score`.

An edit request sets `wants_source_video_edit`. Cards without `source_video_edit` drop. Do not override that ranking silently. A different model needs a new `decision_log` entry with the same subject.

## Cost

Use the launch card's `price_estimate.usd` as `cost_estimate.total_estimated_usd`. It is the OpenMontage Seedance draft figure, or empty when the card has catalog units only. `live_quote` is false. Line item tool is `identity_middle_layer`, operation `draft_video`.

Record the same figure with `CostTracker.estimate`. Do not reserve until the launch stage.

Also check music, even when this clip needs none:

1. `registry.get_by_capability("music_library")`
2. `registry.get_by_capability("music_search")`
3. `registry.get_by_capability("music_generation")`

If there is no score, set `music_source.source_type` to `none`.

## Concepts

Write at least three `concept_options` that differ in treatment, not in the person's identity. Example split: edit the source clip, motion-reference a trend, or a shorter close-up chunk. `narrative_structure` uses the proposal schema enum. Select one only after the person chooses. Leave `approval.status` as `pending` until then.

`delivery_promise.promise_type` is `motion_led` or `source_led`. `motion_required` is true. `approved_fallback` is null. A Ken Burns still is not a substitute.

## Composition runtime

Generated chunks stitch with ffmpeg (`video_stitch`). That does not skip the runtime conversation when titles, captions, or end cards are in scope.

Present both Remotion and HyperFrames before locking `render_runtime`. Check `video_compose.get_info()["render_engines"]`. The engine key for the HTML runtime is `hyperframes`.

- Remotion: best when the overlay reuses the React scene stack. Tradeoff: a face-replacement clip does not need that stack, and adding it can cover the face.
- HyperFrames: best when the overlay is HTML and GSAP type. Tradeoff: it is a second render on top of the generated clip.
- ffmpeg: best when the deliverable is the generated clip itself. Tradeoff: no designed titles.

Recommend one. Log `render_runtime_selection` with every runtime in `options_considered`. A locked `render_runtime` is required once `approval.status` is `approved`.

For a face-only clip with no titles, recommend `ffmpeg` and still list Remotion and HyperFrames as considered options.

## Packet

`production_plan.pipeline` is `identity-insert`. `stages` cover intake through compose. `budget_verdict` compares the draft estimate with the project cap (default $10).
