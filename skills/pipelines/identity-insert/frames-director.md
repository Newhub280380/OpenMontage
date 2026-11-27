# Frames Director — Identity Insert

A reference keeps someone recognizable, not identical. When the wish needs this person, build stills first and animate second.

## Stills

The plan lists three frames: `first` at 0, `key` at the midpoint, `last` at the clip end. Each `still` is null until an image-edit tool, under its own approved quote, paints the person into a measured frame from the source.

Show those three roles and wait. Approve gate `frames` only after `sheet.approved` is true.

## Mannequin pass

When `video_mode.mode` is `edit` and `mannequin.applies` is true:

1. Pass 1 replaces the actor with a green full-body motion-capture mannequin. Motion, camera, light, and timing stay.
2. Pass 2 replaces that green suit with `@name`. The original actor is not the target.

When the mode is `reference`, say plainly that the mannequin pass does not run and the frames are not preserved.

Do not animate until `frames.approved` is true.
