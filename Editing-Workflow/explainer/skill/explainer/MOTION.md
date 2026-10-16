# MOTION.md: how an explainer reel moves

Read this before you plan a storyboard (Director) or build a reel (Animator). The scripts enforce what can be checked
(the composer, gate E5's layout-check in Chromium, the contrast pass), on the creator's machine and at no token cost; the
rest is your eye. The bar is the one in motion-graphics-skills: **stunning, or it is not done.** The look follows Apple's
Human Interface Guidelines (clarity, deference, one colour meaning one thing) in Catppuccin Latte.

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
   to 1420 (780 px wide below y 960, clear of Instagram's buttons). A title grows to 150 px; numbers to 1.3x.
2. **Type is the picture.** A hero word is 120 px or more; a label is 34 px or more after the scale; at most about 5
   words of on-screen text at once, and never the narration's sentence (the captions already say it).
3. **One accent, one meaning.** Catppuccin Latte, light only (tokens.json): ink `text`, secondary `subtext0`, unsaid
   caption words `overlay2`, rules `surface1`, cards `base` with a hairline, and **blue is the accent: "what the voice
   is talking about now"**. Green, red and peach are signals, always beside a label (never colour alone). Every role
   pair meets WCAG on both backgrounds (test_theme). No gradient text, no glow on type or shapes.
4. **Real things.** A real logo (simple-icons), a real page (snap-page.py), a real number with a source. No stock
   icons standing in for a product the voice names.
5. **No two beats look the same.** The composer WARNs when two scenes in a row share a layout: change the picture,
   or merge the two into one build that keeps growing (one object changing beats a new widget every line).

## 2. Motion with a reason

1. **Nothing moves unless the voice gives it a reason.** "I'd rather have no motion than bad motion" (HyperFrames).
   No slow push-in on every scene, no glows drifting the whole time. A piece arrives on the word that names it; a
   screenshot holds still, then punches in on the line its `focus` names, on that word. The one exception is the
   hold: a build may keep **one** small alive thing while it waits for its next word (the library's float, pulse or
   the hub's slow turn), and that is all.
2. **The background moves on the cut.** Its glows travel with each cut (expo.out, about 1.2 s) and hold between cuts.
3. **Eases:** arrivals decelerate (`power3.out` for pieces, `expo.out` for scenes and cuts); exits accelerate
   (`power3.in`, 0.2 to 0.28 s). **Never `back`, `elastic` or `bounce`**: an overshoot reads as cheap. No linear
   movement (linear is for counts, draws and the hub's slow turn).
4. **One object changing shape** beats a fade: a bar that grows, a line that draws, a card that turns. Show a dim ghost
   of where a build is going (the library's build-up scenes do), stagger by a beat, keep the hold to one alive thing.
5. **Deterministic, on the timeline.** No `Math.random` or `Date.now`, no `repeat` or `yoyo`, no `infinite` CSS
   animation: every render of the page is the same frame for frame (the custom-scene lint refuses them).

## 3. Cuts

Every cut is **velocity-matched**: the old scene accelerates into the cut, the new one decelerates out of it, and a
short blur carries the speed (HyperFrames' cut catalogue). The composer picks them:
- **zoom-through:** out 1 to 1.2 with a 10 px blur, `power3.in` 0.2 s; in 0.75 to 1 out of an 8 px blur, `expo.out` 0.5 s;
- **whip (push):** out 260 px up with a 12 px blur; in from 300 px below out of a 10 px blur;
- **wipe:** a new background opens as a circle; **burst:** a spray for the hook or a reveal; **cut:** a hard cut.

## 4. The hook, and bespoke moments

**The hook (0 to 3 s) is kinetic type from data** (`kinetic`): a big accent token, one or two words, a claim line, a
strike and a punch, each rising out of its mask on its word. The writer hints it in script.json
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
clipped text and WCAG contrast. It costs nothing and catches what an eye skimming stills misses. Then look at the stills
the composer names (a contact sheet is one image) as a design director would, full size and at 200 px wide: is the hero
big and clear, does anything sit small in empty space, is any text the narration repeated? Fix, re-run, then render.
