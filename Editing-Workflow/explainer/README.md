# Explainer: the agent team (free tools only)

The agent team for **faceless animated explainer reels**: a voice explains one idea while code-drawn scenes land on
its words, with word captions on top. No camera, no footage. **1080x1920, 60 fps, 30 to 90 s, free tools only.** The
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
│   ├── tokens.json                 the looks (Catppuccin Latte; paper: warm paper, near-black ink, one red; dark: near-black, manim's colours), roles, motion
│   ├── MOTION.md                   how a reel looks and moves (from motion-graphics-skills, HyperFrames, Remotion)
│   ├── lexicon.json                pronunciations ("WACC" → "wack"), kept across projects
│   ├── voice-rates.json            words a second for each voice and speed, measured from its samples
│   ├── assets/fonts/               DM Sans, JetBrains Mono, Archivo (wide), Instrument Serif italic (OFL, licences beside them)
│   └── scripts/
│       ├── script-check.py         gate E1: length, hook, sources, payoff and call to action; writes SCRIPT.md
│       ├── tts-kokoro.py           the voice, line by line, joined with pauses, levelled to -16 LUFS
│       ├── align-script.py         gate E2: what Parakeet heard → the shown words with times (transcript.json)
│       ├── plan-storyboard.py      the draft storyboard from the script's viz hints and the aligned words
│       ├── explainer-compose.py    gate E3: storyboard.json → a 1080x1920, 60 fps HyperFrames page and its sound bed
│       ├── transitions.py          how each scene comes in: fade, whip, zoom-through, wipe, burst, cut, brush, leak; the close
│       ├── sound.py                the sound bed: a generated pad or the creator's music, ducked, with sound effects
│       ├── snap-page.py            a real page's screenshot with local Chrome, for the browser scene
│       ├── pace-check.py           gate E4 (pacing): no still stretch over 3 s, no picture held over 8 s, one read at a time
│       ├── layout-check.py         gate E5 (a clean picture): every scene in Chromium, no overlap, spill or unsafe text
│       ├── layout-probe.mjs        what layout-check runs in Chromium (HyperFrames' puppeteer and Chrome)
│       ├── motion-check.py         gate E6 (a living picture): on the page before any render, and on the rendered file
│       ├── stills.py               the Checkpoint B stills, settled, plus the hook at 0.3, 0.7 and 1.0 s, and a fresh sheet
│       ├── review.py               the Animator's review sheets: a strip per cut, a timing sheet per scene, 1:1 crops
│       ├── paper.py                the paper look's seeded texture (assets/paper.png)
│       ├── palettes.py             the five colour palettes, listed for the creator to choose (best fit for a topic first)
│       ├── preflight.py            prepares a machine once (Windows included) and writes PREFLIGHT.md
│       ├── skill-version.py        pins the skill's files at the brief; a changed skill stops the next stage
│       ├── new-version.py          a clean folder for each version of a reel (v2, v3...)
│       ├── headline.py             the headline layer: a big top-left headline, kicker, sub or serif aside over any scene
│       ├── thread.py               the thread: one line through the reel that morphs on the words (drop, loop, wave...)
│       ├── imagesize.py            an image's size from its own header (PNG, JPEG, WebP, GIF)
│       ├── explainer_lib.py        shared: word anchors, the scene area, the looks, text measured with real glyph widths
│       ├── scenes/                 one module per scene type (55, custom included), found without a list
│       ├── dev/                    calibration tools (glyph widths, scene heights in Chromium)
│       └── tests/                  589 tests (python3 -m unittest discover -s tests -t .)
└── agents/                         → install to .claude/agents/
    explainer-writer.md · explainer-voice.md · explainer-director.md · explainer-animator.md
```

---

## 1. What makes an explainer different

> **The end of every run is a project you edit, not a finished video.** After you approve the stills, the team hands
> you an editor project: open `<project>.fcproj` in [filmcraft](https://github.com/storytold/filmcraft) (free, open
> source; or import the `.xml` into filmcraft, Premiere Pro or DaVinci Resolve). Your own camera files are cut by word
> on the first track (never re-encoded), every card or scene is its own transparent clip on its own track, the voice,
> music and sound effects are on theirs, captions come as an editable `.srt`, and markers show the hook and each
> scene's word and source. You trim, re-time, mix and export. A finished render is still there when you want one:
> just ask (`python3 Editing-Workflow/wf.py render ...`).

| Problem | What the team does | Where |
|---|---|---|
| There is no face to hold the first second | the hook is line 0, at most 12 words, a specific promise, kinetic type on a dark ground; E3 fails a hook item later than 0.8 s, so it is whole on screen by 1.0 s | PLAYBOOK §E1 |
| The voice must say "one thousand dollars" while the screen shows "$1,000" | every line is kept twice, `say` and `show`; captions show `show`, timed across the whole `say` span | §E2, §E5 |
| A misread acronym spoils the reel | a pronunciation lexicon shared by every project; a bad line is regenerated alone | §E3 |
| Graphics drift off their words | every scene and item is anchored to a word (`word:N`), never to seconds; the kit's beat-check checks every entrance against its word | §E4 |
| A scene that sits still too long | `pace-check.py` fails any stretch over 3 s with nothing changing and any picture held over 8 s (a flow that travels may hold longer); on the page and on the rendered file, `motion-check.py` (E6) fails a still stretch over 1 s or a reel still more than 15% of the time; a slow camera drift and particles keep every frame alive | §E1, §E6 |
| A diagram that overflows or collides | gate E5 (`layout-check.py`) opens every scene in Chromium on your machine and fails on text over text, text crossing a shape, text out of its card, anything outside the safe area, small text, clipped text and WCAG contrast; the hub computes its own geometry; every scene type passes it at three lengths of text (`test_every_scene_case_is_clean`) | §E4 |
| A hook that costs tokens to write | the `kinetic` scene: kinetic type from a one-line hint in script.json, no code | §E6 |
| A small widget in an empty frame | every library scene is scaled up (to 1.8x) to fill the scene area, y 345 to 1105, the centre of the frame, with small captions under it (44 px with a soft halo, y 1130 to 1235, the one bottom line for any text) and bare shapes running on to y 1650; no ease overshoots, nothing breathes without a reason, every cut is velocity-matched; the hook is kinetic type from data, and custom scenes are kept for what the library can't draw ([MOTION.md](skill/explainer/MOTION.md)) | §E6 |
| Slides instead of a video | build-up scenes that grow on the words, with empty slots that fill as they are said (never ghost text); objects instead of boxes: a chat, a document, a hero number, a prompt bar, an editor's timeline, a reel feed, 3D bars, a cube, 3D cards, a briefcase, a beaker, a donut, a coin, a balance scale, a neural network, loss curves and a loss surface, and a stage that keeps one picture changing, and more (59 library scenes); automatic transitions, real logos and real page screenshots | §E4, §E6 |
| A reel that looks like slides, not a magazine | the `paper` look (`"look": "paper"`): warm paper, near-black ink, one red accent and three typefaces, a wide heavy grotesque for headlines (Archivo 125% 800), a serif italic for asides, mono for labels; a headline layer puts a big top-left headline over any scene, sized to the fewest lines that stay big | §E4.6, §E4.11, MOTION §1.6 |
| A math reel in the 3Blue1Brown style | the `dark` look (`"look": "dark"`): near-black grounds with manim's colours; `plot` (loss curves whose tangents slide to the minimum), `network` (a pixel digit in, a forward pass, the answer ringed, the error swept back) and `surface` (a ball stepping down a loss bowl); `stage` keeps one picture on screen, its objects coming in, moving and resizing on their words; `"captions": "off"` and `"close": "rewind"` | §E6.11, §E6.12 |
| Nothing ties the scenes together | the thread: one line through the whole reel that drops in, loops, turns into a wave, a ruler or an underline on the voice's words and lifts off at the end; no shape of it rests in the captions (E3) | §E4.12 |
| A product or a place you can only show as a picture | `product-hero` (a cut-out with the title behind it, notes drawn on with a leader and a label), `photo-grid` (one to four photos, each credited), plus waveforms, a mode switch, a step chart, line art drawn on, a price sticker and a crossed-out list | §E4.13 |
| Every scene on the same ground | four grounds with a rhythm: the hook on ink, the payoff and every third scene on blue, the rest light; every colour checked at 3:1 or better on its ground by E5 | §E6 |
| Two scenes on screen at once | the old scene leaves on the cut and the next enters on it; E5 looks at every handover, 1/30 s apart | §E4 |
| A length guessed from a word count | `script-check.py --voice` times the script at the voice's own measured rate, pauses included; the length is decided at Checkpoint A | §E1 |
| A machine nobody prepared | `preflight.py` once per machine: the Python command, UTF-8, every tool, every suite, failing tests named | SKILL.md |
| Silence between lines | a sound bed under the voice (a generated pad or the creator's track), ducked, with a whoosh on transitions and a pop as items land | §E3 |
| A storyboard costs many tokens | the Writer hints a picture for each line (`viz`) and `plan-storyboard.py` writes the draft with every anchor; the Director only edits | §E2, §E4 |
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
V=.claude/skills/explainer/assets/vendor && mkdir -p $V/katex $V/lucide $V/three $V/simple-icons && cd $V \
  && npm pack gsap@3.14.2 katex@0.16.11 lucide-static@0.454.0 three@0.169.0 simple-icons@13.21.0 \
  && for f in *.tgz; do mkdir -p "x-$f" && tar -xzf "$f" -C "x-$f"; done \
  && cp x-gsap-*/package/dist/gsap.min.js . \
  && cp -R x-katex-*/package/dist/katex.min.js x-katex-*/package/dist/katex.min.css x-katex-*/package/dist/fonts katex/ \
  && cp x-lucide-static-*/package/icons/*.svg lucide/ \
  && cp x-three-*/package/build/three.module.min.js three/ \
  && cp -R x-simple-icons-*/package/icons x-simple-icons-*/package/_data simple-icons/ \
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
| `script-check.py` | gate E1 on `script.json`; writes `SCRIPT.md` | 16: lengths and target (30 to 90 s), the brief's warnings (format, audience, goal, you, a question, an example, the format's shape), hook, sources (objects or plain strings), payoff and call to action, the report |
| `tts-kokoro.py` | Kokoro line by line (`--only` one line), pauses by break, high-pass, compression, two-pass loudnorm to -16 LUFS / -1 dBTP (a peak over -1 dBTP fails); `--samples` for the voice choice; a `fake` engine for tests | 7 (1 needs Kokoro) |
| `align-script.py` | gate E2: sequence alignment of heard to spoken words (tolerant of spelling, of the lexicon's respellings, of digits heard for number words: "1,000", "10%", "2024", "2.5"), shown words timed across their spoken span, spoken-only words at the start included | 11 |
| `pace-check.py` | gate E4's pacing, from the `moments.json` the composer writes next to the page: every tween, count and item is a moment of change, ambient motion is not; a still stretch over 3 s fails, over 2 s warns (the kit's gap-scan can't see it: scenes always cover the voice); the read floor: a number on screen 1.0 s, the last read 1.5 s before the end, two reads at once warned | 11, and it runs in the end-to-end test |
| `plan-storyboard.py` | the draft storyboard: `viz` hints into scenes with each item on its word (an unspoken item halfway between its neighbours), money into count-ups, steps into numbers, brands into logo cards, the rest into draft titles; `PLAN.md` says which rule made each scene | 6, including the draft composing and passing pace-check, and a line with two pictures |
| `transitions.py` | the transition for each scene (fade first, wipe on a new background, then a zoom-through and a whip, velocity-matched with a motion blur), the matching exit, the background wipe, the seeded burst | 7 |
| `sound.py` | the generated pad and sound effects (the same bytes every time), the events (a whoosh per moving transition, a chime on the payoff, pops 0.35 s apart), the bed: looped, faded, ducked under the voice | 6: never silent, at least 6 dB of ducking, the creator's track looped and faded |
| `snap-page.py` | a page's screenshot at an exact size with local Chrome in a fresh profile | 2 (1 needs Chrome) |
| `explainer-compose.py` | gate E3: places every scene by its measured height and scales it up to fill the scene area, glows that travel with each cut, transitions, word captions with the highlight box, the voice and the sound bed, the kit's markup; WARNs on a title that repeats the voice and on the same layout twice in a row | 33 (6 for the craft rules: fill, title size, the taller area, same layout), plus the kit's beat-check run on its page; bad storyboard values fail with the scene named |
| `scenes/*.py` | 59 library scenes (build-up scenes, UI objects, the hero stat, giant captions, the logo card, eight 3D scenes, three math scenes and the stage among them) and the sandboxed custom scene | 39 across the scene and asset suites (a screenshot punching in on its focus line among them), 10 for the custom contract (unique build names, and MOTION.md's banned eases, loops and randomness) |
| heights | each scene's predicted height against Chromium, 3 cases × 2 column widths × every scene type, and the kinetic hook at the width it was composed at | over 236 measured rows (one fixture per scene group): every one 0 to 4 px over, never under |
| `layout-check.py` | gate E5: every scene in Chromium at the moment it is fully built, and every handover (overlap, cover, crossing, spill, safe area, size, contrast on the composited ground; `hyperframes check` adds clipping) | 4, including every scene type at three lengths of text, clean |
| `motion-check.py` | gate E6 on the page (`--index`: the stills tool's seek at 10 fps, grey, boil off) and on the rendered file (FFmpeg at 10 frames a second); fails a still stretch over 1 s or more than 15% still | 8 in `test_motion.py` |
| `review.py` | the Animator's sheets from the page in Chromium: 25 frames around every cut, a scene's timing sheet, every item as it lands, 1:1 crops, a crop that follows one element | 6 in `test_review.py` |
| `paper.py`, the brush, the boil, the close | the seeded paper texture (≤ 6% darker), the five-band brush wipe, hand-drawn stroke boil in paper, the last scene leaving onto the hook's ground | `test_paper.py`, `test_transitions.py`, `test_boil.py` |
| `stills.py` | Checkpoint B: every scene settled, the hook at 0.3, 0.7 and 1.0 s, a sheet that is always fresh | in `test_sops.py` |
| `preflight.py`, `skill-version.py`, `new-version.py` | the machine prepared once; the skill pinned at the brief; a clean folder per version | in `test_sops.py` and `test_portable.py` (every text file opened as UTF-8, so Windows passes) |
| theme | every look (Latte, paper and dark), every role pair at its WCAG ratio, every colour on every scene case in the look's palette | 5 |
| `headline.py`, the looks, the hero face | the headline's size (120 to 64 px, fewest lines), the room it leaves the scene, the paper palette and fonts, the hero face on every hero selector, the planner's look and word anchors | in `test_editorial.py` |
| `thread.py` | every shape at 96 points, keys in time order, drawn on and morphed on its words, seek-safe, behind the scenes and captions, no shape resting in the captions, bad key data named, a held wave handing on its scroll, its colour on every ground | 12 |
| `imagesize.py`, `scenes/_annotate.py` | image sizes from their headers, notes on an image that fit or are refused by name | in `test_images.py` |
| `scenes/kinetic.py` | the kinetic hook: pieces on their words, the accent, bad data refused, any hook fits its width | 5, and the planner's kinetic shorthand |
| `explainer_lib.py` | anchors, tokens, glyph-width text measuring | 5 |
| docs | frontmatter parses, cited scripts exist, § references resolve, links, mermaid fences, the STATUS Voice row, the reused QA and Packager briefs, MOTION.md read first | 10 |
| end to end | script-check → fake voice → alignment → compose → beat-check → `hyperframes check` → a 60 fps render → the kit's `verify-render.py --res 1080x1920` | 1 (needs FFmpeg, the kit, HyperFrames and a local GSAP), plus 1 with real Kokoro and Parakeet |

**How it was verified** (2026-10-14 to 2026-10-18, on Linux with HyperFrames 0.8.157 to 0.8.171, and Chromium):
- the whole suite: 589 tests, all passing; 3 skipped where Kokoro or a long render is not available (2026-10-24, after the dark look, the math scenes and the stage; before that, the balance scale, the close and loop fixes and captions that follow the ground; 2026-10-22, after the craft pass from ClaudeAnimationBase; 2026-10-21, after the editor hand-off; before that, 2026-10-18, after the
  editorial pass: the paper look, the headline layer, the thread and nine new scenes);
- a 33 s paper-look demo (USB-C, with stand-in images) passed E1 to E5 before rendering, then E6 and
  `verify-render.py` on the render;
- a 48 s demo of the RAG reel rebuilt with the new scenes passed E1 to E5 before rendering, then E6 and
  `verify-render.py` on the render;
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
- **Formula widths** are estimated from the TeX source (KaTeX's real width is only known in the browser); a long
  formula is shrunk to its row in the browser, and gate E5 checks the result.
- **Fonts:** this profile bundles its own copy of DM Sans, JetBrains Mono, Archivo and Instrument Serif, so its
  glyph-width measurements do not depend on the kit's files.
- **Images** are the creator's: the team never generates or fetches photos; a photo without a credit fails E3.
