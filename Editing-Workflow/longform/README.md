# YouTube long-form: the agent team

The agent team for **YouTube long-form videos**: roughly 8 to 25 minutes, a hook and several sections, 16:9, 4K at
30 fps, **free tools only**. You bring raw talking-head clips and screen recordings; the team cuts them on your last
takes, shapes the story with you, plans and builds every card, finds free B-roll and sound, and hands you an
**editor project** to finish. A finished 4K master, levelled and chaptered, is there when you ask for one.

It implements the workflow in [`../README.md`](../README.md) for this one profile, on top of the kit
([`../kit/`](../kit/README.md)), with the project files from [`../templates/`](../templates/README.md), and with
professional long-form practice built in from [background research](RESEARCH.md).

```
longform/
├── README.md                     this file
├── RESEARCH.md                   what professional long-form YouTubers do, with sources and confidence levels
├── skill/youtube-longform/       → install to .claude/skills/youtube-longform/
│   ├── SKILL.md                  the Producer: runs in your main conversation
│   └── PLAYBOOK.md               the long-form doctrine every agent follows (§L0 to §L14)
└── agents/                       → install to .claude/agents/
    ├── longform-ingest.md        ├── longform-animator.md
    ├── longform-transcriber.md   ├── longform-renderer.md
    ├── longform-cutter.md        ├── longform-qa.md
    ├── longform-director.md      ├── longform-assembler.md
    ├── longform-researcher.md    ├── longform-librarian.md
    ├── longform-broll-scout.md   └── longform-analyst.md
    └── longform-sound-designer.md
```

The team has no scripts of its own: it runs the kit's cut, compose and check scripts, and the Reels skill's
`reels-handoff.py` (with `--format 16x9`) for the editor project, so install the Reels skill too if you want the
hand-off (section 2).

---

## 1. What makes long-form different

> **The end of every run is a project you edit, not a finished video.** After you approve the stills, the team hands
> you an editor project: open `edit/<project>.fcproj` in [filmcraft](https://github.com/storytold/filmcraft) (free,
> open source; or import the `.xml` into filmcraft, Premiere Pro or DaVinci Resolve). Every section sits end to end on
> one sequence: your own camera files cut by word on V1 (never re-encoded), B-roll on V2, every card its own
> transparent clip on V3, styled captions on V4 (off), your voice, the music and the sound effects on A1 to A3, a
> chapter marker at each section and a marker for every note. You trim, re-time, mix and export. A finished render is
> still there when you want one: just ask (`python3 Editing-Workflow/wf.py render videos/<project> --profile longform`).

The kit edits hooks and sections well. A long video adds problems a hook doesn't have, and this team is built around
them:

| Long-form problem | What the team does | Where |
|---|---|---|
| The title and thumbnail make a promise the first minute must keep | the Producer records a **Brief**; the Director's story pass checks where the promise is paid off | PLAYBOOK §L1 |
| YouTube judges the intro at 30 s | a hook shape for 0 to 30 s, two or three **hook angles** for you to pick, a flash-forward when the opening is weak | §L2 |
| A middle that sags | sections joined by **but / therefore**, every WEAK join flagged with a fix, re-hooks at every boundary, strong beats near 3:00 and 6:00 | §L3 |
| Over-editing (the 2023 "retention editing" look) | tight early, clarity later, breathers after payoffs, every change must earn its place | §L4 |
| Tangents, repeats and stock phrases | flagged in the story pass and by `wording.py` on the kept words, for you to decide; never rewritten for you | §L5 |
| Sounding like yourself | an optional **voice profile** from 3 to 6 of your own scripts or videos (rhythm, openers, words you never use), passed to every agent that writes | SKILL § 3 |
| One composition can't hold 20 minutes | the approved cut is **split into sections**, each planned, built and checked alone, then laid end to end in the hand-off | §L0 |
| A voice that needs polish | an opt-in before/after pair you judge by ear, never applied blind | §L9 |
| Music across 20 minutes | one full-length bed timed to the sections, ducked under the voice (on the music track of the project, or on the master) | §L9 |
| Publishing | chapters validated, closed captions, mid-roll ad-break candidates, end-screen zone, disclosure reminders | §L11, §L12 |
| Not knowing what works for *your* audience | a retention review a week after publishing, mapped onto the storyboard | §L13 |

## 2. Install

From the folder you run Claude Code in (the one with your `videos/`), with this repository's `Editing-Workflow/`
folder and the kit's `youtube-edit` skill already installed (`.claude/skills/youtube-edit/`, copied from
`Editing-Workflow/kit/youtube-edit`):

