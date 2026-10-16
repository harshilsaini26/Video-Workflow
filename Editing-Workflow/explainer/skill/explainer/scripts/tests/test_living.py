"""Motion with a reason (MOTION.md): no scene breathes or pushes in on its own; the background's glows move only on a
cut, travelling with it, and hold still between cuts; no ease overshoots. None of that ambient motion counts as a change
for pace-check (gate E4 still wants a new picture)."""
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

    def test_no_scene_breathes(self):
        # HyperFrames' motion language: no lazy breathing, no slow push-in; a held scene is still unless it says something
        html, _ = self.build(BOARD)
        self.assertNotRegex(html, r"tl\.\w+\('#\w+-live'")
        self.assertNotIn("push", TOK["ambient"])

    def test_each_background_has_its_own_glows(self):
        html, _ = self.build(BOARD)                      # black, black, then light at the count-up: two background layers
        for i, bg in enumerate(("mantle", "base")):
            layer = re.search(r'<div class="bg" id="bg%d"[^>]*>(.*?)</div>' % i, html).group(1)
            glows = re.findall(r'<i class="orb" id="bg%d-o(\d)" style="[^"]*background:radial-gradient\(circle, ([^ ]+) 0%%' % i, layer)
            self.assertEqual([c for _, c in glows], [E.rgba(TOK["palette"][g["color"]], g["alpha"]) for g in TOK["ambient"]["glows"][bg]], bg)
        self.assertNotIn('id="orbs"', html)              # no shared layer whose colours suit only one background

    def test_glows_move_only_on_a_cut_and_travel_with_it(self):
        board = copy.deepcopy(BOARD)                     # four scenes on black: three cuts
        board["scenes"] = [
            {"type": "title", "id": "a", "bg": "mantle", "in": "word:0", "out": "word:5", "text": "One"},
            {"type": "title", "id": "b", "bg": "mantle", "in": "word:5", "out": "word:10", "text": "Two"},
            {"type": "title", "id": "c", "bg": "mantle", "in": "word:10", "out": "word:15", "text": "Three"},
            {"type": "title", "id": "d", "bg": "mantle", "in": "word:15", "out": "end", "text": "Four"}]
        html, _ = self.build(board)
        sh = TOK["ambient"]["shift"]
        cuts = [round(t_word(i) - E.LEAD, 3) for i in (5, 10, 15)]
        # fromTo with the start written out: a render chunk that seeks into an overlap draws what a straight play draws
        moves = re.findall(r"tl\.fromTo\('#bg0-o(\d)', \{ x: (-?[\d.]+), y: (-?[\d.]+) \}, \{ x: (-?[\d.]+), y: (-?[\d.]+), "
                           r"duration: ([\d.]+), ease: '([\w.]+)', immediateRender: false \}, ([\d.]+)\);", html)
        last = {}
        for k, x0, y0, x, y, dur, ease, t in moves:
            self.assertEqual((float(x0), float(y0)), last.get(k, (0.0, 0.0)))   # each move starts where the last one ended
            last[k] = (float(x), float(y))
        moves = [(k, x, y, dur, ease, t) for k, x0, y0, x, y, dur, ease, t in moves]
        self.assertEqual(len(moves), 3 * len(cuts))      # every glow, on every cut, and never between
        self.assertEqual(sorted({float(m[5]) for m in moves}), cuts)
        for k, x, y, dur, ease, t in moves:
            self.assertEqual(ease, "expo.out")
            self.assertEqual(float(dur), sh["duration"])
            self.assertGreaterEqual(abs(float(x)), 0.5 * sh["x"])   # a move you can see, not a wobble
            self.assertLessEqual(abs(float(x)), sh["x"])
            self.assertLessEqual(abs(float(y)), sh["y"])
        self.assertNotIn("sine.inOut', ease", html)
        self.assertNotRegex(html, r"tl\.to\('#bg\d-o\d', \{[^}]*ease: 'sine")

    def test_no_ease_overshoots(self):
        # back, elastic and bounce read as cheap (HyperFrames motion-language.md, motion-graphics-skills' banned list)
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        srcs = [os.path.join(here, "scenes", f) for f in os.listdir(os.path.join(here, "scenes")) if f.endswith(".py")]
        srcs += [os.path.join(here, f) for f in ("explainer-compose.py", "transitions.py")]
        for p in srcs:
            self.assertNotRegex(read(p), r"['\"](back|elastic|bounce)\.\w+", p)

    def test_ambient_motion_is_not_a_change(self):
        _, out = self.build(BOARD)
        with open(os.path.join(out, "moments.json")) as f:
            spans = json.load(f)["spans"]
        self.assertLess(max(e - s for s, e in spans), 2.0)        # idle floats and glow shifts are not changes
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "only", "bg": "mantle", "in": "word:0", "out": "end", "text": "One idea"}]
        _, out = self.build(board)
        r = run("pace-check.py", "--index", os.path.join(out, "index.html"))
        self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_icon_row_stays_centred_as_icons_arrive(self):
        board = copy.deepcopy(BOARD)
        board["scenes"] = [{"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"},
                           {"type": "icon-row", "id": "sc", "bg": "mantle", "in": "word:4", "out": "end",
                            "items": [{"icon": "book", "label": "Read", "at": "word:6"}, {"icon": "clock", "label": "Wait", "at": "word:9"}]}]
        html, _ = self.build(board)
        width = int(re.search(r'id="sc-live" style="width:(\d+)px', html).group(1))
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
