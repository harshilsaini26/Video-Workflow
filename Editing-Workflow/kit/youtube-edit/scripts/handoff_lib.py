#!/usr/bin/env python3
"""handoff_lib.py: what every profile's editor hand-off shares (explainer handoff.py, reels-handoff.py for reels and
long-form): keeping the last edit/ aside, the filmcraft project, HANDOFF.md."""
import json, os, shutil, subprocess

import filmcraft


class HandoffError(Exception):
    pass


def load(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def set_aside(edit):
    """Move an existing edit/ to edit.v<N>/ (the creator may have saved work in it); returns the new name or None."""
    if not os.path.isdir(edit):
        return None
    n = 1
    while os.path.exists("%s.v%d" % (edit, n)):
        n += 1
    shutil.move(edit, "%s.v%d" % (edit, n))
    return "%s.v%d" % (edit, n)


def media_seconds(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def make_project(xml, srt, out_fcproj):
    """The filmcraft project next to the XML when filmcraft-cli is installed; returns its path or None."""
    if not filmcraft.find_cli():
        return None
    try:
        res = filmcraft.to_project(xml, srt if srt and os.path.isfile(srt) else None, out_fcproj)
    except filmcraft.FilmcraftError as e:
        raise HandoffError(str(e))
    if res["offlineMedia"]:
        raise HandoffError("filmcraft could not find %s" % ", ".join(str(m) for m in res["offlineMedia"]))
    return out_fcproj


def write_handoff_md(path, name, tracks, markers, fcproj, export, profile, off_note):
    rows = "\n".join("| %s | %s | %s |" % (k, n, what) for k, n, what in tracks)
    marks = "\n".join("- **%s** at %.2f s: %s" % (m[1], m[0], m[2] or "") for m in markers)
    opened = ("Open `%s.fcproj` in filmcraft." % name) if fcproj else (
        "In filmcraft: File > Import > `%s.xml` (Premiere and Resolve: File > Import the same file)." % name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("""# %s: the edit

%s The clips it uses are in `media/` (your camera files stay where they are, never copied or re-encoded); the
captions are `captions.srt` (filmcraft: Captions > Import Captions). If you move this folder, filmcraft finds the
media again with File > Link Media.

## Tracks

| Track | Name | What is on it |
|---|---|---|
%s

%s

## Markers

%s

## What is left to you

- the edit itself: trims, pacing, anything you want to move, swap or drop;
- the final mix and the export (%s);
- then, if you like, check your export: `python3 qa-export.py --video <your export> --profile %s`.
""" % (name, opened, rows, off_note, marks, export, profile))
    return path
