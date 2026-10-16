"""explainer_lib: word anchors, tokens, and finding the Reels helpers."""
import unittest

import explainer_lib as E

W = [{"text": "Hello", "start": 1.0, "end": 1.3}, {"text": "there", "start": 1.4, "end": 1.7}]


class Lib(unittest.TestCase):
    def test_resolve_word_and_lead(self):
        self.assertEqual(E.resolve("word:1", W), 1.4)
        self.assertAlmostEqual(E.resolve("word:1", W, lead=True), 1.2)
        self.assertEqual(E.resolve(3.5, W), 3.5)
        self.assertEqual(E.anchor_text("word:0", W), "Hello")
        self.assertEqual(E.anchor_text(3.5, W), "-")

    def test_resolve_rejects_bad_anchors(self):
        for ref in ("word:9", "w:1", "word:x", "word:-1"):
            with self.assertRaises(ValueError, msg=ref):
                E.resolve(ref, W)

    def test_tokens_have_the_house_colours(self):
        t = E.load_tokens()
        self.assertEqual(E.theme(t, "mantle")["accent"], "#1e66f5")    # Catppuccin Latte blue (test_theme has the rest)
        self.assertLessEqual(t["motion"]["exit"], 0.7 * t["motion"]["enter"])

    def test_reels_lib_is_found(self):
        self.assertEqual(E.L.SAFE["bottom"], 1248)

    def test_text_metrics_from_glyphs(self):
        self.assertAlmostEqual(E.text_width("x", 100), 57.1)                 # DM Sans 700: x is 0.571 em
        self.assertAlmostEqual(E.text_width("ab", 100, "mono500"), 120.0)    # JetBrains Mono: 0.6 em a character
        self.assertAlmostEqual(E.text_width("ab", 100, "mono500", 0.1), 140.0)
        self.assertEqual(E.text_lines("xx xx", 100, 260), 1)                  # 114.2 + 23.5 + 114.2
        self.assertEqual(E.text_lines("xx xx", 100, 240), 2)
        self.assertEqual(E.text_lines("xxxxxxxx", 100, 100), 1)              # a word never breaks: min_width catches it
