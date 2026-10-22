# Explainer Craft Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catch motion and timing problems before any render, give the Animator real review sheets, and add paper
texture, a brush wipe, stroke boil, a closing transition and craft doctrine to the explainer.

**Architecture:**
- **Checks:** both new checks reuse the page seek of `stills.mjs`. E6 samples the page; E4 reads the new
  `moments["items"]` the composer writes.
- **Look:** each look addition is a small module beside its neighbours: `paper.py`, `transitions.brush`, a boil filter
  in `scenes/__init__.py`, the close in `explainer-compose.py`.
- **Doctrine:** goes to MOTION.md, PLAYBOOK and the director agent, and the docs tests see it.

**Tech Stack:** Python 3 stdlib (unittest, zlib, struct), Node + puppeteer-core (already used by `stills.mjs`),
GSAP 3, HyperFrames 0.8.171 for the test render only.

**Spec:** `docs/superpowers/specs/2026-10-22-explainer-craft-pass-design.md`

## Global Constraints

**Process**
- Explainer scripts live in `Editing-Workflow/explainer/skill/explainer/scripts`. Tests:
  `python3 -m unittest discover -s tests -t .` (source `scratchpad/env.sh` first for the browser tests).
- TDD; commit only on a green explainer suite. Commits end with the two attribution lines. No model ids in repo files.

**Look rules that must hold**
- Seek-safe: every new motion is a GSAP tween or set on `tl` with `immediateRender:false`, or ambient.
- No `Math.random`; seeds are fixed.
- No overshoot eases (MOTION.md §2.4).

**Thresholds**
- E6 on the page: 10 fps at 180x320 grey; FAIL a still stretch over 1.0 s or more than 15% still.
- E4 read floor:
  - FAIL a number on screen under 1.0 s before its exit;
  - FAIL the last item landing under 1.5 s before the end;
  - WARN two items in one scene, outside one stagger group, landing under 0.6 s apart.
- Paper texture: a 540x960 tile, darkening ≤ 6% against `base`.
- Brush wipe:
  - bands: five, `random.Random(1000 + k)`, -0.1 rad, staggers `[0, .14, .06, .18, .1]`;
  - motion: cover with power3.in over the exit, uncover 0.3 s with expo.out.
- Boil: scale 2.5 px, seed steps at 12 fps, ambient; never on text; `data-boil="off"` disables it.
- Close: 0.4 s, ending exactly at D, onto the hook's ground.

## Review Focus

1. A reel whose last scene is a giant-caption or a comment-cta (no `.cam` push): the close still ends at D, and E5's
   last handover stays clean (`test_the_last_scene_leaves`, Task 5).
2. A stagger of 6 items 0.1 s apart is one read, not five warnings (`test_a_stagger_is_one_read`, Task 2).
3. Boil on a line-art scene in the latte look: off by default; on only in paper (`test_boil_only_in_paper`, Task 6).
4. `review.py --follow` on an element that is hidden for part of its life: it skips the hidden frames, never crashes
   (`test_follow_skips_hidden_frames`, Task 3).
5. Paper texture against the `blue` and `ink` grounds: only the `base` ground carries it (`test_texture_only_on_base`,
   Task 4).

---

### Task 1: E6 on the page

**Files:**
- Modify:
  - `scripts/stills.mjs`: a job may carry `size: [w, h]` and `gray: true` (screenshots resized in the page with a
    canvas, saved as PNG); `data-boil="off"` is set on `<html>` when `job.boil === false`
  - `scripts/motion-check.py`: the `--index` mode
- Test: `tests/test_motion.py`

**Interfaces:**
- **Produces:** `motion-check.py --index public/index.html [--fps 10] [--max-still 1.0] [--max-share 0.15]`, with the same
  output lines as `--video` (`E6 PASS|FAIL: ...`) and exit 0 or 1. `frames_from_page(index, fps) -> list[bytes]`, grey
  frames at 180x320.

- [ ] **Step 1: Write the failing tests:**
  - `test_a_frozen_page_fails`: compose BOARD with a scene that holds still for 1.5 s (a `title` with no items, out at
    +2 s), run `--index`, check FAIL and that the stretch is named.
  - `test_a_living_page_passes`: the normal BOARD passes.
  - `test_boil_is_off_while_measuring`: the job written for the page has `"boil": false`.
  - All three skip without Chrome.
- [ ] **Step 2: Run, and see them fail. Implement it:**
  - `--index` writes a stills job of `t = k/fps` shots with `size` and `gray`;
  - it reads the PNGs back as bytes, through zlib (no PIL; write a small PNG reader for 8-bit grey, `png_gray()`);
  - then the existing `still_runs()`.
