"""reels-moments.py: reels from a long video. The Director (Claude) still judges what is worth a reel; the script shows
the transcript in windows with absolute times, and checks the picks: the schema, edges snapped to sentences, 15 to 60 s,
overlaps above 50% removed (the higher score kept), lines that need earlier context flagged; then a folder per pick."""
import json, os, unittest
from .helpers import read, run, scratch, write


def long_transcript(d, minutes=6):
    """Sentences of 10 words, 0.4 s a word: one sentence every 4 s; sentence 20 says "as I said"."""
    words, t, n = [], 0.0, 0
    while t < minutes * 60:
        texts = ["As", "I", "said", "the", "cable", "is", "the", "same", "every", "time."] if n == 20 else \
                ["word%d" % k for k in range(9)] + ["end%d." % n]
        for x in texts:
            words.append({"text": x, "start": round(t, 2), "end": round(t + 0.3, 2)})
            t += 0.4
        n += 1
    return write(os.path.join(d, "long-video", "transcript.json"), {"words": words})


def moments(d, picks):
    return write(os.path.join(d, "moments.json"), [dict({"score": 70, "hook": "h", "why": "w", "payoff": "p"}, **p) for p in picks])


class Moments(unittest.TestCase):
    def test_windows_keep_absolute_times(self):
        d = scratch(self)
        r = run("reels-moments.py", "--transcript", long_transcript(d), "--windows", "--minutes", "2", "--overlap", "0.5")
        self.assertEqual(r.returncode, 0, r.stdout)
        parts = r.stdout.split("== window ")
        self.assertGreaterEqual(len(parts), 4)
        self.assertIn("1:30", parts[2].splitlines()[0])                           # the second window starts at 1:30
        self.assertIn("[1:32.00]", parts[2])                                      # its sentences keep their real times

    def test_edges_snap_to_sentences(self):
        d = scratch(self)
        t = long_transcript(d)
        r = run("reels-moments.py", "--transcript", t, "--check", moments(d, [{"start": 61.3, "end": 89.0}]), "--out", os.path.join(d, "MOMENTS.md"))
        self.assertEqual(r.returncode, 0, r.stdout)
        checked = json.loads(read(os.path.join(d, "moments.checked.json")))
        self.assertEqual((checked[0]["start"], checked[0]["end"]), (60.0, 91.9))   # the sentence's first word; its last word's end

    def test_length_bounds(self):
        d = scratch(self)
        t = long_transcript(d)
        for a, b in ((100.0, 111.9), (120.0, 195.9)):
            r = run("reels-moments.py", "--transcript", t, "--check", moments(d, [{"start": a, "end": b}]), "--out", os.path.join(d, "M.md"))
            self.assertEqual(r.returncode, 1, (a, b))
            self.assertIn("moment 1", r.stdout)
            self.assertIn("15 to 60 s", r.stdout)

    def test_overlap_keeps_higher_score(self):
        d = scratch(self)
        t = long_transcript(d)
        m = moments(d, [{"start": 100.0, "end": 139.9, "score": 60}, {"start": 116.0, "end": 155.9, "score": 80},
                        {"start": 200.0, "end": 239.9, "score": 50}, {"start": 224.0, "end": 263.9, "score": 40}])
        r = run("reels-moments.py", "--transcript", t, "--check", m, "--out", os.path.join(d, "M.md"))
        self.assertEqual(r.returncode, 0, r.stdout)
        kept = json.loads(read(os.path.join(d, "moments.checked.json")))
        self.assertEqual([k["score"] for k in kept], [80, 50, 40])               # 60% overlap: the 80 stays; 40%: both stay
        self.assertIn("overlaps", r.stdout)

    def test_context_leak_flagged(self):
        d = scratch(self)
        r = run("reels-moments.py", "--transcript", long_transcript(d), "--check", moments(d, [{"start": 72.0, "end": 103.9}]),
                "--out", os.path.join(d, "M.md"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("as I said", r.stdout)
        self.assertIn("as I said", read(os.path.join(d, "M.md")))

    def test_scaffold_writes_cut_lists(self):
        d = scratch(self)
        t = long_transcript(d)
        m = moments(d, [{"start": 60.0, "end": 91.9}, {"start": 200.0, "end": 239.9}])
        r = run("reels-moments.py", "--transcript", t, "--check", m, "--out", os.path.join(d, "M.md"), "--scaffold", os.path.join(d, "videos"))
        self.assertEqual(r.returncode, 0, r.stdout)
        cl = json.loads(read(os.path.join(d, "videos", "long-video-reel-2", "cut-list.json")))
        self.assertEqual(cl["kept"], [{"start": 200.0, "end": 239.9}])
        self.assertTrue(os.path.isfile(os.path.join(d, "videos", "long-video-reel-1", "MOMENT.md")))

    def test_bad_schema_is_named(self):
        d = scratch(self)
        bad = write(os.path.join(d, "m.json"), [{"start": 10, "score": 50}])
        r = run("reels-moments.py", "--transcript", long_transcript(d), "--check", bad, "--out", os.path.join(d, "M.md"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("moment 1", r.stdout)
        self.assertIn("end", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
