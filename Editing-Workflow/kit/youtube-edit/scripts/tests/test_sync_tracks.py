"""sync-tracks.py: the offset's sign (positive = B started after A) and --write-aligned trimming the earlier file."""
import json, os, unittest
from .helpers import ffmpeg, needs_ffmpeg, probe, run, scratch


def take(path, seconds, start=0.0):
    """A clip whose audio is one seeded noise take; `start` cuts the head off, like a recorder started later."""
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=160x90:rate=30:duration=12",
           "-f", "lavfi", "-i", "anoisesrc=d=12:c=pink:r=48000:a=0.5:seed=7",
           "-ss", "%.3f" % start, "-t", "%.3f" % seconds,
           "-c:v", "libx264", "-preset", "ultrafast", "-g", "1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path)
    return path


@needs_ffmpeg
class SyncTracks(unittest.TestCase):
    def offset(self, a, b, *extra):
        r = run("sync-tracks.py", "--a", a, "--b", b, *extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout[:r.stdout.rindex("}") + 1]), r

    def test_b_started_later_is_positive_and_the_earlier_file_is_trimmed(self):
        d = scratch(self)
        a = take(os.path.join(d, "cam.mp4"), 10)                 # the camera started first
        b = take(os.path.join(d, "screen.mp4"), 8, start=2.0)    # the screen recorder started 2 s later
        res, _ = self.offset(a, b)
        self.assertAlmostEqual(res["offset_b_after_a"], 2.0, delta=0.01)
        self.assertGreater(res["confidence"], 3)
        out = os.path.join(d, "aligned")
        self.offset(a, b, "--write-aligned", out)
        _, cam = probe(os.path.join(out, "cam-aligned.mp4"))
        _, scr = probe(os.path.join(out, "screen-aligned.mp4"))
        self.assertAlmostEqual(cam, 8.0, delta=0.1)              # the 2 s head came off the camera file
        self.assertAlmostEqual(scr, 8.0, delta=0.1)              # the screen file is untouched

    def test_b_started_first_is_negative(self):
        d = scratch(self)
        a = take(os.path.join(d, "cam.mp4"), 8, start=2.0)
        b = take(os.path.join(d, "screen.mp4"), 10)
        res, _ = self.offset(a, b)
        self.assertAlmostEqual(res["offset_b_after_a"], -2.0, delta=0.01)
