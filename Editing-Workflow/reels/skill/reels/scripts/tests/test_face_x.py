"""reels-face-x.py: where the speaker is in each kept segment (the median face centre, 0 to 1 of the frame width), so
the editor hand-off can place each footage clip on the face; the creator adjusts it in the editor. OpenCV is optional:
the detector test is skipped without it."""
import importlib.util, json, os, unittest
from .helpers import SCRIPTS, ffmpeg, needs_ffmpeg, read, run, scratch, write

try:
    import cv2                                         # noqa: F401
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def module():
    spec = importlib.util.spec_from_file_location("face_x", os.path.join(SCRIPTS, "reels-face-x.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class FaceX(unittest.TestCase):
    def test_the_median_of_samples(self):
        m = module()
        xs = iter([0.2, 0.3, 0.3, 0.9, 0.3])
        self.assertEqual(m.segment_x(lambda path, t: next(xs), "clip.mp4", 0.0, 5.0, samples=5), 0.3)
        self.assertIsNone(m.segment_x(lambda path, t: None, "clip.mp4", 0.0, 5.0, samples=5))      # no face in any sample

    def test_samples_spread_over_the_segment(self):
        m = module()
        seen = []
        m.segment_x(lambda path, t: seen.append(t) or 0.5, "clip.mp4", 10.0, 20.0, samples=5)
        self.assertEqual(seen, [11.0, 13.0, 15.0, 17.0, 19.0])

    def test_segments_map_to_camera_files_through_ingest(self):
        m = module()
        d = scratch(self)
        write(os.path.join(d, "cut-list.json"), {"kept": [{"start": 1.0, "end": 2.0}, {"start": 4.0, "end": 5.0}]})
        write(os.path.join(d, "ingest.json"), {"clips": [{"path": "/raw/A.MP4", "duration": 3.0, "source_start": 0.0},
                                                          {"path": "/raw/B.MP4", "duration": 3.0, "source_start": 3.0}]})
        calls = []
        out = m.face_x(lambda path, t: calls.append((path, round(t, 2))) or 0.4, os.path.join(d, "cut-list.json"),
                       os.path.join(d, "ingest.json"), None, samples=1)
        self.assertEqual(out, {"0": 0.4, "1": 0.4})
        self.assertEqual(calls, [("/raw/A.MP4", 1.5), ("/raw/B.MP4", 1.5)])

    @needs_ffmpeg
    @unittest.skipUnless(HAS_CV2, "needs opencv-python-headless")
    def test_segments_without_faces_are_omitted(self):
        d = scratch(self)
        src = os.path.join(d, "source.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc=s=640x360:r=30:d=4", "-c:v", "libx264", "-preset", "ultrafast", src)
        write(os.path.join(d, "cut-list.json"), {"kept": [{"start": 0.5, "end": 3.5}]})
        r = run("reels-face-x.py", "--source", src, "--cut-list", os.path.join(d, "cut-list.json"), "--out", os.path.join(d, "face-x.json"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(read(os.path.join(d, "face-x.json"))), {})

    def test_without_opencv_it_says_how_to_get_it(self):
        if HAS_CV2:
            self.skipTest("OpenCV is installed here")
        d = scratch(self)
        write(os.path.join(d, "cut-list.json"), {"kept": [{"start": 0.5, "end": 3.5}]})
        r = run("reels-face-x.py", "--source", os.path.join(d, "x.mp4"), "--cut-list", os.path.join(d, "cut-list.json"), "--out", os.path.join(d, "f.json"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("opencv-python-headless", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
