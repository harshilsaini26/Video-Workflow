#!/usr/bin/env python3
"""preflight.py: prepare this machine once and write down how it runs everything (SOP S3).

  preflight.py --out videos/_preflight [--suite NAME=FOLDER ...] [--no-tests]

The RAG reel's Windows machine was never prepared: `python3` did not exist there, the tests failed 49 times until UTF-8
mode was on, several scripts needed flags nobody had written down, and four failing tests were never looked at. This
records, in one file every brief links to (PREFLIGHT.md, and preflight.json for scripts):
- the Python command that works here (this interpreter), its version, UTF-8 mode and the text encoding;
- node, npx, HyperFrames, FFmpeg, the Chrome and puppeteer gate E5 uses, numpy, Kokoro, espeak-ng;
- the test suites (the kit, Reels and Explainer skills found beside this one, or --suite), run with PYTHONUTF8=1,
  with every failing test named.
Exit 1 when a test fails or a tool the pipeline needs is missing, so nobody starts a video on a machine that isn't ready.
"""
import argparse, json, locale, os, platform, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_check as LC

NEEDED = ("node", "npx", "ffmpeg", "ffprobe", "hyperframes", "chrome", "puppeteer", "numpy")


def first_line(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        out = (r.stdout or r.stderr).strip().splitlines()
        return out[0].strip() if r.returncode == 0 and out else None
    except (OSError, subprocess.SubprocessError):
        return None


def tools():
    npx = shutil.which("npx")
    t = {"node": first_line([shutil.which("node") or "node", "--version"]),
         "npx": npx,
         "hyperframes": first_line([npx or "npx", "--no-install", "hyperframes", "--version"]) if npx else None,
         "ffmpeg": first_line(["ffmpeg", "-version"]) if shutil.which("ffmpeg") else None,
         "ffprobe": shutil.which("ffprobe"),
         "chrome": LC.find_chrome(),
         "puppeteer": LC.find_puppeteer(),
         "espeak-ng": shutil.which("espeak-ng") or shutil.which("espeak")}
    for mod in ("numpy", "kokoro"):
        try:
            __import__(mod)
            t[mod] = "installed"
        except ImportError:
            t[mod] = None
    return t


def default_suites():
    """The three skills' test folders, installed side by side (.claude/skills/...) or in this repository."""
    cands = {"kit": [os.path.join(HERE, "..", "..", "youtube-edit", "scripts"), os.path.join(HERE, "..", "..", "..", "..", "kit", "youtube-edit", "scripts")],
             "reels": [os.path.join(HERE, "..", "..", "reels", "scripts"), os.path.join(HERE, "..", "..", "..", "..", "reels", "skill", "reels", "scripts")],
             "explainer": [HERE]}
    out = {}
    for name, paths in cands.items():
        hit = next((os.path.abspath(p) for p in paths if os.path.isdir(os.path.join(p, "tests"))), None)
        if hit:
            out[name] = hit
    return out


def run_suite(folder):
    env = dict(os.environ, PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=folder, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    text = r.stdout + r.stderr
    failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): \w+ \(([\w.]+)\)", text, re.M)))
    ran = re.search(r"^Ran (\d+) tests? in", text, re.M)
    last = [l for l in text.strip().splitlines() if l.startswith(("OK", "FAILED"))]
    return {"folder": folder, "ran": int(ran.group(1)) if ran else 0, "result": last[-1] if last else "no result",
            "failed": failed, "ok": r.returncode == 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--suite", action="append", default=[], help="NAME=FOLDER (a folder with tests/); default: the three skills")
    ap.add_argument("--no-tests", action="store_true")
    a = ap.parse_args()
    py = {"command": sys.executable, "version": platform.python_version(), "platform": platform.platform(),
          "utf8_mode": bool(sys.flags.utf8_mode), "encoding": locale.getpreferredencoding(False),
          "PYTHONUTF8": os.environ.get("PYTHONUTF8", "")}
    t = tools()
    suites = {}
    if not a.no_tests:
        chosen = dict(s.split("=", 1) for s in a.suite) if a.suite else default_suites()
        for name, folder in chosen.items():
            suites[name] = run_suite(os.path.abspath(folder))
    missing = [k for k in NEEDED if not t.get(k)] if not a.suite else []
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "preflight.json"), "w", encoding="utf-8") as f:
        json.dump({"python": py, "tools": t, "suites": suites, "missing": missing}, f, indent=1)
    win = sys.platform.startswith("win")
    md = ["# Preflight", "",
          "Written by preflight.py. Every brief links here: run the scripts the way this file says.", "",
          "## Python", "",
          "- Command: `%s` (use this, not `python3`, in every brief)" % py["command"],
          "- Version %s on %s" % (py["version"], py["platform"]),
          "- UTF-8 mode: %s; text encoding %s; PYTHONUTF8=%s" % ("on" if py["utf8_mode"] else "off", py["encoding"], py["PYTHONUTF8"] or "unset"),
          "- %s" % ("Set PYTHONUTF8=1 for good: `setx PYTHONUTF8 1`, then open a new terminal" if win else
                    "Keep PYTHONUTF8=1 set for any subprocess that prints or reads text"), "",
          "## Tools", ""]
    md += ["- %s: %s" % (k, v or "**missing**") for k, v in t.items()]
    md += ["", "Gate E5 (layout-check.py) uses: PUPPETEER_DIR=%s, CHROME=%s" % (t.get("puppeteer") or "-", t.get("chrome") or "-"), ""]
    if suites:
        md += ["## Tests (run with PYTHONUTF8=1)", ""]
        for name, s in suites.items():
            md.append("- **%s** (%s): ran %d, %s" % (name, s["folder"], s["ran"], s["result"]))
            md += ["  - failing: `%s`" % x for x in s["failed"]]
        md.append("")
    if missing:
        md += ["## Missing", "", ", ".join(missing) + ": install before the first video (the kit's SETUP.md)", ""]
    with open(os.path.join(a.out, "PREFLIGHT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    bad = missing or any(not s["ok"] for s in suites.values())
    for name, s in suites.items():
        print("%s: %s%s" % (name, s["result"], (" (failing: %s)" % ", ".join(s["failed"])) if s["failed"] else ""))
    print("PREFLIGHT %s: %s" % ("FAIL" if bad else "OK", os.path.join(a.out, "PREFLIGHT.md")))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
