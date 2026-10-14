# Explainer: the agent team (free tools only)

The agent team for **faceless animated explainer reels**: a voice explains one idea while code-drawn scenes land on
its words, with word captions on top. No camera, no footage. **1080x1920, 60 fps, 60 to 90 s, free tools only.** The
voice is Kokoro-82M, which runs on your own computer (Apache-2.0); the picture is HyperFrames + GSAP with KaTeX and
Lucide icons. It implements the workflow in [`../README.md`](../README.md) for this profile, reuses five agents from
[`../reels/`](../reels/README.md) for rendering, checking, packaging and learning, and adds tested scripts for the
voice and the scenes. The design is in [`SPEC.md`](SPEC.md), the evidence in [`RESEARCH.md`](RESEARCH.md).

```
explainer/
├── README.md                       this file
├── SPEC.md                         the design
├── PLAN.md                         the build plan it was made from
├── RESEARCH.md                     what works in faceless explainer reels, the voice licence, AI labels
├── skill/explainer/                → install to .claude/skills/explainer/
│   ├── SKILL.md                    the Producer: runs in your main conversation
│   ├── PLAYBOOK.md                 the doctrine every agent follows (§E0 to §E8)
│   ├── tokens.json                 the look: fonts, colours, backgrounds, highlight, motion timing
│   ├── lexicon.json                pronunciations ("WACC" → "wack"), kept across projects
│   ├── assets/fonts/               DM Sans 500/700 and JetBrains Mono 500 (OFL, licences beside them)
│   └── scripts/
│       ├── script-check.py         gate E1: length, hook, sources, payoff and call to action; writes SCRIPT.md
│       ├── tts-kokoro.py           the voice, line by line, joined with pauses, levelled to -16 LUFS
│       ├── align-script.py         gate E2: what Parakeet heard → the shown words with times (transcript.json)
│       ├── explainer-compose.py    gate E3: storyboard.json → a 1080x1920, 60 fps HyperFrames page
│       ├── pace-check.py           gate E4 (pacing): no still stretch over 6 s on the page
│       ├── explainer_lib.py        shared: word anchors, the scene area, text measured with real glyph widths
│       ├── glyphs.json             the fonts' glyph widths, measured in Chromium
│       ├── scenes/                 one module per scene type (13, custom included)
│       ├── dev/                    calibration tools (glyph widths, scene heights in Chromium)
│       └── tests/                  92 tests (python3 -m unittest discover -s tests -t .)
└── agents/                         → install to .claude/agents/
    explainer-writer.md · explainer-voice.md · explainer-director.md · explainer-animator.md
```

---

## 1. What makes an explainer different

| Problem | What the team does | Where |
|---|---|---|
| There is no face to hold the first second | the hook is line 0, at most 12 words, on screen by 0.3 s, a specific promise | PLAYBOOK §E1 |
| The voice must say "one thousand dollars" while the screen shows "$1,000" | every line is kept twice, `say` and `show`; captions show `show`, timed across the whole `say` span | §E2, §E5 |
| A misread acronym spoils the reel | a pronunciation lexicon shared by every project; a bad line is regenerated alone | §E3 |
| Graphics drift off their words | every scene and item is anchored to a word (`word:N`), never to seconds; the kit's beat-check checks every entrance against its word | §E4 |
| A scene that sits still too long | `pace-check.py` fails any stretch over 6 s with nothing changing | §E1 |
| Text overflowing or under the app's buttons | each scene knows its own height (calibrated in Chromium to within 4 px) and is placed inside the safe zone by construction | §E4 |
| Nothing on screen for a moment | the composer fails on any gap over 0.3 s with no scene | §E4 |
| A number with nothing behind it | every number on screen carries a source, checked twice (script and storyboard) | §E7 |
| An AI voice may need a label | the posting checklist turns on Instagram's AI label, and says to check the other apps' rules | §E3, RESEARCH §5 |

## 2. Install

From the folder you run Claude Code in, with the kit's `youtube-edit` skill and the Reels skill and agents already
installed (see [`../reels/README.md`](../reels/README.md) section 2), and this repository's `Editing-Workflow/`
folder present:

```bash
mkdir -p .claude/skills .claude/agents
cp -R Editing-Workflow/explainer/skill/explainer .claude/skills/
mkdir -p .claude/skills/explainer/templates && cp -R Editing-Workflow/templates/. .claude/skills/explainer/templates/
cp Editing-Workflow/explainer/agents/explainer-*.md .claude/agents/
# the voice (free, runs locally; espeak-ng helps with words outside its dictionary):
pip install kokoro soundfile          # and: sudo apt install espeak-ng   (or: brew install espeak-ng)
npx hyperframes models install parakeet
# free libraries, copied locally so renders work offline:
V=.claude/skills/explainer/assets/vendor && mkdir -p $V/katex $V/lucide $V/three && cd $V \
  && npm pack gsap@3.14.2 katex@0.16.11 lucide-static@0.454.0 three@0.169.0 \
  && for f in *.tgz; do mkdir -p "x-$f" && tar -xzf "$f" -C "x-$f"; done \
  && cp x-gsap-*/package/dist/gsap.min.js . \
  && cp -R x-katex-*/package/dist/katex.min.js x-katex-*/package/dist/katex.min.css x-katex-*/package/dist/fonts katex/ \
  && cp x-lucide-static-*/package/icons/*.svg lucide/ \
  && cp x-three-*/package/build/three.module.min.js three/ \
  && rm -rf x-* *.tgz && cd -
# check the scripts:
cd .claude/skills/explainer/scripts && python3 -m unittest discover -s tests -t . && cd -
```

