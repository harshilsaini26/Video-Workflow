#!/usr/bin/env python3
"""motion-check.py: gate E6, a picture that is never still for long, measured on the rendered file.

  motion-check.py --video output.mp4 [--max-still 1.0] [--max-share 0.15] [--fps 10]
  motion-check.py --index public/index.html [...]      the composed page, before any render


FFmpeg reads the reel at 10 frames a second, 180x320, in grey; a frame is still when under 0.1% of it (58 pixels)
changes visibly, by more than 5/255, from the one before. Counting what visibly moves, not the average change, lets a
small thing moving (a cursor, a particle) count, as the eye counts it, and a faint change over the whole frame (a ground
brightening) not. Fails (exit 1) on a still stretch over --max-still seconds, naming its times, or when more than
--max-share of the reel is still. The reference reel this gate was set against is still 3% of the time and never for
more than 0.4 s; the RAG reel that prompted it was still 48% of the time. Ambient motion (the camera's drift, the
particles) counts here: it is what keeps the picture alive. No tokens: FFmpeg and numpy.

--index samples the page itself through the stills tool's seek (stills.mjs), at the same size and in grey, with the
stroke boil off (data-boil="off"), so a frozen stretch is found before the render; it needs node, puppeteer and Chrome.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 180, 320
LEVEL = 5             # a pixel changes visibly when it moves by more than this, out of 255
STILL = 0.001         # the share of the frame changing visibly under which a frame is still


def changes(path, fps):
    """The share of the frame changing visibly from each frame to the next, one value per 1/fps seconds after the first."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=%g,scale=%d:%d,format=gray" % (fps, W, H),
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
    if len(frames) < 2:
        return []
    return list((np.abs(np.diff(frames, axis=0)) > LEVEL).mean(axis=(1, 2)))


def frames_from_page(index, fps, keep_job=None):
    """Grey W x H frames of the composed page at t = k/fps over its whole duration, as bytes."""
    sys.path.insert(0, HERE)
    import layout_check as LC
    pdir, chrome = LC.find_puppeteer(), LC.find_chrome()
    if not (shutil.which("node") and pdir and chrome):
        raise RuntimeError("needs node, puppeteer and Chrome: install HyperFrames (npx hyperframes browser ensure)")
    with open(index, encoding="utf-8") as f:
        m = re.search(r'id="stage"[^>]*data-duration="([\d.]+)"', f.read())
    if not m:
        raise RuntimeError("no #stage with a data-duration in %s" % index)
    tmp = tempfile.mkdtemp(prefix="e6-")
    try:
        shots = [{"t": round(k / fps, 4), "file": os.path.join(tmp, "%05d.gray" % k)} for k in range(int(float(m.group(1)) * fps))]
        job = {"index": os.path.abspath(index), "shots": shots, "puppeteer_dir": pdir, "chrome": chrome,
               "size": [W, H], "gray": True, "boil": False}
        jp = keep_job or os.path.join(tmp, "job.json")
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(job, f)
        r = subprocess.run([shutil.which("node"), os.path.join(HERE, "stills.mjs"), jp], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
        if r.returncode:
            raise RuntimeError("stills.mjs failed: " + (r.stderr or r.stdout)[-800:])
        out = []
        for s in shots:
            with open(s["file"], "rb") as f:
                out.append(f.read())
        return out
    finally:
        shutil.rmtree(tmp, True)


def page_changes(frames):
    """changes() for frames already read: the share of pixels changing visibly from each frame to the next."""
    return [sum(abs(x - y) > LEVEL for x, y in zip(a, b)) / float(len(a)) for a, b in zip(frames, frames[1:])]


def still_runs(ch, fps):
    """[(start, end)] seconds of every still stretch."""
    runs, start = [], None
    for i, c in enumerate(list(ch) + [STILL + 1]):
        if c < STILL and start is None:
            start = i
        elif c >= STILL and start is not None:
            runs.append((start / float(fps), (i + 1) / float(fps)))
            start = None
    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video")
    src.add_argument("--index", help="the composed page (public/index.html), sampled before any render")
    ap.add_argument("--keep-job", help=argparse.SUPPRESS)
    ap.add_argument("--max-still", type=float, default=1.0)
    ap.add_argument("--max-share", type=float, default=0.15)
    ap.add_argument("--fps", type=float, default=10.0)
    a = ap.parse_args()
    if a.index:
        try:
            ch = page_changes(frames_from_page(a.index, a.fps, a.keep_job))
        except (RuntimeError, OSError) as e:
            print("E6 ERROR: %s" % e)
            sys.exit(2)
    elif not shutil.which("ffmpeg"):
        print("E6 ERROR: no ffmpeg on PATH")
        sys.exit(2)
    else:
        try:
            ch = changes(a.video, a.fps)
        except ImportError:
            print("E6 ERROR: needs numpy (pip install numpy)")
            sys.exit(2)
    if not ch:
        print("E6 ERROR: no frames read from %s" % (a.index or a.video))
        sys.exit(2)
    runs = still_runs(ch, a.fps)
    share = sum(1 for c in ch if c < STILL) / float(len(ch))
    longest = max([e - s for s, e in runs] or [0.0])
    bad = [(s, e) for s, e in runs if e - s > a.max_still + 1e-6]
    for s, e in bad:
        print("E6 FAIL: still from %.2f to %.2f s (%.1f s; at most %.1f s): nothing on screen moves; give the scene a "
              "build, a camera move or a cut" % (s, e, e - s, a.max_still))
    if share > a.max_share:
        print("E6 FAIL: still %.0f%% of the time (at most %.0f%%)" % (100 * share, 100 * a.max_share))
    if bad or share > a.max_share:
        sys.exit(1)
    print("E6 PASS: still %.0f%% of the time, the longest still %.1f s (%d frames at %g fps)"
          % (100 * share, longest, len(ch) + 1, a.fps))


if __name__ == "__main__":
    main()
