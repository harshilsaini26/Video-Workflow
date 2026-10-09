#!/usr/bin/env python3
"""reels-storyboard-md.py: the delivery STORYBOARD.md for a Reel (time / beat / on screen, the captions, the camera, the
loop, and every asset with its licence), generated from the same storyboard.json the composition is built from.

The kit's storyboard-md.py describes the 16:9 formats only; this one knows the Reels formats and adds the captions, the
loop, and the assets with their licences.

Usage: python3 reels-storyboard-md.py --spec videos/<p>/storyboard.json --out deliver/STORYBOARD.md --title "my-reel v2"
                                      [--assets videos/<p>/ASSET-REQUESTS.md] [--note "what changed"] [--concern "..."]
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--spec", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--title", required=True)
ap.add_argument("--assets")
ap.add_argument("--note", action="append", default=[])
ap.add_argument("--concern", action="append", default=[])
a = ap.parse_args()

S = json.load(open(a.spec))
WHAT = {"hook": "hook text", "headline": "headline", "point": "big point", "steps": "numbered steps card",
        "pills": "pills", "logo": "logo plate + pop", "chip": "punchline chip", "stat": "count-up number",
        "clip": "full-frame clip", "image": "full-frame image"}

def item_text(it):
    return it["text"] if isinstance(it, dict) else it[0]

def on_screen(b):
    t = b["type"]
    if t == "stat":
        # the same digits the reel shows (reels-compose.py writes the number with full_digits too)
        return L.full_digits(float(b["value"]), b.get("prefix", ""), b.get("suffix", ""), int(b.get("decimals", 0))) + (
            (" · " + b["label"]) if b.get("label") else "")
    if b.get("items"):
        return ((b["title"] + ": ") if b.get("title") else "") + ", ".join(item_text(i) for i in b["items"])
    if b.get("text"):
        return b["text"] + ((" · " + b["sub"]) if b.get("sub") else "")
    if b.get("label"):
        return "%s · %s" % (os.path.basename(b.get("src", "")), b["label"])
    return os.path.basename(b.get("src", ""))

out = ["# " + a.title, ""]
if a.note:
    out += ["## What changed", ""] + ["- " + n for n in a.note] + [""]
if a.concern:
    out += ["## Concerns to check", ""] + ["- " + c for c in a.concern] + [""]
out += ["## %s (%.1f s, %s fps, 1080x1920)" % (S["id"], float(S["duration"]), S.get("fps", 60)), "",
        "| Time | Beat | On screen | Anchor |", "|---|---|---|---|"]
for b in sorted(S.get("beats", []), key=lambda b: float(b["in"])):
    anchor = "-" if b.get("anchor") in (None, "-") else '"%s"' % str(b["anchor"]).replace("|", "/")
    out.append("| %.1f - %.1f | %s | %s | %s |" % (float(b["in"]), float(b["out"]), WHAT.get(b["type"], b["type"]),
                                                 on_screen(b).replace("|", "/"), anchor))
moves = [op for op in S.get("camera", []) if op[0] != "set"]
sets = [op for op in S.get("camera", []) if op[0] == "set"]
out.append("| camera | %d moves, %d framing sets | %s | |" % (len(moves), len(sets), ", ".join("%s %.1f" % (op[0], float(op[1])) for op in moves)))
C = S.get("captions", {})
if C is True or C is None:
    C = {}
out += ["", "**Captions:** " + ("off" if C is False else "burned in, up to %s words at a time%s%s" % (
    C.get("max_words", 3), (", off " + ", ".join("%.1f-%.1f s" % tuple(r) for r in C.get("off", []))) if C.get("off") else "",
    (", names: " + ", ".join(C.get("terms", []))) if C.get("terms") else ""))]
if S.get("loop"):
    lp = S["loop"]
    out.append("**Loop:** last \"%s\" → first \"%s\"%s" % (lp.get("last", "?"), lp.get("first", "?"), (" (%s)" % lp["note"]) if lp.get("note") else ""))
if S.get("sounds"):
    out.append("**Sounds:** " + ", ".join("%s at %.1f s" % (os.path.basename(s["src"]), float(s["at"])) for s in S["sounds"]))
if a.assets and os.path.exists(a.assets):
    rows = [l for l in open(a.assets).read().splitlines() if re.match(r"\| r\d+ ", l)]
    out += ["", "## Assets and licences", "", "| id | kind | file | source | licence | used |", "|---|---|---|---|---|---|"]
    for l in rows:
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) >= 12 and c[7] == "filled":
            out.append("| %s | %s | %s | %s | %s | %s |" % (c[0], c[1], c[8], c[9], c[10], c[11]))
out.append("")
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
open(a.out, "w").write("\n".join(out))
print("wrote %s (%d beats)" % (a.out, len(S.get("beats", []))))
