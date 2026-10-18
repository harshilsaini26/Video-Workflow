# Explainer editorial pass (the Bose reference) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the explainer the Bose reel's art direction while staying as animated as it is now:
- an editorial "paper" look;
- a headline layer;
- product images with depth and annotations;
- photo grids;
- one thread that runs through the reel;
- six small scenes;
- captions kept, but smaller and at the bottom, so the centre always belongs to the animation.

**Architecture:**
- A look is a set of token overrides (`tokens.json` → `looks.paper`), chosen per storyboard (`"look": "paper"`). Scenes keep reading colours through `theme()`; text sized in the look's hero face reads its glyph table through `E.hero()`.
- New layers (headline, thread, annotations) are composer features or shared helpers. The new visuals are scene modules found by `scenes.discover()`.
- E6 (`motion-check.py`) is not touched.

**Tech Stack:** Python 3 (stdlib, numpy for E6), HyperFrames 0.8.168, GSAP 3.14.2, puppeteer/Chrome for E5 and the stills, FFmpeg. New fonts come from npm `@fontsource-variable/archivo@5.3.0` (wdth axis) and `@fontsource/instrument-serif@5.3.0`, both OFL.

**Spec:** the user's messages of 2026-10-18 (this plan's Rulings record them), and my Bose analysis: no captions band in the centre, a warm paper ground, near-black ink and one accent, three typefaces, top-left headlines, product cut-outs with depth, annotations, a photo grid with credits, a thread line, and waveform, step chart, line art, price sticker, crossed list and mode switch.

## Rulings (made at planning; the user may redirect)

1. **Captions stay, smaller and at the bottom.**
   - They move from the top band (y 330 to 470, 64 px) to the bottom of the safe area: y 1130 to 1235, 44 px, at most two lines, in the narrow column (150 to 930).
   - The brand band stays at y 281 to 321. "The centre for the animation" means the scene area becomes y 345 to 1105.
   - Text and cards end by 1105. Bare shapes may still run to 1650, behind the captions, which get a halo in the ground's colour.
   - 1235 stays the one bottom line for any text (SOP S7).
2. **E6 is unchanged** (max still 1.0 s, at most 15% still). Every new scene keeps moving while it holds: the waveform scrolls, the thread drifts, photos drift.
3. **The look is chosen per reel.**
   - `latte` stays the default, so existing storyboards render as before. `paper` is the editorial look.
   - The Producer asks for the look at the brief, defaulting to `paper` for product and tech topics.
   - In `paper` the planner puts every scene on one ground (`base`); colour comes from images and the accent.
4. **Three typefaces, by role.**
   - Hero: Archivo at width 125 and weight 800 in `paper`; DM Sans 700 in `latte`. It sets headlines, kinetic, giant captions, title cards, stat figures and price stickers.
   - Aside: Instrument Serif italic, for short asides ("seriously?").
   - Label: JetBrains Mono, as now.
   - Body text inside UI mock-ups stays DM Sans in both looks, so the 236 measured scene heights still hold.
5. **Images are the creator's.** `src` paths are relative to storyboard.json, as `logo-card` already works. Every photo needs a `credit`, shown in a mono chip; a scene with photos and no credit fails E3. The demo uses generated stand-in images, labelled as such.
6. **Depth is allowed only where it is declared.** Text marked `data-depth="behind"` (a product-hero title) may be covered by its own scene's hero image, and E5's cover check skips that pair only. Every other check still applies. That title must be at least 120 px.
7. **The thread** is one SVG path on its own layer, between the backgrounds and the scenes. It morphs between named shapes (`drop`, `loop`, `wave`, `rule`, `underline`, `off`) on words.
   - Every shape is a 96-point polyline in frame coordinates, so any shape morphs into any other.
   - It is decoration for E5 (like the ground) and a moment of change for E4.
8. **The step chart** is a `shape: "step"` option on `line-chart`, not a new scene. The crossed list is a new scene (`crossed-list`), not a `list-cards` option, because its type and motion differ.

