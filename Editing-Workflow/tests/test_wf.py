"""wf.py: one entry point for every profile. It only calls what exists: the README's install steps, each suite's own
test command, the preflight, a stage's gate scripts, the hand-off, and the opt-in render."""
import os, re, subprocess, sys, tempfile, shutil, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # Editing-Workflow
README = os.path.join(os.path.dirname(ROOT), "README.md")


def wf(*args, cwd=None):
    return subprocess.run([sys.executable, os.path.join(ROOT, "wf.py")] + list(args), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cwd)


class Wf(unittest.TestCase):
    def test_install_dry_run_lists_the_readme_copy_steps(self):
        with open(README, encoding="utf-8") as f:
            readme = f.read()
        for profile in ("longform", "reels", "explainer"):
            r = wf("install", profile, "--dry-run")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            want = [l.strip() for l in readme.splitlines() if l.startswith("cp ") and "/%s/" % profile in l]
            self.assertTrue(want, profile)
            for line in want:
                self.assertIn(line, r.stdout, (profile, line))

    def test_install_copies_for_real(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        os.symlink(ROOT, os.path.join(d, "Editing-Workflow"))
        r = wf("install", "reels", "--to", d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(d, ".claude", "skills", "reels", "scripts", "reels-handoff.py")))
        self.assertTrue(os.path.isfile(os.path.join(d, ".claude", "agents", "reels-cutter.md")))

    def test_test_runs_each_suite_command(self):
        r = wf("test", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for path in ("kit/youtube-edit/scripts", "reels/skill/reels/scripts", "explainer/skill/explainer/scripts"):
            self.assertRegex(r.stdout, r"%s.*python3? -m unittest discover -s tests -t \." % re.escape(path))

    def test_handoff_routes_by_profile(self):
        self.assertIn("explainer/skill/explainer/scripts/handoff.py --project videos/p", wf("handoff", "videos/p", "--profile", "explainer", "--dry-run").stdout)
        self.assertIn("reels-handoff.py --project videos/p", wf("handoff", "videos/p", "--profile", "reels", "--dry-run").stdout)
        lf = wf("handoff", "videos/p", "--profile", "longform", "--dry-run", "--", "--section", "videos/p/01").stdout
        self.assertIn("reels-handoff.py --project videos/p --format 16x9 --section videos/p/01", lf)

    def test_gates_run_the_stage_scripts(self):
        out = wf("gates", "videos/p", "--profile", "explainer", "--stage", "E1", "--dry-run").stdout
        self.assertIn("script-check.py --script videos/p/script.json --report videos/p/SCRIPT.md", out)
        for prof in ("reels", "longform"):   # the kept cut is in source time: the source's transcript, not the flat cut's
            out = wf("gates", "videos/p", "--profile", prof, "--stage", "wording", "--dry-run").stdout
            self.assertIn("wording.py --transcript videos/p/transcript-raw.json --kept videos/p/cut-list.json", out)
        out = wf("gates", "videos/p", "--profile", "reels", "--stage", "H1", "--dry-run").stdout
        self.assertIn("handoff-check.py --edit videos/p/edit --profile reels", out)

    def test_render_says_opt_in(self):
        r = wf("render", "videos/p", "--profile", "explainer", "--dry-run")
        self.assertIn("opt-in", r.stdout)
        self.assertIn("render", r.stdout)

    def test_unknown_profile_is_named(self):
        r = wf("install", "podcast", "--dry-run")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("podcast", r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
