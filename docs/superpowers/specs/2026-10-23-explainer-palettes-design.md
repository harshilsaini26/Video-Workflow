# Explainer colour palettes: design

Date: 2026-10-23. Scope agreed with the creator in chat (four answers below).

## Intent

Five named colour palettes for the explainer, picked per reel, each with its own mood, rules and "best for" list:

| Palette | Colours | Ground | Text | Rule |
|---|---|---|---|---|
| `terracotta` (Terracotta Sunset) | #E07A5F #F2CC8F #81B29A #3D405B #F4F1DE | #F4F1DE | #3D405B (8.9:1) | #E07A5F for accents and buttons |
| `monochrome` (Monochrome Ink) | #000000 #2B2B2B #6E6E6E #C4C4C4 #FFFFFF | #FFFFFF | #000000 (21:1) | restraint: no colour |
| `electric-pop` (Electric Pop) | #FF006E #FB5607 #FFBE0B #8338EC #3A86FF | #FFFFFF | near-black | two colours per reel; never a bright colour on another |
| `nordic-frost` (Nordic Frost) | #CAF0F8 #90E0EF #00B4D8 #0077B6 #03045E | #CAF0F8 | #03045E (14.7:1) | light for grounds, dark for type, mid tones for accents |
| `bold-citrus` (Bold Citrus) | #F94144 #F3722C #F8961E #F9C74F #90BE6D | one per scene, in order | #2A1D0E | a gradient across the reel; text in a deep neutral |

## Decisions (the creator's answers)

1. **A palette is colour only.** `"palette": "<name>"` in the storyboard (or script.json, which the planner carries over),
   beside `"look"` (latte or paper: fonts, texture, boil). Any palette works with either look; no palette keeps the look's
   own colours.
2. **Terracotta keeps #E07A5F exactly for shapes** (highlight boxes, series fills, buttons) with #3D405B text on them;
   words that are themselves accent-coloured use the same hue made deep enough for 3:1 on the ground.
3. **Electric Pop sits on a white ground**, with near-black text; #FF006E and #8338EC are its two colours (the reference's
   60% and 30%); the other three appear only as the signals (good, bad, warn), always beside a label.
4. **Bold Citrus steps the ground per scene**: scene 1 on #F94144, scene 2 on #F3722C, and on through #90BE6D, then round
   again; text is always #2A1D0E.

## How

- `tokens.json` gains `palettes`: each palette's title, five colours, mood, use and best-for, and the few choices that
  are its own (ground, text, accent, second accent, the strong and dark grounds, signals, series, the citrus cycle).
- `explainer_lib.load_tokens(look, palette)` derives everything else from those: the 26 palette names the scenes use
  (neutrals mixed from the text colour toward the ground), the roles on all four grounds, series, highlight and the UI
  paper roles. Where a palette colour is too light to read as text on its ground, the derived text colour keeps its hue
  and is darkened (or lightened on a dark ground) until it reaches the contrast the theme tests require; shapes keep the
  exact hex.
- The composer reads `"palette"`; with a cycle (citrus) each scene's ground is the next colour in it.

## Checks

The existing theme tests (every role at its contrast on every ground, text over the glows, nothing on a page outside the
palette) and gate E5 on every scene case run for every palette; plus a test per decision above.