Then open a **new** conversation and say:

> Make an explainer reel about [topic] for [who]. About 75 seconds, ending with [call to action].

or paste notes or a finished script instead of a topic. Models: every agent says `model: inherit`; a smaller model
suits the Voice agent, and keep the Producer, Writer and Director on the strongest.

## 3. The team

```mermaid
flowchart TD
    YOU(["🙋 You"]):::you <--> P["🧑‍💼 The Producer<br/>your project manager,<br/>the only one<br/>you talk to"]:::lead
    P --> G1["✍️ Writer<br/>a short script,<br/>every fact sourced"]:::team
    P --> G2["🎙️ Voice<br/>a free AI voice,<br/>word timings"]:::team
    P --> G3["🎨 Director + Animator<br/>scenes on the words,<br/>captions, checks"]:::team
    P --> G4["🔍 From the Reels team<br/>render, QA, package,<br/>learn, stats"]:::team
    classDef you fill:#FFE7A8,stroke:#C98A00,color:#1a1a1a
    classDef team fill:#D4F1F4,stroke:#1B8A99,color:#1a1a1a
    classDef lead fill:#E4DCF7,stroke:#6B4FBB,color:#1a1a1a
    classDef done fill:#D7F0D2,stroke:#3C8D2F,color:#1a1a1a
```

<sub>🟨 yellow = you · 🟦 blue = the AI team · 🟩 green = finished</sub>

| Agent | Jobs | Writes |
|---|---|---|
| **Producer** (skill) | the brief, every stage, both checkpoints, routing, delivery | `STATUS.md`, `NOTES.md`, briefs |
| `explainer-writer` | `write`, `rewrite` | `script.json`, `SCRIPT.md`, `SOURCES.md` |
| `explainer-voice` | `samples` (first project), `voice`, `fix` | `voice.wav`, `lines/`, `voice/asr.json`, `transcript.json`, `VOICE.md` |
| `explainer-director` | `plan`, `replan` | `storyboard.json`, `custom/<id>.md`, `ASSET-REQUESTS.md` |
| `explainer-animator` | `build`, `rebuild`: custom scenes, compose, check, stills | `public/`, `custom/*.html`, `snaps/guides/sheet.png`, `snaps/SCENES.md` |
| `reels-renderer` | 1080x1920, 60 fps, 20 Mb/s, BT.709 | `output.mp4` |
| `reels-qa` | the file checks, captions, loudness, first frame (no footage checks) | `QA.md` |
| `reels-packager` | music (if any), -14 LUFS, covers, `captions.srt`, post caption and checklist | `deliver/` |
| `reels-librarian` | a note → a rule; new pronunciations; custom scenes promoted to the library | PLAYBOOK, lexicon, scenes, tests |
| `reels-analyst` | Insights a week after posting | `INSIGHTS.md` |

## 4. The flow

```mermaid
flowchart LR
    A["💡 Your topic,<br/>notes or script"]:::you --> B["✍️ A short script<br/>with sources"]:::team
    B --> C{"👀 You approve<br/>the script<br/>(and pick a voice)"}:::ask
    C --> D["🎙️ The voice,<br/>word by word"]:::team
    D --> E["🎨 Scenes on<br/>the words"]:::team
    E --> F{"👀 You approve<br/>the stills"}:::ask
    F --> G["🎬 Rendered,<br/>checked, packaged"]:::team
    G --> H(["✅ Your reel"]):::done
    classDef you fill:#FFE7A8,stroke:#C98A00,color:#1a1a1a
    classDef team fill:#D4F1F4,stroke:#1B8A99,color:#1a1a1a
    classDef done fill:#D7F0D2,stroke:#3C8D2F,color:#1a1a1a
    classDef ask fill:#FFFFFF,stroke:#888888,color:#1a1a1a
```

<sub>🟨 yellow = you · 🟦 blue = the AI team · 🟩 green = finished · ⬜ white = waits for you</sub>

<details>
<summary>The detailed flow (agents, files and gates)</summary>

