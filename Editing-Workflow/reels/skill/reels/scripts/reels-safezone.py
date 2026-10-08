#!/usr/bin/env python3
"""reels-safezone.py: draw the platform safe zone over snapshots so a person (or an agent reading the PNG) can see at a
glance whether anything important sits under Instagram, TikTok or YouTube Shorts interface.

Shaded red: the areas the platforms cover (top 14 %, bottom 35 %, 6 % each side: Meta's published box, PLAYBOOK §R3).
Shaded orange: the right-hand action column band (below y 960, the outer 150 px each side) where centred content stays
narrower. Cyan outline: the caption slot. Frames of any 9:16 size are scaled to match.

Usage:
  python3 reels-safezone.py --dir videos/<p>/snaps --out videos/<p>/snaps/guides [--sheet]
  python3 reels-safezone.py --in a.png b.png --out guides/
Writes one guided PNG per input (same name) and, with --sheet, guides/sheet.png (4 columns, 270 px wide each).
"""
import argparse, glob, json, math, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inputs", nargs="*", default=[])
ap.add_argument("--dir")
ap.add_argument("--out", required=True)
ap.add_argument("--sheet", action="store_true")
a = ap.parse_args()

files = list(a.inputs)
if a.dir:
    files += sorted(f for f in glob.glob(os.path.join(a.dir, "*.png")) if os.path.basename(f) != "sheet.png")
if not files:
    sys.exit("no PNG to guide (give --in files or --dir)")
os.makedirs(a.out, exist_ok=True)

def size(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "json", path], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    return int(s["width"]), int(s["height"])

outs = []
for f in files:
    w, h = size(f)
    if abs(w / h - L.W / L.H) > 0.02:
        print("skip %s: %dx%d is not 9:16" % (f, w, h)); continue
    k = w / L.W
    sx = lambda v: int(round(v * k))
    boxes = [
        (0, 0, w, sx(L.SAFE_TOP), "red@0.30"),                                         # top band
        (0, h - sx(L.SAFE_BOTTOM), w, sx(L.SAFE_BOTTOM), "red@0.30"),                  # bottom band
        (0, sx(L.SAFE_TOP), sx(L.SAFE_SIDE), h - sx(L.SAFE_TOP + L.SAFE_BOTTOM), "red@0.30"),          # left
        (w - sx(L.SAFE_SIDE), sx(L.SAFE_TOP), sx(L.SAFE_SIDE), h - sx(L.SAFE_TOP + L.SAFE_BOTTOM), "red@0.30"),   # right
        (sx(L.SAFE_SIDE), sx(L.RIGHT_COL_TOP), sx(L.RIGHT_COL_W - L.SAFE_SIDE), sx(L.SAFE["bottom"] - L.RIGHT_COL_TOP), "orange@0.25"),
        (w - sx(L.RIGHT_COL_W), sx(L.RIGHT_COL_TOP), sx(L.RIGHT_COL_W - L.SAFE_SIDE), sx(L.SAFE["bottom"] - L.RIGHT_COL_TOP), "orange@0.25"),
    ]
    vf = ",".join("drawbox=x=%d:y=%d:w=%d:h=%d:color=%s:t=fill" % b for b in boxes)
    vf += ",drawbox=x=%d:y=%d:w=%d:h=%d:color=cyan@0.9:t=%d" % (sx(L.NARROW["left"]), sx(L.CAPTION_TOP), sx(L.NARROW["right"] - L.NARROW["left"]),
                                                                sx(L.CAPTION_MAX_BOTTOM - L.CAPTION_TOP), max(2, sx(4)))
    dst = os.path.join(a.out, os.path.basename(f))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f, "-vf", vf, dst], check=True)
    outs.append(dst)
    print("guided", dst)

if a.sheet and outs:
    cols = 4; rows = math.ceil(len(outs) / cols)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for o in outs: cmd += ["-i", o]
    n = len(outs)
    while n % cols: cmd += ["-i", outs[-1]]; n += 1
    scaled = ";".join("[%d]scale=270:480,setsar=1[s%d]" % (i, i) for i in range(n))     # frames may differ in size
    cmd += ["-filter_complex", scaled + ";" + "".join("[s%d]" % i for i in range(n)) + "concat=n=%d:v=1:a=0,tile=%dx%d" % (n, cols, rows),
            "-frames:v", "1", os.path.join(a.out, "sheet.png")]
    subprocess.run(cmd, check=True)
    print("sheet:", os.path.join(a.out, "sheet.png"))
