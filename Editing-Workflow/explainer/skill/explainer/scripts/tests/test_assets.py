"""Real logos and real pages, fetched on the creator's machine: a logo card from simple-icons (or the creator's own image),
the browser scene showing a screenshot that punches in on its focus line, and snap-page.py taking that screenshot with local Chrome."""
import json, os, re, shutil, struct, unittest, zlib
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
import explainer_lib as E
from .test_scenes_ui import stub_vendor

CHROMES = [os.environ.get("CHROME", ""), "/opt/pw-browsers/chromium"] + [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chromium-browser")]
CHROME = next((c for c in CHROMES if c and os.path.exists(c)), None)
COURSERA = '<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Coursera</title><path d="M2 2h20v20H2z"/></svg>'


def png(path, w, h):
    """A one-colour PNG of w x h with an alpha channel (a cut-out; enough for the header the scenes read)."""
    raw = b"".join(b"\x00" + b"\x30\x60\xc0\xff" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return path


def vendor_with_logos(d):
    v = stub_vendor(d)
    write(os.path.join(v, "simple-icons", "icons", "coursera.svg"), COURSERA)
    write(os.path.join(v, "simple-icons", "_data", "simple-icons.json"),
          {"icons": [{"title": "Coursera", "hex": "0056D2", "source": "https://about.coursera.org/press"}]})
    return v


class Assets(unittest.TestCase):
    def build(self, scene, files=()):
        d = scratch(self)
        for name, (w, h) in files:
            png(os.path.join(d, name), w, h)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": "mantle", "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc]})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", vendor_with_logos(d))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else ""), out

    def test_logo_card_inlines_the_brand_mark_in_its_colour(self):
        r, html, _ = self.build({"type": "logo-card", "logo": "coursera", "badge": "1", "sub": "Introduction to Corporate Finance"})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(html, r'<svg[^>]*fill="#0056D2"[^>]*>.*<path d="M2 2h20v20H2z"', )
        self.assertIn(">Coursera<", html)                     # the name defaults to the brand's title
        self.assertIn("Coursera is a trademark of its owner", r.stdout)
        self.assertNotIn("<title>", html.split('id="host-sc"')[1])   # the SVG's tooltip title is dropped

    def test_unknown_logo_names_the_install(self):
        r, _, _ = self.build({"type": "logo-card", "logo": "no-such-brand"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-brand", r.stdout)
        self.assertIn("npm pack simple-icons@13.21.0", r.stdout)

    def test_logo_card_from_the_creators_own_image(self):
        r, html, out = self.build({"type": "logo-card", "src": "img/wharton.png", "name": "Wharton"}, files=[("img/wharton.png", (64, 64))])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(os.path.exists(os.path.join(out, "assets", "sc-wharton.png")))
        self.assertIn('src="assets/sc-wharton.png"', html)
        r, _, _ = self.build({"type": "logo-card", "src": "img/missing.png", "name": "X"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("img/missing.png", r.stdout)

    def test_a_screenshot_holds_still_until_its_focus_then_punches_in(self):
        # no lazy scroll down the page (it drifted into blank page); the page moves once, on the word that names the line
        scene = {"type": "browser", "title": "Introduction to Corporate Finance", "domain": "coursera.org", "screenshot": "shots/page.png"}
        r, html, out = self.build(scene, files=[("shots/page.png", (1280, 2400))])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(os.path.exists(os.path.join(out, "assets", "sc-page.png")))
        self.assertNotRegex(html, r"tl\.\w+\('#sc-shot'")
        r, html, _ = self.build(dict(scene, focus={"y": 1500, "at": "word:8"}), files=[("shots/page.png", (1280, 2400))])
        self.assertEqual(r.returncode, 0, r.stdout)
        iw = int(re.search(r'id="sc-live" style="width:(\d+)px', html).group(1))
        k = iw / 1280.0
        m = re.search(r"tl\.to\('#sc-shot', \{ y: (-?[\d.]+), scale: 1\.25, transformOrigin: '50% ([\d.]+)px', duration: 0\.8, "
                      r"ease: 'expo\.out' \}, ([\d.]+)\);", html)
        self.assertTrue(m, html[-3000:])
        self.assertAlmostEqual(float(m.group(2)), 1500 * k, delta=1)
        from scenes import browser
        self.assertAlmostEqual(float(m.group(1)), browser.VIEW / 2.0 - 1500 * k, delta=1)    # the line lands mid-view
        self.assertAlmostEqual(float(m.group(3)), t_word(8) - E.LEAD, places=3)
        self.assertRegex(html, r'id="sc-view" data-at="%.3f" data-anchor="word8"' % (t_word(8) - E.LEAD))
        for fy in (0, 2390):     # a line at the very top or bottom: the page never pulls away from the view's edge
            r, html, _ = self.build(dict(scene, focus={"y": fy, "at": "word:8"}), files=[("shots/page.png", (1280, 2400))])
            m = re.search(r"tl\.to\('#sc-shot', \{ y: (-?[\d.]+), scale: 1\.25, transformOrigin: '50% ([\d.]+)px'", html)
            y, o, tall = float(m.group(1)), float(m.group(2)), 2400 * k
            self.assertLessEqual(y - 0.25 * o, 0.01, fy)                          # the top of the page at or above the view's top
            self.assertGreaterEqual(o + 1.25 * (tall - o) + y, browser.VIEW - 0.01, fy)   # its bottom at or below the view's bottom
        r, _, _ = self.build(dict(scene, focus={"y": 2600, "at": "word:8"}), files=[("shots/page.png", (1280, 2400))])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("focus", r.stdout)
        r, _, _ = self.build(dict(scene, screenshot="shots/none.png"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("shots/none.png", r.stdout)

    @unittest.skipUnless(CHROME, "no Chrome or Chromium found")
    def test_snap_page_takes_a_local_screenshot(self):
        d = scratch(self)
        page = write(os.path.join(d, "page.html"), "<html><body style='margin:0;background:#2A35D6;height:3000px'>A page</body></html>")
        out = os.path.join(d, "shots", "page.png")
        r = run("snap-page.py", "--url", "file://" + page, "--out", out, "--width", "1000", "--height", "1400")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, "rb") as f:
            head = f.read(24)
        self.assertEqual(head[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", head[16:24]), (1000, 1400))

    @unittest.skipUnless(CHROME, "no Chrome or Chromium found")
    def test_snap_page_fails_on_a_page_that_does_not_load(self):
        # Chrome draws its own "This site can't be reached" page; a screenshot of that must never reach a reel
        d = scratch(self)
        out = os.path.join(d, "shots", "down.png")
        r = run("snap-page.py", "--url", "http://127.0.0.1:9/", "--out", out, "--width", "800", "--height", "600", "--wait", "1000")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("did not load", r.stdout + r.stderr)
        self.assertFalse(os.path.exists(out))

    def test_snap_page_needs_chrome(self):
        r = run("snap-page.py", "--url", "file:///x.html", "--out", "/tmp/x.png", "--chrome", "/no/such/chrome")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Chrome", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
