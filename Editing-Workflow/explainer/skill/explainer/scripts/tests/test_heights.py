"""Scene heights against Chromium: every module's height() is at most 4 px over what the browser lays out, never under.

The fixture comes from dev/make-cases.py and dev/measure-scenes.mjs (see dev/README.md); rerun them after changing a
scene's CSS constants or the fonts.
"""
import json, os, unittest
from scenes import REGISTRY

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "heights.json")


def rows():
    with open(FIX) as f:
        return json.load(f)


class Heights(unittest.TestCase):
    def test_fixture_covers_every_scene_type(self):
        seen = {}
        for r in rows():
            seen.setdefault(r["type"], set()).add((r["case"], r["width"]))
        for t in sorted(set(REGISTRY) - {"custom"}):
            self.assertIn(t, seen, "no measured cases for %s" % t)
            self.assertGreaterEqual(len({c for c, _ in seen[t]}), 3, t)
            if not getattr(REGISTRY[t], "BAKED", False):   # a baked scene is measured at the width it was composed at
                self.assertEqual({w for _, w in seen[t]}, {950, 780}, t)

    def test_module_heights_match_chromium(self):
        bad = []
        for r in rows():
            h = REGISTRY[r["type"]].height(r["scene"], r["width"])
            if not 0 <= h - r["height"] <= 4:
                bad.append("%s at %d px: predicted %d, measured %d" % (r["case"], r["width"], h, r["height"]))
        self.assertEqual(bad, [])
