"""From script to a verified render: script-check, the voice, alignment, the composer, HyperFrames, verify-render."""
import importlib.util, json, os, shutil, statistics, subprocess, unittest
from .helpers import KIT_SCRIPTS, HAS_FFMPEG, load, needs_ffmpeg, needs_kit, run, run_kit, scratch, write

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "e2e")
PAUSE = {"comma": 0.15, "sentence": 0.35, "section": 0.6}
WORD = 0.32   # the fake engine's seconds a word


def hyperframes_ok():
    if not shutil.which("npx"):
        return False
    try:
        return subprocess.run(["npx", "--no-install", "hyperframes", "--version"], capture_output=True, timeout=120).returncode == 0
    except subprocess.TimeoutExpired:
        return False


HAS_HF = hyperframes_ok()
needs_hf = unittest.skipUnless(HAS_HF, "npx hyperframes is not available")
VENDOR = os.environ.get("EXPLAINER_VENDOR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "assets", "vendor")
needs_gsap = unittest.skipUnless(os.path.exists(os.path.join(VENDOR, "gsap.min.js")),
                                 "no local GSAP (npm pack gsap@3.14.2 into assets/vendor/, or set EXPLAINER_VENDOR): a render must not need the network")


def fake_asr(script):
    """What a recogniser would hear in the fake voice: each say word, 0.32 s apart, the line pauses between."""
    out, t = [], 0.0
    lines = script["lines"]
    for k, ln in enumerate(lines):
        for w in ln["say"].split():
            out.append({"text": w, "start": round(t, 3), "end": round(t + 0.3, 3)})
            t += WORD
        if k < len(lines) - 1:
            t += PAUSE[ln.get("break", "sentence")]
    return {"words": out}


def stage(test):
    d = scratch(test)
    for f in ("script.json", "storyboard.json"):
        shutil.copy(os.path.join(FIX, f), os.path.join(d, f))
    return d


class EndToEnd(unittest.TestCase):
    def check(self, r, what):
        self.assertEqual(r.returncode, 0, "%s failed:\n%s%s" % (what, r.stdout[-3000:], r.stderr[-3000:]))

    @needs_ffmpeg
    @needs_kit
    @needs_hf
    @needs_gsap
    def test_fake_voice_to_verified_render(self):
        d = stage(self)
        r = run("script-check.py", "--script", os.path.join(d, "script.json"))
        # a 12 s render keeps the suite fast; E1's length bound (160 to 240 words) is the one rule it may break
        errors = [l for l in r.stdout.splitlines() if l.startswith("  ") or "FAIL" in l]
        self.assertTrue(r.returncode == 0 or all("under 160 words" in l or l.startswith("E1 FAIL") for l in errors), r.stdout)
        self.assertNotIn("no source", r.stdout)
        self.assertEqual(len([l for l in r.stdout.splitlines() if l.startswith("  - ")]), 1, r.stdout)
        self.check(run("tts-kokoro.py", "--script", os.path.join(d, "script.json"), "--out", os.path.join(d, "voice.wav"), "--engine", "fake"), "tts")
        write(os.path.join(d, "asr.json"), fake_asr(load(os.path.join(d, "script.json"))))
        self.check(run("align-script.py", "--script", os.path.join(d, "script.json"), "--asr", os.path.join(d, "asr.json"),
                       "--out", os.path.join(d, "transcript.json"), "--report", os.path.join(d, "VOICE.md")), "align")
        pub = os.path.join(d, "public")
        self.check(run("explainer-compose.py", "--spec", os.path.join(d, "storyboard.json"), "--out", pub, "--vendor", VENDOR), "compose")
        self.check(run_kit("beat-check.py", "--index", os.path.join(pub, "index.html"), "--transcript", os.path.join(d, "transcript.json")), "beat-check")
        self.check(subprocess.run(["npx", "--no-install", "hyperframes", "check", pub], capture_output=True, text=True, timeout=600), "hyperframes check")
        mp4 = os.path.join(d, "output.mp4")
        self.check(subprocess.run(["npx", "--no-install", "hyperframes", "render", pub, "--fps", "60", "--video-bitrate", "20M",
                                   "--workers", "2", "-o", mp4], capture_output=True, text=True, timeout=1800), "render")
        r = run_kit("verify-render.py", "--render", mp4, "--index", os.path.join(pub, "index.html"), "--res", "1080x1920",
                    "--out", os.path.join(d, "VERIFY.md"))
        self.check(r, "verify-render")
        self.assertIn("PASS", open(os.path.join(d, "VERIFY.md")).read())

    @unittest.skipUnless(importlib.util.find_spec("kokoro") and HAS_HF, "needs Kokoro (pip install kokoro) and npx hyperframes with Parakeet")
    def test_real_kokoro_parakeet_alignment(self):
        d = stage(self)
        S = load(os.path.join(d, "script.json"))
        self.check(run("tts-kokoro.py", "--script", os.path.join(d, "script.json"), "--out", os.path.join(d, "voice.wav")), "tts")
        tdir = os.path.join(d, "asr")
        os.makedirs(tdir)
        self.check(subprocess.run(["npx", "--no-install", "hyperframes", "transcribe", os.path.join(d, "voice.wav"), "-d", tdir,
                                   "--engine", "parakeet", "--json"], capture_output=True, text=True, timeout=1800), "transcribe")
        asr = os.path.join(tdir, "transcript.json")
        r = run("align-script.py", "--script", os.path.join(d, "script.json"), "--asr", asr, "--out", os.path.join(d, "transcript.json"))
        self.check(r, "align")
        ratio = float(r.stdout.split("E2 PASS: ")[1].split("%")[0]) / 100
        self.assertGreaterEqual(ratio, 0.98)
        words = load(os.path.join(d, "transcript.json"))
        spans = {l["id"]: (l["start"], l["end"]) for l in words["lines"]}
        for w in words["words"]:
            a, b = spans[w["line"]]
            self.assertTrue(a <= w["start"] <= b, w)
        heard = load(asr)["words"]
        offsets = [abs(w["start"] - min(heard, key=lambda h: abs(h["start"] - w["start"]))["start"]) for w in words["words"]]
        print("\nmedian caption-to-word offset: %.3f s over %d words" % (statistics.median(offsets), len(offsets)))
