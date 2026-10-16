"""kinetic: the hook as kinetic type, from data (no Claude-written code): a big hero token, one or two words beside it, a
claim line that can be struck through, and a punch that lands last; every piece rises out of its mask on its word."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY

HOOK = {"type": "kinetic", "id": "hk", "bg": "mantle", "in": "word:0", "out": "word:12",
        "big": {"text": "3", "at": "word:0"}, "words": [{"text": "STEP", "at": "word:1"}, {"text": "TRICK", "at": "word:2"}],
        "line": {"text": "AI INVENTS", "at": "word:5"}, "strike": {"word": "INVENTS", "at": "word:7"},
        "punch": {"text": "LESS", "at": "word:7"}, "source": "s1"}
TAIL = {"type": "title", "id": "tail", "bg": "mantle", "in": "word:12", "out": D, "text": "The end"}


class Kinetic(unittest.TestCase):
    def build(self, scene):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [scene, TAIL]})
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
        return r, (read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else "")

    def test_the_type_fits_any_width_it_is_given(self):
        mod = REGISTRY["kinetic"]
        long = dict(HOOK, big={"text": "90%", "at": "word:0"}, words=[{"text": "OF", "at": "word:1"}, {"text": "SCRIPTS", "at": "word:2"}])
        for w in (950, 780, mod.min_width(long)):     # any width the composer may give it
            z = mod.sizes(long, w)
            self.assertLessEqual(E.text_width("90%", z["big"], spacing=mod.TRACK) + z["gap"]
                                 + E.text_width("SCRIPTS", z["word"], spacing=mod.TRACK), w)
        self.assertLessEqual(mod.min_width(long), 780)
        self.assertGreater(mod.height(HOOK, 950), mod.height(long, mod.min_width(long)))

    def test_every_piece_rises_on_its_word(self):
        r, html = self.build(HOOK)
        self.assertEqual(r.returncode, 0, r.stdout)
        body = html.split('id="host-hk"')[1].split('id="host-tail"')[0]
        self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), 6)   # big, 2 words, line, strike, punch
        for sel, w in (("#hk-b", 0), ("#hk-w1", 2), ("#hk-l", 5), ("#hk-p", 7)):
            t = max(0.0, t_word(w) - E.LEAD)
            self.assertRegex(html, r"tl\.fromTo\('%s', \{ yPercent: 110 \}, \{ yPercent: 0, duration: [\d.]+, ease: 'expo\.out', "
                                   r"immediateRender: false \}, %.3f\);" % (sel, t))
        self.assertRegex(html, r"tl\.fromTo\('#hk-x', \{ scaleX: 0 \}, \{ scaleX: 1, duration: [\d.]+, ease: 'power3\.inOut'")

    def test_the_hero_and_the_punch_are_the_accent(self):
        r, html = self.build(HOOK)
        acc = E.theme(E.load_tokens(), "mantle")["accent"]
        self.assertRegex(html, r'<span class="kn-big" id="hk-b"[^>]*style="color:%s' % acc)
        self.assertRegex(html, r'<span class="kn-p" id="hk-p"[^>]*style="color:%s' % acc)

    def test_bad_data_fails_with_a_reason(self):
        cases = [(dict(HOOK, strike={"word": "MAGIC", "at": "word:7"}), "strike"),
                 (dict(HOOK, big={"text": "12345", "at": "word:0"}), "big"),
                 (dict(HOOK, words=[{"text": "A", "at": "word:1"}] * 3), "words"),
                 (dict(HOOK, punch={"text": "far far less", "at": "word:7"}), "punch"),
                 ({k: v for k, v in HOOK.items() if k not in ("big", "words")}, "big or words")]
        for sc, word in cases:
            r, _ = self.build(sc)
            self.assertNotEqual(r.returncode, 0, word)
            self.assertIn(word, r.stdout, word)

    def test_a_line_too_wide_fails(self):
        r, _ = self.build(dict(HOOK, line={"text": "ARTIFICIAL INTELLIGENCE INVENTS EVERYTHING ALL DAY LONG", "at": "word:5"}))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("wider than the", r.stdout)


if __name__ == "__main__":
    unittest.main()
