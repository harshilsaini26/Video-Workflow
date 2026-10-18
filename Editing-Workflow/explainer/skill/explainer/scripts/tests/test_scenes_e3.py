"""The editorial scenes (group E3): crossed-list, price-sticker, line-art. Rows in the hero face crossed out on their
words, a price sticker that slams in and breathes, a big line drawing drawn on with a serif caption under it. Each one
refuses bad data with a reason, lands its items on their words, keeps moving while it holds, and composes clean (E5) on
every ground of both looks."""
import copy, importlib.util, json, os, re, unittest
from .helpers import SCRIPTS, read, run, scratch, write
from .test_assets import png
from .test_layout import have_browser
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY, Ctx

TOK = E.load_tokens()
W = lambda i: "word:%d" % i
ICONS = ("book", "clock", "calculator", "send", "file-text")
TYPES = ("crossed-list", "price-sticker", "line-art")
STROKE_SVG = ('<?xml version="1.0" encoding="UTF-8"?>\n<!-- drawn by hand -->\n<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" '
              'viewBox="0 0 100 50" fill="none" stroke="#123456" stroke-width="3" stroke-linecap="round"><title>cable</title>'
              '<g transform="translate(2 2)"><path d="M0 0 L90 40"/><circle cx="50" cy="20" r="10" style="stroke-width:2"/></g>'
              '<polyline points="0,40 20,30 40,40"/></svg>')
FILLED_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" fill="none" stroke="black"><path d="M0 0 L9 9"/>'
              '<rect x="1" y="1" width="4" height="4" fill="#ff0000"/></svg>')
DEFAULT_FILL_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" stroke="black"><circle cx="5" cy="5" r="4"/></svg>'
STYLE_FILL_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" fill="none" stroke="black">'
                  '<ellipse cx="5" cy="5" rx="4" ry="2" style="fill: currentColor"/></svg>')
TEXT_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" fill="none" stroke="black"><path d="M0 0 L9 9"/>'
            '<text x="1" y="5">hi</text></svg>')

GOOD = {
    "crossed-list": {"type": "crossed-list", "prefix": "NO", "items": [
        {"text": "CHARGING CASE", "at": W(6), "strike": W(8)}, {"text": "BATTERY", "at": W(10)},
        {"text": "WIRES", "at": W(12), "strike": W(14)}]},
    "price-sticker": {"type": "price-sticker", "price": "$99", "label": "FOR THE PAIR", "at": W(6), "source": "s1"},
    "line-art": {"type": "line-art", "icon": "book", "caption": "a library in your pocket", "at": W(6), "strike": W(10)},
}
ANCHORED = {"crossed-list": 5, "price-sticker": 1, "line-art": 2}     # rows and strikes; the sticker; the drawing and its strike


def lead(i):
    return round(t_word(i) - E.LEAD, 3)


def cases_e3():
    spec = importlib.util.spec_from_file_location("cases_e3", os.path.join(SCRIPTS, "dev", "cases_e3.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Case(unittest.TestCase):
    def build(self, scene, bg="mantle", look=None, files=None, start=4):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        for name, body in (files or {}).items():
            if isinstance(body, tuple):
                png(os.path.join(d, name), *body)
            else:
                write(os.path.join(d, name), body)
        first = {"type": "title", "id": "lead", "bg": bg, "in": "word:0", "out": W(start), "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": W(start), "out": D}, **scene)
        board = dict({"id": "t", "scenes": [first, sc], "sound": {"music": "none", "sfx": False}}, **({"look": look} if look else {}))
        sp = write(os.path.join(d, "storyboard.json"), board)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d, icons=ICONS))
        self.out = out
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def ok(self, scene, **kw):
        r, html = self.build(scene, **kw)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html

    def fails(self, scene, *texts, **kw):
        r, _ = self.build(scene, **kw)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        for text in texts:
            self.assertIn(text, r.stdout + r.stderr)

    def body(self, html):
        return html.split('id="host-sc"')[1].split('id="captions"')[0]

    def ambient(self, scene, files=None):
        """The scene rendered on its own: (its ctx, its timeline lines)."""
        d = scratch(self)
        for name, body in (files or {}).items():
            write(os.path.join(d, name), body)
        sc = dict({"id": "sc", "in": "word:4", "out": D}, **copy.deepcopy(scene))
        ctx = Ctx(sc, lead(4), D, words30(), TOK, stub_vendor(d, icons=ICONS), scratch(self), "mantle", spec_dir=d)
        _, js = REGISTRY[sc["type"]].render(sc, ctx, (150, 400, 780))
        return ctx, js


