"""The video and grade scenes (group C): grade-slider, eyedropper-grade, film-look, playing-grid, video-card, reel-feed.
Each refuses bad data with a reason, lands its items on their words, composes on all four grounds with and without the
creator's picture, and does its one thing on its word: a knob reaches its value, a colour lands in the palette, the
grain steps deterministically, a tile lifts, play turns to pause, the feed swipes."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_assets import png
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY

W = lambda i: "word:%d" % i
T = lambda i: "%.3f" % (t_word(i) - E.LEAD)       # an item's time on the page: its word minus the lead

GOOD = {
    "grade-slider": {"type": "grade-slider", "sliders": [{"kind": "contrast", "from": 0, "to": 40, "at": W(6)},
                                                         {"kind": "temperature", "label": "Warmth", "from": -20, "to": 60, "at": W(9)}]},
    "eyedropper-grade": {"type": "eyedropper-grade", "picks": [{"color": "peach", "x": 0.3, "y": 0.3, "at": W(6)},
                                                               {"color": "teal", "label": "Shadows", "x": 0.7, "y": 0.8, "at": W(10)}]},
    "film-look": {"type": "film-look", "at": W(7), "title": "The film look"},
    "playing-grid": {"type": "playing-grid", "tiles": [{"label": "Vlog", "at": W(5)}, {"at": W(6)}, {"at": W(7)}, {"at": W(8)},
                                                       {"label": "Review", "at": W(9)}, {"at": W(10)}],
                     "pick": {"tile": 4, "at": W(13)}},
    "video-card": {"type": "video-card", "title": "Colour grading in ten minutes", "channel": "Studio Notes", "meta": "1.2M views",
                   "duration": "10:24", "start": "1:05", "play": {"at": W(7)}},
    "reel-feed": {"type": "reel-feed", "reels": [
        {"user": "@studio.notes", "caption": "Three grades every film uses", "likes": 12400, "comments": 318, "shares": 1200},
        {"user": "@colourlab", "caption": "Teal and orange, explained", "likes": 98000, "comments": 2100, "shares": 5400, "at": W(9)},
        {"user": "@grain", "caption": "Why grain looks expensive", "likes": 431000, "comments": 9800, "shares": 12000, "at": W(14)}]},
}
ANCHORED = {"grade-slider": 2, "eyedropper-grade": 2, "film-look": 1, "playing-grid": 7, "video-card": 1, "reel-feed": 2}
BAD = {   # a broken copy of each, and the words its refusal must say
    "grade-slider": [({"sliders": []}, "1 to 3 sliders"),
                     ({"sliders": [{"kind": "glow", "from": 0, "to": 10, "at": W(6)}]}, "kind is one of"),
                     ({"sliders": [{"kind": "contrast", "from": 0, "to": 140, "at": W(6)}]}, "-100 to 100"),
                     ({"sliders": [{"kind": "contrast", "from": 20, "to": 20, "at": W(6)}]}, "nothing moves")],
    "eyedropper-grade": [({"picks": [{"color": "crimson", "x": 0.3, "y": 0.3, "at": W(6)}]}, "Catppuccin Latte colour name"),
                         ({"picks": [{"color": "peach", "x": 1.4, "y": 0.3, "at": W(6)}]}, "fraction of the picture"),
                         ({"picks": [{"color": "peach", "x": 0.2, "y": 0.3}]}, "has no at")],
    "film-look": [({"at": None}, "missing 'at'"), ({"before": "a much too long label"}, "short words")],
    "playing-grid": [({"tiles": [{"at": W(5)}] * 3}, "4 to 9 tiles"), ({"cols": 4}, "cols is 2 or 3"),
                     ({"pick": {"tile": 9, "at": W(13)}}, "pick needs tile"), ({"pick": {"tile": 1, "at": W(8)}}, "before every tile")],
    "video-card": [({"duration": "ten minutes"}, "duration is m:ss"), ({"start": "11:00"}, "before the duration"),
                   ({"play": {}}, "play needs at")],
    "reel-feed": [({"reels": GOOD["reel-feed"]["reels"][:1]}, "2 or 3 reels"),
                  ({"reels": [GOOD["reel-feed"]["reels"][0], dict(GOOD["reel-feed"]["reels"][1], at=None)]}, "has no at"),
                  ({"reels": [dict(GOOD["reel-feed"]["reels"][0], caption="A caption that runs on and on far past the two lines the phone has room for"),
                              GOOD["reel-feed"]["reels"][1]]}, "more than two lines")],
}


class SceneC(unittest.TestCase):
    def build(self, scene, bg="mantle", pic=None):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        if pic:
            png(os.path.join(d, pic), 320, 200)
        lead = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc], "sound": {"music": "none", "sfx": False}})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else ""), out

    def ok(self, scene, **kw):
        r, html, out = self.build(scene, **kw)
        self.assertEqual(r.returncode, 0, "%s: %s" % (scene["type"], r.stdout + r.stderr))
        return html, out

    def body(self, html):
        return html.split('id="host-sc"')[1].split('id="captions"')[0]

    # ---- every type ---------------------------------------------------------------------------------------------------
    def test_every_type_is_discovered(self):
        for t in GOOD:
            self.assertIn(t, REGISTRY)

    def test_bad_data_fails_with_a_reason(self):
        for t, cases in BAD.items():
            for change, words in cases:
                sc = dict(copy.deepcopy(GOOD[t]), **change)
                sc = {k: v for k, v in sc.items() if v is not None}
                r, _, _ = self.build(sc)
                self.assertNotEqual(r.returncode, 0, "%s %s" % (t, change))
                self.assertIn("E3 FAIL: sc:", r.stdout, t)
                self.assertIn(words, r.stdout, "%s: %s" % (t, r.stdout))

    def test_items_carry_data_at_on_their_words(self):
        for t, sc in GOOD.items():
            html, _ = self.ok(sc)
            found = re.findall(r'data-at="([\d.]+)" data-anchor="word(\d+)"', self.body(html))
            self.assertEqual(len(found), ANCHORED[t], t)
            for at, w in found:
                self.assertEqual(at, T(int(w)), t)          # each item's time is its own word, less the lead

    def test_composes_on_every_ground_with_and_without_a_picture(self):
        for t, sc in GOOD.items():
            for bg in ("mantle", "base", "blue", "ink"):
                html, _ = self.ok(sc, bg=bg)
                self.assertIn('class="vg-ill"', html, (t, bg))          # the built-in picture
            html, out = self.ok(dict(sc, src="shots/pic.png"), pic="shots/pic.png")
            self.assertIn('src="assets/sc-pic.png"', html, t)
            self.assertTrue(os.path.exists(os.path.join(out, "assets", "sc-pic.png")), t)
            self.assertNotIn('class="vg-ill"', html, t)
            r, _, _ = self.build(dict(sc, src="shots/missing.png"))
            self.assertIn("shots/missing.png", r.stdout, t)
            r, _, _ = self.build(dict(sc, src="notes.txt"))
            self.assertIn("PNG or JPG", r.stdout, t)

    def test_motion_is_deterministic_and_never_overshoots(self):
        for t, sc in GOOD.items():
            html, _ = self.ok(sc)
            script = self.body(html) + html.split("// sc (")[1]
            for banned in ("Math.random", "Date.now", "repeat:", "yoyo", "back.", "elastic", "bounce", "infinite"):
                self.assertNotIn(banned, script, (t, banned))
            again, _ = self.ok(sc)
            self.assertEqual(html.split("<script>")[-1], again.split("<script>")[-1], t)   # the same timeline, line for line

    def test_furniture_numbers_need_no_source_but_a_claim_does(self):
        for t, sc in GOOD.items():
            self.assertFalse(sc.get("source"))
            self.ok(sc)                                      # slider values, points, counts, timecodes: furniture
        r, _, _ = self.build(dict(GOOD["video-card"], title="3 ways to grade"))
        self.assertIn("needs a source", r.stdout)
        r, _, _ = self.build(dict(GOOD["grade-slider"], sliders=[dict(GOOD["grade-slider"]["sliders"][0], label="Contrast 2")]))
        self.assertIn("needs a source", r.stdout)

    def test_heights_fit_the_scene_area(self):
        for t, sc in GOOD.items():
            self.assertLessEqual(REGISTRY[t].height(sc, 780), 600, t)

    # ---- each one's own moment ------------------------------------------------------------------------------------------
    def test_a_knob_reaches_its_value_on_its_word_and_the_grade_follows(self):
        html, _ = self.ok(GOOD["grade-slider"])
        self.assertRegex(html, r"tl\.fromTo\('#sc-k0', \{ left: '50%%' \}, \{ left: '70%%', duration: [\d.]+, ease: '[\w.]+', "
                               r"immediateRender: false \}, %s\);" % T(6))
        self.assertRegex(html, r"tl\.fromTo\('#sc-k1', \{ left: '40%%' \}, \{ left: '80%%',[^}]*\}, %s\);" % T(9))
        self.assertRegex(html, r"tl\.fromTo\('#sc-f0', \{ filter: 'contrast\(1\)' \}, \{ filter: 'contrast\(1\.4\)',[^}]*\}, %s\);" % T(6))
        self.assertRegex(html, r"tl\.fromTo\('#sc-w1', \{ opacity: 0 \}, \{ opacity: 0\.51,[^}]*\}, %s\);" % T(9))   # warm comes in
        self.assertRegex(html, r"tl\.fromTo\('#sc-c1', \{ opacity: 0\.17 \}, \{ opacity: 0,[^}]*\}, %s\);" % T(9))   # cool goes
        self.assertIn('id="sc-v1" style="width:', html)
        self.assertRegex(html, r'id="sc-v1"[^>]*>-20<')

    def test_a_picked_colour_lands_in_the_palette_and_tints_the_picture(self):
        html, _ = self.ok(GOOD["eyedropper-grade"])
        tok = E.load_tokens()["palette"]
        self.assertIn(">%s<" % tok["peach"].upper(), html)          # the swatch's hex code
        self.assertIn(">Shadows<", html)
        self.assertRegex(html, r"tl\.set\('#sc-lp', \{ x: [\d.]+, y: [\d.]+, backgroundColor: '%s' \}, %s\);" % (tok["teal"], T(10)))
        self.assertRegex(html, r"tl\.fromTo\('#sc-s1', \{ opacity: 0\.4 \}")                 # its slot waits, then fills
        self.assertRegex(html, r"tl\.fromTo\('#sc-t1', \{ opacity: 0 \}, \{ opacity: 0\.85,")   # the picture leans to it
        sc = copy.deepcopy(GOOD["eyedropper-grade"])
        sc["picks"][1]["at"] = W(6)
        r, _, _ = self.build(sc)
        self.assertIn("at least 0.4 s apart", r.stdout)

    def test_three_picks_stack_their_slots(self):
        sc = copy.deepcopy(GOOD["eyedropper-grade"])
        sc["picks"].append({"color": "mauve", "x": 0.5, "y": 0.5, "at": W(14)})
        from scenes import eyedropper_grade as ed
        self.assertGreater(ed.height(sc, 780), ed.height(GOOD["eyedropper-grade"], 780))
        html, _ = self.ok(sc)
        self.assertEqual(len(re.findall(r'class="ed-slot st"', html)), 3)

    def test_the_grain_steps_on_the_timeline_the_same_every_render(self):
        a, _ = self.ok(GOOD["film-look"])
        b, _ = self.ok(GOOD["film-look"])
        seeds = lambda h: re.findall(r"tl\.set\('#sc-turb', \{ attr: \{ seed: (\d+) \} \}, ([\d.]+)\);", h)
        self.assertGreater(len(seeds(a)), 50)
        self.assertEqual(seeds(a), seeds(b))
        self.assertGreater(len({s for s, _ in seeds(a)}), 40)                # it really changes
        times = [float(x) for _, x in seeds(a)]
        self.assertGreaterEqual(min(times), float(T(7)))                     # it starts on the word
        self.assertRegex(a, r"tl\.fromTo\('#sc-bt, #sc-bb', \{ scaleY: 0 \}, \{ scaleY: 1,[^}]*\}, %s\);" % T(7))
        self.assertRegex(a, r"id=\"sc-a\" data-at=\"%s\"" % T(7))           # the chip's AFTER
        self.assertIn(">BEFORE<", a)

    def test_the_picked_tile_lifts_and_the_others_dim(self):
        html, _ = self.ok(GOOD["playing-grid"])
        self.assertRegex(html, r"tl\.fromTo\('#sc-t4', \{ scale: 1 \}, \{ scale: 1\.06,[^}]*\}, %s\);" % T(13))
        dim = re.search(r"tl\.fromTo\('([^']+)', \{ opacity: 1 \}, \{ opacity: 0\.38,[^}]*\}, %s\);" % T(13), html)
        self.assertTrue(dim)
        self.assertEqual(sorted(dim.group(1).split(", ")), ["#sc-t%d" % i for i in (0, 1, 2, 3, 5)])
        for i in range(6):                                                    # each waits as an empty frame
            self.assertIn("tl.set('#sc-t%d .gt', { opacity: 0 }, 0);" % i, html)
            self.assertRegex(html, r"tl\.fromTo\('#sc-f%d', \{ width: '\d+%%' \}" % i)   # and its bar runs once it lands
        from scenes import playing_grid as pg
        boxes = pg.layout(GOOD["playing-grid"], 600)
        for (x, y, w, h) in boxes:                                            # the lifted tile stays in the box
            self.assertGreaterEqual(x - w * (pg.LIFT - 1) / 2, 0)
            self.assertLessEqual(x + w + w * (pg.LIFT - 1) / 2, 600)

    def test_play_turns_to_pause_on_its_word_and_the_clock_runs(self):
        html, _ = self.ok(GOOD["video-card"])
        self.assertRegex(html, r'id="sc-btn" data-at="%s"' % T(7))
        self.assertRegex(html, r"tl\.fromTo\('#sc-pl', \{ opacity: 1, scale: 1 \}, \{ opacity: 0,[^}]*\}, %s\);" % T(7))
        self.assertRegex(html, r"tl\.fromTo\('#sc-pa', \{ opacity: 0, scale: 0\.6 \}, \{ opacity: 1,")
        self.assertIn(">1:05</b>&nbsp;/ 10:24<", html)
        tick = re.search(r"tl\.fromTo\(\{ v: 65 \}, \{ v: 65 \}, \{ v: ([\d.]+), duration: ([\d.]+), ease: 'none'", html)
        self.assertTrue(tick)
        self.assertAlmostEqual(float(tick.group(1)) - 65, float(tick.group(2)), places=2)   # it plays in real time
        from scenes import _vg
        self.assertEqual(_vg.clock(3760), "1:02:40")
        self.assertEqual(_vg.parse_clock("1:02:40"), 3760)

    def test_the_feed_swipes_to_each_reel_on_its_word(self):
        from scenes import reel_feed as rf
        html, _ = self.ok(GOOD["reel-feed"])
        for i, w in ((1, 9), (2, 14)):
            self.assertRegex(html, r"tl\.fromTo\('#sc-strip', \{ y: %d \}, \{ y: %d, duration: [\d.]+, ease: 'expo\.out', "
                                   r"immediateRender: false \}, %s\);" % (-(i - 1) * rf.SH, -i * rf.SH, T(w)))
            self.assertRegex(html, r'id="sc-r%d" data-at="%s"' % (i, T(w)))
        self.assertIn(">12.4K<", html)
        self.assertIn(">1,200<", html)
        self.assertIn("tl.fromTo({ v: 12400 }, { v: 12400 }, { v: %d," % rf.bump(12400), html)   # the likes tick up
        sc = copy.deepcopy(GOOD["reel-feed"])
        sc["reels"][2]["at"] = W(10)
        r, _, _ = self.build(sc)
        self.assertIn("give each reel at least", r.stdout)


if __name__ == "__main__":
    unittest.main()