```bash
mkdir -p .claude/skills .claude/agents
cp -R Editing-Workflow/longform/skill/youtube-longform .claude/skills/
mkdir -p .claude/skills/youtube-longform/templates && cp -R Editing-Workflow/templates/. .claude/skills/youtube-longform/templates/
cp Editing-Workflow/longform/agents/longform-*.md .claude/agents/
```

Or `python3 Editing-Workflow/wf.py install longform`, which runs the same steps (`--dry-run` prints them). For the
editor hand-off, install the Reels skill as well ([`../reels/README.md`](../reels/README.md) § 2): the hand-off script
lives there. For the native `.fcproj`, install `filmcraft-cli`; without it you get the `.xml` to import.
`python3 Editing-Workflow/wf.py doctor` says what is installed and what is missing.

Then open a **new** conversation (skills and agents load at the start of one) and say:

> Use my long-form team to edit this video. The raw clips are [file names], in this order.

The Producer checks the setup first (section 0 of its SKILL.md) and tells you anything missing. Optional: a free
`PEXELS_API_KEY` in your environment for stock B-roll.

**Models.** Every agent file says `model: inherit` (the conversation's model). To save cost, set the `model:` field
of the small-tier agents (Ingest, Transcriber, B-roll scout, Sound designer, Renderer, Assembler) to a smaller model;
keep the Producer, the Director and the Librarian on the strongest.

**Keeping the source in sync.** The installed copies under `.claude/` are the live ones. When the Librarian saves a
rule, it lists the files it changed; copy them back here so the repository keeps the learning.

## 3. Where you decide

The Producer is the only agent that talks to you, and it stops at each of these points until you answer.

| When | What you decide | What you are shown |
|---|---|---|
| **The brief** | the working title and thumbnail idea, the promise in one line, who it is for, the length, the raw files and their order, a sponsor, music, names and terms to spell right, the language (Parakeet for English and European languages, Whisper large-v3 for Hindi and others), anything that must be in it; optionally your voice profile | one numbered message; skip what you already said |
| **Checkpoint A: the cut and the story** | what is cut and kept, the sections and their order, the hook angle, each weak join, the candidate cuts, the colour, level and voice-polish proposals | `PAPER-CUT.md` (raw length → flat length, every removal and its reason), `CUT-REVIEW.html` for anything over 3 minutes, `STORY.md`, the wording notes, numbered questions |
| **Checkpoint B: the plan as stills** | per section: every card, diagram and draft format, the B-roll and the sounds; the voice polish, keep or skip | `<part>/snaps/sheet.png`, what is on screen when, the voice pair to play on headphones and a phone speaker, the Animator's concerns |
| **The hand-off** | you finish the project (the default), or ask for a rendered master | `edit/`, with `HANDOFF.md` listing what is where |
| **Notes** | what to change, with times, in plain words | each note in `NOTES.md` verbatim, routed by its kind; a vague one gets one specific question back |
| **"Save this to the skill"** | which notes become lasting rules | the rule in one line, and which files under `.claude/` to copy back here |

Every answer is written down word for word (A01..., B01..., D01... for decisions), so a new conversation can pick the
project up from `STATUS.md` and `NOTES.md`.

## 4. The team

```mermaid
flowchart TD
    YOU(["🙋 You"]):::you <--> P["🧑‍💼 The Producer<br/>your project manager,<br/>the only one<br/>you talk to"]:::lead
    P --> G1["✂️ Prep crew<br/>gets the footage in,<br/>writes every word down,<br/>cuts the mistakes<br/><i>Ingest · Transcriber · Cutter</i>"]:::team
    P --> G2["🎨 Creative crew<br/>shapes the story,<br/>plans each section,<br/>finds pages, clips, sounds<br/><i>Director · Researcher</i><br/><i>B-roll scout · Sound designer</i>"]:::team
    P --> G3["🎬 Build crew<br/>animates each section,<br/>hands off the project,<br/>renders on request<br/><i>Animator · Renderer</i>"]:::team
    P --> G4["🔍 Quality crew<br/>checks every file,<br/>packages it<br/>for upload<br/><i>QA · Assembler</i>"]:::team
    P --> G5["📚 Memory crew<br/>saves your feedback,<br/>studies your<br/>YouTube stats<br/><i>Librarian · Analyst</i>"]:::team
    classDef you fill:#FFE7A8,stroke:#C98A00,color:#1a1a1a
    classDef team fill:#D4F1F4,stroke:#1B8A99,color:#1a1a1a
    classDef lead fill:#E4DCF7,stroke:#6B4FBB,color:#1a1a1a
```

<sub>🟨 yellow = you · 🟪 purple = the Producer · 🟦 blue = the AI team</sub>

| Agent | Jobs | Runs | Writes |
|---|---|---|---|
| **Producer** (skill) | the brief, every stage, both checkpoints, routing, the hand-off, notes | the whole project | `STATUS.md`, `NOTES.md`, every brief |
| `longform-ingest` | copy, probe, classify, constant frame rate, join, align, measure level and colour | at the start; new files | `ingest.json`, `source.mp4`, `metadata.json`, `ingest/INGEST.md`, `raw-cfr/`, `aligned/` |
| `longform-transcriber` | `raw`, `flat`, `section`, `render` (windowed Parakeet, or Whisper; sanity checks) | after every change to a timed file | `transcript-raw.json`, `speech.v1`, `transcript.json`, `<part>/transcript.json`, `qa/*-transcript.json` |
| `longform-cutter` | `cut`, `note`, `split`; `wording.py` on the kept words | the flat cut; cut notes; after Checkpoint A | `cut-list.json`, `cut-map.json`, `PAPER-CUT.md`, `CUT-REVIEW.html`, `keeps.txt`, `sections.json`, `<part>/public/input-video.mp4` |
| `longform-director` | `story`, `plan`, `replan` | before Checkpoint A; per section; on-screen notes | `STORY.md`, `<part>/storyboard.json`, `<part>/ASSET-REQUESTS.md` |
| `longform-researcher` | logos, sites, pages, posts, screenshots, product photos, icons | per section, in parallel | files in `public/img/` and `_shared/img/`; its rows |
| `longform-broll-scout` | free licensed stock B-roll | per section, in parallel | `broll-shortlist.md`, `broll/`, `<part>/public/broll/`; its rows |
| `longform-sound-designer` | `assets`, `voice` (the before/after pair), `bed` | per section; voice before Checkpoint B; bed for the music track or the master | `_shared/sfx/`, `music/`, `voice/`; its rows |
| `longform-animator` | `build`, `rebuild`, `handoff` | per section after Gate G6; the hand-off after Checkpoint B | `<part>/public/index.html`, `<part>/snaps/`, `<part>/layers/`, `edit/` |
| `longform-renderer` | `render`, `patch` (**opt-in**) | only when you ask for a finished file | `<part>/output-4k.mp4` (earlier versions kept) |
| `longform-qa` | verify a section, a patch, the master; `qa-export.py` on your export if you ask | after every render; on request | `<part>/QA.md`, `QA.md` (master), `VERIFY.md`, `qa/` |
| `longform-assembler` | `package` from your export; on request the master: music duck, -14 LUFS, chapters, captions, ad breaks, delivery | after your export; after every part passed QA | `chapters.txt`, `captions.srt`, `ad-breaks.txt`, `STORYBOARD.md`, `DESCRIPTION.md`; for a render also `assembly.json`, the master and its no-music twin |
| `longform-librarian` | save a note as a rule; a repeat as a check + test | on "save this to the skill" | `SKILL.md`, `PLAYBOOK.md`, `STYLE-GUIDE.md`, scripts and tests |
| `longform-analyst` | `teardown`, `retention` | every two videos; a week after publishing | `videos/_teardown/COMPARE.md`, `RETENTION.md` |

## 5. The long-form flow

```mermaid
flowchart TD
    A["🎥 You answer the brief<br/>and record"]:::you --> B["✂️ The team cuts out<br/>mistakes and checks<br/>the story flows"]:::team
    B --> C{"👀 Checkpoint A<br/>the cut, the story,<br/>the hook angle"}:::ask
    C --> D["📑 The video is split<br/>into sections"]:::team
    D --> E["🎨 Each section gets<br/>its text, graphics,<br/>clips and sounds"]:::team
    E --> F{"👀 Checkpoint B<br/>you check the stills"}:::ask
    F --> G["🎞️ Every section on one<br/>sequence: your editor<br/>project, checked"]:::team
    G --> H["✏️ You finish it<br/>in filmcraft<br/>(or ask for a render)"]:::you
    H --> I(["✅ Packaged: chapters,<br/>captions, description"]):::done
    I -. "a week after publishing" .-> K["📈 Optional: learn from<br/>your YouTube stats"]:::team
    classDef you fill:#FFE7A8,stroke:#C98A00,color:#1a1a1a
    classDef team fill:#D4F1F4,stroke:#1B8A99,color:#1a1a1a
    classDef done fill:#D7F0D2,stroke:#3C8D2F,color:#1a1a1a
    classDef ask fill:#FFFFFF,stroke:#888888,color:#1a1a1a
```

<details>
<summary>Show the detailed version (every stage, check and file)</summary>

```mermaid
flowchart TD
    REC["Record<br/><i>you</i>"] --> ING["Ingest<br/>probe · CFR · join · measure"]
    ING --> TRR["Transcribe raw<br/>(windowed)"]
    TRR --> CUT["Cut<br/>last takes · edges · dead air · wording notes"]
    CUT --> STO["Story pass<br/>sections · but/therefore · hook angles<br/>tangents · repeats · re-engagement"]
    STO --> CPA{"✋ Checkpoint A<br/>PAPER-CUT.md + STORY.md"}
    CPA -- "changes" --> CUT
    CPA -- "approved" --> SPL["Split into sections<br/>one flat cut + transcript each"]
    SPL --> SEC

    subgraph SEC ["for every section · in parallel where safe"]
      direction TB
      PLN["Plan<br/>storyboard.json + ASSET-REQUESTS.md"] --> AST["Assets<br/>Researcher · B-roll · Sound"]
      AST --> CMP["Compose + pre-checks<br/>check · beat-check · gap-scan · stills"]
      CMP --> CPB{"✋ Checkpoint B<br/>stills · diagrams · voice pair"}
      CPB -- "changes" --> PLN
    end

    CPB -- "approved, every section" --> HO["Hand-off<br/>reels-handoff.py --format 16x9<br/>gate H1"]
    HO --> ED["You edit and export<br/>(qa-export.py if you ask)"]
    ED --> PKG["Package<br/>chapters · captions · ad breaks · STORYBOARD · DESCRIPTION"]
    CPB -. "only if you ask" .-> RND["Render 4K per section"]
    RND --> QAS{"QA"}
    QAS -- "FAIL → owner" --> CMP
    QAS -- "PASS, every section" --> ASM["Assemble<br/>music bed ducked · -14 LUFS"]
    ASM --> QAM{"QA on the master"}
    QAM -- "PASS" --> PKG
    PKG --> NOTES{"Notes<br/><i>you</i>"}
    NOTES -- "notes → v2" --> PLN
    NOTES -- "save this" --> LIB["Librarian<br/>rule · check + test"]
    PKG -. "a week after publishing" .-> RET["Analyst<br/>retention review"]
    RET -. "proposed rules, your yes" .-> LIB
```

</details>

| # | Stage | Agent · job | Gate |
|---|---|---|---|
| 2 | Ingest | `longform-ingest` | G1 |
| 3 | Transcribe | `longform-transcriber` · raw | sanity checks |
| 4 | Cut | `longform-cutter` · cut (with `longform-transcriber` · flat) | G2 G3 G4 |
| 4b | Story pass | `longform-director` · story | G5 (story) |
| A | **Checkpoint A** | you | approval |
| 4c | Section split | `longform-cutter` · split, then `longform-transcriber` · section | split check |
| 5 | Plan, per section | `longform-director` · plan | G5 |
| 6 | Assets, per section | Researcher, B-roll scout, Sound designer, in parallel | G6 |
| 6v | Voice polish (if proposed) | `longform-sound-designer` · voice | pair ready |
| 7 | Compose, per section | `longform-animator` · build | G7 G8 G9 |
| B | **Checkpoint B** | you | approval |
| 8 | **Hand-off** | `longform-animator` · handoff | H1 (`handoff-check.py`) |
| 9 | You edit | you, in filmcraft (or Premiere, or Resolve) | your call |
| 10 | Package | `longform-assembler` · package, from your export | G12 |
| R | Render (opt-in) | `longform-renderer`, `longform-qa`, `longform-assembler` · master | G10 to G12 |
| 11 | Notes | you | every note routed |
| 12 | Learn | `longform-librarian` | G13 |

What each gate checks, and who owns each failure: [the workflow README](../README.md#7-quality-gates) § 7 and § 8.
To run a stage's gates yourself: `python3 Editing-Workflow/wf.py gates videos/<project> --profile longform --stage H1`.

## 6. Files the long-form team adds

On top of the kit's files and the four project files ([`../templates/`](../templates/README.md)):

```
videos/<project>/
├── STATUS.md · NOTES.md · QA.md (master)         the project files
├── ingest/INGEST.md, ingest/stills/, ingest/colour/   Ingest: every file measured, flags with stills
├── raw-cfr/ · aligned/                           Ingest: constant-frame-rate copies; aligned face/screen pairs
├── keeps.txt                                     Cutter: the hand-cut --keep arguments
├── STORY.md                                      Director: sections, joins, hook angles, wording notes, re-engagement map, candidate cuts
├── sections.json                                 Cutter: each section's flat-cut start, end, length
├── voice/before.wav, after.wav, CHAIN.txt        Sound designer: the voice-polish pair (only if proposed)
├── music/master-bed.wav, BED.md                  Sound designer: the full-length bed and its changes
├── edit/                                         Animator: <project>.fcproj, <project>.xml, captions.srt, HANDOFF.md, media/
├── assembly.json                                 Assembler (opt-in render only)
├── RETENTION.md                                  Analyst: the retention review
└── <NN-slug>/                                    one folder per section (00-hook, 01-..., NN-sponsor)
    ├── public/input-video.mp4, cut-list.json, cut-map.json, transcript.json, audio.wav
    ├── storyboard.json · ASSET-REQUESTS.md · QA.md
    ├── plan/ (shot stills) · snaps/ · layers/ (each card as a transparent clip) · qa/
    └── output-4k.mp4 (+ earlier versions)        opt-in render only
```

The package goes next to your export, or for a render to `~/Movies/YouTube Renders/<project>/` (`~/Videos/...` off a
Mac): the master, the no-music twin, `chapters.txt`, `captions.srt`, `ad-breaks.txt`, `STORYBOARD.md`,
`DESCRIPTION.md` (with the publish checklist), `ASSEMBLY.md`, `PAPER-CUT.md`.

## 7. The research, in one table

Full detail, sources and confidence levels: [`RESEARCH.md`](RESEARCH.md).

| Finding | Source level | Became |
|---|---|---|
| YouTube measures the intro at 30 s; over half still watching = above typical | Official | the hook shape (§L2), the retention review (§L13) |
| The first minute must deliver the thumbnail's promise; front-load the best moment | Documented (MrBeast production guide) | §L1, the flash-forward (§L2) |
| Re-engagement around minutes 3 and 6 | Documented | the re-engagement map (§L3) |
| Replace "and then" with "but" and "therefore" | Documented (Trey Parker, Randy Olson) | section joins and WEAK flags (§L3) |
| Slower, story-led pacing outperformed the "overstim" style (38 → 23 cuts a minute) | Documented (MrBeast, Tubefilter) | tight early, clarity later, breathers (§L4) |
| B-roll is the largest share of a pro team's edit time; it must illustrate | Documented (Ali Abdaal's team) | proof first, the B-roll scout's checks (§L6) |
| Murch's Rule of Six: emotion > story > rhythm > eye trace | Documented | cut tie-breaker, kept-on-purpose pauses (§L5) |
| J and L cuts; continuous room tone | Practice | split edits inside sections (§L5) |
| Voice chain: high-pass, light denoise, EQ, gentle compression, de-ess | Practice | opt-in voice polish with a before/after pair (§L9) |
| Music 15 to 20 dB under the voice; -14 LUFS / -1 dBTP working target | Practice | 16 / 19 dB ducking, re-levelled master (§L9) |
| Correct before grading; the skin line shows hue only | Practice | measure and propose, never grade unasked (§L10) |
| 4K SDR 35 to 45 Mb/s at 30 fps, H.264 High, closed GOP, AAC 48 kHz | Official | the delivery spec (§L12) |
| Chapters: 0:00 first, at least 3, each 10 s or more | Practice | the Assembler validates (§L12) |
| End screens use the last 5 to 20 s | Official | the end-screen zone (§L12) |
| Mid-rolls on videos of 8 minutes or more, at natural breaks | Official | `ad-breaks.txt` (§L12) |
| Paid promotion and realistic synthetic content must be disclosed | Official | the publish checklist (§L11) |
| Closed-caption files beat burned-in text for long-form | Practice | `captions.srt`, no burned-in captions (§L8, §L12) |

## 8. Limits

- **Agents can't listen.** Sound decisions are measured (levels, presence, loudness); anything that needs ears (the
  voice polish, the music's mood) comes to you as files to play.
- **Section joins are hard cuts** in a rendered master (`assemble.py` concatenates), so split edits live inside
  sections; in the editor project you can soften any join yourself.
- **Captions for a master are built by the Assembler** from the master's transcript, following §L12; a dedicated
  script with a test would make this more robust (a good first job for the Librarian).
- **Retention data** comes from you (a screenshot or CSV of YouTube Studio); the agents have no YouTube account access.
- **The team never uploads or publishes.** The package is a checklist; you post.
- **Reels** (9:16, 1080x1920, 60 fps) is a separate profile with its own team: [`../reels/`](../reels/README.md).
  Its `moments` route cuts reels out of a long-form project.
