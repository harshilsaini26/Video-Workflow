#!/usr/bin/env python3
"""review.py: the Animator's review sheets, from the composed page in Chromium, before any render.

  review.py --index public/index.html --out snaps/review --cuts
  review.py ... --scene ID [--step 0.12]     the viewer-timing sheet of one scene, from its in to its out
  review.py ... --items                      every item as it lands: its data-at -0.1, +0.25 and +0.6 s, one row each
  review.py ... --crop [x,y,w,h]             1:1 crops at each scene's settled moment (default: its box and the captions)
  review.py ... --follow '#sid-x'            a crop that tracks one element's box over its life, 6 frames

--cuts writes a strip for every handover in moments.json: the cut -0.3 s to +0.5 s at every 1/30 s, 8 columns of
216x384 (cut-NN-<a>-<b>.png). Every cell is labelled with its time. The gates measure; these are for looking (the
gates cannot see a cut that jars, a read that comes too soon, a hero that is soft). Prints each file with its cells,
and the ms per frame. Uses stills.mjs and the puppeteer and Chrome that gate E5 uses.
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explainer_lib as E
import layout_check as LC

CUT = (-0.3, 0.5, 1 / 30.0)
CELL = (216, 384)


def plan(a, moments, tmp):
    """(shots, follow, sheets, size) for the mode asked."""
    frame = lambda k: os.path.join(tmp, "%05d.png" % k)
    shots, sheets = [], []

    def sheet(name, times, cols):
        cells = []
        for t, label in times:
            shots.append({"t": round(max(0.0, t), 4), "file": frame(len(shots))})
            cells.append({"file": shots[-1]["file"], "label": label})
        sheets.append({"file": os.path.join(a.out, name), "cols": cols, "cell": list(CELL), "cells": cells})

    sc = moments["scenes"] if moments else []
    if a.cuts:
        lo, hi, step = CUT
        n = int(round((hi - lo) / step)) + 1
        for k, (x, y) in enumerate(zip(sc, sc[1:]), 1):
            sheet("cut-%02d-%s-%s.png" % (k, x["id"], y["id"]),
                  [(y["in"] + lo + j * step, "%+.3f" % (lo + j * step)) for j in range(n)], 8)
    elif a.scene:
        s = next((s for s in sc if s["id"] == a.scene), None)
        if not s:
            sys.exit("no scene %r in moments.json (%s)" % (a.scene, ", ".join(x["id"] for x in sc)))
        n = int(math.ceil((s["out"] - s["in"]) / a.step - 1e-9))
        sheet("scene-%s.png" % s["id"], [(s["in"] + j * a.step, "%.2f s" % (s["in"] + j * a.step)) for j in range(n)], 8)
    elif a.items:
        times = []
        for i in moments.get("items", []):
            times += [(i["t"] + d, "%s %+.2f" % (i["scene"], d)) for d in (-0.1, 0.25, 0.6)]
        sheet("items.png", times, 3)
    elif a.crop is not None:
        rects = None
        if a.crop:
            try:
                x, y, w, h = [int(v) for v in a.crop.split(",")]
            except ValueError:
                sys.exit("--crop takes x,y,w,h in pixels of the 1080x1920 frame")
            if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > 1080 or y + h > 1920:
                sys.exit("--crop %s is not inside the 1080x1920 frame" % a.crop)
            rects = [("crop", (x, y, w, h))]
        for k, (s, smp) in enumerate(zip(sc, LC.samples(moments)), 1):
            for name, (x, y, w, h) in rects or [("box", s["box"]), ("captions", (0, E.CAPTION_BAND[0], 1080, E.CAPTION_BAND[1] - E.CAPTION_BAND[0]))]:
                shots.append({"t": smp["t"], "file": os.path.join(a.out, "crop-%02d-%s-%s.png" % (k, s["id"], name)),
                              "clip": {"x": max(0, x), "y": max(0, y), "w": min(w, 1080 - max(0, x)), "h": min(h, 1920 - max(0, y))}})
        return shots, None, sheets, None
    elif a.follow:
        files = [frame(j) for j in range(6)]
        name = "follow-%s.png" % "".join(c if c.isalnum() or c in "-_" else "" for c in a.follow)
        sheets.append({"file": os.path.join(a.out, name), "cols": 6, "cell": list(CELL),
                       "cells": [{"file": f, "label": "%d/6" % (j + 1)} for j, f in enumerate(files)]})
        return shots, {"sel": a.follow, "n": 6, "pad": 40, "files": files}, sheets, None
    return shots, None, sheets, list(CELL)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--cuts", action="store_true")
    mode.add_argument("--scene")
    mode.add_argument("--items", action="store_true")
    mode.add_argument("--crop", nargs="?", const="")
    mode.add_argument("--follow")
    ap.add_argument("--step", type=float, default=0.12)
    a = ap.parse_args()
    if a.step <= 0:
        sys.exit("--step must be over 0")
    mp = os.path.join(os.path.dirname(os.path.abspath(a.index)), "moments.json")
    moments = None
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as f:
            moments = json.load(f)
    elif not a.follow:
        sys.exit("no moments.json next to %s: compose the page first" % a.index)
    pdir, chrome = LC.find_puppeteer(), LC.find_chrome()
    if not (shutil.which("node") and pdir and chrome):
        sys.exit("needs node, puppeteer and Chrome: install HyperFrames (npx hyperframes browser ensure)")
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="review-")
    try:
        shots, follow, sheets, size = plan(a, moments, tmp)
        job = {"index": os.path.abspath(a.index), "shots": shots, "puppeteer_dir": pdir, "chrome": chrome, "sheets": sheets}
        if follow:
            job["follow"] = follow
        if size:
            job["size"] = size
        jp = os.path.join(tmp, "job.json")
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(job, f)
        t0 = time.time()
        r = subprocess.run([shutil.which("node"), os.path.join(HERE, "stills.mjs"), jp], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
        took = time.time() - t0
        if r.returncode:
            sys.exit("stills.mjs failed: " + (r.stderr or r.stdout)[-800:])
        made = json.loads(r.stdout.strip().splitlines()[-1]).get("sheets", {})
    finally:
        shutil.rmtree(tmp, True)
    for s in shots:
        if s.get("clip"):
            print("%s: 1 crop at %.2f s" % (os.path.basename(s["file"]), s["t"]))
    for path, n in made.items():
        print("%s: %d cells" % (os.path.basename(path), n) if n else "%s: nothing to show (the element is never visible)" % os.path.basename(path))
    frames = len(shots) + (follow["n"] if follow else 0)
    print("%d frames in %.1f s: %.0f ms per frame, in %s" % (frames, took, 1000 * took / max(1, frames), a.out))


if __name__ == "__main__":
    main()
