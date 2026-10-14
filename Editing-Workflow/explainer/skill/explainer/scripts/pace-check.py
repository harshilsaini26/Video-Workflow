#!/usr/bin/env python3
"""pace-check.py: gate E4's pacing half: something on screen changes at least every few seconds.

  pace-check.py --index public/index.html [--max 6] [--warn 4]

The kit's gap-scan measures stretches with no overlay on screen; an explainer's scenes cover the whole voice by
construction, so it can never find one. This reads the page's scene timeline instead: every scene's entrance and exit,
every item, count, draw and highlight is a moment of change (each tween from its start to its end; a custom scene
counts as changing from its in to its out). Captions are not counted. A stretch with no change longer than --max
seconds fails, naming the scene on screen; one longer than --warn is listed (PLAYBOOK §E1.4: a change every 2 to 4 s).
"""
import argparse, re, sys


def moments(page):
    root = re.search(r'data-composition-id="[^"]*" data-start="0" data-duration="([\d.]+)"', page)
    if not root:
        sys.exit("no composition root in the page")
    D = float(root.group(1))
    block = page[page.index("// scenes"):page.index("// captions")]
    scenes, spans = [], []
    for line in block.splitlines():
        line = line.strip()
        m = re.match(r"// (\w+) \(([\w-]+)\) ([\d.]+) to ([\d.]+) s", line)
        if m:
            scenes.append((float(m.group(3)), m.group(1)))
            continue
        m = re.search(r"window\.\w+\(tl, document\.getElementById\(\"[^\"]*\"\), ([\d.]+), ([\d.]+)\)", line)
        if m:                                                  # a custom scene animates on its own between t0 and t1
            spans.append((float(m.group(1)), float(m.group(2))))
            continue
        m = re.match(r"countUp\('[^']*', [-\d.]+, [-\d.e+]+, ([\d.]+), ([\d.]+),", line)
        if m:
            t = float(m.group(1))
            spans.append((t, t + float(m.group(2))))
            continue
        m = re.match(r"tl\.(fromTo|to|set)\(.*, ([\d.]+)\);$", line)
        if m:
            t = float(m.group(2))
            d = re.findall(r"duration: ([\d.]+)", line)
            amount = re.findall(r"amount: ([\d.]+)", line)
            spans.append((t, t + (float(d[-1]) if d else 0.0) + (float(amount[-1]) if amount else 0.0)))
    return D, sorted(scenes), sorted(spans)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", required=True)
    ap.add_argument("--max", type=float, default=6.0)
    ap.add_argument("--warn", type=float, default=4.0)
    a = ap.parse_args()
    with open(a.index) as f:
        D, scenes, spans = moments(f.read())

    def scene_at(t):
        cur = scenes[0][1] if scenes else "?"
        for t_in, sid in scenes:
            if t_in <= t + 1e-6:
                cur = sid
        return cur

    still, cursor = [], 0.0
    for s, e in spans:
        if s > cursor:
            still.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < D:
        still.append((cursor, D))
    bad = [(s, e) for s, e in still if e - s > a.max]
    warn = [(s, e) for s, e in still if a.warn < e - s <= a.max]
    for s, e in warn:
        print("WARN nothing changes from %.2f to %.2f s (%.1f s, in scene %s)" % (s, e, e - s, scene_at(s)))
    longest = max([e - s for s, e in still] or [0.0])
    if bad:
        for s, e in bad:
            print("E4 FAIL: nothing changes from %.2f to %.2f s (%.1f s, in scene %s); at most %.1f s: add an item, a "
                  "reveal or a new scene on a word inside it" % (s, e, e - s, scene_at(s), a.max))
        sys.exit(1)
    print("E4 PASS: %d scenes, %d moments of change, the longest still stretch %.1f s" % (len(scenes), len(spans), longest))


if __name__ == "__main__":
    main()
