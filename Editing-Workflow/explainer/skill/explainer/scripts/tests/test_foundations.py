"""The rules the RAG reel's retrospective asked for, held by the composer and the gates (SOP S7, S8, S9; the 90 s
ceiling; a picture never held too long) and the scene library found without a list to edit."""
import copy, json, os, re, unittest
from .helpers import load, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
import explainer_lib as E
import scenes

LIST = {"type": "list-cards", "id": "lc", "bg": "mantle", "in": "word:0", "out": "word:12",
        "items": [{"label": "Search", "at": "word:0"}, {"label": "Answer", "at": "word:1"}]}


def compose(test, board, voice=VOICE, words=None):
    d = scratch(test)
    write(os.path.join(d, "transcript.json"), {"words": words or words30()})
    silent_wav(os.path.join(d, "voice.wav"), voice)
    sp = write(os.path.join(d, "storyboard.json"), board)
    r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
    return r, d


class Area(unittest.TestCase):
    def test_text_and_cards_end_by_1235_and_pictures_by_1650(self):
        # S7: one bottom limit, the same in the composer, the probe and QA
        self.assertEqual(E.SCENE["bottom"], 1235)
        self.assertEqual(E.PICTURE_BOTTOM, 1650)
        self.assertFalse(E.inside_scene(150, 900, 780, 336))
        self.assertTrue(E.inside_scene(150, 900, 780, 335))

    def test_every_scene_box_ends_by_1235(self):
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        for sc in load(os.path.join(d, "public", "moments.json"))["scenes"]:
            left, top, w, h = sc["box"]
            self.assertLessEqual(top + h, 1235, sc["id"])


class Handover(unittest.TestCase):
    def test_the_old_scene_is_gone_by_the_cut(self):
        # S9: the exit ends on the cut, the next scene enters on it: never two scenes on screen at once
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = open(os.path.join(d, "public", "index.html"), encoding="utf-8").read()
        m = load(os.path.join(d, "public", "moments.json"))
        hook, n1 = m["scenes"][0], m["scenes"][1]
        exits = re.findall(r"tl\.to\('#hook', \{ opacity: 0[^}]*duration: ([\d.]+)[^}]*\}, ([\d.]+)\);", page)
        self.assertEqual(len(exits), 1, page[-3000:])
        dur, at = map(float, exits[0])
        self.assertAlmostEqual(at + dur, n1["in"], places=2)
        host = re.search(r'id="host-hook" data-start="([\d.]+)" data-duration="([\d.]+)"', page)
        self.assertAlmostEqual(float(host.group(1)) + float(host.group(2)), hook["out"], places=2)


class Hook(unittest.TestCase):
    def test_a_hook_item_after_0_8_s_fails(self):
        # S8: the hook is on screen by 1.0 s; its items land by 0.8 s
        board = copy.deepcopy(BOARD)
        late = copy.deepcopy(LIST)
        late["items"][1]["at"] = "word:3"            # word 3 starts at 1.7 s, so the item lands at 1.5 s
        board["scenes"] = [late, dict(BOARD["scenes"][2], **{"in": "word:12"})]
        r, _ = compose(self, board)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E3 FAIL: lc: the hook", r.stdout)
        self.assertIn("0.8 s", r.stdout)

    def test_a_hook_on_its_first_words_passes(self):
        board = copy.deepcopy(BOARD)
        board["scenes"] = [copy.deepcopy(LIST), dict(BOARD["scenes"][2], **{"in": "word:12"})]
        r, _ = compose(self, board)
        self.assertEqual(r.returncode, 0, r.stdout)


class Seen(unittest.TestCase):
    def test_an_item_on_its_scenes_cut_fails(self):
        # the exit runs over the last 0.2 s before the cut: an item landing there (or on the cut) is never seen, so E3
        # fails it, naming the item and the latest time it can land
        board = copy.deepcopy(BOARD)
        board["scenes"][1] = dict(LIST, id="lc", **{"in": "word:8", "out": "word:18"})
        board["scenes"][1]["items"] = [{"label": "Search", "at": "word:9"}, {"label": "Answer", "at": "word:18"}]
        r, _ = compose(self, board)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E3 FAIL: lc:", r.stdout)
        self.assertIn("too close to the scene's end to be seen", r.stdout)

    def test_an_item_with_time_to_be_seen_passes(self):
        board = copy.deepcopy(BOARD)
        board["scenes"][1] = dict(LIST, id="lc", **{"in": "word:8", "out": "word:18"})
        board["scenes"][1]["items"] = [{"label": "Search", "at": "word:9"}, {"label": "Answer", "at": "word:16"}]
        r, _ = compose(self, board)
        self.assertEqual(r.returncode, 0, r.stdout)


class Ceiling(unittest.TestCase):
    def test_a_voice_over_90_s_fails(self):
        board = copy.deepcopy(BOARD)
        r, _ = compose(self, board, voice=90.4)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("over the 90 s ceiling", r.stdout)


class HoldTime(unittest.TestCase):
    def moments(self, scenes, spans):
        d = scratch(self)
        write(os.path.join(d, "public", "index.html"), "<html></html>")
        write(os.path.join(d, "public", "moments.json"), {"duration": scenes[-1]["out"], "scenes": scenes, "spans": spans})
        return run("pace-check.py", "--index", os.path.join(d, "public", "index.html"))

    def test_a_scene_held_over_8_s_fails_even_while_it_changes(self):
        sc = [{"id": "a", "type": "custom", "in": 0.0, "out": 9.0}, {"id": "b", "type": "title", "in": 9.0, "out": 11.0}]
        r = self.moments(sc, [[t * 1.0, t * 1.0 + 0.5] for t in range(11)])
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E4 FAIL: a is held 9.0 s", r.stdout)

    def test_a_scene_over_6_s_warns_and_one_that_travels_may_hold(self):
        sc = [{"id": "a", "type": "flow", "in": 0.0, "out": 6.5}, {"id": "b", "type": "title", "in": 6.5, "out": 8.0}]
        r = self.moments(sc, [[t * 1.0, t * 1.0 + 0.5] for t in range(8)])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN a is held 6.5 s", r.stdout)
        sc = [{"id": "a", "type": "flow", "in": 0.0, "out": 12.0, "travels": True}, {"id": "b", "type": "title", "in": 12.0, "out": 13.0}]
        r = self.moments(sc, [[t * 1.0, t * 1.0 + 0.5] for t in range(13)])
        self.assertEqual(r.returncode, 0, r.stdout)


class Decor(unittest.TestCase):
    def test_ui_furniture_numbers_need_no_source(self):
        # a timecode or a like count in a mock-up is furniture, not a claim: a scene names those keys in DECOR_KEYS
        from . import explainer_compose_shim as C
        self.assertFalse(C.shows_number({"type": "x", "time": "0:12", "likes": 1200}, decor={"time", "likes"}))
        self.assertTrue(C.shows_number({"type": "x", "time": "0:12", "text": "3 steps"}, decor={"time"}))


class Discovery(unittest.TestCase):
    def test_a_scene_module_is_found_without_a_list(self):
        d = scratch(self)
        write(os.path.join(d, "spark.py"), 'TYPE = "spark"\nCSS = ""\n')
        write(os.path.join(d, "_helper.py"), "X = 1\n")
        write(os.path.join(d, "notes.py"), "Y = 2\n")
        found = scenes.discover(d, "spark_pkg")
        self.assertEqual(sorted(found), ["spark"])
        self.assertIn("kinetic", scenes.REGISTRY)
        self.assertNotIn("custom_", scenes.REGISTRY)


if __name__ == "__main__":
    unittest.main()
