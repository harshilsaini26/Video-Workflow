"""The five palettes (colour only, laid on either look): every given colour kept exactly, every role at its contrast on
every ground, nothing on a page outside the palette, and each palette's own rule: Terracotta's exact #E07A5F for shapes,
Electric Pop on white with two colours, Bold Citrus stepping the ground scene by scene."""
import copy, os, re, unittest
from .helpers import load, read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
from . import test_theme as TT
import explainer_lib as E

GIVEN = {"terracotta": ["#E07A5F", "#F2CC8F", "#81B29A", "#3D405B", "#F4F1DE"],
         "monochrome": ["#000000", "#2B2B2B", "#6E6E6E", "#C4C4C4", "#FFFFFF"],
         "electric-pop": ["#FF006E", "#FB5607", "#FFBE0B", "#8338EC", "#3A86FF"],
         "nordic-frost": ["#CAF0F8", "#90E0EF", "#00B4D8", "#0077B6", "#03045E"],
         "bold-citrus": ["#F94144", "#F3722C", "#F8961E", "#F9C74F", "#90BE6D"]}


def tok(name, look="latte"):
    return E.load_tokens(look=look, palette=name)


def low(c):
    return c.lower()


class Palettes(unittest.TestCase):
    def test_the_five_palettes_and_their_cards(self):
        self.assertEqual(E.PALETTES, tuple(GIVEN))
        cards = load(os.path.join(os.path.dirname(E.__file__), "..", "tokens.json"))["palettes"]
        for name, colours in GIVEN.items():
            self.assertEqual(cards[name]["colors"], colours, name)
            for k in ("title", "mood", "use", "best_for"):
                self.assertTrue(cards[name][k], (name, k))

    def test_every_given_colour_is_in_the_page_palette(self):
        for name, colours in GIVEN.items():
            pal = {low(v) for v in tok(name)["palette"].values()}
            for c in colours:
                self.assertIn(low(c), pal, (name, c))

    def test_every_role_meets_its_contrast_in_both_looks(self):
        t = TT.Theme("test_every_role_meets_its_contrast")
        for name in GIVEN:
            for look in E.LOOKS:
                t.contrast(tok(name, look))
                t.glows(tok(name, look))

    def test_a_look_without_a_palette_keeps_its_own_colours(self):
        self.assertEqual(E.load_tokens(look="paper")["palette"], E.load_tokens(look="paper", palette=None)["palette"])
        with self.assertRaises(ValueError):
            E.load_tokens(palette="sunrise")

    def test_terracotta_keeps_its_hex_for_shapes_and_deepens_it_for_words(self):
        c = E.theme(tok("terracotta"), "base")
        self.assertEqual((low(c["bg"]), low(c["ink"])), ("#f4f1de", "#3d405b"))
        self.assertEqual((low(c["highlight"]["fill"]), low(c["highlight"]["text"])), ("#e07a5f", "#3d405b"))
        self.assertIn("#e07a5f", [low(f) for f, _ in c["series"]])
        self.assertNotEqual(low(c["accent"]), "#e07a5f")
        self.assertGreaterEqual(TT.ratio(c["accent"], c["bg"]), 3.0)

    def test_monochrome_has_no_colour(self):
        for v in tok("monochrome")["palette"].values():
            r, g, b = (int(v[i:i + 2], 16) for i in (1, 3, 5))
            self.assertEqual(r, g, v)
            self.assertEqual(g, b, v)

    def test_electric_pop_on_white_uses_two_colours(self):
        t = tok("electric-pop")
        c = E.theme(t, "base")
        self.assertEqual(low(c["bg"]), "#ffffff")
        self.assertEqual(low(c["accent"]), "#ff006e")
        loud = {"#ff006e", "#fb5607", "#ffbe0b", "#8338ec", "#3a86ff"}
        for g in ("mantle", "base", "blue", "ink"):
            th = E.theme(t, g)
            used = {low(x) for x in [th["bg"], th["accent"], th["accent2"], th["highlight"]["fill"]] + [f for f, _ in th["series"]]}
            self.assertLessEqual(used & loud, {"#ff006e", "#8338ec"}, g)
            for f, on in th["series"]:                              # never one bright colour on another
                self.assertFalse(low(f) in loud and low(on) in loud, (g, f, on))

    def test_nordic_frost_reads_darkest_on_lightest(self):
        c = E.theme(tok("nordic-frost"), "base")
        self.assertEqual((low(c["bg"]), low(c["ink"])), ("#caf0f8", "#03045e"))


class Citrus(unittest.TestCase):
    def test_the_ground_steps_scene_by_scene(self):
        d = scratch(self)
        b = copy.deepcopy(BOARD)
        b["palette"] = "bold-citrus"
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), b), "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = read(os.path.join(d, "public", "index.html"))
        fills = [low(f) for f in re.findall(r'<div class="bg" id="bg\d+" style="background:(#[0-9A-Fa-f]{6})', html)]
        self.assertEqual(fills[:3], ["#f94144", "#f3722c", "#f8961e"])
        c = E.theme(tok("bold-citrus"), E.load_tokens(palette="bold-citrus")["cycle"][1])
        self.assertEqual(low(c["ink"]), "#2a1d0e")


class Carried(unittest.TestCase):
    def test_an_unknown_palette_is_named(self):
        d = scratch(self)
        b = dict(copy.deepcopy(BOARD), palette="sunrise")
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), b), "--out", os.path.join(d, "public"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("terracotta", r.stdout)

    def test_the_planner_carries_the_palette(self):
        from . import test_plan as TP
        _, sb, _ = TP.Plan("test_rules_without_a_hint").plan(dict(copy.deepcopy(TP.SCRIPT), palette="nordic-frost"))
        self.assertEqual(sb["palette"], "nordic-frost")


class Pages(unittest.TestCase):
    def test_every_colour_on_every_scene_is_in_its_palette(self):
        t = TT.Theme("test_every_colour_on_every_scene_is_latte")
        for name in GIVEN:
            t.every_colour("latte", {k: low(v) for k, v in tok(name)["palette"].items()}, palette=name)


if __name__ == "__main__":
    unittest.main()
