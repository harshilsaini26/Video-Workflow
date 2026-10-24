#!/usr/bin/env python3
"""wf.py: one entry point for every profile (kit, longform, reels, explainer). It only calls what already exists.

  python3 Editing-Workflow/wf.py install <profile> [--to .]        the README's copy steps (kit first for any team)
  python3 Editing-Workflow/wf.py test [profile]                    each suite's own unittest command
  python3 Editing-Workflow/wf.py doctor                            the machine check (preflight.py)
  python3 Editing-Workflow/wf.py gates <project> --profile P --stage S   a stage's gate scripts, in order
  python3 Editing-Workflow/wf.py handoff <project> --profile P [-- extra args]   the editor hand-off (the default end)
  python3 Editing-Workflow/wf.py render <project> --profile P      the full render: opt-in, only when the creator asks
  any command: --dry-run prints the commands instead of running them

Run it from the folder you run Claude Code in (the one holding .claude/ and Editing-Workflow/). The scripts are taken
from the installed skills (.claude/skills/...) when present, else from this repository.
The one-command shape is borrowed from Anil-matcha/AI-Youtube-Shorts-Generator (MIT).
"""
import argparse, json, glob, os, shlex, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PROFILES = ("kit", "longform", "reels", "explainer")
INSTALL = {
    "kit": [("mkdir", ".claude/skills"), ("tree", "Editing-Workflow/kit/youtube-edit", ".claude/skills/")],
    "longform": [("mkdir", ".claude/skills .claude/agents"), ("tree", "Editing-Workflow/longform/skill/youtube-longform", ".claude/skills/"),
                 ("templates", "youtube-longform"), ("glob", "Editing-Workflow/longform/agents/longform-*.md", ".claude/agents/")],
    "reels": [("mkdir", ".claude/skills .claude/agents"), ("tree", "Editing-Workflow/reels/skill/reels", ".claude/skills/"),
              ("templates", "reels"), ("glob", "Editing-Workflow/reels/agents/reels-*.md", ".claude/agents/")],
    "explainer": [("mkdir", ".claude/skills .claude/agents"), ("tree", "Editing-Workflow/explainer/skill/explainer", ".claude/skills/"),
                  ("templates", "explainer"), ("glob", "Editing-Workflow/explainer/agents/explainer-*.md", ".claude/agents/")],
}
SUITES = {"kit": "kit/youtube-edit/scripts", "reels": "reels/skill/reels/scripts", "explainer": "explainer/skill/explainer/scripts"}
INSTALLED = {"kit": ".claude/skills/youtube-edit/scripts", "reels": ".claude/skills/reels/scripts", "explainer": ".claude/skills/explainer/scripts"}


def fail(msg):
    print("wf: " + msg)
    sys.exit(2)


def scripts(suite):
    """An installed skill's scripts folder when present, else the repository's (relative paths, as printed)."""
    return INSTALLED[suite] if os.path.isdir(INSTALLED[suite]) else os.path.join("Editing-Workflow", SUITES[suite])


def show(steps):
    out = []
    for s in steps:
        if s[0] == "mkdir":
            out.append("mkdir -p " + s[1])
        elif s[0] == "tree":
            out.append("cp -R %s %s" % (s[1], s[2]))
        elif s[0] == "templates":
            out.append("mkdir -p .claude/skills/%s/templates && cp -R Editing-Workflow/templates/. .claude/skills/%s/templates/" % (s[1], s[1]))
        elif s[0] == "glob":
            out.append("cp %s %s" % (s[1], s[2]))
    return out


