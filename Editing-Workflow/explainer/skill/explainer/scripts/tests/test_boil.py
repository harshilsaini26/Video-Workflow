"""Boil (after ClaudeAnimationBase's hand-drawn line wobble, MIT): in the paper look the strokes (the thread, the
annotation circles and leaders, line-art) wobble a little, as if drawn by hand: one SVG turbulence filter whose seed
steps 12 times a second as ambient motion. Never on text or fills; off in latte; off for a whole page with
data-boil="off" on the root (the motion gate samples the page that way)."""
import copy, os, re, unittest
from .helpers import load, read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
from .test_assets import png
from .test_scenes_ui import stub_vendor
from .test_thread import THREAD


def board(look):
    b = copy.deepcopy(BOARD)
    b["look"] = look
    b["thread"] = copy.deepcopy(THREAD)
    for sc in b["scenes"]:
        sc["bg"] = "base"
    b["scenes"][1] = {"type": "line-art", "id": "la", "bg": "base", "in": "word:8", "out": "word:18", "icon": "book",
                      "caption": "read it", "at": "word:9"}
    b["scenes"][2] = {"type": "product-hero", "id": "ph", "bg": "base", "in": "word:18", "out": "end", "src": "bud-1200x1200.png",
                      "alt": "an earbud", "at": "word:19", "aspect": 1.0,
                      "notes": [{"x": 0.75, "y": 0.16, "label": "A WIRE?", "at": "word:21", "mark": "circle", "side": "left"}]}
    return b


class Boil(unittest.TestCase):
    def page(self, look):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        png(os.path.join(d, "bud-1200x1200.png"), 1200, 1200)
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), board(look)), "--out",
                os.path.join(d, "public"), "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return read(os.path.join(d, "public", "index.html")), load(os.path.join(d, "public", "moments.json"))

    def boiling(self, html):
        return re.findall(r"<(\w+)[^>]*\bclass=\"[^\"]*\bboil\b[^\"]*\"[^>]*>", html)

    def test_strokes_boil_text_never(self):
        html, _ = self.page("paper")
        tags = self.boiling(html)
        self.assertIn("circle", tags)                                       # the annotation's circle
        self.assertIn("path", tags)                                         # line-art and the thread
        self.assertIn("i", tags)                                            # the annotation's leader
        self.assertNotIn("text", tags)
        for m in re.finditer(r"<(div|span|i|p)\b[^>]*\bclass=\"[^\"]*\bboil\b[^\"]*\"[^>]*>([^<]*)", html):
            self.assertEqual(m.group(2).strip(), "", "text boils: %s" % m.group(0))
        self.assertIn('<filter id="boil"', html)
        self.assertIn('scale="2.5"', html)

    def test_thread_boils(self):
        html, _ = self.page("paper")
        self.assertRegex(html, r'<path id="th-p" class="boil"')

    def test_boil_only_in_paper(self):
        html, _ = self.page("latte")
        self.assertEqual(self.boiling(html), [])
        self.assertNotIn('<filter id="boil"', html)

    def test_boil_steps_are_ambient(self):
        _, on = self.page("paper")
        _, off = self.page("latte")
        self.assertEqual(on["spans"], off["spans"])

    def test_boil_off_switch(self):
        html, _ = self.page("paper")
        self.assertIn('html:not([data-boil="off"]) .boil { filter:url(#boil); }', html)
