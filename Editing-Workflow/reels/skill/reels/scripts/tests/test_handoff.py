"""The editor hand-off (reels and long-form): the kept cut laid on the creator's own camera files (no re-encode), b-roll,
each card as a transparent clip, sound effects, captions, as an FCP 7 XML for filmcraft (or Premiere, or Resolve)."""
import json, os, sys, unittest
from .helpers import KIT_SCRIPTS, ffmpeg, needs_ffmpeg, needs_kit, read, run, scratch, write

PAGE = """<!doctype html>
<html><head></head>
<body>
  <div id="stage" data-composition-id="reel" data-start="0" data-duration="%(D).3f" data-fps="60" data-width="1080" data-height="1920">
    <video id="bg-video" src="input-video.mp4" playsinline data-has-audio="true" data-start="0" data-duration="%(D).3f" data-track-index="1"></video>
    <video class="cutaway-video clip" id="cut1" src="broll.mp4" muted playsinline data-start="0.400" data-duration="0.500" data-media-start="0.200" data-track-index="3"></video>
    <div class="card-host clip" id="host-c1" data-card-id="c1" data-start="0.200" data-duration="1.000" data-track-index="5"><div class="card">A</div></div>
    <div class="clip cap-layer" id="captions" data-start="0" data-duration="%(D).3f" data-track-index="2"><div class="cap" id="cap0">hi</div></div>
    <audio id="sfx-pop-c1" src="sfx/pop.mp3" data-start="0.200" data-duration="0.72" data-track-index="9" data-volume="0.50"></audio>
    <script>
      (function () {
        const tl = window.gsap.timeline({ paused: true });
        tl.to({}, { duration: %(D).3f }, 0);
        window.__timelines = window.__timelines || {};
        window.__timelines["reel"] = tl;
      })();
    </script>
  </div>
</body>
</html>
"""


def camera(path, sec=3, size="1920x1080", rate=60):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ffmpeg("-f", "lavfi", "-i", "testsrc=s=%s:r=%d:d=%s" % (size, rate, sec), "-f", "lavfi", "-i", "sine=d=%s" % sec,
           "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", path)
    return path


def section(test, root, name, kept, clips, D=1.8):
    W = os.path.join(root, name) if name else root
    write(os.path.join(W, "public", "index.html"), PAGE % {"D": D})
    camera(os.path.join(W, "public", "broll.mp4"), 1)
    os.makedirs(os.path.join(W, "public", "sfx"), exist_ok=True)
    ffmpeg("-f", "lavfi", "-i", "sine=d=0.72", os.path.join(W, "public", "sfx", "pop.mp3"))
    write(os.path.join(W, "cut-list.json"), {"source_duration": sum(c[1] for c in clips), "kept": [{"start": a, "end": b} for a, b in kept], "removed": []})
    for n in ("c1", "captions"):
        write(os.path.join(W, "layers", n + ".mov"), "stand-in")
    return W


def ingest(root, clips, fps="60/1", size=(1920, 1080)):
    t, out = 0.0, []
    for path, sec in clips:
        out.append({"file": os.path.basename(path), "path": path, "duration": float(sec), "source_start": t,
                    "width": size[0], "height": size[1], "fps": round(eval(fps), 3), "fps_exact": fps})
        t += sec
    write(os.path.join(root, "ingest.json"), {"raw_dir": os.path.dirname(clips[0][0]), "clips": out})


def parse(W):
    sys.path.insert(0, KIT_SCRIPTS)
    import nle_xml
    return nle_xml.parse(os.path.join(W, "edit", os.path.basename(W) + ".xml"))


