# Explainer Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the third profile, `Editing-Workflow/explainer/`. It makes faceless, code-animated 60 to 90 s vertical
explainer reels with a free local AI voice (Kokoro) and word-timed captions.

**Architecture:**
- **The voice:** `script.json` (spoken `say` and shown `show` text for each line) → `tts-kokoro.py` → `voice.wav`.
  Parakeet transcribes it, and `align-script.py` writes `transcript.json` (display words with times).
- **The picture:** the Director writes `storyboard.json` (scenes anchored to `word:N`) → `explainer-compose.py` turns
  it into a HyperFrames composition, using one module per scene type plus a sandboxed `custom` scene.
- **The rest:** Reels' Renderer, QA, Packager, Librarian and Analyst are reused unchanged.

**Tech Stack:** Python 3 (stdlib + numpy), FFmpeg, HyperFrames + GSAP 3.14.2, KaTeX (MIT), lucide-static (ISC),
Kokoro-82M via `pip install kokoro` (Apache-2.0), Parakeet (through `npx hyperframes transcribe`), unittest.

**Spec:** [`SPEC.md`](SPEC.md). Read it before every task; section numbers below (§) refer to it.

## Global Constraints

- **Free tools and licences only.** No paid service, no non-commercial model weights.
- **Output:** 1080x1920, 60 fps. The composition root carries `data-fps="60" data-width="1080" data-height="1920"`.
- **Safe zone and areas:**
  - safe zone `reels_lib.SAFE` (65,269 to 1015,1248); `reels_lib.NARROW` (150 to 930) below `reels_lib.RIGHT_COL_TOP` (960);
  - scene area x 65 to 1015, y 520 to 1248;
  - caption band y 330 to 470.
- **Captions:** phrases of up to 4 words and 24 characters. The phrase clears at a pause of 0.35 s or more.
- **Anchors:** `word:N` is the Nth display word (0-based) in `transcript.json`. An entrance starts 0.2 s before its
  word (`LEAD = 0.2`).
- **Timing:**
  - scenes overlap by at most 0.3 s; a background cross-fade lasts 0.4 s;
  - the composition's duration is the voice's length plus 0.5 s.
- **Pauses between lines:** 0.15 s (`comma`), 0.35 s (`sentence`), 0.6 s (`section`). Kokoro speed 1.0 to 1.1.
- **Voice levels:** `voice.wav` at -16 LUFS, true peak at most -1 dBTP, high-pass at 80 Hz.
- **E1 (script):** 2.7 words a second; 60 to 90 s is 160 to 240 words. The hook (line 0) is at most 12 words. A line
  whose `show` has a digit, `%` or `$`, or `"fact": true`, needs `source`. `payoff` and `cta` must name existing lines.
- **E2 (voice):** at least 98% of `say` words align; no gap inside a sentence over 1.2 s; length within ±10% of
  `target_seconds`.
- **Kit compatibility:** every timed element is `<div class="card-host clip" data-start data-duration
  data-anchor="<word text>">`; captions sit in `class="clip cap-layer"`; the timeline is registered in
  `window.__timelines[<json id>]`. The kit's `beat-check.py`, `gap-scan.py`, `snap-beats.py` and `verify-render.py`
  must read the page unchanged.
- **Repository rules:**
  - everything lives under `Editing-Workflow/explainer/`; the kit folder is not modified;
  - commit trailers: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
    `Claude-Session: https://claude.ai/code/session_01NHkfDqHcXZT9s2Fh2CLk3f`;
  - no model identifiers in repository files.

Paths used below:
- `S` = `Editing-Workflow/explainer/skill/explainer/scripts`
- `T` = `$S/tests`
- run tests with `cd $S && python3 -m unittest tests.<module> -v`

## Review Focus

1. **Spoken and shown text differ** ("one thousand dollars" against "$1,000", "twenty twenty-four" against "2024",
   "W A C C" against "WACC"). The captions must show `show`, timed across the whole `say` span (Task 3 test
   `test_say_show_spans_map_times`).