## Global Constraints

- Free tools only; 1080x1920 at 60 fps; render with `--video-bitrate 20M`; the Packager writes the CRF 18 upload copy.
- Every text at least 28 px drawn (E5), and at least 3:1 contrast against its ground and the glows (test_theme).
- The hook is whole on screen by 1.0 s; its items land by 0.8 s.
- Exits run in the last 0.2 s before the cut; an item lands by `t_out - 0.5`.
- No overshoot eases (MOTION.md); linear only for counts, draws, drifts and the thread's scroll.
- Seeded randomness only; every render is identical; no `Math.random`, no `Date`.
- UTF-8 on every text open and subprocess. `pathToFileURL` in .mjs files; `shutil.which("npx") or "npx"`.
- TDD. Commit only on a green full explainer suite. Every commit ends with the attribution lines in the session reminder. No model names in repo files.
- Scenes are discovered from `scripts/scenes/*.py`. A new scene has a `dev/cases_e.py` entry and measured rows in `tests/fixtures/heights-e.json`, and passes `test_every_scene_case_is_clean` on every ground of both looks.

## Review Focus

1. A `paper` reel whose storyboard sets `bg: "blue"` or `"ink"` on a scene: its roles must still pass 3:1 (the looks test covers every ground of every look).
2. A headline long enough to need three lines on a tall scene: E3 must say which to shorten, never overlap the scene (`test_a_headline_that_leaves_no_room_fails`).
3. A creator image that is a JPEG with no alpha, or very wide (a 3:1 banner), in `product-hero`: it must fit the area and E5 must pass (`test_any_aspect_fits`).
4. A thread key whose shape crosses the captions band: it is drawn behind the captions, which keep their halo (`test_the_thread_passes_behind_the_captions`).
5. Windows paths in `src` (`assets\\earbuds.png`): resolved like `logo-card` (`test_backslash_src_resolves`).

---

### Task 1: Captions at the bottom; the centre for the scene

**Files:**
- Modify: `scripts/explainer_lib.py` (SCENE, CAPTION_BAND, a new CAPTION_SIZE)
- Modify: `scripts/explainer-compose.py` (CAP_SIZE, CENTRE, WIDE_CENTRE, the caption halo)
- Modify: `scripts/layout_check.py` and `scripts/layout-probe.mjs` (wherever the area is read)
- Modify: the tests that pin 520, 1235 or 330 to 470 (test_foundations Area, test_custom, test_craft and others found by grep)
- Docs: PLAYBOOK §E4 and §E5, MOTION.md, SKILL.md QA brief ("caption slot"), README tables

**Interfaces:**
- Produces:
  - `E.SCENE = {"left": 65, "top": 345, "right": 1015, "bottom": 1105}`;
  - `E.CAPTION_BAND = (1130, 1235)`;
  - `E.CAPTION_SIZE = 44`;
  - `E.TEXT_BOTTOM = 1235`, the one line for any text, captions included;
  - `E.PICTURE_BOTTOM` stays 1650.

- [ ] **Step 1:** Write tests in `tests/test_editorial.py`, class `Layout`:
  - `test_captions_sit_at_the_bottom_small`: compose BOARD; every `.cap` box has top ≥ 1130 and bottom ≤ 1235, CSS `font-size:44px`, and left ≥ 150 and right ≤ 930.
  - `test_the_centre_is_the_scenes`: every scene box sits in y 345 to 1105, and a wide scene centres on (345 + 960) // 2.
  - `test_captions_have_a_halo_in_the_grounds_colour`: the `.cap` text-shadow contains `E.theme(tok, bg)["bg"]` of the scene under it.
- [ ] **Step 2:** Run `python3 -m unittest tests.test_editorial`. Expected: 3 FAIL.
- [ ] **Step 3:** Change the constants and the caption CSS:
  - `font-size:44px`; line-height 52px; the band's `top`/`height` from CAPTION_BAND; the narrow column;
  - `text-shadow: 0 0 18px <bg>, 0 0 6px <bg>`, set per chunk like the colours;
  - `chunk_words(..., 4, 24)` is unchanged.