@needs_ffmpeg
@needs_kit
class Reels(unittest.TestCase):
    def two_cameras(self):
        d = scratch(self)
        W = os.path.join(d, "reel-01")
        a, b = camera(os.path.join(d, "raw", "A.MP4")), camera(os.path.join(d, "raw", "B.MP4"))
        return W, a, b

    def handoff(self, W, *extra):
        r = run("reels-handoff.py", "--project", W, "--no-render", "--xml-only", *extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return parse(W)

    def test_kept_segments_map_to_camera_files(self):
        W, a, b = self.two_cameras()
        section(self, W, None, [(0.5, 1.5), (3.2, 4.0)], [(a, 3), (b, 3)])
        ingest(W, [(a, 3), (b, 3)])
        p = self.handoff(W)
        self.assertEqual([t["name"] for t in p["video"]], ["footage", "b-roll", "cards", "captions (styled)"])
        self.assertEqual([t["name"] for t in p["audio"]], ["footage audio", "music", "sfx"])
        v1 = p["video"][0]["clips"]
        self.assertEqual([(c["pathurl"].endswith("/A.MP4"), c["in"], c["start"], c["end"]) for c in v1[:1]], [(True, 30, 0, 60)])
        self.assertTrue(v1[1]["pathurl"].endswith("/B.MP4"))
        self.assertEqual((v1[1]["in"], v1[1]["start"], v1[1]["end"]), (12, 60, 108))
        self.assertEqual(len(p["audio"][0]["clips"]), 2)

    def test_a_segment_across_two_clips_splits(self):
        W, a, b = self.two_cameras()
        section(self, W, None, [(2.5, 3.5)], [(a, 3), (b, 3)])
        ingest(W, [(a, 3), (b, 3)])
        v1 = self.handoff(W)["video"][0]["clips"]
        self.assertEqual(len(v1), 2)
        self.assertEqual([(c["in"], c["out"], c["start"], c["end"]) for c in v1], [(150, 180, 0, 30), (0, 30, 30, 60)])
        self.assertTrue(v1[0]["pathurl"].endswith("/A.MP4") and v1[1]["pathurl"].endswith("/B.MP4"))

    def test_no_reencode_raw_is_referenced(self):
        W, a, b = self.two_cameras()
        section(self, W, None, [(0.5, 1.5)], [(a, 3)])
        ingest(W, [(a, 3)])
        p = self.handoff(W)
        self.assertTrue(p["video"][0]["clips"][0]["pathurl"].endswith("/raw/A.MP4"))
        media = os.listdir(os.path.join(W, "edit", "media"))
        self.assertNotIn("A.MP4", media)

    def test_cards_broll_and_sfx(self):
        W, a, b = self.two_cameras()
        section(self, W, None, [(0.5, 1.5)], [(a, 3)])
        ingest(W, [(a, 3)])
        p = self.handoff(W)
        broll = p["video"][1]["clips"][0]
        self.assertEqual((broll["start"], broll["end"], broll["in"]), (24, 54, 12))
        self.assertEqual([(c["name"], c["start"]) for c in p["video"][2]["clips"]], [("c1", 12)])
        self.assertFalse(p["video"][3]["enabled"])
        sfx = p["audio"][2]["clips"][0]
        self.assertEqual((sfx["start"], sfx["name"]), (12, "pop.mp3"))
        self.assertIn("audiolevels", sfx["effects"])

    def test_face_x_sets_position(self):
        W, a, b = self.two_cameras()
        section(self, W, None, [(0.5, 1.5), (1.6, 2.0)], [(a, 3)])
        ingest(W, [(a, 3)])
        write(os.path.join(W, "face-x.json"), {"0": 0.30})
        v1 = self.handoff(W)["video"][0]["clips"]
        self.assertIn("basic", v1[0]["effects"])
        self.assertNotIn("basic", v1[1]["effects"])
        xml = read(os.path.join(W, "edit", "reel-01.xml"))
        self.assertIn("<horiz>-0.2000</horiz>", xml)

    def test_longform_sections_and_chapters(self):
        d = scratch(self)
        W = os.path.join(d, "my-video")
        a = camera(os.path.join(d, "raw", "C0001.MP4"), 4, "1280x720", 30)
        ingest(W, [(a, 4)], fps="30/1", size=(3840, 2160))
        s1 = section(self, W, "01-setup", [(0.0, 1.0)], [(a, 4)], D=1.0)
        s2 = section(self, W, "02-tutorial", [(2.0, 3.0)], [(a, 4)], D=1.0)
        r = run("reels-handoff.py", "--project", W, "--section", s1, "--section", s2, "--format", "16x9", "--no-render", "--xml-only")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        p = parse(W)
        self.assertEqual((p["width"], p["height"], p["timebase"]), (3840, 2160, 30))
        v1 = p["video"][0]["clips"]
        self.assertEqual([(c["start"], c["end"], c["in"]) for c in v1], [(0, 30, 0), (30, 60, 60)])
        self.assertEqual([(m["name"], m["frame"]) for m in p["markers"] if m["name"].startswith("Chapter")],
                         [("Chapter: 01-setup", 0), ("Chapter: 02-tutorial", 30)])
        self.assertEqual([c["start"] for c in p["video"][2]["clips"]], [6, 36])

    def test_a_missing_card_clip_is_named(self):
        W, a, b = self.two_cameras()
        section(self, W, None, [(0.5, 1.5)], [(a, 3)])
        ingest(W, [(a, 3)])
        os.remove(os.path.join(W, "layers", "c1.mov"))
        r = run("reels-handoff.py", "--project", W, "--no-render", "--xml-only")
        self.assertEqual(r.returncode, 1)
        self.assertIn("c1", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
