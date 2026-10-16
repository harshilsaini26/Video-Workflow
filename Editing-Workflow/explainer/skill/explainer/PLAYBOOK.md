# Explainer playbook

The doctrine for faceless, code-animated explainer reels: 60 to 90 s, vertical, an AI voice, word-timed captions and
a scene for every moment. The Producer and every explainer agent read it at the start of every project. The evidence
behind each rule is in the workflow repository's `Editing-Workflow/explainer/RESEARCH.md`; the design in its `SPEC.md`.

Paths: `ES=.claude/skills/explainer` (this skill), `RS=.claude/skills/reels`, `SK=.claude/skills/youtube-edit`,
`W=videos/<project>`.

## §E0 The profile

- **What it makes:** a 1080x1920, 60 fps reel, 60 to 90 s, with no camera footage. A voice explains one idea; the
  picture is built in code (HyperFrames + GSAP) from a library of scenes, plus Claude-written custom scenes.
- **Free only:** Kokoro-82M for the voice (Apache-2.0, runs locally), Parakeet for timing, HyperFrames, FFmpeg, KaTeX
  (MIT), Lucide icons (ISC), simple-icons for brand marks (CC0 data; each mark is its owner's trademark, shown only to
  name the brand), Chrome on the creator's machine for page screenshots, DM Sans and JetBrains Mono (OFL, bundled in
  `assets/fonts/`), and a music pad and sound effects the composer generates. No paid voice, stock, AI video or avatar.
- **The layers:** a background (blue, black or light) with three soft orbs drifting across it, one scene at a time in
  the scene area (x 65 to 1015, y 520 to 1248; 780 px wide below y 960), a transition layer, and captions in the band
  at y 330 to 470. Under the voice, a sound bed (§E3.7). Nothing else goes on screen.
- **The look** lives in `$ES/tokens.json`: change it once and every scene follows.
- **Reused from Reels unchanged:** the renderer, QA, packager, librarian and analyst, and their checks (Reels PLAYBOOK
  §R3 safe zone, §R10 free sources).

## §E1 Hook and structure

