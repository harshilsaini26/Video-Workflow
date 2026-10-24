"""wording.py: plain spoken words. Leaked AI text, invisible characters and a preamble hook fail; stock phrases,
stock structures, em dashes in speech, a hook with nothing concrete in it or longer than 3 s, and over-long lines warn;
the loop back to the hook is a note. Every pattern carries an example that must fire and a lookalike that must not."""
import json, os, unittest
from .helpers import SCRIPTS, run, scratch, write


def lines(*texts, say=None):
    return [{"id": "l%d" % i, "text": t, "say": (say or {}).get(i, t)} for i, t in enumerate(texts)]


HOOK = "3 Excel habits that hide your mistakes"
END = "Fix one Excel habit tonight and follow for part 2"


class Patterns(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(SCRIPTS, "wording.json"), encoding="utf-8") as f:
            self.lists = json.load(f)

    def test_each_fail_pattern_fires(self):
        import wording as W
        for p in self.lists["fail"]:
            r = W.check_lines(lines(HOOK, p["example"], END))
            self.assertTrue(any(m.startswith("line l1:") and p["id"] in m for m in r["fail"]), (p["id"], r))
        for p in self.lists["hook_fail"]:
            r = W.check_lines(lines(p["example"], "Then it gets cheaper", END))
            self.assertTrue(any(m.startswith("line l0:") and p["id"] in m for m in r["fail"]), (p["id"], r))

    def test_each_warn_pattern_fires_and_its_lookalike_does_not(self):
        import wording as W
        for p in self.lists["warn"]:
            fired = W.check_lines(lines(HOOK, p["example"], END))
            self.assertTrue(any(m.startswith("line l1:") and p["id"] in m for m in fired["warn"]), (p["id"], fired))
            calm = W.check_lines(lines(HOOK, p["lookalike"], END))
            self.assertFalse(any(m.startswith("line l1:") for m in calm["warn"] + calm["fail"]), (p["id"], calm))

    def test_ordinary_finance_and_tech_words_pass(self):
        import wording as W
        for t in ("Compound interest grows the balance", "A statistically significant result", "Turn the phone to landscape mode",
                  "It's not working on my laptop", "Comment CABLE and I'll send you the list", "The robust case costs 9 dollars",
                  "Three cards, a pen, and a notebook"):
            r = W.check_lines(lines(HOOK, t, END))
            self.assertEqual([m for m in r["fail"] + r["warn"] if m.startswith("line l1:")], [], t)


class Rules(unittest.TestCase):
    def test_invisible_characters_fail(self):
        import wording as W
        for ch in ("​", "﻿", "⁠"):
            r = W.check_lines(lines(HOOK, "One cable" + ch + " for all", END))
            self.assertTrue(any("invisible" in m for m in r["fail"]), repr(ch))

    def test_em_dash_in_speech_warns_but_not_on_screen(self):
        import wording as W
        r = W.check_lines(lines(HOOK, "One cable for all", END, say={1: "One cable — for all"}))
        self.assertTrue(any(m.startswith("line l1:") and "dash" in m for m in r["warn"]))
        r = W.check_lines(lines(HOOK, "One cable — for all", END, say={1: "One cable for all"}))
        self.assertFalse(any("dash" in m for m in r["warn"]))

    def test_hook_needs_something_concrete(self):
        import wording as W
        r = W.check_lines(lines("This changes how you charge things", "Then it gets cheaper", END))
        self.assertTrue(any(m.startswith("line l0:") and "number or a name" in m for m in r["warn"]))
        r = W.check_lines(lines("USB-C changes how you charge things", "Then it gets cheaper", END))
        self.assertFalse(any("number or a name" in m for m in r["warn"]))

    def test_a_rank_is_not_a_hashtag(self):
        import wording as W
        r = W.check_lines(lines("The #1 mistake new investors make", "Then", END))
        self.assertFalse(any("hashtag" in m for m in r["fail"]), r)

    def test_hook_timing(self):
        import wording as W
        r = W.check_lines(lines("9 things about Excel that nobody ever tells you", "Then", END), rate=2.4)   # 9 words: 3.75 s
        self.assertTrue(any(m.startswith("line l0:") and "3.0 s" in m for m in r["warn"]))
        r = W.check_lines(lines("9 Excel habits nobody tells you", "Then", END), rate=2.4)
        self.assertFalse(any("3.0 s" in m for m in r["warn"]))
        r = W.check_lines([dict(l, dur=d) for l, d in zip(lines(HOOK, "Then", END), (3.4, 1, 1))])   # real times win
        self.assertTrue(any("3.0 s" in m for m in r["warn"]))

    def test_long_lines_warn(self):
        import wording as W
        long_line = " ".join(["word"] * 19)
        r = W.check_lines(lines(HOOK, long_line, END))
        self.assertTrue(any(m.startswith("line l1:") and "split" in m for m in r["warn"]))
        r = W.check_lines(lines(HOOK, " ".join(["word"] * 12), END))
        self.assertFalse(any("split" in m for m in r["warn"]))

    def test_loop_hint(self):
        import wording as W
        r = W.check_lines(lines("One cable charges everything", "Middle", "Three cables now, not one drawer"))
        self.assertEqual(r["note"], [])
        r = W.check_lines(lines("One cable charges everything", "Middle", "Follow for part two"))
        self.assertTrue(any("loop" in m for m in r["note"]))
        self.assertFalse(any("loop" in m for m in r["warn"] + r["fail"]))


