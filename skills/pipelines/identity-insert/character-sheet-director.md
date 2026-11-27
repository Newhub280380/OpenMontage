# Character Sheet Director — Identity Insert

The sheet is the identity anchor. Video models receive the portrait and both turnaround plates when the prompt says `@name`.

## Shape

- 1 to 16 photo ids. Do not drop extras and do not invent ids.
- Three plates: portrait (`face`), body (`front`, `full_body`, `back`), face sheet (both three-quarter views and both profiles).
- Eight views total. `rendered` stays false in this planner. A later image tool may draw the plates only after this gate is approved, and only under its own quote.
- Alias is `@` plus a lowercase handle, for example `@driver`.

## Approval

Show the view list and which photo id feeds each view. Wait for approval. Set the plan gate `sheet` through `identity_middle_layer` action `approve`.

Reject a sheet that beautifies age or changes a project rule in `rules`. Those rules are copied into the preserve block.

Do not start frame insertion, and do not call an image provider, before `sheet.approved` is true.
