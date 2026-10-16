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
        lead = {"type": "title", "id": "lead", "bg": "black", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": "black", "in": "word:4", "out": D}, **scene)
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
            ctx = Ctx(sc, 1.9, D, words, TOK, stub_vendor(scratch(self)), scratch(self), "black")
            mod = REGISTRY[t]
            mod.render(sc, ctx, (150, 600, 780))
            self.assertTrue(ctx.ambient_lines, t)
            self.assertTrue(all(l.startswith("tl.") for l in ctx.ambient_lines), t)

    def test_the_structure_shows_dimmed_until_each_piece_is_said(self):
        # the stage is never bare while a build waits for its first word: every piece is a dim ghost from the scene's in
        ghosts = {"flow": r"#sc-n\d", "stack": r"#sc-s\d", "cards": r"#sc-c\d", "compare": r"#sc-[lr]\d", "hub": r"#sc-n\d"}
        t_in = 0.5 + 4 * 0.4 - E.LEAD
        for t, sel in ghosts.items():
            r, html = self.build(GOOD[t])
            self.assertEqual(r.returncode, 0, r.stdout)
            dim = re.findall(r"tl\.to\('(%s)', \{ opacity: 0\.18,[^}]* duration: [\d.]+, ease: '[\w.]+' \}, ([\d.]+)\);" % sel, html)
            self.assertEqual(len(dim), COUNTS[t], t)
            self.assertTrue(all(abs(float(x) - t_in) < 1e-3 for _, x in dim), t)
        r, html = self.build(GOOD["timeline"])                     # the rail and its empty dots come in with the scene
        self.assertIn("tl.fromTo('#sc .tm-rail, #sc .tm-dot', { opacity: 0, y: -16 }", html)
        self.assertNotIn("WARN sc: nothing shows", r.stdout)

    def test_heights_are_fixed(self):
        for t, sc in GOOD.items():
            mod = REGISTRY[t]
            self.assertEqual(mod.height(sc, 950), mod.height(sc, 780), t)
            self.assertLessEqual(mod.height(sc, 780), E.SCENE["bottom"] - E.SCENE["top"], t)

    def test_light_background_builds(self):
        for t, sc in GOOD.items():
            r, _ = self.build(dict(sc, bg="light"))
            self.assertEqual(r.returncode, 0, "%s: %s" % (t, r.stdout))


if __name__ == "__main__":
    unittest.main()
