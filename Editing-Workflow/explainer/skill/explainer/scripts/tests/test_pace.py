"""pace-check.py (gate E4, pacing): something on screen changes at least every few seconds. The kit's gap-scan cannot
see this here: the scenes cover the whole voice by construction, so it never finds an empty stretch."""
import copy, os, unittest
from .helpers import load, run, scratch, write
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


def moments(items, D=10.0):
    """A hand-written moments.json: two scenes, a change every second, and the given items."""
    return {"duration": D, "spans": [[t, t + 1] for t in range(int(D))], "items": items,
            "scenes": [{"id": "a", "type": "title", "in": 0, "out": 5}, {"id": "cu", "type": "count-up", "in": 5, "out": D}]}


def it(scene, t, group=None, number=False, text="x"):
    return {"scene": scene, "t": t, "text": text, "group": group or "%s@%s" % (scene, t), "number": number}


class ReadFloor(unittest.TestCase):
    def check(self, items, D=10.0):
        d = scratch(self)
        mp = write(os.path.join(d, "moments.json"), moments(items, D))
        return run("pace-check.py", "--index", os.path.join(d, "index.html"), "--moments", mp)

    def test_items_are_in_moments(self):
        page = Pace("test_changing_reel_passes").page(BOARD)
        m = load(os.path.join(os.path.dirname(page), "moments.json"))
        self.assertTrue(m["items"])
        self.assertEqual({"scene", "t", "text", "group", "number"}, set(m["items"][0]))
        cu = [i for i in m["items"] if i["scene"] == "cu"]
        self.assertTrue(cu and all(i["number"] for i in cu))
        self.assertFalse(any(i["number"] for i in m["items"] if i["scene"] == "hook"))
        self.assertIn("Three certificates", " ".join(i["text"] for i in m["items"]))

    def test_a_number_needs_a_second(self):
        r = self.check([it("a", 1.0), it("cu", 9.2 - 1.5, number=True), it("a", 4.2, number=True)], D=9.2)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r"E4 FAIL: .*a.*0\.8 s")

    def test_the_last_read_needs_time(self):
        r = self.check([it("a", 1.0), it("cu", 8.8)])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("1.2 s before the end", r.stdout)

    def test_two_reads_at_once_warn(self):
        r = self.check([it("a", 1.0), it("a", 1.4), it("cu", 6.0)])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN two reads at once", r.stdout)

    def test_a_stagger_is_one_read(self):
        r = self.check([it("a", 1.0 + 0.1 * k, group="a-list") for k in range(6)] + [it("cu", 6.0)])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("two reads", r.stdout)

    def test_the_existing_cases_still_pass(self):
        r = run("pace-check.py", "--index", Pace("test_changing_reel_passes").page(BOARD))
        self.assertNotIn("before the end", r.stdout)
        self.assertNotIn("before its scene", r.stdout)
