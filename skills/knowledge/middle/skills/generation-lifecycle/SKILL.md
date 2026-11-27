Adapted for OpenMontage. Sales copy and third-party product calls were removed. This file does not authorize a paid provider call.

# Generation lifecycle

Plan the smallest valid request, then stop before a paid call.

1. Infer the modality: image, video, music, or voice.
2. Read `model-cards/catalog.json` and rank video models with `lib.scoring.rank_providers` through `identity_middle_layer`. Do not invent a model that has no card.
3. Read that model's card before writing fields. Use only modes, durations, resolutions, and alias rules the card lists.
4. References are ids in the plan. This step does not upload or read photo bytes.
5. Build a launch card: model, full prompt, settings, catalog estimate, expiry. Record the estimate with `CostTracker`. Wait for sheet approval, then frame approval, then the launch card.
6. An expired card is not refreshed into a running job. A price that no longer matches the card is re-quoted. The planning tool never calls a provider.

A comparison or a prompt-only request does not authorize a paid job.
