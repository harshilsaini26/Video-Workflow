"""assemble.py: a work folder you already had is never deleted (only what the script wrote), a segment with a silent
audio track assembles (loudnorm measures it as -inf and is skipped), and the md5 matches the file."""
import hashlib, os, re, unittest
from .helpers import ffmpeg, needs_ffmpeg, probe, read, run, scratch, write


def clip(path, seconds, audio="sine=frequency=440:sample_rate=48000"):
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=%s" % seconds, "-f", "lavfi", "-i", "%s:duration=%s" % (audio, seconds)
           if not audio.startswith("anullsrc") else audio, "-t", str(seconds),
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path)
    return path


@needs_ffmpeg
class Assemble(unittest.TestCase):
    def manifest(self, d, segments):
        return write(os.path.join(d, "assembly.json"), {"project": "t", "width": 320, "height": 180, "fps": 30, "loudness": -14,
                                                         "segments": segments})

    def test_an_existing_work_folder_is_kept(self):
        d = scratch(self)
        clip(os.path.join(d, "a.mp4"), 1.5)
        work = os.path.join(d, "renders"); os.makedirs(work)
        precious = write(os.path.join(work, "hook-4k.mp4"), "a render the user already had")
        out = os.path.join(d, "deliver", "t.mp4")
        r = run("assemble.py", "--manifest", self.manifest(d, [{"name": "Hook", "file": "a.mp4"}]), "--out", out, "--work", work)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(precious))                       # the user's file survives
        self.assertEqual(sorted(os.listdir(work)), ["hook-4k.mp4"])    # and only the script's own files are gone

    def test_the_default_work_folder_is_removed(self):
        d = scratch(self)
        clip(os.path.join(d, "a.mp4"), 1.5)
        out = os.path.join(d, "deliver", "t.mp4")
        r = run("assemble.py", "--manifest", self.manifest(d, [{"name": "Hook", "file": "a.mp4"}]), "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(d, "assembly-work")))

    def test_a_silent_segment_assembles_and_the_md5_matches(self):
        d = scratch(self)
        clip(os.path.join(d, "a.mp4"), 1.5)
        clip(os.path.join(d, "quiet.mp4"), 1.0, audio="anullsrc=r=48000:cl=stereo")
        out = os.path.join(d, "deliver", "t.mp4")
        r = run("assemble.py", "--manifest", self.manifest(d, [{"name": "Hook", "file": "a.mp4"}, {"name": "Cutaway", "file": "quiet.mp4"}]),
                "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        streams, dur = probe(out)
        self.assertAlmostEqual(dur, 2.5, delta=0.15)
        md5 = re.search(r"md5 ([0-9a-f]{32})", r.stdout).group(1)
        h = hashlib.md5()
        with open(out, "rb") as f:
            h.update(f.read())
        self.assertEqual(md5, h.hexdigest())
        self.assertIn("silent", read(os.path.join(d, "deliver", "ASSEMBLY.md")))
