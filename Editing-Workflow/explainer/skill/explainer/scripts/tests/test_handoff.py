"""The editor hand-off (explainer): no rendered reel, an editable project. handoff.py lays the voice, the music, the
sound effects and each scene as its own transparent clip on its own track of an FCP 7 XML (filmcraft, Premiere,
Resolve), with markers for the hook and each scene's word and source, and the captions as an .srt."""
import array, copy, glob, json, os, re, shutil, unittest, wave
from .helpers import load, read, run, scratch, write
from .test_compose import BOARD, t_word
from .test_foundations import compose
import explainer_lib as E

GFX = ("ground", "captions", "hook", "n1", "cu")


def project(test, board=None):
    b = copy.deepcopy(board or BOARD)
    b["scenes"][2]["source"] = "s1"
    r, d = compose(test, b)
    test.assertEqual(r.returncode, 0, r.stdout)
    write(os.path.join(d, "notes.json"), [{"t": 2.0, "name": "Check", "comment": "is the pause too long?"}])
    gfx = os.path.join(d, "layers")                 # render-layers.py writes here; the hand-off copies into edit/media/gfx
    os.makedirs(gfx)
    for n in GFX:
        write(os.path.join(gfx, n + (".mp4" if n == "ground" else ".mov")), "stand-in")
    return d


def handoff(d, *extra):
    return run("handoff.py", "--project", d, "--no-render", "--xml-only", *extra)


def xml_of(d):
    X = E.find_kit("nle_xml")
    return X.parse(os.path.join(d, "edit", os.path.basename(d) + ".xml")), X