2. **A word or number that never wraps** (a long single word in `title`, `number`, `count-up` or `bars` text) must fail
   the build when it is wider than its column, never overflow (Tasks 5 and 6 test `test_unbreakable_word_too_wide_fails`).
3. **Every moment of the voice needs a scene.** A gap of more than 0.3 s with no scene, at the start, between scenes or
   at the end, must fail (Task 5 test `test_uncovered_time_fails`).
4. **Anchors out of order** (`out` before `in`, or an item's `at` outside its scene's time) must fail with the scene id
   named (Task 5 test `test_anchor_order_errors_name_the_scene`).
5. **An emphasis term with punctuation or a repeat** ("NPV," or NPV twice) must highlight every occurrence, ignoring
   punctuation (Task 5 test `test_emphasis_matches_normalised_and_repeated`).

---

### Task 1: Scaffold, shared library and test helpers

**Files:**
- Create: `$S/explainer_lib.py`, `$S/tests/__init__.py`, `$S/tests/helpers.py`, `$S/tests/test_lib.py`,
  `Editing-Workflow/explainer/skill/explainer/tokens.json`

**Interfaces:**
- Produces:
  - `explainer_lib.find_reels_lib() -> module`: imports `reels_lib` from the first existing of `$REELS_SCRIPTS`,
    `$S/../../reels/scripts` (installed) or `$S/../../../../reels/skill/reels/scripts` (repository). Exits with a clear
    message when none exists.
  - `explainer_lib.L` = that module (`SAFE`, `NARROW`, `RIGHT_COL_TOP`, `chunk_words`, `load_words`, `norm`,
    `full_digits`).
  - Constants: `SCENE = {"left": 65, "top": 520, "right": 1015, "bottom": 1248}`, `CAPTION_BAND = (330, 470)`,
    `LEAD = 0.2`, `MAX_OVERLAP = 0.3`, `BG_FADE = 0.4`, `TAIL = 0.5`.
  - `resolve(ref: str | float, words: list[dict], lead: bool = False) -> float`: `"word:N"` gives `words[N]["start"]`
    (minus `LEAD` when `lead`); a number passes through. Raises `ValueError("bad anchor %r" % ref)` for anything else
    or an out-of-range N.
  - `anchor_text(ref, words) -> str`: the display word's text, or `"-"` for a plain number.
  - `load_tokens(path=None) -> dict`: reads `tokens.json` next to `$S/..`. Keys `fonts`, `colors` (`cyan #0AF0F0`,
    `amber #FFB904`, `magenta #CD00EE`, `white #FFFFFF`), `backgrounds` (`blue`, `black`, `light`, each a CSS
    `background` value), `highlight` (fill, text colour, handle colour) and
    `motion` (`enter_ease: "power3.out"`, `exit_ease: "power2.in"`, `enter: 0.42`, `exit: 0.28`,
    `stagger_total_max: 0.5`). The label font is `JetBrains Mono` (SIL OFL), staged from
    `vendor/fonts/JetBrainsMono-500.woff2` (`npm pack @fontsource/jetbrains-mono@5.1.0`). When the file is missing, labels
    fall back to `ui-monospace` with a printed WARN; this is never a failure.
  - `text_width(text, size) -> float` = `len(text) * size * 0.56`, and `text_lines(text, size, width) -> int`, both as
    in reels-compose.
  - `tests/helpers.py`: `run`, `run_kit`, `scratch`, `write`, `read`, `load`, `needs_ffmpeg`, `needs_kit`, all as in
    Reels' helpers. Plus `transcript(spec: str) -> dict`, where `"Hello@1.0 there@1.4"` gives words 0.3 s long.

