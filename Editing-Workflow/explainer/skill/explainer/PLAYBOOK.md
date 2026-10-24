# Explainer playbook

The doctrine for faceless, code-animated explainer reels: 30 to 90 s, vertical, an AI voice, word-timed captions and
a scene for every moment. The Producer and every explainer agent read it at the start of every project. The evidence
behind each rule is in the workflow repository's `Editing-Workflow/explainer/RESEARCH.md`; the design in its `SPEC.md`.
How a reel looks and moves (fill the frame, motion with a reason, velocity-matched cuts, a bespoke hook) is in
`$ES/MOTION.md`, read with this one.

Paths: `ES=.claude/skills/explainer` (this skill), `RS=.claude/skills/reels`, `SK=.claude/skills/youtube-edit`,
`W=videos/<project>`.

## §E0 The profile

- **What it makes:** a 1080x1920, 60 fps reel, 30 to 90 s, with no camera footage. A voice explains one idea; the
  picture is built in code (HyperFrames + GSAP) from a library of scenes, plus Claude-written custom scenes.
- **Free only:** Kokoro-82M for the voice (Apache-2.0, runs locally), Parakeet for timing, HyperFrames, FFmpeg, KaTeX
  (MIT), Lucide icons (ISC), simple-icons for brand marks (CC0 data; each mark is its owner's trademark, shown only to
  name the brand), Chrome on the creator's machine for page screenshots, DM Sans and JetBrains Mono (OFL, bundled in
  `assets/fonts/`), and a music pad and sound effects the composer generates. No paid voice, stock, AI video or avatar.
