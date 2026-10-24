"""explainer-compose.py: storyboard + transcript + voice -> a kit-compatible HyperFrames page (gate E3)."""
import copy, os, re, unittest, wave
from .helpers import load, needs_kit, read, run, run_kit, scratch, write
import explainer_lib as E
import transitions as X

TOK = E.load_tokens()
STEP, T0 = 0.4, 0.5


def words30(t0=T0):
    texts = ["word%d" % i for i in range(30)]
    texts[3], texts[17] = "NPV,", "npv"
    return [{"text": t, "start": round(t0 + i * STEP, 3), "end": round(t0 + i * STEP + 0.3, 3)} for i, t in enumerate(texts)]


def t_word(i):
    return T0 + i * STEP


VOICE = 12.6
D = VOICE + E.TAIL


def silent_wav(path, seconds):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * int(seconds * 8000))


BOARD = {
    "id": "test-01", "fps": 60, "voice": "voice.wav", "transcript": "transcript.json",
    "captions": {"emphasis": ["NPV"]},
    "scenes": [
        {"type": "title", "id": "hook", "bg": "mantle", "in": "word:0", "out": "word:8",
         "text": "Three certificates nobody tells you about", "kicker": "IF YOU'RE NEW"},
        {"type": "number", "id": "n1", "bg": "mantle", "in": "word:8", "out": "word:18", "n": 1, "name": "Coursera finance"},
        {"type": "count-up", "id": "cu", "bg": "base", "in": "word:18", "out": D, "value": 1000, "prefix": "$",
         "sub": "saved a year", "source": "s1"},
    ],
}