- [ ] **Step 1:** Write `tests/test_lib.py`:
  - `test_resolve_word_and_lead`: `resolve("word:1", W) == 1.4`; with `lead=True`, `1.2`; `resolve(3.5, W) == 3.5`.
  - `test_resolve_rejects_bad_anchors`: `"word:9"` (out of range), `"w:1"` and `"word:x"` each raise `ValueError`.
  - `test_tokens_have_the_house_colours`: `load_tokens()["colors"]["cyan"] == "#0AF0F0"`, the three background keys
    exist, and `motion.exit <= 0.7 * motion.enter` (exits 30 to 50% shorter, SPEC §6.3).
  - `test_reels_lib_is_found`: `explainer_lib.L.SAFE["bottom"] == 1248`.
- [ ] **Step 2:** Run `python3 -m unittest tests.test_lib -v`. Expected: an ImportError / FAIL.
- [ ] **Step 3:** Implement `explainer_lib.py`, `tokens.json` and `tests/helpers.py` to the interfaces above.
- [ ] **Step 4:** Run it again. Expected: 4 tests OK.
- [ ] **Step 5:** Commit: `git add Editing-Workflow/explainer/skill && git commit` with the message "explainer: shared
  lib, tokens, test helpers" and the trailers.

### Task 2: The script and gate E1 (`script-check.py`)

**Files:** Create `$S/script-check.py`, `$T/test_script_check.py`.

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces the `script.json` schema, which Tasks 3, 4 and 12 use:

  ```json
  {"title": "...", "target_seconds": 75, "voice": "am_michael",
   "lines": [{"id": "l0", "say": "...", "show": "...", "break": "comma|sentence|section",
              "emphasis": ["NPV"], "source": "s1", "fact": false}],
   "payoff": "l9", "cta": "l12",
   "sources": {"s1": {"title": "...", "url": "...", "note": "..."}}}
  ```

- CLI: `script-check.py --script script.json [--report SCRIPT.md]`. Exit 0 with a summary (words, estimated seconds,
  lines, sources) or exit 1 listing every failure. `--report` writes a readable `SCRIPT.md` (the `show` text, numbered
  lines, sources as a list) for Checkpoint A.

- [ ] **Step 1:** Write the tests:
  - `test_valid_script_passes_and_estimates_length`: 200 `show` words gives exit 0 and "est 74.1 s" (200/2.7).
  - `test_too_short_and_too_long_fail`: 150 words fails ("under 160 words"); 250 words fails ("over 240 words").
  - `test_long_hook_fails`: line 0 with 13 words fails ("hook is 13 words").
  - `test_number_without_source_fails`: `show` "It costs $1,000" with no `source` fails, naming the line id. The same
    line with `"source": "s1"` and `sources.s1` passes. A `source` key missing from `sources` fails.
  - `test_payoff_and_cta_must_exist`: `cta: "l99"` fails.
  - `test_report_lists_sources`: `--report` writes `SCRIPT.md` containing each source URL.
- [ ] **Step 2:** Run. Expected: FAIL (the script is missing).
- [ ] **Step 3:** Implement `script-check.py`. Word count = words in `show` text (split on whitespace). Range bounds:
  160 to 240 words, scaled by `target_seconds` (`round(target*2.7) ± 15%`). With no target the bounds are 160 to 240.
- [ ] **Step 4:** Run. Expected: 6 OK.
- [ ] **Step 5:** Commit with the message "explainer: script schema and gate E1".

### Task 3: Script alignment and gate E2 (`align-script.py`)

**Files:** Create `$S/align-script.py`, `$T/test_align.py`.

**Interfaces:**
- Consumes: the Task 2 schema; ASR output `{"words": [{"text", "start", "end"}]}` (the Parakeet shape).
- Produces:
  - `align(lines: list[dict], asr: list[dict]) -> tuple[list[dict], dict]`. It returns display words
    `[{"text", "start", "end", "line"}]` (taken from `show`) and stats
    `{"say_words", "matched", "ratio", "max_gap", "gap_line"}`.
  - CLI: `align-script.py --script script.json --asr asr.json --out transcript.json [--report VOICE.md]`. Exit 1 when
    `ratio < 0.98` or `max_gap > 1.2` inside a line; the message names the line id.
