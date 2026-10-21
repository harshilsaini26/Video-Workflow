# Premiere hand-off and human-in-the-loop: design

Date: 2026-10-21. Status: approved in conversation (sections 1 and 2); this file is for the creator's review.

## 1. Intent

**What the creator asked for**
- No finished, rendered reel at the end of a run. Instead, a project the creator opens in **Adobe Premiere Pro** and
  finishes by hand, so the work keeps a human hand and costs fewer agent tokens.
- Applies to all three profiles: explainer, reels and long-form YouTube.
- Take the useful parts of three MIT-licensed repositories (sergebulaev/instagram-skills,
  Jakeschincariol/instagram-agent-skill, Anil-matcha/AI-Youtube-Shorts-Generator), as the six items in §5.

**Decisions taken with the creator**
- Explainer scenes reach Premiere as **separate transparent clips** (ProRes 4444 with alpha), one per scene, on
  their own track.
- Captions come two ways: an **editable `.srt`** imported as Premiere captions, and the **styled caption
  animation** as its own clip track, switched off by default.
- The full render stays as an **opt-in** command. Agents never run it unless the creator asks.

**Success looks like this**
- The creator imports one `.xml` into Premiere and gets the right sequence size and frame rate, every track, and
  every clip on its word.
- The raw camera files are cut without re-encoding.
- Every gate up to Checkpoint B still runs. The suites stay green.

**Assumptions**
- Premiere Pro 2020 or later on macOS or Windows.
- The creator copies or syncs the project folder to the editing machine. Premiere relinks by file name when paths
  differ.

## 2. The exchange format

**Final Cut Pro 7 XML** (`xmeml` version 4). Premiere imports it natively through File → Import, with no plugin.

**What it carries**
- One `<sequence>` with timebase and NTSC flag, width and height, and a 60 fps (or 30 fps long-form) timebase.
- Video and audio tracks, each with `enabled` on or off.
- `<clipitem>`s with `start`, `end`, `in` and `out` in frames, and a `<file>` holding a `pathurl` (`file://`,
  percent-encoded), the source duration and the source media's characteristics.
- Sequence markers (name and comment), clip opacity and audio levels.

**Rejected alternatives**
- Native `.prproj`: undocumented and version-fragile.
- CMX 3600 EDL: only one video track.
- OpenTimelineIO: needs a plugin.

**New shared module:** `Editing-Workflow/kit/youtube-edit/scripts/premiere_xml.py`, standard library only.

```
Timeline(name, width, height, fps)            # fps 60 or 30, integer timebase, ntsc FALSE
  .video_track(name, enabled=True) -> Track   # index = order added (V1 first)
  .audio_track(name, enabled=True) -> Track
  .marker(t, name, comment="")                # sequence marker
Track.clip(path, start, end, src_in=0.0, name=None, duration=None, opacity=None, level_db=None, position=None)
  # seconds in; frames out (round to the sequence timebase); duration = the source's length (probed by the caller)
Timeline.write(path) -> path                  # pretty-printed UTF-8 XML; one <file id> per distinct path
Timeline.validate() -> [problems]             # in <= out <= source duration, no overlap within a track, every path exists
```

## 3. The hand-off stage (all three profiles)

### 3.1 The new flow

The stage replaces **Render → QA render → Package** after Checkpoint B:

```
... Checkpoint B (stills approved) → Hand-off (new) → creator edits in Premiere → (optional) qa-export on the creator's export → Learn
```

### 3.2 The output folder

`videos/<project>/premiere/` holds:

| File | What it is |
|---|---|
| `<project>.xml` | the sequence |
| `media/` | voice, music and sound effects WAVs; `gfx/<id>.mov` (each scene, card or overlay as transparent ProRes 4444); `captions-styled.mov` |
| `captions.srt` | the editable captions |
| `HANDOFF.md` | each track and what is on it, the marker legend, how to relink, the checks still to run, and what is left to the creator |

The raw camera files are **referenced where they are** (the file the cut list was made on, from `ingest.json`).
They are not copied.

### 3.3 Tracks per profile

| Profile | Video tracks | Audio tracks |
|---|---|---|
| Explainer | V1 ground (the background colour and glows as one clip), V2 the thread, V3 scenes, V4 headlines, V5 styled captions (off) | A1 voice, A2 sound bed, A3 sound effects |
| Reels | V1 footage (the kept segments from `cut-list.json`, source in/out on the camera file), V2 b-roll, V3 cards and overlays, V4 styled captions (off) | A1 footage audio, A2 music, A3 sound effects |
| Long-form | as reels at 1920x1080 and the profile's frame rate, one sequence per project | as reels, with sections laid end to end |