```mermaid
flowchart TD
    BR["Brief (Producer)"] --> W["explainer-writer · write<br/>script.json, SCRIPT.md, SOURCES.md"]
    W --> E1{"E1 script-check.py"}
    E1 -- fail --> W
    E1 -- pass --> CA{"Checkpoint A<br/>script + sources<br/>(+ 3 voice samples, first project)"}
    CA -- notes --> W
    CA -- approved --> V["explainer-voice · voice<br/>tts-kokoro.py → voice.wav<br/>Parakeet → voice/asr.json"]
    V --> E2{"E2 align-script.py<br/>98% heard, no gap over 1.2 s,<br/>length within 10%"}
    E2 -- fail --> VF["explainer-voice · fix<br/>lexicon, --only line"]
    VF --> E2
    E2 -- pass --> D["explainer-director · plan<br/>storyboard.json (word anchors)"]
    D --> AN["explainer-animator · build<br/>explainer-compose.py"]
    AN --> E3{"E3 compose<br/>fits, no holes, sources, custom contract"}
    E3 -- storyboard --> D
    E3 -- pass --> E4{"E4 beat-check + pace-check<br/>hyperframes check, stills"}
    E4 -- fail --> AN
    E4 -- pass --> CB{"Checkpoint B<br/>stills + voiceover"}
    CB -- notes --> D
    CB -- approved --> R["reels-renderer → output.mp4"]
    R --> Q{"reels-qa · render"}
    Q -- fail --> R
    Q -- pass --> PK["reels-packager → deliver/"]
    PK --> QF{"reels-qa · final"}
    QF -- pass --> DONE(["Delivered"])
    DONE --> LB["reels-librarian · learn"]
```

</details>

## 5. The scripts and how they were verified

| Script | What it does | Tests |
|---|---|---|
| `script-check.py` | gate E1 on `script.json`; writes `SCRIPT.md` | 8: lengths and target, hook, sources (objects or plain strings), payoff and call to action, the report |
| `tts-kokoro.py` | Kokoro line by line (`--only` one line), pauses by break, high-pass, compression, two-pass loudnorm to -16 LUFS / -1 dBTP; `--samples` for the voice choice; a `fake` engine for tests | 6 (1 needs Kokoro) |
| `align-script.py` | gate E2: sequence alignment of heard to spoken words (tolerant of spelling, of the lexicon's respellings, of digits heard for number words: "1,000", "10%", "2024", "2.5"), shown words timed across their spoken span | 10 |
| `pace-check.py` | gate E4's pacing: every tween, count and item on the page is a moment of change; a still stretch over 6 s fails (the kit's gap-scan can't see it: scenes always cover the voice) | 3, and it runs in the end-to-end test |
| `explainer-compose.py` | gate E3: places every scene by its measured height, background cross-fades, word captions with the highlight box, the voice clip, the kit's markup | 18, plus the kit's beat-check run on its page |
| `scenes/*.py` | 12 library scenes and the sandboxed custom scene | 22 across the scene suites, 7 for the custom contract |
| heights | each scene's predicted height against Chromium, 3 text lengths × 2 column widths × 12 scene types | 2, over 72 measured rows: every one 0 to 4 px over, never under |
| `explainer_lib.py` | anchors, tokens, glyph-width text measuring | 5 |
| docs | frontmatter parses, cited scripts exist, § references resolve, links, mermaid fences, the STATUS Voice row, the reused QA and Packager briefs | 9 |
| end to end | script-check → fake voice → alignment → compose → beat-check → `hyperframes check` → a 60 fps render → the kit's `verify-render.py --res 1080x1920` | 1 (needs FFmpeg, the kit, HyperFrames and a local GSAP), plus 1 with real Kokoro and Parakeet |

**How it was verified** (2026-10-14, on Linux with HyperFrames 0.8.157 and Chromium):
- the whole suite: 92 tests, all passing; 2 skipped where Kokoro is not installed;
- the end-to-end run (pace-check included): a 4-line, 30-word script voiced by the fake engine (11.09 s, -15.95 LUFS), aligned 100% with
  the widest gap inside a line 0.02 s, composed into 4 scenes, 4 backgrounds and 8 caption phrases, rendered at
  1080x1920 and 60 fps (11.6 s, about 20 MB) and passed by `verify-render.py`; the frames were looked at by eye;
- the scene heights: glyph widths of the bundled fonts and the laid-out height of every scene type, measured in
  Chromium with `dev/` (see [`skill/explainer/scripts/dev/README.md`](skill/explainer/scripts/dev/README.md)).

**Not yet verified here:** the real voice. Kokoro could not be installed in the build environment (its model downloads
from Hugging Face, which that environment's network blocks), so `test_real_kokoro_parakeet_alignment` (Kokoro voice →
Parakeet → align, 98% at least) and the real speaking rate (RESEARCH §3) are checked on the first real project.

## 6. Known limits

- **One language:** English voices (`a` American, `b` British). Kokoro has other languages; the scripts and lexicon
  assume English.
- **Formula widths** are estimated from the TeX source (KaTeX's real width is only known in the browser); Checkpoint B
  stills catch an overflow.
- **The kit's DM Sans files** are not usable DM Sans (Chromium draws them with the fallback serif's widths), so this
  profile bundles its own fonts. The kit is left as it came.