- Algorithm (not obvious from the signature):
  1. Normalise words: lower-case, strip punctuation.
  2. Align `say` words to ASR words with `difflib.SequenceMatcher` per line window, accepting a fuzzy match
     (ratio ≥ 0.8) for single substitutions.
  3. Map `show` words onto `say` words per line, proportionally by position when the counts differ. Each `show` word
     takes the span from its first to its last mapped `say` word.
  4. Interpolate unmatched `say` words between their matched neighbours.

- [ ] **Step 1:** Write the tests:
  - `test_exact_match_gives_asr_times`.
  - `test_say_show_spans_map_times`: `say` "it costs one thousand dollars", `show` "It costs $1,000". "$1,000" spans
    from the start of "one" to the end of "dollars".
  - `test_skipped_word_lowers_ratio_and_fails_under_98`: 100 `say` words with 3 missing from the ASR gives exit 1 and
    "97.0% aligned (line l…)".
  - `test_substitution_is_tolerated`: ASR "wack" against `say` "wack" is fine; ASR "whack" counts as matched (fuzzy).
  - `test_gap_inside_a_line_fails`: a 1.5 s hole between two words of one line gives exit 1 ("gap 1.50 s in line l2").
    The same hole between lines passes.
  - `test_transcript_shape_feeds_reels_lib`: the output loads with `L.load_words`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement to the interface.
- [ ] **Step 4:** Run. Expected: 6 OK.
- [ ] **Step 5:** Commit with the message "explainer: align the voice to the script (gate E2)".

### Task 4: The voice (`tts-kokoro.py`)

**Files:** Create `$S/tts-kokoro.py`, `$T/test_tts.py`,
`Editing-Workflow/explainer/skill/explainer/lexicon.json` (seed: `{"WACC": "wack", "EBITDA": "ee-bit-dah",
"NPV": "N P V", "IRR": "I R R", "DCF": "D C F"}`).

**Interfaces:**
- Consumes: the Task 2 schema; `lexicon.json`.
- Produces: the CLI `tts-kokoro.py --script script.json --out voice.wav [--voice ID] [--speed 1.0] [--only l3]
  [--engine kokoro|fake] [--lexicon PATH] [--samples DIR]`.
  - It writes `lines/<id>.wav` (24 kHz mono) for each line. `--only` regenerates just that line.
  - It joins the lines with pauses by `break` (0.15, 0.35 or 0.6 s), then runs the cleanup chain:
    `highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=10:release=120`, then two-pass `loudnorm=I=-16:TP=-1`.
    The output is `voice.wav` (48 kHz mono).
  - It prints `{"duration", "lufs", "peak"}` as JSON.
  - It exits 1 when the length is more than 10% off `target_seconds`.
  - `--samples DIR` writes three 10 s samples of line 0 with the voices `af_heart`, `am_michael` and `bf_emma` (for
    Checkpoint A).
  - Lexicon entries are whole-word, case-sensitive replacements in `say` before synthesis.
- The `fake` engine (for tests) writes a 220 Hz tone, 0.32 s per `say` word, with no network and no model. `kokoro`
  imports `kokoro.KPipeline(lang_code="a")`, falling back to `"b"` for `bf_*` voices, at 24000 Hz.