Markers:
- the hook window;
- each scene or card on its anchor word, with its brief line and source;
- the Cutter's "check this cut" notes;
- chapter starts (long-form).

### 3.4 How the transparent clips are made

- **Explainer:** `explainer-compose.py --layers` writes one page per scene into `public/layers/<id>.html`. Each page
  holds the scene alone, on a transparent ground, timed from its in to its out.
  `hyperframes render public -c layers/<id>.html --format mov` writes `media/gfx/<id>.mov`. The ground, the thread,
  the headline and the styled captions are each one layer page too.
- **Reels and long-form:** the animator's composition already separates footage from overlays. The `--layers` mode
  of `reels-compose.py` writes each card or overlay as its own page, the same way.
- These are short pieces, not the reel. The Producer says how long they took to make.

### 3.5 Scripts

| Script | What it does |
|---|---|
| `handoff.py` (one per profile) | the explainer's `explainer/skill/explainer/scripts/handoff.py`, the reels' `reels/skill/reels/scripts/reels-handoff.py`, and long-form's use of the reels one with `--format 16x9`. Each maps the profile's existing data (storyboard, `moments.json`, `cut-list.json`, the sound events) onto `premiere_xml.Timeline`. |
| `handoff-check.py` (gate H1, in the kit) | parses the XML back. It checks that every `pathurl` exists, every clip is inside its source, the sequence settings match the profile, the voice track has no gap the transcript says is speech, every scene in the storyboard has its clip, and the `.srt` matches the transcript. FAIL names the clip. |
| `qa-export.py` (optional) | runs the existing checks on the creator's own Premiere export: loudness, size and frame rate, black frames, and the motion check (E6) for explainer. It reports only; it never edits. |

### 3.6 The opt-in render

- `wf.py render <project>` runs the existing render path, with E6 and `verify-render`, unchanged.
- The SKILL files say agents run it only when the creator asks.

## 4. More human input at the checkpoints

- **Checkpoint A, hook angles:** the Writer, or the Director for reels and long-form, offers 2 to 3 hook angles from
  a curated list of formulas that fit a faceless, sourced reel:
  - Nobody Tells You
  - Negative Command
  - Statistic
  - Head To Head
  - Superlative
  - Contrarian Flip
  - Numbered With A Favourite
  - If This Then Watch
  - Permission
  - Objection

  The creator picks one or rewrites it. The first-person "receipt" formulas are left out, because without a real,
  sourced number they push toward invented examples.
- **Wording notes:** wording findings (§5.1) are shown beside each line in `SCRIPT.md` or `CUT.md` as notes for the
  creator. Nothing is rewritten automatically.
- **Voice profile:** an optional `voice` section in the brief, filled only from 3 to 6 of the creator's real scripts or
  posts (rhythm, openers, words they never use, their call-to-action style). The Writer reads it when it is filled.
  It is never invented.
- **`POST.md`:** a draft for the creator to edit, checked by `post-check.py`.

## 5. The six items from the three repositories

### 5.1 Wording checks

**Module:** `kit/youtube-edit/scripts/wording.py`, run by:
- the explainer's script gate (E1, on `say` and `show`);
- the reels and long-form Cutter's gate (on the kept transcript text);
- `post-check.py`.

**FAIL on**
- leaked AI text (`oaicite`, `turn0search`, "as of my last update", "as an AI", template blanks like `[Your Name]`);
- invisible Unicode format characters (category Cf);
- a hook preamble in line 0: a greeting, "in this video/reel", "stop scrolling", or a hashtag or emoji in a spoken
  hook.

**WARN on**
- the curated phrase list: lead-ins ("here's the thing", "the result?", "let's dive in"), sincerity markers ("real
  talk", "honestly?"), closers and openers;
- the structure list: "it's not X, it's Y", "not just X but Y", the staccato run "No X. No Y. Just Z.";
- an em dash or `--` in spoken text (use a pause break instead);
- no number or proper name in the hook;
- a hook over 3.0 s, or any line over 4.0 s, at the voice's measured rate (explainer) or the real word times (reels
  and long-form);
- no content word shared by the last line and the hook (the loop hint; never a FAIL).

**Left out:** the over-broad single words ("compound", "significant", "robust", "landscape", "quietly") and the
word-triplet regex. Each list entry has one test that fires and one that must not misfire.

### 5.2 `post-check.py`

**Location:** `kit/youtube-edit/scripts/post-check.py`, run on `POST.md` by the reels and explainer packagers.

