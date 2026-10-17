"""The hook and the captions: a kinetic hook written as plain words still gets its hero token ("5 STEPS" → a big 5),
and giant captions (the voice's own words, one to three at a time, huge in the middle of the frame) take over from the
caption band while they run."""
import copy, os, re, unittest
from .helpers import load, read, run, scratch, write
from .test_compose import BOARD, D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY

TOK = E.load_tokens()


def compose(test, scenes, emphasis=()):
    d = scratch(test)
    write(os.path.join(d, "transcript.json"), {"words": words30()})
    silent_wav(os.path.join(d, "voice.wav"), VOICE)
    sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": scenes, "captions": {"emphasis": list(emphasis)}})
    r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
    return r, (read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else ""), d


class KineticHook(unittest.TestCase):
    def test_a_number_written_into_the_words_becomes_the_hero(self):
        mod = REGISTRY["kinetic"]
        sc = {"type": "kinetic", "words": [{"text": "5 STEPS", "at": "word:0"}, {"text": "AI LOOKS IT UP", "at": "word:1"}]}
        mod.normalize(sc)
        self.assertEqual(sc["big"], {"text": "5", "at": "word:0"})
        self.assertEqual([w["text"] for w in sc["words"]], ["STEPS", "AI LOOKS IT UP"])
        same = {"type": "kinetic", "big": {"text": "3", "at": "word:0"}, "words": [{"text": "5 STEPS", "at": "word:1"}]}
        mod.normalize(same)                                   # a hero already given is kept
        self.assertEqual(same["big"]["text"], "3")
        r, html, _ = compose(self, [{"type": "kinetic", "id": "hk", "bg": "ink", "in": "word:0", "out": "word:8",
                                     "words": [{"text": "5 STEPS", "at": "word:0"}, {"text": "AI LOOKS IT UP", "at": "word:1"}], "source": "s1"},
                                    dict(BOARD["scenes"][2], **{"in": "word:8"})])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(html, r'<span class="kn-big" id="hk-b"[^>]*>5</span>')


class GiantCaptions(unittest.TestCase):
    SC = {"type": "giant-captions", "id": "gc", "bg": "blue", "in": "word:8", "out": "word:18", "keywords": ["word12"]}

    def test_the_voices_words_land_huge_on_their_own_times(self):
        r, html, d = compose(self, [dict(BOARD["scenes"][0], out="word:8"), self.SC, dict(BOARD["scenes"][2], **{"in": "word:18"})])
        self.assertEqual(r.returncode, 0, r.stdout)
        for i in range(8, 18):
            self.assertRegex(html, r"tl\.fromTo\('#gc-w%d', \{ opacity: 0[^}]*\}, \{[^}]*\}, %.3f\);" % (i, t_word(i) - 0.05), i)
        acc = E.theme(TOK, "blue")["accent"]
        self.assertRegex(html, r'id="gc-w12"[^>]*style="color:%s' % acc)
        sizes = [int(s) for s in re.findall(r'class="gc-c"[^>]*style="[^"]*font-size:(\d+)px', html)]
        self.assertTrue(sizes and min(sizes) >= 120, sizes)
        m = load(os.path.join(d, "public", "moments.json"))
        self.assertGreaterEqual(len([s for s in m["spans"] if t_word(8) - 0.2 <= s[0] <= t_word(18)]), 10)

    def test_the_caption_band_steps_aside_while_they_run(self):
        r, html, _ = compose(self, [dict(BOARD["scenes"][0], out="word:8"), self.SC, dict(BOARD["scenes"][2], **{"in": "word:18"})])
        caps = re.findall(r"tl\.set\('#cap(\d+)', \{ visibility: 'visible' \}, ([\d.]+)\);", html)
        lo, hi = t_word(8) - E.LEAD, t_word(18) - E.LEAD
        self.assertTrue(caps)
        self.assertFalse([c for c, t in caps if lo - 1e-3 <= float(t) < hi - 1e-3], caps)

    def test_the_handle_and_the_part_read_on_every_ground(self):
        # the band above the captions takes each ground's quiet colour as the ground changes, like the captions do
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        board = {"id": "t", "brand": {"handle": "@you", "part": 1},
                 "scenes": [dict(BOARD["scenes"][0], bg="mantle", out="word:8"), dict(BOARD["scenes"][1], bg="blue", **{"in": "word:8", "out": "word:18"}),
                            dict(BOARD["scenes"][2], bg="ink", **{"in": "word:18"})]}
        sp = write(os.path.join(d, "storyboard.json"), board)
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout[-300:])
        html = read(os.path.join(d, "public", "index.html"))
        for bg, w in (("blue", 8), ("ink", 18)):
            self.assertIn("tl.set('#brand', { color: '%s' }, %.3f);" % (E.theme(TOK, bg)["muted"], t_word(w) - E.LEAD), html, bg)

    def test_emphasised_caption_words_carry_more_weight(self):
        r, html, _ = compose(self, [dict(BOARD["scenes"][0], out="end")], emphasis=["NPV"])
        self.assertIn(".cap .cw.em {", html)
        self.assertRegex(html, r"\.cap \.cw\.em \{[^}]*transform: ?scale\(1\.1\d?\)")


if __name__ == "__main__":
    unittest.main()
