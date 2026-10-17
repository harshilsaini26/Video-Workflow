#!/usr/bin/env python3
"""motion-check.py: gate E6, a picture that is never still for long, measured on the rendered file.

  motion-check.py --video output.mp4 [--max-still 1.0] [--max-share 0.15] [--fps 10]

FFmpeg reads the reel at 10 frames a second, 180x320, in grey; a frame is still when it differs from the one before by
under 0.25/255 on average (an eye cannot see that). Fails (exit 1) on a still stretch over --max-still seconds, naming
its times, or when more than --max-share of the reel is still. The reference reel this gate was set against is still
7% of the time and never for more than 0.5 s; the RAG reel that prompted it was still 67% of the time. Ambient motion
(the camera's drift, the particles) counts here: it is what keeps the picture alive. No tokens: FFmpeg and numpy.
"""
import argparse, shutil, subprocess, sys

W, H = 180, 320
STILL = 0.25          # mean absolute change, out of 255, under which a frame is still


def changes(path, fps):
    """The mean change from each frame to the next, one value per 1/fps seconds after the first frame."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=%g,scale=%d:%d,format=gray" % (fps, W, H),
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
    if len(frames) < 2:
        return []
    return list(np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2)))


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
    ap.add_argument("--video", required=True)
    ap.add_argument("--max-still", type=float, default=1.0)
    ap.add_argument("--max-share", type=float, default=0.15)
    ap.add_argument("--fps", type=float, default=10.0)
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        print("E6 ERROR: no ffmpeg on PATH")
        sys.exit(2)
    try:
        ch = changes(a.video, a.fps)
    except ImportError:
        print("E6 ERROR: needs numpy (pip install numpy)")
        sys.exit(2)
    if not ch:
        print("E6 ERROR: no frames read from %s" % a.video)
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
