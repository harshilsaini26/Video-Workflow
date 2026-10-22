"""The editorial pass (the Bose reference, 2026-10-18): captions small at the bottom so the centre is always the
animation's, the paper look, three typefaces, the headline layer."""
import os, re, unittest
from .helpers import load, read
from .test_compose import BOARD
from .test_foundations import compose
import explainer_lib as E

TOK = E.load_tokens()


class Layout(unittest.TestCase):
    def test_captions_sit_at_the_bottom_small(self):
        # the captions leave the centre: 44 px, at most two lines, at the bottom of the safe area in the narrow column
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        css = re.search(r"\.cap \{[^}]*\}", page).group(0)
        self.assertIn("left:150px; width:780px; top:1130px; height:105px;", css)
        self.assertIn("font-size:44px", css)
        self.assertEqual(E.CAPTION_BAND, (1130, 1235))
        self.assertEqual(E.CAPTION_SIZE, 44)

    def test_the_centre_is_the_scenes(self):
        self.assertEqual(E.SCENE, {"left": 65, "top": 345, "right": 1015, "bottom": 1105})
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        for sc in load(os.path.join(d, "public", "moments.json"))["scenes"]:
            left, top, w, h = sc["box"]
            self.assertGreaterEqual(top, 345, sc["id"])
            self.assertLessEqual(top + h, 1105, sc["id"])

    def test_a_wide_scene_centres_in_the_area_unless_it_would_reach_the_buttons(self):
        # the centre is the animation's: a full-width scene centres on the area's middle (725), and only a tall one
        # rises, just enough to end above y 960 (the action column)
        from . import explainer_compose_shim as C
        import explainer_lib as E2

        def mod(h):
            class M:
                TYPE, CSS, MAX_SCALE = "m", ".m { font-size:40px; }", 1.0
                min_width = staticmethod(lambda sc: 900)
                height = staticmethod(lambda sc, w: h)
            return M
        left, top, w, h, iw, ih, s = C.place("small", mod(300), {})
        self.assertEqual(w, 950)
        self.assertAlmostEqual(top + h / 2.0, 725, delta=1)
        left, top, w, h, iw, ih, s = C.place("tall", mod(560), {})
        self.assertEqual(w, 950)
        self.assertLessEqual(top + h, E2.L.RIGHT_COL_TOP - E2.IDLE_ROOM)
        self.assertGreaterEqual(top, E2.SCENE["top"] + E2.IDLE_ROOM)

    def test_captions_have_a_halo_in_the_grounds_colour(self):
        # a bare shape may pass behind the captions (it runs on to y 1650): the words keep a halo of their ground
        r, d = compose(self, BOARD)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        for i, bg in ((0, "mantle"),):
            m = re.search(r'<div class="cap" id="cap%d" style="([^"]*)"' % i, page)
            self.assertIn("text-shadow:0 0 18px %s, 0 0 6px %s" % ((E.theme(TOK, bg)["bg"],) * 2), m.group(1))


class Looks(unittest.TestCase):
    def test_paper_overrides_the_palette_by_name(self):
        paper = E.load_tokens(look="paper")
        self.assertEqual(paper["look"], "paper")
        self.assertEqual(paper["palette"]["base"], "#EFEAE3")
        self.assertEqual(paper["palette"]["text"], "#141414")
        self.assertEqual(E.theme(paper, "base")["accent"], "#D9472E")
        self.assertEqual(set(paper["palette"]), set(TOK["palette"]))          # the same 26 names: scenes resolve either look
        self.assertEqual(paper["motion"], dict(TOK["motion"], boil=True))     # what a look does not name stays (paper boils)

    def test_latte_is_the_default(self):
        self.assertEqual(E.LOOKS, ("latte", "paper"))
        self.assertEqual(E.load_tokens()["look"], "latte")
        self.assertEqual(E.load_tokens(look="latte")["palette"], TOK["palette"])

    def test_a_paper_reel_composes_on_paper(self):
        board = dict(BOARD, look="paper")
        r, d = compose(self, board)
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        self.assertIn("background:#EFEAE3".lower(), page.lower().replace(" ", ""))
        self.assertEqual(load(os.path.join(d, "public", "moments.json"))["look"], "paper")

    def test_an_unknown_look_fails_naming_the_known_ones(self):
        r, _ = compose(self, dict(BOARD, look="neon"))
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E3 FAIL", r.stdout)
        self.assertIn("latte, paper", r.stdout)

    def test_the_planner_puts_a_paper_reel_on_one_ground(self):
        # the editorial look keeps one ground: colour comes from the pictures and the accent, not from the ground
        from .test_plan import SCRIPT, Plan
        import copy
        script = dict(copy.deepcopy(SCRIPT), payoff="l4", look="paper")
        _, sb, _ = Plan.plan(self, script)
        self.assertEqual(sb["look"], "paper")
        self.assertEqual({s["bg"] for s in sb["scenes"]}, {"base"})


FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "assets", "fonts")


class Fonts(unittest.TestCase):
    def test_the_fonts_ship_with_their_licences(self):
        for font, lic, name in (("Archivo-wdth.woff2", "OFL-Archivo.txt", "Archivo"),
                                ("InstrumentSerif-Italic.woff2", "OFL-InstrumentSerif.txt", "Instrument Serif")):
            self.assertTrue(os.path.isfile(os.path.join(FONTS, font)), font)
            text = read(os.path.join(FONTS, lic))
            self.assertIn(name, text)
            self.assertIn("SIL Open Font License", text)

    def test_glyph_tables_cover_ascii(self):
        g = E.glyphs()
        for table in ("wide800", "serif400i"):
            for c in range(32, 127):
                self.assertIn(chr(c), g[table], (table, chr(c)))

    def test_wide_is_wider_than_dm_sans(self):
        self.assertGreater(E.text_width("WIRED", 100, "wide800"), E.text_width("WIRED", 100, "display700") * 1.15)

    def test_the_hero_face_follows_the_look(self):
        E.use_look(E.load_tokens(look="paper"))
        h = E.hero()
        self.assertEqual((h["family"], h["stretch"], h["weight"], h["glyphs"]), ("Archivo", "125%", 800, "wide800"))
        self.assertIn("font-stretch:125%", h["css"])
        E.use_look(E.load_tokens())
        self.assertEqual(E.hero()["glyphs"], "display700")
        self.assertEqual(E.aside()["glyphs"], "serif400i")

    def test_paper_pages_load_the_fonts(self):
        r, d = compose(self, dict(BOARD, look="paper"))
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        self.assertRegex(page, r'@font-face \{ font-family: "Archivo"; src: url\("fonts/Archivo-wdth.woff2"\)[^}]*font-stretch: 62% 125%')
        self.assertRegex(page, r'@font-face \{ font-family: "Instrument Serif"; src: url\("fonts/InstrumentSerif-Italic.woff2"\)[^}]*font-style: italic')
        for f in ("Archivo-wdth.woff2", "InstrumentSerif-Italic.woff2"):
            self.assertIn('href="fonts/%s"' % f, page)
            self.assertTrue(os.path.isfile(os.path.join(d, "public", "fonts", f)))


def with_headline(h, scene=1, board=None):
    import copy
    b = copy.deepcopy(board or BOARD)
    b["scenes"][scene]["headline"] = h
    return b


