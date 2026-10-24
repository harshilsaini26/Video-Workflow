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
- the estimated length is outside 30 to 90 s, or outside target_seconds +-15% (inside 30 to 90) when there is a
  target. The estimate is the spoken words at the voice's own rate (voice-rates.json, measured from its samples by
  tts-kokoro.py --samples; 2.4 words a second until then, am_michael's) plus the pauses between lines (SOP S4);
- there are more section breaks than 3 every 75 s (each is a long pause; SOP S5);
- with --voice voice.wav (the script voiced once before Checkpoint A, SOP S16): the voiced length is over 90 s, with
  the lines to trim listed (never the hook, the payoff or the call to action);
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

Usage: python3 script-check.py --script videos/<p>/script.json [--report videos/<p>/SCRIPT.md] [--voice voice.wav]
       [--rates voice-rates.json]
"""
import argparse, json, os, re, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
WPS = 2.4                    # am_michael at 1.0, measured on the RAG reel; a voice's own rate replaces it
PAUSE = {"comma": 0.15, "sentence": 0.35, "section": 0.6}       # tts-kokoro.py's pauses between lines
HOOK_MAX = 12
MIN_S, MAX_S = 30, 90
SECTIONS_PER_75 = 3
FORMATS = ("how-to", "versus", "myth", "story", "explainer")
GOALS = {"follow": ("follow",), "comment": ("comment", "tell me", "drop", "reply"), "save": ("save",),
         "share": ("share", "send"), "link": ("link", "bio"), "learn": ()}
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
NUMERIC = re.compile(r"[\d%$]")

ap = argparse.ArgumentParser()
ap.add_argument("--script", required=True)
ap.add_argument("--report")
ap.add_argument("--voice", help="the voiced script (voice.wav): its real length is checked")
ap.add_argument("--rates", default=os.path.join(HERE, "..", "voice-rates.json"))
a = ap.parse_args()

with open(a.script, encoding="utf-8") as f:
    S = json.load(f)
lines = S.get("lines", [])
sources = S.get("sources", {}) or {}
errors = []

ids = [ln.get("id") for ln in lines]
dupes = sorted({i for i in ids if ids.count(i) > 1})
if dupes:
    errors.append("line ids repeat: %s" % ", ".join(map(str, dupes)))
if not lines:
    errors.append("no lines")

spoken = lambda ln: str(ln.get("say") or ln.get("show", ""))
words = sum(len(spoken(ln).split()) for ln in lines)
voice, speed = S.get("voice", "am_michael"), float(S.get("speed", 1.0))
rates = {}
if a.rates and os.path.exists(a.rates):
    with open(a.rates, encoding="utf-8") as f:
        rates = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
rate = float(rates.get("%s@%g" % (voice, speed), WPS))
pauses = sum(PAUSE.get(ln.get("break") or "sentence", PAUSE["sentence"]) for ln in lines[:-1])
est = words / rate + pauses
target = S.get("target_seconds")
if target and not MIN_S <= float(target) <= MAX_S:   # a target outside leaves no length to aim for
    errors.append("target_seconds %g is outside %d to %d s" % (float(target), MIN_S, MAX_S))
elif est < MIN_S:
    errors.append("about %.1f s: under 30 s (at %.1f words a second, at least %d words)" % (est, rate, (MIN_S - pauses) * rate))
elif est > MAX_S:
    errors.append("about %.1f s: over 90 s (at %.1f words a second, at most %d words)" % (est, rate, (MAX_S - pauses) * rate))
elif target:
    lo, hi = max(MIN_S, float(target) * 0.85), min(MAX_S, float(target) * 1.15)
    if est < lo:
        errors.append("about %.1f s: under the %g s target (%.1f s at least)" % (est, float(target), lo))
    if est > hi:
        errors.append("about %.1f s: over the %g s target (%.1f s at most)" % (est, float(target), hi))
sections = sum(1 for ln in lines[:-1] if ln.get("break") == "section")
allowed = max(1, int(SECTIONS_PER_75 * est / 75.0 + 1e-9))
if sections > allowed:
    errors.append("%d section breaks: at most %d in a reel this long (3 every 75 s; each is a %.1f s pause); make the "
                  "others sentence breaks" % (sections, allowed, PAUSE["section"]))
voiced = None
if a.voice:
    with wave.open(a.voice) as w:
        voiced = w.getnframes() / float(w.getframerate())
    if voiced > MAX_S + 1e-6:
        need = int((voiced - MAX_S) * rate) + 1
        keep = {lines[0].get("id"), S.get("payoff"), S.get("cta")} if lines else set()
        cands = sorted((ln for ln in lines if ln.get("id") not in keep), key=lambda ln: -len(spoken(ln).split()))
        picked, got = [], 0
        for ln in cands:
            if got >= need:
                break
            picked.append(ln)
            got += len(spoken(ln).split())
        errors.append("voiced %.1f s: over the 90 s ceiling; trim about %d words; lines to trim or shorten: %s"
                      % (voiced, need, ", ".join("%s (%d words)" % (ln.get("id"), len(spoken(ln).split())) for ln in picked)))

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

# ---- plain spoken words (PLAYBOOK §E2.9; the kit's wording.py): fails block E1, the rest is for the writer -----------
notes = []
sys.path.insert(0, HERE)
import explainer_lib as E
if E.kit_dir():
    _w = E.find_kit("wording").check_lines([{"id": ln.get("id"), "text": ln.get("show", ""), "say": ln.get("say")} for ln in lines],
                                           rate=rate)
    errors += _w["fail"]
    warnings += _w["warn"]
    notes += _w["note"]
else:
    warnings.append("the kit's wording check was not found (install the kit next to this skill): the words were not checked")
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

summary = ("%d words, est %.1f s (%.1f words a second for %s at %g, plus %.1f s of pauses), %d lines, %d sources%s"
           % (words, est, rate, voice, speed, pauses, len(lines), len(sources), (", voiced %.1f s" % voiced) if voiced else ""))
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
    if warnings or notes:
        out += ["", "## Worth a look", ""] + ["- " + w for w in warnings + notes]
    if errors:
        out += ["", "## Gate E1: FAIL", ""] + ["- " + e for e in errors]
    with open(a.report, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

for w in warnings:
    print("E1 WARN: " + w)
for n in notes:
    print("E1 NOTE: " + n)
if errors:
    print("E1 FAIL: " + summary)
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("E1 PASS: " + summary)
