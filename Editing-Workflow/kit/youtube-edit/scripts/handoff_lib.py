#!/usr/bin/env python3
"""handoff_lib.py: what every profile's editor hand-off shares (explainer handoff.py, reels-handoff.py for reels and
long-form): keeping the last edit/ aside, the filmcraft project, HANDOFF.md."""
import contextlib, filecmp, json, os, shutil, subprocess

import filmcraft


class HandoffError(Exception):
    pass


def load(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except ValueError as e:
            raise HandoffError("%s is not valid JSON (%s)" % (path, e))


def set_aside(edit):
    """Move an existing edit/ to edit.v<N>/ (the creator may have saved work in it); returns the new name or None."""
    if not os.path.isdir(edit):
        return None
    n = 1
    while os.path.exists("%s.v%d" % (edit, n)):
        n += 1
    shutil.move(edit, "%s.v%d" % (edit, n))
    return "%s.v%d" % (edit, n)


@contextlib.contextmanager
def staged(edit):
    """Build a new edit/ with the last one kept aside (edit.v<N>); if anything fails, the half-built folder goes and the
    last edit/ comes back exactly as it was. Yields the aside path (or None)."""
    aside = set_aside(edit)
    try:
        yield aside
    except BaseException as e:            # a failure, or a script's own sys.exit: the last edit/ comes back either way
        shutil.rmtree(edit, True)
        if aside:
            shutil.move(aside, edit)
        if isinstance(e, (SystemExit, KeyboardInterrupt)):
            raise
        raise HandoffError(str(e) if isinstance(e, HandoffError) else "%s: %s" % (type(e).__name__, e))


def place(tl, lanes, path, start, end, **kw):
    """Put a clip on the first lane where it does not overlap (cards and scenes may overlap at a handover); a new lane
    ("<name> 2", ...) is added above when none is free."""
    f = tl.frames
    for tr in lanes:
        if all(f(end) <= f(c["start"]) or f(start) >= f(c["end"]) for c in tr.clips):
            return tr.clip(path, start, end, **kw)
    tr = tl.video_track("%s %d" % (lanes[0].name, len(lanes) + 1), enabled=lanes[0].enabled)
    lanes.append(tr)
    return tr.clip(path, start, end, **kw)


def link_or_copy(src, dst):
    """The same file in two places without twice the disk: a hard link, else a copy."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy(src, dst)
    return dst


def free_name(dst, src):
    """dst, or dst with -2, -3... before its extension when another file already holds that name; the same file again
    reuses its copy."""
    base, ext = os.path.splitext(dst)
    n, cand = 1, dst
    while os.path.exists(cand) and not filecmp.cmp(cand, src, shallow=False):
        n += 1
        cand = "%s-%d%s" % (base, n, ext)
    return cand


def check_clip(path, need):
    """A rendered layer clip must last its slot: one left over from an earlier build (--no-render) may be shorter."""
    sec = media_seconds(path)
    if sec is not None and sec < need - 0.05:
        raise HandoffError("%s lasts %.2f s but its slot is %.2f s: it is from an earlier build; render the clips again "
                           "(run without --no-render)" % (os.path.basename(path), sec, need))


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

%s The clips it uses are in `media/`%s; the
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
- then, if you like, check your export: `python3 "%s" --video <your export> --profile %s`.
""" % (name, opened, "" if profile == "explainer" else " (your camera files stay where they are, never copied or re-encoded)",
       rows, off_note, marks, export, os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa-export.py"), profile))
    return path
