"""The craft rules from motion-graphics-skills, HyperFrames and Remotion (MOTION.md): the picture fills the frame, nothing
moves without a reason, cuts carry their velocity, and no ease overshoots."""
import copy, json, math, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import BOARD, D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E

TOK = E.load_tokens()
AREA_H = E.SCENE["bottom"] - E.SCENE["top"]
LIST = {"type": "list-cards", "id": "lc", "bg": "black", "in": "word:4", "out": D,
        "items": [{"label": "Newer", "at": "word:6"}, {"label": "Private", "at": "word:9"}, {"label": "Wrong", "at": "word:12"}]}
LEAD_IN = {"type": "title", "id": "lead", "bg": "black", "in": "word:0", "out": "word:4", "text": "Lead in"}


def boxes(html):
    """{id: (left, top, width, height, inner width, inner height, scale)} for every scene box on the page."""
    out = {}
    for m in re.finditer(r'<div class="box" id="(\w+)" style="left:(\d+)px;top:(\d+)px;width:(\d+)px;height:(\d+)px">'
                         r'<div class="live" id="\1-live" style="width:(\d+)px;height:(\d+)px;transform:scale\(([\d.]+)\)">', html):
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
        self.assertTrue(E.L.inside_safe(left, top, w, h))
        self.assertGreaterEqual(top, E.SCENE["top"])
        self.assertLessEqual(top + h, E.SCENE["bottom"])

    def test_every_template_scene_fills_the_area_and_stays_inside_it(self):
        html, out, _ = self.build(BOARD)
        bx = boxes(html)
        self.assertEqual(set(bx), {"hook", "n1", "cu"})
        for sid, (left, top, w, h, iw, ih, s) in bx.items():
            self.assertTrue(E.L.inside_safe(left, top, w, h), sid)
            self.assertGreaterEqual(top, E.SCENE["top"], sid)
            self.assertLessEqual(top + h, E.SCENE["bottom"], sid)
        with open(os.path.join(out, "moments.json")) as f:
            sc = {x["id"]: x for x in json.load(f)["scenes"]}
        for sid, b in bx.items():
            self.assertEqual(sc[sid]["box"], list(b[:4]), sid)
            self.assertEqual(sc[sid]["scale"], b[6], sid)

    def test_a_scene_can_cap_its_scale(self):
        html, _, _ = self.build(BOARD)          # a title sets its own size: it is never blown up past it
        self.assertEqual(boxes(html)["hook"][6], 1.0)

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


if __name__ == "__main__":
    unittest.main()
