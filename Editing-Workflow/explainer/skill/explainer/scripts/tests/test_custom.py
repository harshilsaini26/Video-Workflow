"""The custom scene contract (SPEC §6.4): Claude-written markup and animation, kept inside its own box and offline."""
import os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
import explainer_lib as E

GOOD = """<style>
  #yield .bar { width: 100px; height: 40px; background: #0AF0F0; }
  #yield .bar.two, #yield svg { opacity: .5; }
  @keyframes pulse { from { opacity: 0; } to { opacity: 1; } }
</style>
<div class="bar"></div><div class="bar two"></div>
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>
<script>
  function buildYield(tl, root, t0, t1) {
    const bars = root.querySelectorAll('.bar');
    tl.fromTo(bars, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: 'power3.out', immediateRender: false }, t0);
    tl.to('#yield .bar', { x: 20, duration: 0.5, ease: 'power2.out' }, t0 + 0.5);
  }
</script>
"""


class Custom(unittest.TestCase):
    def build(self, html=GOOD, box=None, second_id="yield2", extra=None, files=None):
        d = scratch(self)
        for name, text in (files or {}).items():
            write(os.path.join(d, name), text)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        write(os.path.join(d, "custom", "yield.html"), html)
        lead = {"type": "title", "id": "lead", "bg": "black", "in": "word:0", "out": "word:4", "text": "Lead in"}
        cu = {"type": "custom", "id": "yield", "bg": "black", "in": "word:4", "out": "word:14",
              "box": box or {"x": 65, "y": 560, "w": 950, "h": 380}, "html": "custom/yield.html", "build": "buildYield", "source": "s1"}
        tail = {"type": "title", "id": second_id, "bg": "black", "in": "word:14", "out": D, "text": "The end"}
        scenes = [lead, cu, tail]
        if extra:
            extra(scenes)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": scenes})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", os.path.join(d, "vendor"))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def fails(self, text, **kw):
        r, _ = self.build(**kw)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)

    def test_box_outside_scene_area_fails(self):
        self.fails("outside the scene area", box={"x": 65, "y": 400, "w": 950, "h": 300})       # into the caption band
        self.fails("outside the scene area", box={"x": 65, "y": 900, "w": 950, "h": 300})       # full width below y 960

    def test_selector_outside_id_fails(self):
        self.fails("outside #yield", html=GOOD.replace("root.querySelectorAll('.bar')", "document.querySelector('.x')"))
        self.fails("document.body", html=GOOD.replace("const bars", "document.body.style.background = 'red'; const bars"))
        self.fails("outside #yield", html=GOOD.replace("#yield .bar.two, #yield svg", "#yield .bar.two, .x"))
        self.fails("outside #yield", html=GOOD.replace("tl.to('#yield .bar'", "tl.to('.bar'"))

    def test_network_fails(self):
        for bad in ("fetch('/data.json');", "const u = 'https://example.com/x.png';", "const v = 'http://example.com';",
                    "import('https://cdn.example.com/m.js');"):
            self.fails("network", html=GOOD.replace("const bars", bad + " const bars"))
        for bad in ("const w = '//cdn.example.com/x.js';", "root.innerHTML = '<img src=//cdn.example.com/a.png>';"):
            self.fails("network", html=GOOD.replace("const bars", bad + " const bars"))   # protocol-relative: the web too
        for bad in ("@import url('https://fonts.example.com/a.css');", "@import '//fonts.example.com/a.css';",
                    "#yield .bar { background: url(//example.com/a.png); }"):
            self.fails("network", html=GOOD.replace("<style>", "<style>\n  " + bad))
        self.assertEqual(self.build(html=GOOD.replace("const bars", "// a comment\n    const bars"))[0].returncode, 0)

    def test_a_module_build_function_must_be_on_window(self):
        # a module's top-level function is private to the module: window.buildYield stays undefined and the scene empty
        module = GOOD.replace("<script>", '<script type="module">')
        self.fails("window.buildYield = buildYield", html=module)
        r, _ = self.build(html=module.replace("  function buildYield", "  window.buildYield = buildYield;\n  function buildYield"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_build_function_fails(self):
        self.fails("buildYield", html=GOOD.replace("function buildYield", "function buildOther"))

    def test_duplicate_id_fails(self):
        self.fails("used twice", second_id="yield")

    def test_valid_custom_scene_builds(self):
        r, html = self.build()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t_in, t_out = t_word(4) - E.LEAD, t_word(14) - E.LEAD
        self.assertIn('window.buildYield(tl, document.getElementById("yield"), %.3f, %.3f)' % (t_in, t_out), html)
        self.assertRegex(html, r'<div class="box" id="yield" style="left:65px;top:560px;width:950px;height:380px"><div class="live" id="yield-live" style="width:950px;height:380px;transform:scale\(1\)">\s*<style>')

    def test_three_needs_its_vendor_copy(self):
        html = GOOD.replace("<script>", '<script type="module">\n  import * as THREE from "three";\n  window.buildYield = buildYield;')
        self.fails("npm pack three@0.169.0", html=html)

    def test_build_names_must_be_unique(self):
        def two(scenes):
            other = dict(scenes[1], id="yield3", html="custom/yield3.html", box=dict(scenes[1]["box"]))
            other["in"], other["out"] = "word:14", "word:20"
            scenes[2]["in"] = "word:20"
            scenes.insert(2, other)
        r, _ = self.build(extra=two, files={"custom/yield3.html": GOOD.replace("#yield", "#yield3")})
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("buildYield", r.stdout + r.stderr)
        self.assertIn("used by both", r.stdout + r.stderr)
