"""Three film grammars from huashu-art-motion (MIT, alchaincyf): 3Blue1Brown's Transform (one object becomes the next,
never a cut), Kurzgesagt's flat world (no outlines, two-tone facets, a camera that crosses scales) and Vox's evidence
desk (clippings, red lines, a highlighter, the marks moving on twos). Bad data is refused with a reason, every piece
lands on its word, every move is a tween on the timeline (seek-safe), and each composes on every ground of every look."""
import math, re, unittest
from . import test_scenes_e3 as E3
import explainer_lib as E
from scenes import REGISTRY

W = E3.W
GOOD = {
    "morph": {"type": "morph", "n": 16, "values": [0.2, 0.9, 0.9, 0.2, 0.9, 0.2, 0.2, 0.9, 0.9, 0.2, 0.2, 0.9, 0.2, 0.9, 0.9, 0.2],
              "steps": [{"form": "grid", "at": W(5), "label": "Pixels"},
                        {"form": "column", "at": W(8), "label": "Input neurons", "color": "accent2"},
                        {"form": "merge", "at": W(11), "label": "One weighted sum", "color": "accent"}]},
}
GOOD["orbit"] = {"type": "orbit", "center": "A drop of sea water",
                 "nodes": [{"text": "Plankton", "at": W(5)}, {"text": "Salt", "at": W(6)}],
                 "dive": {"into": 0, "at": W(8), "center": "A diatom",
                          "nodes": [{"text": "Silica shell", "at": W(14)}, {"text": "Chloroplast", "at": W(16)}]}}
GOOD["clippings"] = {"type": "clippings", "source": "le2012",
                     "items": [{"kind": "clipping", "head": "A computer learns to see cats",
                                "lines": ["1,000 machines, 16,000 cores", "Ten million video frames", "No labels at all"], "at": W(5)},
                               {"kind": "label", "text": "2012 · Google", "at": W(9)},
                               {"kind": "note", "text": "Nobody told it what a cat is", "at": W(12)}],
                     "marks": [{"kind": "highlight", "item": 0, "line": 1, "at": W(7)},
                               {"kind": "circle", "item": 1, "at": W(10)},
                               {"kind": "underline", "item": 2, "at": W(14)}]}
ANCHORED = {"morph": 3, "orbit": 5, "clippings": 6}


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

    def test_heights_fit_the_area(self):
        for t, sc in GOOD.items():
            m = REGISTRY[t]
            self.assertLessEqual(m.height(sc, m.min_width(sc)), 712, t)