def install(profile, to, dry):
    steps = INSTALL[profile]
    if dry:
        print("\n".join(show(steps)))
        return 0
    j = lambda p: os.path.join(to, p)
    for s in steps:
        if s[0] == "mkdir":
            for d in s[1].split():
                os.makedirs(j(d), exist_ok=True)
        elif s[0] == "tree":
            shutil.copytree(j(s[1]), j(os.path.join(s[2], os.path.basename(s[1]))), dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
        elif s[0] == "templates":
            shutil.copytree(j("Editing-Workflow/templates"), j(".claude/skills/%s/templates" % s[1]), dirs_exist_ok=True)
        elif s[0] == "glob":
            for f in glob.glob(j(s[1])):
                shutil.copy(f, j(s[2]))
    print("\n".join(show(steps)))
    print("wf: installed %s in %s" % (profile, os.path.abspath(to)))
    return 0


def run(cmds, dry, cwd=None):
    code = 0
    for c in cmds:
        print(("(in %s) " % cwd if cwd else "") + " ".join(shlex.quote(x) if " " in x else x for x in c))
        if not dry:
            r = subprocess.run(c, cwd=cwd)
            code = code or r.returncode
    return code


def gates(p, profile, stage):
    py = "python3"
    ex, kit = scripts("explainer"), scripts("kit")
    table = {
        ("explainer", "E1"): [[py, ex + "/script-check.py", "--script", p + "/script.json", "--report", p + "/SCRIPT.md"]],
        ("explainer", "E4"): [[py, ex + "/pace-check.py", "--index", p + "/public/index.html"]],
        ("explainer", "E5"): [[py, ex + "/layout-check.py", "--index", p + "/public/index.html"]],
        ("explainer", "H1"): [[py, kit + "/handoff-check.py", "--edit", p + "/edit", "--profile", "explainer", "--transcript", p + "/transcript.json",
                               "--storyboard", p + "/storyboard.json"]],
        ("reels", "wording"): [[py, kit + "/wording.py", "--transcript", p + "/transcript-raw.json", "--kept", p + "/cut-list.json"]],
        ("longform", "wording"): [[py, kit + "/wording.py", "--transcript", p + "/transcript-raw.json", "--kept", p + "/cut-list.json"]],
        ("reels", "H1"): [[py, kit + "/handoff-check.py", "--edit", p + "/edit", "--profile", "reels"]],
        ("longform", "H1"): [[py, kit + "/handoff-check.py", "--edit", p + "/edit", "--profile", "longform"]],
    }
    for prof in ("explainer", "reels"):
        table[(prof, "post")] = [[py, kit + "/post-check.py", "--post", p + "/deliver/POST.md", "--script", p + "/script.json"]]
    if (profile, stage) not in table:
        fail("no stage %r for %s; stages: %s" % (stage, profile, ", ".join(sorted(s for pr, s in table if pr == profile))))
    return table[(profile, stage)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", choices=("install", "test", "doctor", "gates", "handoff", "render"))
    ap.add_argument("target", nargs="?", default="")
    ap.add_argument("--profile", default="")
    ap.add_argument("--stage", default="")
    ap.add_argument("--to", default=".")
    ap.add_argument("--dry-run", action="store_true")
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    a = ap.parse_args(argv[:argv.index("--")] if "--" in argv else argv)
    if a.command == "install":
        if a.target not in PROFILES:
            fail("no profile %r; the profiles are %s" % (a.target, ", ".join(PROFILES)))
        return install(a.target, a.to, a.dry_run)
    if a.command == "test":
        which = [a.target] if a.target else list(SUITES)
        bad = [w for w in which if w not in SUITES]
        if bad:
            fail("no suite %r; the suites are %s" % (bad[0], ", ".join(SUITES)))
        code = 0
        for w in which:
            code = run([["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."]], a.dry_run, cwd=scripts(w)) or code
        return code
    if a.command == "doctor":
        return run([["python3", scripts("explainer") + "/preflight.py"]], a.dry_run)
    if a.profile not in ("explainer", "reels", "longform"):
        fail("give --profile explainer, reels or longform (got %r)" % a.profile)
    if not a.target:
        fail("give the project folder, e.g. videos/my-reel")
    p = a.target.rstrip("/")
    if a.command == "gates":
        return run(gates(p, a.profile, a.stage), a.dry_run)
    if a.command == "handoff":
        if a.profile == "explainer":
            cmd = ["python3", scripts("explainer") + "/handoff.py", "--project", p]
        else:
            cmd = ["python3", scripts("reels") + "/reels-handoff.py", "--project", p] + (["--format", "16x9"] if a.profile == "longform" else [])
            sj = os.path.join(p, "sections.json")
            if a.profile == "longform" and "--section" not in extra and os.path.isfile(sj):   # every section, in order
                with open(sj, encoding="utf-8") as f:
                    for sec in json.load(f):
                        cmd += ["--section", "%s/%s" % (p, sec["part"])]
        return run([cmd + extra], a.dry_run)
    if a.command == "render":
        print("wf: the full render is opt-in: the default end is the editor hand-off (wf.py handoff). Rendering because you asked.")
        if a.profile == "longform":
            fail("long-form renders per section through its Renderer agent (longform-renderer); ask the Producer for it")
        hf = os.environ.get("HYPERFRAMES_CMD", "npx --no-install hyperframes")
        return run([shlex.split(hf) + ["render", p + "/public", "--resolution", "portrait", "--fps", "60", "--video-bitrate", "20M"] + extra], a.dry_run)


if __name__ == "__main__":
    sys.exit(main() or 0)