- [ ] **Step 1:** Write the tests (`@needs_ffmpeg`):
  - `test_fake_engine_lines_and_pauses`: three lines of 5 words with breaks `comma`, `section`, `sentence` give a
    `voice.wav` of 3×5×0.32 + 0.15 + 0.6 s (± 0.05). The last line's break adds nothing.
  - `test_only_regenerates_one_line`: after a full run, `--only l1` rewrites only `lines/l1.wav` (the other mtimes are
    unchanged) and rebuilds `voice.wav`.
  - `test_levels_and_peak`: the JSON shows `lufs` within -16 ± 1 and `peak <= -1.0`.
  - `test_length_gate`: `target_seconds` far from the result gives exit 1 ("off target by").
  - `test_lexicon_is_applied`: the fake engine records the text it got in `lines/<id>.txt`. "WACC" becomes "wack".
  - `test_real_kokoro_smoke`: decorated with `skipUnless(kokoro importable)`. One short line gives a non-silent wav
    longer than 0.5 s.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: 5 OK, 1 skipped (or 6 OK where Kokoro is installed).
- [ ] **Step 5:** Commit with the message "explainer: voice generation with Kokoro, line by line".

### Task 5: The composer core and the first three scenes

**Files:** Create `$S/explainer-compose.py`, `$S/scenes/__init__.py`, `$S/scenes/title.py`, `$S/scenes/number.py`,
`$S/scenes/count_up.py`, `$T/test_compose.py`.

**Interfaces:**
- Consumes: Task 1 (`resolve`, `anchor_text`, `load_tokens`, `SCENE`, `CAPTION_BAND`, `L`, `text_width`,
  `text_lines`); `transcript.json` from Task 3.
- Produces the scene module contract, which Tasks 6, 7 and 8 follow:
  - `TYPE: str`
  - `validate(scene: dict) -> list[str]`: data-shape errors.
  - `height(scene: dict, width: int) -> int`: the measured box height at that width.
  - `min_width(scene: dict) -> int`: the widest unbreakable text, plus padding.
  - `render(scene: dict, ctx: Ctx, box: tuple[int, int, int]) -> tuple[str, list[str]]`: HTML inside the box, plus
    GSAP lines.
  - `Ctx` holds `t_in`, `t_out`, `at(ref) -> float` (resolved with the lead), `esc`, `tokens`, `vendor(name) -> str`
    (a staged path, or `fail`) and `fail(msg)`.
  - `scenes.REGISTRY: dict[str, module]`.
- The CLI: `explainer-compose.py --spec storyboard.json --out public [--vendor DIR]`.
  - It reads `transcript` and `voice` relative to the spec.
  - It places each scene centred vertically in `SCENE`: wide (950) unless it reaches below 960, then narrow (780);
    `height` is re-measured at the chosen width.
  - It fails when the scene is outside `SCENE`, or when `min_width > width`.
  - Backgrounds: one full-frame layer per `bg` change, cross-faded over `BG_FADE`.
  - Captions: `L.chunk_words(words, 4, 24)` in the caption band; the spoken word goes from dim to white; emphasis
    words get the highlight box.
  - The voice is an `<audio id="voice" data-start="0" data-duration=D data-track-index="1" data-volume="1">`.
  - Kit-compatible markup (Global Constraints). GSAP, fonts and KaTeX are staged as in reels-compose; `--vendor`
    overrides the vendor folder for tests.
  - Exit 1 on any rule below.

