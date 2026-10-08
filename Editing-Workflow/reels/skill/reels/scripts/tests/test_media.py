"""The ffmpeg-backed Reels scripts: reels-conform.py (vertical cutaways at 60 fps), reels-safezone.py (guides on
snapshots), reels-captions.py (SRT). All media is synthesised with lavfi."""
import os, unittest
from .helpers import ffmpeg, needs_ffmpeg, probe, read, run, scratch, words, write


@needs_ffmpeg
class Conform(unittest.TestCase):
    def src(self, d):
        path = os.path.join(d, "land.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=24", "-f", "lavfi", "-i", "sine=f=440:r=48000", "-t", "5",
               "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", path)
        return path

    def check(self, out, dur):
        p = probe(out)
        v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
        self.assertEqual((v["width"], v["height"]), (1080, 1920))
        self.assertEqual(v["r_frame_rate"], "60/1")
        self.assertFalse([s for s in p["streams"] if s["codec_type"] == "audio"])
        self.assertAlmostEqual(float(p["format"]["duration"]), dur, delta=0.05)
        self.assertTrue(os.path.exists(out + ".sheet.png"))

    def test_landscape_cover_and_blur(self):
        d = scratch(self); src = self.src(d)
        for fit in ("cover", "blur", "contain"):
            out = os.path.join(d, "broll", fit + ".mp4")
            r = run("reels-conform.py", "--in", src, "--out", out, "--start", "0.5", "--dur", "3.5", "--fit", fit, "--focus", "0.3")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.check(out, 3.5)
            self.assertIn("1080x1920, 60/1 fps", r.stdout)

    def test_still_becomes_a_push(self):
        d = scratch(self)
        png = os.path.join(d, "shot.png")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=1280x800", "-frames:v", "1", png)
        out = os.path.join(d, "still.mp4")
        r = run("reels-conform.py", "--in", png, "--out", out, "--dur", "2", "--fit", "blur")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.check(out, 2.0)

    def test_too_long_is_refused(self):
        d = scratch(self); src = self.src(d)
        out = os.path.join(d, "x.mp4")
        r = run("reels-conform.py", "--in", src, "--out", out, "--start", "3", "--dur", "4")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("longer than the source", r.stderr)
        self.assertFalse(os.path.exists(out))


@needs_ffmpeg
class SafeZone(unittest.TestCase):
    def test_guides_any_9x16_size_and_skips_others(self):
        d = scratch(self)
        snaps = os.path.join(d, "snaps"); os.makedirs(snaps)
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=1080x1920", "-frames:v", "1", os.path.join(snaps, "a.png"))
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=540x960", "-frames:v", "1", os.path.join(snaps, "b.png"))
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=1920x1080", "-frames:v", "1", os.path.join(snaps, "c.png"))
        out = os.path.join(snaps, "guides")
        r = run("reels-safezone.py", "--dir", snaps, "--out", out, "--sheet")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("skip", r.stdout)
        for name, size in (("a.png", (1080, 1920)), ("b.png", (540, 960))):
            v = probe(os.path.join(out, name))["streams"][0]
            self.assertEqual((v["width"], v["height"]), size)
        self.assertTrue(os.path.exists(os.path.join(out, "sheet.png")))
        self.assertFalse(os.path.exists(os.path.join(out, "c.png")))


class StoryboardMd(unittest.TestCase):
    def test_all_formats_and_assets(self):
        from .test_compose import ALL
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), dict(ALL, loop={"first": "Stop paying", "last": "it's free", "note": "the claim returns"}))
        assets = write(os.path.join(d, "ASSET-REQUESTS.md"),
                       "| id | kind | beat | at | dur | spec | owner | state | file | source | licence | used | note |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
                       "| r01 | logo | lg | 3.55 | 1.4 | OBS logo | Asset scout | filled | ../_shared/img/obs.svg | obsproject.com | brand logo | whole | - |\n"
                       "| r02 | sfx | lg | 3.85 | 0.4 | pop | Asset scout | skip | - | - | - | - | none fit |\n")
        out = os.path.join(d, "deliver", "STORYBOARD.md")
        r = run("reels-storyboard-md.py", "--spec", sp, "--out", out, "--title", "t v1", "--assets", assets, "--note", "first cut")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        md = read(out)
        for needle in ("| 0.0 - 1.5 | hook text | Stop paying for editing | - |", "| 1.9 - 3.2 | pills | Free, No watermark |",
                       "count-up number | $1,000 · saved a month", "**Loop:** last \"it's free\"", "| r01 | logo | ../_shared/img/obs.svg |",
                       "## What changed"):
            self.assertIn(needle, md)
        self.assertNotIn("| r02 |", md)       # only filled rows are delivered


class Captions(unittest.TestCase):
    def test_srt_with_terms(self):
        d = scratch(self)
        tr = write(os.path.join(d, "transcript.json"), words("I@0 use@0.3 hyperframes@0.6 and@0.9 parakeet.@1.2 Then@3.0 export@3.3 it@3.6 late@20"))
        out = os.path.join(d, "captions.srt")
        r = run("reels-captions.py", "--transcript", tr, "--out", out, "--terms", "HyperFrames,Parakeet", "--duration", "10")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = read(out)
        self.assertIn("I use HyperFrames and Parakeet", s)
        self.assertIn("00:00:00,000 --> ", s)
        self.assertNotIn("late", s)
        self.assertIn("wrote %s: 2 cues" % out, r.stdout)


if __name__ == "__main__":
    unittest.main()
