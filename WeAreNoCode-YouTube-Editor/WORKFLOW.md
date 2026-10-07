# The workflow

How a video goes from the camera to a finished file with this kit. It is pieced together from `youtube-edit/SKILL.md`
(the rulebook Claude follows), the scripts in `youtube-edit/scripts/`, `STYLE-GUIDE.md`, `SETUP.md` and `PROMPTS.md`.

There are two lanes:

- **Lane A: YouTube (16:9, 4K, 30 fps).** What the kit was built for. Every step below works today.
- **Lane B: Reels (9:16, 1080x1920, 60 fps, free tools only).** Most steps work today; the animation step needs
  building first. See the end of this file.

```
 Record ─► Ingest ─► Cut ─► ✋ Checkpoint A ─► Plan ─► ✋ Checkpoint B ─► Render ─► Verify ─► Assemble ─► Deliver
  you      Claude   Claude   you read the cut   Claude   you read the stills  Claude    Claude    Claude     Claude
                                                                                                             │
                     ┌───────────────────────── "Save this to the skill" ◄── you give notes ◄────────────────┘
                     ▼
               SKILL.md gets one new rule; the next video starts from it
```

You do three things: record, answer at the two checkpoints, and give notes on the finished draft. Claude does the rest.

---

## 0. One-time setup

Follow `SETUP.md` steps 1 to 6, then type the install prompt from `PROMPTS.md`. Claude checks and installs:

| Tool | Job | Cost |
|---|---|---|
| Claude Code (desktop app, Local, your project folder) | runs everything | paid plan ($20 to set up; editing uses more) |
| Node.js 22+ and the HyperFrames CLI (`npx hyperframes`) | draws the animations, renders the video, transcribes | free |
| Parakeet (`npx hyperframes models install parakeet`) | every word with its time | free |
| FFmpeg + ffprobe | cutting, encoding, checks | free |
| Python 3 + numpy | the scripts | free |
| auto-editor | where you speak, by the audio | free |
| Google Chrome | snapshots, page captures | free |
| Tella, Epidemic Sound (connectors) | screen recordings, music and sound effects | paid, **optional** |

Then the tests, from the scripts folder: `cd .claude/skills/youtube-edit/scripts && python3 -m unittest tests`.
It must end with `OK` (31 tests). Run them again after changing any script.

Commands below use `SK=".claude/skills/youtube-edit"` and `W="videos/<project>"` (one folder per video).

---

## 1. Record (you)

- 4K, 30 fps, flat: no in-camera zooms, captions or transitions. Mic on every file. A second of silence at each end.
- **Fluffed a line? Pause about two seconds and say the whole sentence again.** The last take wins.
  "Cut that" or "scratch that" drops what came before it.
- No spoken notes to yourself (they are speech and get kept). Clap instead.
- Say lists as lists, name tools out loud (logos come from the name), say money in full ("a thousand dollars a month").
- Tutorials as two files: face and screen at once, both with the mic, one clap, the same file name.

## 2. Ingest (Claude)

Pick the route by what you hand over:

| You hand over | Route |
|---|---|
| One raw clip, 1 to 3 min (a hook, an intro) | Cut → storyboard → render |
| Several raw clips for one video | `ingest.py` orders and joins them into `source.mp4`, then the same |
| A talking section over 3 min | Cut + `stutter-scan.py` + `CUT-REVIEW.html`, storyboard under the long-form rules, render per section |
| A flat cut you already made | skip to Plan |
| Face file + screen file | `sync-tracks.py` lines them up; the screen becomes full-frame cutaways |
| A Tella recording | the Tella route in SKILL.md (cut locally, layouts and zooms through the connector) |
| Every finished piece of one video | `assemble.py` |

## 3. Cut: raw clip to flat cut (Claude)

