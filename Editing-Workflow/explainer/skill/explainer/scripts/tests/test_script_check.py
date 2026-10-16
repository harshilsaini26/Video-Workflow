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
        r, _ = self.check(script(70))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("under 81 words", r.stdout + r.stderr)
        r, _ = self.check(script(250))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("over 240 words", r.stdout + r.stderr)

    def test_a_short_reel_is_welcome(self):
        # short-form explainers: "a quick how-to in under 30 seconds", "smarter in less than a minute"
        r, _ = self.check(script(90, target=30))            # 30 s -> 81 +- 15% -> 81..93
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("est 33.3 s", r.stdout)

    def test_target_narrows_the_range_inside_81_to_240(self):
        r, _ = self.check(script(200, target=60))          # 60 s -> 162 +- 15% -> 138..186
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

    def test_target_outside_30_to_90_is_named(self):
        for t in (25, 100):
            r, _ = self.check(script(200, target=t))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("target_seconds %d is outside 30 to 90 s" % t, r.stdout)
            self.assertNotIn("under 81", r.stdout)

    # ---- the brief behind a reel that spreads (PLAYBOOK §E1, §E2): advice, so warnings; a misspelt value fails ----
    def brief(self, **over):
        s = script(120, format="how-to", audience="new analysts who freeze at Excel", goal="comment")
        s["lines"][1]["show"] = s["lines"][1]["say"] = "Here is what you do first when the sheet looks scary okay"
        s["lines"][1]["role"] = "step"
        s["lines"][2]["role"] = "step"
        s["lines"][3]["role"] = "example"
        s["lines"][-1]["show"] = s["lines"][-1]["say"] = "Which step trips you up? Comment below"
        s.update(over)
        return s

    def test_a_full_brief_has_no_warnings(self):
        r, _ = self.check(self.brief())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARN", r.stdout)

    def test_a_bare_script_is_told_what_is_missing(self):
        r, _ = self.check(script(120))
        self.assertEqual(r.returncode, 0, r.stdout)
        for word in ("format", "audience", "goal", "you", "question", "example"):
            self.assertRegex(r.stdout, r"E1 WARN: .*%s" % word, word)

    def test_unknown_format_or_goal_fails(self):
        for key, bad in (("format", "dance"), ("goal", "viral")):
            r, _ = self.check(self.brief(**{key: bad}))
            self.assertNotEqual(r.returncode, 0, key)
            self.assertIn("%s %r" % (key, bad), r.stdout)

    def test_the_call_to_action_serves_the_goal(self):
        r, _ = self.check(self.brief(goal="follow"))       # the CTA asks for a comment, the goal is follows
        self.assertEqual(r.returncode, 0)
        self.assertRegex(r.stdout, r"E1 WARN: .*call to action.*follow")

    def test_each_format_has_its_shape(self):
        s = self.brief(format="myth")                       # a myth needs the myth and the truth
        r, _ = self.check(s)
        self.assertRegex(r.stdout, r"E1 WARN: .*myth.*truth")
        s["lines"][4]["role"], s["lines"][5]["role"] = "myth", "truth"
        r, _ = self.check(s)
        self.assertNotIn("WARN", r.stdout)
        r, _ = self.check(self.brief(format="versus"))       # this vs that wants a compare picture
        self.assertRegex(r.stdout, r"E1 WARN: .*versus.*compare")
        r, _ = self.check(self.brief(format="story"))        # a story: the problem, then the solution
        self.assertRegex(r.stdout, r"E1 WARN: .*problem.*solution")

    def test_the_report_carries_the_brief(self):
        d = scratch(self)
        rep_ = os.path.join(d, "SCRIPT.md")
        r = run("script-check.py", "--script", write(os.path.join(d, "script.json"), self.brief()), "--report", rep_)
        md = read(rep_)
        for text in ("how-to", "new analysts who freeze at Excel", "comment"):
            self.assertIn(text, md)
