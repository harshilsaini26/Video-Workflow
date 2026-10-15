"""pace-check.py (gate E4, pacing): something on screen changes at least every few seconds. The kit's gap-scan cannot
see this here: the scenes cover the whole voice by construction, so it never finds an empty stretch."""
import copy, os, unittest
from .helpers import run, scratch, write
from .test_compose import BOARD, D, VOICE, silent_wav, words30


class Pace(unittest.TestCase):
    def page(self, board):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), board)
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return os.path.join(d, "public", "index.html")

    def test_changing_reel_passes(self):
        r = run("pace-check.py", "--index", self.page(BOARD))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("E4 PASS", r.stdout)

    def test_one_static_scene_fails(self):
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "only", "bg": "black", "in": "word:0", "out": "end", "text": "One idea"}]
        r = run("pace-check.py", "--index", self.page(board))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nothing changes from", r.stdout)
        self.assertIn("only", r.stdout)

    def test_threshold_is_adjustable(self):
        r = run("pace-check.py", "--index", self.page(BOARD), "--max", "3")
        self.assertNotEqual(r.returncode, 0)
