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
        self.assertEqual(X.pick(0, None, "black", None), "fade")            # the first scene fades up
        self.assertEqual(X.pick(3, "black", "light", None), "wipe")         # a new background is wiped in
        self.assertEqual(X.pick(1, "black", "black", None), "zoom")
        self.assertEqual(X.pick(2, "black", "black", None), "push")
        self.assertEqual(X.pick(2, "black", "light", "burst"), "burst")     # the storyboard's choice wins
        self.assertEqual(set(X.KINDS), {"fade", "push", "zoom", "wipe", "burst", "cut"})

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
        self.assertIn("tl.to('#hook', { opacity: 0, scale: 1.2, filter: 'blur(10px)', duration: 0.2, ease: 'power3.in' }, %.3f);" % t_n1, html)
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
        self.assertIn("tl.to('#hook', { opacity: 0, y: -260, filter: 'blur(12px)', duration: 0.2, ease: 'power3.in' }, %.3f);" % t_n1, html)

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
        self.assertIn("fade, push, zoom, wipe, burst, cut", r.stdout)


if __name__ == "__main__":
    unittest.main()
