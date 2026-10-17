"""Block heights against Chromium: the composer places every block by its predicted height (layout.json), so a
prediction under the real height could push a block (or a caption) past the safe zone, and one far over refuses layouts that fit.
Each prediction must be 0 to 4 px over what Chromium lays out with DM Sans. The fixture comes from dev/make-cases.py and
dev/measure-blocks.mjs; rerun them after changing a format's CSS, the fonts or the text measuring."""
import json, os, unittest
from .helpers import run, scratch, write
import reels_lib as L

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "heights.json")


class Heights(unittest.TestCase):
    def predicted(self, beat):
        if "caption" in beat:   # a caption chunk: the composer checks it against the safe zone with reels_lib.caption_height
            return L.caption_height(beat["caption"], beat["size"]), ""
        d = scratch(self)
        b = dict(beat, id="b", **{"in": 0.0, "out": 4.0, "anchor": "-"})
        sp = write(os.path.join(d, "storyboard.json"), {"id": "h", "duration": 5.0, "fps": 60, "captions": False, "beats": [b]})
        r = run("reels-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        if r.returncode:
            return None, r.stderr.strip()[-200:]
        with open(os.path.join(d, "public", "layout.json"), encoding="utf-8") as f:
            return json.load(f)[0]["height"], ""

    def test_predictions_match_chromium(self):
        with open(FIX, encoding="utf-8") as f:
            rows = json.load(f)
        self.assertGreaterEqual(len(rows), 40)
        bad = []
        for r in rows:
            h, err = self.predicted(r["beat"])
            if h is None:
                bad.append("%s: refused (%s), but Chromium lays it out %d px tall" % (r["case"], err, r["height"]))
            elif not 0 <= h - r["height"] <= 4:
                bad.append("%s: predicted %d, measured %d" % (r["case"], h, r["height"]))
        self.assertEqual(bad, [])
