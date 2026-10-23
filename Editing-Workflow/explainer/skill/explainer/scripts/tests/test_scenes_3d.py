"""The 3D box scenes (CSS 3D, seek-safe): bars-3d rising on a tilted floor, the labelled cube that turns and twists, and
3D number cards dropping in. Each refuses bad data with a reason, lands its pieces on their words, grows by tweening on
the timeline (never a CSS animation), keeps its labels flat over the 3D so gate E5 can read them, and composes on every
ground of both looks. And the light-leak wipe: a soft streak over the cut, never picked on its own."""
import copy, re, unittest
from . import test_scenes_e3 as E3
from .test_compose import BOARD, D, t_word
import explainer_lib as E
import transitions as X
from scenes import REGISTRY

W = E3.W
TYPES = ("bars-3d", "cube", "cards-3d")
GOOD = {
    "bars-3d": {"type": "bars-3d", "source": "s1", "floor": "THREE-STATEMENT MODEL", "bars": [
        {"label": "MERGER", "value": 60, "at": W(6)}, {"label": "LBO", "value": 100, "at": W(8)}, {"label": "DCF", "value": 35, "at": W(10)}]},
    "cube": {"type": "cube", "at": W(5), "turns": [{"dir": "right", "at": W(8)}, {"dir": "right", "at": W(11)}],
             "twist": [{"dir": "left", "at": W(14)}], "highlight": {"cell": "B2", "at": W(16)}},
    "cards-3d": {"type": "cards-3d", "cards": [{"text": "1", "at": W(6)}, {"text": "2", "at": W(8)}, {"text": "3", "sub": "the core", "at": W(10)}]},
}
ANCHORED = {"bars-3d": 3, "cube": 5, "cards-3d": 3}           # the bars; the cube, its turns, twist and highlight; the cards


class Shared(E3.Case):
    def test_every_type_is_found(self):
        for t in TYPES:
            self.assertIn(t, REGISTRY)

    def test_pieces_land_on_their_words(self):
        for t, sc in GOOD.items():
            body = self.body(self.ok(sc))
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), ANCHORED[t], t)

    def test_every_ground_of_both_looks_and_no_css_animation(self):
        for look in E.LOOKS:
            for t, sc in GOOD.items():
                for bg in ("mantle", "base", "blue", "ink"):
                    html = self.ok(sc, bg=bg, look=look)
                    self.assertNotRegex(self.body(html), r"repeat:|yoyo|Math\.random|Date\b|@keyframes|animation:", (look, t, bg))

    def test_heights_are_fixed_by_width(self):
        for t, sc in GOOD.items():
            m = REGISTRY[t]
            self.assertLessEqual(abs(m.height(sc, 950) * 780 - m.height(sc, 780) * 950), 2 * 950, t)   # a fixed aspect
            self.assertGreater(m.height(sc, 780), 300, t)


class Bars3D(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "bars-3d", "source": "s1", "bars": [{"label": "A", "value": 1, "at": W(6)}]}, "2 to 4 bars")
        self.fails({"type": "bars-3d", "source": "s1", "bars": [{"label": "A", "value": -1, "at": W(6)}, {"label": "B", "value": 2, "at": W(7)}]},
                   "a number >= 0")
        self.fails({"type": "bars-3d", "source": "s1", "bars": [{"label": "A", "value": 1}, {"label": "B", "value": 2, "at": W(7)}]}, "has no at")

    def test_three_faces_per_bar_and_heights_in_proportion(self):
        body = self.body(self.ok(GOOD["bars-3d"]))
        for i in range(3):
            self.assertEqual(len(re.findall(r'class="b3-f b3-(?:top|s|e)"', body.split('id="sc-b%d"' % i)[1].split("</div></div>")[0] + "</div>")), 3)
        hs = [float(h) for h in re.findall(r'data-h="([\d.]+)"', body)]
        self.assertEqual(len(hs), 3)
        self.assertAlmostEqual(hs[0] / hs[1], 0.6, places=2)
        self.assertAlmostEqual(hs[2] / hs[1], 0.35, places=2)

    def test_each_bar_grows_on_its_word_seek_safe(self):
        html = self.ok(GOOD["bars-3d"])
        for i, w in enumerate((6, 8, 10)):
            m = re.search(r"tl\.fromTo\('#sc-b%d', \{ '--h': 0 \}, \{ '--h': ([\d.]+),[^}]*immediateRender: false \}, ([\d.]+)\);" % i, html)
            self.assertTrue(m, i)
            self.assertAlmostEqual(float(m.group(2)), E3.lead(w) + 0.08, places=2)

    def test_labels_and_the_floor_caption_sit_flat_over_the_3d(self):
        body = self.body(self.ok(GOOD["bars-3d"]))
        flat = body.split('class="b3-labels"')[1]
        for name in ("MERGER", "LBO", "DCF"):
            self.assertIn(">%s<" % name, flat)
        self.assertRegex(flat, r'class="b3-cap"[^>]*>THREE-STATEMENT MODEL<')     # flat under the floor: tilted, it read too small


