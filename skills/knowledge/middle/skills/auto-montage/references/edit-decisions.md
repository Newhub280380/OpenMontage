# Edit Decisions

How to turn a brief and a pile of material into a timeline that feels cut by
a person. These are defaults; the user's stated style wins.

## Build Beats First

1. State the one thing the viewer should feel or know by the end.
2. Split the length into beats: opening hook, development (one idea per
   beat), payoff, optional call to action or end card.
3. Assign material to beats before trimming. Prefer the user's own footage
   for anything factual (their product, place, people); generate only what is
   missing or impossible to film. One gap = one clear shot, not a mini-story.
4. With a voiceover, the script drives the beats: one beat per sentence or
   clause group, and the picture changes where the idea changes.

## Pacing Budget

- Vertical social (reels, shorts, tiktok): first shot 1–2 s and it must carry
  the hook visually; shots 1.2–3 s; nothing static longer than 3 s without
  motion or new information.
- Landscape explainers and brand films: 2.5–6 s per shot; let hero shots
  breathe.
- Vary lengths. Three equal shots in a row read as a slideshow; a longer shot
  after quick ones gives emphasis.
- Total length within ±5 % of the brief. If material runs short, extend holds
  on strong shots or add a card before adding generations.

## Trimming

- User footage: cut out camera start/stop wobble, focus hunting and the first
  ~0.3 s after a visible cut in the source. Start a shot just before the
  action peaks, end it right after — not after the motion dies.
- Generated clips: models often ease in and out and may drift at the tail.
  Plan gaps 0.5–1 s longer than needed and trim `in` ≥ 0.3 s and the weak
  tail. Check the clip's first and last frames for artifacts, warped hands,
  text garbage or identity drift, and trim past them.
- Speech in user footage: never cut inside a word. Cut in the pause after a
  sentence; leave 0.1–0.2 s of air before the first syllable and after the
  last. When you only know timings roughly, err toward more air.

## Cutting to Sound

- On speech: picture cuts land at sentence or clause boundaries of the
  voiceover, ideally a few frames before the new idea is spoken.
- On music: when the bed has a clear beat, place cuts on beats or bar lines;
  measure the tempo from the track's stated BPM if known, else keep cuts on a
  steady grid (for example every 2 beats at 120 BPM = 1 s). Do not force
  every cut onto the grid when speech says otherwise — speech wins.
- The script applies 30 ms audio fades at every cut, so hard cuts do not
  click. Use `fade_in`/`fade_out` on a segment only for deliberate dips to
  black (opening, ending, a chapter change).

## Holds and Rest

- Hold the payoff shot and the final frame 0.5–1.5 s longer than the pace
  elsewhere; viewers need time to read a product or a face.
- A short `color` card (0.5–1 s) works as a breath between sections or as
  the end card behind captions. Keep cards rare in short social edits.
- Stills (`image`) should almost always move (`zoom-in`/`zoom-out`) and stay
  under 3 s.

## Framing

- Generate in the master aspect so nothing has to be cropped.
- User footage in another aspect: `crop` when the subject is centered and
  survives the crop; `blur` when the whole frame matters (screens, group
  shots, documents); `pad` for clean letterboxing in landscape delivery.
- Check the contact sheet: faces or products cut off by a crop mean `blur`
  or a different trim.

## Consistency

- Keep one color mood per edit; do not mix a warm generated shot between cold
  footage without reason. Say so in the prompt when generating.
- For recurring people or products across generated shots, apply
  `video-identity-consistency` and reuse the same references for every gap.