- **The layers:** a Catppuccin Latte ground (`mantle` #e6e9ef and `base` #eff1f5, strong `blue` #1e66f5, dark `ink`
  #4c4f69: the planner sets a rhythm, MOTION.md §1.3) with faint glows that travel with each cut and particles drifting
  for the whole reel, one scene at a time scaled up to fill the scene area (x 65 to 1015, y 345 to 1105, the centre of
  the frame; 780 px wide below y 960) inside a camera that slowly pushes in, a transition layer, and small captions
  under it in the band at y 1130 to 1235 (y 1235 is the one bottom line for any text, in the composer, gate E5 and
  QA). Under the voice, a sound bed
  (§E3.7). Nothing else goes on screen.
- **The look** lives in `$ES/tokens.json`: change it once and every scene follows.
- **Reused from Reels unchanged:** the renderer, QA, packager, librarian and analyst, and their checks (Reels PLAYBOOK
  §R3 safe zone, §R10 free sources).

## §E1 Hook and structure

0. **The brief before the script:** who the reel is for and the pain it solves (`audience`), what it should get
   (`goal`: follow, comment, save, share, link, learn) and its shape (`format`). The call to action asks for the goal;
   `script-check.py` warns when any of these is missing or the call to action asks for something else.
1. **The hook is line 0, at most 12 words**, and it promises something specific: a number, a mistake, a secret, a
   result ("3 certificates finance bros gatekeep"). The first scene starts entering at frame 0 and is fully on screen
   by 1.0 s (QA checks this instead of Reels' 0.35 s: every scene fades in).
2. **One idea per reel.** If the script needs "and also", it is two reels, or a **series**: name it and number the
   parts (`brand.series`, `brand.part`: "PART 2" shows on every frame) and let the call to action promise the next.
   **Short wins:** 30 to 60 s for a how-to or a single point; up to 90 s only when the idea needs it.
3. **The shape:** hook (0 to 3 s) → why it matters (one line) → the steps or the evidence (most of the time) → the
   payoff (the promise kept, named in `payoff`) → the call to action (`cta`), in the last 5 s.
   **Formats** (the shapes that spread for informative reels; `script-check.py` warns when a format's shape is
   missing): `how-to` (a problem solved in steps, `role: step`), `versus` (this vs that, a `compare` picture), `myth`
   (the common belief, then the truth: `role: myth`, then `role: truth`), `story` (a mini case study or anecdote: the
   problem, then the solution, `role: problem` then `role: solution`), `explainer` (one concept made simple).
4. **Every 1.5 to 3 s something changes:** a new scene, a new item, a count, a highlight, a step in a build-up scene
   (the reference reels change their picture every 1.5 to 2 s). `pace-check.py` (gate E4) fails a still stretch over
   3 s and warns over 2 s. Ambient motion (§E6.6) never counts as a change. The kit's gap-scan cannot see this here, since scenes always cover the voice.
5. **The ending is the payoff or the CTA**, never a fade, a logo sting or "thanks for watching".

## §E2 Script rules

1. **Length:** the spoken words at the voice's own measured rate (`voice-rates.json`, written by the samples; 2.4 words
   a second for am_michael until measured) plus the pauses between lines; 30 to 90 s (`script-check.py`, gate E1). A
   target (30 to 90 s; 90 is a target too) narrows that to its own ±15%. At most 3 section breaks every 75 s. The
   script is voiced once before Checkpoint A and `script-check.py --voice` gives its real length; over 90 s it lists
   the lines to trim, and the creator decides (SOP S4, S5, S16).
2. **Every line twice:** `say` is what the voice reads ("one thousand dollars", "wack"); `show` is what the screen
   shows ("$1,000", "WACC"). Numbers are shown in full digits (1,000, never 1K).
3. **Short lines:** one breath, one clause. A line over about 18 words gets split.
4. **Breaks:** `comma` (0.15 s) inside a thought, `sentence` (0.35 s) between thoughts, `section` (0.6 s) where the
   scene changes topic.
5. **Plain words.** A term the viewer may not know is defined on screen the first time (a `title` kicker or a `qa-stack`).
6. **Emphasis** (`emphasis` on a line, `captions.emphasis` in the storyboard): at most one word a line, and only the
   word carrying the point.
7. **A picture for every line:** the Writer adds a `viz` hint to each line that names something to show (a scene type
   from §E4.1 and its items as plain words: `{"type": "flow", "nodes": ["Retrieve", "Augment", "Generate"]}`).
   A line over about 3 s gets a list of hints, each after the first starting on a word of the line (`"from": "large"`).
   `plan-storyboard.py` turns the hints into the draft storyboard (§E4.8); a line without one becomes a draft title
   the Director must replace. A hint may carry a **`headline`** (§E4.11: `{"text": "No battery", "at": "battery",
   "aside": "seriously?", "aside_at": "seriously"}`, words for its anchors), and the script may carry a **`look`**
   (`paper` or `latte`) and a **`thread`** (§E4.12: its keys' `at` are words of the voice, in order).
8. **Talk to one viewer:** "you" and contractions, never "users" or "one"; one question to the viewer (in the hook
   or the call to action) so the comments have something to answer; one real example (`role: example`: a case, a
   number, a short story) because a concrete case is what people remember; humour only where it serves the point
   (one light line, never a sketch). `script-check.py` warns when a script never says "you", asks nothing or gives no
   example.
9. **Plain spoken words** (the kit's `wording.py`, run by `script-check.py`): no preamble in the hook ("hey guys", "in
   this video", "stop scrolling"; E1 fails it), no leaked AI text or invisible characters (fail); no stock phrases
   ("here's the thing", "game changer", "let's dive in"), no "it's not X, it's Y" or "No X. No Y. Just Z." shapes, no
   dash in `say` (the voice reads it as a pause: use a break), a hook with a number or a name in it that is said in
   3 s, lines of 18 words or fewer (warnings). The writer fixes what is named; nothing is rewritten automatically.
   **Do not over-correct:** contractions and one natural list of three are fine; never add hedges, "honestly", or a
   number to sound human (every number is sourced, §E7). The lists credit the repositories they came from
   (RESEARCH.md › Credits).

## §E3 Voice

1. **One voice for the channel.** At Checkpoint A of the first project, the creator picks from three 10 s samples
   (`af_heart`, `am_michael`, `bf_emma`); the Brief records it, and it never changes without the creator.
2. **Line by line:** `tts-kokoro.py` voices each line to `lines/<id>.wav`; a bad line is fixed and regenerated alone
   with `--only <id>`. Speed 1.0 to 1.1.
3. **Pronunciation first in the lexicon:** a misread term gets a `lexicon.json` entry (whole word, case-sensitive),
   not a respelling in one script, so it stays fixed in every project. The Librarian keeps the lexicon.
4. **Levels:** `voice.wav` is high-passed at 80 Hz, gently compressed and levelled to -16 LUFS with the true peak at
   most -1 dBTP. The Packager masters the whole reel to -14 LUFS with the music.
5. **Gate E2:** at least 98% of the `say` words are heard back by Parakeet; no gap inside a line over 1.2 s; the
   true peak at most -1 dBTP; the length within 10% of the target (`align-script.py`, `tts-kokoro.py`). A failure names the line.
6. **Disclosure:** a realistic AI voice may need the platform's AI label (Meta's "AI info"); the posting checklist
   reminds the creator, who checks the platform's current rule. The voice never imitates a real person.
7. **The sound bed:** the composer writes `bed.wav` under the voice: by default a generated pad (soft chords, made on
   the creator's machine, nothing to license), or the creator's own track (`"sound": {"music": "music/<file>"}`, its
   licence in SOURCES.md), looped, faded and ducked under the voice so the reel never drops to silence between lines;
   a whoosh ahead of each moving transition and a pop as items land (`"sfx": false` turns them off; `"music": "none"`
   for no music). The Packager levels the reel with the bed already in it.
8. **A chime on the payoff:** the payoff's first scene lands with a soft two-tone chime (the planner marks it
   `"chime": true`), the one sound the viewer remembers the point by; a pop never sounds on top of it. A trending
   sound is the creator's call at posting, only when it fits, under the voice.

## §E4 Scenes and pacing

1. **Pick the scene by what the words do** (data fields as the storyboard writes them; every scene also has `type`,
   `id`, `bg`, `in`, `out`, and `source` when it shows a number or a claim):

   | The words... | Scene | Data |
   |---|---|---|
   | open the reel (the hook) | `kinetic` | `big{text, at}` (a number or capitals, 4 characters), `words[{text, at}]` (1 or 2), `line{text, at}`, `strike{word, at}` (a word of the line), `punch{text, at}` (1 or 2 words) |
   | make a claim or name the topic | `title` | `text`, `kicker`, `size` (72 to 132, default 104) |
   | count steps ("the first", "number two") | `number` | `n` (1 or 2 characters), `name` |
   | land one number | `count-up` | `value`, `prefix`, `suffix`, `decimals`, `sub` |
   | list 2 to 4 things | `list-cards` | `items[{label, at}]` |
   | list 2 to 4 things with a picture each | `icon-row` | `items[{icon, label, at}]` (a Lucide icon name) |
   | show change over time | `line-chart` | `points`, `x`, `label`, `prefix`, `suffix`, `reveal[{point, at}]`, `shape` (line, or step: a level, then the jump) |
   | compare amounts | `bars` | `rows[{label, value, text, hi, at}]` (2 to 5) |
   | say how long something takes | `duration` | `value`, `unit` (hours, days, weeks), `style` (clock, dial) |
   | ask the viewer's questions | `qa-stack` | `items[{text, em[], at}]` (at most 5) |
   | name a website, course or product | `browser` | `title`, `subtitle`, `badges[]`, `button`, `domain`, or `screenshot` (a PNG from `snap-page.py`) |
   | name a company, school or product by its mark | `logo-card` | `logo` (a simple-icons slug) or `src` (an image), `name`, `badge`, `sub` |
   | walk through a process | `flow` | `nodes[{label, icon, at}]` (2 to 6; 5 or 6 travel down a window, the camera moving to each step) |
   | build one thing on another | `stack` | `items[{label, at}]` (2 to 5, the first at the bottom) |
   | set two things against each other | `compare` | `left` / `right{title, items[{text, at}]}` (1 to 4), `winner{side, at}` |
   | walk through a plan or a history | `timeline` | `steps[{label, sub, at}]` (2 to 5) |
   | count named things ("three certificates") | `cards` | `cards[{title, sub, at}]` (1 to 4), `focus{card, at}` |
   | name the parts of one idea | `hub` | `center` (one short word), `items[{label, at}]` (2 to 6) |
   | walk through a table or a calculation | `sheet` | `rows[[...]]` (at most 8), `highlight{row or cell, at}`, `formula` |
   | give a formula | `formula` | `tex`, `parts[{tex, at}]` (KaTeX) |
   | land a hero figure ("8 HOURS", "+$363") | `stat` | `value`, `prefix`, `suffix`, `unit`, `decimals`, `label`, `at` (200 to 320 px; needs a source) |
   | ask and answer (an assistant, a support bot) | `chat` | `name`, `messages[{role, text, at, cite{text, at}}]` (2, 4 or 6, user first) |
   | show the passage a system found | `doc` | `name`, `title`, `blocks[{text, at, tag} or {filler: n}]` (a block with `at` highlights) |
   | let the words be the picture | `giant-captions` | `keywords[]` (the voice's own words, 1 to 3 at a time, 120 to 200 px; the caption band steps aside) |
   | words or tools piling up | `gravity-drop` | `items[{text, at}]` (2 to 8), `style` (chips or words) |
   | open a chapter | `title-card` | `kicker`, `title` (6 words at most), `subtitle` (or `{text, at}`) |
   | cross one thing out (and bring its replacement) | `icon-strike` | `icon`, `label`, `at`, `strike{at}`, `replacement{icon, label, at}` |
   | say what is not there ("no case, no battery") | `crossed-list` | `prefix` (mono, over each row, 12 characters at most), `items[{text, at, strike}]` (2 to 5, hero face; `strike` draws a line through and greys the row) |
   | say what it costs | `price-sticker` | `price` (8 characters at most), `label` (mono, 28 at most), `src` (a product image, any aspect), `at` (needs a source) |
   | draw one thing, with an aside | `line-art` | `icon` (Lucide) or `svg` (the creator's stroke-only SVG; a filled shape fails), `caption` (serif aside, 14 words at most), `at`, `strike` (crosses the caption out) |
   | compare sizes in 3D (deals, models, market share) | `bars-3d` | `bars[{label, value, at, text?, hi?}]` (2 to 4; labels 10 characters at most), `floor` (a caption under it, 24 at most); needs a source |
   | "every piece connects", "solve it step by step" | `cube` | `at`, `labels` (9 cells, 3 characters each; default A1 to C3), `turns[{dir: left/right/up/down, at}]`, `twist[{dir: left/right, at}]` (the top layer), `highlight{cell, at}` |
   | count steps or options in 3D | `cards-3d` | `cards[{text, sub?, at}]` (1 to 4; `text` a mark of 3 characters at most, never a figure; `sub` 16 at most) |
   | "what's inside", the deal book, the prep | `briefcase` | `at` (it lands), `open` (the lid swings up and papers rise), `papers` (1 to 5), `label` (a caption under it, 24 at most) |
   | parts of a whole that stack (debt and equity, a price's make-up) | `beaker` | `layers[{label, value, at, text?}]` (1 to 4, bottom up; values are shares of the glass, 100 at most); needs a source |
   | parts of a whole that share (who pays, market share) | `donut` | `slices[{label, value, at, text?}]` (2 to 5), `center` (the total, 9 characters at most, in the hole); needs a source |
   | one key metric as an object (EPS, ROI, WACC) | `coin` | `text` (4 characters at most, never a figure), `dir` (up or down: an arrow on the face), `sub` (a line under it, 22 at most), `at` (it spins in) |
   | two sides weighed (cost against value, risk against return) | `balance` | `left`, `right` (each {`label` 12 at most, `at`}: a weight drops into its pan), `tip` ({`to`: left or right, `at`}: that side goes down; without it the scale stays level), `note` ({`text` 24 at most, `at`}: a line above the beam) |
   | the call to action: comment a word | `comment-cta` | `keyword{text, at}`, `gets{text, at}` |
   | what people say | `comment-drop` | `comments[{name, text, likes, time, at}]` (2 to 4) |
   | typing into an AI | `prompt-bar` | `prompt{text, at}`, `send{at}`, `reply{text, at}` |
   | planning shots | `storyboard-deck` | `frames[{note, sketch, at}]` (2 to 4; sketch face, screen, chart, wide or title) |
   | bringing files in | `file-drop` | `files[{name, size, icon, at}]` (1 to 4), `done{label, at}` |
   | cutting a video | `nle-timeline` | `tracks[{kind, clips[{label, length}]}]`, `cuts[{track, time, length, at}]` |
   | removing what you don't need | `jiggle-delete` | `tiles[{label, icon, at}]` (3 to 8; a tile with `at` is deleted then), `jiggle{at}`, `done{at}` |
   | grading a picture | `grade-slider` | `src`, `sliders[{kind, label, from, to, at}]` (contrast, saturation, exposure, temperature) |
   | picking a colour from a picture | `eyedropper-grade` | `src`, `picks[{color, label, x, y, at}]` (Latte colour names) |
   | giving a picture a film look | `film-look` | `src`, `at`, `title`, `before`, `after` |
   | many videos at once | `playing-grid` | `src`, `cols`, `tiles[{label, src, at}]` (4 to 9), `pick{tile, at}` |
   | one video | `video-card` | `src`, `title`, `channel`, `meta`, `duration`, `start`, `play{at}` |
   | the reels feed | `reel-feed` | `src`, `reels[{user, caption, likes, comments, shares, at}]` (2 to 3) |
   | a sound, and how it changes | `waveform` | `states[{kind, label, at}]` (1 to 4; noise, calm, music, pulse or flat), `color` (ink or accent) |
   | switching modes (noise cancelling, a setting) | `mode-switch` | `options[{label, wave, note, at}]` (2 to 4, left to right; a label of 10 characters at most, a waveform kind) |
   | show the product itself, big, with its name behind it | `product-hero` | `src` (a cut-out PNG is best), `alt`, `aspect` (width / height; the composer notes the right value), `title` (behind it, 124 to 200 px), `title_at`, `at`, `notes[{x, y, label, at, mark, side}]`, `float` |
   | show real photos, credited | `photo-grid` | `photos[{src, credit, tag, at}]` (1 to 4; every photo needs a `credit`), `layout` (stack 1 to 3, grid 1 to 4, collage 2 to 4), `notes[]` (on the first photo) |
   | need something the library can't show (only when the creator asks) | `custom` | `box{x, y, w, h}`, `html`, `build` (§E6.5) |

2. **Ids** are letters, digits and `_` (the page builds `<id>-...` ids from them), never `stage`, `captions`, `voice`,
   `bg<n>` or `cap<n>`.
3. **Anchors, not seconds:** every `in`, `out` and item `at` is `word:N`, the Nth display word in `transcript.json`.
   An entrance lands 0.2 s before its word; the kit's beat-check holds it to 0.15 to 0.25 s.
4. **No dead air, no double exposure:** scenes cover the whole voice; more than 0.3 s with no scene fails the build.
   A scene ends where the next begins (its `out` is the next one's `in`): the old one's exit is over by the cut, and
   gate E5 checks every cut (SOP S9). The last scene runs to `"end"`. A scene holds at most 8 s (E4; a travelling flow
   may hold longer), and the hook's items land by 0.8 s (E3, SOP S8).
5. **One hero element per scene**; never the same scene type three times in a row.
6. **Grounds keep a rhythm** in the `latte` look: the hook on `ink`, the payoff on `blue`, `mantle`/`base` by section,
   a `blue` beat every third scene in a section (the planner sets it; MOTION.md §1.3). The `paper` look keeps **one
   ground** (`base`, the warm paper): colour comes from the images and the one accent (MOTION.md §1.6).
7. **Fit by construction:** each scene knows its height; the composer scales it to fill the scene area, narrows it
   below y 960, and fails a word wider than its column. A scene too tall may shrink to 0.8, never under 28 px text;
   past that, drop a row or an item (the captions carry the words) and **never split a scene to fix its height**. The hub works out its own geometry (every node clears the middle and every other node), a formula shrinks
   itself to its row, and the kinetic hook sizes each row to the width it is given.
8. **Start from the planner:** `plan-storyboard.py` writes the draft storyboard from the script's `viz` hints (§E2.7)
   and the aligned words: each hint's items on the words that say them, money and percent figures as count-ups,
   numbered steps as numbers, known brands as logo cards, the rest as draft titles. The Director edits the draft
   (replacing every draft title with a picture) rather than writing scenes and anchors by hand. The hook is a
   `kinetic` scene from the script's hint; custom scenes only when the creator asks for one.
9. **Never a bare stage:** something shows on a scene's first word. The build-up scenes and list-cards show every
   piece as an empty slot from the start (its outline, its words hidden) and fill each one on its word; any other scene whose first change comes over 0.8 s
   after it starts gets a WARN from the composer (start the scene later, or put an item on its first word).
10. **Gate E5, a clean picture:** `layout-check.py --index public/index.html` opens every scene in Chromium on the
   creator's machine at the moment it is fully built and fails on text over text, text covered by or crossing a shape
   that is not its card, text spilling out of its card, anything outside the safe area, and text under 28 px;
   `hyperframes check` at the same moments adds clipped text and WCAG contrast. No tokens; every failure names the
   scene and the text. Run after every compose, before any still goes to the creator.

11. **Headlines** (`"headline"` on any placed scene; `headline.py`): the scene's title top-left in the look's hero
   face, the scene's picture centred under it. Upper case unless `"case": "as-is"`; at most three lines and 260 px
   (the fewest lines that stay big); `accent` words in the accent; a mono `kicker` above and `sub` below; an
   Instrument Serif italic `aside` ("seriously?", "Yes." in the accent). The lines rise on `at`, the aside on
   `aside_at`. E3 names a headline that leaves the scene too little room: shorten it or drop an item.
12. **The thread** (`"thread"` in the storyboard; `thread.py`): one line through the whole reel, as the reference's cable
   runs from scene to scene. Keys `{"at", "shape", ...}` in time order, shapes `drop`, `loop`, `wave`, `rule`,
   `underline`, `off`; it draws on at the first key and morphs on each later key's word. It runs above the ground and
   under the scenes and the captions, may pass behind a scene's words (E5 treats it as the ground), and each morph is
   a change for E4. No key's shape rests in the captions (y 1130 to 1235, x 150 to 930; E3 names the key): a stem goes
   down the outer edge (x under 150 or over 930), a loop or a wave sits above or below the band (a morph across the
   band passes behind the captions, under their halo). Use it for continuity: the line that drops in becomes the loop round a year, the wave under a
   sound, the ruler of a timeline; take it `off` when the story moves on.
13. **Images** are the creator's (`src`, relative to storyboard.json; PNG, JPEG, WebP or GIF; sized from their own
   headers): a product cut-out in `product-hero`, photos in `photo-grid`, each photo with a `credit` shown on it (E3
   fails a photo without one). Notes over an image (`notes`: a circle drawn on, a leader, a pill label) point at what
   the voice names. Only a product-hero's title may sit behind its image (`data-depth="behind"`, at least 120 px):
   every other text is never covered.

## §E5 Captions

1. **Phrases of up to 4 words and 24 characters**, 44 px, at most two lines, in the band at y 1130 to 1235 (the
   narrow column, under the scene: the centre is the animation's), with a halo of their ground, cleared at a pause
   of 0.35 s or more.
2. **The word being spoken turns from muted (`overlay2`, 3.3:1 or more) to ink (`text`, 6.6:1 or more).**
3. **Emphasis words get the highlight box** (an accent fill with corner handles), matched without punctuation or case,
   every time they are said.
4. **Captions show `show`, timed across `say`:** "$1,000" stays on screen for all of "one thousand dollars".
5. Captions never repeat a scene's on-screen title word for word for more than about 2 s; if they would, show a
   picture instead (the composer WARNs on a title that says what the voice is saying; the hook is exempt).

## §E6 Motion

1. **Entrances ease out** (`tokens.motion.enter_ease`, 0.42 s); **exits ease in (`power3.in`) and are shorter**
   (0.2 to 0.28 s). **No `back`, `elastic` or `bounce` ease** anywhere: an overshoot reads as cheap (MOTION.md §2).
2. **Staggers total 0.5 s at most**, however many items.
3. **No linear easing on movement.** Linear is for counts, draws and the hub's slow constant turn only.
4. **Items arrive on their words**, not all at once at the scene's start.
5. **Custom scenes** (the contract): the storyboard gives a `box` inside the scene area, an `html` file (relative to
   `storyboard.json`) and a `build` function name. The file holds a `<style>` whose every selector starts with
   `#<id>`, the markup, and a script defining a function named for its scene, `build<Id>(tl, root, t0, t1)` (two
   custom scenes never share a name: the composer refuses it), which adds its tweens to the shared timeline
   between `t0` and `t1` and selects only through `root` or `'#<id> ...'`. The composer refuses `document.body`, a
   selector outside `#<id>`, any network use (`fetch`, a web address, `//host` included, `import()`, CSS `@import`),
   and a missing function. A function defined in a `<script type="module">` (three.js) also needs
   `window.build<Id> = build<Id>;`: a module's names are its own, so the page could not call it. GSAP is always there; KaTeX and three.js come from the local vendor folder. Checkpoint B shows them at in, middle and out;
   one the creator likes is promoted into the library by the Librarian, with a test.
6. **Motion with a reason** (MOTION.md §2): every scene's camera pushes in slowly and steadily (0.95 to 0.995, linear,
   so the picture is never still), but nothing on the content pushes in unless the voice asks for it, and the
   background never drifts: its three glows travel with each cut (up to 380 px across and 420 px down,
   expo.out over 1.2 s, each move written from where the last one ended, so every render is the same) and hold
   between cuts. A build-up scene keeps one
   idle motion while it holds (a pulse down a connector, a float, a slow turn); a screenshot holds still and punches
   in (1.25x) on its `focus` line on that line's word. None of this ambient motion counts as a change for pace-check
   (§E1.4).
7. **Transitions are automatic and velocity-matched:** the first scene fades up, a scene on a new background wipes it
   in as a growing circle, and the rest alternate a zoom-through (the old scene rushes past the viewer into a blur,
   the new one lands from behind) and a whip (the old one flies up, the new one lands from below), each exit
   accelerating into the cut and each entrance decelerating out of it. A scene can name its own with `"transition"`:
   `fade`, `push`, `zoom`, `wipe`, `burst` (a spray of colour, for a hook or a reveal), `cut` or `brush`. In the paper
   look a new ground comes in with the **brush** (five ragged bands cover the frame on the cut and sweep off). Every
   scene leaves, the last one too: **the close** takes it off in the first half of the last 0.4 s and the hook's ground wipes in over the second (the
   last scene runs 1 s at least, or E3 refuses it), so the loop
   seams into the hook. Choose a transition for a reason (MOTION.md §3): a new place, a wipe or brush; the same idea,
   a fade; a jolt, a whip. **`leak`** (a soft streak of light in the accent colours sweeping across over the cut) is
   never chosen on its own: name it for a burst of energy or a reveal.
8. **Fill the frame:** the composer lays each library scene out narrower and scales it up (to 1.8x; a title to
   150 px, a number to 1.3x) to fill the scene area; `moments.json` records each scene's box and scale. Two scenes in
   a row with the same layout get a WARN: change the picture, or merge them into one build.
9. **The hook is kinetic type from data** (`kinetic`, §E4.1): a big accent token, stacked words, a claim struck
   through and a punch, each on its word. No code to write, so a reel costs no tokens beyond its script. Custom scenes
   (§E6.5) are opt-in, only when the creator asks for a moment the library cannot make.
10. **Palettes (colour only, on either look):** `"palette": "<name>"` in script.json or the storyboard recolours the
    reel and keeps the look's fonts, texture and boil. Pick by the subject; leave it out for the look's own colours.

    | Palette | Colours | Mood | Rule | Best for |
    |---|---|---|---|---|
    | `terracotta` | #E07A5F #F2CC8F #81B29A #3D405B #F4F1DE | warm, grounded, unhurried; handmade | #F4F1DE ground, #3D405B text (8.9:1), #E07A5F for shapes and buttons; accent words take it deeper | lifestyle, wellness, artisan food, interiors |
    | `monochrome` | #000000 #2B2B2B #6E6E6E #C4C4C4 #FFFFFF | bold, editorial; composition does the work | no colour; restraint is the effect | fashion, photography, architecture, luxury |
    | `electric-pop` | #FF006E #FB5607 #FFBE0B #8338EC #3A86FF | loud, made to stop a scroll | white ground; only #FF006E and #8338EC (the other three are the signals); never one bright colour on another | youth brands, events, music, entertainment |
    | `nordic-frost` | #CAF0F8 #90E0EF #00B4D8 #0077B6 #03045E | clear, trustworthy | light for grounds, dark for type (#03045E on #CAF0F8), mid tones for accents | tech, SaaS, finance, healthcare |
    | `bold-citrus` | #F94144 #F3722C #F8961E #F9C74F #90BE6D | fun, appetizing | each scene's ground is the next colour, in order; text #2A1D0E | food, fitness, kids, quick service |

    Every palette passes the theme's contrast rules on every ground and gate E5 on every scene case; a colour too light
    to read as text keeps its hue and is taken deeper for words only, while shapes that carry words (buttons, badges,
    stickers, keyword chips: the `fill` role) keep the exact hex, as Terracotta's #E07A5F buttons with #3D405B on them
    (`tokens.json` palettes; `explainer_lib.palette_tokens`). The creator picks: `palettes.py --for "<topic>"` lists the
    five, best fit first; `plan-storyboard.py --palette <name>` overrides the script's.

## §E7 Sources and claims

1. **Every number, name or claim on screen has a source**: a line whose `show` has a digit, `%` or `$` (or
   `"fact": true`) carries `source`, a key in `SOURCES.md` (gate E1). In the storyboard, a scene whose text shows a
   digit, `%` or a currency sign, and every `count-up`, `line-chart`, `bars` and `duration` scene, carries `source`
   too, and the key must be one of `script.json`'s sources (gate E3; formula TeX aside).
2. **A source is a page someone can open:** the publisher, the title, the date and the link. "Common knowledge" is not
   a source for a number.
3. **Round honestly:** a shown number matches its source to the precision shown.
4. **No invented examples presented as real:** an illustration says so ("say a stock costs $100").

## §E8 Failure patterns

| Pattern | Cause | Fix (owner) |
|---|---|---|
| E2 fails on one line, under 98% | a term Kokoro can't say (an acronym, a name) | `lexicon.json` entry, `--only <id>`, align again: the aligner listens for the lexicon's spelling (Voice) |
| a gap inside a line over 1.2 s | a comma read as a long pause, or a stumble | split the line or reword it (Writer), regenerate (Voice) |
| "no scene from a to b" | a scene's `out` before the next `in` | move the anchor (Director) |
| "overlap by 0.5 s" | the next scene starts before the old one's `out` | end the old scene on the next scene's `in` word (Director) |
| "the hook is not whole on screen by 1.0 s" | a hook item lands after 0.8 s | anchor the hook's pieces to words 0 and 1 (Director; the planner does it) |
| "over the 90 s ceiling" | the voice runs past 90 s | trim the lines `script-check.py --voice` lists, with the creator (Writer) |
| "E4 FAIL: <id> is held 9.0 s" | one picture held over 8 s | split the line's picture into two scenes, or use a flow that travels (Director) |
| "are both on screen" (E5) | two scenes overlap at a cut | the old scene's `out` on the new one's `in`; a custom scene's exit inside its time (Director, Animator) |
| "contrast 2.4:1" (E5) | text too close to what is behind it | the scene's colours come from its ground's roles; a UI mock-up uses the paper roles (the Librarian, with a test) |
| "E6 FAIL: still from 12.3 to 14.0 s" | the rendered picture froze | a build, a camera move or a cut inside that stretch (Director) |
| "SKILL FAIL: ... changed since the pin" | the skill was updated or edited mid-project | tell the creator; re-pin only when they choose (Producer) |
| "wider than the column" | a long single word or number at its size | shorter word, or a smaller `size` within the scene's range (Director) |
| "taller than the scene area" | too many items or long labels | fewer items, or split into two scenes (Director) |
| a caption shows the misheard word | the display words come from `show`, so the script is wrong | fix `show` (Writer), re-align (Voice) |
| a beat-check MISS | the anchor word was changed in the script after the storyboard | re-anchor (Director) |
| a custom scene refused by the lint | a selector outside `#<id>`, `document.body`, a web address | rewrite inside the box (Animator) |
| "nothing changes from a to b" (E4) | a scene holds over 3 s with nothing arriving | an item on a word inside it, a build-up scene, or a new scene (Director) |
| "the title repeats what the voice is saying" | a draft title, or a title made of the line's words | a picture: a `viz` hint or a library scene (Writer, Director) |
| "unknown logo" | the slug is not in simple-icons (or the set is not installed) | the slug from simpleicons.org, or `src` with the creator's image (Director, Animator) |
| a screenshot shows a cookie banner or a sign-in wall | the page needs a click or a login | `snap-page.py` with a longer `--wait`, another page, or the creator's own capture (Director) |
| the voice sounds flat across the reel | every line at the same speed and break | vary the breaks; speed 1.05 on lists (Voice) |