def spans(lines):
    out = []
    for l in lines:
        m = re.match(r"tl\.(?:to|fromTo)\(.*, ([\d.]+)\);$", l)
        if m:
            d = re.findall(r"duration: ([\d.]+)", l)
            out.append((float(m.group(1)), float(m.group(1)) + float(d[-1] if d else 0)))
    return sorted(out)


class Shared(Case):
    def test_every_type_is_found(self):
        for t in TYPES:
            self.assertIn(t, REGISTRY)

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            body = self.body(self.ok(sc))
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), ANCHORED[t], t)

    def test_every_ground_of_both_looks(self):
        for look in E.LOOKS:
            for t, sc in GOOD.items():
                for bg in ("mantle", "base", "blue", "ink"):
                    body = self.body(self.ok(sc, bg=bg, look=look))
                    self.assertNotRegex(body, r"repeat:|yoyo|Math\.random|Date\b", (look, t, bg))

    def test_an_item_outside_the_scene_fails(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            if t == "crossed-list":
                bad["items"][0]["at"] = W(2)
            else:
                bad["at"] = W(2)
            self.fails(bad, "outside the scene")

    def test_an_item_too_close_to_the_end_fails(self):
        # an item lands by t_out - 0.5 (its exit starts 0.2 s before the cut, and it is seen for 0.3 s first)
        from scenes import SceneError
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            if t == "crossed-list":
                bad["items"][2]["strike"] = W(15)
            else:
                bad["at"] = W(15)
                bad.pop("strike", None)
            sc_ = dict({"id": "sc", "in": "word:4", "out": "word:16"}, **bad)
            ctx = Ctx(sc_, lead(4), lead(16), words30(), TOK, stub_vendor(scratch(self), icons=ICONS), scratch(self), "mantle")
            with self.assertRaises(SceneError) as e:
                REGISTRY[t].render(sc_, ctx, (150, 400, 780))
            self.assertIn("too close to the scene's end", str(e.exception), t)

    def test_the_cases_validate_and_compose_in_both_looks(self):
        mod = cases_e3()
        self.assertEqual(set(mod.CASES), set(TYPES))
        for t, variants in mod.CASES.items():
            self.assertGreaterEqual(len(variants), 3, t)
            for name, data in variants:
                self.assertEqual(REGISTRY[t].validate(data), [], (t, name))
                for look in E.LOOKS:
                    files = {data["src"]: (1280, 256)} if data.get("src") else None
                    self.ok(dict({"type": t}, **data), look=look, files=files, start=1)     # the cases run from word 1

    def test_text_is_28_px_or_more(self):
        for t in TYPES:
            sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", REGISTRY[t].CSS)]
            self.assertTrue(sizes and min(sizes) >= E.MIN_TEXT, t)

    def test_no_hex_colours_no_randomness_no_overshoot_in_the_modules(self):
        for t in TYPES:
            src = read(os.path.join(SCRIPTS, "scenes", "%s.py" % t.replace("-", "_")))
            self.assertNotRegex(src, r"#[0-9A-Fa-f]{6}\b", t)
            self.assertNotRegex(src, r"Math\.random|Date\(|['\"](back|elastic|bounce)\.\w+", t)

    def test_each_keeps_moving_while_it_holds(self):
        # nothing is still for more than a second: once its items are in, idle motion runs on to the scene's end
        for t, sc in GOOD.items():
            ctx, _ = self.ambient(sc)
            self.assertTrue(ctx.ambient_lines, t)
            self.assertTrue(all(l.startswith("tl.") for l in ctx.ambient_lines), t)
            sp = spans(ctx.ambient_lines)
            for (a0, a1), (b0, _) in zip(sp, sp[1:]):
                self.assertLessEqual(b0 - a1, 0.05, (t, a1, b0))           # back to back, no rest between
            self.assertLessEqual(sp[0][0], lead(14) + 1.0, t)               # it starts once the scene is built, or before
            self.assertGreaterEqual(sp[-1][1], D - 1.0 - 1e-6 - 1.6, t)     # and runs to the scene's end

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
    def test_e5_clean_on_every_ground_of_both_looks(self):
        from .test_layout import LC
        vendor = os.environ.get("EXPLAINER_VENDOR")
        if not vendor or not os.path.isdir(os.path.join(vendor, "lucide")):
            self.skipTest("needs the real vendor folder (EXPLAINER_VENDOR: gsap, katex, lucide)")
        variants = [GOOD["crossed-list"],
                    {"type": "crossed-list", "items": [{"text": "A CHARGING CASE THAT CHARGES ITSELF", "at": W(6), "strike": W(7)},
                                                       {"text": "CABLES", "at": W(9)}]},
                    GOOD["price-sticker"],
                    dict(GOOD["price-sticker"], price="$1,299", src="wide.png"),
                    dict(GOOD["price-sticker"], src="tall.png", label="EACH"),
                    GOOD["line-art"],
                    {"type": "line-art", "svg": "art.svg", "caption": "one cable for everything, seriously", "at": W(6), "strike": W(9)}]
        files = {"wide.png": (1280, 256), "tall.png": (300, 1200), "art.svg": STROKE_SVG}
        pages, root = [], scratch(self)
        bgs = ("mantle", "blue", "base", "ink")
        for look in E.LOOKS:
            for k, sc in enumerate(variants):
                d = os.path.join(root, "%s-%d" % (look, k))
                write(os.path.join(d, "transcript.json"), {"words": words30()})
                silent_wav(os.path.join(d, "voice.wav"), VOICE)
                for name, body in files.items():
                    png(os.path.join(d, name), *body) if isinstance(body, tuple) else write(os.path.join(d, name), body)
                bg = bgs[(k + (look == "paper")) % 4]
                first = {"type": "title", "id": "lead", "bg": bg, "in": "word:0", "out": "word:4", "text": "Lead in"}
                sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "look": look, "sound": {"music": "none", "sfx": False},
                                                                "scenes": [first, dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **sc)]})
                r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", vendor)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                with open(os.path.join(d, "public", "moments.json"), encoding="utf-8") as f:
                    pages.append({"index": os.path.join(d, "public", "index.html"), "samples": LC.samples(json.load(f))})
        issues = LC.probe_pages(pages)
        self.assertEqual([], ["%s: %s %s" % (os.path.basename(os.path.dirname(os.path.dirname(i["page"]))), i["text"], i["detail"])
                              for i in issues])