| Step | Script / tool | What it does |
|---|---|---|
| 1 | `ffmpeg` → `audio-raw.wav` | 16 kHz mono audio for transcription |
| 2 | `npx hyperframes transcribe --engine parakeet` | every word with its time (`transcript-raw.json`) |
| 3 | `auto-editor` | speech chunks by loudness (`speech.v1`) |
| 4 | `paper-cut.py` | keeps the last take of each line, drops restarts, "cut that", false starts, long pauses → `cut-list.json` + **`PAPER-CUT.md`** |
| 5 | `hand-cut.py` (only if needed) | fixes misreads: a list read as restarts, a retake with a wrong number |
| 6 | `tighten-cut.py` | trims lead-ins, tails and inner pauses by the sound |
| 7 | `sliver.py --fix` | removes breaths and leftovers of dropped takes |
| 8 | `edge-audit.py --fix`, then again until **0 issues** | every cut edge checked by ear (the audio), not by the transcript |
| 9 | `apply-cut.py` | one frame-accurate encode → `public/input-video.mp4` + `cut-map.json` (every jump cut) |
| 10 | transcribe again | `transcript.json`, now in flat-cut time |
| 11 | `dead-air.py --plan` → `patch-cut.py --drop-flat` → back to 8 | loops until **0 pauses** over 0.40 s |

### ✋ Checkpoint A: the cut (you)

Read `PAPER-CUT.md` (and `CUT-REVIEW.html` on long sections). Answer in plain words:
"keep the earlier take of the studio line", "the joke at 1:12 goes". Claude re-runs the loop above.

## 4. Plan: flat cut to storyboard (Claude)

Claude reads `transcript.json` and `cut-map.json` and writes `storyboard.json`, the plan and the source in one file.

- **Formats:** more than 40 in the library (lower line, glass card, logo card, site cutaway, pills, world camera, chat...).
  Explainers are found in the transcript, not requested ("first / second / third", "the way this works is").
  Never the same device twice in a row; a tie goes to the one used least. Diagrams are proposed to you before building.
- **Timing:** every element enters on its word, 0.15 to 0.25 s ahead of it.
- **Camera:** top-anchored zooms, `set 1.0` at every jump cut, punch-ins 118 to 125 %, slow creeps 110 to 112 %.
  About 7 overlays and 7 camera moves per 90 s.
- **Sound:** silence by default; a pop on a logo, a click on a cursor click, typing on typing. Never a whoosh under text.
- **B-roll:** a person or job you name gets 2.5 to 3.5 s of stock footage (Pexels first, free), conformed with
  `broll-conform.py`.
- **The hook gate:** the first 3 s sell the video, it works muted, and the promise has a payoff time (`loops`).

Then the checks, all before any render:

| Step | Script / tool | Fails when |
|---|---|---|
| 1 | `compose.py --spec storyboard.json --out public` | bad input (overlapping camera moves, made-up quotes, unknown icons); warns on a device used twice in a row |
| 2 | `npx hyperframes check public` | the composition breaks HyperFrames' rules |
| 3 | `beat-check.py` | an element lands too early or late on its word, or has no word; the transcript is out of date |
| 4 | `gap-scan.py` (long form) | over 15 s with nothing on screen in the first 90 s, 20 s after, 30 s ever |
| 5 | `snap-beats.py` | (never fails) one still per moment, tiled into `snaps/sheet.png` |

### ✋ Checkpoint B: the plan (you)

Look at `snaps/sheet.png` and the storyboard. A snapshot takes seconds and a render takes minutes, so this is the cheap
place to change things. Notes like "the card covers my face at 0:14" become one number changed in the storyboard.

## 5. Render and verify (Claude)

| Step | What | Why |
|---|---|---|
| 1 | `npx hyperframes render --resolution 4k --video-bitrate 45M` | the 1920x1080 composition renders at 2x; ~1 min per 30 s |
| 2 | `ffmpeg -c copy` with BT.709 tags | the render drops colour tags; faces look redder without them |
| 3 | `verify-render.py` (+ `--words` / `--kept`) | black frames and flashes, size, tags, bitrate, duration, A/V sync, clipped words. **Exit 1 = do not deliver** |

Long renders (over ~2 min): one worker, streaming encode, segmented capture. The settings are in SKILL.md under
"Traps that waste a render". A note on a long render costs a patch (`window-patch.py`), not a full re-render.