- [ ] **Step 1:** Write `$T/test_compose.py` (with a 30-word transcript and a storyboard of `title`, `number` and
  `count-up` covering it):
  - `test_builds_vertical_60_with_voice_and_kit_markup`: `data-fps="60"`, `id="voice"`, a `card-host clip` per scene
    with `data-anchor` equal to the anchor word, and `window.__timelines[`.
  - `test_scene_box_inside_scene_area_both_widths`: every `class="box"` style is within `SCENE`; a scene reaching
    below 960 gets `width:780px`.
  - `test_unbreakable_word_too_wide_fails`: a `title` with a 26-character single word at 120 px fails ("wider than the").
  - `test_uncovered_time_fails`: a 1 s hole between scenes fails ("no scene from"). The same check applies to the
    start (first `in` > 0.3 s) and the end (last `out` < D - 0.3 s).
  - `test_overlap_over_0_3_fails`: scenes overlapping 0.5 s fail; overlapping 0.25 s pass.
  - `test_anchor_order_errors_name_the_scene`: `out` before `in` fails, naming the scene id.
  - `test_emphasis_matches_normalised_and_repeated`: emphasis `["NPV"]`, with transcript words "NPV," and "npv", gives
    two highlight spans.
  - `test_background_crossfades_on_change`: bg `black` → `light` gives one fade at the second scene's `in`.
  - `test_caption_layer_is_excluded_by_gap_scan` (`@needs_kit`): the kit's `gap-scan.py` runs on the page, and
    coverage counts scenes only.
  - `test_kit_beat_check_passes` (`@needs_kit`): the kit's `beat-check.py` exits 0.
  - `test_motion_rules`:
    - every GSAP entrance in the page uses `tokens.motion.enter_ease`, and every exit uses `exit_ease` with a duration
      ≤ `exit`;
    - no `ease: 'none'` on an `x`/`y`/`scale` tween;
    - per scene, the stagger total (last item delay) is ≤ 0.5 s.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement the composer and the three scenes. Each scene's `height` comes from its own CSS constants,
  using the measurement approach in Task 9.
- [ ] **Step 4:** Run. Expected: 11 OK.
- [ ] **Step 5:** Commit with the message "explainer: composer core, captions, backgrounds, first scenes".

### Task 6: Data and list scenes

**Files:** Create `$S/scenes/list_cards.py`, `line_chart.py`, `bars.py`, `duration.py`, `qa_stack.py`, and
`$T/test_scenes_data.py`.

**Interfaces:** Consumes the Task 5 contract. Data fields exactly as in SPEC §6.2. Item times (`at`) are anchors, and
each must fall inside the scene's `[in, out]`.

- [ ] **Step 1:** Write the tests, one per scene, with these assertions:
  - **`list-cards`:** 2 to 4 items allowed (1 or 5 fails); each card's GSAP entrance time is its `at` minus `LEAD`.
  - **`line-chart`:**
    - `len(points) == len(x)`, or it fails;
    - the `reveal` point index must be in range;
    - the count-up target is the last revealed point;
    - numbers are formatted with `L.full_digits`.
  - **`bars`:** values ≥ 0; the bar width is proportional to `value / max`; `hi` rows use the cyan token.
  - **`duration`:** `unit` is one of `hours`, `days`, `weeks`; `style` is `clock` or `dial`.
  - **`qa-stack`:** at most 5 items; each `em` term gets the highlight in its item.
  - **Shared:** `test_item_at_outside_scene_fails` and `test_unbreakable_word_too_wide_fails` (a bar label of one
    40-character word).
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement the five modules.
- [ ] **Step 4:** Run. Expected: all OK.
- [ ] **Step 5:** Commit with the message "explainer: list, chart, bar, duration and Q&A scenes".

### Task 7: Mock-UI, formula and icon scenes

**Files:** Create `$S/scenes/browser.py`, `sheet.py`, `formula.py`, `icon_row.py`, and `$T/test_scenes_ui.py`.

**Interfaces:**
- Consumes the Task 5 contract and `Ctx.vendor`.
- `formula` needs `vendor/katex/katex.min.js` and `katex.min.css` (plus `fonts/`). It renders in the browser with
  `katex.render`.
- `icon-row` inlines `vendor/lucide/<name>.svg`.
- A missing vendor file fails, naming the install command:
  - `npm pack katex@0.16.11` / `npm pack lucide-static@0.454.0`;
  - unpack to `$ES/assets/vendor/`.

