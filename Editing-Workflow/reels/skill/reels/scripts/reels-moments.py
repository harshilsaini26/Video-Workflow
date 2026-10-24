#!/usr/bin/env python3
"""reels-moments.py: reels from a long video (PLAYBOOK §R12). The Director judges what is worth a reel; this script
shows the transcript in windows and checks the picks, so "three reels from my long video" is the same every time.

  python3 reels-moments.py --transcript T --windows [--minutes 8 --overlap 1]
      the transcript as timed sentences, in overlapping windows, times always absolute (m:ss.ss)
  python3 reels-moments.py --transcript T --check moments.json --out MOMENTS.md [--scaffold videos/]
      moments.json: [{"start", "end", "score" (0 to 100), "hook", "why", "payoff"}]
      checks the schema; snaps each start to its sentence's first word and each end to its sentence's last word;
      fails a moment outside 15 to 60 s; of two moments overlapping by more than half, keeps the higher score; flags
      lines that need earlier context ("as I said"); writes moments.checked.json next to moments.json and MOMENTS.md for
      the creator to pick from; --scaffold makes videos/<long>-reel-<n>/ with a cut-list.json seeded from each moment.

The rubric the Director scores with (PLAYBOOK §R12) is adapted from Anil-matcha/AI-Youtube-Shorts-Generator (MIT).
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_lib as L

MIN_S, MAX_S, OVERLAP = 15.0, 60.0, 0.5
CONTEXT = ("as I said", "as I mentioned", "like I said", "like I mentioned", "as we saw", "we talked about", "earlier")
NEED = ("start", "end", "score", "hook", "why", "payoff")


def clock(t):
    return "%d:%05.2f" % (int(t // 60), t - 60 * int(t // 60))


def sentences(words):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if L.ends_sentence(w["text"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"start": c[0]["start"], "end": c[-1]["end"], "text": " ".join(w["text"] for w in c)} for c in out]


def snap(t, sents, edge):
    for s in sents:
        if s["start"] - 1e-6 <= t <= s["end"] + 1e-6:
            return s[edge]
    nearest = min(sents, key=lambda s: min(abs(s["start"] - t), abs(s["end"] - t)))
    return nearest[edge]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--windows", action="store_true")
    ap.add_argument("--minutes", type=float, default=8.0)
    ap.add_argument("--overlap", type=float, default=1.0)
    ap.add_argument("--check")
    ap.add_argument("--out")
    ap.add_argument("--scaffold")
    a = ap.parse_args()
    try:
        run(a, ap)
    except (OSError, ValueError, AttributeError) as e:
        print("MOMENTS ERROR: cannot read %s (%s)" % (getattr(e, "filename", None) or a.check or a.transcript, e))
        sys.exit(2)


def run(a, ap):
    with open(a.transcript, encoding="utf-8") as f:
        words = json.load(f).get("words", [])
    sents = sentences(words)
    if not sents:
        print("MOMENTS FAIL: %s has no words" % a.transcript)
        sys.exit(1)
    if a.windows:
        span, step, t, n = a.minutes * 60, (a.minutes - a.overlap) * 60, 0.0, 1
        end = sents[-1]["end"]
        while t < end:
            print("== window %d: %s to %s" % (n, clock(t)[:-3], clock(min(t + span, end))[:-3]))
            for s in sents:
                if t <= s["start"] < t + span:
                    print("[%s] %s" % (clock(s["start"]), s["text"]))
            t, n = t + step, n + 1
        return
    if not a.check or not a.out:
        ap.error("give --windows, or --check moments.json with --out MOMENTS.md")
    with open(a.check, encoding="utf-8") as f:
        picks = json.load(f)
    errs, notes, kept = [], [], []
    for i, m in enumerate(picks, 1):
        miss = [k for k in NEED if k not in m]
        if miss:
            errs.append("moment %d: needs %s" % (i, ", ".join(miss)))
            continue
        s, e = snap(float(m["start"]), sents, "start"), snap(float(m["end"]), sents, "end")
        if not MIN_S <= e - s <= MAX_S:
            errs.append("moment %d (%s to %s): %.1f s once snapped to sentences; a reel from a long video is 15 to 60 s"
                        % (i, clock(s), clock(e), e - s))
            continue
        text = " ".join(x["text"] for x in sents if s - 1e-6 <= x["start"] and x["end"] <= e + 1e-6)
        leaks = [c for c in CONTEXT if re.search(r"\b%s\b" % re.escape(c), text, re.I)]
        kept.append(dict(m, start=round(s, 3), end=round(e, 3), n=i, leaks=leaks))
    for k in sorted(kept, key=lambda k: -float(k["score"])):
        if k.get("dropped"):
            continue
        for o in kept:
            if o is k or o.get("dropped"):
                continue
            ov = min(k["end"], o["end"]) - max(k["start"], o["start"])
            if ov > OVERLAP * min(k["end"] - k["start"], o["end"] - o["start"]) and float(o["score"]) <= float(k["score"]):
                o["dropped"] = True
                notes.append("moment %d overlaps moment %d by more than half: kept %d (score %s)" % (o["n"], k["n"], k["n"], k["score"]))
    final = sorted([k for k in kept if not k.get("dropped")], key=lambda k: k["start"])
    for k in final:
        for c in k["leaks"]:
            notes.append("moment %d says “%s”: it needs earlier context; open it so it stands alone, or pick another" % (k["n"], c))
    out = ["# Moments", "", "Picked from %s. Choose the ones to make; each becomes its own reel." % os.path.basename(os.path.dirname(os.path.abspath(a.transcript))), "",
           "| # | From | To | Length | Score | Hook | Why | Payoff | Note |", "|---|---|---|---|---|---|---|---|---|"]
    for j, k in enumerate(final, 1):
        out.append("| %d | %s | %s | %.1f s | %s | %s | %s | %s | %s |" % (j, clock(k["start"]), clock(k["end"]), k["end"] - k["start"], k["score"],
                                                                         k["hook"], k["why"], k["payoff"], "; ".join("says “%s”" % c for c in k["leaks"])))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    clean = [{x: k[x] for x in NEED} for k in final]
    with open(os.path.join(os.path.dirname(os.path.abspath(a.check)), "moments.checked.json"), "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=1)
    for n in notes:
        print("MOMENTS NOTE: " + n)
    for e in errs:
        print("MOMENTS FAIL: " + e)
    if errs:
        sys.exit(1)
    if a.scaffold:
        long = os.path.basename(os.path.dirname(os.path.abspath(a.transcript)))
        for j, k in enumerate(clean, 1):
            d = os.path.join(a.scaffold, "%s-reel-%d" % (long, j))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "cut-list.json"), "w", encoding="utf-8") as f:
                json.dump({"source_duration": words[-1]["end"], "kept": [{"start": k["start"], "end": k["end"]}], "removed": []}, f, indent=1)
            with open(os.path.join(d, "MOMENT.md"), "w", encoding="utf-8") as f:
                f.write("# %s, reel %d\n\nFrom %s to %s of %s.\n\n- Hook: %s\n- Why: %s\n- Payoff: %s\n"
                        % (long, j, clock(k["start"]), clock(k["end"]), long, k["hook"], k["why"], k["payoff"]))
    print("MOMENTS PASS: %d of %d moments kept%s" % (len(clean), len(picks), (", scaffolded in %s" % a.scaffold) if a.scaffold else ""))


if __name__ == "__main__":
    main()
