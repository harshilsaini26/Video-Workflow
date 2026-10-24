#!/usr/bin/env python3
"""snap-page.py: a screenshot of a real web page for the browser scene, taken with Chrome on this machine (free, local).

  snap-page.py --url https://www.coursera.org/learn/corporate-finance --out videos/<p>/shots/course.png
               [--width 1280] [--height 1600] [--wait 4000] [--chrome PATH]

Writes a PNG of exactly --width x --height (the top of the page; the browser scene's `focus` can punch in on a line further down).
Chrome is found at --chrome, $CHROME, the usual install paths, or on PATH. A fresh profile is used every time, so you
are never signed in and nothing personal is captured. The page is loaded once first: when Chrome shows its own error
page instead ("This site can't be reached"), nothing is written and the error is named. A proxy in HTTPS_PROXY is passed
to Chrome. Check the result before using it: a cookie banner or a sign-in wall can cover the page (try a longer
--wait, or crop it out).
"""
import argparse, os, re, shutil, struct, subprocess, sys, tempfile

PATHS = ["/opt/pw-browsers/chromium",
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         "/Applications/Chromium.app/Contents/MacOS/Chromium",
         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
         r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def find_chrome(explicit):
    if explicit:
        return explicit if os.path.exists(explicit) else None
    for c in [os.environ.get("CHROME", "")] + PATHS + [shutil.which(n) or "" for n in NAMES]:
        if c and os.path.exists(c):
            return c
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=1600)
    ap.add_argument("--wait", type=int, default=4000, help="ms of page time before the shot (default 4000)")
    ap.add_argument("--chrome", help="path to Chrome or Chromium")
    a = ap.parse_args()
    chrome = find_chrome(a.chrome)
    if not chrome:
        sys.exit("no Chrome or Chromium found%s: install Google Chrome, or pass --chrome PATH (or set CHROME)"
                 % (" at %s" % a.chrome if a.chrome else ""))
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    profile = tempfile.mkdtemp(prefix="snap-page-")
    base = [chrome, "--headless=new", "--hide-scrollbars", "--disable-gpu", "--mute-audio", "--no-first-run", "--disable-extensions",
            "--force-device-scale-factor=1", "--user-data-dir=%s" % profile, "--window-size=%d,%d" % (a.width, a.height),
            "--virtual-time-budget=%d" % a.wait]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        base.insert(1, "--no-sandbox")         # Chrome refuses to run as root with its sandbox (containers)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy and a.url.startswith("http"):
        base.append("--proxy-server=%s" % proxy)   # Chrome on Linux ignores the environment's proxy otherwise
    try:
        dom = subprocess.run(base + ["--dump-dom", a.url], capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace").stdout
        if 'id="main-frame-error"' in dom:     # Chrome's own error page, not the page asked for
            code = re.search(r"\b(ERR_[A-Z_]+)", dom)
            sys.exit("the page did not load (%s): %s; nothing written" % (code.group(1) if code else "Chrome's error page", a.url))
        r = subprocess.run(base + ["--screenshot=%s" % out, a.url], capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        sys.exit("Chrome took over 120 s on %s" % a.url)
    finally:
        shutil.rmtree(profile, True)
    if not os.path.exists(out):
        last = (r.stderr.strip().splitlines() or ["no message"])[-1]
        code = re.search(r"Page load failed: (net::)?(ERR_[A-Z_]+)", r.stderr)   # newer headless Chrome says so itself
        if code:
            sys.exit("the page did not load (%s): %s; nothing written" % (code.group(2), a.url))
        sys.exit("Chrome wrote no screenshot (%s)" % last)
    with open(out, "rb") as f:
        head = f.read(24)
    w, h = struct.unpack(">II", head[16:24])
    print("wrote %s (%d x %d) from %s" % (out, w, h, a.url))


if __name__ == "__main__":
    main()