class Headline(unittest.TestCase):
    H = {"text": "No battery inside", "kicker": "THE CATCH", "aside": "seriously?", "at": "word:9", "aside_at": "word:11",
         "accent": ["battery"]}

    def test_a_headline_sits_top_left_and_the_scene_below_it(self):
        import headline
        r, d = compose(self, with_headline(self.H))
        self.assertEqual(r.returncode, 0, r.stdout)
        sc = [s for s in load(os.path.join(d, "public", "moments.json"))["scenes"] if s["id"] == "n1"][0]
        hl = headline.layout(self.H, 950)
        self.assertEqual(sc["headline"], [65, 345, 950, hl["height"]])
        self.assertGreaterEqual(sc["box"][1], 345 + hl["height"] + headline.GAP)
        self.assertLessEqual(sc["box"][1] + sc["box"][3], 1105)

    def test_a_headline_rises_on_its_word_line_by_line(self):
        from .test_compose import t_word
        r, d = compose(self, with_headline(dict(self.H, text="No battery inside the earbuds at all")))
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        t0 = t_word(9) - E.LEAD
        self.assertIn("tl.fromTo('#n1-hl0', { yPercent: 110 }, { yPercent: 0, duration: 0.55, ease: 'expo.out', immediateRender: false }, %.3f);" % t0, page)
        self.assertIn("tl.fromTo('#n1-hl1', { yPercent: 110 }, { yPercent: 0, duration: 0.55, ease: 'expo.out', immediateRender: false }, %.3f);" % (t0 + 0.08), page)
        self.assertRegex(page, r'id="n1-hl0" data-at="%.3f" data-anchor="word9"' % t0)
        self.assertRegex(page, r"tl\.fromTo\('#n1-ha', \{ opacity: 0, y: 12 \}, \{ opacity: 1, y: 0, duration: 0\.4")

    def test_accent_words_take_the_accent_in_the_hero_face(self):
        r, d = compose(self, with_headline(self.H))
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        c = E.theme(TOK, "mantle")
        self.assertRegex(page, r'<span class="hl-w" style="color:%s">BATTERY</span>' % c["accent"])     # upper case by default
        self.assertIn(E.hero()["css"], page)
        self.assertRegex(page, r'class="hl-aside"[^>]*>seriously\?<')

    def test_a_headline_that_leaves_no_room_fails(self):
        import copy
        b = with_headline(dict(self.H, text="A very long headline that wraps onto three whole lines here", aside=None, aside_at=None, accent=[]))
        b["scenes"][1] = dict(b["scenes"][1], type="stack", items=[{"label": "Layer " + "ABCDE"[i], "at": "word:%d" % (9 + i)} for i in range(5)])
        for k in ("n", "name"):
            b["scenes"][1].pop(k, None)
        r, _ = compose(self, b)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E3 FAIL: n1: the headline leaves", r.stdout)
        self.assertIn("shorten the headline or drop an item", r.stdout)

    def test_a_headline_too_long_for_three_lines_fails_naming_it(self):
        import headline
        errs = headline.validate({"text": " ".join(["Extraordinarily"] * 9)})
        self.assertTrue(any("three lines" in e for e in errs), errs)
        self.assertEqual(headline.validate(self.H), [])
        self.assertTrue(headline.validate({"text": "x", "accent": ["y"]}))       # an accent word must be in the text

    def test_a_short_headline_takes_one_line_while_it_stays_big(self):
        # fewer lines first: "NO BATTERY" on one line at about 100 px reads better than two lines at 120
        import headline
        E.use_look(E.load_tokens(look="paper"))
        try:
            lay = headline.layout({"text": "No battery"})
            self.assertEqual(len(lay["lines"]), 1)
            self.assertGreaterEqual(lay["size"], 88)
            lay = headline.layout({"text": "Your phone powers everything"})
            self.assertLessEqual(len(lay["lines"]), 3)
        finally:
            E.use_look(E.load_tokens())

    def test_headline_text_is_never_under_28_px(self):
        import headline
        lay = headline.layout({"text": " ".join(["Considerable"] * 3), "kicker": "K"}, 950)
        self.assertGreaterEqual(lay["size"], 64)
        self.assertGreaterEqual(headline.KICKER, 28)