class Morph(E3.Case):
    def test_bad_data_is_refused(self):
        sc = GOOD["morph"]
        self.fails(dict(sc, n=2), "n is 4 to 64")
        self.fails(dict(sc, steps=sc["steps"][:1]), "2 to 6 steps")
        self.fails(dict(sc, steps=[dict(sc["steps"][0], form="blob"), sc["steps"][1]]), "form is one of grid, column, row, ring, bars, merge")
        self.fails(dict(sc, values=[0.5] * 3), "values: one 0 to 1 per piece (16)")
        self.fails(dict(sc, steps=[sc["steps"][0], dict(sc["steps"][1], color="purple")]), "color is a role")
        self.fails(dict(sc, steps=[sc["steps"][0], dict(sc["steps"][1], form="bars")]), "bars needs heights")
        self.fails(dict(sc, steps=[sc["steps"][0], dict(sc["steps"][1], label="x" * 40)]), "label: 1 to 28 characters")

    def test_every_piece_is_one_path_with_the_same_points_in_every_form(self):
        # a Transform tweens each point to its partner: every form gives every piece the same number of points, from its
        # top-left, clockwise, so nothing twists or flips on the way
        import scenes.morph as M
        for form in ("grid", "column", "row", "ring", "merge"):
            shapes = M.forms({"form": form}, 16, 780, 600)
            self.assertEqual(len(shapes), 16, form)
            for pts in shapes:
                self.assertEqual(len(pts), M.POINTS, form)
        bars = M.forms({"form": "bars", "heights": [0.1 * k for k in range(1, 17)]}, 16, 780, 600)
        self.assertEqual({len(p) for p in bars}, {M.POINTS})
        for pts in M.forms({"form": "grid"}, 16, 780, 600) + M.forms({"form": "column"}, 16, 780, 600):
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            self.assertLess(pts[0][0], cx)            # the first point is up and to the left
            self.assertLess(pts[0][1], cy)
            # clockwise on screen (y down): the shoelace sum is positive
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
            self.assertGreater(area, 0)
        for pts in M.forms({"form": "grid"}, 16, 780, 600) + M.forms({"form": "ring"}, 16, 780, 600):
            for x, y in pts:
                self.assertTrue(0 <= x <= 780 and 0 <= y <= 600, (x, y))

    def test_each_step_after_the_first_tweens_every_path_with_the_smooth_ease(self):
        html = self.ok(GOOD["morph"])
        body = self.body(html)
        self.assertEqual(len(re.findall(r'<path class="mo-p" id="sc-p\d+"', body)), 16)
        self.assertIn("window.smoothEase = function (t) { return t * t * t * (t * (6 * t - 15) + 10); };", html)
        # two later steps x 16 pieces: one d tween each, on the smooth ease, lagged a little piece by piece
        tw = re.findall(r"tl\.to\('#sc-p(\d+)', \{ attr: \{ d: '[^']+' \}, fill: '#[0-9a-fA-F]{6}', fillOpacity: [\d.]+, "
                        r"duration: ([\d.]+), ease: smoothEase \}, ([\d.]+)\);", html)
        self.assertEqual(len(tw), 32)
        starts = sorted({float(s) for _, _, s in tw})
        self.assertGreater(len(starts), 2)                 # lagged, not all at once
        self.assertLess(starts[-1] - starts[0], 0.6 + E3.lead(11) - E3.lead(8) + 0.01)

    def test_the_first_form_comes_in_and_each_label_hands_over_upward(self):
        html = self.ok(GOOD["morph"])
        t0 = E3.lead(5)
        self.assertRegex(html, r"tl\.fromTo\('#sc-p0', \{ opacity: 0, scale: 0\.6 \}")
        labs = re.findall(r'<div class="mo-label" id="sc-l(\d)"', html)
        self.assertEqual(labs, ["0", "1", "2"])
        # the old label lifts away and is gone before the next one rises in
        out = re.search(r"tl\.to\('#sc-l0', \{ opacity: 0, y: -30, duration: 0\.2, ease: 'power3\.in' \}, ([\d.]+)\);", html)
        self.assertIsNotNone(out)
        self.assertAlmostEqual(float(out.group(1)), E3.lead(8), places=2)      # whole until its next word (the beat still)
        self.assertIn("tl.fromTo('#sc-l1', { opacity: 0, y: 30 }", html)
        self.assertRegex(html, r"tl\.fromTo\('#sc-l1', [^;]*\}, %.3f\);" % (E3.lead(8) + 0.2))
        self.assertGreater(E3.lead(8), t0)

    def test_merge_puts_every_piece_on_one_circle(self):
        import scenes.morph as M
        shapes = M.forms({"form": "merge"}, 16, 780, 600)
        self.assertTrue(all(p == shapes[0] for p in shapes))

    def test_an_indicate_grows_and_lights_one_piece_then_lets_go(self):
        sc = dict(GOOD["morph"], indicate={"piece": 5, "at": W(13)})
        html = self.ok(sc)
        t = E3.lead(13)
        self.assertIn("tl.to('#sc-p5', { scale: 1.2, fill: '", html)
        self.assertRegex(html, r"tl\.to\('#sc-p5', \{ scale: 1, fill: '#[0-9a-fA-F]{6}', duration: 0\.4, ease: 'sine\.inOut' \}, %.3f\);" % (t + 0.4))
        self.fails(dict(GOOD["morph"], indicate={"piece": 99, "at": W(13)}), "indicate.piece is 0 to 15")


