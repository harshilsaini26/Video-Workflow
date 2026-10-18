"""The editorial pass (the Bose reference, 2026-10-18): captions small at the bottom so the centre is always the
animation's, the paper look, three typefaces, the headline layer."""
import os, re, unittest
from .helpers import load, read
from .test_compose import BOARD
from .test_foundations import compose
import explainer_lib as E

TOK = E.load_tokens()


class Layout(unittest.TestCase):
    def test_captions_sit_at_the_bottom_small(self):
        # the captions leave the centre: 44 px, at most two lines, at the bottom of the safe area in the narrow column
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        css = re.search(r"\.cap \{[^}]*\}", page).group(0)
        self.assertIn("left:150px; width:780px; top:1130px; height:105px;", css)
        self.assertIn("font-size:44px", css)
        self.assertEqual(E.CAPTION_BAND, (1130, 1235))
        self.assertEqual(E.CAPTION_SIZE, 44)

    def test_the_centre_is_the_scenes(self):
        self.assertEqual(E.SCENE, {"left": 65, "top": 345, "right": 1015, "bottom": 1105})
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        for sc in load(os.path.join(d, "public", "moments.json"))["scenes"]:
            left, top, w, h = sc["box"]
            self.assertGreaterEqual(top, 345, sc["id"])
            self.assertLessEqual(top + h, 1105, sc["id"])

    def test_a_wide_scene_centres_in_the_area_unless_it_would_reach_the_buttons(self):
        # the centre is the animation's: a full-width scene centres on the area's middle (725), and only a tall one
        # rises, just enough to end above y 960 (the action column)
        from . import explainer_compose_shim as C
        import explainer_lib as E2

        def mod(h):
            class M:
                TYPE, CSS, MAX_SCALE = "m", ".m { font-size:40px; }", 1.0
                min_width = staticmethod(lambda sc: 900)
                height = staticmethod(lambda sc, w: h)
            return M
        left, top, w, h, iw, ih, s = C.place("small", mod(300), {})
        self.assertEqual(w, 950)
        self.assertAlmostEqual(top + h / 2.0, 725, delta=1)
        left, top, w, h, iw, ih, s = C.place("tall", mod(560), {})
        self.assertEqual(w, 950)
        self.assertLessEqual(top + h, E2.L.RIGHT_COL_TOP - E2.IDLE_ROOM)
        self.assertGreaterEqual(top, E2.SCENE["top"] + E2.IDLE_ROOM)

    def test_captions_have_a_halo_in_the_grounds_colour(self):
        # a bare shape may pass behind the captions (it runs on to y 1650): the words keep a halo of their ground
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        for i, bg in ((0, "mantle"),):
            m = re.search(r'<div class="cap" id="cap%d" style="([^"]*)"' % i, page)
            self.assertIn("text-shadow:0 0 18px %s, 0 0 6px %s" % ((E.theme(TOK, bg)["bg"],) * 2), m.group(1))


class Looks(unittest.TestCase):
    def test_paper_overrides_the_palette_by_name(self):
        paper = E.load_tokens(look="paper")
        self.assertEqual(paper["look"], "paper")
        self.assertEqual(paper["palette"]["base"], "#EFEAE3")
        self.assertEqual(paper["palette"]["text"], "#141414")
        self.assertEqual(E.theme(paper, "base")["accent"], "#D9472E")
        self.assertEqual(set(paper["palette"]), set(TOK["palette"]))          # the same 26 names: scenes resolve either look
        self.assertEqual(paper["motion"], TOK["motion"])                      # what a look does not name stays

    def test_latte_is_the_default(self):
        self.assertEqual(E.LOOKS, ("latte", "paper"))
        self.assertEqual(E.load_tokens()["look"], "latte")
        self.assertEqual(E.load_tokens(look="latte")["palette"], TOK["palette"])

    def test_a_paper_reel_composes_on_paper(self):
        board = dict(BOARD, look="paper")
        r, d = compose(self, board)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        self.assertIn("background:#EFEAE3".lower(), page.lower().replace(" ", ""))
        self.assertEqual(load(os.path.join(d, "public", "moments.json"))["look"], "paper")

    def test_an_unknown_look_fails_naming_the_known_ones(self):
        r, _ = compose(self, dict(BOARD, look="neon"))
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E3 FAIL", r.stdout)
        self.assertIn("latte, paper", r.stdout)

    def test_the_planner_puts_a_paper_reel_on_one_ground(self):
        # the editorial look keeps one ground: colour comes from the pictures and the accent, not from the ground
        from .test_plan import SCRIPT, Plan
        import copy
        script = dict(copy.deepcopy(SCRIPT), payoff="l4", look="paper")
        _, sb, _ = Plan.plan(self, script)
        self.assertEqual(sb["look"], "paper")
        self.assertEqual({s["bg"] for s in sb["scenes"]}, {"base"})


if __name__ == "__main__":
    unittest.main()
