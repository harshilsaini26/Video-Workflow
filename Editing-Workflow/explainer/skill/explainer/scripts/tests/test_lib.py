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
        self.assertEqual(t["colors"]["cyan"], "#0AF0F0")
        for bg in ("blue", "black", "light"):
            self.assertIn(bg, t["backgrounds"])
        self.assertLessEqual(t["motion"]["exit"], 0.7 * t["motion"]["enter"])

    def test_reels_lib_is_found(self):
        self.assertEqual(E.L.SAFE["bottom"], 1248)
