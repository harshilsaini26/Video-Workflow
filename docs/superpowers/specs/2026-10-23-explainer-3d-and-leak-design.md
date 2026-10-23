# Explainer 3D box scenes and the light-leak wipe: design

Date: 2026-10-23. Scope chosen by the creator: the box objects (3D bars, the labelled cube, 3D number cards) in CSS 3D,
and the light-leak wipe. Containers, round objects and the balance scale come later.

## How the 3D is drawn

CSS 3D transforms, no WebGL: a floor plane tilted `rotateX(58deg) rotateZ(-40deg)` (orthographic, so a label's place
can be computed), boxes built from three faces (top, front, side) with `transform-style: preserve-3d`. Shading uses
`filter: brightness()` on the faces (top 1.18, side 0.78), so no colour outside the palette appears. Heights grow by
tweening a CSS variable (`--h`) on the timeline: seek-safe like every other scene. Labels are flat HTML placed over the
3D (their positions computed from the same projection), so gate E5 can check them.

## The scenes

- **`bars-3d`**: 2 to 5 bars `{label, value, at, text?}` rising on their words from a tilted floor, labels above the bars,
  an optional `floor` caption written on the floor; colours from the series, the tallest (or `hi`) in the accent fill.
- **`cube`**: a 3x3x3 cube of cubies with labels on its front face (`labels`, default A1 to C3), arriving on `at`, turning
  a quarter on each `turns[{dir: left|right|up|down, at}]` and twisting its top layer on `twist[{dir: left|right, at}]`;
  `highlight{cell, at}` lights one labelled cell.
- **`cards-3d`**: 1 to 4 thick cards `{text, sub?, at}` standing at an angle, each dropping in on its word.

## The light-leak wipe

Transition kind `leak`: a wide, soft streak in the palette's accent and second accent sweeps across the frame over the
cut (screen blend), the old scene exiting under it as in a zoom. Never chosen automatically; named for a reason (a jolt
of energy, a reveal). It rides on the transition layer like the brush and gets a whoosh.

## Checks

Each scene: validation, structure, timing on its words, seek-safe tweens; calibration cases (so the theme tests, the
in-palette check and gate E5 cover every scene case in every look and palette) and measured heights. The leak: its
sweep is centred on the cut, its colours are the palette's, it is never picked automatically, and a whoosh plays.
