"""The 3D containers and round objects: a briefcase whose lid opens and papers rise on the word, a beaker filling in
labelled layers, a thick donut whose slices sweep in, and a coin that flips in. Like the box scenes: bad data refused
with a reason, every piece on its word, tweens on the timeline (seek-safe), words flat over the 3D for gate E5, and
every ground of both looks."""
import re, unittest
from . import test_scenes_e3 as E3
import explainer_lib as E
from scenes import REGISTRY

W = E3.W
TYPES = ("briefcase", "beaker", "donut", "coin")
GOOD = {
    "briefcase": {"type": "briefcase", "at": W(5), "open": W(8), "papers": 3, "label": "THE DEAL BOOK"},
    "beaker": {"type": "beaker", "source": "s1", "layers": [{"label": "DEBT", "value": 60, "at": W(6)},
                                                           {"label": "EQUITY", "value": 40, "at": W(9)}]},
    "donut": {"type": "donut", "source": "s1", "center": "$2,600M", "slices": [
        {"label": "STOCK", "value": 780, "text": "$780M", "at": W(6)}, {"label": "CASH", "value": 1040, "text": "$1,040M", "at": W(8)},
        {"label": "DEBT", "value": 780, "text": "$780M", "at": W(10)}]},
    "coin": {"type": "coin", "text": "EPS", "dir": "up", "sub": "earnings per share", "at": W(6)},
}
ANCHORED = {"briefcase": 2, "beaker": 2, "donut": 3, "coin": 1}


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

    def test_heights_keep_their_aspect_and_fit_the_area(self):
        for t, sc in GOOD.items():
            m = REGISTRY[t]
            self.assertLessEqual(abs(m.height(sc, 950) * 780 - m.height(sc, 780) * 950), 2 * 950, t)
            self.assertLessEqual(m.height(sc, m.min_width(sc)), 712, t)


class Briefcase(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "briefcase", "at": W(5)}, "open")
        self.fails({"type": "briefcase", "at": W(5), "open": W(8), "papers": 9}, "1 to 5 papers")

    def test_the_lid_opens_and_the_papers_rise_on_the_word(self):
        html = self.ok(GOOD["briefcase"])
        lid = re.search(r"tl\.to\('#sc-lid', \{ rotationX: (-?\d+), [^}]*\}, ([\d.]+)\);", html)
        self.assertTrue(lid)
        self.assertGreater(abs(int(lid.group(1))), 60)
        self.assertAlmostEqual(float(lid.group(2)), E3.lead(8), places=2)
        self.assertEqual(len(re.findall(r'class="bc-paper"', html)), 3)
        rises = re.findall(r"tl\.fromTo\('#sc-p\d', \{[^}]*\}, \{[^}]*immediateRender: false \}, ([\d.]+)\);", html)
        self.assertEqual(len(rises), 3)
        self.assertTrue(all(float(t) > E3.lead(8) for t in rises))
        self.assertRegex(html, r'class="bc-cap"[^>]*>THE DEAL BOOK<')


class Beaker(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "beaker", "source": "s1", "layers": [{"label": "A", "value": 70, "at": W(6)},
                                                                {"label": "B", "value": 50, "at": W(7)}]}, "100")
        self.fails({"type": "beaker", "source": "s1", "layers": []}, "1 to 4 layers")

    def test_layers_fill_from_the_bottom_in_proportion(self):
        html = self.ok(GOOD["beaker"])
        hs = [float(h) for h in re.findall(r'class="bk-layer" id="sc-k\d" data-h="([\d.]+)"', html)]
        self.assertEqual(len(hs), 2)
        self.assertAlmostEqual(hs[0] / hs[1], 1.5, places=2)
        for i, w in enumerate((6, 9)):
            m = re.search(r"tl\.fromTo\('#sc-k%d', \{ scaleY: 0 \}, \{ scaleY: 1,[^}]*immediateRender: false \}, ([\d.]+)\);" % i, html)
            self.assertTrue(m, i)
            self.assertAlmostEqual(float(m.group(1)), E3.lead(w), places=2)
        self.assertRegex(html, r">60% DEBT<|>DEBT<")


class Donut(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "donut", "source": "s1", "slices": [{"label": "A", "value": 1, "at": W(6)}]}, "2 to 5 slices")
        self.fails({"type": "donut", "source": "s1", "slices": [{"label": "A", "value": -1, "at": W(6)},
                                                               {"label": "B", "value": 1, "at": W(7)}]}, "a number > 0")

    def test_slices_sweep_in_their_share_on_their_words(self):
        html = self.ok(GOOD["donut"])
        total = 780 + 1040 + 780
        shares = [float(x) for x in re.findall(r'class="dn-slice" id="sc-s\d" data-share="([\d.]+)"', html)]
        self.assertEqual([round(s, 3) for s in shares], [round(780 / total, 3), round(1040 / total, 3), round(780 / total, 3)])
        for i, w in enumerate((6, 8, 10)):
            self.assertRegex(html, r"tl\.fromTo\('#sc-s%d [^']*', \{ strokeDasharray: '0 [\d.]+' \}, \{ strokeDasharray: '[\d.]+ [\d.]+',[^}]*"
                                   r"immediateRender: false \}, %.3f\);" % (i, E3.lead(w)))
        self.assertRegex(html, r'class="dn-center"[^>]*>\$2,600M<')
        for t in ("$780M", "$1,040M"):
            self.assertIn(">%s<" % t, html.split('class="dn-labels"')[1])

    def test_the_ring_has_depth(self):
        html = self.ok(GOOD["donut"])
        self.assertGreaterEqual(len(re.findall(r'class="dn-depth"', html)), 6)


class Coin(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "coin", "at": W(6)}, "text")
        self.fails({"type": "coin", "text": "TOOLONG", "at": W(6)}, "at most 4 characters")
        self.fails({"type": "coin", "text": "EPS", "dir": "sideways", "at": W(6)}, "up or down")

    def test_it_flips_in_on_its_word_and_has_an_edge(self):
        html = self.ok(GOOD["coin"])
        m = re.search(r"tl\.fromTo\('#sc-coin', \{[^}]*rotationY: (-?\d+)[^}]*\}, \{[^}]*rotationY: 0,[^}]*immediateRender: false \}, ([\d.]+)\);", html)
        self.assertTrue(m)
        self.assertGreaterEqual(abs(int(m.group(1))), 360)
        self.assertAlmostEqual(float(m.group(2)), E3.lead(6), places=2)
        self.assertGreaterEqual(len(re.findall(r'class="cn-edge"', html)), 24)
        self.assertRegex(html, r'class="cn-text"[^>]*>EPS<')
        self.assertIn("earnings per share", html)


if __name__ == "__main__":
    unittest.main()