class Orbit(E3.Case):
    def test_bad_data_is_refused(self):
        sc = GOOD["orbit"]
        self.fails(dict(sc, nodes=[]), "1 to 4 nodes")
        self.fails(dict(sc, nodes=[{"text": "x" * 20, "at": W(5)}]), "node text: 1 to 14 characters")
        self.fails(dict(sc, center="x" * 30), "center: 1 to 20 characters")
        self.fails(dict(sc, shape="star"), "shape is circle, rounded or hex")
        self.fails(dict(sc, dive=dict(sc["dive"], into=5)), "dive.into is 0 to 1")
        # the new level's nodes come once the pull-out is over, so no word is ever read while the camera crosses scales
        self.fails(dict(sc, dive=dict(sc["dive"], nodes=[{"text": "Shell", "at": W(9)}])), "after the dive")

    def test_flat_shapes_with_no_outline_and_two_tone_facets(self):
        html = self.body(self.ok(GOOD["orbit"]))
        centre = re.search(r'<g class="ob-flat" id="sc-c0">(.*?)</g>', html).group(1)
        # shadow, highlight, base: the shape filled three times inside its own clip, never stroked; the shadow and the
        # highlight are the base under see-through ink and paper (palette colours only)
        fills = re.findall(r'<(?:circle|rect|path)[^>]*fill="([^"]+)"', centre)
        self.assertEqual(len(fills), 5)
        self.assertEqual(len([f for f in fills if f.startswith("rgba(")]), 2)
        self.assertNotIn("stroke", centre)
        self.assertIn('clip-path="url(#sc-k0)"', centre)
        for i in range(2):
            self.assertRegex(html, r'<g class="ob-flat ob-node" id="sc-n0-%d"' % i)

    def test_nodes_pop_on_their_words_with_a_ripple_never_an_overshoot(self):
        html = self.ok(GOOD["orbit"])
        t = E3.lead(5)
        self.assertIn("tl.fromTo('#sc-n0-0', { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out', "
                      "immediateRender: false }, %.3f);" % t, html)
        self.assertRegex(html, r"tl\.fromTo\('#sc-r0-0', \{ opacity: 0\.55, scale: 1 \}, \{ opacity: 0, scale: 2\.4")
        self.assertNotRegex(html, r"back\.|elastic|bounce")

    def test_the_dive_crosses_scales_into_the_node_and_pulls_out_of_the_next_centre(self):
        html = self.ok(GOOD["orbit"])
        t = E3.lead(8)
        self.assertIn("window.zoomIn = function (Z)", html)
        # labels and the centre's name go first; then the camera pushes into the node on a log zoom until it fills the box
        self.assertRegex(html, r"tl\.to\('#sc-w0 \.ob-pill, #sc-w0 \.ob-name', \{ opacity: 0, duration: 0\.2, ease: 'power3\.in' \}, %.3f\);" % t)
        m = re.search(r"tl\.to\('#sc-w0', \{ scale: ([\d.]+), x: (-?[\d.]+), y: (-?[\d.]+), duration: 0\.8, ease: zoomIn\(([\d.]+)\) \}, %.3f\);" % t, html)
        self.assertIsNotNone(m)
        self.assertGreater(float(m.group(1)), 8)
        self.assertEqual(m.group(1), m.group(4))
        # the next level comes out of a centre in the node's own colour, on a log zoom out
        self.assertRegex(html, r"tl\.fromTo\('#sc-w1', \{ opacity: 1, scale: ([\d.]+) \}, \{ scale: 1, duration: 1, ease: zoomOut\(\1\), immediateRender: false \}, %.3f\);" % (t + 0.8))
        self.assertIn("tl.set('#sc-w0', { opacity: 0 }, %.3f);" % (t + 0.8), html)

    def test_its_pictures_are_checked_before_each_beat(self):
        import json, os
        self.ok(GOOD["orbit"])
        with open(os.path.join(self.out, "moments.json"), encoding="utf-8") as f:
            m = json.load(f)
        sc = [s for s in m["scenes"] if s["id"] == "sc"][0]
        self.assertEqual(sc["beats"], sorted(round(E3.lead(i), 3) for i in (5, 6, 8, 14, 16)))

    def test_stars_and_glow_only_on_a_dark_ground(self):
        dark = self.body(self.ok(GOOD["orbit"], look="dark"))
        light = self.body(self.ok(GOOD["orbit"]))
        self.assertIn('class="ob-star"', dark)
        self.assertIn('class="ob-glow"', dark)
        self.assertNotIn('class="ob-star"', light)


