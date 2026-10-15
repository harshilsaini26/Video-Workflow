"""reels_lib: caption chunking, SRT, the safe zone, full digits."""
import unittest
from .helpers import words
import reels_lib as L


def W(spec):
    return words(spec)["words"]


class Chunks(unittest.TestCase):
    def texts(self, chunks):
        return [" ".join(w["text"] for w in c["words"]) for c in chunks]

    def test_max_words(self):
        c = L.chunk_words(W("one@0 two@0.3 three@0.6 four@0.9 five@1.2"), max_words=3, max_chars=40)
        self.assertEqual(self.texts(c), ["one two three", "four five"])

    def test_max_chars(self):
        c = L.chunk_words(W("extraordinarily@0 complicated@0.3 words@0.6"), max_words=3, max_chars=18)
        self.assertEqual(self.texts(c), ["extraordinarily", "complicated words"])

    def test_pause_breaks(self):
        c = L.chunk_words(W("so@0 this@0.3 then@1.5"), max_words=3, max_chars=40)   # 0.9 s gap after "this"
        self.assertEqual(self.texts(c), ["so this", "then"])

    def test_sentence_end_breaks_and_punctuation_is_cleaned(self):
        c = L.chunk_words(W("Done.@0 Next,@0.3 we@0.6 go@0.9 now@1.2"), max_words=3, max_chars=40)
        self.assertEqual(self.texts(c), ["Done", "Next we go", "now"])

    def test_comma_breaks_after_two_words(self):
        c = L.chunk_words(W("first@0 thing,@0.3 then@0.6 more@0.9"), max_words=3, max_chars=40)
        self.assertEqual(self.texts(c), ["first thing", "then more"])

    def test_keeps_question_marks_money_and_percent(self):
        self.assertEqual(L.clean_word("really?"), "really?")
        self.assertEqual(L.clean_word("$1,000."), "$1,000")
        self.assertEqual(L.clean_word("40%,"), "40%")

    def test_timing(self):
        c = L.chunk_words(W("a@0 b@0.3 c@0.6 d@0.9"), max_words=2, max_chars=40, tail=0.6)
        self.assertEqual((c[0]["start"], c[0]["end"]), (0.0, 0.6))     # ends where the next chunk starts
        self.assertEqual((c[1]["start"], c[1]["end"]), (0.6, 1.8))     # the last: its last word's end + tail

    def test_min_duration_never_overlaps_the_next(self):
        ws = [{"text": "a", "start": 0.0, "end": 0.05}, {"text": "b.", "start": 0.1, "end": 0.15}, {"text": "c", "start": 0.2, "end": 0.3}]
        c = L.chunk_words(ws, max_words=3, max_chars=40, min_dur=0.25)
        for x, y in zip(c, c[1:]):
            self.assertLessEqual(x["end"], y["start"])


class Srt(unittest.TestCase):
    def test_format(self):
        s = L.to_srt([{"start": 0.0, "end": 1.5, "words": [{"text": "hello"}, {"text": "there"}]},
                      {"start": 3661.25, "end": 3662.0, "words": [{"text": "late"}]}])
        self.assertIn("1\n00:00:00,000 --> 00:00:01,500\nhello there\n", s)
        self.assertIn("2\n01:01:01,250 --> 01:01:02,000\nlate\n", s)

    def test_two_lines_at_the_middle_space(self):
        self.assertEqual(L.wrap_two_lines("this caption is much longer than one short line", 30),
                         "this caption is much\nlonger than one short line")


class SafeZone(unittest.TestCase):
    def test_box(self):
        self.assertEqual(L.SAFE, {"left": 65, "top": 269, "right": 1015, "bottom": 1248})

    def test_inside(self):
        self.assertTrue(L.inside_safe(65, 290, 950, 300))          # wide, high up
        self.assertFalse(L.inside_safe(65, 200, 950, 100))         # under the top band
        self.assertFalse(L.inside_safe(65, 1100, 950, 100))        # wide in the action-column band
        self.assertTrue(L.inside_safe(150, 1100, 780, 100))        # narrow there is fine
        self.assertFalse(L.inside_safe(150, 1200, 780, 100))       # past the bottom band

    def test_full_digits(self):
        self.assertEqual(L.full_digits(207000000, "$"), "$207,000,000")
        self.assertEqual(L.full_digits(12.5, "", "%", 1), "12.5%")



class TextMetrics(unittest.TestCase):
    def test_widths_from_measured_glyphs(self):
        self.assertAlmostEqual(L.text_width("x", 100), 57.1)                   # DM Sans 700: x is 0.571 em
        self.assertAlmostEqual(L.text_width("ab", 100, "mono500", 0.1), 140.0)  # JetBrains Mono, letter-spaced

    def test_lines_wrap_between_words(self):
        self.assertEqual(L.text_lines("xx xx", 100, 260), 1)                    # 114.2 + 23.5 + 114.2
        self.assertEqual(L.text_lines("xx xx", 100, 240), 2)
        self.assertEqual(L.text_lines("xxxxxxxx", 100, 100), 1)                 # a word never breaks
        self.assertEqual(L.text_lines("xx xx", 100, 252, space=0.26), 2)         # a fixed .26 em gap: 254.4
        self.assertEqual(L.text_lines("xx xx", 100, 255, space=0.26), 1)

    def test_a_count_is_measured_at_its_widest_moment(self):
        # DM Sans digits are proportional (0 is about twice as wide as 1), so on the way to $11,111,111 the count shows
        # $10,000,000, far wider than the final number; every value from 0 up must fit
        self.assertAlmostEqual(L.count_width(11111111, 150, "$", spacing=-0.02), L.text_width("$10,000,000", 150, spacing=-0.02))
        for value, dec in ((12345, 0), (987, 0), (40.5, 1)):
            widest = max(L.text_width(L.full_digits(k / 10 ** dec, "$", "%", dec), 100) for k in range(int(value * 10 ** dec) + 1))
            self.assertGreaterEqual(L.count_width(value, 100, "$", "%", dec) + 1e-9, widest, value)
        self.assertGreater(L.count_width(-250, 100), L.text_width("250", 100))   # a negative count shows its minus


if __name__ == "__main__":
    unittest.main()
