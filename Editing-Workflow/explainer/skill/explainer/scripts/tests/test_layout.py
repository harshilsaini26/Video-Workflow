"""Gate E5, layout-check.py: every scene is checked in Chromium on the creator's machine, at the moment it is fully
built, for text that collides with text or crosses a shape, text that spills out of its card, anything outside the
safe area, and text too small to read on a phone; HyperFrames' own check adds overlap, clipping and WCAG contrast."""
import json, os, shutil, subprocess, unittest
from .helpers import SCRIPTS, run, scratch, write

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
        }
        for word, body in cases.items():
            r = self.check(body)
            self.assertNotEqual(r.returncode, 0, "%s: %s" % (word, r.stdout))
            self.assertIn("E5 FAIL: sc:", r.stdout, word)
            self.assertIn(word, r.stdout, word)

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


if __name__ == "__main__":
    unittest.main()