1. **The hook is line 0, at most 12 words**, and it promises something specific: a number, a mistake, a secret, a
   result ("3 certificates finance bros gatekeep"). The first scene starts entering at frame 0 and is fully on screen
   by 1.0 s (QA checks this instead of Reels' 0.35 s: every scene fades in).
2. **One idea per reel.** If the script needs "and also", it is two reels.
3. **The shape:** hook (0 to 3 s) → why it matters (one line) → the steps or the evidence (most of the time) → the
   payoff (the promise kept, named in `payoff`) → the call to action (`cta`), in the last 5 s.
4. **Every 1.5 to 3 s something changes:** a new scene, a new item, a count, a highlight, a step in a build-up scene
   (the reference reels change their picture every 1.5 to 2 s). `pace-check.py` (gate E4) fails a still stretch over
   3 s and warns over 2 s. The living layer (§E6.6) keeps the picture moving in between, but it never counts as a
   change. The kit's gap-scan cannot see this here, since scenes always cover the voice.
5. **The ending is the payoff or the CTA**, never a fade, a logo sting or "thanks for watching".

## §E2 Script rules

1. **Length:** 2.7 words a second; 60 to 90 s is **160 to 240 words** (`script-check.py`, gate E1). A target length
   (60 to 90 s; anything else fails) narrows that to its own ±15%.
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
   `plan-storyboard.py` turns the hints into the draft storyboard (§E4.8); a line without one becomes a draft title
   the Director must replace.

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

## §E4 Scenes and pacing

1. **Pick the scene by what the words do** (data fields as the storyboard writes them; every scene also has `type`,
   `id`, `bg`, `in`, `out`, and `source` when it shows a number or a claim):

   | The words... | Scene | Data |
   |---|---|---|
   | make a claim or name the topic | `title` | `text`, `kicker`, `size` (72 to 132, default 104) |
   | count steps ("the first", "number two") | `number` | `n` (1 or 2 characters), `name` |
   | land one number | `count-up` | `value`, `prefix`, `suffix`, `decimals`, `sub` |
   | list 2 to 4 things | `list-cards` | `items[{label, at}]` |
   | list 2 to 4 things with a picture each | `icon-row` | `items[{icon, label, at}]` (a Lucide icon name) |
   | show change over time | `line-chart` | `points`, `x`, `label`, `prefix`, `suffix`, `reveal[{point, at}]` |
   | compare amounts | `bars` | `rows[{label, value, text, hi, at}]` (2 to 5) |
   | say how long something takes | `duration` | `value`, `unit` (hours, days, weeks), `style` (clock, dial) |
   | ask the viewer's questions | `qa-stack` | `items[{text, em[], at}]` (at most 5) |
   | name a website, course or product | `browser` | `title`, `subtitle`, `badges[]`, `button`, `domain`, or `screenshot` (a PNG from `snap-page.py`) |
   | name a company, school or product by its mark | `logo-card` | `logo` (a simple-icons slug) or `src` (an image), `name`, `badge`, `sub` |
   | walk through a process | `flow` | `nodes[{label, icon, at}]` (2 to 4) |
   | build one thing on another | `stack` | `items[{label, at}]` (2 to 5, the first at the bottom) |
   | set two things against each other | `compare` | `left` / `right{title, items[{text, at}]}` (1 to 4), `winner{side, at}` |
   | walk through a plan or a history | `timeline` | `steps[{label, sub, at}]` (2 to 5) |
   | count named things ("three certificates") | `cards` | `cards[{title, sub, at}]` (1 to 4), `focus{card, at}` |
   | name the parts of one idea | `hub` | `center` (one short word), `items[{label, at}]` (2 to 6) |
   | walk through a table or a calculation | `sheet` | `rows[[...]]` (at most 8), `highlight{row or cell, at}`, `formula` |
   | give a formula | `formula` | `tex`, `parts[{tex, at}]` (KaTeX) |
   | need something the library can't show | `custom` | `box{x, y, w, h}`, `html`, `build` (§E6.5) |

2. **Ids** are letters, digits and `_` (the page builds `<id>-...` ids from them), never `stage`, `captions`, `voice`,
   `bg<n>` or `cap<n>`.
3. **Anchors, not seconds:** every `in`, `out` and item `at` is `word:N`, the Nth display word in `transcript.json`.
   An entrance lands 0.2 s before its word; the kit's beat-check holds it to 0.15 to 0.25 s.
4. **No dead air:** scenes cover the whole voice; more than 0.3 s with no scene fails the build. Scenes hand over with
   the old one exiting while the new one enters (at most 0.3 s of overlap). The last scene runs to `"end"`.
5. **One hero element per scene**; never the same scene type three times in a row.
6. **Backgrounds** mark sections: change `bg` where the script's `section` breaks are, not on every scene.
7. **Fit by construction:** each scene knows its height; the composer centres it, narrows it below y 960, and fails a
   word wider than its column. Shorten the words, never shrink the type below the scene's minimum.
8. **Start from the planner:** `plan-storyboard.py` writes the draft storyboard from the script's `viz` hints (§E2.7)
   and the aligned words: each hint's items on the words that say them, money and percent figures as count-ups,
   numbered steps as numbers, known brands as logo cards, the rest as draft titles. The Director edits the draft
   (replacing every draft title with a picture) rather than writing scenes and anchors by hand. Custom scenes: at most
   one a reel.

## §E5 Captions

1. **Phrases of up to 4 words and 24 characters**, in the band at y 330 to 470, cleared at a pause of 0.35 s or more.
2. **The word being spoken turns from dim to full colour**; on the light background the colours invert.
3. **Emphasis words get the highlight box** (an accent fill with corner handles), matched without punctuation or case,
   every time they are said.
4. **Captions show `show`, timed across `say`:** "$1,000" stays on screen for all of "one thousand dollars".
5. Captions never repeat a scene's on-screen title word for word for more than about 2 s; if they would, show a
   picture instead (the composer WARNs on a title that says what the voice is saying; the hook is exempt).

## §E6 Motion

1. **Entrances ease out** (`tokens.motion.enter_ease`, 0.42 s); **exits ease in and are shorter** (0.28 s).
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
6. **The living layer:** the picture never stands still. Three orbs drift behind every scene on a fixed path; each
   scene pushes in slowly (to 1.045) for as long as it is on screen; and each build-up scene keeps an idle motion going
   while it holds (a pulse down a connector, a float, a breathing dot, a slow turn). None of this counts as a change
   for pace-check (§E1.4): it keeps the picture alive between changes, it is not one.
7. **Transitions are automatic:** the first scene fades up, a scene on a new background wipes it in as a growing
   circle, and the rest alternate a zoom and a push, the old scene leaving to match. A scene can name its own with
   `"transition"`: `fade`, `push`, `zoom`, `wipe`, `burst` (a spray of colour, for a hook or a reveal) or `cut`.

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
