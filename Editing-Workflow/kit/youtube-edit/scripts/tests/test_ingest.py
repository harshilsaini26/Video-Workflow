"""ingest.py --concat: matching clips join by stream copy; mismatched clips (another frame rate, mono audio, no audio)
join in ONE encode with stereo 48 kHz audio throughout, so the audio stays in line with the picture."""
import json, os, subprocess, unittest
from .helpers import ffmpeg, load, needs_ffmpeg, probe, run, scratch


def clip(path, seconds, fps=30, audio="stereo"):
    cmd = ["-f", "lavfi", "-i", "testsrc2=size=320x180:rate=%d:duration=%s" % (fps, seconds)]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s" % seconds, "-ac", "2" if audio == "stereo" else "1"]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
    cmd += (["-c:a", "aac", "-shortest"] if audio else [])
    ffmpeg(*(cmd + [path]))
    return path


def audio_info(path):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=channels,sample_rate",
                                   "-of", "json", path], capture_output=True, text=True, check=True).stdout)
    return [(s["channels"], int(s["sample_rate"])) for s in j["streams"]]


@needs_ffmpeg
class Ingest(unittest.TestCase):
    def test_matching_clips_join_by_stream_copy(self):
        d = scratch(self); raw = os.path.join(d, "raw"); os.makedirs(raw)
        clip(os.path.join(raw, "C0001.mp4"), 2); clip(os.path.join(raw, "C0002.mp4"), 2)
        r = run("ingest.py", "--raw", raw, "--out", d, "--concat")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(load(os.path.join(d, "ingest.json"))["concat"]["stream_copy"])

    def test_mismatched_clips_join_in_one_pass_with_aligned_stereo_audio(self):
        d = scratch(self); raw = os.path.join(d, "raw"); os.makedirs(raw)
        clip(os.path.join(raw, "C0001.mp4"), 2)                          # 30 fps, stereo
        clip(os.path.join(raw, "C0002.mp4"), 2, fps=25, audio="mono")   # another frame rate, mono
        clip(os.path.join(raw, "C0003.mp4"), 2, audio=None)             # no audio track at all
        r = run("ingest.py", "--raw", raw, "--out", d, "--concat")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ing = load(os.path.join(d, "ingest.json"))
        self.assertFalse(ing["concat"]["stream_copy"])
        src = os.path.join(d, "source.mp4")
        streams, _ = probe(src)
        self.assertAlmostEqual(streams["video"], 6.0, delta=0.1)
        self.assertAlmostEqual(streams["audio"], streams["video"], delta=0.1)   # the silent clip keeps the audio in line
        self.assertEqual(audio_info(src), [(2, 48000)])
        self.assertEqual([f for f in os.listdir(d) if f.startswith("raw-normalised")], [])   # no intermediate lossy pass
