#!/usr/bin/env python3
"""new-version.py: start the next version of a reel in a clean folder (SOP S14).

  new-version.py --project videos/<p>

Moves the last version's build (public/, snaps/, output*.mp4, deliver/, QA.md) whole into versions/vN/ and copies
storyboard.json there as a record, so nothing from the old build is mixed into the new one and every version can be
compared later. The script, the voice, the transcript, NOTES.md and STATUS.md stay where they are; storyboard.json
stays too, to be edited for the new version. Prints the version folder it wrote.
"""
import argparse, glob, os, shutil, sys

MOVE = ["public", "snaps", "deliver", "QA.md"]
COPY = ["storyboard.json"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    p = os.path.abspath(a.project)
    if not os.path.isdir(p):
        sys.exit("no project folder at %s" % p)
    found = [m for m in MOVE if os.path.exists(os.path.join(p, m))] + \
            [os.path.basename(f) for f in sorted(glob.glob(os.path.join(p, "output*.mp4")))]
    if not found:
        sys.exit("nothing to move aside in %s: the project has no build yet" % p)
    n = 1
    while os.path.exists(os.path.join(p, "versions", "v%d" % n)):
        n += 1
    dest = os.path.join(p, "versions", "v%d" % n)
    os.makedirs(dest)
    for name in found:
        shutil.move(os.path.join(p, name), os.path.join(dest, name))
    for name in COPY:
        if os.path.exists(os.path.join(p, name)):
            shutil.copy2(os.path.join(p, name), os.path.join(dest, name))
    print("v%d: moved %s into %s; the next build starts clean" % (n, ", ".join(found), dest))


if __name__ == "__main__":
    main()
