# Explainer: Catppuccin Latte, a layout gate, prompt-only reels

**Goal (the creator's words):** a framework that spends very few tokens and uses the device's hardware to make very
clean, professional, highly animated Instagram reels from a prompt; diagrams never overflow or collide; the colours
are Catppuccin Latte, designed with the apple-design and motion-design skills.

## Decisions
- **Palette:** Catppuccin Latte (catppuccin/palette `palette.json`), light only. Backgrounds `mantle` #e6e9ef
  (default) and `base` #eff1f5; cards are the lighter of the two with a hairline. Semantic roles, each with its
  measured WCAG ratio on both backgrounds (HIG `accessibility.md`: 4.5:1 up to 17 pt, 3:1 large or bold):
  ink `text` (7.1 / 6.6), dim `subtext0` (4.4 / 4.1), muted `overlay2` (3.5 / 3.3), accent `blue` (4.3 / 4.0, bold
  and large only), on-accent `base` on blue (4.3). Signals `green`, `red`, `peach` are shapes beside a label, never
  the only carrier of meaning (HIG `color.md` › Inclusive color). One colour means one thing: blue is "what the voice
  is talking about now".
- **Motion personality (motion-design):** Corporate/Premium: entrances decelerate (power3.out 0.42 s, expo.out for
  cuts), exits accelerate and are shorter, staggers under 0.5 s, no overshoot, ambient glows move only on cuts.
- **Gate E5 `layout-check.py`, on the device:** HyperFrames `check` (text overlap, clipping, WCAG contrast) at each
  scene's fully built moment, plus our probe in the same Chromium: text covered by or crossing another shape, text
  spilling out of its card, anything outside the safe area, text under 28 px. Zero tokens; a failure names the scene
  and the element.
- **Prompt-only:** the hook is a library `kinetic` scene (the kinetic type of the bespoke demo hook, from data), so
  no reel needs Claude-written code; custom scenes become opt-in.

## Tasks
1. Theme: tokens.json, `Ctx.c` roles, every scene and the composer on roles; planner backgrounds; tests (every
   colour on a page is Latte, every role pair meets its ratio).
2. layout-check.py + layout-probe.mjs; tests on a clean page and on a page with an overlap, a spill and an
   out-of-area label.
3. Audit: compose every make-cases case and run the gate; fix every scene it flags (hub first); re-measure heights.
4. `kinetic` scene; planner uses it for the hook; MOTION.md/playbook: custom scenes opt-in.
5. Docs, full suites, demo render with the gate passing, send.
