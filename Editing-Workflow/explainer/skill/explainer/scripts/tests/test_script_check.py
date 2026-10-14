"""script-check.py (gate E1): length, hook, sources, payoff and call to action; the Checkpoint A sheet."""
import os, unittest
from .helpers import read, run, scratch, write


def script(n_words=200, hook_words=8, target=None, **over):
    """A script of n_words shown words: a hook line, then 10-word lines, the last two being payoff and CTA."""
    lines = [{"id": "l0", "say": " ".join(["hook"] * hook_words), "show": " ".join(["hook"] * hook_words), "break": "sentence"}]
    left, i = n_words - hook_words, 1
    while left > 0:
        k = min(10, left)
        words = " ".join(["word"] * k)
        lines.append({"id": "l%d" % i, "say": words, "show": words, "break": "sentence"})
        left -= k; i += 1
    s = {"title": "t", "voice": "am_michael", "lines": lines, "payoff": lines[-2]["id"], "cta": lines[-1]["id"],
         "sources": {"s1": {"title": "Course page", "url": "https://example.com/course", "note": "duration"}}}
    if target:
        s["target_seconds"] = target
    s.update(over)
    return s


class ScriptCheck(unittest.TestCase):
    def check(self, spec, *extra):
        d = scratch(self)
        r = run("script-check.py", "--script", write(os.path.join(d, "script.json"), spec), *extra)
        return r, d

    def test_valid_script_passes_and_estimates_length(self):
        r, _ = self.check(script(200))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("est 74.1 s", r.stdout)
        self.assertIn("200 words", r.stdout)

    def test_too_short_and_too_long_fail(self):
        r, _ = self.check(script(150))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("under 160 words", r.stdout + r.stderr)
        r, _ = self.check(script(250))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("over 240 words", r.stdout + r.stderr)

    def test_target_narrows_the_range_inside_160_to_240(self):
        r, _ = self.check(script(200, target=60))          # 60 s -> 162 +- 15% -> 160..186
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("over 186 words", r.stdout + r.stderr)

    def test_long_hook_fails(self):
        r, _ = self.check(script(200, hook_words=13))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hook is 13 words", r.stdout + r.stderr)

    def test_number_without_source_fails(self):
        s = script(200)
        s["lines"][1]["show"] = "It costs $1,000 to start this course now honestly"
        r, _ = self.check(s)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("l1", r.stdout + r.stderr)
        self.assertIn("no source", r.stdout + r.stderr)
        s["lines"][1]["source"] = "s1"
        r, _ = self.check(s)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s["lines"][1]["source"] = "s9"                      # a key that is not in sources
        r, _ = self.check(s)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("s9", r.stdout + r.stderr)
        s["lines"][1]["source"] = None
        s["lines"][2]["fact"] = True                        # a fact without digits still needs a source
        s["lines"][1]["show"] = "word word word word word word word word word word"
        r, _ = self.check(s)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("l2", r.stdout + r.stderr)

    def test_payoff_and_cta_must_exist(self):
        r, _ = self.check(script(200, cta="l99"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cta", r.stdout + r.stderr)

    def test_report_lists_sources(self):
        d = scratch(self)
        out = os.path.join(d, "SCRIPT.md")
        r = run("script-check.py", "--script", write(os.path.join(d, "script.json"), script(200)), "--report", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        md = read(out)
        self.assertIn("https://example.com/course", md)
        self.assertIn("1. hook hook", md)

    def test_sources_may_be_plain_strings(self):
        d = scratch(self)
        rep = os.path.join(d, "SCRIPT.md")
        r, _ = self.check(script(200, sources={"s1": "Coursera, Financial Markets, 2026, https://example.com"}), "--report", rep)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Coursera, Financial Markets", read(rep))