class Clippings(E3.Case):
    def test_bad_data_is_refused(self):
        sc = GOOD["clippings"]
        self.fails(dict(sc, items=[]), "1 to 4 items")
        self.fails(dict(sc, items=[{"kind": "poster", "text": "x", "at": W(5)}]), "kind is clipping, print, label or note")
        self.fails(dict(sc, marks=[{"kind": "highlight", "item": 1, "line": 0, "at": W(10)}]), "a highlight marks a line of a clipping")
        self.fails(dict(sc, marks=[{"kind": "highlight", "item": 0, "line": 7, "at": W(7)}]), "line is 0 to 2")
        self.fails(dict(sc, marks=[{"kind": "scribble", "item": 0, "at": W(7)}]), "kind is highlight, circle or underline")
        self.fails(dict(sc, marks=[{"kind": "circle", "item": 2, "at": W(10)}]), "before its item lands")
        self.fails(dict(sc, items=[{"kind": "print", "src": "p.png", "at": W(5)}]), "a print needs its credit")

    def test_paper_on_any_ground_with_torn_edges(self):
        for look in E.LOOKS:
            body = self.body(self.ok(GOOD["clippings"], bg="ink", look=look))
            self.assertRegex(body, r'<div class="cl-item cl-clipping" id="sc-i0"')
            self.assertRegex(body, r'<div class="cl-paper" data-torn="1" style="[^"]*clip-path:polygon\([^)]+\)')
            self.assertRegex(body, r'<div class="cl-item cl-label" id="sc-i1"')
            self.assertRegex(body, r'<div class="cl-item cl-note" id="sc-i2"')

    def test_the_marks_move_on_twos_and_the_camera_layer_stays_smooth(self):
        html = self.ok(GOOD["clippings"])
        self.assertIn("window.onTwos = function (n, k)", html)
        # every item slides in tilted and settles on twos (12 steps a second), never an overshoot
        self.assertRegex(html, r"tl\.fromTo\('#sc-i0', \{ opacity: 0, x: 140, rotation: -?[\d.]+ \}, \{ opacity: 1, x: 0, rotation: -?[\d.]+, "
                               r"duration: 0\.58, ease: onTwos\(7, 4\), immediateRender: false \}, %.3f\);" % E3.lead(5))
        # the highlighter sweeps its line on twos, as a background under the words (so the words stay on top)
        self.assertRegex(html, r"tl\.fromTo\('#sc-h0', \{ backgroundSize: '0%% 100%%' \}, \{ backgroundSize: '100%% 100%%', duration: 0\.75, "
                               r"ease: 'steps\(9\)', immediateRender: false \}, %.3f\);" % E3.lead(7))
        # the red circle and the underline are drawn by hand, one stroke each, on twos
        for i, w in ((1, 10), (2, 14)):
            self.assertRegex(html, r"tl\.fromTo\('#sc-m%d', \{ strokeDashoffset: [\d.]+ \}, \{ strokeDashoffset: 0, duration: [\d.]+, "
                                   r"ease: 'steps\(\d+\)', immediateRender: false \}, %.3f\);" % (i, E3.lead(w)))
        self.assertNotRegex(html, r"back\.|elastic|bounce")

    def test_a_label_types_at_thirteen_characters_a_second(self):
        html = self.ok(GOOD["clippings"])
        n = len("2012 · Google")
        self.assertRegex(html, r"tl\.fromTo\('#sc-t1', \{ clipPath: 'inset\(0 100%% 0 0\)' \}, \{ clipPath: 'inset\(0 0%% 0 0\)', "
                               r"duration: %s, ease: 'steps\(%d\)', immediateRender: false \}" % (round(n / 13.0, 2), n), html)

    def test_red_strings_tie_each_item_to_the_last(self):
        body = self.body(self.ok(GOOD["clippings"]))
        self.assertEqual(len(re.findall(r'<path class="cl-string" id="sc-s\d"', body)), 2)
        self.assertEqual(len(re.findall(r'<circle class="cl-pin"', body)), 4)
        self.assertNotIn("cl-string", self.body(self.ok(dict(GOOD["clippings"], strings=False))))

    def test_a_print_is_a_creators_photo_with_a_border_tape_and_its_credit(self):
        sc = {"type": "clippings", "items": [{"kind": "print", "src": "p.png", "credit": "Photo: Ana", "label": "The lab", "halftone": True, "at": W(5)}]}
        body = self.body(self.ok(sc, files={"p.png": (400, 300)}))
        self.assertRegex(body, r'<div class="cl-item cl-print" id="sc-i0"')
        self.assertIn('class="cl-tape"', body)
        self.assertIn("Photo: Ana", body)
        self.assertIn("grayscale(1)", body)
        self.assertIn('class="cl-dots"', body)

    def test_the_marker_is_a_colour_of_every_look(self):
        for look in E.LOOKS:
            tok = E.load_tokens(look=look)
            self.assertRegex(E.theme(tok, "base")["marker"], r"^rgba\(")
        for pal in E.PALETTES:
            tok = E.load_tokens(look="paper", palette=pal)
            self.assertRegex(E.theme(tok, "base")["marker"], r"^rgba\(")


