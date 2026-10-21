# Editor Hand-off (filmcraft) and Human-in-the-Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every profile (explainer, reels, long-form) ends at an editable project for filmcraft (FCP 7 XML, plus a
native `.fcproj` when `filmcraft-cli` is present) instead of a rendered reel. Wording checks, a post-caption check, a
moments finder, a speaker-position finder and one entry point are added from the three MIT repositories.

**Architecture:**
- One generic kit tool turns any composed HyperFrames page into transparent per-layer clips. Every profile's pages
  share the kit markup (`card-host` clips, `.cap-layer`, `.bg`, `svg.thread`, `#brand`, `#bg-video`).
- One kit module writes FCP 7 XML.
- One hand-off script per profile maps that profile's existing data onto the module: the storyboard, `moments.json`,
  `cut-list.json` and `ingest.json`.
- Gates up to Checkpoint B are unchanged. The render stays as an opt-in command.

**Tech Stack:** Python 3 standard library (unittest, xml.etree, json), HyperFrames 0.8.171
(`render --format mov`, ProRes 4444 with alpha), FFmpeg/ffprobe, filmcraft-cli (built from source, optional),
opencv-python-headless (optional).

**Spec:** `docs/superpowers/specs/2026-10-21-editor-handoff-design.md`

## Global Constraints

**Process**
- Free tools only; no paid APIs. Agents never render the full reel unless the creator asks (`wf.py render`).
- TDD with stdlib unittest. Commit only on a green suite for every profile touched.
- Commit messages end with:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01NHkfDqHcXZT9s2Fh2CLk3f`.
  No model identifiers in repo files.
- Develop and push on `claude/admiring-pascal-q7h8si`.

**Delivered project**
- Sequences: explainer and reels 1080x1920 at 60 fps; long-form at the recorded size and frame rate (3840x2160 at
  30 fps by default; 29.97 is timebase 30 with `ntsc` TRUE).
- FCP 7 XML `xmeml version="4"`. `pathurl` is a `file://` URL, absolute and percent-encoded.
- Raw camera files are referenced, never copied or re-encoded.
- Layer clips are `media/gfx/<name>.mov`, ProRes 4444 with alpha (`hyperframes render --format mov`).
- Output folder: `videos/<project>/edit/`, holding `<project>.xml`, `<project>.fcproj` (when `filmcraft-cli` is
  present), `captions.srt`, `HANDOFF.md` and `media/`.
- The styled-captions track is disabled (`<enabled>FALSE</enabled>`).

**Checks**
- Wording, FAIL:
  - leaked AI text;
  - invisible Unicode characters (category Cf);
  - a hook preamble (greeting, "in this video/reel", "stop scrolling", hashtag, emoji).
- Wording, WARN:
  - the phrase and structure lists;
  - an em dash or `--` in spoken text;
  - no number or name in the hook;
  - a hook over 3.0 s or a line over 4.0 s;
  - no shared content word between the last line and the hook (the loop hint; never a FAIL).
