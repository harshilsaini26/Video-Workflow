"""The craft rules from motion-graphics-skills, HyperFrames and Remotion (MOTION.md): the picture fills the frame, nothing
moves without a reason, cuts carry their velocity, and no ease overshoots."""
import copy, json, math, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import BOARD, D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E

TOK = E.load_tokens()
AREA_H = E.SCENE["bottom"] - E.SCENE["top"]
LIST = {"type": "list-cards", "id": "lc", "bg": "mantle", "in": "word:4", "out": D,
        "items": [{"label": "Newer", "at": "word:6"}, {"label": "Private", "at": "word:9"}, {"label": "Wrong", "at": "word:12"}]}
LEAD_IN = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}


def boxes(html):
    """{id: (left, top, width, height, inner width, inner height, scale)} for every scene box on the page."""
    out = {}
    for m in re.finditer(r'<div class="box" id="(\w+)" style="left:(\d+)px;top:(\d+)px;width:(\d+)px;height:(\d+)px">'
                         r'<div class="cam" id="\1-cam"><div class="live" id="\1-live" style="width:(\d+)px;height:(\d+)px;transform:scale\(([\d.]+)\)">', html):
        out[m.group(1)] = tuple(int(x) for x in m.groups()[1:7]) + (float(m.group(8)),)
    return out


class Craft(unittest.TestCase):
    def build(self, board):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), board)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return read(os.path.join(out, "index.html")), out, r.stdout

    # ---- fill the frame ---------------------------------------------------------------------------------------------
    def test_a_small_scene_is_scaled_up_to_fill_the_area(self):
        html, _, _ = self.build(dict(BOARD, scenes=[LEAD_IN, LIST]))
        left, top, w, h, iw, ih, s = boxes(html)["lc"]
        self.assertGreaterEqual(s, 1.4)                                   # 34 px labels become 48 px or more
        self.assertEqual(w, math.floor(iw * s))
        self.assertEqual(h, math.ceil(ih * s))
        col = 780 if top + h > E.L.RIGHT_COL_TOP else 950
        self.assertGreaterEqual(max(w / col, h / AREA_H), 0.85)          # it reaches across the area one way or the other
        self.assertTrue(E.inside_scene(left, top, w, h))
        self.assertGreaterEqual(top, E.SCENE["top"])
        self.assertLessEqual(top + h, E.SCENE["bottom"])

    def test_every_template_scene_fills_the_area_and_stays_inside_it(self):
        html, out, _ = self.build(BOARD)
        bx = boxes(html)
        self.assertEqual(set(bx), {"hook", "n1", "cu"})
        for sid, (left, top, w, h, iw, ih, s) in bx.items():
            self.assertTrue(E.inside_scene(left, top, w, h), sid)
            self.assertGreaterEqual(top, E.SCENE["top"], sid)
            self.assertLessEqual(top + h, E.SCENE["bottom"], sid)
        with open(os.path.join(out, "moments.json")) as f:
            sc = {x["id"]: x for x in json.load(f)["scenes"]}
        for sid, b in bx.items():
            self.assertEqual(sc[sid]["box"], list(b[:4]), sid)
            self.assertEqual(sc[sid]["scale"], b[6], sid)

    def test_a_title_grows_to_a_hero_size_and_no_further(self):
        html, _, _ = self.build(BOARD)          # 104 px by default; a hero word is 120 px or more, and 150 px is plenty
        s = boxes(html)["hook"][6]
        self.assertGreater(s, 1.0)
        self.assertLessEqual(104 * s, 150.5)
        board = copy.deepcopy(BOARD)
        board["scenes"][0]["size"] = 132
        left, top, w, h, iw, ih, s = boxes(self.build(board)[0])["hook"]
        self.assertLessEqual(132 * s, 150.5)
        self.assertEqual(w, math.floor(iw * s))          # the box is sized with the scale the page draws with
        self.assertEqual(h, math.ceil(ih * s))
        self.assertTrue(E.inside_scene(left, top, w, h))

    def test_a_wide_word_still_gets_the_wide_column(self):
        # a one-line title whose word needs 781 to 950 px fits the full width above y 960, as before the taller area
        board = copy.deepcopy(BOARD)
        board["scenes"][0]["text"] = "Internationalisa"
        left, top, w, h, iw, ih, s = boxes(self.build(board)[0])["hook"]
        self.assertGreater(w, 780)
        self.assertLessEqual(top + h, E.L.RIGHT_COL_TOP)
        self.assertTrue(E.inside_scene(left, top, w, h))

    def test_the_scene_area_ends_at_the_one_bottom_limit(self):
        # SOP S7: text and cards end by y 1235, the same line QA and the Reels guides use
        self.assertEqual(E.SCENE["bottom"], 1235)
        self.assertTrue(E.inside_scene(150, 900, 780, 335))
        self.assertFalse(E.inside_scene(65, 900, 950, 335))        # below y 960 it keeps clear of the action column
        self.assertFalse(E.inside_scene(150, 900, 780, 336))
        tm = {"type": "timeline", "id": "tm", "bg": "mantle", "in": "word:4", "out": D,
              "steps": [{"label": "Step " + "ABCDE"[i], "at": "word:%d" % (5 + 2 * i)} for i in range(5)]}
        left, top, w, h, iw, ih, s = boxes(self.build(dict(BOARD, scenes=[LEAD_IN, tm]))[0])["tm"]
        self.assertGreaterEqual(s, 1.0)                            # five steps still fill the narrow column
        self.assertLessEqual(top + h, 1235)

    def test_a_scene_too_wide_even_unscaled_still_fails(self):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        bad = copy.deepcopy(LIST)
        bad["items"][0]["label"] = "Supercalifragilisticexpialidocious-ness"
        sp = write(os.path.join(d, "storyboard.json"), dict(BOARD, scenes=[LEAD_IN, bad]))
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("wider than the", r.stdout)

    def test_the_same_layout_twice_in_a_row_warns(self):
        # no two beats with the same layout (motion-graphics-skills' launch learnings; HyperFrames: never the same framing)
        second = dict(LIST, id="lc2", **{"in": "word:14"})
        second["items"] = [dict(it, at="word:%d" % (16 + 2 * i)) for i, it in enumerate(LIST["items"])]
        first = dict(LIST, out="word:14")
        _, _, out = self.build(dict(BOARD, scenes=[LEAD_IN, first, second]))
        self.assertIn("WARN lc2: the same layout (list-cards) as the scene before", out)
        _, _, out = self.build(dict(BOARD, scenes=[LEAD_IN, LIST]))
        self.assertNotIn("the same layout", out)


if __name__ == "__main__":
    unittest.main()
