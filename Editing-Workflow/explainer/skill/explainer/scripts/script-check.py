#!/usr/bin/env python3
"""script-check.py: gate E1 for an Explainer script (SPEC §8), and the Checkpoint A sheet.

script.json:
{"title": "...", "target_seconds": 45, "voice": "am_michael",
 "format": "how-to|versus|myth|story|explainer", "audience": "who it is for and the pain it solves",
 "goal": "follow|comment|save|share|link|learn",
 "lines": [{"id": "l0", "say": "what the voice reads", "show": "what the captions and scenes show",
            "break": "comma|sentence|section", "emphasis": ["NPV"], "source": "s1", "fact": false,
            "role": "step|example|myth|truth|problem|solution"}],
 "payoff": "l9", "cta": "l12",
 "sources": {"s1": {"title": "...", "url": "...", "note": "..."}}}

Fails when:
- the shown text is outside the length range (2.7 words a second; 81 to 240 words, 30 to 90 s, narrowed to +-15% of
  target_seconds x 2.7 when there is a target);
- format or goal is set to something unknown;
- the hook (line 0) is over 12 words;
- a line whose shown text has a digit, % or $ (or is marked "fact": true) has no source, or names one that isn't
  listed;
- payoff or cta names a line that doesn't exist;
- line ids repeat.

Warns (PLAYBOOK §E1, §E2; what makes an informative reel spread), and still passes, when:
- format, audience or goal is missing (decide what the reel is for and who it is for first);
- the call to action does not ask for the goal (goal comment: the CTA asks for a comment);
- no line talks to the viewer ("you") or asks them a question;
- no line is a real example (role example);
- the format's shape is missing: how-to steps (two lines with role step), myth then truth, problem then solution,
  versus with a compare picture.

Usage: python3 script-check.py --script videos/<p>/script.json [--report videos/<p>/SCRIPT.md]
"""
import argparse, json, re, sys

WPS = 2.7
MIN_WORDS, MAX_WORDS, HOOK_MAX = 81, 240, 12      # 30 to 90 s at 2.7 words a second
MIN_S, MAX_S = 30, 90
FORMATS = ("how-to", "versus", "myth", "story", "explainer")
GOALS = {"follow": ("follow",), "comment": ("comment", "tell me", "drop", "reply"), "save": ("save",),
         "share": ("share", "send"), "link": ("link", "bio"), "learn": ()}
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
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
if target and not MIN_S <= float(target) <= MAX_S:   # a target outside leaves no length to aim for
    errors.append("target_seconds %g is outside %d to %d s" % (float(target), MIN_S, MAX_S))
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

# ---- the brief: what the reel is for, and the shape that makes it land (warnings) -------------------------------------
warnings = []
fmt, goal, aud = S.get("format"), S.get("goal"), S.get("audience")
if fmt is not None and fmt not in FORMATS:
    errors.append("format %r is not one of %s" % (fmt, ", ".join(FORMATS)))
if goal is not None and goal not in GOALS:
    errors.append("goal %r is not one of %s" % (goal, ", ".join(GOALS)))
if not fmt:
    warnings.append("no format: name the reel's shape (%s)" % ", ".join(FORMATS))
if not aud:
    warnings.append("no audience: say who this is for and the pain it solves")
if not goal:
    warnings.append("no goal: say what the reel should get (%s) and make the call to action ask for it" % ", ".join(GOALS))
by_id = {ln.get("id"): ln for ln in lines}
shown = lambda ln: str(ln.get("show", ""))
if goal in GOALS and GOALS[goal] and S.get("cta") in by_id:
    if not any(v in shown(by_id[S["cta"]]).lower() for v in GOALS[goal]):
        warnings.append("the call to action (%s) does not ask for the goal, %s: %r" % (S["cta"], goal, shown(by_id[S["cta"]])))
if lines and not any(YOU.search(shown(ln)) for ln in lines):
    warnings.append("no line says you: talk to the viewer, not about them")
if lines and not any("?" in shown(ln) for ln in lines):
    warnings.append("no question to the viewer: ask one (in the hook or the call to action) to invite comments")
roles = [ln.get("role") for ln in lines]
if lines and "example" not in roles:
    warnings.append("no real example (role example): one concrete case, number or story makes it stick")
shape = {"how-to": (roles.count("step") >= 2, "a how-to needs its steps: two or more lines with role step"),
         "myth": ("myth" in roles and "truth" in roles and roles.index("myth") < roles.index("truth"),
                  "a myth reel says the myth, then the truth (roles myth and truth, in that order)"),
         "story": ("problem" in roles and "solution" in roles and roles.index("problem") < roles.index("solution"),
                   "a story sets up the problem, then the solution (roles problem and solution, in that order)"),
         "versus": (any(isinstance(v, dict) and v.get("type") == "compare" for ln in lines
                        for v in (ln.get("viz") if isinstance(ln.get("viz"), list) else [ln.get("viz")])),
                    "a versus reel shows the two side by side: a compare picture (viz type compare)")}
if fmt in shape and not shape[fmt][0]:
    warnings.append(shape[fmt][1])

summary = "%d words, est %.1f s, %d lines, %d sources" % (words, words / WPS, len(lines), len(sources))
if a.report:
    out = ["# %s" % S.get("title", "Script"), "", summary, "",
           "**Format:** %s · **Audience:** %s · **Goal:** %s" % (fmt or "-", aud or "-", goal or "-"), "", "## Script (as shown)", ""]
    for n, ln in enumerate(lines, 1):
        tag = []
        if ln.get("id") == S.get("payoff"): tag.append("payoff")
        if ln.get("id") == S.get("cta"): tag.append("call to action")
        if ln.get("source"): tag.append("source %s" % ln["source"])
        if ln.get("role"): tag.append(ln["role"])
        out.append("%d. %s%s" % (n, ln.get("show", ""), ("  _(%s)_" % ", ".join(tag)) if tag else ""))
        if ln.get("say") and ln.get("say") != ln.get("show"):
            out.append("   spoken: \"%s\"" % ln["say"])
    out += ["", "## Sources", ""]
    for k, v in sources.items():
        if isinstance(v, dict):
            out.append("- **%s** %s: %s%s" % (k, v.get("title", ""), v.get("url", ""), (" (%s)" % v["note"]) if v.get("note") else ""))
        else:   # a plain "Publisher, Title, date, link" string
            out.append("- **%s** %s" % (k, v))
    if warnings:
        out += ["", "## Worth a look", ""] + ["- " + w for w in warnings]
    if errors:
        out += ["", "## Gate E1: FAIL", ""] + ["- " + e for e in errors]
    with open(a.report, "w") as f:
        f.write("\n".join(out) + "\n")

for w in warnings:
    print("E1 WARN: " + w)
if errors:
    print("E1 FAIL: " + summary)
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("E1 PASS: " + summary)