- `post-check`, FAIL:
  - a first line over 125 characters or starting with `#` or `@`;
  - a caption over 2,200 characters;
  - more than 5 hashtags, or a hashtag mid-sentence;
  - bait (except the reel's own comment keyword);
  - a dead closer;
  - leaked AI text;
  - an unsourced number.
- `post-check`, WARN: fewer than 3 hashtags, more than one ask, 4 or more emoji.
- `reels-moments`: 15 to 60 s; overlaps above 50% removed (higher score kept); context-leak phrases flagged.
- Credit `sergebulaev/instagram-skills`, `Jakeschincariol/instagram-agent-skill` and
  `Anil-matcha/AI-Youtube-Shorts-Generator` (all MIT) in each ported file header and in the RESEARCH credits.

**Test commands**
- kit: `cd Editing-Workflow/kit/youtube-edit/scripts && python3 -m unittest discover -s tests -t .`
- reels: `cd Editing-Workflow/reels/skill/reels/scripts && python3 -m unittest discover -s tests -t .`
- explainer: `cd Editing-Workflow/explainer/skill/explainer/scripts && python3 -m unittest discover -s tests -t .`
  (source `scratchpad/env.sh` first for the browser tests)

## Review Focus

1. A path with spaces, `#`, `%` or non-ASCII letters, or a Windows path, must import with every clip online
   (`test_pathurl_encoding`, Task 1).
2. Ingest joined several camera clips, and a kept segment spans the join. It becomes two timeline clips on the right
   files, with no gap and no overlap (`test_a_segment_across_two_clips_splits`, Task 5).
3. A layer whose host starts at 0 or ends at the composition's end must render its first and last frames
   (`test_edge_layers_keep_first_and_last_frame`, Task 3).
4. 29.97 fps long-form footage must keep its frames exact over 10 minutes, with no drift
   (`test_ntsc_frames_do_not_drift`, Task 1).
5. A hand-off run twice must not duplicate media or leave stale layer clips; the second run replaces the first
   (`test_rerun_replaces_the_edit_folder`, Task 4).

## Rulings made at planning (the creator may redirect)

1. **Shared modules live in the kit** (`kit/youtube-edit/scripts`), because every profile installs it.
   `explainer_lib.find_kit()` imports them the same way `find_reels_lib()` does.
2. **Headlines stay inside their scene clip.** They are inside the scene's host. The explainer tracks are:
   - V1 ground
   - V2 thread
   - V3 scenes
   - V4 brand (handle and PART n)
   - V5 styled captions (off)

   This replaces the spec's "V4 headlines".
3. **The sound effects get their own stem.** `sound.py` writes `music.wav` and `sfx.wav` as well as `bed.wav`, so
   A2 and A3 are separate. The bed mix is unchanged for the opt-in render.
4. **Agent notes become markers through `notes.json`.** The Cutter's and the Director's "check this" notes are a
   `notes.json` list `[{t, name, comment}]` in the project folder, and every hand-off turns them into markers.

---

### Task 1: `nle_xml.py`, the FCP 7 XML writer

**Files:**
- Create: `Editing-Workflow/kit/youtube-edit/scripts/nle_xml.py`
- Test: `Editing-Workflow/kit/youtube-edit/scripts/tests/test_nle_xml.py`

**Interfaces:**
- **Produces:**
  - `Timeline(name: str, width: int, height: int, fps: float)`. The fps is 60, 30, 25, 24, 29.97 or 59.94. 29.97
    and 59.94 give timebase 30 or 60 with ntsc TRUE.
  - `.video_track(name: str, enabled=True) -> Track` and `.audio_track(name, enabled=True) -> Track`, in the order
    added.
  - `.marker(t: float, name: str, comment="")`.
  - `Track.clip(path, start, end, src_in=0.0, name=None, duration=None, opacity=None, level_db=None, position=None)`.
    Times are in seconds. `duration` is the source length in seconds (required for a video file). `position` is
    `(x, y)` in the FCP Basic Motion centre convention.
  - `Timeline.frames(t: float) -> int`, which rounds to the sequence timebase. For ntsc rates the timebase frame
    count is `round(t * fps_exact)` with `fps_exact = 30000/1001` or `60000/1001`.
  - `Timeline.validate() -> list[str]` and `Timeline.write(path) -> path`.
  - `to_pathurl(path: str) -> str` (`file:///…`, percent-encoded, Windows drive letters as `file:///C:/…`).
  - `parse(path) -> dict`, the reader the tests and `handoff-check` use:
    `{name, width, height, timebase, ntsc, video: [{name, enabled, clips:[{name, start, end, in, out, pathurl}]}], audio: [...], markers: [{frame, name, comment}]}`.

- [ ] **Step 1: Write the failing tests** in `test_nle_xml.py`:
  - `test_round_trip_keeps_tracks_clips_and_markers`: a 1080x1920, 60 fps timeline with 2 video tracks (the second
    disabled), 1 audio track, 3 clips and 2 markers. After `write` then `parse`, the dict has the same sizes, the
    enabled flags, frame values, and marker frames and names.
  - `test_seconds_to_frames`: at 60 fps, 1.0 → 60 and 2.508 → 150. At 30, 0.034 → 1.
  - `test_ntsc_frames_do_not_drift`: 29.97 (timebase 30, ntsc TRUE), and 600.0 s → 17982 frames.
  - `test_pathurl_encoding`: `/a b/c#d%e/é.mov` → `file:///a%20b/c%23d%25e/%C3%A9.mov`; `C:\x\y z.mov` →
    `file:///C:/x/y%20z.mov`.
  - `test_one_file_element_per_path`: two clips of the same file give one `<file id>` with a full body and one
    reference.
  - `test_validate_names_each_problem`: a clip with out > duration; an overlap on one track; a missing file. Each
    problem string names the clip.
- [ ] **Step 2: Run, and see them fail.** Run the kit tests: `python3 -m unittest tests.test_nle_xml`. Expected:
  ModuleNotFoundError `nle_xml`.
- [ ] **Step 3: Implement `nle_xml.py`** with `xml.etree.ElementTree`, inside `<xmeml version="4"><sequence>`:
  - `<rate><timebase/><ntsc/></rate>`, `<media><video><format><samplecharacteristics>` with width and height;
  - `<track>` per track with `<enabled>`;
  - `<clipitem>` with `<start> <end> <in> <out>`, `<file id>`, `<pathurl>`, `<duration>`;
  - `<filter><effect><effectid>basic</effectid>` for position, `opacity` for opacity, and `audiolevels` for
    `level_db`;
  - `<marker><name><comment><in><out>-1</out>`.

  Write with an XML declaration and `<!DOCTYPE xmeml>`.
- [ ] **Step 4: Run, and see them pass.** Then run the whole kit suite: green.
- [ ] **Step 5: Commit** (`nle_xml: the FCP 7 XML writer for the editor hand-off`).

### Task 2: `filmcraft-cli`, built and wrapped

**Files:**
- Create: `Editing-Workflow/kit/youtube-edit/scripts/filmcraft.py`
- Test: `kit/.../tests/test_filmcraft.py`
- Modify: `Editing-Workflow/kit/README.md` (how to get `filmcraft-cli`: a release, or
  `cargo build --release -p filmcraft-cli` in a filmcraft checkout)

**Interfaces:**
- **Consumes:** `nle_xml.Timeline` and `nle_xml.parse` (Task 1).
- **Produces:**
  - `find_cli() -> str | None` (`$FILMCRAFT_CLI`, then the PATH);
  - `to_project(xml_path, srt_path, out_fcproj) -> dict`, the CLI's JSON result;
  - `inspect(fcproj) -> dict`, the `inspect sequence` JSON.
  - Both raise `FilmcraftError(msg)` with the CLI's stderr.

- [ ] **Step 1: Build `filmcraft-cli`** in the scratchpad: clone `storytold/filmcraft`, then
  `cargo build --release -p filmcraft-cli` (run it in the background; it can take a long time). Expected: the binary
  `target/release/filmcraft-cli`. If the build cannot finish, write a ledger ruling and go on. The tests below skip
  without the binary.
- [ ] **Step 2: Find the commands.** Use `filmcraft-cli commands import`, `filmcraft-cli describe file.import`, and
  the caption import command (`filmcraft-cli commands caption`). Ledger the exact command lines that create a project
  from an FCP 7 XML and an `.srt`, and that save it.
- [ ] **Step 3: Write the failing tests** (skipped when `find_cli()` is None):
  - `test_xml_becomes_a_project_with_every_clip_online`: build a 2 s, 1080x1920, 60 fps timeline from two tiny
    ffmpeg test files (a `testsrc` ProRes 4444 `.mov` with alpha, and a sine `.wav`), plus one marker and a two-cue
    `.srt`. Then `to_project` and `inspect` must show:
    - the sequence size and frame rate;
    - 2 tracks with 1 clip each, on their frames;
    - the marker;
    - 2 captions;
    - `offlineMedia == []`.
  - `test_a_bad_xml_is_named`: a damaged file raises `FilmcraftError` with the file name.
- [ ] **Step 4: Run, and see them fail** (`ModuleNotFoundError filmcraft`, or skipped when no binary).
- [ ] **Step 5: Implement** with `subprocess.run([cli, ..., "--json"])`, using the commands from Step 2.
- [ ] **Step 6: Run, and see them pass.** Run the whole kit suite. Commit
  (`filmcraft: make a native project from the hand-off XML, and read it back`).

### Task 3: `layer-pages.py` and `render-layers.py`, transparent clips from any composed page

**Files:**
- Create: `kit/youtube-edit/scripts/layer-pages.py` and `kit/youtube-edit/scripts/render-layers.py`
- Test: `kit/.../tests/test_layers.py`

**Interfaces:**
- **Produces:**
  - `layer-pages.py --index public/index.html --out public/layers [--layers layers.json]` writes
    `public/layers/<name>.html` and `public/layers/layers.json` as `[{name, track, t_in, t_out, page}]`.
  - The default layer groups, by selector:
    - `ground`: `.bg`
    - `thread`: `svg.thread`
    - `brand`: `#brand`
    - `captions`: `.cap-layer` without `#brand`
    - one layer per `.card-host` (its id without `host-`), with its own `t_in` and `t_out` from `data-start` and
      `data-duration`
  - `#bg-video`, `video.cutaway-video` and `<audio>` are removed from every layer page. Footage and sound reach the
    editor as their own clips.
  - `render-layers.py --public public --layers public/layers/layers.json --out edit/media/gfx [--workers N]` runs
    `npx --no-install hyperframes render public -c layers/<name>.html --format mov --fps <fps> -o <out>/<name>.mov`
    for each layer. It then prints one line per clip with its ffprobe `pix_fmt`; a clip whose `pix_fmt` lacks alpha is
    a failure.

- [ ] **Step 1: A spike.** On the demo page (`scratchpad/demo3/public`), write one layer page by hand: scene `l3`
  alone, on a transparent ground. Then:
  - set `data-duration` to the host's span and shift every `data-start` by `-t_in`;
  - wrap the timeline: `const M = gsap.timeline({paused:true}); M.add(tl.tweenFromTo(t_in, t_out, {ease:'none'}), 0); window.__timelines[id] = M;`;
  - render it with `--format mov`.

  Expected: `ffprobe` shows `prores`, `yuva444p12le` (or another `yuva*`), and a duration equal to the span. Ledger
  the working recipe; if the wrapper fails, ledger the ruling that replaces it.
- [ ] **Step 2: Write the failing tests:**
  - `test_one_page_per_host_and_per_group`: on a fixture page (two hosts, a `.bg`, a `.cap-layer` with `#brand`, an
    `svg.thread`, a `#bg-video`, two `<audio>`), the layers are `ground`, `thread`, `brand`, `captions` and the two
    hosts, with the hosts' times.
  - `test_a_layer_page_shows_only_its_layer`: in `l1.html`, every other group is `display:none` by an injected rule;
    `body` and `html` have a transparent background; there is no `<video>` or `<audio>`.
  - `test_times_are_shifted_to_the_layer`: the root `data-duration` is the span; every clip's `data-start` is minus
    `t_in`; the page registers the wrapper timeline under the composition id with `tweenFromTo(t_in, t_out`.
  - `test_edge_layers_keep_first_and_last_frame`: a host at 0 and one ending at the composition's end keep
    `t_in == 0` and `t_out == D`.
  - `test_render_writes_alpha_movs` (needs Chrome and HyperFrames, as the explainer browser tests do): render a
    0.5 s fixture layer, then check that `pix_fmt` starts with `yuva` and the duration is within one frame.
- [ ] **Step 3: Run, and see them fail. Implement both scripts.** `layer-pages.py` uses `html.parser`-free string
  surgery on the kit's own markup, the same way `compose.py` writes it; ids and classes are fixed by that markup.
- [ ] **Step 4: Run the kit suite: green. Commit** (`layer-pages: any composed page as transparent per-layer clips`).

### Task 4: The explainer hand-off

**Files:**
- Create: `Editing-Workflow/explainer/skill/explainer/scripts/handoff.py`
- Modify:
  - `explainer/skill/explainer/scripts/sound.py` (`mix_bed` also writes the stems)
  - `explainer-compose.py:550-562` (writes `music.wav` and `sfx.wav`; `moments["sounds"]` unchanged)
  - `explainer_lib.py` (`find_kit()`)
- Test: `explainer/.../tests/test_handoff.py`

**Interfaces:**
- **Consumes:** `nle_xml.Timeline`, `nle_xml.parse`, `filmcraft.find_cli` and `filmcraft.to_project` (Tasks 1 and 2);
  `layers.json` from Task 3; `reels_lib.chunk_words` and `reels_lib.to_srt`.
- **Produces:**
  - `handoff.py --project videos/<p> [--no-render]`, which writes `edit/` as in the Global Constraints. With
    `--no-render`, it expects `edit/media/gfx/*.mov` to exist (tests make them with ffmpeg).
  - The tracks, in order:
    - V1 ground
    - V2 thread
    - V3 scenes (one clip per host, on its `t_in`)
    - V4 brand
    - V5 styled captions (disabled)
    - A1 voice
    - A2 music
    - A3 sfx
  - The markers:
    - "Hook" at 0, with the comment "whole by 1.0 s";
    - one per scene at its `t_in`, named `<id> · <type>`, with the comment holding the scene's anchor word and its
      `source`;
    - every `notes.json` entry.

- [ ] **Step 1: Write the failing tests:**
  - `test_tracks_and_order`: compose the BOARD fixture, write fake `.mov` files, run `handoff.py --no-render`, then
    `parse` the XML and check the 5 video tracks (V5 disabled) and 3 audio tracks.
  - `test_every_scene_lands_on_its_frame`: each V3 clip's start equals `frames(moments.scenes[i].in)`.
  - `test_markers_carry_anchor_and_source`.
  - `test_captions_srt_matches_the_transcript`: the cue count and the first and last times come from `to_srt`.
  - `test_stems_are_written`: `music.wav` and `sfx.wav` sum to `bed.wav`, minus the voice ducking, within -40 dB
    RMS.
  - `test_missing_layer_clip_is_named`: delete one `.mov`; the exit code is 1, and stdout names the scene and the
    `render-layers.py` command.
  - `test_rerun_replaces_the_edit_folder`: run twice; there is one XML and no stale `.mov` from a removed scene.
- [ ] **Step 2: Run, and see them fail. Implement it.** Without `--no-render`, `handoff.py` runs `layer-pages.py`
  then `render-layers.py`. When `filmcraft.find_cli()` finds the CLI, it writes the `.fcproj`. It writes
  `HANDOFF.md`: a track table, the marker legend, relinking (filmcraft: File ▸ Link Media), the checks to run on
  export (`qa-export.py`), and what is left to the creator.
- [ ] **Step 3: Run the explainer suite: green. Commit** (`explainer: hand off an editable project, not a render`).

### Task 5: The reels and long-form hand-off

**Files:**
- Create: `Editing-Workflow/reels/skill/reels/scripts/reels-handoff.py`
- Test: `reels/.../tests/test_handoff.py`

**Interfaces:**
- **Consumes:** Tasks 1 to 3; `cut-list.json` (`kept: [{start,end}]` in source time); `ingest.json`
  (`clips: [{path, duration, source_start, width, height, fps_exact}]`); `face-x.json` from Task 10 (optional).
- **Produces:**
  - `reels-handoff.py --project videos/<p> [--section DIR ...] [--format 9x16|16x9] [--no-render]`. Without
    `--section`, the project folder is the one section.
  - The tracks:
    - V1 footage (the kept segments mapped to camera clips);
    - V2 b-roll (`cutaway-video` sources with their `data-media-start`);
    - V3 cards (one layer clip per host);
    - V4 styled captions (disabled);
    - A1 footage audio (linked to V1);
    - A2 music;
    - A3 sfx (the page's `<audio>` elements as clips).
  - The sections are laid end to end, with a chapter marker at each section's start (16x9).

- [ ] **Step 1: Write the failing tests:**
  - `test_kept_segments_map_to_camera_files`: two fake camera clips (ffmpeg `testsrc`, 3 s each), an `ingest.json`
    with `source_start` 0 and 3, and `kept` [0.5–1.5] and [3.2–4.0]. V1 then has clips on clip A at `in` 0.5 and on
    clip B at `in` 0.2, back to back.
  - `test_a_segment_across_two_clips_splits`: kept [2.5–3.5] gives two V1 clips (A 2.5–3.0 and B 0.0–0.5) with no
    gap.
  - `test_no_reencode_raw_is_referenced`: the V1 `pathurl`s are the raw paths, and `media/` holds no copy of them.
  - `test_longform_sections_and_chapters`: two sections at 16x9 and 3840x2160, 30 fps; the second section starts
    where the first ends; there is one chapter marker per section.
  - `test_face_x_sets_position`: with a `face-x.json` of `{segment index: 0.30}`, that V1 clip's position x is
    -0.20 (centre convention). Without the file, there is no position filter.
- [ ] **Step 2: Run, and see them fail. Implement it** (the shared marker, `notes.json`, `HANDOFF.md` and `.fcproj`
  steps as in Task 4).
- [ ] **Step 3: Run the reels suite: green. Commit** (`reels and long-form: hand off an editable project on the camera files`).

### Task 6: Gate H1 `handoff-check.py`, and `qa-export.py`

**Files:**
- Create: `kit/youtube-edit/scripts/handoff-check.py` and `kit/youtube-edit/scripts/qa-export.py`
- Test: `kit/.../tests/test_handoff_check.py`

**Interfaces:**
- **Consumes:** `nle_xml.parse`.
- **Produces:**
  - `handoff-check.py --edit videos/<p>/edit --profile explainer|reels|longform [--transcript transcript.json] [--storyboard storyboard.json]`.
    It prints `H1 PASS` or one `H1 FAIL: <clip or file>: <why>` line per problem, and exits 0 or 1.
  - `qa-export.py --video <creator export> --profile …` prints the existing checks (loudness via ffmpeg `ebur128`,
    size and frame rate, black frames, E6 for explainer by calling `motion-check.py` when present). It only reports
    and always exits 0, with a summary line.

- [ ] **Step 1: Write the failing tests**, one passing and one failing case per rule:
  - `test_missing_media_fails`
  - `test_clip_outside_source_fails`
  - `test_wrong_sequence_settings_fail`
  - `test_voice_gap_under_speech_fails`: an A1 hole where the transcript has words
  - `test_scene_without_clip_fails`
  - `test_srt_mismatch_fails`
  - `test_clean_handoff_passes`
- [ ] **Step 2: Run, and see them fail. Implement both. Run the kit suite. Commit**
  (`handoff-check (H1) and qa-export on the creator's own export`).

### Task 7: `wording.py`, and its use in the script and cut gates

**Files:**
- Create: `kit/youtube-edit/scripts/wording.py` and `kit/youtube-edit/scripts/wording.json`. The json holds the
  lists, each entry with its source repository.
- Modify:
  - `explainer/skill/explainer/scripts/script-check.py` (calls `wording.check_lines` on every line's `say` and
    `show`; fails and warnings as in the Global Constraints)
  - `explainer/skill/explainer/scripts/explainer_lib.py` (`find_kit`, from Task 4)
- Test: `kit/.../tests/test_wording.py` and `explainer/.../tests/test_script_check.py`

**Interfaces:**
- **Produces:**
  - `check_lines(lines: list[dict(text, say=None, dur=None)], hook_index=0) -> {"fail": [str], "warn": [str]}`.
    Each message starts with `line <n>:`.
  - `wording.py --script script.json [--voice-rate R]` or `--transcript transcript.json --kept cut-list.json`. It
    prints `WORDING PASS|FAIL` and the messages, and exits 1 on a fail.

- [ ] **Step 1: Write the failing tests:**
  - `test_each_fail_pattern_fires`: for each entry in `wording.json["fail"]`, its example sentence fails.
  - `test_each_warn_pattern_fires_and_its_lookalike_does_not`: every warn entry carries an `example` and a
    `lookalike` in the json, and both are tested. The lookalikes include "landscape mode", "compound interest", "a
    statistically significant result", "it's not working", and "Comment CABLE and I'll send you the list".
  - `test_invisible_characters_fail`: U+200B, U+FEFF and U+2060 in `say`.
  - `test_hook_timing`: a hook of 9 words at 2.4 words a second (3.75 s) warns; one of 6 words passes.
  - `test_loop_hint`: the last line sharing "cables" with a hook that has "cable" does not warn; no shared word
    warns.
  - In `test_script_check.py`: `test_wording_fails_block_e1` and `test_wording_warnings_reach_SCRIPT_md`.
- [ ] **Step 2: Run, and see them fail. Implement. Run the kit and explainer suites. Commit**
  (`wording: plain spoken words, checked at E1 and on the cut`).

### Task 8: `post-check.py`

**Files:**
- Create: `kit/youtube-edit/scripts/post-check.py`
- Test: `kit/.../tests/test_post_check.py`

**Interfaces:**
- **Consumes:** `wording.check_lines` for the shared lists.
- **Produces:** `post-check.py --post POST.md [--script script.json] [--brief BRIEF.md] [--keyword WORD]`. It prints
  `POST PASS|FAIL`, and exits 0 or 1.

- [ ] **Step 1: Write the failing tests**, one per rule in the Global Constraints:
  - `test_first_line_over_125_fails`
  - `test_first_line_hashtag_fails`
  - `test_over_2200_fails`
  - `test_six_hashtags_fail`
  - `test_mid_sentence_hashtag_fails`
  - `test_bait_fails_but_own_keyword_passes`
  - `test_dead_closer_fails`
  - `test_unsourced_number_fails_sourced_passes`: numbers are matched after normalising "1,000", "1k" and "one
    thousand" against the script's `show` and `sources`.
  - `test_warnings_do_not_fail`
- [ ] **Step 2: Run, and see them fail. Implement. Run the kit suite. Commit**
  (`post-check: the post caption checked before the creator posts`).

### Task 9: `reels-moments.py`

**Files:**
- Create: `reels/skill/reels/scripts/reels-moments.py`
- Test: `reels/.../tests/test_moments.py` (fixture: `tests/fixtures/long-transcript.json`, about 6 minutes of word
  times)

**Interfaces:**
- **Produces:**
  - `--transcript T --windows [--minutes 8 --overlap 1]` prints timed sentences per window, in absolute times.
  - `--transcript T --check moments.json --out MOMENTS.md` validates, snaps, deduplicates and flags, and exits 1 on
    a hard problem.
  - `--check moments.json --scaffold videos/` creates `videos/<long>-reel-<n>/` with a `cut-list.json` seeded from
    the moment.
  - The schema is `[{start, end, score (0–100), hook, why, payoff}]`.

- [ ] **Step 1: Write the failing tests:**
  - `test_windows_keep_absolute_times`: the second window's first sentence starts at its real time.
  - `test_edges_snap_to_sentences`: start 61.3 inside a sentence snaps to that sentence's first word; end snaps to a
    sentence end.
  - `test_length_bounds`: 12 s and 75 s each fail with the moment named.
  - `test_overlap_keeps_higher_score`: two moments overlapping 60% keep the higher score; at 40% both stay.
  - `test_context_leak_flagged`: "as I said" in a moment warns.
  - `test_scaffold_writes_cut_lists`.
- [ ] **Step 2: Run, and see them fail. Implement it** (sentence ends via `reels_lib.ends_sentence`). Add the
  eight-signal rubric to PLAYBOOK §R12, credited. **Run the reels suite. Commit**
  (`reels-moments: picks from a long video, checked and snapped`).

### Task 10: `reels-face-x.py`

**Files:**
- Create: `reels/skill/reels/scripts/reels-face-x.py`
- Test: `reels/.../tests/test_face_x.py` (skipped without `cv2`)

**Interfaces:**
- **Produces:** `--source <camera file or source.mp4> --cut-list cut-list.json [--ingest ingest.json] --out face-x.json`.
  The output is `{segment index: x}`, where x is 0 to 1 of the frame width, the median of the largest face's centre
  over 5 frames per segment. A segment with no face is left out.

- [ ] **Step 1: Write the failing tests:**
  - `test_segments_without_faces_are_omitted`: on ffmpeg `testsrc`, the result is `{}`.
  - `test_the_median_of_samples`: a stubbed detector returns x = 0.2, 0.3, 0.3, 0.9, 0.3, and the result is 0.3.
- [ ] **Step 2: Run, and see them fail. Implement** (Haar `haarcascade_frontalface_default.xml` from `cv2.data`).
  **Run the reels suite. Commit** (`reels-face-x: the speaker's place per segment, for the editor`).

### Task 11: `wf.py`, one entry point

**Files:**
- Create: `Editing-Workflow/wf.py` and `Editing-Workflow/tests/test_wf.py`

**Interfaces:**
- **Consumes:** the existing scripts only.
- **Produces:**
  - `install <profile> --to <dir>`
  - `test [profile]`
  - `doctor`
  - `gates <project> --stage N --profile P`
  - `handoff <project> --profile P`
  - `render <project> --profile P` (prints "opt-in render" first)
  - `--dry-run` prints the commands instead of running them.

- [ ] **Step 1: Write the failing tests:**
  - `test_install_dry_run_lists_the_readme_copy_steps`: for each profile it matches the README's commands.
  - `test_test_runs_each_suite_command`: dry run.
  - `test_handoff_routes_by_profile`.
  - `test_render_says_opt_in`.
  - `test_unknown_profile_is_named`.
- [ ] **Step 2: Run, and see them fail. Implement. Run the tests. Commit** (`wf.py: one entry point for every profile`).

### Task 12: The flow, the agents and the docs

**Files:**
- Modify:
  - `explainer/skill/explainer/SKILL.md`, `reels/skill/reels/SKILL.md` and `longform/skill/youtube-longform/SKILL.md`.
    The stage tables replace Render, QA render and Package with Hand-off (H1) → the creator edits → optional
    `qa-export`; the render becomes opt-in; Checkpoint A offers 2 to 3 hook angles; the brief gets a `voice` profile
    question.
  - `explainer/agents/explainer-writer.md`: hook angles from the curated ten; wording notes; the voice profile; the
    over-correction guard.
  - `reels/agents/reels-packager.md` and the explainer packaging section: `POST.md` is a draft, run through
    `post-check.py`; call to action with a reason; hashtag tiers.
  - `reels/agents/reels-cutter.md` and `longform/agents/longform-cutter.md`: after the cut, run
    `wording.py --transcript transcript.json --kept cut-list.json`, and list its notes in `CUT.md` for Checkpoint A.
  - The renderer, QA and assembler agent files: marked opt-in.
  - `explainer/skill/explainer/PLAYBOOK.md` §E2 ("Plain spoken words", the over-correction guard) and
    `reels/skill/reels/PLAYBOOK.md` §R12 and §R13.
  - The RESEARCH credits in all three profiles.
  - READMEs: root, `Editing-Workflow/`, and each profile (the hand-off, filmcraft, `wf.py`, test counts).
- Create: `reels/skill/reels/scripts/tests/test_docs.py`, modelled on the explainer's (frontmatter, cited scripts
  exist, § references resolve, relative links).
- Test: each profile's docs test.

- [ ] **Step 1: Write the failing docs test for reels**, and extend the explainer's:
  - `test_stage_table_ends_in_handoff`: no stage named Render without "(opt-in)".
  - `test_cited_scripts_exist`: this covers `handoff.py`, `post-check.py`, `wording.py` and `wf.py`.
- [ ] **Step 2: Run, and see them fail. Make the doc changes. Run all suites. Commit**
  (`docs: the hand-off flow, hook angles, the voice profile, credits`).

### Task 13: The demo hand-off, end to end

**Files:** none in the repo. The scratchpad holds `demo3/edit/`.

- [ ] **Step 1:** Run `wf.py handoff <scratchpad>/demo3 --profile explainer`. This renders the layer clips only, not
  the reel.
- [ ] **Step 2:** Run `handoff-check.py --edit demo3/edit --profile explainer`. Expected: H1 PASS.
- [ ] **Step 3:** If `filmcraft-cli` was built: import, then `inspect`. Expected: every clip online, 5 video tracks
  and 3 audio tracks, the markers, and the captions. Take a screenshot with `filmcraft-cli render_preview` if
  available (one frame at 5 s).
- [ ] **Step 4:** Send the creator `demo3/edit/` zipped (XML, `.fcproj`, srt, `HANDOFF.md`, media), plus the
  preview frame.
- [ ] **Step 5:** The final whole-branch review on the most capable model, then fix the Critical and Important
  findings test-first, then run every suite and push.