class Cube(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "cube", "at": W(5), "labels": ["A1"]}, "9 labels")
        self.fails({"type": "cube", "at": W(5), "turns": [{"dir": "sideways", "at": W(7)}]}, "left, right, up or down")
        self.fails({"type": "cube", "at": W(5), "twist": [{"dir": "up", "at": W(7)}]}, "left or right")
        self.fails({"type": "cube", "at": W(5), "highlight": {"cell": "Z9", "at": W(7)}}, "Z9")

    def test_27_cubies_with_the_labels_on_the_front(self):
        body = self.body(self.ok(GOOD["cube"]))
        self.assertEqual(len(re.findall(r'class="cb-q"', body)), 27)
        self.assertEqual(re.findall(r'class="cb-l"[^>]*>([A-C]\d)<', body), ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"])

    def test_turns_add_up_and_the_twist_moves_the_top_layer(self):
        html = self.ok(GOOD["cube"])
        turns = re.findall(r"tl\.to\('#sc-turn', \{ rotationY: (-?\d+),[^}]*\}, ([\d.]+)\);", html)
        self.assertEqual([int(r) for r, _ in turns], [-90, -180])
        self.assertAlmostEqual(float(turns[0][1]), E3.lead(8), places=2)
        self.assertRegex(html, r"tl\.to\('#sc-top', \{ rotationY: 90,")
        self.assertIn('id="sc-top"', html)
        self.assertEqual(len(re.findall(r'class="cb-q"', html.split('id="sc-top"')[1].split('id="sc-rest"')[0])), 9)


class Cards3D(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "cards-3d", "cards": []}, "1 to 4 cards")
        self.fails({"type": "cards-3d", "cards": [{"text": "TOO LONG", "at": W(6)}]}, "at most 3 characters")
        self.fails({"type": "cards-3d", "cards": [{"text": "$5", "at": W(6)}]}, "is a figure")

    def test_each_card_has_depth_and_drops_on_its_word(self):
        html = self.ok(GOOD["cards-3d"])
        body = self.body(html)
        self.assertEqual(len(re.findall(r'class="c3-card"', body)), 3)
        self.assertEqual(len(re.findall(r'class="c3-edge', body)), 6)            # a right and a bottom edge each
        for i, w in enumerate((6, 8, 10)):
            m = re.search(r"tl\.fromTo\('#sc-c%d', \{[^}]*y: -(\d+)[^}]*\}, \{[^}]*immediateRender: false \}, ([\d.]+)\);" % i, html)
            self.assertTrue(m, i)
            self.assertAlmostEqual(float(m.group(2)), E3.lead(w), places=2)
        self.assertIn(">the core<", body)


class Leak(unittest.TestCase):
    def test_the_streak_is_centred_on_the_cut(self):
        html, js = X.leak(3, 5.0, ["#ff006e", "#8338ec"])
        self.assertIn('class="tx-leak"', html)
        self.assertIn("mix-blend-mode:screen", html)
        m = re.search(r"tl\.fromTo\('#txl3', \{ x: (-?\d+)[^}]*\}, \{ x: (-?\d+), duration: ([\d.]+)[^}]*\}, ([\d.]+)\);", js[0])
        x0, x1, dur, start = int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4))
        self.assertAlmostEqual(start + dur / 2, 5.0, places=3)
        self.assertLess(x0, -1080)
        self.assertGreater(x1, 1080)

    def test_never_picked_on_its_own(self):
        self.assertIn("leak", X.KINDS)
        for i in range(8):
            for prev, bg in (("mantle", "mantle"), ("mantle", "blue"), (None, "base")):
                for look in ("latte", "paper"):
                    self.assertNotEqual(X.pick(i, prev, bg, None, look=look), "leak")

    def test_a_named_leak_composes_in_the_palette_colours_with_a_whoosh(self):
        from . import test_transitions as TT
        b = copy.deepcopy(BOARD)
        b["scenes"][1]["transition"] = "leak"
        html = TT.InThePage.build(self, b)
        self.assertIn('id="txl1"', html)
        c = E.theme(E.load_tokens(), b["scenes"][0]["bg"])
        self.assertIn(E.rgba(c["accent"], 0.85), html)
        import sound
        cut = t_word(8) - E.LEAD
        self.assertIn((round(cut - sound.LEAD, 3), "whoosh"), sound.events([("leak", cut)], []))


if __name__ == "__main__":
    unittest.main()
