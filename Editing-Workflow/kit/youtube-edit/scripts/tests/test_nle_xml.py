"""nle_xml: the FCP 7 XML (xmeml v4) the editor hand-off writes. filmcraft, Premiere and Resolve import it."""
import os, unittest
from .helpers import scratch, write


def files(d, *names):
    return [write(os.path.join(d, n), "x") for n in names]


class Writer(unittest.TestCase):
    def test_round_trip_keeps_tracks_clips_and_markers(self):
        import nle_xml as X
        d = scratch(self)
        a, b, v = files(d, "a.mov", "b.mov", "voice.wav")
        tl = X.Timeline("demo", 1080, 1920, 60)
        v1, v2 = tl.video_track("scenes"), tl.video_track("captions", enabled=False)
        a1 = tl.audio_track("voice")
        v1.clip(a, 0.0, 1.0, duration=1.0)
        v2.clip(b, 0.5, 2.0, src_in=0.25, duration=3.0)
        a1.clip(v, 0.0, 2.0, duration=2.0)
        tl.marker(0.0, "Hook", "whole by 1.0 s")
        tl.marker(1.5, "l1 · title")
        p = X.parse(tl.write(os.path.join(d, "demo.xml")))
        self.assertEqual((p["name"], p["width"], p["height"], p["timebase"], p["ntsc"]), ("demo", 1080, 1920, 60, False))
        self.assertEqual([t["enabled"] for t in p["video"]], [True, False])
        self.assertEqual(len(p["audio"]), 1)
        c = p["video"][1]["clips"][0]
        self.assertEqual((c["start"], c["end"], c["in"], c["out"]), (30, 120, 15, 105))
        self.assertTrue(c["pathurl"].startswith("file://") and c["pathurl"].endswith("/b.mov"))
        self.assertEqual([(m["frame"], m["name"]) for m in p["markers"]], [(0, "Hook"), (90, "l1 · title")])
        self.assertEqual(p["markers"][0]["comment"], "whole by 1.0 s")

    def test_seconds_to_frames(self):
        import nle_xml as X
        self.assertEqual(X.Timeline("t", 1080, 1920, 60).frames(1.0), 60)
        self.assertEqual(X.Timeline("t", 1080, 1920, 60).frames(2.508), 150)
        self.assertEqual(X.Timeline("t", 1920, 1080, 30).frames(0.034), 1)

    def test_ntsc_frames_do_not_drift(self):
        import nle_xml as X
        tl = X.Timeline("t", 3840, 2160, 29.97)
        self.assertEqual((tl.timebase, tl.ntsc), (30, True))
        self.assertEqual(tl.frames(600.0), 17982)

    def test_pathurl_encoding(self):
        import nle_xml as X
        self.assertEqual(X.to_pathurl("/a b/c#d%e/é.mov"), "file:///a%20b/c%23d%25e/%C3%A9.mov")
        self.assertEqual(X.to_pathurl("C:\\x\\y z.mov"), "file:///C:/x/y%20z.mov")

    def test_one_file_element_per_path(self):
        import nle_xml as X
        d = scratch(self)
        a, = files(d, "a.mov")
        tl = X.Timeline("t", 1080, 1920, 60)
        tr = tl.video_track("v")
        tr.clip(a, 0, 1, duration=5)
        tr.clip(a, 1, 2, src_in=3, duration=5)
        with open(tl.write(os.path.join(d, "t.xml")), encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text.count("<pathurl>"), 1)
        self.assertEqual(text.count('<file id="'), 2)

    def test_scale_and_position_are_written(self):
        # a landscape camera file on a vertical reel: scaled to cover the frame (filmcraft imports at 100%)
        import nle_xml as X
        d = scratch(self)
        a, = files(d, "a.mov")
        tl = X.Timeline("t", 1080, 1920, 60)
        tl.video_track("v").clip(a, 0, 1, duration=1, scale=177.7778, position=(0.6321, 0.0))
        p = X.parse(tl.write(os.path.join(d, "t.xml")))
        self.assertIn("basic", p["video"][0]["clips"][0]["effects"])
        with open(os.path.join(d, "t.xml"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("<parameterid>scale</parameterid>", text)
        self.assertIn("<value>177.7778</value>", text)
        self.assertIn("<horiz>0.6321</horiz>", text)

    def test_validate_names_each_problem(self):
        import nle_xml as X
        d = scratch(self)
        a, = files(d, "a.mov")
        tl = X.Timeline("t", 1080, 1920, 60)
        tr = tl.video_track("v")
        tr.clip(a, 0, 2, src_in=0, duration=1, name="too-long")
        tr.clip(a, 1.5, 2.5, duration=5, name="overlaps")
        tl.video_track("w").clip(os.path.join(d, "gone.mov"), 0, 1, duration=1, name="missing")
        probs = "\n".join(tl.validate())
        for name in ("too-long", "overlaps", "missing"):
            self.assertIn(name, probs)


if __name__ == "__main__":
    unittest.main()
