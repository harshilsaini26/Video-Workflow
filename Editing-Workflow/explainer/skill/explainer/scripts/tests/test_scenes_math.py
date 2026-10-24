"""The math scenes (the 3Blue1Brown-style reference, Video-52107): a plot of loss curves whose tangents slide down to
the minimum, a neural network that lights up forward and sweeps back, and a loss surface a ball descends. Bad data is
refused with a reason, every piece lands on its word, every move is a tween on the timeline (seek-safe), and each
composes on every ground of every look."""
import math, re, unittest
from . import test_scenes_e3 as E3
import explainer_lib as E
from scenes import REGISTRY

W = E3.W
GOOD = {
    "plot": {"type": "plot", "x": "w", "y": "L", "tangent": W(6), "descend": W(9),
             "panels": [{"from": 0.9, "min": 0.1}, {"from": -0.7, "min": 0.3}, {"from": 0.5, "min": -0.4}]},
}
GOOD["network"] = {"type": "network", "layers": [4, 6, 6, 10], "labels": [str(d) for d in range(10)],
                   "input": {"digit": 3, "at": W(5)}, "forward": W(7), "answer": {"node": 8, "at": W(10)}, "backward": W(13)}
GOOD["surface"] = {"type": "surface", "label": "LOSS", "start": [-0.6, 0.55], "descend": {"at": W(8), "steps": 6}}
ANCHORED = {"plot": 2, "network": 4, "surface": 1}


class Shared(E3.Case):
    def test_every_type_is_found(self):
        for t in GOOD:
            self.assertIn(t, REGISTRY)

    def test_pieces_land_on_their_words(self):
        for t, sc in GOOD.items():
            body = self.body(self.ok(sc))
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), ANCHORED[t], t)

    def test_every_ground_of_every_look_and_no_css_animation(self):
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


class Plot(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "plot", "panels": []}, "1 to 6 panels")
        self.fails({"type": "plot", "panels": [{"from": 2, "min": 0}]}, "-1 to 1")
        self.fails({"type": "plot", "panels": [{"from": 0.5, "min": 0.5}]}, "from and min differ")
        self.fails(dict(GOOD["plot"], x="weights"), "at most 3 characters")

    def test_a_curve_per_panel_and_its_point_starts_at_from(self):
        html = self.ok(GOOD["plot"])
        self.assertEqual(len(re.findall(r'class="pl-curve"', html)), 3)
        for i, p in enumerate(GOOD["plot"]["panels"]):
            m = re.search(r'class="pl-panel" id="sc-p%d" data-m="(-?[\d.]+)" data-u="(-?[\d.]+)"' % i, html)
            self.assertTrue(m, i)
            self.assertEqual((float(m.group(1)), float(m.group(2))), (p["min"], p["from"]))
        self.assertRegex(html, r'class="pl-ax"[^>]*>w<')
        self.assertRegex(html, r'class="pl-ax"[^>]*>L<')

    def test_tangents_appear_then_slide_to_the_minimum_seek_safe(self):
        html = self.ok(GOOD["plot"])
        t_tan = re.search(r"tl\.fromTo\('#sc-t0', \{ opacity: 0 \}, \{ opacity: 1,[^}]*\}, ([\d.]+)\);", html)
        self.assertTrue(t_tan)
        self.assertAlmostEqual(float(t_tan.group(1)), E3.lead(6), places=2)
        for i, p in enumerate(GOOD["plot"]["panels"]):
            m = re.search(r"tl\.fromTo\(\{ u: -?[\d.]+ \}, \{ u: (-?[\d.]+) \}, \{ u: (-?[\d.]+), duration: [\d.]+, ease: '[\w.]+', immediateRender: false, "
                          r"onUpdate: function \(\) \{ plotAt\('sc-p%d', this\.targets\(\)\[0\]\.u\); \} \}, ([\d.]+)\);" % i, html)
            self.assertTrue(m, i)
            self.assertEqual((float(m.group(1)), float(m.group(2))), (p["from"], p["min"]))
            self.assertGreaterEqual(float(m.group(3)), E3.lead(9) - 1e-3)
        self.assertIn("window.plotAt = function (id, u)", html)



