"""filmcraft: the hand-off XML and captions made into a native filmcraft project by filmcraft-cli, and read back.
Skipped when filmcraft-cli is not installed ($FILMCRAFT_CLI or on the PATH)."""
import os, unittest
from .helpers import HAS_FFMPEG, ffmpeg, scratch, write


class Project(unittest.TestCase):
    def setUp(self):
        import filmcraft
        if not filmcraft.find_cli() or not HAS_FFMPEG:
            self.skipTest("needs filmcraft-cli ($FILMCRAFT_CLI or PATH) and ffmpeg")

    def fixture(self):
        import nle_xml as X
        d = scratch(self)
        a, v = os.path.join(d, "a b.mov"), os.path.join(d, "voice.wav")
        ffmpeg("-f", "lavfi", "-i", "testsrc=s=1080x1920:r=60:d=2,format=yuva444p10le", "-c:v", "prores_ks", "-profile:v", "4444", a)
        ffmpeg("-f", "lavfi", "-i", "sine=f=440:d=2", "-ar", "48000", "-ac", "2", v)
        srt = write(os.path.join(d, "captions.srt"), "1\n00:00:00,000 --> 00:00:00,900\nhello there\n\n2\n00:00:01,000 --> 00:00:01,900\nsecond cue\n")
        tl = X.Timeline("fixture", 1080, 1920, 60)
        tl.video_track("scenes").clip(a, 0.5, 2.0, src_in=0.25, duration=2)
        tl.audio_track("voice").clip(v, 0, 2, duration=2)
        tl.marker(0.5, "Hook", "whole by 1.0 s")
        return d, tl.write(os.path.join(d, "fixture.xml")), srt

    def test_xml_becomes_a_project_with_every_clip_online(self):
        import filmcraft
        d, xml, srt = self.fixture()
        res = filmcraft.to_project(xml, srt, os.path.join(d, "fixture.fcproj"))
        self.assertEqual(res["offlineMedia"], [])
        self.assertEqual(res["captions"], 2)
        info = filmcraft.inspect(os.path.join(d, "fixture.fcproj"))
        seq = info["sequence"]
        self.assertEqual((seq["settings"]["width"], seq["settings"]["height"]), (1080, 1920))
        self.assertEqual(seq["settings"]["frame_rate"], {"num": 60, "den": 1})
        clip = seq["video"][0]["items"][0]
        self.assertEqual((clip["startFrame"], clip["endFrame"]), (30, 120))
        self.assertEqual(len(seq["audio"][0]["items"]), 1)
        self.assertEqual([(m["name"], m["comment"]) for m in seq["markers"]], [("Hook", "whole by 1.0 s")])
        self.assertEqual(len(info["captions"]), 2)
        self.assertTrue(all(m["status"] == "online" for m in info["media"]))

    def test_a_bad_xml_is_named(self):
        import filmcraft
        d = scratch(self)
        bad = write(os.path.join(d, "broken.xml"), "<xmeml version=\"4\"><sequence>")
        with self.assertRaises(filmcraft.FilmcraftError) as e:
            filmcraft.to_project(bad, None, os.path.join(d, "x.fcproj"))
        self.assertIn("broken.xml", str(e.exception))


if __name__ == "__main__":
    unittest.main()
