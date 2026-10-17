# MOTION.md: how an explainer reel moves

Read this before you plan a storyboard (Director) or build a reel (Animator). The scripts enforce what can be checked
(the composer, gate E5's layout-check in Chromium, the contrast pass), on the creator's machine and at no token cost; the
rest is your eye. The bar is the one in motion-graphics-skills: **stunning, or it is not done.** The look follows Apple's
Human Interface Guidelines (clarity, deference, one colour meaning one thing) in Catppuccin Latte.

**Measured against the reference reel** (2026-10-17, the RAG reel beside a reel the creator rates highly): the
reference is still 7% of the time and never longer than 0.5 s, changes its ground between black, strong blue and light
every few seconds, shows real objects (course pages, charts with numbers, a clock, a phone feed) and puts a giant figure
on screen often. The RAG reel was still 67% of the time, sat on one pale ground, held one diagram for 27 s and showed
labelled boxes. The rules below are what closed that gap.

Distilled from three free, open sources, read as references (none of their code runs here):
- [charlie947/motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills): the eight-part brief
  ("the hero fills 60 to 70% of the frame and shows one satisfying change"), the effect recipes, the explainer review
  rules, the reel-export safe zone.
- [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes), `skills/faceless-explainer`: the motion
  language, the cut catalogue, typography and the portrait layout rules.
- [remotion-dev/remotion](https://github.com/remotion-dev/remotion), the prompt-to-motion-graphics skills: springs and
  expo-out arrivals, "never constrain content to a small centred box".

## 1. The picture

1. **Fill the frame.** The hero is big: 60 to 70% of the frame, never a small widget in empty space. The composer
   lays every library scene out narrower and scales it up (to 1.8x) to fill the scene area, x 65 to 1015 and y 520
   to 1235 (780 px wide below y 960, clear of Instagram's buttons and caption). **Text and card edges end by y 1235**,
   one line for the composer, gate E5 and QA (SOP S7); shapes with no text may run on to y 1650 so the lower frame is
   not left empty. A title grows to 150 px; numbers to 1.3x; a `stat` is 200 to 320 px.
2. **Type is the picture.** A hero word is 120 px or more; a label is 34 px or more after the scale; at most about 5
   words of on-screen text at once, and never the narration's sentence (the captions already say it).
3. **One accent, one meaning; four grounds.** Catppuccin Latte (tokens.json) on four grounds: the light `mantle` and
   `base`, strong `blue`, and dark `ink` (Latte's text colour). On the light ones: ink `text`, secondary `subtext0`,
   cards `base` with a hairline, and **blue is the accent: "what the voice is talking about now"**; on `blue` and `ink`
   the text turns light, cards are outlined in the ground's own colour, and the accent becomes one that shows there
   (light chips on blue, yellow on ink). **Change grounds with the story** (the planner does: the hook on `ink`, the
   payoff on `blue`, light grounds between, a blue beat every third scene in a section): a reel on one pale ground
   reads as one long slide. **UI mock-ups stay light paper on any ground** (a window, a chat, a document, an editor:
   `ctx.pc`), like the reference's white windows on blue. Green, red and peach are signals, always beside a label.
   Every text holds 3:1 against what is really behind it (gate E5; all text is 28 px or more). No gradient text.
4. **Real things, not labelled boxes.** A real logo (simple-icons), a real page (snap-page.py), a real number with a
   source as a giant `stat`, a `chat` with the question and its answer, the `doc` passage a system found, an editor's
   timeline, a phone's reel feed. A box with a word in it is the last resort, not the default.
5. **No two beats look the same.** The composer WARNs when two scenes in a row share a layout: change the picture,
   or merge the two into one build that keeps growing (one object changing beats a new widget every line).

## 2. Motion with a reason

1. **The picture is never still** (changed 2026-10-17, measured: the earlier "nothing moves without a reason" left
   two thirds of the RAG reel's frames frozen). The camera moves through every scene: a steady push-in from 0.95 to
   0.995 (linear, so it never comes to rest; shallower where the scene's smallest text would drop under 28 px) with a 1.5° turn that alternates scene to scene (`.cam`, the composer's), and a field of small squares and
   dots rises behind the scenes for the whole reel. Both are quiet enough to read through and never count as a new
   picture for pace-check. Gate E6 (`motion-check.py`) measures the rendered file: no still stretch over 1 s, under
   15% still (a frame is still when under 0.1% of it changes visibly). **Pieces still arrive on the words that name them**; a screenshot punches in on its `focus` word; a
   build keeps one small alive thing while it waits.
2. **The background moves on the cut.** Its glows travel with each cut (expo.out, about 1.2 s) and hold between cuts.
3. **A new picture at least every 8 s** (E4). A long process travels: `flow` with 5 or 6 steps runs down a window
   and the camera moves to each step as it is said. Never hold one diagram while a highlight walks down it.
4. **Eases:** arrivals decelerate (`power3.out` for pieces, `expo.out` for scenes and cuts); exits accelerate
   (`power3.in`, 0.2 s, over before the cut). **Never `back`, `elastic` or `bounce`**: an overshoot reads as cheap. A
   `gravity-drop` falls and rebounds as physics (power2 in, then smaller power2 out and in), not as an eased overshoot.
   Linear only for counts, draws, the hub's slow turn, the camera's drift and the particles' rise.
5. **One object changing shape** beats a fade: a bar that grows, a line that draws, a card that turns. A build shows
   where it is going as **empty slots** (outlines, their words hidden), never as faint text, then fills each on its word.
6. **Deterministic, on the timeline.** No `Math.random` or `Date.now`, no `repeat` or `yoyo`, no `infinite` CSS
   animation: every render of the page is the same frame for frame (the custom-scene lint refuses them).

## 3. Cuts

Every cut is **velocity-matched**: the old scene accelerates into the cut, the new one decelerates out of it, and a
short blur carries the speed (HyperFrames' cut catalogue). **The old scene is gone by the cut** (its exit runs over the
0.2 s before it); two scenes are never on screen together, and gate E5 looks at every cut every 2 frames to prove it
(SOP S9). The composer picks them:
- **zoom-through:** out 1 to 1.2 with a 10 px blur, `power3.in` 0.2 s; in 0.75 to 1 out of an 8 px blur, `expo.out` 0.5 s;
- **whip (push):** out 260 px up with a 12 px blur; in from 300 px below out of a 10 px blur;
- **wipe:** a new background opens as a circle; **burst:** a spray for the hook or a reveal; **cut:** a hard cut.

## 4. The hook, and bespoke moments

**The hook (0 to 3 s) is kinetic type from data** (`kinetic`): a big accent token, one or two words, a claim line, a
strike and a punch, each rising out of its mask; **whole on screen by 1.0 s** (E3 holds every hook item to 0.8 s; the
planner lands the pieces on the words said by then). A number written into the words ("5 STEPS") becomes the big
token. Where the words themselves are the picture, `giant-captions` puts them 120 to 200 px in the middle of the frame
and the caption band steps aside. The writer hints it in script.json
(`{"type": "kinetic", "big": "3", "words": ["STEP", "TRICK"], "line": "AI INVENTS", "strike": "INVENTS", "punch": "LESS"}`)
and the planner lands every piece on its word: no code, no tokens beyond the script. **Custom scenes are opt-in**: only
when the creator asks for a moment the library cannot make. Brief one the motion-graphics-skills way:
1. **The bar:** what would make a designer stop scrolling?
2. **The one rule:** what is the hero, and what is its one satisfying change?
3. **Look:** sizes (hero 120 px+), the accent, what sits in each of the three depth layers.
4. **Motion:** which word triggers each move; the ease; the hold.
5. **Never:** the banned list above.

## 5. Before you call it done

**Gate E5 first** (`layout-check.py`): every scene in Chromium at the moment it is fully built, failing on text over
text, text covered by or crossing a shape, text out of its card, anything outside the safe area, text under 28 px,
clipped text, text under 3:1, and two scenes on screen at a cut. It costs nothing and catches what an eye skimming
stills misses. Then look at the settled stills (`stills.py`: every scene once all of it has arrived, the hook at 0.3,
0.7 and 1.0 s) as a design director would, full size and at 200 px wide: is the hero big and clear, does anything sit
small in empty space, is any text the narration repeated? Fix, re-run, then render; after the render, E6.
