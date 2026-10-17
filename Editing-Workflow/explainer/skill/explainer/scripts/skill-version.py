#!/usr/bin/env python3
"""skill-version.py: the skill's version, pinned in STATUS.md and checked at each stage (SOP S11, S12).

  skill-version.py                      print the version (a hash of the skill's scripts, docs and tokens)
  skill-version.py --pin STATUS.md      write it into STATUS.md's header table ("| Skill | <hash> |")
  skill-version.py --check STATUS.md    exit 1, naming the changed files, when the skill differs from the pin

The RAG reel's skill was updated mid-session and silently undid a composer fix, and makers edited shared scripts in
.claude/ where nothing is versioned. A pin makes both visible: the Producer pins at ingest and checks before each stage;
a change is the creator's call (keep the pin, or re-pin and say so in STATUS.md). The hash covers every file but tests,
caches, the vendor folder and what the tools write themselves (voice-rates.json); a manifest beside STATUS.md (.skill-manifest.json) names what changed.
"""
import argparse, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKIP_DIRS = {"__pycache__", "tests", "vendor", ".git"}
SKIP_FILES = {"voice-rates.json", ".DS_Store", "Thumbs.db"}   # written by the skill's own tools or the OS, not changes to it


def manifest(root=ROOT):
    out = {}
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if f.endswith((".pyc", ".log")) or f in SKIP_FILES:
                continue
            path = os.path.join(d, f)
            with open(path, "rb") as fh:
                out[os.path.relpath(path, root).replace(os.sep, "/")] = hashlib.sha256(fh.read()).hexdigest()
    return out


def version(m):
    return hashlib.sha256(json.dumps(m, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pin")
    ap.add_argument("--check")
    a = ap.parse_args()
    m = manifest()
    v = version(m)
    if a.pin:
        with open(a.pin, encoding="utf-8") as f:
            text = f.read()
        row = "| Skill | %s |" % v
        text = re.sub(r"^\| Skill \| [^|]* \|$", row, text, flags=re.M) if re.search(r"^\| Skill \|", text, re.M) \
            else re.sub(r"(\n\|[^\n]*\|\n\|[-| ]+\|\n)", r"\1" + row + "\n", text, count=1)
        if row not in text:
            text += "\n" + row + "\n"
        with open(a.pin, "w", encoding="utf-8") as f:
            f.write(text)
        with open(os.path.join(os.path.dirname(os.path.abspath(a.pin)), ".skill-manifest.json"), "w", encoding="utf-8") as f:
            json.dump({"version": v, "files": m}, f, indent=1)
        print("pinned skill %s in %s" % (v, a.pin))
    elif a.check:
        with open(a.check, encoding="utf-8") as f:
            pin = re.search(r"^\| Skill \| ([0-9a-f]+) \|$", f.read(), re.M)
        if not pin:
            print("SKILL FAIL: %s has no Skill row: pin it with skill-version.py --pin" % a.check)
            sys.exit(1)
        if pin.group(1) == v:
            print("SKILL OK: %s, as pinned" % v)
            return
        old = {}
        mp = os.path.join(os.path.dirname(os.path.abspath(a.check)), ".skill-manifest.json")
        if os.path.exists(mp):
            with open(mp, encoding="utf-8") as f:
                old = json.load(f).get("files", {})
        changed = sorted(k for k in set(m) | set(old) if m.get(k) != old.get(k))
        print("SKILL FAIL: the skill is %s, pinned %s: it changed since the pin (an update, or an edit by a maker): %s. "
              "Tell the creator; keep working only once they choose to re-pin" % (v, pin.group(1), ", ".join(changed) or "see the diff"))
        sys.exit(1)
    else:
        print(v)


if __name__ == "__main__":
    main()
