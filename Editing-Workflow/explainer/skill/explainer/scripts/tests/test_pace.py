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
        board = copy.deepcopy(BOARD)
        board["scenes"] = [dict(BOARD["scenes"][0], out="word:5"), dict(BOARD["scenes"][1], **{"in": "word:5", "out": "word:10"}),
                           {"type": "title", "id": "t2", "bg": "mantle", "in": "word:10", "out": "word:15", "text": "Then this"},
                           dict(BOARD["scenes"][2], **{"in": "word:15", "out": "word:21"}),
                           {"type": "title", "id": "t3", "bg": "base", "in": "word:21", "out": "word:26", "text": "And this"},
                           {"type": "title", "id": "t4", "bg": "base", "in": "word:26", "out": "end", "text": "The end"}]
        r = run("pace-check.py", "--index", self.page(board))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("E4 PASS", r.stdout)

    def test_one_static_scene_fails(self):
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "only", "bg": "mantle", "in": "word:0", "out": "end", "text": "One idea"}]
        r = run("pace-check.py", "--index", self.page(board))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nothing changes from", r.stdout)
        self.assertIn("only", r.stdout)

    def test_threshold_is_adjustable(self):
        r = run("pace-check.py", "--index", self.page(BOARD), "--max", "1")
        self.assertNotEqual(r.returncode, 0)

    def test_a_still_stretch_over_3_s_fails_by_default(self):
        # the reference reel changes its picture every 1.5 to 2 s; 3 s with nothing new is the most a reel may hold
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "a", "bg": "mantle", "in": "word:0", "out": "word:11", "text": "Hold"},
                           dict(BOARD["scenes"][2], **{"in": "word:11"})]     # the title holds 4.4 s
        r = run("pace-check.py", "--index", self.page(board))
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("at most 3.0 s", r.stdout)
