#!/usr/bin/env python3
"""handoff-check.py: gate H1, the editor hand-off checked before it reaches the creator. It reads the edit folder's
FCP 7 XML back and fails, naming the clip or file, on:
  - a clip whose media is not there;
  - a clip that runs past the end of its source;
  - sequence settings that are not the profile's (explainer, reels: 1080x1920 at 60 fps; long-form: 16:9);
  - a hole in the first audio track (the voice, or the footage's sound) where the transcript has a word;
  - a storyboard scene with no clip on any video track;
  - captions.srt missing words the transcript has.

  python3 handoff-check.py --edit videos/<p>/edit --profile explainer|reels|longform
                           [--transcript videos/<p>/transcript.json] [--storyboard videos/<p>/storyboard.json]
"""
import argparse, glob, json, os, re, sys

import nle_xml as X


def words_of(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower())]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--edit", required=True)
    ap.add_argument("--profile", required=True, choices=("explainer", "reels", "longform"))
    ap.add_argument("--transcript", default="")
    ap.add_argument("--storyboard", default="")
    a = ap.parse_args()
    xmls = sorted(glob.glob(os.path.join(a.edit, "*.xml")))
    if not xmls:
        print("H1 FAIL: %s: no .xml (run the hand-off first)" % a.edit)
        sys.exit(1)
    p = X.parse(xmls[0])
    fps = p["timebase"] * (1000 / 1001.0 if p["ntsc"] else 1.0)
    bad = []
    if a.profile in ("explainer", "reels"):
        if (p["width"], p["height"], p["timebase"], p["ntsc"]) != (1080, 1920, 60, False):
            bad.append("sequence: %dx%d at %s fps; a %s is 1080x1920 at 60 fps" % (p["width"], p["height"], round(fps, 3), a.profile))
    elif not (p["width"] > p["height"] and abs(p["width"] / float(p["height"]) - 16 / 9.0) < 0.01):
        bad.append("sequence: %dx%d; long-form is 16:9 (3840x2160 or 1920x1080)" % (p["width"], p["height"]))
    for t in p["video"] + p["audio"]:
        for c in t["clips"]:
            path = X.path_from_url(c["pathurl"] or "")
            if not os.path.isfile(path):
                bad.append("%s: no file at %s" % (c["name"], path))
            if c["duration"] is not None and c["out"] > c["duration"]:
                bad.append("%s: runs %d frames past the end of its source (on %s)" % (c["name"], c["out"] - c["duration"], t["name"]))
    words = []
    if a.transcript and os.path.isfile(a.transcript):
        with open(a.transcript, encoding="utf-8") as f:
            words = json.load(f).get("words", [])
    if words and p["audio"]:
        a1 = p["audio"][0]
        for w in words:
            s, e = w["start"] * fps, w["end"] * fps
            if not any(c["start"] <= s + 0.5 and c["end"] >= e - 0.5 for c in a1["clips"]):
                bad.append("%s: no sound under “%s” at %.2f s" % (a1["name"], w["text"], w["start"]))
    if a.storyboard and os.path.isfile(a.storyboard):
        with open(a.storyboard, encoding="utf-8") as f:
            ids = [s.get("id") for s in json.load(f).get("scenes", [])]
        names = {c["name"] for t in p["video"] for c in t["clips"]}
        bad += ["%s: a scene with no clip on any video track" % i for i in ids if i and i not in names]
    srt = os.path.join(a.edit, "captions.srt")
    if words:
        if not os.path.isfile(srt):
            bad.append("captions.srt: missing")
        else:
            with open(srt, encoding="utf-8") as f:
                cues = [l for l in f.read().splitlines() if l.strip() and not l.strip().isdigit() and "-->" not in l]
            have, k, lost = words_of(" ".join(cues)), 0, []
            for w in (x for wd in words for x in words_of(wd["text"])):
                while k < len(have) and have[k] != w:
                    k += 1
                if k == len(have):
                    lost.append(w)
                else:
                    k += 1
            if lost:
                bad.append("captions.srt: %d words of the transcript are not in it (%s)" % (len(lost), ", ".join(lost[:5])))
    for b in bad:
        print("H1 FAIL: " + b)
    if bad:
        sys.exit(1)
    print("H1 PASS: %s (%d video tracks, %d audio, %d clips)" % (os.path.basename(xmls[0]), len(p["video"]), len(p["audio"]),
                                                                 sum(len(t["clips"]) for t in p["video"] + p["audio"])))


if __name__ == "__main__":
    main()
