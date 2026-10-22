"""motion-check.py (gate E6): the rendered reel is never still for long. Measured on the file, on this machine, with
FFmpeg: frames at 10 fps, small and grey; a frame is still when under 0.1% of it changes visibly (by more than 5/255)
from the one before. The reference reel is still 3% of the time and never longer than 0.4 s; the RAG reel was still 48%
of the time."""
import glob, json, os, subprocess, unittest
from .helpers import load, needs_ffmpeg, run, scratch, write
from .test_layout import have_browser


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


def drawn(path, frame, seconds, fps=30, w=360, h=640):
    """A video drawn frame by frame: frame(i) -> bytes of one w x h grey frame."""
    n = int(seconds * fps)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "%dx%d" % (w, h), "-r", str(fps),
                    "-i", "-", "-pix_fmt", "yuv420p", path], input=b"".join(frame(i) for i in range(n)), check=True)
    return path


def square(i, w=360, h=640, ground=230):
    """A 16 px square crossing a flat ground, 4 px a frame: a small thing moving, as a cursor or a particle does."""
    img = bytearray([ground]) * (w * h)
    x0, y0 = (40 + 4 * i) % (w - 16), 300
    for y in range(y0, y0 + 16):
        img[y * w + x0: y * w + x0 + 16] = bytes([120]) * 16
    return bytes(img)


@needs_ffmpeg
class MotionCheck(unittest.TestCase):
    def test_a_small_thing_moving_is_not_still(self):
        # a frame's average change dilutes a small motion by the frame's size: the eye still sees it move
        v = drawn(os.path.join(scratch(self), "sq.mp4"), square, 3)
        r = run("motion-check.py", "--video", v)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_faint_change_over_the_whole_frame_is_still(self):
        # the whole ground brightening by a level a frame changes every pixel a little: nothing is seen to move
        v = drawn(os.path.join(scratch(self), "fade.mp4"), lambda i: bytes([150 + i // 3]) * (360 * 640), 3)
        r = run("motion-check.py", "--video", v)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("E6 FAIL", r.stdout)

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


# a page whose square moves for 1 s, stands still 1.5 s, then moves again: its seek draws the square at time t
PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>html, body { margin:0; }
#stage { position:relative; width:1080px; height:1920px; background:#e6e9ef; } #sq { position:absolute; top:900px; width:120px;
height:120px; background:#4c4f69; }</style></head><body><div id="stage" data-composition-id="t" data-duration="4">
<div id="sq"></div></div><script>window.__timelines = {"t": {"seek": function (t) {
  var x = t < 1 ? t : t < 2.5 ? 1 : t - 1.5; document.getElementById("sq").style.left = (60 + 300 * x) + "px"; }}};</script>
</body></html>"""


@unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome (npx hyperframes browser ensure)")
class MotionOnThePage(unittest.TestCase):
    def test_a_frozen_page_fails(self):
        page = write(os.path.join(scratch(self), "public", "index.html"), PAGE)
        r = run("motion-check.py", "--index", page)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"E6 FAIL: still from 1\.[01]\d? to 2\.[4-6]")

    def test_a_living_page_passes(self):
        from .test_compose import BOARD, VOICE, silent_wav, words30
        vendor = os.environ.get("EXPLAINER_VENDOR")
        if not vendor or not os.path.exists(os.path.join(vendor, "gsap.min.js")):
            self.skipTest("needs the real vendor folder (EXPLAINER_VENDOR: gsap)")
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        out = os.path.join(d, "public")
        c = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), BOARD), "--out", out, "--vendor", vendor)
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)
        r = run("motion-check.py", "--index", os.path.join(out, "index.html"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("E6 PASS", r.stdout)

    def test_boil_is_off_while_measuring(self):
        d = scratch(self)
        page = write(os.path.join(d, "public", "index.html"), PAGE)
        r = run("motion-check.py", "--index", page, "--keep-job", os.path.join(d, "job.json"))
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)
        job = load(os.path.join(d, "job.json"))
        self.assertIs(job["boil"], False)
        self.assertTrue(job["gray"])
        self.assertEqual(job["size"], [180, 320])
        self.assertEqual(len(job["shots"]), 40)                       # 4 s at 10 fps


if __name__ == "__main__":
    unittest.main()
