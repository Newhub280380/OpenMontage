# Launch Director — Identity Insert

Nothing paid runs in this stage. The stage ends with a card the person can accept.

## Card

Show:

- model id and why the scorer ranked it
- the full compiled prompt
- settings: mode, field, 480p, duration, aspect, chunk count
- `price_estimate` in USD when OpenMontage publishes a rate, otherwise catalog units, with `live_quote: false`
- `created_at` and `expires_at` (15 minutes)
- `idempotency_key` for this exact request

## Budget

`CostTracker.estimate` already recorded `identity_middle_layer` / `draft_video`.

On approval, in order:

1. Gate `sheet` is already true.
2. Gate `frames` is already true.
3. Gate `launch` through action `approve`, with `now` if you are testing expiry.
4. The tool calls `approve_tool` and `reserve(..., human_approved=True)`.

`human_approved` only covers the single-action threshold. The budget cap still applies. An over-cap reserve is a refusal, not a cheaper silent model.

If `expires_at` is in the past, the card is dead. Build a new plan. Do not reuse the old key for a changed prompt.

`paid_call_allowed` on this tool stays false. A later provider call is a different tool, chosen from the registry, using the reserved amount as `max` spend. If that tool's live quote is higher, stop and re-quote.
