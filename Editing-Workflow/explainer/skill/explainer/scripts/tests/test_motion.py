"""motion-check.py (gate E6): the rendered reel is never still for long. Measured on the file, on this machine, with
FFmpeg: frames at 10 fps, small and grey; a frame is still when it differs from the one before by under 0.25/255 on
average. The reference reel is still 7% of the time and never longer than 0.5 s; the RAG reel was still 67% of the time."""
import os, subprocess, unittest
from .helpers import needs_ffmpeg, run, scratch


def video(path, parts):
    """parts: [("move"|"still", seconds)] joined into one small video."""
    segs = []
    for i, (kind, sec) in enumerate(parts):
        src = "testsrc2=size=360x640:rate=30" if kind == "move" else "color=c=0xe6e9ef:size=360x640:rate=30"
        p = path + ".%d.mp4" % i
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, "-t", str(sec), "-pix_fmt", "yuv420p", p], check=True)
        segs.append(p)
    lst = path + ".txt"
    with open(lst, "w", encoding="utf-8") as f:
        f.write("".join("file '%s'\n" % s for s in segs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", path], check=True)
    return path


@needs_ffmpeg
class MotionCheck(unittest.TestCase):
    def test_a_moving_reel_passes(self):
        v = video(os.path.join(scratch(self), "a.mp4"), [("move", 4)])
        r = run("motion-check.py", "--video", v)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("E6 PASS", r.stdout)

    def test_a_still_picture_fails_with_its_times(self):
        v = video(os.path.join(scratch(self), "b.mp4"), [("move", 1.5), ("still", 2.5), ("move", 1.0)])
        r = run("motion-check.py", "--video", v)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E6 FAIL", r.stdout)
        self.assertRegex(r.stdout, r"still from 1\.[4-6]\d? to 4\.[0-1]")

    def test_the_limits_can_be_set(self):
        v = video(os.path.join(scratch(self), "c.mp4"), [("move", 3), ("still", 0.8), ("move", 3)])
        self.assertEqual(run("motion-check.py", "--video", v).returncode, 0)
        self.assertNotEqual(run("motion-check.py", "--video", v, "--max-still", "0.5").returncode, 0)


if __name__ == "__main__":
    unittest.main()
