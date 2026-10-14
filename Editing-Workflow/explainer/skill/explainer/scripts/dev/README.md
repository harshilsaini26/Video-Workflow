# Developer tools (not part of a video run)

The scene modules know their own heights before a browser sees them, so the composer can place every scene inside the
scene area by construction. These tools keep that true. Rerun them after changing a scene's CSS constants, adding a
scene type, or changing the fonts in `../assets/fonts/`.

They need Node, puppeteer (`npm i puppeteer-core` here, or `PUPPETEER_DIR=<a folder that has it>`) and Chromium
(`/opt/pw-browsers/chromium`, or `CHROME=<path>`).

1. **Glyph widths:** `node measure-glyphs.mjs ../../assets/fonts > ../glyphs.json`. These are the advance widths of DM Sans
   500/700 and JetBrains Mono 500. `explainer_lib.text_lines` wraps text with them, word by word.
2. **Scene heights:**
   ```
   python3 make-cases.py /tmp/cases --vendor <vendor folder with katex/ and lucide/>
   node measure-scenes.mjs /tmp/cases > /tmp/measured.jsonl
   python3 make-cases.py /tmp/cases --merge /tmp/measured.jsonl
   ```
   This writes `../tests/fixtures/heights.json`. Then run `python3 -m unittest tests.test_heights` from `scripts/`: each
   module's `height()` must be 0 to 4 px over what Chromium lays out, never under.
