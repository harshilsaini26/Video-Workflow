# Explainer craft pass (from ClaudeAnimationBase): design

Date: 2026-10-22. Status: scope chosen by the creator; this file is for their review.

## 1. Intent

**The creator's ask:** keep the explainer's own style (no new "data story" format), and take the improvements found in
JohnHeibel/ClaudeAnimationBase (MIT), in four groups:

1. checks that catch problems before any render;
2. a review tool to look at what the gates only measure;
3. three look additions and a closing transition;
4. craft doctrine.

**Out of scope:**

- the STYLE.md "data storytelling" format;
- the GPU line in preflight;
- anything p5 or p5.brush inside our pages;
- the Clawd character;
- the "no text" rule;
- overshoot eases.

**Success:**

- Every addition is either a tested gate or a tested capability, or it is doctrine that the docs tests can see.
- The existing gates stay green on every scene case, in both looks.
- The editor hand-off carries the new layers.

## 2. Checks before any render

### 2.1 E6 on the page

`motion-check.py --index public/index.html [--fps 10]` samples the composed page at 10 fps and 180x320 in grey, through
the stills tool's page seek (`stills.mjs` gains a `size` option and a sampling mode). It reuses `still_runs()` with the
same thresholds as on a video:

- **FAIL:** a still stretch over 1.0 s, or more than 15% of the reel still.

Two more rules:

- **No boil while measuring:** the page is sampled with `data-boil="off"` on the root, so the boil (§4.3) cannot hide a
  frozen stretch.
- **Where it runs:** the Animator's `build` runs it after E5, as part of gate E6. The `--video` mode stays for the
  opt-in render and `qa-export.py`.

### 2.2 The read floor (gate E4)

The composer writes `moments["items"]`: `[{scene, t, text, group}]` for every item with a `data-at`, where `group` is
the stagger group (items of one stagger share it).

`pace-check.py` adds these rules:

| Rule | Level |
|---|---|
| A number (stat, count-up, price-sticker, number, the hero figure) is on screen less than 1.0 s before its scene exits | FAIL |
| The last item of the reel lands less than 1.5 s before the end | FAIL |
| Two items in one scene, not in one stagger group, land less than 0.6 s apart | WARN ("two reads at once") |

MOTION.md §2 gains the rule: one read at a time; fast actions, slow meanings; give the last read time to land.

## 3. The review tool: `review.py`

**Location:** `scripts/review.py`. It reuses `stills.mjs`, whose job format gains `clip: {x, y, w, h}` and
`follow: "#selector"`. It writes `snaps/review/`.

Every sheet is built in the browser, with each cell labelled by its time.

| Mode | What it shows |
|---|---|
| `--cuts` | for every handover in `moments.json`: cut -0.3 s to cut +0.5 s, every 1/30 s, 8 columns at 216x384 (`cut-NN-<a>-<b>.png`) |
| `--scene ID --step 0.12` | the viewer-timing sheet of one scene, in/out at that step |
| `--items` | for each item: `data-at` -0.1, +0.25 and +0.6 s, one row per item |
| `--crop x,y,w,h` | 1:1 crops at the scene's settled moment; by default, each scene's box and the caption band |
| `--follow '#sid-x'` | a crop that tracks the element's bounding box over its life, 6 frames |

A run prints the ms per frame. Stills (Checkpoint B) are unchanged; the review sheets are the Animator's working
material and go into `snaps/SCENES.md`.

The Animator's "done when" adds:

- one viewer-timing sheet per scene;
- a strip for every cut;
- a crop for every hero (the kinetic hook, a stat, a product-hero), each looked at before Checkpoint B.

## 4. Look

### 4.1 Paper texture (the `paper` look)

`paper.py` writes `assets/paper.png` once per look version, deterministic, using the standard library only (zlib, PNG):

- a 540x960 tile;
- seeded blotches and fibres;
- at most 6% darkening against `base` (so E5's 3:1 contrast holds on every role);
- scaled to the frame as the `.bg` ground's background image.

It is static, so E4 and E6 are unaffected, and it rides in the ground layer of the hand-off. Latte has no texture.

### 4.2 The brush wipe

A new transition kind, `brush`, in `transitions.py`, built like `burst()`:

- five ragged SVG bands, the shape seeded by `random.Random(1000 + k)`, rotated -0.1 rad, staggered
  `[0, .14, .06, .18, .1]` of the cover time;
- the bands cover over the exit (power3.in), the cut happens under full cover, and they uncover over 0.3 s (expo.out);
- colours are the look's accent and ink, on `.tx-layer` (the hand-off's `tx` track);
- a whoosh in the sound bed.

`brush` is offered on a new background in the paper look; the order of the other kinds is unchanged.

### 4.3 Boil (strokes only)

An `feTurbulence` plus `feDisplacementMap` filter (scale 2.5 px), its seed stepped at 12 fps as ambient motion (as in
`film_look.py`), applied to:

- the thread;
- `_annotate` circles and leaders;
- `line-art` strokes.

Never to text or fills; the filter region is each stroke's bounding box. It is on by default in `paper`, off in
`latte`, and switched off for the whole page by `data-boil="off"`.

### 4.4 A closing transition

The last scene now leaves: a 0.4 s close ending exactly at D, onto the hook's ground (`ink` in latte, `base` in
paper), so the loop seams into the hook. E5 checks the last handover like any other.

## 5. Craft doctrine

**MOTION.md §2 and §4, PLAYBOOK §E6, and `agents/explainer-director.md`:**

- lead the eye before an important item (the thread or the camera moves there first);
- cause, then reaction, never on the same frame;
- choose a transition for a reason (a new place: wipe or brush; the same idea continuing: fade; a jolt: whip), not
  mechanically;
- the ending rhymes with the hook;
- avoid twinning (offset staggers);
- "into, between and out of": every scene enters and every scene leaves, including the last.

**The push-in contradiction:** the code pushes every scene in, slowly and linearly (MOTION.md §2.1); PLAYBOOK §E6.6 says
"no scene pushes in on its own". The playbook is corrected to match: a slow push on every scene's camera, never a push
the voice did not ask for on the content.

## 6. Testing (test first)

| Area | Tests |
|---|---|
| `motion-check --index` | a page with a 1.5 s frozen stretch fails; a living page passes; the boil does not count |
| `pace-check` | each new rule has a passing and a failing case; `moments.json` carries the items |
| `review.py` | each mode writes its sheet with the right number of cells; a crop is exactly w x h; `follow` tracks a moving box |
| `paper.py` | the same bytes every time; darkening ≤ 6%; E5 is clean on every paper scene case (the layout test) |
| `brush` | the bands are on `.tx-layer`; the handover is clean in E5; a whoosh is in `sounds` |
| Boil | strokes have the filter, text never does; the steps are ambient (E4 unchanged); `data-boil="off"` removes it |
| Closing | the last scene's exit ends at D; E5 sees the handover |
| Docs | the docs tests see the new rules; the push-in sentence is fixed |
