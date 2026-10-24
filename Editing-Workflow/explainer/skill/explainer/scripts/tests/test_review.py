"""review.py: the Animator's review sheets (strips around every cut, a scene's timing sheet, every item as it lands,
1:1 crops, a crop that follows one element), made in Chromium from the composed page, before any render."""
import math, os, re, unittest
from .helpers import load, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
from .test_layout import have_browser
from .test_motion import PAGE
from .test_scenes_ui import stub_vendor
import imagesize

# a square shown only from 1 s to 2.5 s: hidden for the first and last part of its scene's life (0 to 4 s)
HIDDEN = PAGE.replace('function (t) {', 'function (t) { document.getElementById("sq").style.visibility = t >= 1 && t < 2.5 ? "visible" : "hidden";') \
    .replace('<div id="sq"></div>', '<div class="card-host" data-start="0" data-duration="4"><div id="sq"></div></div>')


def cells(stdout, name):
    m = re.search(r"%s: (\d+) cells" % re.escape(name), stdout)
    return int(m.group(1)) if m else None


@unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
class Review(unittest.TestCase):
    def page(self):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), BOARD), "--out", out,
                "--vendor", os.environ.get("EXPLAINER_VENDOR") or stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return os.path.join(out, "index.html"), os.path.join(d, "review")

    def review(self, *args, page=None):
        index, out = page or self.page()
        r = run("review.py", "--index", index, "--out", out, *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ms per frame", r.stdout)
        return r.stdout, out

    def test_cuts_strip_has_25_cells_per_handover(self):
        out, d = self.review("--cuts")
        files = sorted(f for f in os.listdir(d) if f.startswith("cut-"))
        self.assertEqual(files, ["cut-01-hook-n1.png", "cut-02-n1-cu.png"])
        for f in files:
            self.assertEqual(cells(out, f), 25)
            w, h = imagesize.size(os.path.join(d, f))[:2]
            self.assertEqual(w, 8 * 216)

    def test_scene_sheet_steps(self):
        index, d = self.page()
        sc = next(s for s in load(os.path.join(os.path.dirname(index), "moments.json"))["scenes"] if s["id"] == "n1")
        out, d = self.review("--scene", "n1", "--step", "0.5", page=(index, d))
        self.assertEqual(cells(out, "scene-n1.png"), math.ceil((sc["out"] - sc["in"]) / 0.5 - 1e-9))

    def test_items_rows(self):
        index, d = self.page()
        n = len(load(os.path.join(os.path.dirname(index), "moments.json"))["items"])
        out, d = self.review("--items", page=(index, d))
        self.assertEqual(cells(out, "items.png"), 3 * n)

    def test_crop_is_exact(self):
        out, d = self.review("--crop", "100,200,300,400")
        crops = sorted(f for f in os.listdir(d) if f.startswith("crop-"))
        self.assertEqual(len(crops), 3)                                  # one per scene, at its settled moment
        self.assertEqual(imagesize.size(os.path.join(d, crops[0]))[:2], (300, 400))

    def test_crop_defaults_to_each_scene_and_the_caption_band(self):
        out, d = self.review("--crop")
        crops = sorted(f for f in os.listdir(d) if f.startswith("crop-"))
        self.assertEqual(len(crops), 6)
        self.assertIn("crop-01-hook-captions.png", crops)

    def test_follow_skips_hidden_frames(self):
        d = scratch(self)
        index = write(os.path.join(d, "public", "index.html"), HIDDEN)
        out, rd = self.review("--follow", "#sq", page=(index, os.path.join(d, "review")))
        self.assertNotIn("Traceback", out)
        n = cells(out, "follow-sq.png")
        self.assertTrue(n and n < 6, out)


if __name__ == "__main__":
    unittest.main()