## 6. Assemble (Claude, when a video has several parts)

`assemble.py --manifest assembly.json` joins the hook, intros, sections and tutorials into one master: every part
levelled to -14 LUFS, optional ducked music, BT.709 tags, plus `ASSEMBLY.md` and `chapters.txt` for the description.
The master is never edited by hand; changes go in the manifest and it runs again.

## 7. Deliver (Claude)

Into `~/Movies/YouTube Renders/<project>/`: the MP4, `STORYBOARD.md` (`storyboard-md.py`: what is on screen when,
every stock clip with its licence) and `PAPER-CUT.md`. Claude reports what it added and its own concerns.

## 8. Notes, and the learning loop (you, then Claude)

1. Watch the whole draft first, then give notes with times: "around second 14 there's a flash, take it out".
2. Claude edits the storyboard or the format, snapshots, renders v2.
3. After each round: **"Save this to the skill."** Claude writes the note as one plain rule in the right section of
   SKILL.md (and in `STYLE-GUIDE.md` + the colour tokens when it changes the look). A new rule that contradicts an old
   one replaces it.
4. A note you give twice should become code: a check in a script plus a test in `scripts/tests/`, so it can't slip.

## 9. Every two videos: the teardown (optional)

`teardown.py` measures two videos from a channel you admire and your last two edits, and `--compare` puts the numbers
side by side (overlays and camera moves per 90 s, words per minute, cut rate). Each gap becomes one rule in the skill.

---

## Lane B: Reels at 1080x1920, 60 fps, free tools only

Where each step stands today:

| Step | Status | What to do |
|---|---|---|
| Record | ✅ | 4K **vertical**, 60 fps (2160x3840 leaves room to zoom; 1080p goes soft past ~112 %) |
| Cut | ✅ | the same loop; `apply-cut.py --fps 60` |
| Transcribe | ✅ | Parakeet, free |
| Screen recordings | ✅ | skip Tella: record with OBS or the OS recorder, use the two-file route (`sync-tracks.py`) |
| Plan + compose | ❌ **needs building** | `compose.py` only builds a 1920x1080, 30 fps stage, and every format is laid out for 16:9 |
| B-roll | ⚠️ needs a small change | `broll-conform.py` always writes 30 fps at 16:9; it needs `--fps` and a vertical size. Pexels has portrait clips |
| Sound | ✅ | the free HyperFrames library; skip Epidemic Sound. Add music in the Instagram app when posting |
| AI B-roll | skip | it costs credits per shot |
| Render | ⚠️ after compose | renders at the composition's size and frame rate; without `--resolution 4k` |
| Verify | ✅ | `verify-render.py --res 1080x1920` (the bitrate floor scales with size) |
| Assemble | ✅ | `assembly.json` with `"width": 1080, "height": 1920, "fps": 60` |

Rules that change for reels (from SKILL.md's "Shorts" section, plus Instagram's layout):

- A separate 1080x1920 composition, never a centre crop of a 16:9 edit.
- Hero text 88 to 110 px; cards full width minus 48 px.
- **Word-by-word captions on** (most reels are watched muted), the caption about 280 px from the bottom, clear of
  Instagram's caption and buttons (bottom ~20 % and the right edge).
- One clear reason to stay in the first 3 seconds, paid off by the end; one open loop.
- Pace: the 7-per-90-seconds budget still fits a full-length reel, but expect notes asking for faster.

**To build before the first reel**, in this order:

1. `compose.py`: a `"canvas": "9:16"` option (1080x1920, `data-fps` 60) with vertical positions for a starter set of
   formats: captions, lower line, pills, logo card, punchline chip, chapter tag, clip, stat tiles (stacked), search.
2. `broll-conform.py`: `--fps` and `--size` options.
3. Tests for both under `scripts/tests/`, next to the existing 31.
4. A Reels section in SKILL.md and a Reels column in `STYLE-GUIDE.md`, so the learning loop works for reels too.