**FAIL on**
- a first line over 125 characters, or one starting with `#` or `@`;
- a caption over 2,200 characters;
- more than 5 hashtags, or a hashtag mid-sentence;
- engagement bait that gives nothing back ("tag 3 friends", "double tap", "comment YES" unless the keyword is the
  reel's comment call to action);
- a dead closer ("thoughts?", "what do you think?");
- leaked AI text;
- a number in the caption that is not a number sourced in `script.json` or the brief.

**WARN on**
- fewer than 3 hashtags;
- more than one ask;
- 4 or more emoji;
- the §5.1 phrase list.

### 5.3 `reels-moments.py`

**Location:** `reels/skill/reels/scripts/reels-moments.py`.

- `--windows` prints the long transcript as timed sentences in overlapping chunks. Times stay absolute.
- `--check moments.json` does the following:
  - validates `{start, end, score, hook, why, payoff}`;
  - snaps the edges to sentence and word boundaries;
  - enforces 15 to 60 s;
  - removes picks that overlap by more than 50%, keeping the higher score;
  - flags lines that need earlier context ("as I said", "earlier", "like I mentioned");
  - writes `MOMENTS.md` for the creator to pick from.
- `--scaffold` makes one project folder per picked moment.

The Director stays the judge. The repository's eight signals become the rubric in PLAYBOOK §R12, credited.

### 5.4 `wf.py`

**Location:** `Editing-Workflow/wf.py`, standard library only. It only calls existing scripts.

| Command | What it does |
|---|---|
| `install <profile> --to <dir>` | the copy steps from the README |
| `test [profile]` | each suite's own unittest command |
| `doctor` | `preflight.py` |
| `gates <project> --stage N` | that stage's gate scripts, in order |
| `handoff <project>` | the hand-off |
| `render <project>` | the opt-in render |

The READMEs point to it.

### 5.5 `reels-face-x.py`

**Location:** `reels/skill/reels/scripts/reels-face-x.py`. It needs the optional `opencv-python-headless`; its test
is skipped when that is missing.

- For each kept segment it samples frames and writes the median x of the largest face to `face-x.json`, or nothing
  for a segment with no face.
- `reels-handoff.py` turns that into each V1 clip's horizontal position. The creator can adjust it in Premiere.
- The Ingest value stays the fallback.

### 5.6 Playbook and docs

- **Explainer PLAYBOOK §E2:** a "Plain spoken words" rule (§5.1) and the over-correction guard: contractions and one
  natural list of three are fine; never add hedges or "honestly"; never add a number to sound human unless it is
  sourced.
- **Reels §R13 and the explainer SKILL hashtag lines:** one call to action that gives a reason, and hashtag tiers
  (2 to 3 niche, 1 to 2 mid, 0 to 1 broad, all on topic, rotated).
- **The voice profile** (§4).
- **A docs test for the reels kit,** modelled on the explainer's (frontmatter, cited scripts exist, § references
  resolve, links).
- **Credits:** each profile's RESEARCH file gets a credits section naming the three repositories (MIT) and what was
  taken. Each ported pattern list names its source in the file header.

## 6. What is not taken

- The hook score and its STRONG / OK / WEAK verdict. Its own README reports it cannot tell a creator's hits from their
  misses (AUC 0.56), and gibberish scores 100.
- `humanize.py`'s automatic rewriting. It changes meaning ("landscape" to "market").
- The detector score, and anything aimed at passing AI detectors. Our AI voice is disclosed.
- The paid services: MuAPI, OpenAI or Gemini keys, Publora, Apify.
- Their clipper, per-frame Haar tracking and chunked highlight code (it has an offset bug), and `yt-dlp` as an input.
- Unsourced numbers: algorithm weights, detector percentages, posting times, feed aspect ratios.

## 7. Errors, testing, what stays

**Errors**
- Every new script fails with the file and the item named, never a traceback, as the existing gates do.
- `handoff.py` stops before writing the XML if a scene's `.mov` is missing, and names the scene and the command that
  makes it.

**Tests (standard-library unittest, test first)**
- `premiere_xml`: the structure parsed back, frames from seconds at 60 and 30 fps, `pathurl` encoding (spaces, a
  `#`, a Windows path), one `<file>` per path, `validate()`.
- `handoff` (each profile): built from the existing test fixtures, with a fake `.mov` per scene; the track layout,
  every clip on its word, the markers.
- `handoff-check`: one passing case and one failing case per rule.
- `wording`, `post-check`, `reels-moments`, `wf`: fixtures for each rule. `reels-face-x` is skipped without OpenCV.
- The existing suites stay green.

**Manual check:** Premiere can't run here. A small sample project (about 3 s, two tracks, one marker) goes to the
creator to import, as the one check that cannot be automated.

**What stays as it is**
- Every gate up to Checkpoint B.
- The render path, now opt-in.
- E6 and `verify-render` on that render, and on `qa-export` of the creator's export.
