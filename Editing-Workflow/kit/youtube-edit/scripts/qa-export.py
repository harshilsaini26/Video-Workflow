#!/usr/bin/env python3
"""qa-export.py: the existing checks, run on the creator's own export from the editor. It only reports (exit 0):
the creator decides. Size and frame rate against the profile, integrated loudness (-14 LUFS for the apps), black
frames, and for an explainer the motion check (E6, motion-check.py) when the explainer scripts are found.

  python3 qa-export.py --video <export.mp4> --profile explainer|reels|longform
"""
import argparse, json, os, re, subprocess, sys

WANT = {"explainer": ((1080, 1920), 60), "reels": ((1080, 1920), 60), "longform": (None, None)}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--video", required=True)
    ap.add_argument("--profile", required=True, choices=sorted(WANT))
    a = ap.parse_args()
    if not os.path.isfile(a.video):
        print("QA-EXPORT: no file at %s" % a.video)
        return
    notes = []
    r = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate", "-of", "json", a.video])
    s = json.loads(r.stdout or "{}").get("streams", [{}])[0]
    w, h = s.get("width"), s.get("height")
    num, den = (s.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = round(int(num) / float(den or 1), 3) if num else 0
    size, rate = WANT[a.profile]
    line = "size %sx%s" % (w, h)
    if size and (w, h) != size:
        line += " (want %dx%d)" % size
        notes.append("size")
    print("  " + line)
    line = "frame rate %s" % fps
    if rate and abs(fps - rate) > 0.01:
        line += " (want %d)" % rate
        notes.append("frame rate")
    print("  " + line)
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-af", "ebur128=peak=true", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    if m:
        lufs = float(m[-1])
        print("  loudness %.1f LUFS%s" % (lufs, "" if abs(lufs + 14) <= 1 else " (the apps play at -14)"))
        if abs(lufs + 14) > 1:
            notes.append("loudness")
    else:
        print("  loudness: no sound to measure (LUFS)")
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vf", "blackdetect=d=0.1:pix_th=0.08", "-an", "-f", "null", "-"])
    blacks = re.findall(r"black_start:([\d.]+)", r.stderr)
    print("  black frames: %s" % (", ".join("%.2f s" % float(b) for b in blacks) if blacks else "none"))
    if blacks:
        notes.append("black frames")
    if a.profile == "explainer":
        here = os.path.dirname(os.path.abspath(__file__))
        for c in [os.environ.get("EXPLAINER_SCRIPTS", ""), os.path.join(here, "..", "..", "explainer", "scripts"),
                  os.path.join(here, "..", "..", "..", "explainer", "skill", "explainer", "scripts")]:
            mc = os.path.join(c, "motion-check.py")
            if c and os.path.isfile(mc):
                r = sh([sys.executable, mc, "--video", a.video])
                print("  " + (r.stdout.strip().splitlines() or ["E6: no result"])[-1])
                if r.returncode != 0:
                    notes.append("motion (E6)")
                break
    print("QA-EXPORT: %s" % ("to look at: " + ", ".join(notes) if notes else "nothing to flag"))


if __name__ == "__main__":
    main()
