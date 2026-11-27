# Intake Director — Identity Insert

## Inputs

Collect three things. Do not read or copy the photo files into the repo.

- `photo_ids`: 1 to 16 string ids
- `video_asset_id`: the reference clip id
- `wish`: one short sentence

Optional: `name` (lowercase handle), `duration_seconds`, `video_mode` (`edit` or `reference`), `rules` (project facts, such as an age description), and a trend query.

## Mode

Call `identity_middle_layer` with `action: plan`.

- `edit` sets field `sourceVideo` and keeps the source frames. Use it when the person must occupy the existing clip.
- `reference` sets field `referenceVideo`. The clip supplies motion and camera only. Say that frame-by-frame identity is not promised.

If the caller did not choose, the planner defaults to edit unless the wish says the motion alone should be repeated.

## Trends

`action: trends` with the wish as `query`. Results are settings and slots. They do not contain the original prompt. When one matches, copy its model, mode, resolution, aspect, and duration onto the plan only if the person agrees. Fill bracket slots. Do not fetch the publisher's sample video.

## Stop

The plan's `render_started` and `generation_performed` are false. Show the mode and the top ranked model. Do not launch.
