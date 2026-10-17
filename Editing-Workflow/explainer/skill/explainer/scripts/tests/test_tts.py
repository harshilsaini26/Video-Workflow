"""tts-kokoro.py: the voice, line by line, joined with pauses, levelled (the fake engine stands in for Kokoro)."""
import importlib.util, json, os, unittest, wave
from .helpers import needs_ffmpeg, read, run, scratch, write

HAS_KOKORO = importlib.util.find_spec("kokoro") is not None


def five(word):
    return " ".join([word] * 5)


def duration(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


@needs_ffmpeg
class Voice(unittest.TestCase):
    def make(self, lines, target=None, extra=()):
        d = scratch(self)
        s = {"title": "t", "lines": lines, "payoff": lines[-1]["id"], "cta": lines[-1]["id"], "sources": {}}
        if target:
            s["target_seconds"] = target
        sp = write(os.path.join(d, "script.json"), s)
        out = os.path.join(d, "voice.wav")
        r = run("tts-kokoro.py", "--script", sp, "--out", out, "--engine", "fake", *extra)
        return d, sp, out, r

    def three(self):
        return [{"id": "l0", "say": five("alpha"), "show": five("alpha"), "break": "comma"},
                {"id": "l1", "say": five("beta"), "show": five("beta"), "break": "section"},
                {"id": "l2", "say": five("gamma"), "show": five("gamma"), "break": "sentence"}]

    def test_fake_engine_lines_and_pauses(self):
        d, sp, out, r = self.make(self.three())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for i in range(3):
            self.assertTrue(os.path.exists(os.path.join(d, "lines", "l%d.wav" % i)))
        self.assertAlmostEqual(duration(out), 3 * 5 * 0.32 + 0.15 + 0.6, delta=0.05)
        with wave.open(out) as w:
            self.assertEqual((w.getframerate(), w.getnchannels()), (48000, 1))
        with wave.open(os.path.join(d, "lines", "l0.wav")) as w:
            self.assertEqual((w.getframerate(), w.getnchannels()), (24000, 1))

    def test_only_regenerates_one_line(self):
        d, sp, out, r = self.make(self.three())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        paths = {i: os.path.join(d, "lines", "l%d.wav" % i) for i in range(3)}
        for p in paths.values():
            os.utime(p, (1000000000, 1000000000))
        os.utime(out, (1000000000, 1000000000))
        r = run("tts-kokoro.py", "--script", sp, "--out", out, "--engine", "fake", "--only", "l1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(os.path.getmtime(paths[0]), 1000000000)
        self.assertEqual(os.path.getmtime(paths[2]), 1000000000)
        self.assertNotEqual(os.path.getmtime(paths[1]), 1000000000)
        self.assertNotEqual(os.path.getmtime(out), 1000000000)

    def test_levels_and_peak(self):
        d, sp, out, r = self.make(self.three())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertAlmostEqual(res["lufs"], -16, delta=1)
        self.assertLessEqual(res["peak"], -1.0)
        self.assertAlmostEqual(res["duration"], duration(out), delta=0.01)

    def test_length_gate(self):
        d, sp, out, r = self.make(self.three(), target=60)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("off target by", r.stdout + r.stderr)
        d, sp, out, r = self.make(self.three(), target=5.5)   # 5.55 s: within 10%
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_samples_are_ten_seconds_and_measure_each_voices_rate(self):
        # SOP S4 and S6: the RAG reel's samples were 3.5 s (one short hook line) and its length was planned at a rate
        # the voice never spoke; the samples now run past 10 s and each voice's words a second is written down
        lines = [{"id": "l%d" % i, "say": " ".join(["word"] * 8), "show": "x", "break": "sentence"} for i in range(6)]
        d = scratch(self)
        rates = os.path.join(d, "voice-rates.json")
        write(rates, {"_note": "kept", "am_michael@1": 2.4})
        _, _, _, r = self.make(lines, extra=("--samples", os.path.join(d, "samples"), "--rates", rates))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        got = json.load(open(rates))
        self.assertEqual(got["_note"], "kept")
        for v in ("af_heart", "am_michael", "bf_emma"):
            self.assertGreaterEqual(duration(os.path.join(d, "samples", v + ".wav")), 10.0, v)
            self.assertAlmostEqual(got["%s@1" % v], 1 / 0.32, delta=0.05)      # the fake voice: 0.32 s a word

    def test_lexicon_is_applied(self):
        lines = [{"id": "l0", "say": "estimate the WACC and WACCs first", "show": "estimate the WACC first"}]
        d, sp, out, r = self.make(lines)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(read(os.path.join(d, "lines", "l0.txt")).strip(), "estimate the wack and WACCs first")

    @unittest.skipUnless(HAS_KOKORO, "kokoro is not installed")
    def test_real_kokoro_smoke(self):
        d = scratch(self)
        sp = write(os.path.join(d, "script.json"), {"title": "t", "lines": [{"id": "l0", "say": "Hello there, friends.", "show": "Hello there, friends."}],
                                                     "payoff": "l0", "cta": "l0", "sources": {}})
        out = os.path.join(d, "voice.wav")
        r = run("tts-kokoro.py", "--script", sp, "--out", out, "--voice", "af_heart")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertGreater(duration(out), 0.5)
        self.assertGreater(json.loads(r.stdout.strip().splitlines()[-1])["lufs"], -40)


class Gate(unittest.TestCase):
    def tts(self):
        import importlib.util
        from .helpers import SCRIPTS
        spec = importlib.util.spec_from_file_location("tts_kokoro", os.path.join(SCRIPTS, "tts-kokoro.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_true_peak_over_minus_1_fails(self):
        g = self.tts().gate_errors
        self.assertEqual(g(60.0, -1.2, 60), [])
        self.assertTrue(any("true peak -0.6 dBTP" in e for e in g(60.0, -0.6, 60)))
        self.assertTrue(any("off target by" in e for e in g(80.0, -1.2, 60)))
