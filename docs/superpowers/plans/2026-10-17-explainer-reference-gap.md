# Explainer: close the gap to the reference, and the RAG-reel SOPs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** make the explainer's reels move, contrast and carry objects like the reference reel, add the 18 scene types
the creator asked for (plus chat, doc and stat), and turn the RAG reel's retrospective (S1 to S16) into gates, tools
and rules.

**Architecture:** the same pipeline (script → E1 → voice → E2 → plan → compose E3 → E4 → E5 → render → QA). New
gates sit inside the existing scripts where they belong (E1 length from a measured voice rate, E3 hook timing and the
90 s ceiling, E4 hold time, E5 handovers and contrast) plus one new render gate, E6 `motion-check.py`, measured on the
rendered file with FFmpeg. Scenes stay data-driven modules (`scenes/<name>.py`), now discovered automatically.

**Tech stack:** Python 3 (stdlib + numpy where the kit already uses it), HyperFrames + GSAP pages, puppeteer-core and
Chrome from HyperFrames, FFmpeg.

**Spec:** the creator's messages of 2026-10-17 (the reference analysis: 9 findings; the RAG retrospective: S1 to S16;
the list of 18 scenes) and the existing `Editing-Workflow/explainer/SPEC.md`.

## Global Constraints

- Free tools only; 1080x1920 at 60 fps; Catppuccin Latte colours only (palette.json values), a brand's own logo aside.
- Text and card edges end by **y 1235** (S7); painted shapes with no text may reach **y 1650**; the button column
  (narrow column below y 960) still applies.
- Every new gate runs on the creator's machine and costs no tokens.
- TDD: a failing test first for every behaviour; commit only on a green full suite.
- Commits end with the session's Co-Authored-By and Claude-Session lines; no model names in repo files.

## Rulings (decisions this plan makes for the creator)

1. **One bottom limit (S7 vs finding 7).** Text and cards: y 1235 everywhere (composer, E5 probe, guides, QA). The
   "use the lower third" finding becomes: shapes without text (particles, floors, illustrations) may run to y 1650.