- [ ] **Step 1:** Write the tests (each test creates a stub vendor folder and passes `--vendor`):
  - **`browser`:** the title and badges are escaped; `domain` is shown in the address bar; no external URL appears in
    the page.
  - **`sheet`:** the row count is at most 8; `highlight` names an existing row or cell (otherwise it fails); `formula`
    is shown in the formula bar.
  - **`formula`:** each `parts[].at` gives a reveal at that time; a missing KaTeX vendor fails with
    "npm pack katex@0.16.11".
  - **`icon-row`:** an unknown icon name fails, naming it; 2 to 4 items; the SVG is inlined (no `<img src=http`).
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run. Expected: all OK.
- [ ] **Step 5:** Commit with the message "explainer: browser, sheet, formula and icon scenes".

### Task 8: The custom scene contract

**Files:** Create `$S/scenes/custom.py`, `$T/test_custom.py`.

**Interfaces:** SPEC §6.4 exactly.
- The HTML file (path relative to the spec) is inserted inside `<div id="<id>" class="box">`.
- The build function is called as `window.<build>(tl, document.getElementById("<id>"), t_in, t_out)`.
- three.js is allowed from `vendor/three/three.module.min.js` (`npm pack three@0.169.0`).

- [ ] **Step 1:** Write the tests. Each violation fails with its own message:
  - `test_box_outside_scene_area_fails`
  - `test_selector_outside_id_fails`: the file contains `document.querySelector('.x')` or `document.body`.
  - `test_network_fails`: `fetch(`, `http://`, `https://` or `import(` with a URL.
  - `test_missing_build_function_fails`
  - `test_duplicate_id_fails`
  - `test_valid_custom_scene_builds`: the page contains the build call with the resolved `t_in` and `t_out`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. The lint uses regular expressions over the HTML file. Allowed selectors are `#<id>`,
  `root.querySelector(...)` and `root.querySelectorAll(...)`.
- [ ] **Step 4:** Run. Expected: 6 OK.
- [ ] **Step 5:** Commit with the message "explainer: sandboxed custom scenes".

### Task 9: Height calibration in Chromium

**Files:** Create `$S/dev/measure-scenes.mjs`, `$T/fixtures/heights.json`, `$T/test_heights.py`.

**Interfaces:**
- `measure-scenes.mjs <cases-dir>`: puppeteer with `/opt/pw-browsers/chromium` or `$CHROME`. For each composed case it
  prints `{case, scene, width, height}` (`offsetHeight` of `.box` once fonts are ready; hidden items forced visible).
- `fixtures/heights.json` records the measured values for at least 3 text lengths × 2 widths per scene type.

- [ ] **Step 1:** Write `test_heights.py`. For every fixture row,
  `0 <= module.height(case, width) - measured <= 4`. It also checks that the fixture file covers every type in
  `REGISTRY` except `custom`.
- [ ] **Step 2:** Run. Expected: FAIL (no fixtures yet).
- [ ] **Step 3:** Run the harness (`node $S/dev/measure-scenes.mjs`), save `heights.json`, and adjust each scene's
  height constants until the test passes. The harness is a developer tool, not part of the run path.
- [ ] **Step 4:** Run `python3 -m unittest tests.test_heights -v`. Expected: OK.
- [ ] **Step 5:** Commit with the message "explainer: scene heights calibrated in Chromium".

### Task 10: End to end

**Files:** Create `$T/test_end_to_end.py`, `$T/fixtures/e2e/` (`script.json`, `storyboard.json`).

