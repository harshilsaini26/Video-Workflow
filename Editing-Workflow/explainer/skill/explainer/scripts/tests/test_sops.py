"""The RAG reel's SOPs as tools: Checkpoint B stills of settled scenes (S10), the skill's version pinned and checked
(S11, S12), each version in a clean folder (S14)."""
import json, os, shutil, unittest
from .helpers import SCRIPTS, needs_ffmpeg, read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
from .test_layout import have_browser
from scenes import png_size


def composed(test):
    d = scratch(test)
    write(os.path.join(d, "transcript.json"), {"words": words30()})
    silent_wav(os.path.join(d, "voice.wav"), VOICE)
    sp = write(os.path.join(d, "storyboard.json"), BOARD)
    r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
    test.assertEqual(r.returncode, 0, r.stdout)
    return d


class Stills(unittest.TestCase):
    @unittest.skipUnless(have_browser(), "needs node, puppeteer and Chrome")
    def test_checkpoint_b_gets_settled_stills_and_the_hook_in_three(self):
        # S10: one full-size still per scene once it is fully built (never mid-entrance), the hook at 0.3, 0.7 and
        # 1.0 s, a fresh sheet: nothing stale from an earlier build
        d = composed(self)
        out = os.path.join(d, "snaps", "stills")
        write(os.path.join(out, "old-still.png"), "stale")
        r = run("stills.py", "--index", os.path.join(d, "public", "index.html"), "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        names = sorted(os.listdir(out))
        self.assertNotIn("old-still.png", names)
        for n in ("hook-0.30.png", "hook-0.70.png", "hook-1.00.png", "STILLS.md"):
            self.assertIn(n, names)
        scenes = [n for n in names if n[0].isdigit()]
        self.assertEqual(len(scenes), 3, names)                 # hook, n1, cu
        self.assertEqual(png_size(os.path.join(out, scenes[0])), (1080, 1920))
        md = read(os.path.join(out, "STILLS.md"))
        self.assertIn("settled", md)
        self.assertIn("n1", md)
        if shutil.which("ffmpeg"):
            self.assertIn("sheet.png", names)

    def test_a_folder_holding_other_work_is_never_wiped(self):
        # a slip such as --out videos/<project> must not delete the script, the voice and STATUS.md
        d = scratch(self)
        keep = write(os.path.join(d, "proj", "STATUS.md"), "# Status")
        r = run("stills.py", "--index", os.path.join(d, "public", "index.html"), "--out", os.path.join(d, "proj"))
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(keep))
        self.assertIn("STATUS.md", r.stdout + r.stderr)


class SkillVersion(unittest.TestCase):
    def test_a_skill_changed_after_its_pin_is_named(self):
        # S12: STATUS.md pins the skill's version; a skill updated mid-project (or a maker's edit, S11) is caught
        d = scratch(self)
        skill = os.path.join(d, "skill")
        shutil.copytree(os.path.dirname(SCRIPTS), skill, ignore=shutil.ignore_patterns("__pycache__", "vendor", "tests"))
        status = write(os.path.join(d, "STATUS.md"), "# Status\n\n| Field | Value |\n|---|---|\n| Project | t |\n")
        tool = os.path.join(skill, "scripts", "skill-version.py")
        import subprocess, sys
        go = lambda *a: subprocess.run([sys.executable, tool] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
        r = go("--pin", status)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(read(status), r"\| Skill \| [0-9a-f]{12} \|")
        self.assertEqual(go("--check", status).returncode, 0)
        with open(os.path.join(skill, "scripts", "explainer-compose.py"), "a", encoding="utf-8") as f:
            f.write("\n# a maker's edit\n")
        r = go("--check", status)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("explainer-compose.py", r.stdout)

    def test_the_voice_rates_the_skill_writes_itself_do_not_break_the_pin(self):
        # tts-kokoro.py --samples writes voice-rates.json into the skill at Checkpoint A, after the pin taken at ingest:
        # machine-written state is not a change to the skill
        d = scratch(self)
        skill = os.path.join(d, "skill")
        shutil.copytree(os.path.dirname(SCRIPTS), skill, ignore=shutil.ignore_patterns("__pycache__", "vendor", "tests"))
        status = write(os.path.join(d, "STATUS.md"), "# Status\n\n| Field | Value |\n|---|---|\n| Project | t |\n")
        tool = os.path.join(skill, "scripts", "skill-version.py")
        import subprocess, sys
        go = lambda *a: subprocess.run([sys.executable, tool] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(go("--pin", status).returncode, 0)
        write(os.path.join(skill, "voice-rates.json"), '{"am_michael@1": 2.61}')
        write(os.path.join(skill, ".DS_Store"), "x")
        r = go("--check", status)
        self.assertEqual(r.returncode, 0, r.stdout)


class Preflight(unittest.TestCase):
    def test_the_machine_is_written_down_once_with_failing_tests_named(self):
        # S3: the RAG reel's Windows machine was never prepared: python3 missing, UTF-8 off, four failing tests nobody
        # looked at; the preflight records how this machine runs everything, and names each failing test
        d = scratch(self)
        suite = os.path.join(d, "suite")
        write(os.path.join(suite, "tests", "__init__.py"), "")
        write(os.path.join(suite, "tests", "test_x.py"), "import unittest\nclass T(unittest.TestCase):\n"
              "    def test_passes(self):\n        pass\n    def test_breaks(self):\n        self.fail('no')\n")
        out = os.path.join(d, "pre")
        r = run("preflight.py", "--out", out, "--suite", "demo=%s" % suite)
        self.assertNotEqual(r.returncode, 0, r.stdout)            # a failing test is a finding, not a pass
        md = read(os.path.join(out, "PREFLIGHT.md"))
        import sys
        self.assertIn(sys.executable, md)
        self.assertIn("PYTHONUTF8", md)
        self.assertIn("test_breaks", md)
        self.assertNotIn("test_passes", md)
        data = json.load(open(os.path.join(out, "preflight.json"), encoding="utf-8"))
        self.assertEqual(data["suites"]["demo"]["failed"], ["tests.test_x.T.test_breaks"])
        self.assertIn("python", data)
        self.assertIn("ffmpeg", data["tools"])


class NewVersion(unittest.TestCase):
    def test_each_version_starts_in_a_clean_folder(self):
        # S14: the last version's build moves aside whole; the script, the voice and the notes stay
        d = scratch(self)
        for p in ("public/index.html", "snaps/stills/a.png", "output.mp4", "deliver/reel.mp4", "QA.md", "storyboard.json",
                  "script.json", "voice.wav", "NOTES.md"):
            write(os.path.join(d, p), "x")
        r = run("new-version.py", "--project", d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("v1", r.stdout)
        for p in ("public", "snaps", "output.mp4", "deliver", "QA.md"):
            self.assertFalse(os.path.exists(os.path.join(d, p)), p)
            self.assertTrue(os.path.exists(os.path.join(d, "versions", "v1", p)), p)
        self.assertTrue(os.path.exists(os.path.join(d, "versions", "v1", "storyboard.json")))   # a record of the plan
        for p in ("script.json", "voice.wav", "NOTES.md", "storyboard.json"):                 # kept to edit for v2
            self.assertTrue(os.path.exists(os.path.join(d, p)), p)
        os.makedirs(os.path.join(d, "public"))
        r = run("new-version.py", "--project", d)
        self.assertIn("v2", r.stdout)
        self.assertTrue(os.path.isdir(os.path.join(d, "versions", "v2", "public")))
        self.assertTrue(os.path.exists(os.path.join(d, "storyboard.json")))   # the plan carries over to edit


if __name__ == "__main__":
    unittest.main()