class Layout(unittest.TestCase):
    def test_tracks_and_order(self):
        d = project(self)
        r = handoff(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        p, _ = xml_of(d)
        self.assertEqual((p["width"], p["height"], p["timebase"]), (1080, 1920, 60))
        self.assertEqual([t["name"] for t in p["video"]], ["ground", "thread", "scenes", "transitions", "brand", "captions (styled)"])
        self.assertEqual([t["enabled"] for t in p["video"]], [True, True, True, True, True, False])
        self.assertTrue(p["video"][0]["clips"][0]["pathurl"].endswith("/gfx/ground.mp4"))
        self.assertEqual([t["name"] for t in p["audio"]], ["voice", "music", "sfx"])
        self.assertTrue(all(t["clips"] for t in p["audio"]))

    def test_every_scene_lands_on_its_frame(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        p, X = xml_of(d)
        tl = X.Timeline("t", 1080, 1920, 60)
        m = {s["id"]: s for s in load(os.path.join(d, "public", "moments.json"))["scenes"]}
        clips = {c["name"]: c for c in p["video"][2]["clips"]}
        self.assertEqual(sorted(clips), ["cu", "hook", "n1"])
        for sid, c in clips.items():
            self.assertEqual(c["start"], tl.frames(m[sid]["in"]), sid)
            self.assertEqual(c["end"], tl.frames(m[sid]["out"]), sid)

    def test_markers_carry_anchor_and_source(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        p, _ = xml_of(d)
        by = {m["name"]: m for m in p["markers"]}
        self.assertEqual(by["Hook"]["frame"], 0)
        self.assertIn("1.0 s", by["Hook"]["comment"])
        self.assertIn("cu · count-up", by)
        self.assertIn("source: s1", by["cu · count-up"]["comment"])
        self.assertIn("word18", by["cu · count-up"]["comment"])
        self.assertEqual(by["Check"]["frame"], 120)

    def test_captions_srt_matches_the_transcript(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        srt = read(os.path.join(d, "edit", "captions.srt"))
        self.assertTrue(srt.startswith("1\n00:00:"))
        words = load(os.path.join(d, "transcript.json"))["words"]
        self.assertIn(words[0]["text"], srt)
        self.assertIn(words[-1]["text"], srt)

    def test_media_is_copied_next_to_the_xml(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        for n in ("voice.wav", "music.wav", "sfx.wav"):
            self.assertTrue(os.path.isfile(os.path.join(d, "edit", "media", n)), n)
        self.assertTrue(os.path.isfile(os.path.join(d, "edit", "HANDOFF.md")))
        self.assertIn("captions (styled)", read(os.path.join(d, "edit", "HANDOFF.md")))


class Disk(unittest.TestCase):
    def test_layer_clips_are_hard_linked_and_a_failed_run_keeps_the_last_edit(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        self.assertEqual(os.stat(os.path.join(d, "layers", "n1.mov")).st_ino, os.stat(os.path.join(d, "edit", "media", "gfx", "n1.mov")).st_ino)
        write(os.path.join(d, "notes.json"), "[ broken")
        r = handoff(d)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(d, "edit", os.path.basename(d) + ".xml")))
        self.assertFalse(os.path.exists(os.path.join(d, "edit.v1")))


class Stems(unittest.TestCase):
    def test_stems_are_written_and_sum_to_the_bed(self):
        d = project(self)
        pub = os.path.join(d, "public")

        def samples(n):
            with wave.open(os.path.join(pub, n)) as w:
                return array.array("h", w.readframes(w.getnframes()))
        bed, music, sfx = samples("bed.wav"), samples("music.wav"), samples("sfx.wav")
        n = min(len(bed), len(music), len(sfx))
        self.assertGreater(n, 48000)
        err = sum((bed[i] - music[i] - sfx[i]) ** 2 for i in range(0, n, 7)) / (n / 7.0)
        sig = sum(bed[i] ** 2 for i in range(0, n, 7)) / (n / 7.0)
        self.assertLess(err, sig * 1e-4 + 4)        # within -40 dB: the stems are the bed, split


class Stale(unittest.TestCase):
    def test_a_quiet_recompose_drops_the_old_stems(self):
        d = project(self)
        pub = os.path.join(d, "public")
        self.assertTrue(os.path.exists(os.path.join(pub, "music.wav")))
        b = load(os.path.join(d, "storyboard.json"))
        b["sound"] = {"music": "none", "sfx": False}
        write(os.path.join(d, "storyboard.json"), b)
        r = run("explainer-compose.py", "--spec", os.path.join(d, "storyboard.json"), "--out", pub)
        self.assertEqual(r.returncode, 0, r.stdout)
        for n in ("music.wav", "sfx.wav", "bed.wav"):
            self.assertFalse(os.path.exists(os.path.join(pub, n)), n)

    def test_a_layer_clip_shorter_than_its_slot_is_named(self):
        import subprocess
        d = project(self)
        clipf = os.path.join(d, "layers", "n1.mov")
        os.remove(clipf)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=60:d=0.2", clipf], check=True)
        r = handoff(d)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("n1.mov", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


class Notes(unittest.TestCase):
    def test_handoff_md_speaks_to_an_explainer_and_gives_the_qa_path(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        md = read(os.path.join(d, "edit", "HANDOFF.md"))
        self.assertNotIn("camera files", md)
        path = re.search(r'python3 "([^"]+qa-export\.py)"', md).group(1)
        self.assertTrue(os.path.isfile(path), path)


class Errors(unittest.TestCase):
    def test_missing_layer_clip_is_named(self):
        d = project(self)
        os.remove(os.path.join(d, "layers", "n1.mov"))
        r = handoff(d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("n1", r.stdout)
        self.assertIn("render-layers.py", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_rerun_replaces_the_edit_folder(self):
        d = project(self)
        self.assertEqual(handoff(d).returncode, 0)
        self.assertEqual(handoff(d).returncode, 0)
        self.assertEqual(len(glob.glob(os.path.join(d, "edit", "*.xml"))), 1)
        kept = glob.glob(os.path.join(d, "edit.v*"))
        self.assertEqual(len(kept), 1)                  # the first one is kept aside, never deleted (the creator may have edited it)


if __name__ == "__main__":
    unittest.main()
