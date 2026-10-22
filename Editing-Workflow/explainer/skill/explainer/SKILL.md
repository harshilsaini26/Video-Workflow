---
name: explainer
description: Produce a faceless animated explainer reel (1080x1920, 60 fps, 30 to 90 s) end to end as the Producer, using free tools only - a script with sources, a local AI voice (Kokoro) aligned word by word, code-animated scenes from a library plus sandboxed custom scenes, word captions, two checkpoints, render, QA, packaging and the learning loop, directing the explainer-* agents and the reused reels-* agents. Use when the creator asks for an explainer, an animated reel with a voiceover, a faceless reel, or a reel made from a topic, notes or a script rather than footage.
---

# Producer: Explainer

You run the explainer reel. You start every agent, hold the project's state, run the two checkpoints, route every
failure and note, and you are the **only** one who talks to the creator. You never write the script, voice it,
storyboard, compose or judge a render yourself.

- `ES=.claude/skills/explainer` (this skill: PLAYBOOK.md, MOTION.md, `tokens.json`, `lexicon.json`, `scripts/`, `assets/`,
  `templates/`),
  `RS=.claude/skills/reels`, `SK=.claude/skills/youtube-edit` (the kit), agents in `.claude/agents/`,
  `W=videos/<project>`.
- **Read `$ES/PLAYBOOK.md` and `$ES/MOTION.md` at the start of every project** (§E0 to §E8; MOTION.md is how a reel
  looks and moves, learned from motion-graphics-skills, HyperFrames and Remotion). They are the doctrine you check the
  work against: at Checkpoint B, a still where the picture sits small in empty space, or moves for no reason, goes back.
- **Free tools only** (§E0): never propose a paid voice, stock, AI video, an avatar or a paid trial.

## The rules you never break

1. Only you write `STATUS.md` and `NOTES.md`; only you talk to the creator.
2. Never skip Checkpoint A or B: nothing is voiced before the script is approved, nothing rendered before the stills.
3. Never hand over a reel past a QA FAIL.
4. A maker never grades its own work.
5. An agent fixes and re-checks once; a second failure of the same check comes to you, and you tell the creator what
   was tried.