- [ ] **Step 4:** Run the full suite. Update every test that pinned the old area, one commit with them, and say in each changed comment why (the band moved).
- [ ] **Step 5:** Rebuild demo2. Run `layout-check.py`; expected `E5 PASS`. Look at the stills: the captions are under the scene.
- [ ] **Step 6:** Commit: "Captions small at the bottom (y 1130 to 1235, 44 px); the scene area is y 345 to 1105".

### Task 2: Looks: `paper` beside `latte`

**Files:**
- Modify: `tokens.json` (new `looks.paper`), `scripts/explainer_lib.py` (`load_tokens(path=None, look=None)`, `LOOKS`)
- Modify: `scripts/explainer-compose.py` (reads `S.get("look", "latte")`; fails on an unknown look, naming the known ones)
- Modify: `scripts/plan-storyboard.py` (`--look`; with `paper`, every scene's `bg` is `base`)
- Test: `tests/test_editorial.py`, class `Looks`; extend `tests/test_theme.py` so its contrast tests loop over `E.LOOKS`

**Interfaces:**
- Produces:
  - `E.LOOKS = ("latte", "paper")`;
  - `E.load_tokens(path=None, look=None) -> dict`, where the look's overrides are deep-merged over the base tokens and `tok["look"]` names the look;
  - `theme()` is unchanged.

`looks.paper` overrides the palette under the same 26 names. The values:

| Names | Colour |
|---|---|
| `base` (the paper) | #EFEAE3 |
| `mantle` | #E8E2D9 |
| `crust` | #DDD6CB |
| `text` (ink) | #141414 |
| `subtext1` | #2E2B27 |
| `subtext0` | #4F4A43 |
| `overlay2` | #6B655C |
| `overlay1` | #8A847A |
| `overlay0` | #A59F94 |
| `surface2` | #C4BDB2 |
| `surface1` | #D6CFC4 |
| `surface0` | #E2DBD0 |
| `peach` (the accent) | #D9472E |
| `red` | #C8361F |
| `maroon` | #B4412E |
| `flamingo` | #E07A5F |
| `rosewater` | #E9A28C |
| `yellow` | #C98A12 |
| `green` | #2F7D4F |
| `teal` | #1F6F63 |
| `sky` | #3A86A8 |
| `sapphire` | #2A6F8F |
| `blue` | #1F4FD1 |
| `lavender` | #6C6FB8 |
| `mauve` | #7A4FB0 |
| `pink` | #C2577A |

Further overrides:
- `roles.accent = "peach"`;
- the highlight's fill is `peach` with text `base`;
- glows on `base`: one `crust` at 0.5 and one `base` at 0 (a vignette);
- particles in `overlay0`, `surface2` and `peach` at 0.25;
- `fonts.hero` = `{"family": "Archivo", "stretch": "125%", "weight": 800, "glyphs": "wide800", "spacing": -0.01}`.

In `latte`, `fonts.hero` is `{"family": "DM Sans", "stretch": "100%", "weight": 700, "glyphs": "display700", "spacing": -0.02}`.

- [ ] **Step 1:** Write the tests:
  - `test_paper_overrides_the_palette_by_name`: `load_tokens(look="paper")["palette"]["base"] == "#EFEAE3"` and the theme accent is `#D9472E`.
  - `test_latte_is_the_default`.
  - `test_an_unknown_look_fails_naming_the_known_ones`: compose with `"look": "neon"`; E3 FAIL lists "latte, paper".
  - `test_the_planner_puts_a_paper_reel_on_one_ground`.
  - The existing test_theme contrast and glow tests, parameterised over looks.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement the merge in `load_tokens`: recursive dict merge, where a list replaces a list. Wire the look through compose, the planner, `stills.py` (via moments.json `look`) and `layout-check.py`.
- [ ] **Step 4:** Run the full suite with `test_theme`'s `test_every_colour_on_every_scene_is_latte` generalised to "in its look's palette"; expected OK.
- [ ] **Step 5:** Commit: "Looks: paper (editorial) beside latte".

### Task 3: The three typefaces

**Files:**
- Create: `assets/fonts/Archivo-wdth.woff2`, `assets/fonts/InstrumentSerif-Italic.woff2`, and their `OFL-*.txt`
- Modify: `../../reels/skill/reels/scripts/dev/measure-glyphs.mjs` (measures `wide800` at `font-stretch:125%` weight 800, and `serif400i`) and `glyphs.json`
- Modify: `scripts/explainer-compose.py` (FONT_FILES per look; `@font-face` for Archivo with `font-stretch: 62% 125%` and Instrument Serif italic)
- Modify: `scripts/explainer_lib.py`: `hero()` and `use_look(tok)`
- Test: `tests/test_editorial.py`, class `Fonts`

**Interfaces:**
- Produces:
  - `E.use_look(tok) -> None`, called by the composer once, before any `place()`;
  - `E.hero() -> {"family", "stretch", "weight", "glyphs", "spacing", "css"}`, where `css` is a ready `font-family:...;font-stretch:...;font-weight:...;letter-spacing:...` string;
  - glyph tables `"wide800"` and `"serif400i"` in reels `glyphs.json`.

- [ ] **Step 1:** Write the tests:
  - `test_the_fonts_ship_with_their_licences`: the files exist, each OFL text names the font.
  - `test_glyph_tables_cover_ascii`: every printable ASCII character is in `wide800` and `serif400i`.
  - `test_wide_is_wider_than_dm_sans`: `text_width("WIRED", 100, "wide800") > text_width("WIRED", 100, "display700") * 1.15`.
  - `test_paper_pages_load_the_fonts`: a paper page has `@font-face` for Archivo and Instrument Serif and preloads both.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Fetch the fonts:
  - Run `npm pack` on both packages in a scratch dir. Copy `files/archivo-latin-wdth-normal.woff2` (or the package's wdth file) and `files/instrument-serif-latin-400-italic.woff2`, plus each LICENSE.
  - If the Archivo package has no wdth file, use `@fontsource/archivo-black` at 400 instead and name the table `wide800` anyway. Record that as a ruling.
  - Measure with the dev script in Chromium, as `dev/README.md` describes.
- [ ] **Step 4:** Run the tests and the full suite. Expected: OK.
- [ ] **Step 5:** Commit: "Three typefaces: Archivo wide (hero), Instrument Serif italic (aside), JetBrains Mono (label)".

### Task 4: The headline layer

**Files:**
- Create: `scripts/headline.py` (sizing and markup, so it can be tested without composing)
- Modify: `scripts/explainer-compose.py`, so that `place()` receives the area left under a headline
- Test: `tests/test_editorial.py`, class `Headline`

**Interfaces:**
- Consumes: `E.hero()`, `E.SCENE`, `ctx.item(ref)`.
- Produces:
  - `headline.validate(h: dict) -> list[str]`;
  - `headline.layout(h, width) -> {"size": int, "lines": [[str]], "height": int}`;
  - `headline.render(h, ctx, top) -> (html, js)`;
  - `headline.GAP = 32` (the gap between the headline and the scene below it).

The data:
```
"headline": {"text": "NO BATTERY", "accent": ["BATTERY"], "kicker": "INSIDE THE EARBUDS",
             "aside": "seriously?", "at": "word:4", "aside_at": "word:6"}
```

- Text: the hero face, size from 120 down to 64 in steps of 4, at most 3 lines in 950 px.
- Kicker: JetBrains Mono 28 px, letter-spacing .18em.
- Aside: Instrument Serif italic, 56 px, ink at 0.6 (accent when it starts with a capital and ends with "." — "Yes.").
- Each line rises through a mask on its word (0.55 s, expo.out), lines 0.08 s apart.
- The kicker types in.
- The aside fades and slides 12 px.

- [ ] **Step 1:** Write the tests:
  - `test_a_headline_sits_top_left_and_the_scene_below_it`: the headline box top is 345 and left is 65; the scene box top ≥ 345 + headline height + 32.
  - `test_a_headline_rises_on_its_word`.
  - `test_accent_words_take_the_accent`.
  - `test_a_headline_that_leaves_no_room_fails`: a 3-line headline plus a tall `stack` gives E3 FAIL "the headline leaves N px for the scene; shorten the headline or drop an item".
  - `test_headline_text_is_at_least_28px_drawn`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. `place()` gets a `top` parameter (default `E.SCENE["top"]`). The headline renders inside the scene host, so it exits with the scene. It is sized by `E.text_width(..., E.hero()["glyphs"], spacing)`.
- [ ] **Step 4:** Run the full suite. Expected: OK. Then run E5 on a composed headline case: PASS.
- [ ] **Step 5:** Commit: "A headline layer: top-left, the hero face, on its words".

### Task 5: The hero face in kinetic, giant captions, title-card and stat

**Files:**
- Modify: `scenes/kinetic.py`, `scenes/giant_captions.py`, `scenes/title_card.py`, `scenes/stat.py`, so they read `E.hero()` for glyphs and CSS instead of `"display700"`
- Test: `tests/test_editorial.py`, class `HeroFace`; the existing kinetic and giant tests stay green in latte

- [ ] **Step 1:** Write tests:
  - `test_paper_kinetic_uses_the_wide_face_and_fits`: compose the kinetic hook in paper; its CSS has `font-stretch:125%`; E5 PASS on the case.
  - `test_latte_unchanged`: the latte HTML of a kinetic case is byte-identical to before. Snapshot the old output into the test before changing the code.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. Measure the new heights for these 4 scenes in paper with `dev/measure-scenes.mjs`, saved to `tests/fixtures/heights-e.json` with a `look` field.
- [ ] **Step 4:** Run the full suite. Expected: OK.
- [ ] **Step 5:** Commit: "The hero face in kinetic, giant captions, title cards and stats".

### Task 6: Images and annotations

**Files:**
- Create: `scripts/imagesize.py` (PNG, JPEG, WebP and GIF header readers, stdlib only)
- Create: `scripts/scenes/_annotate.py`
- Modify: `scripts/scenes/__init__.py` (`ctx.image(rel) -> (page_path, w, h)`; Windows backslashes normalised)
- Test: `tests/test_images.py`

**Interfaces:**
- Produces:
  - `imagesize.size(path) -> (w, h)`, raising `ValueError("not a PNG, JPEG, WebP or GIF")`;
  - `ctx.image(rel)`;
  - `_annotate.validate(notes) -> list[str]`;
  - `_annotate.render(notes, ctx, box_w, box_h, sid) -> (html, js)`.

Each note:
```
{"x": 0..1, "y": 0..1, "label": "WAIT… A WIRE?", "at": "word:N", "mark": "circle"|"dot"|"none", "side": "left"|"right"}
```

- `x` and `y` are fractions of the image box.
- A note draws its mark (an SVG circle, r 56, accent stroke 6, drawn on over 0.45 s), then a leader line to a mono pill label (accent fill, base text, 28 px), which pops in 0.15 s later.
- The labels stay inside the box: E3 fails a label that would not fit, naming it.

- [ ] **Step 1:** Write the tests:
  - `test_sizes_of_png_jpeg_webp_gif` (write tiny files in the test);
  - `test_backslash_src_resolves`;
  - `test_a_note_draws_its_circle_then_its_label_on_its_word`;
  - `test_a_label_that_cannot_fit_fails_naming_it`.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. Notes are absolutely positioned inside the image box's wrapper, so they move with the camera.
- [ ] **Step 4:** Run the full suite. Expected: OK.
- [ ] **Step 5:** Commit: "Images: sizes without PIL, ctx.image, annotations that draw on".

### Tasks 7 to 9: the new scenes (parallel; each its own module, cases, fixtures and tests)

All four groups consume Tasks 1 to 6. Each scene:
- has TYPE, CSS, `validate`, `height(scene, width)`, `min_width`, `render`, and DECOR_KEYS where numbers are furniture;
- has cases in `dev/cases_e.py` (three lengths each) and measured rows in `tests/fixtures/heights-e.json` (both looks, both columns);
- has tests in `tests/test_scenes_e.py` (one class per scene: validation, timing on words, motion while held, E5 clean);
- keeps moving while held, so no still stretch over 1 s comes from it.

| Task | Scene | Data | What it does |
|---|---|---|---|
| 7 | `product-hero` | `src`, `alt`, `title` (behind, hero face, at least 120 px), `title_at`, `at`, `notes[]` (Task 6), `float` (true) | The image rises in with a soft shadow, then floats (y ±8 px, sine, scene-long) and pushes in slowly. The title sits behind it (`data-depth="behind"`), revealed per line. Any aspect fits (`test_any_aspect_fits`). |
| 7 | `photo-grid` | `photos[{src, credit, tag?, at}]` (1 to 4), `layout` (`stack`, `grid`, `collage`) | Photos slide in one by one (0.12 s stagger, expo.out) with rounded corners and a shadow. A credit chip (mono 28 px, base on ink at 0.8) sits bottom-left; a tag chip sits top-left. Each photo drifts slowly. E3 fails a photo with no credit. |
| 8 | `waveform` | `states[{kind: "noise"/"calm"/"music"/"pulse"/"flat", label, at}]`, `color` | One SVG path of 200 points scrolls left forever (phase over the scene, linear). Its amplitude and shape tween between states on their words, from a seeded noise table, so it is the same every render. The label is mono 28 px under the line. |
| 8 | `mode-switch` | `options[{label, wave, note, at}]` (2 to 4), `image?` | A segmented control: a pill slides under the active option on its word, a waveform below takes that option's wave, and the note line under it changes. |
| 8 | `line-chart` `shape: "step"` | as now plus `shape` | The line is drawn as steps (H/V segments); the counted value follows the last step. |
| 9 | `crossed-list` | `prefix` ("NO"), `items[{text, at, strike}]` (2 to 5) | Hero-face rows rise on their words; on `strike` a 6 px line draws through (0.3 s) and the row greys to `muted`; the mono prefix sits above each row. |
| 9 | `price-sticker` | `price`, `label`, `src?`, `at`, `source` (NEEDS_SOURCE) | A rotated (-6°) accent sticker slams in from scale 1.5 (expo.out, no overshoot), with a shadow that tightens as it lands, then breathes ±1° (sine, scene-long). There is an optional product image behind it. |
| 9 | `line-art` | `icon` (Lucide) or `svg` (the creator's stroke-only SVG), `caption` (serif aside), `strike` | The drawing is drawn on by stroke-dashoffset (1.2 s, power2.inOut) and the caption fades in; on `strike` the caption is struck through in the accent. An SVG with fills fails validation. |

- [ ] **Steps, per task:**
  1. tests;
  2. FAIL;
  3. module, cases and measured fixtures;
  4. full suite OK and `test_every_scene_case_is_clean` on both looks;
  5. commit per group: "Scenes: product-hero and photo-grid", "Scenes: waveform, mode-switch and the step chart", "Scenes: crossed-list, price-sticker and line-art".

### Task 10: The thread

**Files:**
- Create: `scripts/thread.py`
- Modify: `scripts/explainer-compose.py` (renders the layer; adds its keys to moments.json `spans`)
- Modify: `scripts/layout-probe.mjs` (skips `[data-thread]` in the cover and crossing checks, as it does the ground)
- Test: `tests/test_thread.py`

**Interfaces:**
- Produces:
  - `thread.SHAPES = ("drop", "loop", "wave", "rule", "underline", "off")`;
  - `thread.N = 96`;
  - `thread.points(shape: str, p: dict) -> list[tuple[float, float]]` (N points in frame px);
  - `thread.validate(spec, words) -> list[str]`;
  - `thread.render(spec, words, tok) -> (html, js, spans)`.

The storyboard:
```
"thread": {"color": "ink"|"accent", "width": 8, "keys": [
   {"at": "word:3", "shape": "drop", "x": 540, "to": 900},
   {"at": "word:9", "shape": "loop", "x": 540, "y": 1000, "rx": 320, "ry": 90},
   {"at": "word:20", "shape": "wave", "y": 1500, "amp": 60},
   {"at": "word:40", "shape": "off"}]}
```

- The first key draws on from the top (0.8 s).
- Each later key morphs from the last over 0.6 s (power3.inOut). A proxy tween's `onUpdate` sets the path's `d` from a linear blend of the two point lists, so seeking any frame gives the same picture.
- A `wave` keeps scrolling (phase, linear) while it holds.
- `off` retracts the line upward.

- [ ] **Step 1:** Write the tests:
  - `test_every_shape_has_n_points_inside_the_frame`;
  - `test_keys_must_rise_in_time_and_name_known_shapes`;
  - `test_the_first_key_draws_on_and_later_keys_morph_on_their_words` (regex the tweens);
  - `test_the_thread_passes_behind_the_captions` (z-index under `.cap` and over `.bg`);
  - `test_morphs_are_moments_for_pace_check`;
  - `test_e5_ignores_the_thread` (compose BOARD with a drop through a title; `layout-check` PASS).
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement. Shapes are pure functions of their params. The layer is `<svg class="thread" data-thread ...>` at z-index 5.
- [ ] **Step 4:** Run the full suite. Expected: OK.
- [ ] **Step 5:** Commit: "The thread: one line through the reel, morphing on words".

### Task 11: Planner hints and docs

**Files:**
- Modify: `scripts/plan-storyboard.py`:
  - `viz` hints for every new type;
  - `headline` passes through;
  - a `thread` in script.json is copied to the storyboard with word anchors resolved like items.
- Modify: SKILL.md (the brief asks for the look; the Packager line unchanged), PLAYBOOK (the scene table, §E4 area, the look, the thread, the depth rule), MOTION.md (the paper look, three faces, the thread doctrine), the four agent files, READMEs (test counts; 47 library scenes)
- Test: `tests/test_editorial.py`, class `Planner`, and `tests/test_docs.py` (each new type is in PLAYBOOK's table)

- [ ] **Step 1:** Write the tests:
  - `test_hints_for_the_new_scenes_plan`;
  - `test_a_thread_in_the_script_reaches_the_storyboard`;
  - `test_every_scene_type_is_in_the_playbook_table` (discover() against the table).
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the full suite. Expected: OK.
- [ ] **Step 5:** Commit: "Planner hints and docs for the editorial pass".

### Task 12: Demo in the paper look, and the comparison

**Scratchpad only:** `demo3/`.

- A 45 to 60 s script on USB-C, using every new scene. Facts come with sources:
  - USB-IF: USB4 v2 runs at 80 Gbps;
  - USB PD 3.1: up to 240 W;
  - EU Directive 2022/2380: USB-C mandatory from 28 Dec 2024.
- Stand-in images are rendered locally: a USB-C cable and plug drawn in SVG, rasterised with Chrome (transparent); three generated "photos". Each is credited "stand-in image".
- Steps:
  1. E1 to E5;
  2. stills;
  3. render;
  4. E6;
  5. `verify-render`;
  6. the upload copy;
  7. the metrics against the Bose reel (`teardown/motion.py`, `fill.py`) and the side-by-side sheet;
  8. send the reel, the stills sheet and the comparison.

### Task 13: Final review

- Run `review-package` over the branch range. Dispatch a fresh reviewer on the most capable model with this plan, its Rulings and the Review Focus.
- Fix Critical and Important findings test-first. Run the full suite, commit and push.
- Report the rulings and the deferred minors.
