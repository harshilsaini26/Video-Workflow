"""paper-cut.py: a removed sentence spoken in the same breath as a kept one is cut out of the audio, not only struck
from the text (with --speech the kept run used to run on to the end of its speech chunk)."""
import os, unittest
from .helpers import load, run, scratch, write

# "Hello there my friends. Today we build a thing. Cut that. Today we build a great thing." in one breath
SPOKEN = [("Hello", 0.40), ("there", 0.70), ("my", 1.00), ("friends.", 1.25),
          ("Today", 1.90), ("we", 2.15), ("build", 2.35), ("a", 2.60), ("thing.", 2.75),
          ("Cut", 3.40), ("that.", 3.65),
          ("Today", 4.30), ("we", 4.55), ("build", 4.75), ("a", 5.00), ("great", 5.15), ("thing.", 5.45)]
REMOVED = (1.90, 3.65 + 0.30)       # the flub and the marker: from "Today" (1.90) to the end of "that." (3.95)


def transcript():
    return {"words": [{"text": t, "start": s, "end": round(s + 0.30, 3)} for t, s in SPOKEN]}


def speech_one_chunk():
    # auto-editor v1: one speech chunk from 0.30 s to 7.70 s (frames at 30 fps), silence after it
    return {"version": "1", "timebase": "30/1", "source": "raw.mp4", "chunks": [[0, 9, 99999], [9, 231, 1], [231, 240, 99999]]}


class PaperCut(unittest.TestCase):
    def cut(self, speech):
        d = scratch(self)
        args = ["--transcript", write(os.path.join(d, "t.json"), transcript()), "--duration", "8.0", "--out-dir", d]
        if speech:
            args += ["--speech", write(os.path.join(d, "speech.v1"), speech_one_chunk())]
        r = run("paper-cut.py", *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return load(os.path.join(d, "cut-list.json"))

    def assert_removed_is_not_kept(self, cl):
        reasons = {x["text"]: x["reason"] for x in cl["removed"] if x["text"]}
        self.assertIn("Cut that.", reasons)
        self.assertIn("Today we build a thing.", reasons)
        a, z = REMOVED
        for seg in cl["kept"]:
            self.assertFalse(seg["start"] < z and seg["end"] > a, "kept %r overlaps the removed %.2f-%.2f" % (seg, a, z))
        # and both kept sentences are still there
        self.assertTrue(any(s["start"] <= 0.40 and s["end"] >= 1.55 for s in cl["kept"]), cl["kept"])
        self.assertTrue(any(s["start"] <= 4.30 and s["end"] >= 5.75 for s in cl["kept"]), cl["kept"])

    def test_same_breath_flub_is_cut_with_speech_chunks(self):
        self.assert_removed_is_not_kept(self.cut(speech=True))

    def test_same_breath_flub_is_cut_without_speech_chunks(self):
        self.assert_removed_is_not_kept(self.cut(speech=False))
