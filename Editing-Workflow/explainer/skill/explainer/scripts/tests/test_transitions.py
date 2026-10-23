"""Transitions: the composer picks how each scene comes in (a push, a zoom, a wipe at a background change), so a reel
moves from picture to picture the way the reference does without the storyboard saying so. A scene can still name its
own ("transition": "burst")."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, t_word, words30
import explainer_lib as E
import transitions as X


class Pick(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(X.pick(0, None, "mantle", None), "fade")            # the first scene fades up
        self.assertEqual(X.pick(3, "mantle", "base", None), "wipe")         # a new background is wiped in
        self.assertEqual(X.pick(1, "mantle", "mantle", None), "zoom")
        self.assertEqual(X.pick(2, "mantle", "mantle", None), "push")
        self.assertEqual(X.pick(2, "mantle", "base", "burst"), "burst")     # the storyboard's choice wins
        self.assertEqual(set(X.KINDS), {"fade", "push", "zoom", "wipe", "burst", "cut", "brush", "leak"})

    def test_burst_is_the_same_every_time(self):
        a, b = X.burst(2, 4.0, ["#fff", "#0AF0F0"]), X.burst(2, 4.0, ["#fff", "#0AF0F0"])
        self.assertEqual(a, b)
        self.assertEqual(len(re.findall(r'class="tx-p"', a[0])), 28)
        self.assertEqual(len(a[1]), 28)


class InThePage(unittest.TestCase):
    def build(self, board, ok=True):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), board)
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        if ok:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            return read(os.path.join(d, "public", "index.html"))
        return r

    def test_board_gets_zoom_then_wipe(self):
        html = self.build(BOARD)                      # hook (black), n1 (black), cu (light)
        t_n1, t_cu = t_word(8) - E.LEAD, t_word(18) - E.LEAD
        # HyperFrames' zoom-through: the old scene rushes past the viewer, the new one lands from behind (velocity-matched)
        self.assertIn("tl.fromTo('#n1', { scale: 0.75, filter: 'blur(8px)' }, { scale: 1, filter: 'blur(0px)', duration: 0.5, "
                      "ease: 'expo.out', immediateRender: false }, %.3f);" % t_n1, html)
        # the exit is over on the cut (SOP S9): it starts 0.2 s before the next scene's in
        self.assertIn("tl.to('#hook', { opacity: 0, scale: 1.2, filter: 'blur(10px)', duration: 0.2, ease: 'power3.in' }, %.3f);" % (t_n1 - 0.2), html)
        self.assertIn("tl.set('#bg1', { opacity: 1 }, %.3f);" % t_cu, html)
        self.assertIn("tl.fromTo('#bg1', { clipPath: 'circle(0%% at 50%% 60%%)' }, { clipPath: 'circle(150%% at 50%% 60%%)', "
                      "duration: 0.55, ease: 'power2.inOut', immediateRender: false }, %.3f);" % t_cu, html)
        self.assertNotIn("tl.to('#bg1', { opacity: 1, duration", html)          # no cross-fade under the wipe

    def test_push_is_a_whip(self):
        board = copy.deepcopy(BOARD)
        board["scenes"][1]["transition"] = "push"
        html = self.build(board)
        t_n1 = t_word(8) - E.LEAD
        self.assertIn("tl.fromTo('#n1', { y: 300, filter: 'blur(10px)' }, { y: 0, filter: 'blur(0px)', duration: 0.5, "
                      "ease: 'expo.out', immediateRender: false }, %.3f);" % t_n1, html)
        self.assertIn("tl.to('#hook', { opacity: 0, y: -260, filter: 'blur(12px)', duration: 0.2, ease: 'power3.in' }, %.3f);" % (t_n1 - 0.2), html)

    def test_named_burst(self):
        board = copy.deepcopy(BOARD)
        board["scenes"][1]["transition"] = "burst"
        html = self.build(board)
        self.assertEqual(len(re.findall(r'<i class="tx-p"', html)), 28)
        self.assertEqual(len(re.findall(r"tl\.fromTo\('#tx1-\d+'", html)), 28)

    def test_cut_has_no_motion(self):
        board = copy.deepcopy(BOARD)
        board["scenes"][1]["transition"] = "cut"
        html = self.build(board)
        self.assertIn("tl.set('#hook', { opacity: 0 }, %.3f);" % (t_word(8) - E.LEAD), html)
        self.assertNotRegex(html, r"tl\.fromTo\('#n1', \{ (scale|y):")

    def test_unknown_transition_fails(self):
        board = copy.deepcopy(BOARD)
        board["scenes"][1]["transition"] = "spin"
        r = self.build(board, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("fade, push, zoom, wipe, burst, cut, brush", r.stdout)



def paper_board(**last):
    """BOARD in the paper look: hook and n1 on base, the count-up on a new ground (blue)."""
    b = copy.deepcopy(BOARD)
    b["look"] = "paper"
    b["scenes"][0]["bg"] = b["scenes"][1]["bg"] = "base"
    b["scenes"][2]["bg"] = "blue"
    b["scenes"][2].update(last)
    return b


class Brush(unittest.TestCase):
    build = InThePage.build

    def test_brush_bands_are_seeded_and_on_the_tx_layer(self):
        html, again = self.build(paper_board()), self.build(paper_board())
        layer = re.search(r'<div class="tx-layer" id="tx">(.*?)</div>\n', html, re.S).group(1)
        paths = re.findall(r'<path class="tx-brush" id="txb2-(\d)" d="([^"]+)"', layer)
        self.assertEqual([p[0] for p in paths], ["0", "1", "2", "3", "4"])
        self.assertEqual(paths, re.findall(r'<path class="tx-brush" id="txb2-(\d)" d="([^"]+)"', again))
        self.assertIn("rotate(%.2f" % (-0.1 * 180 / 3.141592653589793), layer)
        cut, cover = t_word(18) - E.LEAD, X.BRUSH
        starts = [float(m) for m in re.findall(r"tl\.fromTo\('#txb2-\d', \{ scaleX: 0 \}.*?\}, ([\d.]+)\);", html)]
        self.assertEqual(starts, [round(cut - cover + f * cover, 3) for f in (0, .14, .06, .18, .1)])

    def test_neighbouring_bands_always_overlap(self):
        # each band's ragged edges may wander, but two neighbours must still overlap at every column on the cut frame
        for k in range(1, 40):
            html, _ = X.brush(k, 4.0, ["#000", "#f00"])
            bands = []
            for d in re.findall(r' d="M([^"]+)Z"', html):
                pts = [tuple(int(v) for v in p.split(",")) for p in d.split(" L")]
                half = len(pts) // 2
                bands.append(([y for _, y in pts[:half]], [y for _, y in pts[half:]][::-1]))
            for (_, bottom), (top, _) in zip(bands, bands[1:]):
                self.assertGreater(min(b - t for b, t in zip(bottom, top)), 0, k)

    def test_brush_covers_then_uncovers(self):
        html = self.build(paper_board())
        cut = t_word(18) - E.LEAD
        for i in range(5):
            cover = re.search(r"tl\.fromTo\('#txb2-%d', \{ scaleX: 0 \}, \{ scaleX: 1, duration: ([\d.]+), ease: 'power3.in'.*?\}, ([\d.]+)\);" % i, html)
            self.assertAlmostEqual(float(cover.group(1)) + float(cover.group(2)), cut, places=2)    # full cover on the cut
            self.assertRegex(html, r"tl\.to\('#txb2-%d', \{ scaleX: 0, transformOrigin: '100%% 50%%', duration: 0.3, ease: 'expo.out' \}, %.3f\);" % (i, cut))
        self.assertIn("tl.set('#bg1', { opacity: 1 }, %.3f);" % cut, html)           # the new ground swaps under the cover

    def test_a_brush_on_the_first_scene_never_starts_before_0(self):
        # GSAP pushes every other tween later by a child placed before 0: the whole page would drift off the voice
        b = paper_board()
        b["scenes"][0]["transition"] = "brush"
        html = self.build(b)
        times = [float(t) for t in re.findall(r"tl\.(?:fromTo|to|set)\('#txb0-\d'.*?\}, (-?[\d.]+)\);", html)]
        self.assertEqual(len(times), 15)
        self.assertGreaterEqual(min(times), 0.0)

    def test_paper_picks_brush_on_a_new_ground(self):
        self.assertEqual(X.pick(2, "base", "blue", None, look="paper"), "brush")
        self.assertEqual(X.pick(2, "base", "blue", None, look="latte"), "wipe")
        self.assertEqual(X.pick(2, "base", "base", None, look="paper"), "push")

    def test_e5_handover_clean_with_brush(self):
        from .test_layout import have_browser
        vendor = os.environ.get("EXPLAINER_VENDOR")
        if not (have_browser() and vendor and os.path.exists(os.path.join(vendor, "gsap.min.js"))):
            self.skipTest("needs node, puppeteer, Chrome and the real vendor folder (EXPLAINER_VENDOR)")
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), paper_board()), "--out",
                os.path.join(d, "public"), "--vendor", vendor)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run("layout-check.py", "--index", os.path.join(d, "public", "index.html"), "--no-hf")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_brush_has_a_whoosh(self):
        import sound
        self.assertEqual(sound.events([("brush", 4.0)], []), [(round(4.0 - sound.LEAD, 3), "whoosh")])


class Close(unittest.TestCase):
    build = InThePage.build

    def test_the_last_scene_leaves(self):
        for last in ({}, {"type": "giant-captions", "keywords": ["word20"]}):
            b = copy.deepcopy(BOARD)
            sc = dict(b["scenes"][2], bg="base", **last)
            if last:
                for k in ("value", "prefix", "sub", "source"):
                    sc.pop(k)
            b["scenes"][2] = sc
            html = self.build(b)
            D_ = round(VOICE + E.TAIL, 3)
            self.assertIn("tl.to('#cu', { opacity: 0, y: -24, duration: %.1f, ease: 'power3.in' }, %.3f);" % (X.CLOSE, D_ - X.CLOSE), html)
            hook_bg = re.search(r'<div class="bg" id="bg0" style="background:([^;"]+)', html).group(1)
            bgs = re.findall(r'<div class="bg" id="(bg\d+)" style="background:([^;"]+)', html)
            self.assertEqual(bgs[-1][1], hook_bg)                                   # the ground at D is the hook's
            self.assertIn("tl.set('#%s', { opacity: 1 }, %.3f);" % (bgs[-1][0], D_ - X.CLOSE), html)


if __name__ == "__main__":
    unittest.main()
