"""The living layer: the picture never stands still. Orbs drift behind every scene, each scene pushes in slowly while it
is on screen, and none of that ambient motion counts as a change for pace-check (gate E4 still wants a new picture)."""
import copy, json, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import BOARD, D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import icon_row

TOK = E.load_tokens()


class Living(unittest.TestCase):
    def build(self, board):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), board)
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return read(os.path.join(out, "index.html")), out

    def test_every_scene_sits_in_a_live_wrapper_that_pushes_in(self):
        html, _ = self.build(BOARD)
        push = TOK["ambient"]["push"]
        for sid in ("hook", "n1", "cu"):
            self.assertRegex(html, r'<div class="box" id="%s"[^>]*><div class="live" id="%s-live">' % (sid, sid))
            self.assertRegex(html, r"tl\.fromTo\('#%s-live', \{ scale: 1 \}, \{ scale: %s, duration: [\d.]+, ease: 'sine.inOut'"
                             % (sid, re.escape(str(push))))

    def test_each_background_has_its_own_glows(self):
        html, _ = self.build(BOARD)                      # black, black, then light at the count-up: two background layers
        for i, bg in enumerate(("black", "light")):
            layer = re.search(r'<div class="bg" id="bg%d"[^>]*>(.*?)</div>' % i, html).group(1)
            glows = re.findall(r'<i class="orb" id="bg%d-o(\d)" style="[^"]*background:radial-gradient\(circle, ([^ ]+) 0%%' % i, layer)
            self.assertEqual([c for _, c in glows], [g["color"] for g in TOK["ambient"]["glows"][bg]], bg)
        self.assertNotIn('id="orbs"', html)              # no shared layer whose colours suit only one background

    def test_glows_travel_visibly_for_the_whole_reel(self):
        html, _ = self.build(BOARD)
        drift = TOK["ambient"]["drift"]
        for i in range(2):
            for k in range(3):
                moves = re.findall(r"tl\.to\('#bg%d-o%d', \{ x: (-?[\d.]+), y: (-?[\d.]+), duration: [\d.]+, ease: 'sine.inOut' \}, ([\d.]+)\);"
                                   % (i, k), html)
                self.assertGreaterEqual(len(moves), int(D // drift["every"]), (i, k))
                self.assertGreaterEqual(max(float(t) for _, _, t in moves), D - drift["every"] - 1e-6)
        xs = [abs(float(x)) for x in re.findall(r"tl\.to\('#bg\d-o\d', \{ x: (-?[\d.]+)", html)]
        ys = [abs(float(y)) for y in re.findall(r"tl\.to\('#bg\d-o\d', \{ x: -?[\d.]+, y: (-?[\d.]+)", html)]
        self.assertGreaterEqual(max(xs), 300)            # the reference's glows travel about 400 px every 2 to 3 s
        self.assertGreaterEqual(max(ys), 400)

    def test_blue_is_a_light_royal_blue(self):
        lum = lambda h: 0.2126 * int(h[1:3], 16) + 0.7152 * int(h[3:5], 16) + 0.0722 * int(h[5:7], 16)
        stops = re.findall(r"#[0-9A-Fa-f]{6}", TOK["backgrounds"]["blue"])
        self.assertGreater(lum(stops[0]), lum(stops[-1]) + 15)          # lighter at the top, like the reference
        self.assertNotIn("205,0,238", TOK["backgrounds"]["blue"])        # no violet baked in: the lilac glow moves instead
        self.assertGreaterEqual(sum(map(lum, stops)) / len(stops), 70)   # the reference's core #2941D1 is about 69

    def test_ambient_motion_is_not_a_change(self):
        _, out = self.build(BOARD)
        with open(os.path.join(out, "moments.json")) as f:
            spans = json.load(f)["spans"]
        self.assertLess(max(e - s for s, e in spans), 2.0)        # the push-ins and drifts would be 3 to 5 s long
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "only", "bg": "black", "in": "word:0", "out": "end", "text": "One idea"}]
        _, out = self.build(board)
        r = run("pace-check.py", "--index", os.path.join(out, "index.html"))
        self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_icon_row_stays_centred_as_icons_arrive(self):
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "lead", "bg": "black", "in": "word:0", "out": "word:4", "text": "Lead in"},
                           {"type": "icon-row", "id": "sc", "bg": "black", "in": "word:4", "out": "end",
                            "items": [{"icon": "book", "label": "Read", "at": "word:6"}, {"icon": "clock", "label": "Wait", "at": "word:9"}]}]
        html, _ = self.build(board)
        width = int(re.search(r'id="sc" style="left:\d+px;top:\d+px;width:(\d+)px', html).group(1))
        pitch = (width + icon_row.COL_GAP) / 2.0
        first = re.search(r"tl\.set\('#sc \.ic-row', \{ x: ([\d.]+) \}, ([\d.]+)\);", html)
        self.assertAlmostEqual(float(first.group(1)), pitch / 2, delta=0.01)
        self.assertAlmostEqual(float(first.group(2)), t_word(4) - E.LEAD, places=3)
        later = re.findall(r"tl\.to\('#sc \.ic-row', \{ x: ([\d.]+), duration: [\d.]+, ease: '[\w.]+' \}, ([\d.]+)\);", html)
        self.assertEqual(len(later), 1)
        self.assertEqual(float(later[0][0]), 0.0)
        self.assertAlmostEqual(float(later[0][1]), t_word(9) - E.LEAD, places=3)


if __name__ == "__main__":
    unittest.main()