class Network(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails({"type": "network", "layers": [4]}, "2 to 5 layers")
        self.fails({"type": "network", "layers": [4, 12]}, "1 to 10 nodes")
        self.fails(dict(GOOD["network"], labels=["a", "b"]), "one label per output node")
        self.fails(dict(GOOD["network"], answer={"node": 10, "at": W(10)}), "answer node")
        self.fails(dict(GOOD["network"], input={"digit": 12, "at": W(5)}), "digit 0 to 9")

    def test_every_node_and_every_edge_is_drawn(self):
        html = self.ok(GOOD["network"])
        L = GOOD["network"]["layers"]
        self.assertEqual(len(re.findall(r'class="nw-node"', html)), sum(L))
        self.assertEqual(len(re.findall(r'class="nw-edge"', html)), sum(a * b for a, b in zip(L, L[1:])))
        for d in range(10):
            self.assertRegex(html, r'class="nw-label"[^>]*>%d<' % d)

    def test_the_digit_is_a_pixel_grid(self):
        html = self.ok(GOOD["network"])
        self.assertEqual(len(re.findall(r'class="nw-px"', html)), 35)
        self.assertEqual(len(re.findall(r'class="nw-px" [^>]*data-on="1"', html)), 14)     # a 5x7 three lights 14 cells

    def test_the_forward_pass_lights_layer_by_layer_and_the_backward_sweeps_back(self):
        html = self.ok(GOOD["network"])
        fwd = [float(re.search(r"tl\.fromTo\('#sc-a%d', \{ opacity: 0 \}, \{ opacity: 1,[^}]*\}, ([\d.]+)\);" % l, html).group(1)) for l in range(4)]
        self.assertAlmostEqual(fwd[0], E3.lead(7), places=2)
        self.assertEqual(fwd, sorted(fwd))
        self.assertGreater(fwd[3], fwd[0])
        back = [float(re.search(r"tl\.fromTo\('#sc-b%d', \{ opacity: 0 \}, \{ opacity: 0\.9,[^}]*\}, ([\d.]+)\);" % l, html).group(1)) for l in (1, 2, 3)]
        self.assertEqual(back, sorted(back, reverse=True))                   # from the output back to the input
        self.assertAlmostEqual(back[-1], E3.lead(13), places=2)
        ring = re.search(r"tl\.fromTo\('#sc-ans', \{[^}]*\}, \{[^}]*\}, ([\d.]+)\);", html)
        self.assertAlmostEqual(float(ring.group(1)), E3.lead(10), places=2)

    def test_the_weights_are_seeded(self):
        a, b = self.ok(GOOD["network"]), self.ok(GOOD["network"])
        edges = lambda h: re.findall(r'class="nw-edge"[^>]*>', h)
        self.assertEqual(edges(a), edges(b))
        self.assertGreater(len(set(re.findall(r'class="nw-edge" [^>]*stroke="(#\w+)"', a))), 1)    # two signs, two colours



class Surface(E3.Case):
    def test_bad_data_is_refused(self):
        self.fails(dict(GOOD["surface"], descend={"at": W(8), "steps": 20}), "1 to 10 steps")
        self.fails(dict(GOOD["surface"], start=[0.9, 0.8]), "inside the rim")
        self.fails(dict(GOOD["surface"], lr=1), "lr is 0.05 to 0.45")

    def test_the_bowl_is_a_mesh_painted_back_to_front(self):
        html = self.ok(GOOD["surface"])
        depth = [float(d) for d in re.findall(r'<polygon class="sf-q" data-d="(-?[\d.]+)"', html)]
        self.assertEqual(len(depth), 10 * 36)
        self.assertEqual(depth, sorted(depth))
        self.assertRegex(html, r'class="sf-label"[^>]*>LOSS<')

    def test_the_ball_steps_down_hill_on_its_word(self):
        html = self.ok(GOOD["surface"])
        hops = [float(t) for t in re.findall(r"tl\.to\('#sc-ball', \{ x: -?[\d.]+, y: -?[\d.]+, duration: [\d.]+, ease: '[\w.]+' \}, ([\d.]+)\);", html)]
        self.assertEqual(len(hops), 6)
        self.assertAlmostEqual(hops[0], E3.lead(8), places=2)
        self.assertEqual(hops, sorted(hops))
        z = [float(v) for v in re.findall(r'class="sf-trail" data-z="([\d.]+)"', html)]
        self.assertEqual(len(z), 6)
        self.assertEqual(z, sorted(z, reverse=True))                              # every step lower than the last


if __name__ == "__main__":
    unittest.main()
