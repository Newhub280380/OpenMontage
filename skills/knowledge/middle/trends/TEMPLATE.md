# Trend template

A trend entry is a settings template: model, mode, resolution, aspect, duration, and bracket slots. The original prompt text is not stored.

When a person asks to repeat a trend, copy the settings onto a launch card and fill the slots. Then compile the prompt in this order:

```
TASK & FORMAT
REFERENCES
ABSOLUTE REPLACEMENT RULES
PRESERVE
REPLACE
INTEGRATE
GLOBAL SETTINGS
TIMELINE
0.00-0.00 measured bounds only
MOTION
CONSTRAINTS
```

Edit-source uses `sourceVideo`. Motion-only uses `referenceVideo`. A stand-in entry (`stand_in: true`) uses the two-pass mannequin plan: actor to a colored suit, then the suit to the approved `@name` sheet.