- [ ] **Step 3: Run the suite: green. Commit** (`E6 on the page: motion checked before any render`).

### Task 2: The read floor (E4)

**Files:**
- Modify: `scripts/explainer-compose.py`, writing `moments["items"]` beside the existing `item_times`
  (`[{scene, t, text, group, number}]`): `group` is the stagger group id when the item is part of one, `number` is true
  for stat, count-up, price-sticker, number and the hero figure.
- Modify: `scripts/pace-check.py`, with the three rules from the Global Constraints.
- Modify: `MOTION.md` §2 (the read rule).
- Test: `tests/test_pace.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_items_are_in_moments`: a composed BOARD's moments carry items with scene, t and text.
  - `test_a_number_needs_a_second`: a hand-written moments file where a count-up lands 0.8 s before its scene's out →
    FAIL naming the scene.
  - `test_the_last_read_needs_time`: the last item lands 1.2 s before the end → FAIL.
  - `test_two_reads_at_once_warn`: two items 0.4 s apart, different groups → WARN.
  - `test_a_stagger_is_one_read`: six items 0.1 s apart in one group → no WARN.
  - `test_the_existing_cases_still_pass`: every BOARD in `test_compose` still passes E4.
- [ ] **Step 2: Run, and see them fail. Implement it. Run the suite** (the scene cases pass E4; if a library scene's
  own timing breaks the number rule, fix the scene, not the rule, and add a ruling). **Commit**
  (`E4: one read at a time, and time for the last one`).

### Task 3: `review.py`

**Files:**
- Create: `scripts/review.py`
- Modify: `scripts/stills.mjs` (`clip` and `follow` per shot; `follow` crops around the element's
  `getBoundingClientRect()` padded 40 px, skipping a frame where it is hidden or zero-sized)
- Test: `tests/test_review.py`

**Interfaces:**
- **Produces:**
  - `review.py --index public/index.html --out snaps/review --cuts | --scene ID [--step 0.12] | --items | --crop [x,y,w,h] | --follow SEL`;
  - sheets as PNGs with a time label per cell, laid out in the page by a small HTML sheet (`sheet.html` written next
    to the cells; screenshot);
  - a printed list of files and the ms per frame.

