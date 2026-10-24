"""The continuous stage (the 3Blue1Brown-style reference, Video-52107): one picture that keeps changing instead of a cut
per idea. Library scenes are its objects, each in its own box in the scene area; they come in and leave on their words,
and on a word an object moves and resizes to a new box (the network shrinks aside, the formula changes above it). Every
box at every move stays in the scene area with its words at 28 px or more; a number inside an object still needs a
source; each object's own CSS comes with it."""
import copy, json, os, re, unittest
import layout_check as LC
from . import test_scenes_e3 as E3
from .test_scenes_math import GOOD as MATH

W = E3.W
NET = {k: v for k, v in MATH["network"].items() if k not in ("input", "backward", "labels")}   # no words: it may shrink
STAGE = {"type": "stage", "objects": [
    {"id": "eq", "scene": {"type": "formula", "tex": "e = \\hat{y} - y"}, "box": [175, 0, 600], "in": W(5), "out": W(10)},
    {"id": "net", "scene": dict(NET, forward=W(6), answer={"node": 8, "at": W(8)}), "box": [175, 200, 600]},
    {"id": "pl", "scene": dict(MATH["plot"], tangent=W(12), descend=W(13), panels=MATH["plot"]["panels"][:2]), "box": [325, 330, 600], "in": W(11)}],
    "moves": [{"obj": "net", "at": W(10), "box": [0, 0, 300]}]}


class Stage(E3.Case):
    def test_bad_data_is_refused(self):
        bad = lambda **kw: dict(copy.deepcopy(STAGE), **kw)
        self.fails(bad(objects=[{"id": "x", "scene": {"type": "nope"}, "box": [0, 0, 600]}]), "unknown scene type 'nope'")
        self.fails(bad(objects=[{"id": "x", "scene": {"type": "stage", "objects": []}, "box": [0, 0, 600]}]), "a stage cannot hold a stage")
        self.fails(bad(objects=[{"id": "x", "scene": NET, "box": [500, 0, 600]}], moves=[]), "outside the scene area")
        self.fails(bad(moves=[{"obj": "nobody", "at": W(10), "box": [0, 0, 300]}]), "no object 'nobody'")
        self.fails(bad(moves=[{"obj": "pl", "at": W(14), "box": [0, 0, 200]}]), "28 px")
        self.fails(bad(objects=STAGE["objects"] + [dict(STAGE["objects"][0])]), "used twice")
        self.fails(bad(objects=[{"id": "x", "scene": dict(NET, layers=[40]), "box": [0, 0, 600]}], moves=[]), "x: a network takes 2 to 5 layers")
        many = [{"id": "e%d" % k, "scene": {"type": "formula", "tex": "x"}, "box": [175, 0, 600]} for k in range(13)]
        self.fails(bad(objects=many, moves=[]), "1 to 12 objects")

    def test_objects_sit_in_their_boxes_and_bring_their_css(self):
        html = self.ok(STAGE)
        for o in STAGE["objects"]:
            # the wrapper GSAP moves carries no CSS transform (HyperFrames: gsap_css_transform_conflict); the fit is inside it
            m = re.search(r'<div class="st-obj" id="sc_%s-obj" style="left:(\d+)px;top:(\d+)px;width:\d+px;height:\d+px[^"]*">'
                          r'<div class="st-fit" style="width:(\d+)px;[^"]*transform:scale\(([\d.]+)\)' % o["id"], html)
            self.assertTrue(m, o["id"])
            self.assertEqual((int(m.group(1)), int(m.group(2))), tuple(o["box"][:2]))
            self.assertAlmostEqual(int(m.group(3)) * float(m.group(4)), o["box"][2], delta=2)
        self.assertIn("id=\"sc_net-nw\"", html)
        self.assertNotRegex(html, r'class="st-obj"[^>]*transform')
        for rule in (".nw-label {", ".pl-ax {", ".f-row {"):
            self.assertIn(rule, html)

    def test_objects_come_in_move_and_leave_on_their_words(self):
        html = self.ok(STAGE)
        mv = re.search(r"tl\.to\('#sc_net-obj', \{ x: (-?[\d.]+), y: (-?[\d.]+), scale: ([\d.]+), duration: [\d.]+, ease: '[\w.]+' \}, ([\d.]+)\);", html)
        self.assertTrue(mv)
        self.assertEqual((float(mv.group(1)), float(mv.group(2)), float(mv.group(3))), (-175.0, -200.0, 0.5))   # 600 px wide to 300
        self.assertAlmostEqual(float(mv.group(4)), E3.lead(10), places=2)
        out = re.search(r"tl\.to\('#sc_eq-obj', \{ opacity: 0, [^}]*\}, ([\d.]+)\);", html)
        self.assertAlmostEqual(float(out.group(1)), E3.lead(10) - 0.2, places=2)
        ins = re.search(r"tl\.fromTo\('#sc_pl-p0', \{ opacity: 0[^}]*\}, \{[^}]*\}, ([\d.]+)\);", html)
        self.assertAlmostEqual(float(ins.group(1)), E3.lead(11), places=2)
        self.assertGreaterEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', self.body(html))), 6)

    def test_an_object_is_hidden_until_its_word(self):
        # a scene's own entrances only bring in some of its parts: the object itself waits unseen until its `in`
        html = self.ok(STAGE)
        self.assertRegex(html, r'<div class="st-obj" id="sc_pl-obj" style="[^"]*visibility:hidden')
        m = re.search(r"tl\.set\('#sc_pl-obj', \{ visibility: 'visible' \}, ([\d.]+)\);", html)
        self.assertAlmostEqual(float(m.group(1)), E3.lead(11), places=2)
        self.assertNotRegex(html, r'<div class="st-obj" id="sc_net-obj" style="[^"]*visibility:hidden')   # in from the start

    def test_a_number_inside_an_object_needs_a_source(self):
        st = copy.deepcopy(STAGE)
        st["objects"].append({"id": "n", "scene": {"type": "count-up", "value": 96, "suffix": "%"}, "box": [0, 0, 600], "in": W(14)})
        self.fails(st, "needs a source")


    def test_gate_e5_looks_at_every_beat_not_only_the_last(self):
        self.ok(STAGE)
        with open(os.path.join(self.out, "moments.json"), encoding="utf-8") as f:
            m = json.load(f)
        sc = [s for s in m["scenes"] if s["id"] == "sc"][0]
        self.assertIn(round(E3.lead(10), 3), sc["beats"])                 # the move
        shots = [s["t"] for s in LC.samples(m) if s["id"] == "sc"]
        self.assertGreaterEqual(len(shots), 4)
        for b in sc["beats"]:
            if b - sc["in"] > 0.6:
                self.assertTrue(any(b - 0.6 <= t < b for t in shots), b)    # the settled picture before each change