class Compose(unittest.TestCase):
    def build(self, edit=None, script=None, t0=T0):
        d = scratch(self)
        board = copy.deepcopy(BOARD)
        if edit:
            edit(board)
        if script is not None:
            write(os.path.join(d, "script.json"), script)
        write(os.path.join(d, "transcript.json"), {"words": words30(t0)})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), board)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", os.path.join(d, "vendor"))
        page = os.path.join(out, "index.html")
        return r, (read(page) if r.returncode == 0 else ""), page, os.path.join(d, "transcript.json")

    def ok(self, edit=None, **kw):
        r, html, page, tp = self.build(edit, **kw)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html, page, tp

    def fails(self, edit, text):
        r, _, _, _ = self.build(edit)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)
        return r

    def test_a_tail_runs_the_page_past_the_voice(self):
        def edit(b):
            b["tail"] = 1.4
            b["scenes"][2]["out"] = "end"
        html, _, _ = self.ok(edit)
        self.assertIn('data-duration="%.3f" data-fps="60"' % (VOICE + 1.4), html)
        self.fails(lambda b: b.update(tail=9), "tail is the seconds")

    def test_the_last_scene_is_long_enough_for_the_close(self):
        # the close takes its last 0.4 s: a last scene under LAST_MIN would be read inside it (or on its ground)
        def edit(b):
            b["scenes"][1]["out"] = b["scenes"][2]["in"] = round(D - 0.8, 3)
        self.fails(edit, "the last scene runs 0.80 s")

    def test_builds_vertical_60_with_voice_and_kit_markup(self):
        html, page, _ = self.ok()
        self.assertIn('data-fps="60" data-width="1080" data-height="1920"', html)
        self.assertRegex(html, r'<audio id="voice" src="voice.wav" data-start="0" data-duration="%.3f" data-track-index="1" data-volume="1"' % VOICE)   # the clip is the voice's length
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(page), "voice.wav")))
        hosts = re.findall(r'<div class="card-host clip" id="host-([\w-]+)" data-start="([\d.]+)" data-duration="([\d.]+)"[^>]*data-anchor="([^"]*)"', html)
        self.assertEqual([(h[0], h[3]) for h in hosts], [("hook", "word0"), ("n1", "word8"), ("cu", "word18")])
        self.assertAlmostEqual(float(hosts[1][1]), t_word(8) - E.LEAD, places=3)
        self.assertIn('window.__timelines["test-01"]', html)
        self.assertIn('class="clip cap-layer"', html)

    def test_the_brand_and_the_series_part_sit_over_the_captions(self):
        # a visual identity on every frame (the handle) and a series the viewer can follow (PART 2), in the safe area
        def edit(b):
            b["brand"] = {"handle": "@harshil", "series": "RAG in 60 s", "part": 2}
        html, _, _ = self.ok(edit)
        m = re.search(r'<div class="brand" id="brand" style="top:(\d+)px;height:(\d+)px;color:([^"]+)"><span>@harshil</span><span>PART 2</span></div>', html)
        self.assertTrue(m, html[:3000])
        top, h = int(m.group(1)), int(m.group(2))
        self.assertGreaterEqual(top, E.L.SAFE["top"])
        self.assertLessEqual(top + h, E.CAPTION_BAND[0])
        self.assertEqual(m.group(3), E.theme(TOK, "mantle")["muted"])
        html, _, _ = self.ok()
        self.assertNotIn('id="brand"', html)                   # nothing when the storyboard names no brand

    def test_fonts_preloaded(self):
        html, page, _ = self.ok()   # a hidden scene's text would otherwise load its font only when shown, a frame late
        for f in sorted(os.listdir(os.path.join(os.path.dirname(page), "fonts"))):
            self.assertIn('<link rel="preload" href="fonts/%s" as="font" type="font/woff2" crossorigin />' % f, html)

    def test_scene_box_inside_scene_area_both_widths(self):
        html, _, _ = self.ok()
        boxes = [tuple(map(int, b)) for b in re.findall(r'class="box"[^>]*style="left:(\d+)px;top:(\d+)px;width:(\d+)px;height:(\d+)px', html)]
        self.assertEqual(len(boxes), 3)
        narrow = 0
        for left, top, width, height in boxes:
            self.assertGreaterEqual(left, E.SCENE["left"])
            self.assertGreaterEqual(top, E.SCENE["top"])
            self.assertLessEqual(left + width, E.SCENE["right"])
            self.assertLessEqual(top + height, E.SCENE["bottom"])
            self.assertTrue(E.inside_scene(left, top, width, height))
            if top + height > E.L.RIGHT_COL_TOP:
                self.assertEqual((left, width), (150, 780))
                narrow += 1
        self.assertGreater(narrow, 0)

    def test_unbreakable_word_too_wide_fails(self):
        def edit(b):
            b["scenes"][0]["text"] = "A " + "x" * 26
            b["scenes"][0]["size"] = 120
        self.fails(edit, "wider than the")

    def test_uncovered_time_fails(self):
        def hole(b):
            b["scenes"][1]["in"] = "word:11"
        self.fails(hole, "no scene from")

        def late_start(b):
            b["scenes"][0]["in"] = "word:2"
        self.fails(late_start, "no scene from 0.00")

        def early_end(b):
            b["scenes"][2]["out"] = "word:28"
        self.fails(early_end, "no scene from")

    def test_scenes_hand_over_on_one_cut(self):
        # SOP S9: a scene ends where the next begins; any overlap would put two scenes on screen
        n1_in = t_word(8) - E.LEAD

        def wide(b):
            b["scenes"][0]["out"] = round(n1_in + 0.1, 3)
        self.fails(wide, "overlap")

        def snug(b):
            b["scenes"][0]["out"] = round(n1_in, 3)
        self.ok(snug)

    def test_last_out_can_be_end(self):
        def edit(b):
            b["scenes"][2]["out"] = "end"
        html, _, _ = self.ok(edit)
        cu = re.search(r'id="host-cu" data-start="([\d.]+)" data-duration="([\d.]+)"', html)
        self.assertAlmostEqual(float(cu.group(1)) + float(cu.group(2)), D, places=3)

        def early(b):
            b["scenes"][1]["out"] = "end"
        self.fails(early, "n1:")

    def test_anchor_order_errors_name_the_scene(self):
        def backwards(b):
            b["scenes"][1]["out"] = "word:4"
        self.fails(backwards, "n1:")

        def missing(b):
            b["scenes"][1]["in"] = "word:99"
        r = self.fails(missing, "n1:")
        self.assertIn("word:99", r.stdout + r.stderr)

    def test_emphasis_matches_normalised_and_repeated(self):
        html, _, _ = self.ok()
        self.assertEqual(len(re.findall(r'class="cw em"', html)), 2)

    def test_background_crossfades_on_change(self):
        def edit(b):
            b["scenes"][1]["bg"] = "base"
            b["scenes"][1]["transition"] = "push"     # a named transition other than wipe keeps the cross-fade
        html, _, _ = self.ok(edit)
        self.assertEqual(len(re.findall(r'class="bg"', html)), 3)      # and the close's, back onto the hook's ground
        fades = re.findall(r"tl\.to\('#bg(\d+)', \{ opacity: 1, duration: ([\d.]+)[^;]*\}, ([\d.]+)\);", html)
        self.assertEqual(len(fades), 1)
        self.assertEqual(fades[0][0], "1")
        self.assertAlmostEqual(float(fades[0][1]), E.BG_FADE)
        self.assertAlmostEqual(float(fades[0][2]), t_word(8) - E.LEAD, places=3)

    def test_count_up_needs_a_source(self):
        def edit(b):
            del b["scenes"][2]["source"]
        self.fails(edit, "cu: ")

    @needs_kit
    def test_caption_layer_is_excluded_by_gap_scan(self):
        _, page, _ = self.ok()
        r = run_kit("gap-scan.py", "--index", page)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 overlay(s)", r.stdout)

    @needs_kit
    def test_kit_beat_check_passes(self):
        _, page, tp = self.ok()
        r = run_kit("beat-check.py", "--index", page, "--transcript", tp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 checked, 0 problem(s)", r.stdout)

    def test_motion_rules(self):
        html, _, _ = self.ok()
        m = TOK["motion"]
        tweens = re.findall(r"^\s*(tl\.(?:fromTo|to)\(.*\);)\s*$", html, re.M)
        self.assertTrue(tweens)
        entrances = exits = 0
        for tw in tweens:
            if re.search(r"ease: 'none'", tw) and re.search(r"\b(x|y|scale): ", tw) and not re.match(r"tl\.fromTo\('#(bg\d+-p\d+|\w+-cam)'", tw):
                # (the background's particles and the camera drift at a constant speed: an ambient drift, not a move with a
                # start and an end)
                self.fail("linear easing on movement: " + tw)
            if tw.startswith("tl.fromTo(") and re.search(r"^tl\.fromTo\([^{]*\{ opacity: 0[,} ]", tw):
                entrances += 1
                self.assertIn("ease: '%s'" % m["enter_ease"], tw)
            elif tw.startswith("tl.to(") and re.search(r"\{ opacity: 0[,} ]", tw):   # to 0, not to 0.4
                exits += 1
                self.assertIn("ease: '%s'" % m["exit_ease"], tw)
                self.assertLessEqual(float(re.search(r"duration: ([\d.]+)", tw).group(1)), E.EXIT if exits <= 2 else X.CLOSE)
        self.assertGreaterEqual(entrances, 3)
        self.assertEqual(exits, 3)          # the last scene leaves too: the close, over the last 0.4 s
        self.assertNotRegex(html, r"stagger: [\d.]")
        for amount in re.findall(r"stagger: \{ amount: ([\d.]+)", html):
            self.assertLessEqual(float(amount), m["stagger_total_max"])

    def test_any_number_on_screen_needs_a_source(self):
        def edit(b):
            b["scenes"][0]["text"] = "Save $1,000 a year"
        self.fails(edit, "hook: ")

        def sourced(b):
            b["scenes"][0]["text"] = "Save $1,000 a year"
            b["scenes"][0]["source"] = "s1"
        self.ok(sourced)

    def test_source_keys_checked_against_the_script(self):
        def edit(b):
            b["scenes"][2]["source"] = "zzz"
        r, _, _, _ = self.build(edit, script={"sources": {"s1": "a page"}})
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("zzz", r.stdout + r.stderr)
        r, _, _, _ = self.build(None, script={"sources": {"s1": "a page"}})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_item_on_the_first_word_with_an_early_voice(self):
        def edit(b):
            b["scenes"][0] = {"type": "qa-stack", "id": "hook", "bg": "mantle", "in": "word:0", "out": "word:8",
                              "items": [{"text": "Is it cheap?", "at": "word:0"}]}
        self.ok(edit, t0=0.1)

    def test_reserved_and_hyphenated_ids_fail(self):
        for bad in ("stage", "captions", "voice", "bg1", "cap2", "a-v"):
            def edit(b, bad=bad):
                b["scenes"][1]["id"] = bad
            self.fails(edit, bad)

    def test_json_numbers_on_screen_need_a_source(self):
        def edit(b):
            b["scenes"][1] = {"type": "sheet", "id": "n1", "bg": "mantle", "in": "word:8", "out": "word:18",
                              "rows": [["Year", "Revenue"], [2023, 1500000]]}
        self.fails(edit, "n1: ")

        def step(b):
            b["scenes"][1]["n"] = "1"     # a step number, not a claim
        self.ok(step)

    def test_bad_values_fail_with_the_scene_named(self):
        for key, val in (("decimals", "one"), ("value", None)):
            def edit(b, key=key, val=val):
                b["scenes"][2][key] = val
            r = self.fails(edit, "E3 FAIL: cu: ")
            self.assertNotIn("Traceback", r.stdout + r.stderr)

        def size(b):
            b["scenes"][0]["size"] = "big"
        r = self.fails(size, "E3 FAIL: hook: ")
        self.assertNotIn("Traceback", r.stdout + r.stderr)