2. **Dark and blue within Latte (finding 3).** Two new backgrounds: `blue` (fill blue; text base) and `ink` (fill
   text #4c4f69; text base; accent yellow, 3.06:1). All text is 28 px or more, so WCAG's large-text 3:1 applies on
   every background; a new `contrast` check in the E5 probe enforces it. UI mock-ups (browser, sheet, chat, doc, the
   editor and social scenes) use fixed light **paper** roles on any background, like the reference's white UI on blue.
3. **Handover (S9).** The old scene's exit now ends on the cut (starts `EXIT` before it) and the new one enters on
   the cut: the two are never both visible. E5 samples every cut every 2 frames and fails when both scenes show
   content above 30% opacity.
4. **Hook (S8).** Every item of the first scene lands by 0.8 s (E3 fails otherwise); the planner anchors a hook's
   pieces to words 0 and 1, staggered 0.1 s.
5. **Hold time (finding 2).** A scene held over 8 s fails E4 (over 6 s warns) unless it travels (a camera move per
   item); `flow` takes up to 6 nodes and travels when they don't fit.
6. **Slots, not ghosts (finding 8).** A piece waiting for its word shows as an empty outline (its text hidden), never
   as faint text.
7. **Gravity drop** uses physical rebounds written as power2 in/out keyframes, not a `bounce` ease (still banned).
8. **The 18 scenes** are read as below (one line each); the creator can redirect any of them.

| # | Scene (type) | What it shows |
|---|---|---|
| 1 | Kinetic hook (`kinetic`, upgraded) | the big token is promoted automatically ("5 STEPS" → big "5" + "STEPS"); pieces land by 0.8 s |
| 2 | Gravity drop (`gravity-drop`) | words or chips fall from above the frame and land in a pile with two small rebounds |
| 3 | Giant captions (`giant-captions`) | the voice's own words, 1 to 3 at a time, 150 to 200 px in the middle; keywords in the accent |
| 4 | Prompt bar (`prompt-bar`) | an AI prompt box: the prompt types in, the send button presses, an optional reply line appears |
| 5 | Storyboard deck (`storyboard-deck`) | storyboard frames (shot number, sketch area, note) dealt from a deck into a fanned row |
| 6 | Icon strike (`icon-strike`) | one big featured icon in a highlight disc; a red strike crosses it; optional replacement icon |
| 7 | File drop (`file-drop`) | file cards drop into a dashed drop zone, a progress bar fills, a check lands |
| 8 | NLE timeline (`nle-timeline`) | an editor timeline: ruler, 2 to 3 tracks of clips, a playhead sweeping, razor cuts that ripple-close |
| 9 | Jiggle delete (`jiggle-delete`) | a grid of app-style tiles jiggles, delete badges appear, chosen tiles shrink away, the rest reflow |
| 10 | Grade slider (`grade-slider`) | a picture with grading sliders; each knob moves and the picture's grade follows (CSS filters) |
| 11 | Eyedropper grade (`eyedropper-grade`) | an eyedropper moves over a picture, a loupe shows the picked colour, a swatch lands, the grade tints toward it |
| 12 | Film look (`film-look`) | letterbox bars slide in, grain, vignette, a warm grade and a light-leak sweep over a picture |
| 13 | Title card (`title-card`) | a cinematic chapter card: kicker, big title, rules that draw out, a subtitle |
| 14 | Playing grid (`playing-grid`) | a grid of video tiles, each with a moving progress bar; one tile is picked and lifts |
| 15 | Reel feed (`reel-feed`) | a phone with a reels feed: the reel's caption, like/comment/share counts ticking, a swipe to the next |
| 16 | Video card (`video-card`) | a video player card: play turns to pause, the progress bar and timecode run, title and channel |
| 17 | Comment CTA (`comment-cta`) | "Comment KEYWORD": a comment box types the keyword, a big keyword chip, what the viewer gets |
| 18 | Comment drop (`comment-drop`) | comments drop in one by one (avatar, name, text, heart) and stack like a feed |
| + | Chat (`chat`) | a chat window: the question bubble, a typing dot row, the answer bubble with a cited source chip |
| + | Doc (`doc`) | a document page with lines of text; the matching passage highlights and a source tag lands |
| + | Stat (`stat`) | a hero figure ("8 HOURS", "+$363"): the number counts, the unit and label land; 200 to 320 px |

## Review Focus

1. A scene on the `blue` or `ink` background whose text or chip reuses a light-background colour (contrast).
2. A hook script whose first two words are a filler ("So, ...") — the hook still lands by 0.8 s and reads.
3. A storyboard written for the old 1420 bottom (a tall scene that no longer fits) — the error says what to drop.
4. A project on Windows: `python3` missing, cp1252 locale, `npx` being `npx.cmd`, `file://C:\...` URLs.
5. A rendered reel with long camera-free holds — E6 fails with the times.

---

### Task 1: Foundations (area, handover, hook, ceiling, hold time, discovery)

**Files:** `explainer_lib.py`, `explainer-compose.py`, `transitions.py`, `pace-check.py`, `layout_check.py`,
`layout-probe.mjs`, `scenes/__init__.py`, `dev/make-cases.py`, `tests/test_heights.py`; tests in `test_compose.py`,
`test_layout.py`, `test_pace.py`, `test_transitions.py`.

- `E.SCENE` bottom 1235, `E.PICTURE_BOTTOM` 1650, `E.EXIT` 0.2; narrow centre from the new area; scale may drop to
  0.8 when nothing fits at 1.0 (MIN_PX still guards legibility).
- Exits run `[t_out - EXIT, t_out]`; a host ends on `t_out`; E5 samples settle at `t_out - EXIT - 0.05`.
- E3 fails: voice over 90.0 s; any first-scene item after 0.8 s.
- E4 (`pace-check.py`): a scene over 8 s fails, over 6 s warns, unless `moments.scenes[i].travels`.
- E5 probe: text/card edges judged against 1235, text-free shapes against 1650; `handover` samples at every cut
  (−0.25 to +0.25 s, every 1/30 s): fail when both scenes show content at ≥ 0.3 opacity.
- Registry discovers `scenes/*.py` with a `TYPE`; cases load `dev/cases_*.py`; heights load `fixtures/heights*.json`.
- Tests: a 1300 px card fails E5 "outside"; a text-free shape at 1600 passes; two scenes cross-fading fail
  "handover"; a hook item at 1.2 s fails E3; a 91 s voice fails E3; a 9 s still scene fails E4; a new module file is
  in the registry without editing `__init__`.

### Task 2: Theme — blue and ink backgrounds, paper roles, contrast gate, background rhythm

**Files:** `tokens.json`, `explainer_lib.theme`, `layout-probe.mjs` (contrast), `plan-storyboard.py` (rhythm), every
scene that sets a colour; `test_theme.py`, `test_plan.py`, `test_layout.py`.

- Backgrounds carry their own `roles`, `series`, `highlight`, glows and `card` (with alpha) overrides.
- `theme()` adds `paper`, `paper_ink`, `paper_dim`, `paper_line` (constant light UI).
- Probe `contrast`: text colour vs the composited colour behind it, under 3:1 fails.
- Planner rhythm: the hook on `ink`, the payoff on `blue`, sections alternate `mantle`/`base`, and inside a long
  section every third scene switches to `blue`.
- Every scene case runs on a rotating background; all pass E5.

### Task 3: Motion — camera, particles, slots, travel, E6

**Files:** `explainer-compose.py` (cam wrapper, particles), `scenes/__init__.py` (slot/fill), the build scenes,
`scenes/flow.py` (travel), new `motion-check.py`; `test_living.py`, `test_scenes_build.py`, new `test_motion.py`.

- `.box > .cam > .live`: the cam drifts every scene (scale 1 → 1.03, y +8 → −8, yaw ±2.5°, sine.inOut over the
  scene) — ambient, never a pace change; `IDLE_ROOM` 24.
- A particle field per background layer (24 squares and dots, seeded, one slow tween each across the reel).
- `ctx.slot(sel)`: outline at 0.35, its `.gt` text hidden; `ctx.fill(sel, t)` brings both in. Replaces `ctx.ghost`.
- `flow`: 2 to 6 nodes; when the column is taller than the area it travels: a mover recentres on each node.
- `motion-check.py --video F [--max-still-share 0.15 --max-still 1.0]`: frames at 10 fps, 180x320 grey; a frame is
  still under 0.25/255 mean change; fails with the still stretches' times. (Ruling at the demo: a frame is still when under 0.1% of it changes by more than 5/255; the mean diluted small visible motion. Reference 3% still, the RAG reel 48%.)

### Task 4: Hook, captions, giant captions

**Files:** `scenes/kinetic.py` (`normalize`), `plan-storyboard.py`, `explainer-compose.py` (captions), new
`scenes/giant_captions.py`; `test_kinetic.py`, `test_plan.py`, `test_compose.py`.

- `kinetic.normalize`: a leading number/short-caps token in the first word piece becomes `big`.
- Pieces sharing a time land 0.1 s apart. The planner anchors line 0's pieces to words 0 and 1.
- Captions: an emphasised word is 1.15x with its handles; the caption band hides while `giant-captions` runs.

### Task 5: SOP tooling (S3, S4, S5, S10, S11, S12, S14, S16)

**Files:** new `preflight.py`, `stills.py`, `skill-version.py`, `new-version.py`; `tts-kokoro.py` (samples ≥ 10 s,
`voice-rates.json`), `script-check.py` (measured rate, pauses, sections, `--voice`); UTF-8, `npx`/`node` lookups and
`pathToFileURL` across the kit, Reels and Explainer scripts; lint tests that every text `open()` names its encoding.

- `script-check.py`: words per second from `voice-rates.json` for the script's voice and speed (default 2.4); the
  estimate adds the pauses; the word range comes from 30 to 90 s at that rate (a 90 s target is valid); more than
  3 section breaks per 75 s fails; `--voice voice.wav` reports the measured length and, over 90 s, fails with the
  trim candidates (lines other than the hook, payoff and CTA, longest first).
- `stills.py --index public/index.html --out snaps/stills`: clears the folder, one full-size still per scene at its
  settle moment, the hook at 0.3, 0.7 and 1.0 s, a contact sheet and `STILLS.md`.
- `skill-version.py [--pin STATUS.md | --check STATUS.md]`: the skill's content hash; `--check` fails when the skill
  changed since the pin (an update or a maker's edit).
- `new-version.py --project DIR`: moves `public/`, `snaps/`, renders and `deliver/` into `versions/vN/`.
- `preflight.py --out DIR`: the Python command, UTF-8 mode, tools found, the three suites run with `PYTHONUTF8=1`,
  failing tests by name; writes `PREFLIGHT.md`.

### Tasks 6 to 9: the new scenes (in parallel; one group each)

Each scene: `scenes/<name>.py` (TYPE, CSS, validate, height, min_width, render; `PAPER = True` for UI mock-ups),
three cases in `dev/cases_<group>.py`, measured heights in `fixtures/heights-<group>.json`, tests in
`tests/test_scenes_<group>.py` (validate errors, items on their words, the build composes, heights 0 to 4 px over
Chromium), and every case clean in E5 on its rotating background.

- Group A (type and social): gravity-drop, title-card, icon-strike, comment-cta, comment-drop.
- Group B (tools): prompt-bar, storyboard-deck, file-drop, nle-timeline, jiggle-delete.
- Group C (video and grade): grade-slider, eyedropper-grade, film-look, playing-grid, video-card, reel-feed.
- Group D (objects): chat, doc, stat.

### Task 10: Planner hints and docs (S1, S2, S6, S7, S9, S11, S13, S15, S16)

`plan-storyboard.py` list keys for the new scenes; `SKILL.md` (brief as a numbered message with defaults; inputs and
angle first; preflight; skill pin; versions; reconcile numbers; listening is the creator's; length decided at
Checkpoint A; settled stills; transcription at the first render QA), agents (makers report, the Librarian changes
scripts; measured vs estimated; drop a row, never split for height), `PLAYBOOK.md`, `MOTION.md`, READMEs, test counts.

### Task 11: Demo and comparison

Rebuild the RAG demo with the new scenes and backgrounds; render; E1 to E6 and `verify-render`; the motion and fill
metrics against the reference; a side-by-side sheet; send.

### Task 12: Final whole-branch review and fixes