class FormulaOverlap(unittest.TestCase):
    """Gate E5 judges a typeset formula by its glyphs: a hat, a subscript or a descender touching another object's words
    is caught (the line-box middle that suits plain text cut those off)."""

    def compose(self, eq_y, out_y):
        from .test_layout import have_browser
        from .helpers import run, scratch, write
        from .test_compose import VOICE, silent_wav, words30
        vendor = os.environ.get("EXPLAINER_VENDOR")
        if not have_browser() or not vendor or not os.path.isdir(os.path.join(vendor, "katex")):
            self.skipTest("needs Chrome and the real vendor folder (EXPLAINER_VENDOR with katex)")
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        out = MATH["outputs"]
        st = {"type": "stage", "id": "st", "bg": "mantle", "in": W(2), "out": "end", "objects": [
            {"id": "eq", "scene": {"type": "formula", "tex": r"e = \hat{y}_i - y_i"}, "box": [175, eq_y, 600]},
            {"id": "out", "scene": dict(out, at=W(3), target={"row": 3, "at": W(4)}, error=W(5), loss=W(6)), "box": [330, out_y, 535]}]}
        sb = {"id": "t", "look": "dark", "captions": "off", "sound": {"music": "none", "sfx": False},
              "scenes": [{"type": "title", "id": "hook", "bg": "mantle", "in": "word:0", "out": W(2), "text": "Lead in"}, st]}
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), sb), "--out", os.path.join(d, "public"),
                "--vendor", vendor)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return run("layout-check.py", "--index", os.path.join(d, "public", "index.html"), "--no-hf")

    def test_a_formula_touching_a_chart_fails(self):
        r = self.compose(60, 200)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"E5 FAIL: st: .*e ?=")

    def test_the_same_two_apart_pass(self):
        r = self.compose(0, 195)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
