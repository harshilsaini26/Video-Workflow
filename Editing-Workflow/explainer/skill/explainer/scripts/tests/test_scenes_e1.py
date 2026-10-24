"""The picture scenes of the editorial pass (group E1): product-hero and photo-grid. A product cut-out that rises in
over its own title (the title is set behind it, declared with data-depth="behind", so its cut-out crosses the letters)
and floats while held; and one to four credited photos that slide in one by one and drift. Each refuses bad data with
a reason, lands its items on their words, keeps moving while it holds, fits any picture and composes clean."""
import copy, importlib.util, json, os, re, shutil, unittest
from .helpers import SCRIPTS, read, run, scratch, write
from .test_assets import png
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY

W = lambda i: "word:%d" % i
TYPES = ("product-hero", "photo-grid")
NOTE = {"x": 0.75, "y": 0.15, "label": "WAIT... A WIRE?", "at": W(9), "mark": "circle", "side": "left"}

GOOD = {
    "product-hero": {"type": "product-hero", "src": "bud.png", "alt": "an earbud", "title": "No wire", "title_at": W(5), "at": W(6),
                     "aspect": 1.0, "notes": [NOTE]},
    "photo-grid": {"type": "photo-grid", "layout": "grid", "photos": [
        {"src": "a.png", "credit": "stand-in image", "tag": "BEFORE", "at": W(5)},
        {"src": "b.png", "credit": "Photo: J. Rivera", "at": W(5)},
        {"src": "c.png", "credit": "stand-in image", "at": W(8)}]},
}
IMAGES = {"bud.png": (1200, 1200), "a.png": (1200, 800), "b.png": (800, 1200), "c.png": (1600, 900)}
ANCHORED = {"product-hero": 3, "photo-grid": 3}     # the title, the image, the note's label; one per photo with its own at


def at_minus_lead(i):
    return round(t_word(i) - E.LEAD, 3)


