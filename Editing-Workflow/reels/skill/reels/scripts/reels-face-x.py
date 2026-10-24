#!/usr/bin/env python3
"""reels-face-x.py: where the speaker is in each kept segment, for the editor hand-off: the median centre of the largest
face over a few frames of the segment, as 0 to 1 of the frame width. reels-handoff.py places each footage clip on it;
the creator can move any clip in the editor. One value per segment, so the framing changes only at a cut, never swims.
A segment with no face is left out (the clip keeps the Ingest framing).

  python3 reels-face-x.py --source <camera file or source.mp4> --cut-list cut-list.json [--ingest ingest.json]
                          --out face-x.json [--samples 5]
  -> face-x.json: {"<segment index>": x}

Needs opencv-python-headless (free; pip install opencv-python-headless). The idea of following the speaker's face
comes from Anil-matcha/AI-Youtube-Shorts-Generator (MIT); per segment, not per frame, so it never jitters.
"""
import argparse, json, os, statistics, sys


def segment_x(detect, path, t0, t1, samples=5):
    """The median face x over `samples` evenly spread times in [t0, t1]; None when no sample finds a face."""
    step = (t1 - t0) / float(samples)
    xs = [x for x in (detect(path, t0 + step * (k + 0.5)) for k in range(samples)) if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def face_x(detect, cut_list, ingest, source, samples=5):
    with open(cut_list, encoding="utf-8") as f:
        kept = json.load(f)["kept"]
    clips = None
    if ingest and os.path.isfile(ingest):
        with open(ingest, encoding="utf-8") as f:
            clips = json.load(f).get("clips")
    out = {}
    for i, k in enumerate(kept):
        s, e = float(k["start"]), float(k["end"])
        if clips:                                       # the segment's middle, on its camera file
            mid = (s + e) / 2.0
            c = next((c for c in clips if c["source_start"] <= mid < c["source_start"] + c["duration"]), clips[-1])
            path, s, e = c["path"], s - c["source_start"], e - c["source_start"]
        else:
            path = source
        x = segment_x(detect, path, s, e, samples)
        if x is not None:
            out[str(i)] = x
    return out


def opencv_detector():
    import cv2
    cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    caps = {}

    def detect(path, t):
        cap = caps.get(path) or caps.setdefault(path, cv2.VideoCapture(path))
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            return None
        h, w = frame.shape[:2]
        scale = 480.0 / max(w, h)
        small = cv2.resize(frame, (int(w * scale), int(h * scale)))
        faces = cascade.detectMultiScale(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(24, 24))
        if len(faces) == 0:
            return None
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        return (x + fw / 2.0) / small.shape[1]
    return detect


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", default="")
    ap.add_argument("--cut-list", required=True)
    ap.add_argument("--ingest", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=5)
    a = ap.parse_args()
    try:
        detect = opencv_detector()
    except ImportError:
        print("FACE-X FAIL: needs OpenCV: pip install opencv-python-headless (free); without it the clips keep the Ingest framing")
        sys.exit(1)
    out = face_x(detect, a.cut_list, a.ingest, a.source, a.samples)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("FACE-X: %d segments with a face, written to %s" % (len(out), a.out))


if __name__ == "__main__":
    main()
