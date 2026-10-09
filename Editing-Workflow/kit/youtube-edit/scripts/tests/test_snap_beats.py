"""snap-beats.py: each moment gets its own snapshot (never a stale frame left in public/snapshots), and a snapshot that
fails is reported, not replaced by another frame. HyperFrames is stood in for by a fake `npx` on PATH."""
import hashlib, os, stat, sys, unittest
from .helpers import needs_ffmpeg, run, scratch, write

FAKE_NPX = r'''#!%s
# fake `npx hyperframes snapshot <public> --at <t>`: writes frame-00-at-<t>s.png in a colour of its own, keeps a copy
import os, subprocess, sys
pub, t = sys.argv[3], sys.argv[5]
if t == os.environ.get("FAKE_FAIL_AT"):
    sys.exit("snapshot failed")
os.makedirs(os.path.join(pub, "snapshots"), exist_ok=True)
out = os.path.join(pub, "snapshots", "frame-00-at-%%ss.png" %% t)
colour = "0x%%06x" %% (int(float(t) * 100) * 4099 %% 0xFFFFFF)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=%%s:s=64x36" %% colour, "-frames:v", "1", out], check=True)
os.makedirs(os.environ["FAKE_RECORD"], exist_ok=True)
subprocess.run(["cp", out, os.path.join(os.environ["FAKE_RECORD"], "%%s.png" %% t)], check=True)
''' % sys.executable


def md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@needs_ffmpeg
class SnapBeats(unittest.TestCase):
    def test_each_moment_gets_its_own_frame_and_failures_are_reported(self):
        d = scratch(self)
        P = os.path.join(d, "proj")
        write(os.path.join(P, "storyboard.json"), {"id": "t", "duration": 5.0, "beats": [
            {"type": "chip", "id": "a", "in": 1.0, "out": 2.0}, {"type": "chip", "id": "b", "in": 2.0, "out": 3.0},
            {"type": "chip", "id": "c", "in": 3.0, "out": 4.0}]})                          # moments 1.9, 2.9, 3.9
        stale = os.path.join(P, "public", "snapshots", "frame-00-at-0.35s.png")           # left over from an earlier run
        write(stale, "not this frame")
        bindir = os.path.join(d, "bin"); os.makedirs(bindir)
        npx = write(os.path.join(bindir, "npx"), FAKE_NPX)
        os.chmod(npx, os.stat(npx).st_mode | stat.S_IEXEC)
        record = os.path.join(d, "record")
        env = {"PATH": bindir + os.pathsep + os.environ["PATH"], "FAKE_RECORD": record, "FAKE_FAIL_AT": "2.9"}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            r = run("snap-beats.py", "--project", P)
        finally:
            for k, v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        snaps = os.path.join(P, "snaps")
        for t in ("1.9", "3.9"):
            self.assertEqual(md5(os.path.join(snaps, "at-%05.2f.png" % float(t))), md5(os.path.join(record, t + ".png")), t)
        self.assertFalse(os.path.exists(os.path.join(snaps, "at-02.90.png")))         # the failed moment is not faked
        self.assertIn("snapshot failed at 2.9", r.stdout)
        self.assertTrue(os.path.exists(os.path.join(snaps, "sheet.png")))
