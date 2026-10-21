"""script-check.py (gate E1): length, hook, sources, payoff and call to action; the Checkpoint A sheet."""
import os, unittest
from .helpers import read, run, scratch, write


def script(n_words=150, hook_words=8, target=None, **over):
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
        # the estimate is the voice's own rate (2.4 words a second for am_michael until measured) plus the pauses
        r, _ = self.check(script(150))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("150 words", r.stdout)
        self.assertIn("est 67.8 s", r.stdout)          # 150 / 2.4 = 62.5 s, plus 15 sentence pauses of 0.35 s
        self.assertIn("2.4 words a second", r.stdout)

    def test_too_short_and_too_long_fail(self):
        r, _ = self.check(script(50))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("under 30 s", r.stdout)
        r, _ = self.check(script(220))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("over 90 s", r.stdout)

    def test_a_measured_rate_sets_the_budget(self):
        # SOP S4: the RAG reel was planned at 2.7 words a second and ran 91.8 s; the rate is the voice's, measured
        d = scratch(self)
        rates = write(os.path.join(d, "voice-rates.json"), {"af_heart@1": 3.0})
        r, _ = self.check(script(230, voice="af_heart"), "--rates", rates)
        self.assertEqual(r.returncode, 0, r.stdout)     # 230 / 3.0 = 76.7 s + 8 s of pauses
        r, _ = self.check(script(230, voice="af_heart"))
        self.assertIn("over 90 s", r.stdout)            # at the default 2.4 it would not fit

    def test_a_short_reel_is_welcome(self):
        # short-form explainers: "a quick how-to in under 30 seconds", "smarter in less than a minute"
        r, _ = self.check(script(70, target=30))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_target_narrows_the_range(self):
        r, _ = self.check(script(150, target=45))      # 67.8 s against 45 s +- 15%
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("over the 45 s target", r.stdout)

    def test_a_90_s_target_is_a_target(self):
        # SOP S16: the RAG reel's target was set to 85 because a 90 s target failed the word count; 90 is valid
        r, _ = self.check(script(185, target=90))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_too_many_section_breaks_fail(self):
        # SOP S5: at most 3 section breaks in 75 s; each is a long pause the viewer feels
        s = script(150)
        for ln in s["lines"][1:6]:
            ln["break"] = "section"
        r, _ = self.check(s)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("5 section breaks", r.stdout)

    def test_the_voiced_length_is_checked_with_trims_to_offer(self):
        # SOP S16: voiced once before Checkpoint A, the real length decides; over 90 s, the lines to trim are listed
        from .test_compose import silent_wav
        d = scratch(self)
        s = script(150)
        s["lines"][3]["say"] = s["lines"][3]["show"] = " ".join(["long"] * 18)
        sp = write(os.path.join(d, "script.json"), s)
        silent_wav(os.path.join(d, "voice.wav"), 91.0)
        r = run("script-check.py", "--script", sp, "--voice", os.path.join(d, "voice.wav"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("voiced 91.0 s", r.stdout)
        self.assertIn("trim", r.stdout)
        self.assertRegex(r.stdout, r"l3 \(18 words\)")
        self.assertNotRegex(r.stdout, r"\bl0 \(")                 # the hook, the payoff and the CTA are not offered
        silent_wav(os.path.join(d, "voice.wav"), 70.0)
        r = run("script-check.py", "--script", sp, "--voice", os.path.join(d, "voice.wav"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("voiced 70.0 s", r.stdout)

    def test_long_hook_fails(self):
        r, _ = self.check(script(150, hook_words=13))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hook is 13 words", r.stdout + r.stderr)

    def test_number_without_source_fails(self):
        s = script(150)
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
        r, _ = self.check(script(150, cta="l99"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cta", r.stdout + r.stderr)

    def test_report_lists_sources(self):
        d = scratch(self)
        out = os.path.join(d, "SCRIPT.md")
        r = run("script-check.py", "--script", write(os.path.join(d, "script.json"), script(150)), "--report", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        md = read(out)
        self.assertIn("https://example.com/course", md)
        self.assertIn("1. hook hook", md)

    def test_sources_may_be_plain_strings(self):
        d = scratch(self)
        rep = os.path.join(d, "SCRIPT.md")
        r, _ = self.check(script(150, sources={"s1": "Coursera, Financial Markets, 2026, https://example.com"}), "--report", rep)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Coursera, Financial Markets", read(rep))

    def test_target_outside_30_to_90_is_named(self):
        for t in (25, 100):
            r, _ = self.check(script(150, target=t))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("target_seconds %d is outside 30 to 90 s" % t, r.stdout)
            self.assertNotIn("under 30 s", r.stdout)

    # ---- the brief behind a reel that spreads (PLAYBOOK §E1, §E2): advice, so warnings; a misspelt value fails ----
    def brief(self, **over):
        s = script(120, format="how-to", audience="new analysts who freeze at Excel", goal="comment")
        s["lines"][0]["show"] = s["lines"][0]["say"] = "3 Excel habits that hide your mistakes"
        s["lines"][0]["source"] = "s1"
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

    def test_wording_fails_block_e1(self):
        # plain spoken words (PLAYBOOK §E2): a preamble hook or leaked AI text fails E1, naming the line
        s = self.brief()
        s["lines"][0]["show"] = s["lines"][0]["say"] = "Hey guys, in this video, 3 Excel habits"
        s["lines"][2]["say"] = s["lines"][2]["show"] = "As of my last update this works"
        r, _ = self.check(s)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("E1 FAIL:", r.stdout)
        self.assertIn("  - line l0: greeting", r.stdout)
        self.assertIn("  - line l2: last-update", r.stdout)

    def test_wording_warnings_reach_SCRIPT_md(self):
        s = self.brief()
        s["lines"][2]["say"] = s["lines"][2]["show"] = "Here's the thing about the sheet you fear"
        d = scratch(self)
        rep = os.path.join(d, "SCRIPT.md")
        r = run("script-check.py", "--script", write(os.path.join(d, "script.json"), s), "--report", rep)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("E1 WARN: line l2: here-thing", r.stdout)
        self.assertIn("line l2: here-thing", read(rep))

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
