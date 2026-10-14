"""align-script.py (gate E2): the voice's recognised words matched to the script, display words timed."""
import os, unittest
from .helpers import load, run, scratch, write
import explainer_lib as E


def asr_from(words, t0=0.5, step=0.35, dur=0.3, holes=None):
    """Recognised words at a steady pace; holes = {index: extra seconds before that word}."""
    out, t = [], t0
    for i, w in enumerate(words):
        t += (holes or {}).get(i, 0.0)
        out.append({"text": w, "start": round(t, 3), "end": round(t + dur, 3)})
        t += step
    return {"words": out}


class Align(unittest.TestCase):
    def align(self, lines, asr):
        d = scratch(self)
        sp = write(os.path.join(d, "script.json"), {"title": "t", "lines": lines, "payoff": lines[-1]["id"], "cta": lines[-1]["id"], "sources": {}})
        ap = write(os.path.join(d, "asr.json"), asr)
        out = os.path.join(d, "transcript.json")
        r = run("align-script.py", "--script", sp, "--asr", ap, "--out", out, "--report", os.path.join(d, "VOICE.md"))
        return r, (load(out) if os.path.exists(out) else None)

    def test_exact_match_gives_asr_times(self):
        lines = [{"id": "l0", "say": "Hello there friends.", "show": "Hello there friends."}]
        asr = asr_from(["Hello", "there", "friends."])
        r, t = self.align(lines, asr)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([w["text"] for w in t["words"]], ["Hello", "there", "friends."])
        self.assertEqual([w["start"] for w in t["words"]], [w["start"] for w in asr["words"]])
        self.assertEqual({w["line"] for w in t["words"]}, {"l0"})
        self.assertIn("100.0% aligned", r.stdout)

    def test_say_show_spans_map_times(self):
        lines = [{"id": "l0", "say": "it costs one thousand dollars", "show": "It costs $1,000"}]
        asr = asr_from(["it", "costs", "one", "thousand", "dollars"])
        r, t = self.align(lines, asr)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([w["text"] for w in t["words"]], ["It", "costs", "$1,000"])
        money = t["words"][2]
        self.assertEqual(money["start"], asr["words"][2]["start"])
        self.assertEqual(money["end"], asr["words"][4]["end"])

    def test_asr_writes_digits_for_spoken_numbers(self):
        lines = [{"id": "l0", "say": "it costs one thousand dollars today", "show": "It costs $1,000 today"}]
        asr = asr_from(["it", "costs", "$1,000", "today"])
        r, t = self.align(lines, asr)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("100.0% aligned", r.stdout)
        self.assertEqual(t["words"][2]["text"], "$1,000")
        self.assertEqual(t["words"][2]["start"], asr["words"][2]["start"])
        self.assertEqual(t["words"][2]["end"], asr["words"][2]["end"])

    def test_skipped_word_lowers_ratio_and_fails_under_98(self):
        words = ["w%d" % i for i in range(100)]
        lines = [{"id": "l%d" % k, "say": " ".join(words[k * 20:(k + 1) * 20]), "show": " ".join(words[k * 20:(k + 1) * 20])} for k in range(5)]
        heard = [w for i, w in enumerate(words) if i not in (41, 45, 50)]   # three words of line l2 never spoken
        r, t = self.align(lines, asr_from(heard))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("97.0% aligned", r.stdout + r.stderr)
        self.assertIn("line l2", r.stdout + r.stderr)

    def test_substitution_is_tolerated(self):
        lines = [{"id": "l0", "say": "estimate the wack first", "show": "estimate the WACC first"}]
        r, t = self.align(lines, asr_from(["estimate", "the", "whack", "first"]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("100.0% aligned", r.stdout)
        self.assertEqual(t["words"][2]["text"], "WACC")

    def test_gap_inside_a_line_fails(self):
        lines = [{"id": "l0", "say": "one two three", "show": "one two three"},
                 {"id": "l1", "say": "four five six", "show": "four five six"},
                 {"id": "l2", "say": "seven eight nine", "show": "seven eight nine"}]
        words = "one two three four five six seven eight nine".split()
        r, _ = self.align(lines, asr_from(words, holes={7: 1.55}))        # between "seven" and "eight"
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("gap 1.60 s in line l2", r.stdout + r.stderr)
        r, _ = self.align(lines, asr_from(words, holes={6: 1.55}))        # between lines l1 and l2: fine
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_transcript_shape_feeds_reels_lib(self):
        lines = [{"id": "l0", "say": "Hello there.", "show": "Hello there."}]
        d = scratch(self)
        r, t = self.align(lines, asr_from(["Hello", "there."]))
        out = write(os.path.join(d, "t.json"), t)
        self.assertEqual([w["text"] for w in E.L.load_words(out)], ["Hello", "there."])