- [ ] **Step 1: Write the failing tests** (Chrome needed; skipped without it):
  - `test_cuts_strip_has_25_cells_per_handover`: the cut at -0.3 to +0.5 s at 1/30 s gives 25 cells per handover.
    BOARD has 2 handovers, so 2 files.
  - `test_scene_sheet_steps`: `--scene n1 --step 0.5` gives `ceil(dur/0.5)` cells.
  - `test_items_rows`: 3 frames per item.
  - `test_crop_is_exact`: `--crop 100,200,300,400` gives a 300x400 PNG (read its size with the kit's `imagesize`).
  - `test_follow_skips_hidden_frames`: following an element hidden for half its life gives fewer frames, and no
    traceback.
- [ ] **Step 2: Run, and see them fail. Implement. Add to `agents/explainer-animator.md` "Done when"** (a sheet per
  scene, a strip per cut, a crop per hero). **Run the suite. Commit** (`review.py: strips, sheets and crops for the Animator`).

### Task 4: Paper texture

**Files:**
- Create: `scripts/paper.py` (`texture(path, seed=7, darkest=0.06) -> path`, a 540x960 RGBA PNG: blotches and fibres,
  in a fixed-seed LCG, as in ClaudeAnimationBase `core.js` `makePaper`, credited)
- Modify: `explainer-compose.py` (in `paper`, the `.bg` of the `base` ground gets
  `background-image:url(assets/paper.png); background-size:1080px 1920px`)
- Test: `tests/test_paper.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_same_bytes_every_time`
  - `test_darkening_is_at_most_six_percent`: decode the PNG; the minimum alpha-weighted luminance stays ≥ 94% of
    `base`.
  - `test_texture_only_on_base`: in a paper reel with blue and ink scenes, only the base `.bg` has the image.
  - `test_latte_has_none`
  - `test_layout_cases_stay_clean`: rely on the existing `test_every_scene_case_is_clean_on_paper`.
- [ ] **Step 2: Run, and see them fail. Implement. Run the suite. Commit** (`paper: a seeded paper texture for the paper look`).

### Task 5: The brush wipe, and the close

**Files:**
- Modify: `scripts/transitions.py` (`"brush"` in KINDS; `brush(k, t, colors, exit_dur) -> (html, js)`; `pick()`
  returns `brush` for a new ground in the paper look)
- Modify: `explainer-compose.py` (wire `brush` like `burst`; the close: when the last scene's `t_out == D`, it exits
  over the last 0.4 s onto the hook's ground, with `wipe_bg` to that ground)
- Modify: `sound.py` (`brush` gets a whoosh, like the moving transitions)
- Test: `tests/test_transitions.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_brush_bands_are_seeded_and_on_the_tx_layer`: 5 `<path class="tx-brush">` inside `.tx-layer`; the same
    path data on a re-compose; the staggers as in the Global Constraints.
  - `test_brush_covers_then_uncovers`: a cover tween ending at the cut with power3.in, then an uncover of 0.3 s with
    expo.out.
  - `test_paper_picks_brush_on_a_new_ground`
  - `test_brush_has_a_whoosh`
  - `test_the_last_scene_leaves`: the last host has an exit tween ending at D; the ground at D is the hook's; with a
    giant-caption last scene too.
  - `test_e5_handover_clean_with_brush` (Chrome)
- [ ] **Step 2: Run, and see them fail. Implement. Run the suite. Commit** (`brush wipe and a closing transition`).

### Task 6: Boil on strokes

**Files:**
- Modify: `scripts/scenes/__init__.py` (`Ctx.boil(selector_ids) -> html`: one shared `<filter id="sid-boil">` with
  feTurbulence plus feDisplacementMap at scale 2.5, and ambient `tl.set` seed steps at 12 fps over the scene's life,
  using `film_look.grain_seed`)
- Modify: `thread.py`, `scenes/_annotate.py` and `scenes/line_art.py`: their stroked SVG elements get
  `filter="url(#…-boil)"` when the look's boil is on
- Modify: `tokens.json` (`looks.paper.motion.boil = true`; the base has `false`)
- Modify: `explainer-compose.py` (CSS `html[data-boil="off"] [filter*="boil"] { filter:none }`)
- Test: `tests/test_boil.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_strokes_boil_text_never`: in paper, line-art paths and annotate circles carry the filter; no element with
    text, and no `<text>`, carries it.
  - `test_boil_only_in_paper`
  - `test_boil_steps_are_ambient`: moments spans are unchanged with boil on or off.
  - `test_boil_off_switch`: the CSS rule is present.
  - `test_thread_boils`
- [ ] **Step 2: Run, and see them fail. Implement. Run the suite** (the layout cases in paper stay clean). **Commit**
  (`boil: hand-drawn strokes in the paper look`).

### Task 7: Craft doctrine and the docs

**Files:**
- Modify:
  - `MOTION.md` §2 and §4: lead the eye; cause then reaction; a transition for a reason (a new place: wipe or brush;
    the same idea: fade; a jolt: whip); the ending rhymes with the hook; avoid twinning; into, between and out of;
  - `PLAYBOOK.md` §E6.6 (the push-in sentence corrected) and §E6.7 (transitions include `brush` and the close);
  - `agents/explainer-director.md` (choose transitions for a reason; plan the rhyme);
  - `SKILL.md` (Checkpoint B mentions the review sheets; E6 runs on the page);
  - `RESEARCH.md` Credits (ClaudeAnimationBase, MIT: what we took, and what we did not: Clawd, "no text", p5.brush,
    overshoot);
  - READMEs (the test counts and the new tools).
- Test: `tests/test_docs.py`
  - `test_craft_doctrine_is_written`: MOTION.md has "lead the eye", "cause, then reaction", "rhymes with the hook",
    "into, between and out of";
  - `test_the_push_in_contradiction_is_gone`: PLAYBOOK has no "No scene pushes in on its own";
  - `test_cited_scripts_exist`: covers `review.py` and `paper.py`.

- [ ] **Step 1: Write the failing docs tests. Step 2: Make the doc changes. Run every suite. Commit and push**
  (`doctrine: lead the eye, transitions with a reason, the close; credits`).

### Task 8: The demo, the review, the finish

- [ ] **Step 1:** Rebuild demo3 (paper), then run E4, E5 and E6 on the page, and `review.py --cuts`. Look at the
  strips; render 2 layer clips for the hand-off check only if a layer changed.
- [ ] **Step 2:** The final whole-branch review on the most capable model, then one fix pass test-first, then every
  suite and a push.
- [ ] **Step 3:** Send the creator the review strips of the demo and the final report.
