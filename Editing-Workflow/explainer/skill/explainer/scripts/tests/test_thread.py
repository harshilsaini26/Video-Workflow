"""The thread (the editorial pass): one line through the reel, as the reference's cable runs from scene to scene. It
draws on at its first key, then morphs on each key's word into the next named shape (drop, loop, wave, rule,
underline, off); a wave keeps scrolling while it holds. It sits behind the scenes and the captions."""
import copy, json, os, re, unittest
from .helpers import load, read
from .test_compose import BOARD, t_word, words30
from .test_foundations import compose
import explainer_lib as E

THREAD = {"color": "ink", "width": 8, "keys": [
    {"at": "word:0", "shape": "drop", "x": 540, "to": 700},
    {"at": "word:9", "shape": "loop", "x": 540, "y": 900, "rx": 300, "ry": 90},
    {"at": "word:19", "shape": "wave", "y": 1400, "amp": 60},
    {"at": "word:26", "shape": "off"}]}


def with_thread(spec=THREAD):
    b = copy.deepcopy(BOARD)
    b["thread"] = copy.deepcopy(spec)
    return b


class Shapes(unittest.TestCase):
    def test_every_shape_has_n_points_inside_the_frame(self):
        import thread
        self.assertEqual(thread.SHAPES, ("drop", "loop", "wave", "rule", "underline", "off"))
        prev = thread.points("drop", {"x": 300, "to": 800})
        for shape in thread.SHAPES:
            pts = thread.points(shape, {}, prev)
            self.assertEqual(len(pts), thread.N, shape)
            for x, y in pts:
                self.assertTrue(-1100 <= x <= 1180 and -60 <= y <= 1980, (shape, x, y))
        self.assertTrue(all(abs(x - 300) < 1e-6 for x, _ in thread.points("off", {}, prev)))   # it leaves where it was
        wave = thread.points("wave", {})
        off = thread.points("off", {}, wave)
        self.assertEqual([x for x, _ in off], [x for x, _ in wave])      # a wave lifts straight up, never sweeps sideways
        self.assertTrue(all(y < 0 for _, y in off))

    def test_keys_must_rise_in_time_and_name_known_shapes(self):
        import thread
        words = words30()
        self.assertEqual(thread.validate(THREAD, words), [])
        bad = copy.deepcopy(THREAD)
        bad["keys"][1]["shape"] = "spiral"
        self.assertTrue(any("spiral" in e for e in thread.validate(bad, words)))
        bad = copy.deepcopy(THREAD)
        bad["keys"][2]["at"] = "word:5"
        self.assertTrue(any("in time order" in e for e in thread.validate(bad, words)))
        self.assertTrue(thread.validate({"keys": []}, words))
        self.assertTrue(thread.validate(dict(THREAD, color="neon"), words))

    def test_no_key_runs_through_the_captions(self):
        # the captions are the one place the line must never cross (it would strike through the words being said):
        # a stem down the middle into a loop below them, or a wave at their height, is refused with the key named
        import thread
        words = words30()
        for key in ({"shape": "loop", "x": 540, "y": 1450, "rx": 300, "ry": 80}, {"shape": "wave", "y": 1180},
                    {"shape": "drop", "x": 540, "to": 1500}):
            bad = copy.deepcopy(THREAD)
            bad["keys"][2].update(key)
            errs = thread.validate(bad, words)
            self.assertTrue(any(e.startswith("key 2") and "captions" in e for e in errs), (key, errs))
        edge = copy.deepcopy(THREAD)
        edge["keys"][0].update({"x": 1040, "to": 1600})               # down the outer edge, clear of the caption column
        self.assertEqual(thread.validate(edge, words), [])


class OnThePage(unittest.TestCase):
    def test_the_thread_draws_on_and_morphs_on_its_words(self):
        r, d = compose(self, with_thread())
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        self.assertRegex(page, r'<svg class="thread" data-thread="1"[^>]*><g id="th-g"><path id="th-p" pathLength="1"')
        times = [float(x) for x in json.loads(re.search(r"const TH_T = (\[[^\]]*\]);", page).group(1))]
        self.assertEqual(times, [round(max(0.0, t_word(i) - E.LEAD), 3) for i in (0, 9, 19, 26)])
        self.assertIn("thAt(tl.time())", page)                         # the shape follows the timeline's own time: seek-safe
        self.assertRegex(page, r"tl\.fromTo\(TH_P, \{ v: 0 \}, \{ v: 1, duration: [\d.]+, ease: 'none'")

    def test_the_thread_passes_behind_the_scenes_and_the_captions(self):
        r, d = compose(self, with_thread())
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        z = int(re.search(r"\.thread \{[^}]*z-index:(\d+)", page).group(1))
        self.assertLess(z, 10)                                          # .card-host is 10, the captions 30
        self.assertLess(page.index('class="thread"'), page.index('class="card-host'))

    def test_morphs_are_moments_for_pace_check(self):
        r, d = compose(self, with_thread())
        self.assertEqual(r.returncode, 0, r.stdout)
        spans = load(os.path.join(d, "public", "moments.json"))["spans"]
        for i in (9, 19):
            t = round(t_word(i) - E.LEAD, 3)
            self.assertIn([t, round(t + 0.6, 3)], spans)

    def test_a_bad_thread_fails_e3(self):
        bad = copy.deepcopy(THREAD)
        bad["keys"][0]["shape"] = "zigzag"
        r, _ = compose(self, with_thread(bad))
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E3 FAIL: thread:", r.stdout)

    def test_e5_ignores_the_thread(self):
        # the line may pass behind a scene's words (the reference runs its cable through WIRED): it is decoration
        from .helpers import run
        r, d = compose(self, with_thread())
        self.assertEqual(r.returncode, 0, r.stdout)
        if not (os.environ.get("CHROME") or os.path.exists("/opt/pw-browsers/chromium")):
            self.skipTest("needs Chrome for the probe")
        r = run("layout-check.py", "--index", os.path.join(d, "public", "index.html"), "--no-hf")
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
