#!/usr/bin/env python3
"""script-check.py: gate E1 for an Explainer script (SPEC §8), and the Checkpoint A sheet.

script.json:
{"title": "...", "target_seconds": 75, "voice": "am_michael",
 "lines": [{"id": "l0", "say": "what the voice reads", "show": "what the captions and scenes show",
            "break": "comma|sentence|section", "emphasis": ["NPV"], "source": "s1", "fact": false}],
 "payoff": "l9", "cta": "l12",
 "sources": {"s1": {"title": "...", "url": "...", "note": "..."}}}

Fails when:
- the shown text is outside the length range (2.7 words a second; 160 to 240 words, narrowed to +-15% of
  target_seconds x 2.7 when there is a target);
- the hook (line 0) is over 12 words;
- a line whose shown text has a digit, % or $ (or is marked "fact": true) has no source, or names one that isn't
  listed;
- payoff or cta names a line that doesn't exist;
- line ids repeat.

Usage: python3 script-check.py --script videos/<p>/script.json [--report videos/<p>/SCRIPT.md]
"""
import argparse, json, re, sys

WPS = 2.7
MIN_WORDS, MAX_WORDS, HOOK_MAX = 160, 240, 12
NUMERIC = re.compile(r"[\d%$]")

ap = argparse.ArgumentParser()
ap.add_argument("--script", required=True)
ap.add_argument("--report")
a = ap.parse_args()

S = json.load(open(a.script))
lines = S.get("lines", [])
sources = S.get("sources", {}) or {}
errors = []

ids = [ln.get("id") for ln in lines]
dupes = sorted({i for i in ids if ids.count(i) > 1})
if dupes:
    errors.append("line ids repeat: %s" % ", ".join(map(str, dupes)))
if not lines:
    errors.append("no lines")

words = sum(len(str(ln.get("show", "")).split()) for ln in lines)
lo, hi = MIN_WORDS, MAX_WORDS
target = S.get("target_seconds")
if target and not 60 <= float(target) <= 90:   # a reel is 60 to 90 s; a target outside leaves no length to aim for
    errors.append("target_seconds %g is outside 60 to 90 s" % float(target))
else:
    if target:
        t = float(target) * WPS
        lo, hi = max(MIN_WORDS, round(t * 0.85)), min(MAX_WORDS, round(t * 1.15))
    if words < lo:
        errors.append("%d words: under %d words (about %.0f s)" % (words, lo, lo / WPS))
    if words > hi:
        errors.append("%d words: over %d words (about %.0f s)" % (words, hi, hi / WPS))

if lines:
    hook = len(str(lines[0].get("show", "")).split())
    if hook > HOOK_MAX:
        errors.append("hook is %d words (line %s); keep it to %d" % (hook, lines[0].get("id"), HOOK_MAX))

for ln in lines:
    needs = bool(NUMERIC.search(str(ln.get("show", "")))) or bool(ln.get("fact"))
    src = ln.get("source")
    if needs and not src:
        errors.append("line %s has a number or a fact but no source: %r" % (ln.get("id"), ln.get("show")))
    if src and src not in sources:
        errors.append("line %s names source %r, which isn't in sources" % (ln.get("id"), src))

for key in ("payoff", "cta"):
    if S.get(key) not in ids:
        errors.append("%s names line %r, which doesn't exist" % (key, S.get(key)))

summary = "%d words, est %.1f s, %d lines, %d sources" % (words, words / WPS, len(lines), len(sources))
if a.report:
    out = ["# %s" % S.get("title", "Script"), "", summary, "", "## Script (as shown)", ""]
    for n, ln in enumerate(lines, 1):
        tag = []
        if ln.get("id") == S.get("payoff"): tag.append("payoff")
        if ln.get("id") == S.get("cta"): tag.append("call to action")
        if ln.get("source"): tag.append("source %s" % ln["source"])
        out.append("%d. %s%s" % (n, ln.get("show", ""), ("  _(%s)_" % ", ".join(tag)) if tag else ""))
        if ln.get("say") and ln.get("say") != ln.get("show"):
            out.append("   spoken: \"%s\"" % ln["say"])
    out += ["", "## Sources", ""]
    for k, v in sources.items():
        if isinstance(v, dict):
            out.append("- **%s** %s: %s%s" % (k, v.get("title", ""), v.get("url", ""), (" (%s)" % v["note"]) if v.get("note") else ""))
        else:   # a plain "Publisher, Title, date, link" string
            out.append("- **%s** %s" % (k, v))
    if errors:
        out += ["", "## Gate E1: FAIL", ""] + ["- " + e for e in errors]
    with open(a.report, "w") as f:
        f.write("\n".join(out) + "\n")

if errors:
    print("E1 FAIL: " + summary)
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("E1 PASS: " + summary)
