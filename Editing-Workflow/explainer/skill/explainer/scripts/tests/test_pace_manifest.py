"""pace-check.py reads the composer's moments.json, not the page's script text, so a custom scene's own comments or
code cannot confuse it."""
import copy, os, unittest
from .helpers import load, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30

CUSTOM = """<style>#yield .bar { width: 100px; height: 40px; }</style>
<div class="bar"></div>
<script>
  // scenes
  // captions
  function buildYield(tl, root, t0, t1) {
    tl.fromTo(root.querySelectorAll('.bar'), { opacity: 0 }, { opacity: 1, duration: 0.4, ease: 'power3.out', immediateRender: false }, t0);
  }
</script>
"""


class Manifest(unittest.TestCase):
    def test_custom_comments_do_not_confuse_pacing(self):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        write(os.path.join(d, "custom", "yield.html"), CUSTOM)
        board = copy.deepcopy(BOARD)
        board["scenes"][1] = {"type": "custom", "id": "yield", "bg": "black", "in": "word:8", "out": "word:18",
                              "box": {"x": 65, "y": 560, "w": 950, "h": 380}, "html": "custom/yield.html", "build": "buildYield"}
        sp = write(os.path.join(d, "storyboard.json"), board)
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m = load(os.path.join(d, "public", "moments.json"))
        self.assertEqual([s["id"] for s in m["scenes"]], ["hook", "yield", "cu"])
        # this test is about what pace-check reads, not the threshold: the BOARD's last scene holds 5 s on purpose
        r = run("pace-check.py", "--index", os.path.join(d, "public", "index.html"), "--max", "6", "--warn", "6")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 scenes", r.stdout)
