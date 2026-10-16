#!/usr/bin/env python3
"""layout-check.py: gate E5, a clean picture. Every scene is looked at in Chromium on this machine, at the moment it is fully
built, and fails on text over text, text covered by or crossing a shape, text spilling out of its card, anything outside
the safe area, text under 28 px, and (from `hyperframes check`) clipped text and WCAG contrast failures. No tokens.

  layout-check.py --index videos/<p>/public/index.html [--no-hf]

Reads moments.json next to the page (the composer writes it). Exit 1 with "E5 FAIL: <scene>: <text>: <problem>" lines;
"E5 PASS" when clean. --no-hf skips the HyperFrames pass (faster; the probe alone).
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout_check as LC

WORDS = {"overlap": "%s", "covered": "is %s", "crosses": "%s", "spill": "%s", "outside": "%s", "small": "%s", "missing": "%s"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", required=True)
    ap.add_argument("--no-hf", action="store_true", help="skip `hyperframes check` (the probe alone)")
    a = ap.parse_args()
    pub = os.path.dirname(os.path.abspath(a.index))
    with open(os.path.join(pub, "moments.json")) as f:
        moments = json.load(f)
    smp = LC.samples(moments)
    try:
        issues = LC.probe(a.index, smp)
        hf = [] if a.no_hf else LC.hf_findings(LC.hf_check(pub, smp), moments["scenes"])
    except RuntimeError as e:
        print("E5 ERROR: %s" % e)
        sys.exit(2)
    lines = []
    for i in issues:
        what = WORDS.get(i["kind"], "%s") % i["detail"]
        lines.append("%s: %s%s (at %.2f s)" % (i["scene"], ('"%s" ' % i["text"]) if i["text"] else "", what, i["t"]))
    for i in hf:
        lines.append("%s: %s%s (hyperframes %s at %s s)" % (i["scene"], ('"%s" ' % i["text"]) if i.get("text") else "",
                                                            i.get("message", ""), i["code"], i.get("time", "-")))
    for line in dict.fromkeys(lines):
        print("E5 FAIL: " + line)
    if lines:
        sys.exit(1)
    print("E5 PASS: %d scenes clean (overlap, cover, spill, safe area, size%s)" % (len(smp), "" if a.no_hf else ", contrast, clipping"))


if __name__ == "__main__":
    main()