class Dive(E3.Case):
    """Kurzgesagt's scale crossing as a cut: the outgoing ground's accent opens from the middle of the scene area on a
    log zoom until it fills the frame on the cut, then shrinks away while the next scene pulls out to its size."""

    def test_it_is_a_transition_never_picked_on_its_own(self):
        import transitions as X
        self.assertIn("dive", X.KINDS)
        self.assertNotEqual(X.pick(3, "base", "blue", None), "dive")

    def test_the_colour_fills_the_frame_on_the_cut_and_the_next_scene_pulls_out(self):
        import transitions as X
        sc = dict(GOOD["morph"], transition="dive")
        html = self.ok(sc)
        t = E3.lead(4)
        self.assertIn(X.ZOOM_JS, html)
        self.assertRegex(html, r'<div class="tx-dive" id="txd1" style="[^"]*background:#[0-9a-fA-F]{6}')
        m = re.search(r"tl\.fromTo\('#txd1', \{ clipPath: 'circle\(24px at 540px 725px\)' \}, \{ clipPath: 'circle\((\d+)px at 540px 725px\)', "
                      r"duration: 0\.45, ease: zoomIn\(([\d.]+)\), immediateRender: false \}, %.3f\);" % (t - 0.45), html)
        self.assertIsNotNone(m)
        self.assertGreaterEqual(int(m.group(1)), int(math.hypot(540, 1920 - 725)))     # the farthest corner is covered
        self.assertRegex(html, r"tl\.to\('#txd1', \{ clipPath: 'circle\(0px at 540px 725px\)', duration: 0\.6, ease: 'power2\.in' \}, %.3f\);" % t)
        self.assertIn("tl.fromTo('#sc', { scale: 1.6, filter: 'blur(6px)' }, { scale: 1, filter: 'blur(0px)', duration: 0.6, ease: zoomOut(1.6), "
                      "immediateRender: false }, %.3f);" % t, html)


if __name__ == "__main__":
    unittest.main()
