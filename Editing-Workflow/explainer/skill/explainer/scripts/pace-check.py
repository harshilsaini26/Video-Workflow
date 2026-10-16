#!/usr/bin/env python3
"""pace-check.py: gate E4's pacing half: something on screen changes at least every few seconds.

  pace-check.py --index public/index.html [--moments public/moments.json] [--max 3] [--warn 2]

The kit's gap-scan measures stretches with no overlay on screen; an explainer's scenes cover the whole voice by
construction, so it can never find one. This reads `moments.json`, which explainer-compose.py writes next to the page:
every scene's entrance and exit, every item, count, draw and highlight, each from its start to its end (a custom scene
counts as changing from its in to its out). Captions and the living layer (the drifting orbs, each scene's slow
push-in, a scene's idle float or pulse) are not counted: they keep the picture alive, they are not a new picture. A
stretch with no change longer than --max seconds fails, naming the scene on screen; one longer than --warn is listed
(PLAYBOOK §E1.4: a change every 1.5 to 3 s).
"""
import argparse, json, os, sys


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", required=True)
    ap.add_argument("--moments", help="default: moments.json next to the index")
    ap.add_argument("--max", type=float, default=3.0)
    ap.add_argument("--warn", type=float, default=2.0)
    a = ap.parse_args()
    path = a.moments or os.path.join(os.path.dirname(os.path.abspath(a.index)), "moments.json")
    if not os.path.exists(path):
        sys.exit("no %s: compose the page again with explainer-compose.py" % path)
    with open(path) as f:
        M = json.load(f)
    D, scenes, spans = float(M["duration"]), M["scenes"], sorted(M["spans"])

    def scene_at(t):
        cur = scenes[0]["id"] if scenes else "?"
        for sc in scenes:
            if sc["in"] <= t + 1e-6:
                cur = sc["id"]
        return cur

    still, cursor = [], 0.0
    for s, e in spans:
        if s > cursor:
            still.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < D:
        still.append((cursor, D))
    bad = [(s, e) for s, e in still if e - s > a.max]
    for s, e in still:
        if a.warn < e - s <= a.max:
            print("WARN nothing changes from %.2f to %.2f s (%.1f s, in scene %s)" % (s, e, e - s, scene_at(s)))
    if bad:
        for s, e in bad:
            print("E4 FAIL: nothing changes from %.2f to %.2f s (%.1f s, in scene %s); at most %.1f s: add an item, a "
                  "reveal or a new scene on a word inside it" % (s, e, e - s, scene_at(s), a.max))
        sys.exit(1)
    print("E4 PASS: %d scenes, %d moments of change, the longest still stretch %.1f s"
          % (len(scenes), len(spans), max([e - s for s, e in still] or [0.0])))


if __name__ == "__main__":
    main()
