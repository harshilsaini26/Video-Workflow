"""The mock-UI, formula and icon scenes: browser, sheet, formula, icon-row (SPEC §6.2)."""
import os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
import explainer_lib as E

SVG = '<!-- @license lucide-static v0.454.0 - ISC -->\n<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M2 2h20"/></svg>\n'


def stub_vendor(d, katex=True, icons=("book", "clock")):
    v = os.path.join(d, "vendor")
    write(os.path.join(v, "gsap.min.js"), "window.gsap={};")
    if katex:
        write(os.path.join(v, "katex", "katex.min.js"), "window.katex={};")
        write(os.path.join(v, "katex", "katex.min.css"), ".katex{}")
        write(os.path.join(v, "katex", "fonts", "KaTeX_Main-Regular.woff2"), "x")
    for name in icons:
        write(os.path.join(v, "lucide", name + ".svg"), SVG)
    return v


class UICase(unittest.TestCase):
    def build(self, scene, **vendor):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": "black", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": "black", "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc]})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d, **vendor))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else ""), out

    def ok(self, scene, **vendor):
        r, html, out = self.build(scene, **vendor)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html, out

    def fails(self, scene, text, **vendor):
        r, _, _ = self.build(scene, **vendor)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)


class Browser(UICase):
    def test_escaped_domain_shown_no_external_url(self):
        html, _ = self.ok({"type": "browser", "title": "Learn <b>finance</b>", "subtitle": "Free courses", "badges": ["Free", "A&B"],
                           "button": "Enroll", "domain": "coursera.org"})
        self.assertIn("Learn &lt;b&gt;finance&lt;/b&gt;", html)
        self.assertIn("A&amp;B", html)
        self.assertRegex(html, r'class="br-url"[^>]*>[^<]*coursera\.org')
        self.assertNotRegex(html, r"https?://")


class Sheet(UICase):
    rows = [["Year", "Cash"], ["1", "$100"], ["2", "$120"], ["3", "$150"]]

    def test_at_most_eight_rows(self):
        self.fails({"type": "sheet", "rows": [["a", "b"]] * 9, "source": "s1"}, "8 rows")

    def test_highlight_must_exist(self):
        self.fails({"type": "sheet", "source": "s1", "rows": self.rows, "highlight": {"row": 7, "at": "word:8"}}, "row 7")
        self.fails({"type": "sheet", "source": "s1", "rows": self.rows, "highlight": {"cell": [1, 5], "at": "word:8"}}, "cell")
        html, _ = self.ok({"type": "sheet", "source": "s1", "rows": self.rows, "highlight": {"cell": [2, 1], "at": "word:8"}, "formula": "=B2*1.2"})
        self.assertRegex(html, r'class="sh-fx"[^>]*><b>fx</b>=B2\*1\.2')
        self.assertRegex(html, r"tl\.\w+\('#sc-hl'.*%.3f\);" % (t_word(8) - E.LEAD))


class Formula(UICase):
    scene = {"type": "formula", "tex": "PV = \\frac{FV}{(1+r)^n}",
             "parts": [{"tex": "PV =", "at": "word:6"}, {"tex": "\\frac{FV}{(1+r)^n}", "at": "word:9"}]}

    def test_parts_reveal_on_their_words(self):
        html, out = self.ok(self.scene)
        for i, w in ((0, 6), (1, 9)):
            self.assertRegex(html, r"tl\.fromTo\('#sc-p%d', \{ opacity: 0[^;]*\}, %.3f\);" % (i, t_word(w) - E.LEAD))
        self.assertIn("katex.render(", html)
        self.assertTrue(os.path.exists(os.path.join(out, "vendor", "katex", "katex.min.js")))
        self.assertTrue(os.path.exists(os.path.join(out, "vendor", "katex", "fonts", "KaTeX_Main-Regular.woff2")))

    def test_missing_katex_names_the_install(self):
        self.fails(self.scene, "npm pack katex@0.16.11", katex=False)


class IconRow(UICase):
    def test_unknown_icon_named(self):
        self.fails({"type": "icon-row", "items": [{"icon": "book", "label": "Read", "at": "word:6"},
                                                  {"icon": "rocket-ship", "label": "Go", "at": "word:8"}]}, "rocket-ship")

    def test_two_to_four_items(self):
        self.fails({"type": "icon-row", "items": [{"icon": "book", "label": "Read", "at": "word:6"}]}, "2 to 4")

    def test_svg_inlined(self):
        html, _ = self.ok({"type": "icon-row", "items": [{"icon": "book", "label": "Read", "at": "word:6"},
                                                         {"icon": "clock", "label": "Wait", "at": "word:8"}]})
        self.assertEqual(len(re.findall(r'<div class="ic-tile"[^>]*><svg', html)), 2)
        self.assertNotRegex(html, r"<img[^>]+src=\"?https?:")
