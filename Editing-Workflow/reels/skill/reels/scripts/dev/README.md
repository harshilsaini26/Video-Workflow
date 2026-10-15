# Developer tools (not part of a reel)

The composer places every block by its predicted height, so the safe zone holds by construction. These tools keep the
predictions true to what Chromium draws with DM Sans. Rerun them after changing a format's CSS, the fonts, or the text
measuring. They need Node, puppeteer (`npm i puppeteer-core` here, or `PUPPETEER_DIR=<a folder that has it>`) and
Chromium (`/opt/pw-browsers/chromium`, or `CHROME=<path>`).

1. **Glyph widths** (shared with the explainer skill): `node measure-glyphs.mjs <fonts> > ../glyphs.json`, where
   `<fonts>` holds DMSans-500/700 and JetBrainsMono-500 (`Editing-Workflow/explainer/skill/explainer/assets/fonts`).
   `reels_lib.text_lines` wraps text with these widths, word by word.
2. **Block heights:**
   ```
   python3 make-cases.py /tmp/rcases
   node measure-blocks.mjs /tmp/rcases > /tmp/rmeasured.jsonl
   python3 make-cases.py /tmp/rcases --merge /tmp/rmeasured.jsonl
   ```
   This writes `../tests/fixtures/heights.json`. Then `python3 -m unittest tests.test_heights` from `scripts/`: each
   prediction must be 0 to 4 px over what Chromium lays out, never under.
