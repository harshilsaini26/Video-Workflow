"""The sound scenes (group E2): waveform, mode-switch, and the line-chart's step shape. A waveform that scrolls for the
scene's whole life and changes its shape on the voice's words; a segmented control whose pill slides to the mode the
voice names, the wave under it taking that mode's shape; a chart drawn as steps. Each one refuses bad data with a reason,
lands its items on their words, draws the same picture on every render, and composes clean (E5) on every ground of both
looks."""
import copy, hashlib, importlib, importlib.util, json, os, re, tempfile, unittest
from .helpers import SCRIPTS, read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY, Ctx

W = lambda i: "word:%d" % i
TOK = E.load_tokens()
T_IN = round(t_word(4) - E.LEAD, 3)        # the scene's in (word 4)

GOOD = {
    "waveform": {"type": "waveform", "color": "accent", "states": [
        {"kind": "noise", "label": "THE STREET", "at": W(5)},
        {"kind": "calm", "label": "NOISE CANCELLING ON", "at": W(10)},
        {"kind": "music", "label": "JUST THE MUSIC", "at": W(15)}]},
    "mode-switch": {"type": "mode-switch", "options": [
        {"label": "QUIET", "wave": "calm", "note": "The street goes away", "at": W(5)},
        {"label": "AWARE", "wave": "noise", "note": "You hear the traffic again", "at": W(10)},
        {"label": "IMMERSE", "wave": "music", "note": "Just the music, all around you", "at": W(15)}]},
}
ANCHORED = {"waveform": 3, "mode-switch": 3}
KINDS = ("noise", "calm", "music", "pulse", "flat")


def at_minus_lead(i):
    return round(t_word(i) - E.LEAD, 3)


def scene_js(html, sid="sc"):
    """The scene's own timeline lines: from its comment to the next scene's (or the end of the script)."""
    m = re.search(r"// %s \([\w-]+\) [\d.]+ to [\d.]+ s\n(.*?)(?=\n\s*// \w+ \(|</script>)" % sid, html, re.S)
    return m.group(1) if m else ""


class Case(unittest.TestCase):
    def build(self, scene, bg="mantle", look=None):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": bg, "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **scene)
        board = dict({"id": "t", "scenes": [lead, sc], "sound": {"music": "none", "sfx": False}}, **({"look": look} if look else {}))
        sp = write(os.path.join(d, "storyboard.json"), board)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else ""), out

    def ok(self, scene, bg="mantle", look=None):
        r, html, _ = self.build(scene, bg, look)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html

    def fails(self, scene, text):
        r, _, _ = self.build(scene)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)


