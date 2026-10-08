#!/usr/bin/env python3
"""reels-conform.py: a stock clip, screen recording, generated clip or still -> a vertical cutaway for a Reel.

Output: 1080x1920 (or 2160x3840 with --uhd), 60 fps constant, no audio, a keyframe every 30 frames (seeks never freeze
the render), H.264 CRF 16, BT.709 tags, plus <out>.sheet.png (first, middle, last frame) to look at before use.

How a source that isn't 9:16 fills the frame (--fit):
  cover    scale to fill and crop; --focus 0..1 picks the horizontal crop (0 = left edge, 0.5 = centre, 1 = right)
  blur     the source whole in the middle, over a blurred, darkened copy of itself (screen recordings, landscape B-roll)
  contain  the source whole on black (rarely right for a Reel)

A still (.png .jpg .jpeg .webp) becomes a slow push (--push, default 1.06) for --dur seconds.

Usage:
  python3 reels-conform.py --in raw.mp4 --out public/broll/desk.mp4 [--start 2.0] [--dur 3.5] [--fit cover|blur|contain]
                           [--focus 0.5] [--uhd] [--fps 60] [--push 1.06] [--grade] [--vf "extra,filters"]
Exit 1 (and nothing written) when the source is shorter than --start + --dur.
"""
import argparse, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--start", type=float, default=0.0)
ap.add_argument("--dur", type=float)
ap.add_argument("--fit", choices=("cover", "blur", "contain"), default="cover")
ap.add_argument("--focus", type=float, default=0.5)
ap.add_argument("--uhd", action="store_true", help="2160x3840 instead of 1080x1920 (zoom headroom)")
ap.add_argument("--fps", type=int, default=60)
ap.add_argument("--push", type=float, default=1.06)
ap.add_argument("--grade", action="store_true", help="a gentle contrast and saturation lift toward camera footage")
ap.add_argument("--vf", default="", help="extra filters applied to the source first, e.g. a blur box over a logo")
a = ap.parse_args()

W, H = (2160, 3840) if a.uhd else (1080, 1920)
if not 0.0 <= a.focus <= 1.0:
    sys.exit("--focus must be between 0 and 1")
still = os.path.splitext(a.src)[1].lower() in (".png", ".jpg", ".jpeg", ".webp")

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    if r.returncode:
        sys.exit("cannot read %s: %s" % (path, r.stderr.strip()))
    return json.loads(r.stdout)

p = probe(a.src)
v = next((s for s in p["streams"] if s["codec_type"] == "video"), None)
if not v:
    sys.exit("no picture in %s" % a.src)
if still:
    if not a.dur:
        sys.exit("a still needs --dur")
    dur = a.dur
else:
    src_dur = float(p["format"]["duration"])
    dur = a.dur if a.dur else src_dur - a.start
    if a.start + dur > src_dur + 1e-3:
        sys.exit("requested %.2f s from %.2f s is longer than the source (%.2f s): pick a shorter window" % (dur, a.start, src_dur))

pre = (a.vf + ",") if a.vf else ""
grade = ",eq=contrast=1.04:saturation=1.06" if a.grade else ""
cover = "scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,crop=%d:%d:(iw-%d)*%.4f:(ih-%d)/2" % (W, H, W, H, W, a.focus, H)
if a.fit == "cover":
    graph = "[0:v]%s%s%s,setsar=1[v]" % (pre, cover, grade)
elif a.fit == "contain":
    graph = "[0:v]%sscale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black%s,setsar=1[v]" % (pre, W, H, W, H, grade)
else:
    graph = ("[0:v]%ssplit[a][b];[a]%s,boxblur=%d:2,eq=brightness=-0.10:saturation=0.9[bg];"
             "[b]scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2%s,setsar=1[v]"
             % (pre, cover.replace(":(iw-%d)*%.4f:" % (W, a.focus), ":(iw-%d)/2:" % W), max(20, W // 27), W - 2 * (W // 27), H, grade))

if still:
    n = int(round(dur * a.fps))
    graph = graph.replace("[v]", "[s]") + ";[s]zoompan=z='1+(%.4f-1)*on/%d':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d[v]" % (a.push, max(1, n - 1), n, W, H, a.fps)
    inp = ["-loop", "1", "-framerate", str(a.fps), "-t", "%.3f" % dur, "-i", a.src]
else:
    inp = ["-ss", "%.3f" % a.start, "-t", "%.3f" % dur, "-i", a.src]
graph += ";[v]fps=%d,format=yuv420p[o]" % a.fps

os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
cmd = (["ffmpeg", "-y", "-v", "error"] + inp + ["-filter_complex", graph, "-map", "[o]", "-an", "-t", "%.3f" % dur,
       "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
       "-movflags", "+faststart+write_colr", a.out])
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode:
    sys.exit("ffmpeg failed: %s" % r.stderr.strip()[-600:])

o = probe(a.out)
ov = next(s for s in o["streams"] if s["codec_type"] == "video")
d_out = float(o["format"]["duration"])
nfr = int(round(d_out * a.fps))
sheet = a.out + ".sheet.png"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.out, "-vf",
                "select='eq(n,0)+eq(n,%d)+eq(n,%d)',scale=360:-2,tile=3x1" % (nfr // 2, max(0, nfr - 2)),
                "-frames:v", "1", "-fps_mode", "vfr", sheet], check=True)
print("wrote %s: %dx%d, %s fps, %.2f s, no audio, fit %s%s" % (a.out, ov["width"], ov["height"], ov["r_frame_rate"], d_out, a.fit,
      " (still, push %.2f)" % a.push if still else ""))
print("sheet: %s (look at it before use)" % sheet)
