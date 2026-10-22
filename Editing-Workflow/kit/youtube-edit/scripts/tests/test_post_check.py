"""post-check.py: the post caption (POST.md) checked before the creator posts it: a hook that shows before "more"
(125 characters), 3 to 5 hashtags at the end, one ask with nothing-for-nothing bait refused, no dead closer, no leaked
AI text, and every number in it sourced in the script."""
import os, unittest
from .helpers import run, scratch, write

SCRIPT = {"lines": [{"id": "l0", "say": "One cable now charges almost everything", "show": "One cable now charges almost everything"},
                    {"id": "l1", "say": "up to two hundred and forty watts", "show": "up to 240 watts", "source": "s2"},
                    {"id": "l2", "say": "eighty gigabits a second", "show": "80 Gbps", "source": "s1"}],
          "sources": {"s1": {"title": "USB4 v2 (2022)", "note": "80 Gbps"}, "s2": {"title": "USB PD 3.1", "note": "up to 240 W"}}}
GOOD = """One cable now carries 240 watts. Here is what that means for your drawer.

Your old chargers can go: one USB-C cable runs a laptop, a monitor and a phone.

Save this for the next time you buy a cable.

#usbc #techtips #cables #gadgets"""


def check(test, post, *extra, script=SCRIPT):
    d = scratch(test)
    return run("post-check.py", "--post", write(os.path.join(d, "POST.md"), post), "--script", write(os.path.join(d, "script.json"), script), *extra)


class Post(unittest.TestCase):
    def test_a_good_caption_passes(self):
        r = check(self, GOOD)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("POST PASS", r.stdout)

    def test_first_line_over_125_fails(self):
        r = check(self, "One cable " * 14 + "\n\n#a #b #c")
        self.assertEqual(r.returncode, 1)
        self.assertIn("125", r.stdout)

    def test_first_line_hashtag_fails(self):
        self.assertEqual(check(self, "#usbc One cable for all\n\n#a #b #c").returncode, 1)
        self.assertEqual(check(self, "@brand One cable for all\n\n#a #b #c").returncode, 1)

    def test_over_2200_fails(self):
        r = check(self, "One cable for all.\n\n" + "words " * 400 + "\n\n#a #b #c")
        self.assertEqual(r.returncode, 1)
        self.assertIn("2,200", r.stdout)

    def test_six_hashtags_fail(self):
        r = check(self, GOOD + " #one #two")
        self.assertEqual(r.returncode, 1)
        self.assertIn("6 hashtags", r.stdout)

    def test_mid_sentence_hashtag_fails(self):
        r = check(self, "One cable for all.\n\nThe #usbc cable runs a laptop.\n\n#a #b #c")
        self.assertEqual(r.returncode, 1)
        self.assertIn("mid-sentence", r.stdout)

    def test_bait_fails_but_own_keyword_passes(self):
        for bait in ("Tag 3 friends who need this", "Double tap if you agree", "Comment YES if you agree"):
            r = check(self, GOOD.replace("Save this for the next time you buy a cable.", bait))
            self.assertEqual(r.returncode, 1, bait)
            self.assertIn("bait", r.stdout)
        ok = GOOD.replace("Save this for the next time you buy a cable.", "Comment CABLE and I'll send you the list")
        self.assertEqual(check(self, ok, "--keyword", "CABLE").returncode, 0)

    def test_dead_closer_fails(self):
        r = check(self, GOOD.replace("Save this for the next time you buy a cable.", "What do you think?"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("closer", r.stdout)

    def test_leaked_ai_text_fails(self):
        self.assertEqual(check(self, GOOD.replace("Your old", "As of my last update, your old")).returncode, 1)

    def test_unsourced_number_fails_sourced_passes(self):
        r = check(self, GOOD.replace("240 watts", "300 watts"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("300", r.stdout)
        for same in ("240 W", "two hundred and forty watts", "80 Gbps", "eighty gigabits"):
            self.assertEqual(check(self, GOOD.replace("240 watts", same)).returncode, 0, same)

    def test_finance_names_and_ranks_are_not_numbers_or_hashtags(self):
        for first in ("The one habit that grows your 401k", "The #1 mistake new investors make", "Your 401(k) match, explained"):
            r = check(self, GOOD.replace("One cable now carries 240 watts. Here is what that means for your drawer.", first))
            self.assertEqual(r.returncode, 0, (first, r.stdout))

    def test_the_keyword_ignores_case(self):
        r = check(self, GOOD.replace("Save this for the next time you buy a cable.", "Comment PLAN and I will send you the list."),
                  "--keyword", "plan")
        self.assertNotIn("bait", r.stdout)

    def test_a_missing_post_or_bad_script_is_named(self):
        d = scratch(self)
        r = run("post-check.py", "--post", os.path.join(d, "nope.md"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("nope.md", r.stdout + r.stderr)
        r = run("post-check.py", "--post", write(os.path.join(d, "POST.md"), GOOD), "--script", write(os.path.join(d, "s.json"), "{bad"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("s.json", r.stdout + r.stderr)

    def test_warnings_do_not_fail(self):
        r = check(self, GOOD.replace("#usbc #techtips #cables #gadgets", "#usbc") + "\n\nFollow for more and share it \U0001F525\U0001F525\U0001F525\U0001F525")
        self.assertEqual(r.returncode, 0, r.stdout)
        for w in ("hashtag", "ask", "emoji"):
            self.assertRegex(r.stdout, r"POST WARN: .*%s" % w, w)


if __name__ == "__main__":
    unittest.main()