class CrossedList(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["crossed-list"]
        self.fails(dict(sc, items=sc["items"][:1]), "2 to 5 items")
        self.fails(dict(sc, items=sc["items"] * 2), "2 to 5 items")
        none = copy.deepcopy(sc)
        none["items"][1]["text"] = ""
        self.fails(none, "item 1 needs text and at")
        self.fails(dict(sc, prefix="NOT ANY MORE, EVER"), "prefix")
        early = copy.deepcopy(sc)
        early["items"][0]["strike"] = W(5)
        self.fails(early, "item 0", "strike", "before it lands")
        order = copy.deepcopy(sc)
        order["items"][0]["at"], order["items"][1]["at"] = W(10), W(6)
        order["items"][0]["strike"] = W(12)
        self.fails(order, "in order")

    def test_rows_rise_through_a_mask_on_their_words(self):
        html = self.ok(GOOD["crossed-list"])
        for i, w in enumerate((6, 10, 12)):
            self.assertRegex(html, r'id="sc-r%d" data-at="%.3f" data-anchor="word%d"' % (i, lead(w), w))
            self.assertIn("tl.set('#sc-r%d', { yPercent: 120 }, 0);" % i, html)
            m = re.search(r"tl\.fromTo\('#sc-r%d', \{ yPercent: 120 \}, \{ yPercent: 0, duration: ([\d.]+), ease: 'expo\.out'[^}]*\}, ([\d.]+)\);" % i, html)
            self.assertIsNotNone(m, i)
            self.assertAlmostEqual(float(m.group(2)), lead(w), places=3)
        self.assertRegex(html, r'class="cl-m"')
        self.assertIn(".cl-m { overflow:hidden;", REGISTRY["crossed-list"].CSS)
        self.assertEqual(html.count('class="cl-p"'), 3)                       # the prefix over every row

    def test_the_strike_draws_through_and_the_row_greys(self):
        html = self.ok(GOOD["crossed-list"])
        c = E.theme(TOK, "mantle")
        for i, w in ((0, 8), (2, 14)):
            self.assertRegex(html, r'id="sc-t%d" data-at="%.3f" data-anchor="word%d"' % (i, lead(w), w))
            m = re.search(r"tl\.fromTo\('#sc-t%d', \{ backgroundSize: '0%% 6px' \}, \{ backgroundSize: '100%% 6px', duration: 0\.3, "
                          r"ease: 'power3\.inOut'[^}]*\}, ([\d.]+)\);" % i, html)
            self.assertIsNotNone(m, i)
            self.assertAlmostEqual(float(m.group(1)), lead(w), places=3)
            g = re.search(r"tl\.to\('#sc-t%d', \{ color: '([^']+)'[^}]*\}, ([\d.]+)\);" % i, html)
            self.assertEqual(g.group(1).lower(), c["muted"].lower())
            self.assertGreaterEqual(float(g.group(2)), lead(w))
        self.assertNotRegex(html, r"#sc-t1', \{ backgroundSize")                 # row 1 is never struck
        self.assertIn("linear-gradient(%s, %s)" % (c["accent"], c["accent"]), html)

    def test_rows_are_set_in_the_looks_hero_face(self):
        mod = REGISTRY["crossed-list"]
        self.assertTrue(mod.HERO_CSS)
        html = self.ok(GOOD["crossed-list"], look="paper")
        self.assertRegex(html, r"%s \{ font-family:'Archivo'; font-stretch:125%%" % re.escape(mod.HERO_CSS))
        long = {"items": [{"text": "A CHARGING CASE FOR EVERY DAY", "at": W(6)}, {"text": "WIRES", "at": W(8)}]}
        try:
            E.use_look(E.load_tokens(look="paper"))
            wide = mod.height(long, 780)
        finally:
            E.use_look(E.load_tokens())
        self.assertGreater(wide, mod.height(long, 780))                       # the wide face wraps sooner


class PriceSticker(Case):
    def test_it_needs_a_source(self):
        sc = dict(GOOD["price-sticker"])
        del sc["source"]
        self.fails(sc, "needs a source")
        self.assertTrue(REGISTRY["price-sticker"].NEEDS_SOURCE)

    def test_bad_data_says_why(self):
        sc = GOOD["price-sticker"]
        self.fails(dict(sc, price="cheap"), "price", "a number")
        self.fails(dict(sc, price="$1,299,999.99"), "price", "at most")
        self.fails(dict(sc, label="THE PRICE FOR THE PAIR, BEFORE ANY DISCOUNT"), "label", "at most")
        no_at = dict(sc)
        del no_at["at"]
        self.fails(no_at, "missing 'at'")
        self.fails(dict(sc, src="nothing-here.png"), "no file at nothing-here.png")

    def test_it_slams_in_on_its_word_and_the_shadow_tightens(self):
        html = self.ok(GOOD["price-sticker"])
        t = lead(6)
        self.assertRegex(html, r'id="sc-st" data-at="%.3f" data-anchor="word6"' % t)
        self.assertIn("tl.set('#sc-st', { rotation: -6 }, 0);", html)
        m = re.search(r"tl\.fromTo\('#sc-st', \{ opacity: 0, scale: 1\.5, boxShadow: '([^']+)' \}, \{ opacity: 1, scale: 1, "
                      r"boxShadow: '([^']+)', duration: ([\d.]+), ease: 'expo\.out'[^}]*\}, ([\d.]+)\);", html)
        self.assertIsNotNone(m)
        self.assertAlmostEqual(float(m.group(4)), t, places=3)
        far, near = [list(map(float, re.findall(r"(\d+)px", s))) for s in (m.group(1), m.group(2))]
        self.assertGreater(far[0], near[0])                                     # it falls from higher...
        self.assertGreater(far[1], near[1])                                     # ...with a softer shadow
        self.assertRegex(html, r'class="ps-price" id="sc-pr"[^>]*>\$99<')
        self.assertRegex(html, r'class="ps-label" id="sc-lb"[^>]*>FOR THE PAIR<')

    def test_it_breathes_a_degree_either_way_for_the_rest_of_the_scene(self):
        ctx, _ = self.ambient(GOOD["price-sticker"])
        rot = re.findall(r"tl\.to\('#sc-st', \{ rotation: (-?[\d.]+), duration: [\d.]+, ease: 'sine\.inOut' \}, ([\d.]+)\);",
                         "\n".join(ctx.ambient_lines))
        self.assertGreaterEqual(len(rot), 4)
        self.assertEqual({float(r) for r, _ in rot}, {-5.0, -7.0})
        self.assertGreater(float(rot[0][1]), lead(6))

    def test_any_image_aspect_fits(self):
        mod = REGISTRY["price-sticker"]
        for w, h in ((1280, 256), (300, 1200), (800, 800)):
            html = self.ok(dict(GOOD["price-sticker"], src="earbuds.png"), files={"earbuds.png": (w, h)})
            m = re.search(r'<img class="ps-img" id="sc-img" src="assets/sc-earbuds\.png"[^>]*style="width:(\d+)px;height:(\d+)px', html)
            self.assertIsNotNone(m, (w, h))
            iw = int(re.search(r'id="sc-live"[^>]*style="width:(\d+)px', html).group(1))
            self.assertLessEqual(int(m.group(1)), iw)
            self.assertLessEqual(int(m.group(2)), mod.IMG_H)
            self.assertAlmostEqual(int(m.group(1)) / float(m.group(2)), w / float(h), delta=0.05 * w / float(h))
            self.assertTrue(os.path.isfile(os.path.join(self.out, "assets", "sc-earbuds.png")))

    def test_the_image_makes_room_for_itself(self):
        mod = REGISTRY["price-sticker"]
        sc = dict(GOOD["price-sticker"])
        self.assertEqual(mod.height(dict(sc, src="x.png"), 780) - mod.height(sc, 780), mod.IMG_H - mod.OVER)


class LineArt(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["line-art"]
        neither = dict(sc)
        del neither["icon"]
        self.fails(neither, "an icon or an svg")
        self.fails(dict(sc, svg="art.svg"), "an icon or an svg, not both")
        self.fails(dict(sc, icon="Not An Icon"), "is not a Lucide name")
        self.fails(dict(sc, icon="unicorn"), "unknown icon 'unicorn'")
        no_icon = dict(sc)
        del no_icon["icon"]
        self.fails(dict(no_icon, svg="art.png"), "svg is a .svg file")
        self.fails(dict(no_icon, svg="missing.svg"), "no file at missing.svg")
        self.fails(dict(sc, caption=""), "missing 'caption'")
        self.fails(dict(sc, caption=" ".join(["word"] * 20)), "caption", "at most")
        self.fails(dict(sc, strike=W(5)), "the strike", "before the drawing")

    def test_a_filled_svg_fails_naming_it(self):
        sc = dict(GOOD["line-art"], svg="drawing.svg")
        del sc["icon"]
        for body, shape in ((FILLED_SVG, "<rect>"), (DEFAULT_FILL_SVG, "<circle>"), (STYLE_FILL_SVG, "<ellipse>")):
            self.fails(sc, "drawing.svg", shape, "fill", "stroke-only", files={"drawing.svg": body})
        self.fails(sc, "drawing.svg", "<text>", files={"drawing.svg": TEXT_SVG})
        self.fails(sc, "drawing.svg", "not an SVG", files={"drawing.svg": "<html>no</html>"})

    def test_a_stroke_only_svg_is_drawn_on_in_the_looks_ink(self):
        sc = dict(GOOD["line-art"], svg="art.svg")
        del sc["icon"]
        html = self.ok(sc, files={"art.svg": STROKE_SVG})
        body = self.body(html)
        self.assertNotIn("#123456", body)                                     # the creator's colours give way to the look's
        self.assertNotIn("<title>", body)
        self.assertEqual(len(re.findall(r'<(?:\w+:)?(?:path|circle|polyline)\b[^>]*\bpathLength="1"', body)), 3)
        self.assertIn('stroke-width="2"', body)                                 # a stroke width set in style= is kept
        self.assertIn('viewBox="0 0 100 50"', body)
        self.assertRegex(body, r'id="sc-art" data-at="%.3f" data-anchor="word6"' % lead(6))
        self.assertIn("color:%s" % E.theme(TOK, "mantle")["ink"], body)

    def test_the_drawing_draws_on_its_word_and_the_caption_follows(self):
        html = self.ok(GOOD["line-art"])
        m = re.search(r"tl\.fromTo\('#sc \.la-s', \{ strokeDashoffset: 1\.02 \}, \{ strokeDashoffset: 0, duration: 1\.2, "
                      r"ease: 'power2\.inOut'[^}]*\}, ([\d.]+)\);", html)
        self.assertIsNotNone(m)
        self.assertAlmostEqual(float(m.group(1)), lead(6), places=3)
        cap = re.search(r"tl\.fromTo\('#sc-cap', \{ opacity: 0[^;]*\}, ([\d.]+)\);", html)
        self.assertGreater(float(cap.group(1)), lead(6))
        self.assertRegex(html, r'class="la-cap" id="sc-cap" style="[^"]*font-family:\'Instrument Serif\'[^"]*font-style:italic')
        self.assertEqual(len(re.findall(r'class="la-s"', self.body(html))), 1)     # the stub icon's one path

    def test_the_caption_is_struck_through_in_the_accent(self):
        html = self.ok(GOOD["line-art"])
        c = E.theme(TOK, "mantle")
        self.assertRegex(html, r'id="sc-ct" data-at="%.3f" data-anchor="word10"' % lead(10))
        m = re.search(r"tl\.fromTo\('#sc-ct', \{ backgroundSize: '0% 5px' \}, \{ backgroundSize: '100% 5px', duration: 0\.3, "
                      r"ease: 'power3\.inOut'[^}]*\}, ([\d.]+)\);", html)
        self.assertIsNotNone(m)
        self.assertAlmostEqual(float(m.group(1)), lead(10), places=3)
        self.assertIn("linear-gradient(%s, %s)" % (c["accent"], c["accent"]), html)
        plain = dict(GOOD["line-art"])
        del plain["strike"]
        self.assertNotIn("backgroundSize", self.ok(plain))

    def test_a_number_in_the_file_name_needs_no_source(self):
        sc = dict(GOOD["line-art"], svg="usb-c-2024.svg")
        del sc["icon"]
        self.ok(sc, files={"usb-c-2024.svg": STROKE_SVG})


if __name__ == "__main__":
    unittest.main()