class Minors(unittest.TestCase):
    def test_a_joiner_inside_indic_text_is_not_invisible(self):
        import wording as W
        r = W.check_lines(lines("5 \u0915\u094d\u200d\u0937 tips", "\u0928\u093e\u200c\u092e here"))
        self.assertFalse(any("invisible" in m for m in r["fail"]), r["fail"])
        r = W.check_lines(lines("5 tips\u200dhere", "Middle"))                 # between Latin letters it is still hidden
        self.assertTrue(any("invisible" in m for m in r["fail"]))

    def test_teens_and_tens_are_numbers(self):
        import wording as W
        for word in ("seventy", "thirteen", "nineteen", "sixty", "ninety"):
            r = W.check_lines(lines("Why %s percent of people quit" % word, "Middle"))
            self.assertFalse(any("no number" in m for m in r["warn"]), word)

    def test_a_missing_or_bad_script_is_named(self):
        d = scratch(self)
        for path in (os.path.join(d, "nope.json"), write(os.path.join(d, "bad.json"), "{not json")):
            r = run("wording.py", "--script", path)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertNotIn("Traceback", r.stderr)
            self.assertIn(os.path.basename(path), r.stdout + r.stderr)


class Cli(unittest.TestCase):
    def test_script_mode(self):
        d = scratch(self)
        s = {"lines": [{"id": "l0", "say": "Hey guys, in this video", "show": "Hey guys, in this video"},
                       {"id": "l1", "say": "Here's the thing", "show": "Here's the thing"}]}
        r = run("wording.py", "--script", write(os.path.join(d, "script.json"), s))
        self.assertEqual(r.returncode, 1)
        self.assertIn("WORDING FAIL", r.stdout)
        self.assertIn("line l0:", r.stdout)

    def test_transcript_mode_reads_the_kept_cut(self):
        d = scratch(self)
        words = [{"text": t, "start": i * 0.4, "end": i * 0.4 + 0.3} for i, t in
                 enumerate("Hey guys welcome back. 3 cables do everything. Here's the thing. Cut this bit.".split())]
        write(os.path.join(d, "transcript.json"), {"words": words})
        write(os.path.join(d, "cut-list.json"), {"kept": [{"start": 1.6, "end": 4.6}]})      # drops the greeting and the last sentence
        r = run("wording.py", "--transcript", os.path.join(d, "transcript.json"), "--kept", os.path.join(d, "cut-list.json"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WORDING PASS", r.stdout)
        self.assertIn("here-thing", r.stdout)
        self.assertNotIn("greeting", r.stdout)


if __name__ == "__main__":
    unittest.main()
