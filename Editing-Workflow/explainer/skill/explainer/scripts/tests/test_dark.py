"""The dark look (the 3Blue1Brown-style reference, Video-52107): every ground near-black or deep, manim's colours on it,
nothing on a page outside its own palette; a storyboard may turn the captions off, and may close with a rewind."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
from .test_theme import Theme, lum
import explainer_lib as E
import transitions as X

DARK = E.load_tokens(look="dark")


class Look(unittest.TestCase):
    def test_it_is_a_look(self):
        self.assertIn("dark", E.LOOKS)
        self.assertEqual(DARK["look"], "dark")

    def test_every_ground_is_dark_and_the_main_one_near_black(self):
        for name in DARK["backgrounds"]:
            c = E.theme(DARK, name)
            self.assertTrue(c["dark"], name)
            self.assertLess(lum(c["bg"]), 0.04, (name, c["bg"]))
        self.assertLess(lum(E.theme(DARK, "mantle")["bg"]), 0.008)

    def test_words_are_light_and_the_accent_is_manims_blue(self):
        c = E.theme(DARK, "mantle")
        self.assertGreater(lum(c["ink"]), 0.7)
        self.assertEqual(c["accent"].lower(), "#58c4dd")

    def test_ui_mockups_stay_light_paper(self):
        for name in DARK["backgrounds"]:
            c = E.theme(DARK, name)
            self.assertGreater(lum(c["paper"]), 0.7, name)
            self.assertLess(lum(c["paper_ink"]), 0.05, name)


class Pages(unittest.TestCase):
    every_colour, compose = Theme.every_colour, Theme.compose

    def test_every_colour_on_every_dark_scene_is_dark(self):
        self.every_colour("dark", {k: v.lower() for k, v in DARK["palette"].items()})


class Board(unittest.TestCase):
    def build(self, board):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), board), "--out", os.path.join(d, "public"))
        return r, (read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else "")

    def test_captions_can_be_turned_off(self):
        b = copy.deepcopy(BOARD)
        b["captions"] = "off"
        r, html = self.build(b)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn('class="cap"', html)
        self.assertNotIn("#cap0", html)
        b["captions"] = "maybe"
        r, _ = self.build(b)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("captions is \"off\" or {emphasis}", r.stdout + r.stderr)

    def test_a_reel_can_close_with_a_rewind(self):
        # the last scene streaks back as a rewind mark (two left triangles) shows, then the hook's ground comes in
        b = copy.deepcopy(BOARD)
        b["close"] = "rewind"
        r, html = self.build(b)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        D = round(VOICE + E.TAIL, 3)
        self.assertRegex(html, r'<div class="rw" id="rw"')
        self.assertIn("tl.fromTo('#rw', { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.12, ease: 'power3.out', immediateRender: false }, %.3f);"
                      % (D - X.CLOSE), html)
        self.assertRegex(html, r"tl\.to\('#cu', \{ opacity: 0, x: 160, filter: 'blur\(14px\)', duration: %s, ease: 'power3.in' \}, %.3f\);"
                         % (X.CLOSE / 2, D - X.CLOSE))
        b["close"] = "spin"
        r, _ = self.build(b)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("close is \"fade\" or \"rewind\"", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
