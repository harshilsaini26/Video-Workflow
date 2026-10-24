#!/usr/bin/env python3
"""make-cases.py: compose one reel per block case, then turn Chromium's measurements into the height fixture.

  make-cases.py DIR                              # writes DIR/<case>/public/ and DIR/cases.json
  node measure-blocks.mjs DIR > measured.jsonl   # each block's laid-out height, real DM Sans loaded
  make-cases.py DIR --merge measured.jsonl       # writes tests/fixtures/heights.json

The composer places every block by its predicted height (layout.json), so a prediction under the real height can push
a block past the safe zone. tests/test_heights.py holds each prediction to 0 to 4 px over Chromium. Rerun after changing
a format's CSS, the fonts or the text measuring. A developer tool, not part of a reel.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURE = os.path.join(SCRIPTS, "tests", "fixtures", "heights.json")
T = {"short": "Free tools", "mid": "Stop paying for editing software", "long": "Every free tool I use to edit a reel from start to finish"}
cases = []


def case(name, beat):
    cases.append((name, beat))


for k, t in T.items():
    for pos in ("top", "mid", "low"):
        case("headline-%s-%s" % (k, pos), {"type": "headline", "text": t, "pos": pos})
        case("headline-box-%s-%s" % (k, pos), {"type": "headline", "text": t, "pos": pos, "box": True, "size": 96})
    case("hook-%s" % k, {"type": "hook", "text": t[:60], "pos": "top"})
    for pos in ("top", "mid"):
        case("point-%s-%s" % (k, pos), {"type": "point", "text": t.split()[0], "sub": t, "pos": pos})
        case("stat-%s-%s" % (k, pos), {"type": "stat", "value": 1000, "prefix": "$", "label": t, "pos": pos, "count_at": 0.5})
    for pos in ("mid", "low"):
        case("chip-%s-%s" % (k, pos), {"type": "chip", "text": t, "pos": pos})
WORDS = ["OBS", "Parakeet", "HyperFrames", "Auto editor tool", "Free music library", "Blender"]
for n in (1, 3, 5):
    for pos in ("top", "mid"):
        case("steps-%d-%s" % (n, pos), {"type": "steps", "title": "Free tools I use daily", "items": [[w, 0.5] for w in WORDS[:n]], "pos": pos})
        case("steps-notitle-%d-%s" % (n, pos), {"type": "steps", "items": [[w, 0.5] for w in WORDS[:n]], "pos": pos})
    case("pills-%d" % n, {"type": "pills", "items": [[w, 0.5] for w in WORDS[:n]], "pos": "top"})

CAPS = [("Free tools", 64), ("Free tools", 100), ("Stop paying for", 84), ("Stop paying for", 100), ("HyperFrames rocks", 84),
        ("Every free tool I use daily", 64), ("Every free tool I use daily", 84)]
for k, (t, size) in enumerate(CAPS):   # one caption chunk; tests/test_heights.py predicts it with reels_lib.caption_height
    case("caption-%d-%d" % (k, size), {"caption": t, "size": size})


def spec(name, b, d):
    if "caption" in b:   # a caption case: the whole text is one chunk, on screen from 0.2 s
        words = [{"text": w, "start": 0.2 + 0.3 * i, "end": 0.45 + 0.3 * i} for i, w in enumerate(b["caption"].split())]
        with open(os.path.join(d, "transcript.json"), "w", encoding="utf-8") as f:
            json.dump({"words": words}, f)
        return {"id": name, "duration": 5.0, "fps": 60, "beats": [],
                "captions": {"transcript": "transcript.json", "size": b["size"], "max_words": 99, "max_chars": 99}}
    beat = dict(b, id="b", **{"in": 0.0, "out": 4.0, "anchor": "-"})
    return {"id": name, "duration": 5.0, "fps": 60, "captions": False, "beats": [beat]}


def compose(root):
    out = []
    for name, b in cases:
        d = os.path.join(root, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "storyboard.json"), "w", encoding="utf-8") as f:
            json.dump(spec(name, b, d), f)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "reels-compose.py"), "--spec", os.path.join(d, "storyboard.json"),
                            "--out", os.path.join(d, "public")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print("skipped %s: %s" % (name, r.stderr.strip()[-160:]))
            continue
        out.append({"case": name, "beat": b})
    with open(os.path.join(root, "cases.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("composed %d cases in %s" % (len(out), root))


def merge(root, measured):
    beats = {c["case"]: c["beat"] for c in json.load(open(os.path.join(root, "cases.json"), encoding="utf-8"))}
    rows = [dict(json.loads(l), beat=beats[json.loads(l)["case"]]) for l in open(measured, encoding="utf-8") if l.strip()]
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    with open(FIXTURE, "w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join(json.dumps(r) for r in rows) + "\n]\n")
    print("wrote %d rows to %s" % (len(rows), FIXTURE))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dir")
    ap.add_argument("--merge")
    a = ap.parse_args()
    merge(a.dir, a.merge) if a.merge else compose(a.dir)
