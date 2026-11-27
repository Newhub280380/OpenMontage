# Prompt Director — Identity Insert

Compile one prompt per chunk. Read the chosen model card in `skills/knowledge/middle/model-cards/` before editing the text.

## Order

The body is:

1. TASK & FORMAT — measured duration, not a guessed one
2. REFERENCES — one role per file
3. ABSOLUTE REPLACEMENT RULES — PRESERVE, then REPLACE, then INTEGRATE
4. GLOBAL SETTINGS — model, mode, field, resolution, prompt language from the card
5. TIMELINE — `0.00` to the chunk end, hundredths of a second
6. MOTION — one performer
7. CONSTRAINTS — identity does not come from the motion clip

## Card rules

- If `aliases` is true, `@Video1` is motion and `@name` is identity.
- If `aliases` is false, name the files in upload order and do not invent `@` tokens.
- If the chunk duration is outside the card's duration list, shorten the chunk. Do not stretch the number.
- Prompt language is the card's `prompt_language` unless the card lists the user's language in `supported_languages` and the wish depends on on-screen text.

## Recovery

If a finished take is not the person, do not add adjectives. Action `recover` with reason `not_like` returns levers: a closer still, a shorter chunk, one person. `rewrote_prompt` stays false.
