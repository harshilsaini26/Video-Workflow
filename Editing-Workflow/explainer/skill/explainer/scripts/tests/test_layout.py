"""Gate E5, layout-check.py: every scene is checked in Chromium on the creator's machine, at the moment it is fully
built, for text that collides with text or crosses a shape, text that spills out of its card, anything outside the
safe area, and text too small to read on a phone; HyperFrames' own check adds overlap, clipping and WCAG contrast."""
import json, os, shutil, subprocess, unittest
from .helpers import SCRIPTS, run, scratch, write
import explainer_lib as E

LC = __import__("importlib").import_module("layout_check") if os.path.exists(os.path.join(SCRIPTS, "layout_check.py")) else None
NODE = shutil.which("node")
PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
  html, body { margin:0; } #stage { position:relative; width:1080px; height:1920px; background:#e6e9ef; font-family:sans-serif; }
  .card-host { position:absolute; left:0; top:0; width:1080px; height:1920px; visibility:hidden; }
  .box { position:absolute; } .card { position:absolute; background:#eff1f5; border-radius:20px; padding:0 20px; height:80px;
  display:flex; align-items:center; font-size:44px; font-weight:700; color:#4c4f69; white-space:nowrap; }
</style></head><body><div id="stage" data-composition-id="t" data-duration="4">
<div class="card-host" id="host-sc" data-start="0" data-duration="4"><div class="box" id="sc" style="left:150px;top:600px;width:780px;height:700px">
%s</div></div></div>
<script>window.__timelines = {"t": {"seek": function () {}}};</script></body></html>"""
CLEAN = '<div class="card" style="left:0;top:0;width:360px">Search</div><div class="card" style="left:400px;top:0;width:360px">Answer</div>'


def have_browser():
    if not (NODE and LC):
        return False
    try:
        return LC.find_puppeteer() is not None and LC.find_chrome() is not None
    except Exception:
        return False


class Gate(unittest.TestCase):
    def check(self, body):
        d = scratch(self)
        pub = os.path.join(d, "public")
        write(os.path.join(pub, "index.html"), PAGE % body)
        write(os.path.join(pub, "moments.json"), {"duration": 4, "scenes": [{"id": "sc", "type": "x", "in": 0, "out": 4}], "spans": []})
        return run("layout-check.py", "--index", os.path.join(pub, "index.html"), "--no-hf")

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
    def test_a_clean_scene_passes(self):
        r = self.check(CLEAN)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("E5 PASS", r.stdout)

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
    def test_each_defect_fails_naming_the_scene_and_the_text(self):
        cases = {
            "overlaps": '<div class="card" style="left:0;top:0;width:360px">Search</div>'
                        '<div class="card" style="left:120px;top:20px;width:360px">Answer</div>',
            "spills out of": '<div class="card" style="left:0;top:0;width:150px;overflow:visible">Supercalifragilistic</div>',
            "outside the safe area": '<div class="card" style="left:0;top:880px;width:360px">Answer</div>',
            "crosses": '<svg style="position:absolute;left:0;top:0" width="780" height="300"><line x1="0" y1="245" x2="780" y2="245" '
                       'stroke="#1e66f5" stroke-width="8"/></svg><div style="position:absolute;left:100px;top:210px;font-size:60px;'
                       'color:#4c4f69;font-weight:700">Answer</div>',
            "too small": '<div class="card" style="left:0;top:0;width:360px;font-size:18px">Answer</div>',
            "contrast": '<div class="card" style="left:0;top:0;width:360px;background:#1e66f5;color:#7287fd">Answer</div>',
        }
        for word, body in cases.items():
            r = self.check(body)
            self.assertNotEqual(r.returncode, 0, "%s: %s" % (word, r.stdout))
            self.assertIn("E5 FAIL: sc:", r.stdout, word)
            self.assertIn(word, r.stdout, word)

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
    def test_text_and_cards_end_by_1235_and_bare_shapes_by_1650(self):
        # SOP S7: one bottom limit for anything with words on it; a shape with no text may use the lower frame
        r = self.check('<div class="card" style="left:0;top:600px;width:360px">Answer</div>')       # y 1200 to 1280
        self.assertIn("outside the safe area", r.stdout)
        r = self.check('<div style="position:absolute;left:0;top:960px;width:300px;height:40px;background:#7287fd"></div>')
        self.assertEqual(r.returncode, 0, r.stdout)                                                  # y 1560 to 1600
        r = self.check('<div style="position:absolute;left:0;top:1060px;width:300px;height:40px;background:#7287fd"></div>')
        self.assertIn("outside the safe area", r.stdout)                                             # y 1660 to 1700

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
    def test_two_scenes_on_screen_at_a_cut_fail(self):
        # SOP S9: the old scene is gone by the cut; if both show above 30% at once, the handover fails
        card = '<div class="box" id="%s" style="left:150px;top:600px;width:780px;height:300px"><div class="card" style="left:0;top:0;width:360px">%s</div></div>'
        host = ('<div class="card-host" id="host-%s" data-start="%s" data-duration="%s">%s</div>')
        for a_dur, ok in (("2.2", False), ("2.0", True)):
            d = scratch(self)
            pub = os.path.join(d, "public")
            body = host % ("sa", "0", a_dur, card % ("sa", "Search")) + host % ("sb", "2.0", "2.0", card % ("sb", "Answer"))
            write(os.path.join(pub, "index.html"), (PAGE % "").replace(
                '<div class="card-host" id="host-sc" data-start="0" data-duration="4"><div class="box" id="sc" style="left:150px;top:600px;width:780px;height:700px">\n</div></div>', body))
            write(os.path.join(pub, "moments.json"), {"duration": 4, "scenes": [{"id": "sa", "type": "x", "in": 0, "out": 2.0},
                                                                                  {"id": "sb", "type": "x", "in": 2.0, "out": 4.0}], "spans": []})
            r = run("layout-check.py", "--index", os.path.join(pub, "index.html"), "--no-hf")
            if ok:
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            else:
                self.assertIn("E5 FAIL: sb:", r.stdout)
                self.assertIn("both on screen", r.stdout)

    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
    def test_every_scene_case_is_clean(self):
        # every library scene, three lengths of text each (dev/make-cases.py), composed and looked at in Chromium
        self.every_case("latte")

    def test_every_scene_case_is_clean_on_paper(self):
        # and in the editorial look: its colours on its grounds
        self.every_case("paper")

    def test_every_scene_case_is_clean_in_each_palette(self):
        # the five palettes (colour only), on paper: its texture darkens the base ground, the harder case for contrast
        for name in E.PALETTES:
            with self.subTest(palette=name):
                self.every_case("paper", name)

    def every_case(self, look, palette=None):
        from .test_theme import make_cases
        from .test_assets import COURSERA, png
        from .test_scenes_ui import stub_vendor
        from .test_compose import silent_wav
        mc = make_cases()
        root = scratch(self)
        vendor = os.environ.get("EXPLAINER_VENDOR")
        if not vendor or not os.path.isdir(os.path.join(vendor, "katex")) or not os.path.isdir(os.path.join(vendor, "lucide")):
            self.skipTest("needs the real vendor folder (EXPLAINER_VENDOR: gsap, katex, lucide, simple-icons)")
        pages = []
        for typ, variants in sorted(mc.CASES.items()):
            for name, data in variants:
                d = os.path.join(root, "%s-%s" % (typ, name))
                write(os.path.join(d, "transcript.json"), {"words": [{"text": "word%d" % i, "start": 0.5 + i * 0.4, "end": 0.8 + i * 0.4}
                                                                      for i in range(40)]})
                silent_wav(os.path.join(d, "voice.wav"), 15.5)
                for rel, w, h in mc.images(data):           # every src anywhere in the data (photos[].src too)
                    png(os.path.join(d, rel), w, h)
                bg = ("mantle", "blue", "base", "ink")[(len(pages) + 1) % 4]     # every scene type meets the dark grounds too
                sc = dict({"type": typ, "id": "sc", "bg": bg, "in": "word:1", "out": 16.0}, **data)
                sb = {"id": "t", "look": look, "scenes": [mc.LEAD_IN, sc], "sound": {"music": "none", "sfx": False}}
                if palette:
                    sb["palette"] = palette
                sp = write(os.path.join(d, "storyboard.json"), sb)
                r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", vendor)
                self.assertEqual(r.returncode, 0, "%s-%s: %s" % (typ, name, r.stdout))
                with open(os.path.join(d, "public", "moments.json"), encoding="utf-8") as f:
                    pages.append({"index": os.path.join(d, "public", "index.html"), "samples": LC.samples(json.load(f))})
        issues = LC.probe_pages(pages)
        self.assertEqual([], ["%s %s: %s %s" % (look, os.path.basename(os.path.dirname(os.path.dirname(i["page"]))), i["text"], i["detail"])
                              for i in issues])

    def test_a_page_not_composed_yet_is_named(self):
        d = scratch(self)
        write(os.path.join(d, "public", "index.html"), "<html></html>")
        r = run("layout-check.py", "--index", os.path.join(d, "public", "index.html"), "--no-hf")
        self.assertEqual(r.returncode, 2)
        self.assertIn("compose", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_hyperframes_findings_that_matter_are_kept(self):
        self.assertTrue(LC, "layout_check.py is missing")
        report = {"layout": {"issues": [
            {"code": "content_overlap", "severity": "info", "time": 2.0, "selector": "#sc-n1", "text": "Rank"},
            {"code": "contrast_aa_failure", "severity": "warning", "time": 2.0, "selector": "#cw3-1", "text": "and",
             "message": "Contrast is 2.1:1; WCAG AA requires 3:1."},
            {"code": "container_overflow", "severity": "info", "time": 2.0, "selector": "#bg0-o1"},
            {"code": "nested_structure_needs_subcomposition", "severity": "warning", "selector": "#host-sc"},
            {"code": "clipped_text", "severity": "info", "time": 2.0, "selector": "div.br-url", "text": "notes / team"}]}}
        kept = LC.hf_findings(report, [{"id": "sc", "in": 0.0, "out": 4.0}])
        self.assertEqual([k["code"] for k in kept], ["content_overlap", "contrast_aa_failure", "clipped_text"])
        self.assertEqual(kept[0]["scene"], "sc")
        self.assertEqual(kept[1]["scene"], "captions")
        # at a handover the old scene leaves through the new one for 0.2 s: two scenes' text crossing then is the cut,
        # not a collision; the same overlap inside one scene, or long after a cut, still fails
        scenes = [{"id": "a", "in": 0.0, "out": 4.0}, {"id": "b", "in": 4.0, "out": 8.0}]
        cross = {"code": "content_overlap", "severity": "info", "selector": "#a-c1", "containerSelector": "#b-c", "text": "x"}
        report = {"layout": {"issues": [dict(cross, time=4.1), dict(cross, time=6.0),
                                         dict(cross, time=4.1, containerSelector="#a-c2"),
                                         dict(cross, time=4.2, selector="#cw3-1", containerSelector="#b-c")]}}
        kept = LC.hf_findings(report, scenes)
        self.assertEqual([k["time"] for k in kept], [6.0, 4.1])


if __name__ == "__main__":
    unittest.main()
