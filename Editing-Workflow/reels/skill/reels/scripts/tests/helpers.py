"""Shared bits for the Reels tests: run a script, scratch dirs, synthetic media, and the kit's scripts for the
compatibility checks. Paths are relative to this file, so the tests run from any install location."""
import json, os, shutil, subprocess, sys, tempfile, unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
needs_ffmpeg = unittest.skipUnless(HAS_FFMPEG, "ffmpeg / ffprobe not on PATH")

_kit = [os.environ.get("KIT_SCRIPTS", ""),
        os.path.join(SCRIPTS, "..", "..", "youtube-edit", "scripts"),                                        # installed
        os.path.join(SCRIPTS, "..", "..", "..", "..", "kit", "youtube-edit", "scripts")]   # repository (Editing-Workflow/kit)
KIT_SCRIPTS = next((os.path.abspath(k) for k in _kit if k and os.path.exists(os.path.join(k, "beat-check.py"))), None)
needs_kit = unittest.skipUnless(KIT_SCRIPTS, "the kit's youtube-edit scripts were not found")


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + [str(a) for a in args], capture_output=True, text=True, cwd=cwd)


def run_kit(script, *args):
    return subprocess.run([sys.executable, os.path.join(KIT_SCRIPTS, script)] + [str(a) for a in args], capture_output=True, text=True)


def scratch(test):
    d = tempfile.mkdtemp(prefix="reels-test-")
    test.addCleanup(shutil.rmtree, d, True)
    return d


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(data if isinstance(data, str) else json.dumps(data))
    return path


def read(path):
    with open(path) as f:
        return f.read()


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + list(args), check=True)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,duration",
                        "-show_entries", "format=duration", "-of", "json", path], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def words(spec):
    """'Hello@1.0 there@1.4' -> transcript words, each 0.3 s long."""
    out = []
    for tok in spec.split():
        txt, t = tok.rsplit("@", 1)
        out.append({"text": txt, "start": float(t), "end": round(float(t) + 0.3, 3)})
    return {"words": out}