class HeroFace(unittest.TestCase):
    def test_a_latte_stat_keeps_its_size(self):
        # the sizes down to 150 are for the wide hero face; a latte figure too wide for the narrow column at 200 still
        # takes the full width at its own size, as before the paper look
        from scenes import REGISTRY
        stat = REGISTRY["stat"]
        long = {"type": "stat", "value": 25000, "prefix": "$", "label": "the median cost of one data breach"}
        E.use_look(E.load_tokens())
        self.assertEqual(stat.size(long), 210)
        self.assertEqual(stat.size({"type": "stat", "value": 8, "unit": "HOURS"}), 260)
        try:
            E.use_look(E.load_tokens(look="paper"))
            self.assertGreaterEqual(stat.size(long), 150)
            self.assertLessEqual(stat.line_width(long, stat.size(long)), stat.WIDE)
        finally:
            E.use_look(E.load_tokens())

    HOOK = {"type": "kinetic", "id": "hk", "bg": "base", "in": "word:0", "out": "word:8", "big": {"text": "5", "at": "word:0"},
            "words": [{"text": "STEPS", "at": "word:1"}], "line": {"text": "AI GUESSES", "at": "word:1"}, "source": "s1"}

    def board(self, look):
        import copy
        b = copy.deepcopy(BOARD)
        b["scenes"] = [dict(self.HOOK), dict(b["scenes"][1], **{"in": "word:8"}), b["scenes"][2]]
        b["look"] = look
        return b

    def test_the_big_words_take_the_paper_hero_face(self):
        from scenes import REGISTRY
        r, d = compose(self, self.board("paper"))
        self.assertEqual(r.returncode, 0, r.stdout)
        page = read(os.path.join(d, "public", "index.html"))
        rule = re.search(r"\n  ([^{}\n]+) \{ font-family:'Archivo'; font-stretch:125%; font-weight:800; \}", page)
        self.assertIsNotNone(rule, page[:3000])
        for t in ("kinetic", "giant-captions", "title-card", "stat"):
            self.assertTrue(REGISTRY[t].HERO_CSS)
        self.assertEqual(rule.group(1), REGISTRY["kinetic"].HERO_CSS)       # the selectors of the scenes on this page only

    def test_a_title_cards_widest_word_is_measured_in_the_hero_face(self):
        # the composer never gives a scene less than its min_width: in paper the title's widest word is wider
        from scenes import REGISTRY
        tc = REGISTRY["title-card"]
        sc = {"type": "title-card", "kicker": "STEP 3", "title": "Build the three statements"}
        latte = tc.min_width(sc)
        E.use_look(E.load_tokens(look="paper"))
        try:
            paper = tc.min_width(sc)
            word = E.text_width("STATEMENTS".lower(), tc.T_SIZE, "wide800", spacing=tc.T_TRACK)
        finally:
            E.use_look(E.load_tokens())
        self.assertGreater(paper, latte)
        self.assertGreaterEqual(paper, word)

    def test_latte_pages_carry_no_hero_rule(self):
        r, d = compose(self, self.board("latte"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("font-stretch:125%", read(os.path.join(d, "public", "index.html")))

    def test_the_scenes_measure_with_the_hero_glyphs(self):
        # a kinetic hook in the wide face takes more room than in DM Sans: its rows are measured in the face it is set in
        from scenes import REGISTRY
        kn = REGISTRY["kinetic"]
        sc = dict(self.HOOK)
        latte = kn.min_width(sc)
        E.use_look(E.load_tokens(look="paper"))
        try:
            self.assertGreater(kn.min_width(sc), latte)
            tc = REGISTRY["title-card"]
            long = {"type": "title-card", "title": "Retrieval augmented generation explained", "kicker": "THE FIX"}
            paper_h = tc.height(long, 780)
        finally:
            E.use_look(E.load_tokens())
        self.assertGreaterEqual(paper_h, tc.height(long, 780))


class Planner(unittest.TestCase):
    def plan(self, script):
        from .test_plan import Plan
        return Plan.plan(self, script)

    def test_a_headline_hint_lands_on_its_words(self):
        import copy
        from .test_plan import SCRIPT
        script = copy.deepcopy(SCRIPT)
        script["lines"][1]["viz"]["headline"] = {"text": "Three moves", "at": "retrieves,", "aside_at": "generates."}
        _, sb, words = self.plan(script)
        flow = next(s for s in sb["scenes"] if s["type"] == "flow")
        h = flow["headline"]
        self.assertEqual(words[int(h["at"].split(":")[1])]["text"], "retrieves,")
        self.assertEqual(words[int(h["aside_at"].split(":")[1])]["text"], "generates.")

    def test_a_strike_written_as_a_word_lands_on_it(self):
        # crossed-list and line-art strike on a word: the Writer names it, the planner anchors it
        import copy
        from .test_plan import SCRIPT
        script = copy.deepcopy(SCRIPT)
        script["lines"][1]["viz"] = {"type": "crossed-list", "prefix": "NO", "items": [{"text": "RETRIEVE", "at": "retrieves,", "strike": "augments,"},
                                                                                       {"text": "GENERATE", "at": "then", "strike": "generates."}]}
        _, sb, words = self.plan(script)
        cl = next(s for s in sb["scenes"] if s["type"] == "crossed-list")
        self.assertEqual([words[int(it["strike"].split(":")[1])]["text"] for it in cl["items"]], ["augments,", "generates."])

    def test_a_thread_in_the_script_reaches_the_storyboard(self):
        # the Writer names the words; the planner anchors each key, in order, across the whole voice
        import copy
        from .test_plan import SCRIPT
        script = copy.deepcopy(SCRIPT)
        script["thread"] = {"color": "accent", "keys": [{"at": "The", "shape": "drop"}, {"at": "augments,", "shape": "loop", "y": 900},
                                                        {"at": "prompt.", "shape": "off"}]}
        _, sb, words = self.plan(script)
        keys = sb["thread"]["keys"]
        self.assertEqual([words[int(k["at"].split(":")[1])]["text"] for k in keys], ["The", "augments,", "prompt."])
        self.assertEqual(sb["thread"]["color"], "accent")
        self.assertEqual(keys[1]["y"], 900)


if __name__ == "__main__":
    unittest.main()