- [ ] **Step 1:** Write `test_fake_voice_to_verified_render`. It is decorated with skips when ffmpeg, the kit or
  `npx hyperframes` is missing. It runs:
  1. `script-check.py`;
  2. `tts-kokoro.py --engine fake`;
  3. a synthetic ASR (the `say` words at the fake engine's known times);
  4. `align-script.py`;
  5. `explainer-compose.py`;
  6. `npx hyperframes check`;
  7. `npx hyperframes render --resolution portrait --fps 60` (12 s, a few scenes);
  8. the kit's `verify-render.py --res 1080x1920`.

  Each stage must exit 0, and VERIFY reports PASS.

  Also write `test_real_kokoro_parakeet_alignment` (SPEC §13 item 2), skipped unless both Kokoro and Parakeet are
  installed. It runs the e2e script through `tts-kokoro.py --engine kokoro`, then
  `npx hyperframes transcribe --engine parakeet`, then `align-script.py`. It asserts that `ratio >= 0.98` and that
  each display word's start lies inside its line's audio span. It records the median caption-to-word offset in the
  test output, for the README's "how it was verified".
- [ ] **Step 2:** Run. Expected: FAIL until the fixtures exist; then PASS.
- [ ] **Step 3:** Commit with the message "explainer: end-to-end test from script to verified render".

### Task 11: The Producer skill, playbook and agents

**Files:** Create `Editing-Workflow/explainer/skill/explainer/SKILL.md`, `PLAYBOOK.md`, and
`Editing-Workflow/explainer/agents/explainer-{writer,voice,director,animator}.md`.

**Interfaces:** The agent files follow the Reels agent format:
- frontmatter `name`, `description`, `tools`, `model: inherit`, and descriptions with no `": "` inside (YAML-safe);
- sections Paths, Your brief gives you, Procedure, Done when, Never, Report.

Each agent cites the exact script commands from Tasks 2 to 8. The Producer uses the flow in SPEC §5 and the gates in
SPEC §8, and routes failures per SPEC §10. It reuses `reels-renderer`, `reels-qa`, `reels-packager`,
`reels-librarian` and `reels-analyst` by name. The PLAYBOOK sections run §E0 to §E8:

| Section | Topic |
|---|---|
| §E0 | the profile |
| §E1 | hook and structure |
| §E2 | script rules |
| §E3 | voice |
| §E4 | scenes and pacing |
| §E5 | captions |
| §E6 | motion |
| §E7 | sources and claims |
| §E8 | failure patterns |

- [ ] **Step 1:** Write a test in `$T/test_docs.py`:
  - every agent and SKILL frontmatter parses with `yaml.safe_load` and has the required keys;
  - every `scripts/<name>.py` mentioned in the docs exists;
  - every `§E<n>` reference resolves to a heading in PLAYBOOK.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Write the documents.
- [ ] **Step 4:** Run. Expected: OK.
- [ ] **Step 5:** Commit with the message "explainer: Producer skill, playbook, four agents".

### Task 12: README, research, and the workflow integration

**Files:**
- Create: `Editing-Workflow/explainer/README.md`, `Editing-Workflow/explainer/RESEARCH.md`.
- Modify:
  - `Editing-Workflow/README.md` (the folder table; a third profile row in section 10; the simple flow diagram style
    with the yellow/blue/green legend);
  - `Editing-Workflow/templates/STATUS.md` (add a `| **Voice** | {Kokoro voice id, fixed for the channel} |` row after
    Language);
  - `Editing-Workflow/templates/examples/STATUS.md` (`| **Voice** | n/a |`).

**Content:**
- **RESEARCH.md:** what works in faceless explainer reels (hooks, pacing, caption style, voice), each claim sourced via
  web search, with confidence levels as in the Reels RESEARCH.md. It also records the Kokoro licence check (SPEC §13
  item 1) and the AI-label rules (item 4).
- **README:** the install steps (SPEC §11), the team, a simple mermaid flow plus the detailed one in `<details>`, the
  scripts table, and a "how it was verified" section filled from the Task 10 run.

- [ ] **Step 1:** Extend `test_docs.py`:
  - README links resolve;
  - every mermaid block is fenced;
  - STATUS.md has a Voice row.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Write the documents. Render the mermaid blocks with mermaid-cli to confirm they parse (as done for
  the other READMEs).
- [ ] **Step 4:** Run the full suites:
  - `cd $S && python3 -m unittest tests` → OK;
  - Reels: 37 OK;
  - kit: 47 OK.
- [ ] **Step 5:** Commit with the message "explainer: README, research, workflow integration", then push to the
  working branch.
