"""Gate H1 (handoff-check.py): the edit folder checked before it reaches the creator, every problem named by its clip
or file; and qa-export.py: the existing checks run on the creator's own export (it only reports)."""
import os, unittest
from .helpers import ffmpeg, needs_ffmpeg, run, scratch, write

WORDS = [{"text": "one", "start": 0.2, "end": 0.5}, {"text": "cable", "start": 0.6, "end": 1.0}, {"text": "now", "start": 1.6, "end": 1.9}]
SRT = "1\n00:00:00,200 --> 00:00:01,000\none cable\n\n2\n00:00:01,600 --> 00:00:01,900\nnow\n"


def edit(test, size=(1080, 1920), fps=60, voice=((0.0, 2.0),), scenes=("l0", "l1"), srt=SRT, missing=False, past=False):
    import nle_xml as X
    d = scratch(test)
    e = os.path.join(d, "edit")
    tl = X.Timeline("p", size[0], size[1], fps)
    tr = tl.video_track("scenes")
    for i, sid in enumerate(scenes):
        f = write(os.path.join(e, "media", "gfx", sid + ".mov"), "x")
        tr.clip(f, i, i + 1, duration=1.5 if past and i == 0 else 1, src_in=0.6 if past and i == 0 else 0, name=sid)
    v = write(os.path.join(e, "media", "voice.wav"), "x")
    a1 = tl.audio_track("voice")
    for t0, t1 in voice:
        a1.clip(v, t0, t1, src_in=t0, duration=2.0)
    xml = tl.write(os.path.join(e, "p.xml"))
    if missing:
        os.remove(os.path.join(e, "media", "gfx", scenes[0] + ".mov"))
    write(os.path.join(e, "captions.srt"), srt)
    write(os.path.join(d, "transcript.json"), {"words": WORDS})
    write(os.path.join(d, "storyboard.json"), {"scenes": [{"id": "l0"}, {"id": "l1"}]})
    return d, e


def check(d, e, profile="explainer"):
    return run("handoff-check.py", "--edit", e, "--profile", profile, "--transcript", os.path.join(d, "transcript.json"),
               "--storyboard", os.path.join(d, "storyboard.json"))


class Gate(unittest.TestCase):
    def test_clean_handoff_passes(self):
        d, e = edit(self)
        r = check(d, e)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("H1 PASS", r.stdout)

    def test_missing_media_fails(self):
        d, e = edit(self, missing=True)
        r = check(d, e)
        self.assertEqual(r.returncode, 1)
        self.assertIn("H1 FAIL: l0", r.stdout)
        self.assertIn("no file", r.stdout)

    def test_clip_outside_source_fails(self):
        d, e = edit(self, past=True)
        r = check(d, e)
        self.assertEqual(r.returncode, 1)
        self.assertIn("H1 FAIL: l0", r.stdout)
        self.assertIn("past the end", r.stdout)

    def test_wrong_sequence_settings_fail(self):
        d, e = edit(self, size=(1920, 1080), fps=30)
        r = check(d, e)
        self.assertEqual(r.returncode, 1)
        self.assertIn("1080x1920", r.stdout)
        self.assertEqual(check(*edit(self, size=(3840, 2160), fps=30), profile="longform").returncode, 0)

    def test_voice_gap_under_speech_fails(self):
        d, e = edit(self, voice=((0.0, 1.2), (1.95, 2.0)))
        r = check(d, e)
        self.assertEqual(r.returncode, 1)
        self.assertIn("“now”", r.stdout)

    def test_scene_without_clip_fails(self):
        d, e = edit(self, scenes=("l0",))
        r = check(d, e)
        self.assertEqual(r.returncode, 1)
        self.assertIn("H1 FAIL: l1", r.stdout)

    def test_srt_mismatch_fails(self):
        d, e = edit(self, srt="1\n00:00:00,200 --> 00:00:01,000\none cable\n")
        r = check(d, e)
        self.assertEqual(r.returncode, 1)
        self.assertIn("captions.srt", r.stdout)
        self.assertIn("now", r.stdout)

    def test_no_xml_is_named(self):
        d = scratch(self)
        r = run("handoff-check.py", "--edit", os.path.join(d, "edit"), "--profile", "reels")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no .xml", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


@needs_ffmpeg
class QaExport(unittest.TestCase):
    def test_reports_size_rate_loudness_and_never_fails(self):
        d = scratch(self)
        v = os.path.join(d, "export.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc=s=1920x1080:r=30:d=2", "-f", "lavfi", "-i", "sine=d=2",
               "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", v)
        r = run("qa-export.py", "--video", v, "--profile", "reels")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("size 1920x1080 (want 1080x1920)", r.stdout)
        self.assertIn("LUFS", r.stdout)
        self.assertIn("QA-EXPORT:", r.stdout)


if __name__ == "__main__":
    unittest.main()
