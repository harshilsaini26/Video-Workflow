# Explainer craft pass: what motion-graphics-skills, HyperFrames and Remotion teach

**Goal:** make the explainer's reels look designed, not assembled: the picture fills the frame, every motion has a
reason, cuts carry velocity, and the hook is bespoke.

**Sources studied (read as data, none of their code runs here):**
- charlie947/motion-graphics-skills: the 8-part prompt ("the hero fills 60 to 70% of the frame and shows one satisfying
  change"; hero word 120 px or more, labels 34 px or more; spring with a small settle; no bounce, no glow, no typewriter;
  "stunning or it's not done"; a still every second judged as a design director), the effect recipes (one object
  changing shape, a ghost of the start state, a stagger of a beat), the vox-explainer review rules.
- heygen-com/hyperframes, skills/faceless-explainer: motion-language.md (power3 by default; no back, bounce or elastic;
  no lazy breathing or slow pans, "no motion rather than bad motion"; velocity-matched cuts; no repeat, yoyo or
  Math.random), cut-catalog.md (zoom-through: out 1 to 1.2 with a 10 px blur, power3.in, 0.2 s; in 0.75 to 1, expo.out,
  0.5 s), typography.md and the portrait layout rules (hero 40 to 60% of the frame, never the same framing twice in a row).
- remotion-dev/remotion, template-prompt-to-motion-graphics skills: "never constrain content to a small centred box",
  springs over linear motion, expo-out for arrivals, a push-cut with a short blur.

## Global constraints
- Free tools only; 1080x1920 at 60 fps; the Reels safe zone and caption band are unchanged.
- TDD for every behaviour change; the suite stays green.

## Tasks
1. **Fill the frame.** The composer scales every template scene up to fill the scene area (lay it out at width W/s,
   scale by s, s up to 1.8), largest s that keeps the height inside the area and every word inside its column. The box
   keeps its outer size; the inner `.live` wrapper carries the static scale. moments.json records each scene's box and
   scale. WARN when a scene fills under 60% of the area both ways.
2. **Motion with a reason.** Drop the slow push-in on every scene and the always-drifting glows (lazy breathing). The
   glows move only on a cut, travelling with it (expo.out, about 1.2 s), and hold still between cuts. No `back`,
   `elastic` or `bounce` ease anywhere in a built page (stack, timeline and logo-card used back.out).
3. **Velocity-matched cuts.** zoom becomes HyperFrames' zoom-through (exit 1 to 1.2, blur 10 px, power3.in 0.2 s; enter
   0.75 to 1, blur 8 to 0, expo.out 0.5 s); push becomes a whip (exit up with a blur, enter from below with a blur).
4. **Bespoke where it counts.** The custom-scene lint also refuses `back`/`elastic`/`bounce` eases, `repeat`, `yoyo`
   and `Math.random` (the doctrine applies to Claude-written scenes too). The composer WARNs when two scenes in a row
   share a layout.
5. **The doctrine, written down.** `MOTION.md` in the skill: the rules above with their sources, the hook and payoff as
   bespoke custom scenes, and the design-director check of stills. SKILL.md, PLAYBOOK and the animator and director
   agents point to it.
6. **Demo.** Rebuild the RAG demo with a bespoke hook, render at 1080x1920 60 fps, and send it with a contact sheet.
