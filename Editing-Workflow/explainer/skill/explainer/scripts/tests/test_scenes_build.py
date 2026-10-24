"""The build-up scenes: flow, stack, compare, timeline, cards, hub. Each one grows on the voice's words (every item has
data-at on its word), keeps one idle motion going while it holds (ctx.ambient), has a fixed height, and refuses a label
too wide for its column."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY, Ctx

TOK = E.load_tokens()
W = lambda i: "word:%d" % i

GOOD = {
    "flow": {"type": "flow", "nodes": [{"label": "Retrieve", "icon": "book", "at": W(6)}, {"label": "Augment", "at": W(9)},
                                       {"label": "Generate", "icon": "clock", "at": W(12)}]},
    "stack": {"type": "stack", "items": [{"label": "Time value", "at": W(6)}, {"label": "Risk and return", "at": W(8)},
                                         {"label": "Cost of capital", "at": W(10)}, {"label": "Budgeting", "at": W(12)}]},
    "compare": {"type": "compare", "left": {"title": "Memory", "items": [{"text": "Guesses", "at": W(6)}, {"text": "Out of date", "at": W(8)}]},
                "right": {"title": "RAG", "items": [{"text": "Looks it up", "at": W(10)}, {"text": "Current", "at": W(12)}]},
                "winner": {"side": "right", "at": W(14)}},
    "timeline": {"type": "timeline", "steps": [{"label": "Week 1", "sub": "Excel basics", "at": W(6)}, {"label": "Week 2", "at": W(9)},
                                               {"label": "Week 3", "sub": "Your first model", "at": W(12)}], "source": "s1"},
    "cards": {"type": "cards", "cards": [{"title": "Corporate Finance", "sub": "Coursera", "at": W(6)},
                                         {"title": "Valuation", "at": W(9)}, {"title": "Financial Engineering", "at": W(12)}],
              "focus": {"card": 1, "at": W(15)}},
    "hub": {"type": "hub", "center": "RAG", "items": [{"label": "Search", "at": W(6)}, {"label": "Rank", "at": W(8)},
                                                      {"label": "Prompt", "at": W(10)}, {"label": "Answer", "at": W(12)}]},
}
COUNTS = {"flow": 3, "stack": 4, "compare": 4, "timeline": 3, "cards": 3, "hub": 4}


def items_of(sc):
    """Every list of word-anchored entries in a scene, in order."""
    for key in ("nodes", "items", "steps", "cards"):
        if key in sc:
            return sc[key]
    return sc["left"]["items"] + sc["right"]["items"]


class Build(unittest.TestCase):
    def build(self, scene):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": "mantle", "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc]})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def test_every_type_is_registered(self):
        for t in GOOD:
            self.assertIn(t, REGISTRY)

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            r, html = self.build(sc)
            self.assertEqual(r.returncode, 0, "%s: %s" % (t, r.stdout + r.stderr))
            body = html.split('id="host-sc"')[1].split('id="captions"')[0]
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), COUNTS[t], t)

    def test_an_item_outside_the_scene_fails(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            items_of(bad)[0]["at"] = W(2)
            r, _ = self.build(bad)
            self.assertNotEqual(r.returncode, 0, t)
            self.assertIn("outside the scene", r.stdout, t)

    def test_a_label_too_wide_fails(self):
        long = "Supercalifragilisticexpialidocious-ness-extraordinaire"   # wider than even the 950 px column
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            it = items_of(bad)[0]
            it["label" if "label" in it else ("text" if "text" in it else "title")] = long
            r, _ = self.build(bad)
            self.assertNotEqual(r.returncode, 0, t)
            self.assertIn("wider than the", r.stdout, t)

    def test_counts_are_checked(self):
        too_few = {"flow": {"nodes": GOOD["flow"]["nodes"][:1]}, "stack": {"items": GOOD["stack"]["items"][:1]},
                   "timeline": {"steps": GOOD["timeline"]["steps"][:1]}, "cards": {"cards": []},
                   "hub": {"items": GOOD["hub"]["items"][:1]},
                   "compare": {"left": {"title": "A", "items": [{"text": "x", "at": W(6)}] * 5}}}
        for t, change in too_few.items():
            r, _ = self.build(dict(GOOD[t], **change))
            self.assertNotEqual(r.returncode, 0, t)

    def test_each_scene_keeps_moving_while_it_holds(self):
        words = words30()
        for t, sc in GOOD.items():
            sc = dict({"id": "sc", "in": "word:4", "out": D}, **copy.deepcopy(sc))
            ctx = Ctx(sc, 1.9, D, words, TOK, stub_vendor(scratch(self)), scratch(self), "mantle")
            mod = REGISTRY[t]
            mod.render(sc, ctx, (150, 600, 780))
            self.assertTrue(ctx.ambient_lines, t)
            self.assertTrue(all(l.startswith("tl.") for l in ctx.ambient_lines), t)

    def test_each_piece_waits_as_an_empty_slot_until_it_is_said(self):
        # the stage is never bare while a build waits for its words, but nothing on it reads as faint text: every piece
        # is an empty outline (its words hidden) from the scene's in, and its words arrive on their own word
        slots = {"flow": r"#sc-n\d", "stack": r"#sc-s\d", "cards": r"#sc-c\d", "compare": r"#sc-[lr]\d", "hub": r"#sc-n\d"}
        t_in = 0.5 + 4 * 0.4 - E.LEAD
        for t, sel in slots.items():
            r, html = self.build(GOOD[t])
            self.assertEqual(r.returncode, 0, r.stdout)
            dim = re.findall(r"tl\.to\('(%s)', \{ opacity: 0\.4,[^}]* duration: [\d.]+, ease: '[\w.]+' \}, ([\d.]+)\);" % sel, html)
            self.assertEqual(len(dim), COUNTS[t], t)
            self.assertTrue(all(abs(float(x) - t_in) < 1e-3 for _, x in dim), t)
            for piece, _ in dim:
                self.assertIn("tl.set('%s .gt', { opacity: 0 }, 0);" % piece, html, t)
                self.assertRegex(html, r"tl\.fromTo\('%s \.gt', \{ opacity: 0 \}, \{ opacity: 1," % re.escape(piece), t)
                self.assertRegex(html, r'id="%s"[^>]*>.*?class="[^"]*\bgt\b' % piece[1:], t)
            self.assertNotIn("opacity: 0.18", html, t)
        r, html = self.build(GOOD["timeline"])                     # the rail and its empty dots come in with the scene
        self.assertIn("tl.fromTo('#sc .tm-rail, #sc .tm-dot', { opacity: 0, y: -16 }", html)
        self.assertNotIn("WARN sc: nothing shows", r.stdout)

    def test_a_long_flow_travels_from_step_to_step(self):
        # five or six steps don't fit the area at a readable size: the column runs past a window and the camera moves
        # to each step as it arrives (a new framing on every step, so E4 lets the scene hold longer)
        from scenes import flow
        sc = {"type": "flow", "nodes": [{"label": "Step " + "ABCDEF"[i], "at": W(5 + 2 * i)} for i in range(6)]}
        self.assertEqual(flow.validate(sc), [])
        self.assertTrue(flow.travels(sc))
        self.assertFalse(flow.travels(GOOD["flow"]))
        self.assertLess(flow.height(sc, 780), 6 * flow.NODE + 5 * flow.LINK)
        self.assertIn("2 to 6", " ".join(flow.validate(dict(sc, nodes=sc["nodes"] + [{"label": "G", "at": W(17)}]))))
        r, html = self.build(sc)
        self.assertEqual(r.returncode, 0, r.stdout)
        moves = re.findall(r"tl\.to\('#sc-mv', \{ y: (-?[\d.]+), duration: [\d.]+, ease: 'expo\.out' \}, ([\d.]+)\);", html)
        self.assertGreaterEqual(len(moves), 3)
        ys = [float(y) for y, _ in moves]
        self.assertEqual(ys, sorted(ys, reverse=True))            # always further down the column
        self.assertIn('"travels": true', read(os.path.join(os.path.dirname(re.search(r"(/tmp/[^\s\"]+)/public/index.html", r.stdout).group(1) + "/public/index.html"), "moments.json")))

    def test_heights_are_fixed(self):
        for t, sc in GOOD.items():
            mod = REGISTRY[t]
            self.assertEqual(mod.height(sc, 950), mod.height(sc, 780), t)
            self.assertLessEqual(mod.height(sc, 780), E.SCENE["bottom"] - E.SCENE["top"], t)

    def test_light_background_builds(self):
        for t, sc in GOOD.items():
            r, _ = self.build(dict(sc, bg="base"))
            self.assertEqual(r.returncode, 0, "%s: %s" % (t, r.stdout))

    def test_a_cards_title_waits_for_the_last_one_to_leave(self):
        r, html = self.build(GOOD["cards"])
        self.assertEqual(r.returncode, 0, r.stdout)
        out = re.search(r"tl\.to\('#sc-t0, #sc-u0', \{ opacity: 0, y: -16, duration: ([\d.]+), ease: '[\w.]+' \}, ([\d.]+)\);", html)
        inn = re.search(r"tl\.fromTo\('#sc-t1', \{ opacity: 0, y: 20 \}, \{[^}]*\}, ([\d.]+)\);", html)
        self.assertGreaterEqual(float(inn.group(1)), float(out.group(2)) + float(out.group(1)) - 1e-6)   # no double exposure

    def test_the_winner_badge_sits_inside_its_head(self):
        from scenes import compare
        self.assertNotRegex(compare.CSS, r"\.cp-win \{[^}]*(right|top):-")
        sc = copy.deepcopy(GOOD["compare"])
        plain = compare.min_width(dict(sc, winner=None))
        self.assertGreaterEqual(compare.min_width(sc), plain)
        self.assertGreaterEqual(compare.min_width(sc), 2 * (int(E.text_width("RAG", compare.T_SIZE)) + 2 * compare.BADGE_ROOM))

    def test_the_address_bar_fits(self):
        from scenes import browser
        short = browser.min_width({"title": "X", "domain": "a.org"})
        long = browser.min_width({"title": "X", "domain": "notes / team-handbook / section-four"})
        self.assertGreater(long, short)
        self.assertGreaterEqual(long, browser.bar_width("notes / team-handbook / section-four"))


class Hub(unittest.TestCase):
    """The hub's geometry is computed, not drawn by eye: every node clears the middle disc and every other node, and
    everything sits inside the box, for two to six labels short or long (gate E5 checks the drawn page too)."""
    SETS = [["In", "Out"], ["Search", "Rank", "Answer"], ["Retrieval", "Augmented", "Generation"],
            ["Budgeting", "Risk", "Valuation", "Markets", "Data", "Models"], ["Time value of money", "Cost of capital"],
            ["Search", "Rank", "Prompt", "Answer"], ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]]

    def test_nodes_clear_the_disc_each_other_and_the_box(self):
        from scenes import hub
        for labels in self.SETS:
            sc = {"center": "RAG", "items": [{"label": l, "at": W(6)} for l in labels]}
            width = max(hub.min_width(sc), 600)
            h = hub.height(sc, width)
            nodes, cx, cy = hub.layout(sc, width)
            for i, (x, y, w, hh) in enumerate(nodes):
                self.assertGreaterEqual(x, 0, labels)
                self.assertGreaterEqual(y, 0, labels)
                self.assertLessEqual(x + w, width + 0.01, labels)
                self.assertLessEqual(y + hh, h + 0.01, labels)
                dx = max(abs(cx - (x + w / 2.0)) - w / 2.0, 0)
                dy = max(abs(cy - (y + hh / 2.0)) - hh / 2.0, 0)
                self.assertGreaterEqual((dx * dx + dy * dy) ** 0.5, hub.DISC / 2.0 + hub.GAP - 0.01, (labels, i))
                for j, (x2, y2, w2, h2) in enumerate(nodes[:i]):
                    apart = max(x2 - (x + w), x - (x2 + w2), y2 - (y + hh), y - (y2 + h2))
                    self.assertGreaterEqual(apart, hub.GAP - 0.01, (labels, i, j))

    def test_three_long_labels_fit_the_narrow_column(self):
        # a portrait frame: the ring may be taller than wide, so three long labels fit 780 px (shrunk to 0.8 at most,
        # which keeps the 44 px labels over the 28 px floor)
        from scenes import hub
        sc = {"center": "RAG", "items": [{"label": l, "at": W(6)} for l in ("Retrieval", "Augmented", "Generation")]}
        self.assertLessEqual(hub.min_width(sc) * 0.8, 780)
        self.assertLessEqual(hub.height(sc, 780) * 0.8, E.SCENE["bottom"] - E.SCENE["top"] - 2 * E.IDLE_ROOM)

    def test_labels_are_large_and_nothing_spins(self):
        from scenes import hub
        self.assertGreaterEqual(hub.N_SIZE, 44)
        sc = dict(GOOD["hub"], id="sc", **{"in": "word:4", "out": D})
        ctx = Ctx(sc, 1.9, D, words30(), TOK, stub_vendor(scratch(self)), scratch(self), "mantle")
        html, js = hub.render(sc, ctx, (150, 600, 700))
        self.assertNotRegex("\n".join(js + ctx.ambient_lines), r"rotation")


if __name__ == "__main__":
    unittest.main()
