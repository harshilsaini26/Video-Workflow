# Explainer: animated faceless reels with an AI voice (design spec)

Status: design approved in conversation, section by section (2026-10-14). This document is for review before any
implementation plan is written. Nothing here is built yet.

## 1. Purpose

A third profile next to [`longform/`](../longform/README.md) and [`reels/`](../reels/README.md): **faceless animated
explainer reels**. The video is code-drawn animated graphics, an AI voiceover and burned-in captions, with no camera
footage. The model is the reference reel "Most finance bros gatekeep these exact certificates" (section 3).

**Success:** from a topic, notes or a finished script, the team delivers a 60 to 90 s vertical reel (1080x1920, 60 fps)
that:
- is accurate (every on-screen fact has a source the creator approved);
- keeps changing on screen every 2 to 4 s, in time with the voice;
- passes the same QA as a Reels reel;
- uses only free tools and free licences.

## 2. Decisions

| Question | Decision | Decided by |
|---|---|---|
| Voice | **AI voice**, free and local: **Kokoro-82M** (Apache-2.0) | Creator (the reference's voice is AI too) |
| Language | **English** (captions in DM Sans, the house font) | Creator |
| On-screen character | **None** in version 1 (the reference's talking mascot is a paid AI avatar) | Creator |
| Topics | **A mix**: career and education, finance, tech. Version 1 builds the core scene set the reference uses, which covers all three. | Creator |
| Script source | **Any per video** (a topic, notes or a finished script); **notes** is the usual route | Creator |
| How the animation is made | **Hybrid**: a tested scene library for about 80%, plus a `custom` scene escape hatch held to the same checks | Creator, on Claude's recommendation |
| Where the spec lives | `Editing-Workflow/explainer/SPEC.md`, inside the one folder the repository keeps | Creator |

## 3. The reference, decompiled

These findings come from the file itself: 87 s, 720x1280, 30 fps, Instagram's re-encode, so the original metadata is
gone.

| Layer | What it is | How it was most likely made | In version 1? |
|---|---|---|---|
| Graphics (about 90% of screen time) | Charts that draw themselves; count-up numbers in step with the line; cash-flow lollipops; mocked course pages, spreadsheets and app windows; Q&A stacks; a clock; formulas; three cross-fading backgrounds (blue gradient, black with a glow, light with a dot grid); small letter-spaced uppercase labels | Code: HTML/CSS/SVG plus GSAP, rendered to video. Scenes morph rather than cut (only about 10 real cuts in 87 s). | Yes: the scene library |
| 3D yield-curve surface | A heat-mapped WebGL surface | three.js in the same page | Only as a `custom` scene |
| Captions | Word by word near the top; keywords in a "selection box" highlight; the phrase clears at pauses | Word timings from the voice drive the caption layer | Yes |
| Voice | Steady delivery, mastered at -14 LUFS with LRA 2.1 LU | An AI voice (paid service) | Yes, as Kokoro (free) |
| Music | A continuous bed, ducked under the voice | Stock music | Yes: a free licensed track, via the Reels Packager |
| Mascot | A paper-bag-head character whose hands and mouth move | A paid AI talking-avatar clip | No |

Structure of the reference:
1. A hook.
2. Three items, each with the same arc: a "Number N" card, the course, what you learn (concepts made visual), why it
   matters, how long it takes.
3. A call to action ("Comment LINK…").

## 4. Constraints

- **Free tools and licences only** (the rule for the whole workflow):
  - HyperFrames and GSAP;
  - Kokoro-82M (Apache-2.0) and Parakeet;
  - KaTeX (MIT), Lucide icons (ISC);
  - DM Sans and a free monospace for labels (SIL OFL);
  - free licensed music (Pixabay, as in Reels).
- Non-commercial models (XTTS-v2, F5-TTS weights) are excluded: the channel is monetised.
- **Output:** 1080x1920, 60 fps, about 20 Mb/s, BT.709, -14 LUFS. This is the Reels format, so Reels' Renderer, QA
  and Packager apply unchanged.
- **Safe zone:** the Reels box (top 269, bottom 672, sides 65 px; the action column below y 960). It is enforced by
  construction.
- **Network:** Kokoro (about 330 MB) and Parakeet download from Hugging Face once. In a cloud session that needs
  `huggingface.co` (and its file hosts) allowed, plus `NODE_USE_ENV_PROXY=1` for HyperFrames' downloads.

## 5. The team and the flow

**New** (`agents/explainer-*.md`):

| Agent | Job | Writes |
|---|---|---|
| **explainer-writer** | Turns a topic, notes or a script into a 60 to 90 s script (160 to 240 words): hook first, a payoff, a call to action. Each line is kept in two forms, spoken and shown. Every fact gets a source. Marks emphasis words. | `SCRIPT.md`, `script.json`, `SOURCES.md` |
| **explainer-voice** | Generates the voice line by line with Kokoro, applies pronunciations and pauses, cleans and levels it, and aligns the word timings | `voice.wav`, `transcript.json` (display words with times), `VOICE.md` |
| **explainer-director** | Plans the storyboard: scenes on word anchors, backgrounds, caption emphasis, custom-scene requests | `storyboard.json`, `ASSET-REQUESTS.md` (only for supplied logos or screenshots) |
| **explainer-animator** | Composes from the library, writes custom scenes, runs the checks and the guided snapshots | `public/index.html`, `snaps/` |

**Reused from Reels, unchanged:** `reels-renderer`, `reels-qa`, `reels-packager` (music bed, -14 LUFS, covers, post
caption, `captions.srt`), `reels-librarian`, `reels-analyst`. Reels' asset scout is used only when the creator supplies
a logo or screenshot.

**Flow:**
1. **Brief** (Producer): the input route (topic, notes or script); audience; length; call to action; terms; the voice
   (fixed for the channel after the first project); music in the file or in the app.
2. **Script** (Writer).
3. **Checkpoint A:** the script, its sources and the length estimate. On the first project, three 10 s voice samples to
   choose from. Nothing is voiced before approval.
4. **Voice** (Voice agent): `voice.wav` plus the aligned `transcript.json`.
5. **Storyboard** (Director), then **compose and check** (Animator).
6. **Checkpoint B:** a guided still of every scene, plus the full voiceover to listen to.
7. **Render** (Reels Renderer), **QA** (Reels QA), **package** (Reels Packager), then **QA final**.
8. **Notes**, then **learn** (Librarian): rules, pronunciations, and custom scenes promoted into the library.

The Producer rules are the same as the other teams: only the Producer talks to the creator; checkpoints are never
skipped; a maker never grades its own work; a second failure of the same check goes to the creator.

## 6. The scene library and the storyboard

### 6.1 Layers

1. **Background:** `blue` (gradient with a violet glow), `black` (with a blue glow) or `light` (off-white with a dot
   grid). It cross-fades in 0.4 s when a scene's `bg` changes.
2. **Scene:** one at a time, inside the scene area (x 65 to 1015, y 520 to 1420 since the craft pass, Instagram's clear
   line; narrower below y 960, as in Reels), scaled up to fill it.
   Scenes hand over with an overlap of at most 0.3 s: the old one exits (ease-in, shorter) while the new one enters
   (ease-out, longer).
3. **Captions:** the band from y 330 to 470.
   - Phrases of up to 4 words and 24 characters.
   - The word being spoken turns from dim to white.
   - Emphasis words get the highlight box (an accent fill with corner handles).
   - The phrase clears at a pause of 0.35 s or more.

### 6.2 Scenes in version 1

| Type | Data | Animation |
|---|---|---|
| `title` | `text`, `kicker` | words rise in, kicker fades |
| `number` | `n`, `name` | badge pops, name slides up |
| `list-cards` | `items[2..4]` each `{label, at}` | cards fan in on their words |
| `line-chart` | `points`, `x`, `label`, `prefix/suffix`, `reveal[{point, at}]` | line draws, points pop, value counts up in step |
| `bars` | `rows[{label, value, text, hi, at}]` | bars grow on their words |
| `count-up` | `value`, `prefix/suffix`, `decimals`, `sub` | number counts up in full digits |
| `browser` | `title`, `subtitle`, `badges[]`, `button`, `domain` | window drops in, contents stagger |
| `sheet` | `rows[[...]]`, `highlight {row\|cell, at}`, `formula` | rows stagger, highlight on its word |
| `qa-stack` | `items[{text, em[], at}]` | questions stack on their words, keywords highlighted |
| `duration` | `value`, `unit` (hours, days, weeks), `style` (clock or dial) | hand or dial sweeps, number counts |
| `formula` | `tex`, `parts[{tex, at}]` | parts appear on their words (KaTeX) |
| `icon-row` | `items[2..4]` each `{icon, label, at}` | icons pop with labels (Lucide) |
| `custom` | section 6.4 | Claude-written, sandboxed |

Each scene is a small module in `scripts/scenes/`. It returns its HTML, its GSAP calls and **its measured height at a
given width**, so placement is checked by construction (the lesson from Reels' code reviews).

### 6.3 The storyboard

```json
{
  "id": "certs-01", "fps": 60, "voice": "voice.wav", "transcript": "transcript.json",
  "captions": {"emphasis": ["Coursera", "NPV", "$1,000"]},
  "scenes": [
    {"type": "title", "id": "hook", "bg": "black", "in": "word:0", "out": "word:9",
     "text": "3 certificates finance bros gatekeep", "kicker": "IF YOU'RE NEW TO FINANCE"},
    {"type": "line-chart", "id": "tvm", "bg": "light", "in": "word:12", "out": "word:31",
     "label": "VALUE OF $100", "points": [100, 114, 152, 214, 265], "x": ["Y0", "Y5", "Y10", "Y15", "Y20"],
     "prefix": "$", "reveal": [{"point": 4, "at": "word:27"}], "source": "s2"}
  ]
}
```

- **Times are word anchors:**
  - `word:N` is the Nth display word in `transcript.json`, so the animation can't drift from the voice;
  - an entrance lands 0.2 s before its word by default (beat-check's 0.15 to 0.25 s window);
  - plain seconds are allowed only for an `out` at the very end.
- **The total duration** is the voice's length plus 0.5 s.
- **Sources:** a scene showing a number, name or claim must carry `source` (a key in `SOURCES.md`).
- **The look** comes from `tokens.json`:
  - fonts: DM Sans 700/500 and a free mono for labels;
  - colours: by default the kit's cyan for key words, amber for money and magenta for punchlines;
  - the three backgrounds, and the highlight-box style.

  Changing the tokens restyles every scene.
- **Motion** follows the motion-design skill:
  - entrances ease out (MD3 emphasized curve), exits ease in and are 30 to 50% shorter;
  - staggers stay under 0.5 s in total;
  - one hero element per scene;
  - no linear easing on movement.

### 6.4 The `custom` scene contract

```json
{"type": "custom", "id": "yield", "bg": "black", "in": "word:3", "out": "word:14",
 "box": {"x": 65, "y": 560, "w": 950, "h": 600}, "html": "custom/yield.html", "build": "buildYield", "source": "s1"}
```

- `custom/yield.html` holds markup scoped under `#yield` and a function `buildYield(tl, root, t0, t1)` that adds its
  animation to the shared GSAP timeline between `t0` and `t1`.
- **The composer fails the build when:**
  - the box is outside the scene area;
  - the id is not unique;
  - the markup or script uses a selector outside `#<id>`, or `document.body`;
  - the script loads anything from the network;
  - the function is missing.
- Libraries a custom scene may use: GSAP, KaTeX and three.js, all copied locally.
- **Checkpoint B** shows custom scenes at their in, middle and out moments.
- **Promotion:** a custom scene the creator likes is turned into a library scene by the Librarian, with a test.

## 7. The voice and the timing

- **The voice:**
  - one Kokoro voice for the channel, chosen from three samples at Checkpoint A on the first project and recorded in
    the Brief;
  - generated **line by line**, then joined with pauses (0.15 s at a comma-like break, 0.35 s between sentences, 0.6 s
    at a section change), so a bad line is regenerated alone;
  - speed 1.0 to 1.1.
- **Spoken and shown text:** `script.json` holds each line twice: `say` (what Kokoro reads: "one thousand dollars",
  "wack") and `show` (what captions and scenes display: "$1,000", "WACC"). `lexicon.json` keeps pronunciations across
  projects; the Librarian adds new entries.
- **Cleanup:**
  - high-pass 80 Hz, gentle compression, true peak at most -1 dBTP;
  - levelled to -16 LUFS in `voice.wav` (the Packager masters the whole reel to -14 LUFS with the music).
- **Alignment** (`align-script.py`):
  - Parakeet transcribes `voice.wav`;
  - the aligner matches the recognised words to the `say` words (sequence alignment, tolerant of spelling) and gives
    each `show` word the time of the `say` words it stands for;
  - it writes `transcript.json` as `{"words": [{"text", "start", "end"}]}`, the shape the kit and Reels already read.
- **The alignment check:** under 98% of `say` words matched, or a gap inside a sentence over 1.2 s, is a FAIL. It names
  the line, and the Voice agent fixes the pronunciation and regenerates that line.
- **Disclosure:** the posting checklist reminds the creator that a realistic AI voice may need the platform's AI label
  (Meta's "AI info"). The creator checks the platform's current rule.

## 8. Checks (gates)

| Gate | Fails when |
|---|---|
| E1 Script | the length is outside the target (2.7 words a second; 60 to 90 s is 160 to 240 words); the hook's first line is over 12 words; a fact has no source; there is no payoff or no call to action |
| E2 Voice | under 98% of words align; a gap inside a sentence is over 1.2 s; the peak is over -1 dBTP; the length is more than 10% off the target |
| E3 Compose | a scene is outside the scene area or in the caption band; a number on screen has no source; an anchor doesn't resolve; scenes overlap more than 0.3 s; the custom-scene contract (6.4) is broken |
| E4 Pacing | the kit's `beat-check` (entrances 0.15 to 0.25 s before their word) and `gap-scan` (no stretch over about 4 s without a change; the caption layer is excluded) |
| B Checkpoint | guided stills of every scene (`reels-safezone.py`) plus the voiceover, approved by the creator |
| QA | Reels QA unchanged: size, 60 fps, bitrate, black frames, -14 LUFS after packaging, captions matching the final audio |

## 9. Testing

The same standard as Reels: each script has unit tests written to fail first, run with `python3 -m unittest tests`.
- **`explainer-compose.py`:**
  - every scene type builds;
  - the safe zone and caption band hold at both column widths;
  - word anchors resolve, and bad anchors fail;
  - the custom-scene contract is enforced (each violation fails);
  - the kit's `beat-check` and `gap-scan` run on the output.
- **`align-script.py`:** exact matches; skipped words; substitutions; `say`/`show` pairs ("one thousand dollars" to
  "$1,000"); the 98% gate.
- **`tts-kokoro.py`:**
  - tested with a stand-in engine (a fake, like the fake `npx` in snap-beats): line splitting, the pause lengths, the
    regenerate-one-line path;
  - a real Kokoro smoke test that runs when the model is installed and is reported as skipped (never silently passed)
    when it isn't.
- **End to end:** one synthetic explainer (a stand-in voice, a few scenes) composed, checked and rendered with
  HyperFrames, then the kit's `verify-render.py`.

## 10. When something fails

| Problem | Owner |
|---|---|
| a wrong or unsourced fact; too long or too short | Writer |
| a mispronounced, skipped or rushed word | Voice (lexicon entry, then regenerate the line) |
| a scene early, late or wrong for the words | Director, then Animator |
| layout, overlap, custom-scene contract | Animator |
| black frames, size, frame rate | Renderer |
| loudness, music level, package | Packager |

An agent fixes and re-checks once; a second failure of the same check goes to the creator.

## 11. Files and install

```
Editing-Workflow/explainer/
├── SPEC.md                         this document
├── README.md                       the team, install, how it was verified (written with the build)
├── RESEARCH.md                     what works in faceless explainer reels, with sources
├── skill/explainer/
│   ├── SKILL.md                    the Producer
│   ├── PLAYBOOK.md                 the doctrine (§E0 ...)
│   ├── tokens.json                 the look
│   ├── lexicon.json                pronunciations
│   └── scripts/
│       ├── explainer-compose.py
│       ├── scenes/                 one module per scene type
│       ├── tts-kokoro.py
│       ├── align-script.py
│       └── tests/
└── agents/
    explainer-writer.md · explainer-voice.md · explainer-director.md · explainer-animator.md
```

- **Install:**
  1. the kit and the Reels skill (for the reused agents and scripts);
  2. `cp -R` this skill and its agents, as the other READMEs show;
  3. `pip install kokoro` and its phonemizer dependency.
- **Repository updates:**
  - the workflow README lists the third profile;
  - the STATUS Brief template gains a **Voice** row.

## 12. Not in version 1

- An on-screen character or mascot.
- Hindi or other languages.
- Generated music.
- 16:9 versions.
- Automatic promotion of custom scenes into the library.
- Real logos or screenshots fetched automatically (only when the creator supplies them).

## 13. Risks and open items, settled during the build

1. **Kokoro:** confirm the licence of the weights and the voices on the model card. Pick the three sample voices.
   Measure its speed on CPU.
2. **Alignment on synthetic speech:** confirm that Parakeet's word times on Kokoro audio are good enough for 0.15 to
   0.25 s caption and entrance accuracy. Fallback: Kokoro's own token timings, if the installed version exposes them.
3. **Network:** the cloud environment must allow Hugging Face's hosts before the first real run. Local runs are not
   affected.
4. **Platform rules:** confirm the current AI-label rule for realistic AI voices on Instagram, Shorts and TikTok.
5. **The monospace label font:** pick one under SIL OFL, available from npm or PyPI so installs work offline.