def cases_e1():
    spec = importlib.util.spec_from_file_location("cases_e1", os.path.join(SCRIPTS, "dev", "cases_e1.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CASES


def make_cases():
    spec = importlib.util.spec_from_file_location("make_cases", os.path.join(SCRIPTS, "dev", "make-cases.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def in_paper(fn):
    E.use_look(E.load_tokens(look="paper"))
    try:
        return fn()
    finally:
        E.use_look(E.load_tokens())


class Case(unittest.TestCase):
    def build(self, scene, bg="mantle", look=None, images=None, vendor=None, headline=None, files=None):
        d = scratch(self)
        for name, data in (files or {}).items():
            with open(os.path.join(d, name), "wb") as f:
                f.write(data)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        for name, (w, h) in dict(IMAGES, **(images or {})).items():
            png(os.path.join(d, name), w, h)
        lead = {"type": "title", "id": "lead", "bg": bg, "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **scene)
        if headline:
            sc["headline"] = headline
        board = {"id": "t", "scenes": [lead, sc], "sound": {"music": "none", "sfx": False}}
        if look:
            board["look"] = look
        sp = write(os.path.join(d, "storyboard.json"), board)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", vendor or stub_vendor(d))
        self.last = d
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def ok(self, scene, **kw):
        r, html = self.build(scene, **kw)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html

    def fails(self, scene, text, **kw):
        r, _ = self.build(scene, **kw)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def moments(self):
        with open(os.path.join(self.last, "public", "moments.json"), encoding="utf-8") as f:
            return {s["id"]: s for s in json.load(f)["scenes"]}

    def body(self, html):
        return html.split('id="host-sc"')[1].split('id="captions"')[0]

    def script(self, html):
        return html.split("// sc (")[1].split("\n// ")[0] if "// sc (" in html else ""


class Shared(Case):
    def test_both_types_are_found(self):
        for t in TYPES:
            self.assertIn(t, REGISTRY)

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            body = self.body(self.ok(sc))
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), ANCHORED[t], t)

    def test_every_ground_in_both_looks(self):
        for t, sc in GOOD.items():
            for look in ("latte", "paper"):
                for bg in ("mantle", "base", "blue", "ink"):
                    html = self.ok(sc, bg=bg, look=look)
                    self.assertNotRegex(self.body(html) + self.script(html), r"repeat:|yoyo|Math\.random|Date\(|back\.|elastic|bounce",
                                        (t, look, bg))

    def test_an_item_outside_the_scene_fails(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            if t == "product-hero":
                bad["at"] = W(2)
            else:
                bad["photos"][0]["at"] = W(2)
            self.fails(bad, "outside the scene")

    def test_text_is_28_px_or_more(self):
        for t in TYPES:
            sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", REGISTRY[t].CSS)]
            self.assertTrue(sizes and min(sizes) >= 28, t)

    def test_no_hex_colours_and_no_unseeded_randomness_in_the_modules(self):
        for f in ("product_hero", "photo_grid"):
            with open(os.path.join(SCRIPTS, "scenes", "%s.py" % f), encoding="utf-8") as fh:
                src = fh.read()
            self.assertNotRegex(src, r"#[0-9A-Fa-f]{6}\b", f)
            self.assertNotRegex(src, r"Math\.random|Date\(|import random|back\.out|elastic|bounce", f)

    def test_cases_cover_three_lengths_and_fit(self):
        cases = cases_e1()
        self.assertEqual(set(cases), set(TYPES))
        for t, variants in cases.items():
            names = [n for n, _ in variants]
            for n in ("short", "mid", "long"):
                self.assertIn(n, names, t)
            for name, data in variants:
                self.assertEqual(REGISTRY[t].validate(data), [], (t, name))
                for look in ("latte", "paper"):
                    E.use_look(E.load_tokens(look=look))
                    try:
                        self.assertLessEqual(REGISTRY[t].height(data, 780), 712, (t, name, look))
                    finally:
                        E.use_look(E.load_tokens())

    def test_every_src_gets_a_placeholder_named_by_its_size(self):
        mc = make_cases()
        imgs = mc.images({"src": "logo.png", "screenshot": "shot.png",
                          "photos": [{"src": "p0-1200x800.png"}, {"src": "deep/p1.png", "notes": []}]})
        self.assertEqual(sorted(imgs), sorted([("logo.png", 1280, 256), ("shot.png", 1280, 2400), ("p0-1200x800.png", 1200, 800),
                                                ("deep/p1.png", 1280, 256)]))


class ProductHero(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["product-hero"]
        self.fails(dict(sc, src=None), "src")
        self.fails(dict(sc, src="bud.txt"), "PNG, JPEG, WebP or GIF")
        self.fails(dict(sc, alt=""), "alt")
        self.fails({k: v for k, v in sc.items() if k != "title"}, "title_at needs a title")
        self.fails(dict(sc, aspect=0), "aspect")
        self.fails(dict(sc, notes=[dict(NOTE, x=3)]), "note 0")
        self.fails(dict(sc, title="An extraordinarily overlong title that never fits three lines"), "title")
        self.fails(dict(sc, src="missing.png"), "no file at missing.png")
        self.fails(dict(sc, float="yes"), "float")

    def test_an_opaque_image_under_a_title_fails_naming_the_fix(self):
        # a JPEG (or a PNG with no alpha) is a rectangle: the title behind it would be hidden, so E3 says what to do;
        # without a title an opaque photo is fine (the JPEG case)
        from .test_images import jpeg_bytes, rgb_png_bytes
        for name, data in (("photo.jpg", jpeg_bytes(1200, 1200)), ("flat.png", rgb_png_bytes(1200, 1200))):
            r, _ = self.build(dict(GOOD["product-hero"], src=name), files={name: data})
            self.assertNotEqual(r.returncode, 0, r.stdout)
            self.assertIn("no transparency", r.stdout)
            self.assertIn("headline", r.stdout)
            sc = {k: v for k, v in GOOD["product-hero"].items() if k not in ("title", "title_at")}
            self.ok(dict(sc, src=name), files={name: data})

    def test_an_image_is_never_stretched_by_the_browser(self):
        # the box comes from the header; if the browser draws it otherwise (an EXIF turn it can't see), it is contained
        self.assertRegex(REGISTRY["product-hero"].CSS, r"\.ph-fl > img \{[^}]*object-fit:contain")
        self.assertRegex(REGISTRY["price-sticker"].CSS, r"\.ps-img \{[^}]*object-fit:contain")

    def test_the_title_sits_behind_the_image_in_the_hero_face(self):
        for look in ("latte", "paper"):
            html = self.ok(GOOD["product-hero"], look=look)
            body = self.body(html)
            self.assertRegex(body, r'<div class="ph-t" id="sc-t" data-depth="behind" data-at="%.3f" data-anchor="word5"' % at_minus_lead(5))
            self.assertLess(body.index('id="sc-t"'), body.index('id="sc-img"'))          # under it in the page order too
            z = lambda cls: int(re.search(r"\.%s \{[^}]*z-index:(\d+)" % cls, REGISTRY["product-hero"].CSS).group(1))
            self.assertLess(z("ph-t"), z("ph-img"))
            self.assertIn(in_paper(lambda: E.hero()["css"]) if look == "paper" else E.hero()["css"], body)
            size = int(re.search(r'class="ph-tl" id="sc-t0" style="font-size:(\d+)px', body).group(1))
            scale = float(re.search(r'id="sc-live"[^>]*transform:scale\(([\d.]+)\)', html).group(1))
            self.assertGreaterEqual(size * scale * E.load_tokens()["ambient"]["camera"]["to"], 120, look)   # drawn

    def test_the_title_rises_line_by_line_through_masks(self):
        sc = dict(GOOD["product-hero"], title="Twelve hours in a pocket")
        page = self.ok(sc)
        lines = re.findall(r'<div class="ph-m" style="height:(\d+)px"><div class="ph-tl" id="sc-t(\d)"', page)
        self.assertGreaterEqual(len(lines), 2)
        for k, (_, i) in enumerate(lines):
            self.assertIn("tl.set('#sc-t%s', { yPercent: 110 }, 0);" % i, page)
            self.assertRegex(page, r"tl\.fromTo\('#sc-t%s', \{ yPercent: 110 \}, \{ yPercent: 0, duration: 0\.6, ease: 'expo\.out', "
                                   r"immediateRender: false \}, %.3f\);" % (i, at_minus_lead(5) + 0.08 * k))

    def test_it_rises_in_then_floats_and_pushes_in_while_held(self):
        page = self.ok(GOOD["product-hero"])
        t = at_minus_lead(6)
        self.assertRegex(page, r"tl\.fromTo\('#sc-img', \{ opacity: 0, y: 90 \}, \{ opacity: 1, y: 0, duration: 0\.7, ease: 'expo\.out', "
                               r"immediateRender: false \}, %.3f\);" % t)
        floats = [(float(a), float(d), float(s)) for a, d, s in
                  re.findall(r"tl\.to\('#sc-fl', \{ y: (-?\d+), duration: ([\d.]+), ease: 'sine\.inOut' \}, ([\d.]+)\);", page)]
        self.assertGreaterEqual(len(floats), 3)
        self.assertEqual({abs(a) for a, _, _ in floats}, {8})
        self.assertAlmostEqual(floats[0][2], t + 0.7, places=3)
        self.assertGreater(floats[-1][2] + floats[-1][1], D - 2.5)                   # it floats for the scene's life
        push = re.search(r"tl\.fromTo\('#sc-fl', \{ scale: 1 \}, \{ scale: 1\.025, duration: ([\d.]+), ease: 'none', immediateRender: false \}, "
                         r"([\d.]+)\);", page)
        self.assertIsNotNone(push)
        self.assertAlmostEqual(float(push.group(1)) + float(push.group(2)), D, places=2)
        still = self.ok(dict(GOOD["product-hero"], float=False))
        self.assertNotRegex(still, r"tl\.to\('#sc-fl', \{ y:")
        self.assertRegex(still, r"tl\.fromTo\('#sc-fl', \{ scale: 1 \}")                 # it still pushes in

    def test_a_soft_shadow_from_the_palette(self):
        page = self.ok(GOOD["product-hero"])
        self.assertIn("filter:drop-shadow(0 30px 40px %s)" % E.rgba(E.theme(E.load_tokens(), "base")["ink"], 0.28), page)

    def test_any_aspect_fits(self):
        mod = REGISTRY["product-hero"]
        for (w, h) in ((3000, 1000), (500, 1000), (1200, 1200), (1920, 1080), (1000, 3000)):
            for give in (True, False):
                for look in ("latte", "paper"):
                    sc = dict(GOOD["product-hero"], src="x.png", notes=[])
                    if give:
                        sc["aspect"] = w / float(h)
                    else:
                        sc.pop("aspect")
                    html = self.ok(sc, look=look, images={"x.png": (w, h)})
                    m = self.moments()["sc"]
                    left, top, bw, bh = m["box"]
                    self.assertTrue(E.inside_scene(left, top - E.IDLE_ROOM, bw, bh + 2 * E.IDLE_ROOM), (w, h, give, look, m["box"]))
                    box = re.search(r'id="sc-img" data-at="[\d.]+" data-anchor="word\d+" style="left:(\d+)px;top:(\d+)px;width:(\d+)px;'
                                    r'height:(\d+)px', html)
                    il, it, iw, ih = map(int, box.groups())
                    self.assertLessEqual(il + iw, bw / m["scale"] + 1, (w, h))
                    self.assertLessEqual(it + ih, bh / m["scale"] + 1, (w, h))
                    self.assertAlmostEqual(iw / float(ih), w / float(h), delta=0.03 * w / float(h))        # never stretched
                    if not give and abs(w - h) > 1:
                        self.assertIn("aspect", self.build(sc, look=look, images={"x.png": (w, h)})[0].stdout)   # a note names it

    def test_the_box_hugs_the_aspect(self):
        mod = REGISTRY["product-hero"]
        base = {"src": "x.png", "alt": "x"}
        self.assertEqual(mod.height(dict(base, aspect=3.0), 950), round(int(950 / mod.PUSH) / 3.0))   # a 3:1 banner, full width
        self.assertLess(mod.height(dict(base, aspect=3.0), 950), mod.height(dict(base, aspect=1.0), 950))
        self.assertLessEqual(mod.height(dict(base, aspect=0.5), 780), 712)
        tall = self.ok(dict(GOOD["product-hero"], src="t.png", aspect=0.5, notes=[]), images={"t.png": (500, 1000)})
        self.assertGreater(self.moments()["sc"]["box"][3], 567)                         # a tall cut-out takes the narrow column's height

    def test_a_title_too_wide_for_any_column_fails(self):
        out = in_paper(lambda: REGISTRY["product-hero"].validate(dict(GOOD["product-hero"], title="Headphones")))
        self.assertTrue(any("wider than" in e for e in out), out)

    def test_under_a_headline_it_takes_the_room_left(self):
        hl = {"text": "No battery", "at": W(5)}
        for look in ("latte", "paper"):
            self.ok(dict(GOOD["product-hero"], title_at=W(6), notes=[]), headline=hl, look=look)
            m = self.moments()["sc"]
            self.assertGreaterEqual(m["box"][1] - E.IDLE_ROOM, m["headline"][1] + m["headline"][3], look)


class PhotoGrid(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["photo-grid"]
        self.fails(dict(sc, photos=[]), "1 to 4 photos")
        self.fails(dict(sc, photos=sc["photos"] * 2), "1 to 4 photos")
        self.fails(dict(sc, layout="mosaic"), "layout is stack, grid or collage")
        self.fails(dict(sc, layout="stack", photos=sc["photos"] + [dict(sc["photos"][0], at=W(9))]), "a stack holds 1 to 3")
        self.fails(dict(sc, layout="collage", photos=sc["photos"][:1]), "a collage holds 2 to 4")
        self.fails(dict(sc, photos=[{"credit": "x", "at": W(5)}]), "photo 0: src")
        late = copy.deepcopy(sc)
        late["photos"][2]["at"] = W(4)
        self.fails(late, "photos land in order")
        self.fails(dict(sc, notes=[dict(NOTE, mark="star")]), "note 0")

    def test_every_photo_needs_a_credit_naming_it(self):
        sc = copy.deepcopy(GOOD["photo-grid"])
        del sc["photos"][1]["credit"]
        out = self.fails(sc, "photo 1 (b.png) has no credit")
        self.assertIn("E3 FAIL", out)

    def test_a_credit_too_wide_for_its_photo_fails_naming_it(self):
        sc = copy.deepcopy(GOOD["photo-grid"])
        sc["layout"] = "collage"
        sc["photos"][1]["credit"] = "J. Rivera"
        sc["photos"].append({"src": "a.png", "credit": "Photo: the photographer's agency", "at": W(10)})
        self.fails(sc, "photo 3 (a.png): its credit")

    def test_photos_slide_in_one_by_one(self):
        page = self.ok(GOOD["photo-grid"])
        starts = [float(s) for s in re.findall(r"tl\.fromTo\('#sc-p\d', \{ opacity: 0, y: 60 \}, \{ opacity: 1, y: 0, duration: 0\.6, "
                                               r"ease: 'expo\.out', immediateRender: false \}, ([\d.]+)\);", page)]
        self.assertEqual(len(starts), 3)
        self.assertAlmostEqual(starts[0], at_minus_lead(5), places=3)
        self.assertAlmostEqual(starts[1], at_minus_lead(5) + 0.12, places=3)          # the same word: 0.12 s after
        self.assertAlmostEqual(starts[2], at_minus_lead(8), places=3)
        self.assertRegex(page, r'id="sc-p0" data-at="%.3f" data-anchor="word5"' % at_minus_lead(5))
        self.assertRegex(page, r'id="sc-p2" data-at="%.3f" data-anchor="word8"' % at_minus_lead(8))
        follow = copy.deepcopy(GOOD["photo-grid"])
        del follow["photos"][1]["at"]                                                   # no at: it follows the one before
        page = self.ok(follow)
        self.assertRegex(page, r"tl\.fromTo\('#sc-p1', [^;]*\}, %.3f\);" % (at_minus_lead(5) + 0.12))

    def test_each_photo_drifts_while_held(self):
        page = self.ok(GOOD["photo-grid"])
        for i in range(3):
            legs = re.findall(r"tl\.to\('#sc-d%d', \{ [xy]: (-?\d+), duration: ([\d.]+), ease: 'sine\.inOut' \}, ([\d.]+)\);" % i, page)
            self.assertGreaterEqual(len(legs), 3, i)
            self.assertLessEqual(max(abs(int(a)) for a, _, _ in legs), 6)
            self.assertGreater(float(legs[-1][2]) + float(legs[-1][1]), D - 2.5, i)
            self.assertRegex(page, r"tl\.fromTo\('#sc-i%d', \{ scale: 1 \}, \{ scale: 1\.06, duration: [\d.]+, ease: 'none'" % i)

    def test_the_chips(self):
        page = self.ok(GOOD["photo-grid"])
        css = REGISTRY["photo-grid"].CSS
        cr = re.search(r"\.pgr-cr \{([^}]*)\}", css).group(1)
        for want in ("left:16px", "bottom:16px", "font-family: var(--label)", "font-size:28px", "letter-spacing:.06em"):
            self.assertIn(want, cr)
        p = E.theme(E.load_tokens(), "base")
        self.assertIn('class="pgr-cr" id="sc-c0" style="background:%s;color:%s">stand-in image<' % (E.rgba(p["ink"], 0.8), p["paper"]), page)
        tag = re.search(r"\.pgr-tag \{([^}]*)\}", css).group(1)
        self.assertIn("left:16px", tag)
        self.assertIn("top:16px", tag)
        self.assertIn('id="sc-g0"', page)
        self.assertNotIn('id="sc-g1"', page)

    def test_photos_have_rounded_corners_a_shadow_and_cover(self):
        css = REGISTRY["photo-grid"].CSS
        self.assertRegex(css, r"\.pgr-d \{[^}]*border-radius:24px")
        self.assertRegex(css, r"\.pgr-i \{[^}]*object-fit:cover")
        self.assertRegex(self.ok(GOOD["photo-grid"]), r'class="pgr-d" id="sc-d0" style="box-shadow:[^"]*rgba\(')

    def test_layouts_have_fixed_proportions_and_fit(self):
        mod = REGISTRY["photo-grid"]
        for layout, counts in (("stack", (1, 2, 3)), ("grid", (1, 2, 3, 4)), ("collage", (2, 3, 4))):
            for n in counts:
                sc = {"layout": layout, "photos": [{"src": "a.png", "credit": "c"}] * n}
                for width in (950, 780):
                    cells, h = mod.cells(sc, width)
                    self.assertEqual(h, mod.height(sc, width))
                    self.assertEqual(len(cells), n)
                    for x, y, w, ch in cells:
                        self.assertTrue(0 <= x and x + w <= width and 0 <= y and y + ch <= h, (layout, n, width))
                        self.assertGreaterEqual(min(w, ch), 128, (layout, n, width))   # room for a tag and a credit
                    other = mod.cells(sc, 700)[0]
                    for (x, y, w, ch), (_, _, w2, h2) in zip(cells, other):
                        self.assertAlmostEqual(w / float(ch), w2 / float(h2), delta=0.03)     # proportions, not sizes
                self.assertLessEqual(mod.height(sc, 780), 712, (layout, n))

    def test_notes_mark_the_first_photo(self):
        page = self.ok(dict(GOOD["photo-grid"], notes=[dict(NOTE, x=0.3, y=0.5, side="right", label="PLUG")]))
        first = page.split('id="sc-d0"')[1].split('id="sc-p1"')[0]
        self.assertIn('id="sc-n0t"', first)


def have_browser():
    from .test_layout import have_browser as hb
    return hb()


class Depth(Case):
    """Gate E5 lets the image cover only the text that declares it sits behind (Ruling 6), in its own scene."""

    def vendor(self):
        v = os.environ.get("EXPLAINER_VENDOR")
        if not v or not os.path.isfile(os.path.join(v, "gsap.min.js")):
            self.skipTest("needs the real vendor folder (EXPLAINER_VENDOR: gsap)")
        return v

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome")
    def test_a_title_behind_its_image_passes_and_the_same_title_in_front_fails(self):
        import layout_check as LC
        sc = dict(GOOD["product-hero"], title="No wire", notes=[])
        self.ok(sc, vendor=self.vendor())
        pub = os.path.join(self.last, "public")
        with open(os.path.join(pub, "moments.json"), encoding="utf-8") as f:
            smp = LC.samples(json.load(f))
        self.assertEqual(LC.probe(os.path.join(pub, "index.html"), smp), [])
        page = read(os.path.join(pub, "index.html"))
        self.assertIn('data-depth="behind"', page)
        write(os.path.join(pub, "index.html"), page.replace(' data-depth="behind"', ""))
        issues = LC.probe(os.path.join(pub, "index.html"), smp)
        self.assertTrue(any(i["kind"] == "covered" and "#sc-pic" in i["detail"] for i in issues), issues)

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome")
    def test_e5_is_clean_for_the_cases_in_both_looks(self):
        import layout_check as LC
        vendor = self.vendor()
        mc = make_cases()
        root = scratch(self)
        pages = []
        for look in ("latte", "paper"):
            for k, (typ, variants) in enumerate(sorted(cases_e1().items())):
                for j, (name, data) in enumerate(variants):
                    d = os.path.join(root, look, "%s-%s" % (typ, name))
                    write(os.path.join(d, "transcript.json"), {"words": [{"text": "word%d" % i, "start": 0.5 + i * 0.4, "end": 0.8 + i * 0.4}
                                                                          for i in range(40)]})
                    silent_wav(os.path.join(d, "voice.wav"), 15.5)
                    for rel, w, h in mc.images(data):
                        png(os.path.join(d, rel), w, h)
                    bg = ("mantle", "blue", "base", "ink")[(k + j) % 4]
                    sc = dict({"type": typ, "id": "sc", "bg": bg, "in": "word:1", "out": 16.0}, **data)
                    sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "look": look, "scenes": [mc.LEAD_IN, sc],
                                                                    "sound": {"music": "none", "sfx": False}})
                    r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", vendor)
                    self.assertEqual(r.returncode, 0, "%s %s-%s: %s" % (look, typ, name, r.stdout))
                    with open(os.path.join(d, "public", "moments.json"), encoding="utf-8") as f:
                        pages.append({"index": os.path.join(d, "public", "index.html"), "samples": LC.samples(json.load(f))})
        issues = LC.probe_pages(pages)
        self.maxDiff = None
        self.assertEqual([], ["%s: %s %s" % (os.path.relpath(i["page"], root), i["text"], i["detail"]) for i in issues])


if __name__ == "__main__":
    unittest.main()