class Shared(Case):
    def test_every_type_is_found(self):
        for t in GOOD:
            self.assertIn(t, REGISTRY)

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            html = self.ok(sc)
            body = html.split('id="host-sc"')[1].split('id="captions"')[0]
            got = re.findall(r'data-at="([\d.]+)" data-anchor="word(\d+)"', body)
            self.assertEqual(len(got), ANCHORED[t], t)
            for at, w in got:
                self.assertAlmostEqual(float(at), at_minus_lead(int(w)), places=3)

    def test_every_ground_of_both_looks(self):
        for t, sc in GOOD.items():
            for look in ("latte", "paper"):
                for bg in ("mantle", "base", "blue", "ink"):
                    html = self.ok(sc, bg, look)
                    self.assertNotRegex(html.split('id="host-sc"')[1], r"repeat:|yoyo|Math\.random|Date\(|Date\.now", (t, look, bg))

    def test_an_item_outside_the_scene_fails(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            (bad["states"] if t == "waveform" else bad["options"])[0]["at"] = W(2)
            self.fails(bad, "outside the scene")

    def test_items_move_forward_in_time(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            key = "states" if t == "waveform" else "options"
            bad[key][0]["at"], bad[key][1]["at"] = W(10), W(5)
            self.fails(bad, "forward in time")

    def test_cases_are_valid_and_fit_the_area(self):
        spec = importlib.util.spec_from_file_location("cases_e2", os.path.join(SCRIPTS, "dev", "cases_e2.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(set(mod.CASES), set(GOOD))
        for t, variants in mod.CASES.items():
            self.assertGreaterEqual(len(variants), 3, t)
            for name, data in variants:
                self.assertEqual(REGISTRY[t].validate(data), [], (t, name))
                self.assertLessEqual(REGISTRY[t].height(data, 780), 600, (t, name))

    def test_measured(self):
        with open(os.path.join(SCRIPTS, "tests", "fixtures", "heights-e2.json"), encoding="utf-8") as f:
            rows = json.load(f)
        for t in GOOD:
            mine = [r for r in rows if r["type"] == t]
            self.assertGreaterEqual(len({r["case"] for r in mine}), 3, t)
            self.assertEqual({r["width"] for r in mine}, {950, 780}, t)

    def test_text_is_28_px_or_more(self):
        for t in GOOD:
            sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", REGISTRY[t].CSS)]
            self.assertTrue(sizes and min(sizes) >= 28, t)

    def test_no_hex_colours_and_no_clock_or_dice_in_the_modules(self):
        for name in ("waveform", "mode_switch", "_wave"):
            with open(os.path.join(SCRIPTS, "scenes", "%s.py" % name), encoding="utf-8") as f:
                src = f.read()
            self.assertNotRegex(src, r"#[0-9A-Fa-f]{6}\b", name)
            self.assertNotRegex(src, r"Math\.random|Date\.now|new Date|performance\.now", name)

    def test_both_scenes_share_one_wave(self):
        # the path code lives in scenes/_wave.py; both modules draw through it
        for name in ("waveform", "mode_switch"):
            with open(os.path.join(SCRIPTS, "scenes", "%s.py" % name), encoding="utf-8") as f:
                self.assertRegex(f.read(), r"from scenes import _wave|from scenes\._wave import|import scenes\._wave", name)
        for t, sc in GOOD.items():
            js = scene_js(self.ok(sc))
            self.assertIn("const sc_wv_draw = function", js, t)
            self.assertIn("for (let i = 0; i < 200; i++)", js, t)            # 200 points

    def test_the_picture_is_the_same_on_every_render(self):
        # seeded: the noise table is written into the page by Python, so two composes give the same page
        for t, sc in GOOD.items():
            a, b = self.ok(sc), self.ok(sc)
            self.assertEqual(a, b, t)
            table = re.search(r"const sc_wv_T = \[([-\d., ]+)\];", a)
            self.assertIsNotNone(table, t)
            vals = [float(v) for v in table.group(1).split(",")]
            self.assertGreaterEqual(len(vals), 128)
            self.assertTrue(all(-1 <= v <= 1 for v in vals))
            self.assertGreater(len(set(vals)), len(vals) // 2)                 # noise, not a constant

    def test_the_wave_scrolls_for_the_whole_scene(self):
        # one linear tween of the phase from the scene's in to its out; ambient (idle motion), so never a change for E4
        for t, sc in GOOD.items():
            r, html, out = self.build(sc)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            js = scene_js(html)
            m = re.search(r"tl\.fromTo\(sc_wv, \{ p: 0 \}, \{ p: ([\d.]+), duration: ([\d.]+), ease: 'none', immediateRender: false, "
                          r"onUpdate: sc_wv_draw \}, ([\d.]+)\);", js)
            self.assertIsNotNone(m, t)
            self.assertAlmostEqual(float(m.group(3)), T_IN, places=3)
            self.assertAlmostEqual(float(m.group(2)), round(D - T_IN, 3), places=3)
            self.assertGreater(float(m.group(1)), 100)                          # it really travels
            with open(os.path.join(out, "moments.json"), encoding="utf-8") as f:
                spans = json.load(f)["spans"]
            self.assertNotIn([T_IN, round(D, 3)], spans, t)

    def test_shapes_change_on_their_words_without_overshoot(self):
        for t, sc in GOOD.items():
            js = scene_js(self.ok(sc))
            items = sc["states"] if t == "waveform" else sc["options"]
            for k, it in enumerate(items):
                kind = it["kind"] if t == "waveform" else it["wave"]
                w = KINDS.index(kind)
                when = at_minus_lead(int(it["at"].split(":")[1]))
                m = re.search(r"tl\.fromTo\(sc_wv, \{[^}]*\}, \{([^}]*)duration: 0\.6, ease: 'power3\.inOut', immediateRender: false, "
                              r"onUpdate: sc_wv_draw \}, %.3f\);" % when, js)
                self.assertIsNotNone(m, (t, k))
                self.assertIn("w%d: 1" % w, m.group(1), (t, k))
            self.assertNotRegex(js, r"back\.|elastic|bounce", t)


class Waveform(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["waveform"]
        self.fails(dict(sc, states=[]), "1 to 4 states")
        self.fails(dict(sc, states=sc["states"] + [{"kind": "flat", "label": "x", "at": W(18)}] * 2), "1 to 4 states")
        bad = copy.deepcopy(sc)
        bad["states"][1]["kind"] = "loud"
        self.fails(bad, "kind is one of noise, calm, music, pulse, flat")
        bad = copy.deepcopy(sc)
        bad["states"][1]["label"] = "  "
        self.fails(bad, "state 1 has no label")
        bad = copy.deepcopy(sc)
        bad["states"][1]["label"] = "A LABEL FAR TOO LONG TO SIT UNDER A WAVE"
        self.fails(bad, "at most 32 characters")
        bad = copy.deepcopy(sc)
        del bad["states"][2]["at"]
        self.fails(bad, "state 2 has no at")
        self.fails(dict(sc, color="red"), "color is ink or accent")

    def test_one_path_in_the_chosen_colour(self):
        for color in ("ink", "accent"):
            for bg in ("mantle", "ink"):
                html = self.ok(dict(GOOD["waveform"], color=color), bg)
                paths = re.findall(r'<path id="sc-wave"[^>]*stroke="([^"]+)"', html)
                self.assertEqual(paths, [E.theme(TOK, bg)[color]], (color, bg))
        self.ok({"type": "waveform", "states": [{"kind": "pulse", "label": "HEARTBEAT", "at": W(6)}]})   # ink by default

    def test_the_label_crossfades_on_each_state(self):
        js = scene_js(self.ok(GOOD["waveform"]))
        times = [at_minus_lead(i) for i in (5, 10, 15)]
        first = re.search(r"tl\.fromTo\('#sc-l0', \{ opacity: 0[^;]*\}, ([\d.]+)\);", js)
        self.assertAlmostEqual(float(first.group(1)), times[0], places=3)
        for k in (1, 2):
            out = re.search(r"tl\.fromTo\('#sc-l%d', \{ opacity: 1 \}, \{ opacity: 0[^;]*\}, ([\d.]+)\);" % (k - 1), js)
            inn = re.search(r"tl\.fromTo\('#sc-l%d', \{ opacity: 0[^;]*\}, ([\d.]+)\);" % k, js)
            self.assertAlmostEqual(float(out.group(1)), times[k], places=3)
            self.assertGreater(float(inn.group(1)), times[k])          # the old one is gone first: they never overlap
            self.assertLessEqual(float(inn.group(1)) + 0.3, times[k] + 0.5 + 1e-6)

    def test_heights_follow_the_longest_label(self):
        mod = REGISTRY["waveform"]
        one = {"type": "waveform", "states": [{"kind": "calm", "label": "CALM", "at": W(5)}]}
        two = {"type": "waveform", "states": [{"kind": "calm", "label": "CALM", "at": W(5)},
                                              {"kind": "noise", "label": "THE WHOLE STREET COMES BACK", "at": W(9)}]}
        self.assertGreater(mod.height(two, 400), mod.height(one, 400))
        self.assertEqual(mod.height(two, 950), mod.height(one, 950))


class ModeSwitch(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["mode-switch"]
        self.fails(dict(sc, options=sc["options"][:1]), "2 to 4 options")
        self.fails(dict(sc, options=sc["options"] * 2), "2 to 4 options")
        bad = copy.deepcopy(sc)
        bad["options"][1]["wave"] = "loud"
        self.fails(bad, "wave is one of noise, calm, music, pulse, flat")
        bad = copy.deepcopy(sc)
        bad["options"][0]["label"] = ""
        self.fails(bad, "option 0 has no label")
        bad = copy.deepcopy(sc)
        bad["options"][0]["label"] = "TRANSPARENCY"
        self.fails(bad, "at most 10 characters")
        bad = copy.deepcopy(sc)
        del bad["options"][2]["note"]
        self.fails(bad, "option 2 has no note")
        bad = copy.deepcopy(sc)
        del bad["options"][1]["at"]
        self.fails(bad, "option 1 has no at")

    def test_the_pill_slides_under_the_option_on_its_word(self):
        js = scene_js(self.ok(GOOD["mode-switch"]))
        n = 3
        first = re.search(r"tl\.fromTo\('#sc-pill', \{ opacity: 0[^;]*\}, ([\d.]+)\);", js)
        self.assertAlmostEqual(float(first.group(1)), at_minus_lead(5), places=3)
        for k, w in ((1, 10), (2, 15)):
            slide = re.search(r"tl\.fromTo\('#sc-pill', \{ xPercent: ([\d.]+) \}, \{ xPercent: ([\d.]+), duration: 0\.6, "
                              r"ease: 'power3\.inOut', immediateRender: false \}, %.3f\);" % at_minus_lead(w), js)
            self.assertIsNotNone(slide, k)
            self.assertEqual((float(slide.group(1)), float(slide.group(2))), (100.0 * (k - 1), 100.0 * k))
            inner = re.search(r"tl\.fromTo\('#sc-in', \{ xPercent: (-?[\d.]+) \}, \{ xPercent: (-?[\d.]+), duration: 0\.6, "
                              r"ease: 'power3\.inOut', immediateRender: false \}, %.3f\);" % at_minus_lead(w), js)
            self.assertAlmostEqual(float(inner.group(2)), round(-100.0 * k / n, 3), places=3)   # its labels stay put

    def test_the_note_changes_with_the_option(self):
        js = scene_js(self.ok(GOOD["mode-switch"]))
        for k, w in ((1, 10), (2, 15)):
            out = re.search(r"tl\.fromTo\('#sc-n%d', \{ opacity: 1 \}, \{ opacity: 0[^;]*\}, ([\d.]+)\);" % (k - 1), js)
            inn = re.search(r"tl\.fromTo\('#sc-n%d', \{ opacity: 0[^;]*\}, ([\d.]+)\);" % k, js)
            self.assertAlmostEqual(float(out.group(1)), at_minus_lead(w), places=3)
            self.assertGreater(float(inn.group(1)), at_minus_lead(w))

    def test_the_control_is_light_paper_with_mono_labels(self):
        mod = REGISTRY["mode-switch"]
        self.assertRegex(mod.CSS, r"\.ms-o \{[^}]*font-family: var\(--label\)")
        pc = E.theme(TOK, "base")
        for bg in ("mantle", "blue", "ink"):
            html = self.ok(GOOD["mode-switch"], bg)
            self.assertRegex(html, r'class="ms-track"[^>]*style="[^"]*background:%s' % pc["chrome"], bg)
            self.assertRegex(html, r'id="sc-pill"[^>]*style="[^"]*background:%s' % pc["accent"], bg)
            self.assertRegex(html, r'class="ms-o ms-on"[^>]*style="[^"]*color:%s' % pc["on_accent"], bg)

    def test_the_longest_row_takes_the_full_width(self):
        # four options of ten characters: wider than the narrow column, so the control is laid out on the full width
        sc = {"type": "mode-switch", "options": [{"label": "IMMERSIVES", "wave": "music", "note": "All of it", "at": W(5 + 2 * k)}
                                                 for k in range(4)]}
        need = REGISTRY["mode-switch"].min_width(sc)
        self.assertGreater(need, 780)
        r, _, out = self.build(sc)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(out, "moments.json"), encoding="utf-8") as f:
            box = [s for s in json.load(f)["scenes"] if s["id"] == "sc"][0]["box"]
        self.assertGreaterEqual(box[2], need)


class StepChart(Case):
    BASE = {"type": "line-chart", "id": "sc", "points": [100, 114, 152, 214, 265], "x": ["Y0", "Y5", "Y10", "Y15", "Y20"],
            "prefix": "$", "label": "VALUE OF $100", "source": "s", "reveal": [{"point": 2, "at": W(6)}, {"point": 4, "at": W(10)}]}
    # the default line's render (html and timeline) before the step shape existed, at a fixed box
    GOLDEN = {"mantle": "3d7244c720a54dd6d762d50c58c0af597305638b725fb08fe5491686e90a7b92",
              "ink": "c6eec2af6470e1b98d937c9678c8feff7d9006ea81c3f45ec18ca8c7afa2cfc9",
              "plain": "fcdeda7a28518bab7a6b8d62ce4a8faf0518e40120ca65bbde67921f2c17ed4d"}

    def render(self, sc, bg="mantle"):
        d = tempfile.mkdtemp(prefix="explainer-test-")
        self.addCleanup(__import__("shutil").rmtree, d, True)
        ctx = Ctx(sc, 1.9, D, words30(), TOK, d, d, bg)
        h, js = REGISTRY["line-chart"].render(sc, ctx, (150, 400, 780))
        return h + "\n" + "\n".join(js)

    def digest(self, s):
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def test_the_default_line_is_unchanged(self):
        for bg in ("mantle", "ink"):
            self.assertEqual(self.digest(self.render(copy.deepcopy(self.BASE), bg)), self.GOLDEN[bg], bg)
        plain = {"type": "line-chart", "id": "sc", "points": [3, 1, 4, 1, 5, 9], "x": list("abcdef"), "source": "s"}
        self.assertEqual(self.digest(self.render(plain, "base")), self.GOLDEN["plain"])
        self.assertEqual(self.render(dict(self.BASE, shape="line")), self.render(copy.deepcopy(self.BASE)))

    def test_bad_shape_says_why(self):
        sc = {k: v for k, v in self.BASE.items() if k != "id"}
        self.fails(dict(sc, shape="curve"), "shape is line or step")

    def test_steps_are_drawn_on_and_counted(self):
        out = self.render(dict(self.BASE, shape="step"))
        d = re.search(r'<path id="sc-line" d="([^"]+)"', out).group(1)
        self.assertRegex(d, r"^M[\d.]+ [\d.]+( H[\d.]+ V[\d.]+){4}$")
        nums = [tuple(map(float, p)) for p in re.findall(r"([\d.]+) ([\d.]+)", d[1:].split(" H")[0])]
        xs = [float(x) for x in re.findall(r"H([\d.]+)", d)]
        ys = [float(y) for y in re.findall(r"V([\d.]+)", d)]
        x0, y0 = nums[0]
        total = sum(abs(b - a) for a, b in zip([x0] + xs, xs)) + sum(abs(b - a) for a, b in zip([y0] + ys, ys))
        dash = float(re.search(r'stroke-dasharray="([\d.]+)"', out).group(1))
        self.assertAlmostEqual(dash, round(total, 1), places=1)
        self.assertRegex(out, r"tl\.to\('#sc-line', \{ strokeDashoffset: 0(\.0)?, duration")    # drawn on to the end
        self.assertEqual(len(re.findall(r"countUp\('#sc-v'", out)), 2)                           # the readout counts with it
        dots = re.findall(r'id="sc-d(\d)" style="left:([\d.]+)px;top:([\d.]+)px', out)
        self.assertEqual([(float(l), float(t)) for _, l, t in dots][1:], list(zip(xs, ys)))      # the dots sit on the steps

    def test_a_step_chart_composes(self):
        sc = {k: v for k, v in self.BASE.items() if k != "id"}
        self.ok(dict(sc, shape="step"))


def _have_e5():
    try:
        from .test_layout import have_browser
    except Exception:
        return False
    vendor = os.environ.get("EXPLAINER_VENDOR")
    return have_browser() and bool(vendor) and os.path.isdir(os.path.join(vendor, "katex"))


class Clean(unittest.TestCase):
    @unittest.skipUnless(_have_e5(), "needs node, puppeteer, Chrome and the real vendor folder (EXPLAINER_VENDOR)")
    def test_e5_clean_on_every_ground_of_both_looks(self):
        # composed with the real GSAP and looked at in Chromium: once every state or option has settled, and before the exit
        LC = importlib.import_module("layout_check")
        vendor = os.environ["EXPLAINER_VENDOR"]
        root = scratch(self)
        pages = []
        for t, sc in GOOD.items():
            items = sc["states"] if t == "waveform" else sc["options"]
            for look in ("latte", "paper"):
                for bg in ("mantle", "base", "blue", "ink"):
                    d = os.path.join(root, "%s-%s-%s" % (t, look, bg))
                    write(os.path.join(d, "transcript.json"), {"words": words30()})
                    silent_wav(os.path.join(d, "voice.wav"), VOICE)
                    lead = {"type": "title", "id": "lead", "bg": bg, "in": "word:0", "out": "word:4", "text": "Lead in"}
                    sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "look": look, "sound": {"music": "none", "sfx": False},
                                                                    "scenes": [lead, dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **sc)]})
                    r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", vendor)
                    self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                    with open(os.path.join(d, "public", "moments.json"), encoding="utf-8") as f:
                        smp = LC.samples(json.load(f))
                    smp += [{"id": "sc", "t": round(at_minus_lead(int(it["at"].split(":")[1])) + 0.8, 3)} for it in items]
                    pages.append({"index": os.path.join(d, "public", "index.html"), "samples": smp})
        issues = LC.probe_pages(pages)
        self.assertEqual([], ["%s: %s %s %s" % (os.path.basename(os.path.dirname(os.path.dirname(i["page"]))), i["t"], i["text"], i["detail"])
                              for i in issues])


if __name__ == "__main__":
    unittest.main()