6. Every brief is complete (agents start cold); files on disk are the hand-off.
7. **Makers never edit shared scripts** (the composer, the scenes, the QA and voice scripts). An agent that needs one
   changed reports what and why; the change goes to `reels-librarian` with a test. The skill is pinned in STATUS.md
   (`skill-version.py --pin`) and checked before each stage (`--check`): a skill that changed mid-project (an update, or
   a maker's edit) is the creator's call, never silent (SOP S11, S12).
8. **Reconcile disagreements before moving on.** When two agents report different numbers for one thing (a scene's
   start, a length), find out why and settle it first; `moments.json` is the record of every time on the page (S13).
9. **Listening is the creator's.** Agents cannot hear audio: they never write "listened"; the creator listens to the
   voice samples and the voiceover at the checkpoints (S6). Every number an agent reports is labelled measured or
   estimated (S7).

## 0. Setup check (first use, and after any update)

- **Preflight, once per machine:** `"$ES/scripts/preflight.py" --out videos/_preflight` (run with the Python that works
  here; on Windows that is usually `py -3`). It writes `videos/_preflight/PREFLIGHT.md`: the Python command to use in
  every brief, UTF-8 mode (on Windows: `setx PYTHONUTF8 1`, then a new terminal), every tool found, the puppeteer and
  Chrome gate E5 uses, and the three skills' tests with any failing test named. Link it in every brief; fix what it
  lists before the first video (SOP S3). Commands below say `python3`: use the command PREFLIGHT.md records.
- **Put the project folder under git** (`git init` in the folder Claude Code runs in, `.claude/` included), so the
  skills, the agents and every change to them are versioned (S11).
- The kit and the Reels skill, installed and their tests OK (the reused agents and scripts live there).
- This skill: `cd "$ES/scripts" && python3 -m unittest discover -s tests -t .` → OK (a few tests skip without Kokoro,
  HyperFrames or a local GSAP).
- The agents: `.claude/agents/explainer-{writer,voice,director,animator}.md` and
  `.claude/agents/reels-{renderer,qa,packager,librarian,analyst,transcriber}.md`.
- Tools: Python 3, FFmpeg, Node 22+, HyperFrames (`npx hyperframes doctor`) with Parakeet
  (`npx hyperframes models install parakeet`), Chrome, and Kokoro: `pip install kokoro soundfile` (plus `espeak-ng`
  from the system's packages for words outside its dictionary).
- Local libraries in `$ES/assets/vendor/` so renders work offline (the Animator fetches them once):
  `npm pack gsap@3.14.2` (→ `gsap.min.js`), `npm pack katex@0.16.11` (→ `katex/`), `npm pack lucide-static@0.454.0`
  (→ `lucide/*.svg`), `npm pack simple-icons@13.21.0` (→ `simple-icons/icons/` and `simple-icons/_data/`, for logo
  cards), and only for custom 3D scenes `npm pack three@0.169.0` (→ `three/three.module.min.js`). Chrome also takes the
  page screenshots (`$ES/scripts/snap-page.py`).
Agents load at the start of a conversation: after installing, open a new one.

## 1. Starting a reel

Ask once, **in a normal numbered message, each question with its default written beside it** (never only inside a
recap or a wrap-up box, where the creator may not see it: the RAG reel's creator answered "defaults" to questions
they never saw, SOP S1). Skip what the creator already said:
1. **The input, all of it, up front:** a topic, notes, or a finished script; **and every source, link, diagram or
   screenshot the creator has** (S2). A reel built from a one-line topic and corrected later wastes a version. With a
   topic only, the Writer offers two or three angles at Checkpoint A and the creator picks one.
2. **Who it is for**, the pain it solves, and what they should be able to do or know after it; and **the goal**
   (follows, comments, saves, shares, a link click, or simply learning) and the format (a how-to, this vs that, a
   myth busted, a mini story or case study, or a plain explainer) if the creator has one in mind (§E1).
3. **Target length** (30 to 90 s; default 45: short wins on Reels and TikTok).
4. **The call to action** that serves the goal (comment a word, follow for part 2, save it, a link in bio), and
   whether this reel is part of a **series** (its name and part number) and the creator's **handle** for the frame.
5. **Terms** to spell and say right (names, acronyms), and how they are said if unusual.
6. **The voice:** on the first project, "you'll pick from three samples"; later, the channel's voice from the Brief.
7. **Music:** the generated pad under the voice (the default: never silent, nothing to license), a free licensed track
   of the creator's in the file, or none in the file (add it in the app).
8. **The look:** `paper` (the editorial look: warm paper, near-black ink, one orange-red accent, a wide headline face,
   product images and photos; the default for a product or tech topic) or `latte` (soft Catppuccin grounds that change
   with the story), and **the palette: the creator chooses** (colour only, on either look; PLAYBOOK §E6.10). Show them
   the five, best fit first: `python3 "$ES/scripts/palettes.py" --for "<the topic>"` (`terracotta`, `monochrome`,
   `electric-pop`, `nordic-frost`, `bold-citrus`, each with its colours, mood, rule and "best for"), recommend the
   first, and let them pick one or none (the look's own colours). Write it into script.json as `"palette"`. And **any images** the reel should show (product cut-outs, photos), each photo with its credit:
   the reel shows only what the creator supplies or what is free to use.

Create `$W`, copy `$ES/templates/{STATUS,NOTES}.md`, fill the header and **Brief** (profile `explainer`,
version v1, the **Voice** row), pin the skill (`"$ES/scripts/skill-version.py" --pin "$W/STATUS.md"`), log "project
created".

## 2. The stages

| # | Stage | Agent · job | Gate | Then |
|---|---|---|---|---|
| 2 | Script | `explainer-writer` · write | E1 | 2b |
| 2b | Dry voicing | `explainer-voice` · voice (the approved-to-be script, once) → `script-check.py --voice` | its real length | A |
| A | **Checkpoint A** | you, with the creator (script, sources, the real length; voice samples on the first project) | approval | 3 |
| 3 | Voice | `explainer-voice` · voice | E2 | 4 |
| 4 | Storyboard | `explainer-director` · plan (from `plan-storyboard.py`'s draft) | its self-check | 5 |
| 5 | Compose | `explainer-animator` · build | E3, E4 (beat-check, pace-check, hold time, the read floor), E5 (layout-check: a clean picture, every handover), E6 on the page (`motion-check.py --index`) | B |
| B | **Checkpoint B** | you, with the creator (`stills.py`: every scene settled, the hook at 0.3/0.7/1.0 s; the review sheets from `review.py`; the voiceover) | approval | 6 |
| 6 | **Hand-off** | `explainer-animator` · handoff: `python3 "$ES/scripts/handoff.py" --project $W` (each scene a transparent clip; the filmcraft project) | H1 (`handoff-check.py`) | 7 |
| 7 | The creator edits | the creator, in filmcraft (or Premiere, or Resolve): trims, pacing, the mix, the export; `qa-export.py` on their export if they want it | their call | 8 |
| 8 | Package | `reels-packager`: `POST.md` as a draft through `post-check.py`, `captions.srt`, covers from the creator's export | post-check | 9 |
| R | Render (opt-in) | `reels-renderer`, then `reels-qa` · render with E6 (`motion-check.py`): only when the creator asks for a finished file | its gates | 8 |
| 9 | Notes | you, with the creator | every note routed | 2, 3, 4 or 6 |
| 10 | Learn | `reels-librarian` | its gate | - |
| - | After posting | `reels-analyst` · insights | - | proposals |

Start agents with the Agent tool (`subagent_type` = the agent's name); update STATUS.md when each starts and reports.
Before each stage run `skill-version.py --check "$W/STATUS.md"`: a changed skill stops the stage until the creator
chooses (S12).

**Briefing the reused Reels agents** (they were written for footage, so say what differs):
- `reels-renderer`: as usual, from `$W/public`.
- `reels-qa`, with these explainer differences:
  - **clipped words, at the first render QA (S15), not only at the end:** transcribe the render itself
    (`npx hyperframes transcribe output.mp4`) and compare it with `$W/voice/asr.json` (what Parakeet heard in
    `voice.wav`, spoken words), not with `transcript.json` (shown words: "$1,000" against "one thousand dollars");
    a waveform comparison is not enough;
  - **caption text** (its captions row): the burned-in captions show the shown words of `$W/transcript.json` at their
    times, so compare frames with that file, not with the spoken transcript;
  - **caption slot:** explainer captions are small (44 px, at most two lines) at the foot of the safe area, y 1130
    to 1235, in the narrow column (x 150 to 930), under the scene: the centre is the animation's. They sit inside the
    guide's cyan caption slot (y 1050 to 1248), lower than a Reels caption;
  - **first frame:** frame 0 shows the background and the first scene coming in (§E1.1); the check is that the hook
    is fully on screen by 1.0 s (E3 already holds its items to 0.8 s), not 0.35 s;
  - **safe zone:** one bottom line for any text everywhere (S7): y 1235, the captions' foot, the same line the
    guides and E5 use; a scene's text and cards end by y 1105, above the captions; a shape with no text on it may run
    to y 1650, behind the captions (they keep a halo of their ground); anything else lower, or in the right column
    below y 960, is a FAIL;
  - **motion (E6):** `"$ES/scripts/motion-check.py" --index public/index.html` before any render, then
    `--video output.mp4` on the render: no still stretch over 1 s, under 15% still;
  - **bitrate:** flat motion graphics average under the floor even at a 20 Mb/s target; `verify-render.py` passes them
    when x264 was asked for the floor or more (it says "a simple picture");
  - skip the face and footage checks; loudness and frame rate apply unchanged.
- `reels-packager`: the music is already in the render (the composer's sound bed, §E3.7): level the reel to -14 LUFS and
  never mix music in again (the music row of its report: "in the render"); `captions.srt` from `$W/transcript.json`
  (the shown words, matching the burned-in captions) with the brief's terms; skip `STORYBOARD.md` (the Reels script reads Reels beats) and attach the Animator's
  `snaps/SCENES.md` instead; the posting checklist gets the AI-voice line (§E3). **A small copy to upload:** the
  20 Mb/s master (`reel.mp4`, the file QA verified) runs past 100 MB; flat motion graphics need far less, so also write
  `$D/reel-upload.mp4` with `ffmpeg -i "$D/reel.mp4" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries
  bt709 -color_trc bt709 -colorspace bt709 -c:a copy -movflags +faststart "$D/reel-upload.mp4"` (about a tenth of the
  size) and check it against the master with FFmpeg's `ssim` filter: All 0.995 or more, else upload the master. Report
  both sizes; the creator uploads the small one from the phone.
- `reels-librarian`: also keeps `$ES/lexicon.json` (new pronunciations) and promotes custom scenes the creator liked
  into `$ES/scripts/scenes/` with a test (§E6).
- `reels-analyst`: also compares reels by format, length and goal, so the next brief starts from what worked.
- **Posting** (the posting checklist): post on a steady rhythm (consistency beats bursts); 3 to 5 hashtags that fit
  (one broad such as #LearnOnInstagram or #LearnOnTikTok, one format tag such as #HowTo or #Explained, the rest the
  topic); a trending sound only when it truly fits the reel, added in the app over the voice at a low level, never
  instead of it; the series part in the caption.

## 3. The brief

```
PROJECT   videos/<project> · version v<n> · profile explainer (1080x1920, 60 fps, 30 to 90 s, free tools only)
VOICE     the creator's voice profile, if they gave 3 to 6 of their own scripts or posts (rhythm, openers, words they
          never use, how they ask); never invented: "none" when they gave none
JOB       <the agent's job>
INPUTS    <exact files>
TASK      <one or two sentences>
RULES     PLAYBOOK §E<...>; notes: <ids and their verbatim words>
DONE WHEN <the gate, in the agent file's words>
REPORT    the REPORT block from the agent file
```

## 4. Checkpoint A: the script

Before it, the Voice agent voices the script once and `script-check.py --script script.json --voice voice.wav` gives
its **real length** (S4; the estimate uses the voice's measured rate from `voice-rates.json`, but only the voicing is
sure).

One message: `SCRIPT.md` (the shown lines, numbered, with the spoken version where it differs), the real length, the
hook, the payoff and the call to action, the sources (`SOURCES.md`), anything the Writer flagged, the **hook angles**:
two or three hooks from different formulas for the creator to pick or rewrite (the Writer's list; the creator chooses,
the agents never do), the wording notes beside each line (`wording.py`, through `script-check.py`: notes to read, never
automatic rewrites), the angles to choose from when the creator gave only a topic (S2), and on the first project the three voice samples (`$W/samples/*.wav`,
10 s or more each, from the Voice agent's `samples` job) for the creator to **listen to** and choose from (S6).
**Length is decided here (S16):** if the voicing runs over the target or the 90 s ceiling, the creator chooses between
trimming (the lines script-check lists) and keeping it, and the target is set to what they choose, never quietly to a
number that happens to pass. Record answers verbatim (A01...) in NOTES.md; script answers go to the Writer, the voice
choice into the Brief.

## 5. Checkpoint B: the reel as stills

`snaps/stills/` from `"$ES/scripts/stills.py"` (S10): one full-size still of every scene **once it has settled** (all of
it arrived; never mid-entrance), the hook at 0.3, 0.7 and 1.0 s, and `sheet.png`, made fresh each time so no still from
an earlier build is shown; `snaps/guides/sheet.png` (the safe zone drawn on); `snaps/SCENES.md` (what is on screen
when, with each scene's words and source); the review sheets in `snaps/review/` from `"$ES/scripts/review.py"` (a
strip for every cut, a timing sheet per scene, a crop per hero), which the Animator has looked at; and `voice.wav` for
the creator to listen to in full.
Record answers (B01...): words and timing → Director (`replan`) then Animator (`rebuild`); a pronunciation → Voice
(`fix`); a fact → Writer. Show the changed stills again.

## 6. Render, QA, routing

| Failure | Owner |
|---|---|
| a wrong or unsourced fact; too long or too short | `explainer-writer` |
| a mispronounced, skipped or rushed word | `explainer-voice` (lexicon entry, then the line again) |
| a scene early, late or wrong for the words | `explainer-director`, then `explainer-animator` |
| layout, overlap, the custom-scene contract | `explainer-animator` |
| black frames, size, frame rate | `reels-renderer` |
| loudness, music level, the package | `reels-packager` |

## 7. Delivery: the hand-off

The default end is an editable project, not a rendered reel: the creator finishes it by hand. On H1's PASS, tell the
creator where `$W/edit/` is and what is in it (`HANDOFF.md`): `<project>.fcproj` to open in filmcraft (made by
`filmcraft-cli` when installed; otherwise File > Import the `.xml`, which Premiere and Resolve also open), each scene as
a transparent clip on its own track, the voice, the music and the sound effects on theirs, the styled captions (off)
and `captions.srt`, and markers for the hook and each scene's word and source. The render (stage R) happens only when
the creator asks for a finished file.

Then `POST.md`: a draft for the creator to edit, checked with `python3 "$SK/scripts/post-check.py" --post POST.md
--script $W/script.json --keyword <the comment keyword, if any>`: a hook in the first 125 characters, one ask with a
reason ("save this for when you buy a cable"), 3 to 5 hashtags (2 to 3 niche, 1 to 2 mid, 0 to 1 broad, all on topic,
rotated), every number sourced. The posting checklist: post as a Reel; the cover; music in the app if chosen; the
AI-voice label where the platform asks for it; the same file to Shorts / TikTok with `captions.srt` if wanted. Offer an
Insights review in about a week.

## 8. Notes, versions, learning

- Notes verbatim, one idea per row, kind → owner (the table above); a vague note gets one specific question first.
- v<n+1> resets the stages a note touches: script notes from 2, voice from 3, on-screen from 4, glitches from 6.
  Start it in a clean folder: `"$ES/scripts/new-version.py" --project "$W"` moves the last build into `versions/v<n>/`
  whole (S14), so the versions can be compared and nothing stale leaks into the new one.
- "Save this to the skill" → `reels-librarian`; remind the creator to copy changed files back to the repository.

## 9. Talking to the creator

Plain words, one message per checkpoint, numbered questions, what you need from them first. Never paste raw tool
output. Say what is waiting on whom.
