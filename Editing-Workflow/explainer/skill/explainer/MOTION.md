# MOTION.md: how an explainer reel moves

Read this before you plan a storyboard (Director) or write a custom scene (Animator). The scripts enforce what can be
checked; the rest is your eye. The bar is the one in motion-graphics-skills: **stunning, or it is not done.**

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
3. **One accent at a time.** Cyan on dark, magenta on light; amber for a second series only. No gradient text, no
   glow on type, no purple-to-blue wash as a background.
4. **Real things.** A real logo (simple-icons), a real page (snap-page.py), a real number with a source. No stock
   icons standing in for a product the voice names.
5. **No two beats look the same.** The composer WARNs when two scenes in a row share a layout: change the picture,
   or merge the two into one build that keeps growing (one object changing beats a new widget every line).

## 2. Motion with a reason

1. **Nothing moves unless the voice gives it a reason.** "I'd rather have no motion than bad motion" (HyperFrames).
   No slow push-in on every scene, no glows drifting the whole time, no endless loops. A piece arrives on the word
   that names it; a screenshot holds still, then punches in on the line its `focus` names, on that word.
2. **The background moves on the cut.** Its glows travel with each cut (expo.out, about 1.2 s) and hold between cuts.
3. **Eases:** arrivals decelerate (`power3.out` for pieces, `expo.out` for scenes and cuts); exits accelerate
   (`power3.in`, 0.2 to 0.28 s). **Never `back`, `elastic` or `bounce`**: an overshoot reads as cheap. No linear
   movement (linear is for counts and draws).
4. **One object changing shape** beats a fade: a bar that grows, a line that draws, a card that turns. Show a dim ghost
   of where a build is going (the library's build-up scenes do), stagger by a beat, keep the hold to one alive thing.
5. **Deterministic.** No `Math.random`, no `repeat` or `yoyo`: every render of the page is the same frame for frame
   (the custom-scene lint refuses them).

## 3. Cuts

Every cut is **velocity-matched**: the old scene accelerates into the cut, the new one decelerates out of it, and a
short blur carries the speed (HyperFrames' cut catalogue). The composer picks them:
- **zoom-through:** out 1 to 1.2 with a 10 px blur, `power3.in` 0.2 s; in 0.75 to 1 out of an 8 px blur, `expo.out` 0.5 s;
- **whip (push):** out 260 px up with a 12 px blur; in from 300 px below out of a 10 px blur;
- **wipe:** a new background opens as a circle; **burst:** a spray for the hook or a reveal; **cut:** a hard cut.

## 4. Bespoke where it counts

The library carries the middle of a reel. **The hook (0 to 3 s) and the payoff are written for this reel** as custom
scenes (PLAYBOOK §E6.5): kinetic type, a chart that morphs, a real page that zooms to its line. Brief yourself the
motion-graphics-skills way before you write one:
1. **The bar:** what would make a designer stop scrolling?
2. **The one rule:** what is the hero, and what is its one satisfying change?
3. **Look:** sizes (hero 120 px+), the accent, what sits in each of the three depth layers.
4. **Motion:** which word triggers each move; the ease; the hold.
5. **Never:** the banned list above.

## 5. Before you call it done

Look at a still every second (`npx hyperframes snapshot public --at ...`) as a design director would, and again at
200 px wide (a thumbnail in a feed). Ask of each: is the hero big and clear? Does anything sit small in empty space?
Is any text the narration repeated? Would this frame make someone stop? Fix, re-snapshot, then render.
