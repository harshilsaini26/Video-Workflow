#!/usr/bin/env python3
"""wording.py: plain spoken words, checked before anything is voiced or cut (explainer gate E1; the reels and long-form
Cutter on the kept transcript; post-check.py on the post caption). It never rewrites: it names the line and why, and
the writer (or the creator) fixes it.

FAIL: leaked AI text, invisible characters, and a hook that opens on a preamble (a greeting, "in this video",
      "stop scrolling", a hashtag or an emoji).
WARN: stock phrases and shapes (wording.json), a dash in spoken text, a hook with no number or name in it, a hook
      longer than 3.0 s, a line over 18 words or 7.5 s (split it).
NOTE: the last line shares no word with the hook (the loop back, where it is natural).

  check_lines([{"id", "text", "say"?, "dur"?}], hook_index=0, rate=2.4) -> {"fail": [...], "warn": [...], "note": [...]}
  python3 wording.py --script script.json [--rate 2.4]
  python3 wording.py --transcript transcript.json --kept cut-list.json      (the kept words, sentence by sentence)

The lists are adapted from sergebulaev/instagram-skills and Jakeschincariol/instagram-agent-skill (both MIT).
"""
import argparse, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK_S, LINE_WORDS, LINE_S, RATE = 3.0, 18, 7.5, 2.4
NUMBER_WORDS = set("one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty hundred thousand "
                   "million billion half double twice".split())
STOP = set("the a an and or but of to in on for with at by from is are was were be it its this that these those you your we our "
           "i my me they them their he she his her not no so as if then than just now how what why who when where here there "
           "can will do does did have has had get got all any some more most one".split())
DASH = re.compile(u"—|–|--")

with open(os.path.join(HERE, "wording.json"), encoding="utf-8") as _f:
    LISTS = json.load(_f)
COMPILED = {k: [(p["id"], re.compile(p["pattern"], re.I), p["why"]) for p in LISTS[k]] for k in ("fail", "hook_fail", "warn")}


def _words(text):
    return re.findall(r"[\w'][\w'\-]*", text or "")


def _content(text):
    return {w.lower().rstrip("s") for w in _words(text) if len(w) >= 3 and w.lower() not in STOP}


def _concrete(text):
    ws = _words(text)
    return (bool(re.search(r"\d", text)) or any(w.lower() in NUMBER_WORDS for w in ws)
            or any(sum(c.isupper() for c in w) >= 2 for w in ws) or any(w[:1].isupper() for w in ws[1:]))


def check_lines(lines, hook_index=0, rate=RATE):
    out = {"fail": [], "warn": [], "note": []}
    for i, ln in enumerate(lines):
        lid, text = ln.get("id", i), ln.get("text") or ""
        say = ln.get("say") if ln.get("say") is not None else text
        tag = "line %s:" % lid
        both = text + "\n" + say
        if any(unicodedata.category(c) == "Cf" for c in both):
            out["fail"].append("%s invisible characters (zero-width or format marks): retype the line" % tag)
        for pid, rx, why in COMPILED["fail"]:
            if rx.search(both):
                out["fail"].append("%s %s: %s" % (tag, pid, why))
        if i == hook_index:
            for pid, rx, why in COMPILED["hook_fail"]:
                if rx.search(text) or rx.search(say):
                    out["fail"].append("%s %s: %s" % (tag, pid, why))
        for pid, rx, why in COMPILED["warn"]:
            if rx.search(text) or rx.search(say):
                out["warn"].append("%s %s: %s" % (tag, pid, why))
        if DASH.search(say):
            out["warn"].append("%s a dash in spoken text: the voice reads it as a pause; use a break or a comma" % tag)
        n = len(_words(say))
        dur = float(ln["dur"]) if ln.get("dur") is not None else n / float(rate)
        if i == hook_index:
            if not _concrete(text):
                out["warn"].append("%s the hook has no number or a name in it: one concrete thing makes the promise real" % tag)
            if dur > HOOK_S:
                out["warn"].append("%s the hook takes %.1f s to say; land it in %.1f s" % (tag, dur, HOOK_S))
        elif n > LINE_WORDS or dur > LINE_S:
            out["warn"].append("%s %d words (%.1f s): split it into two breaths" % (tag, n, dur))
    if len(lines) > 2 and not (_content(lines[-1].get("text")) & _content(lines[hook_index].get("text"))):
        out["note"].append("line %s: shares no word with the hook; a loop back to it, where natural, brings viewers round again"
                           % lines[-1].get("id", len(lines) - 1))
    return out


def _from_script(path):
    with open(path, encoding="utf-8") as f:
        s = json.load(f)
    return [{"id": l.get("id", i), "text": l.get("show", l.get("say", "")), "say": l.get("say")} for i, l in enumerate(s.get("lines", []))]


def _from_transcript(path, kept_path):
    with open(path, encoding="utf-8") as f:
        words = json.load(f).get("words", [])
    with open(kept_path, encoding="utf-8") as f:
        kept = json.load(f).get("kept", [])
    inside = [w for w in words if any(k["start"] - 1e-3 <= w["start"] and w["end"] <= k["end"] + 1e-3 for k in kept)]
    lines, cur = [], []
    for w in inside:
        cur.append(w)
        if re.search(r"[.!?]$", w["text"]):
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    return [{"id": "%.2fs" % c[0]["start"], "text": " ".join(w["text"] for w in c), "dur": c[-1]["end"] - c[0]["start"]} for c in lines]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--script")
    ap.add_argument("--transcript")
    ap.add_argument("--kept")
    ap.add_argument("--rate", type=float, default=RATE)
    a = ap.parse_args()
    if a.script:
        lines = _from_script(a.script)
    elif a.transcript and a.kept:
        lines = _from_transcript(a.transcript, a.kept)
    else:
        ap.error("give --script, or --transcript with --kept")
    r = check_lines(lines, rate=a.rate)
    for k in ("fail", "warn", "note"):
        for m in r[k]:
            print("WORDING %s: %s" % (k.upper(), m))
    print("WORDING %s: %d lines, %d to fix, %d to look at" % ("FAIL" if r["fail"] else "PASS", len(lines), len(r["fail"]), len(r["warn"])))
    sys.exit(1 if r["fail"] else 0)


if __name__ == "__main__":
    main()
