#!/usr/bin/env python3
"""reels-handoff.py: the end point of the Reels and long-form teams, the editor hand-off. No rendered video: an
editable project the creator finishes in filmcraft (or Premiere, or Resolve).

  python3 reels-handoff.py --project videos/<p> [--section DIR ...] [--format 9x16|16x9] [--music FILE]
                           [--no-render] [--xml-only] [--hf "npx --yes hyperframes@0.8.171"]

Per section (the project folder itself when no --section; long-form passes its sections in order) it reads
cut-list.json (kept segments in source time), public/index.html (the composed cards, b-roll and sound effects),
transcript.json, notes.json and face-x.json; the project's ingest.json maps source time back to each camera file, so
the footage is the creator's own files cut by word, never re-encoded (a kept segment across two files becomes two
clips). Each card is rendered once as a transparent clip (layer-pages.py, render-layers.py; --no-render: use the clips
already in <section>/layers/).

Writes <project>/edit/: <p>.xml, <p>.fcproj (filmcraft-cli), captions.srt, HANDOFF.md, media/ (b-roll, sound effects,
gfx). Tracks: V1 footage, V2 b-roll, V3 cards, V4 captions (styled; off), A1 footage audio, A2 music, A3 sfx.
Markers: the hook, a chapter at each section's start (16x9), and every note.
"""
import argparse, json, math, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = next((os.path.abspath(k) for k in [os.environ.get("KIT_SCRIPTS", ""), os.path.join(HERE, "..", "..", "youtube-edit", "scripts"),
                                          os.path.join(HERE, "..", "..", "..", "..", "kit", "youtube-edit", "scripts")]
            if k and os.path.exists(os.path.join(k, "nle_xml.py"))), None)
if KIT:
    sys.path.insert(0, KIT)
    import handoff_lib as H
sys.path.insert(0, HERE)


def fail(msg):
    print("HANDOFF FAIL: " + msg)
    sys.exit(1)


def attr(tag, name):
    m = re.search(r'\b%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fps_of(clip):
    num, den = (str(clip.get("fps_exact") or clip.get("fps") or "30").split("/") + ["1"])[:2]
    return float(num) / float(den)


def to_camera(t0, t1, clips):
    """Source time [t0, t1] as [(clip, in, out)] on the camera files, split where one file ends and the next starts."""
    out = []
    for c in clips:
        a, b = c["source_start"], c["source_start"] + c["duration"]
        lo, hi = max(t0, a), min(t1, b)
        if hi - lo > 1e-6:
            out.append((c, lo - a, hi - a))
    return out


def segments(section):
    """[(flat start, source start, source end)]: from cut-map.json (where apply-cut put each segment, snapped to the
    source's frames, as the cards and captions are timed), else from the cut list laid end to end."""
    cm = H.load(os.path.join(section, "cut-map.json"))
    if cm and cm.get("segments"):
        return [(float(g["flat_start"]), float(g["src_start"]), float(g["src_end"])) for g in cm["segments"]]
    out, t = [], 0.0
    for k in H.load(os.path.join(section, "cut-list.json"))["kept"]:
        out.append((t, float(k["start"]), float(k["end"])))
        t += float(k["end"]) - float(k["start"])
    return out


def framing(clip, W, Hh, face):
    """(scale %, centre offset) for a camera clip on the sequence: scaled to cover the frame, and moved so the face (0 to 1
    of the clip's width) sits in the middle, never so far that the frame shows past the clip's edge."""
    ws, hs = clip.get("width"), clip.get("height")
    if not ws or not hs:
        return None, None
    s = max(W / float(ws), Hh / float(hs))
    if face is None:
        return round(100 * s, 4), None
    room = max(0.0, (ws * s - W) / 2.0 / W)
    return round(100 * s, 4), (round(max(-room, min(room, (0.5 - float(face)) * ws * s / W)), 4), 0.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--section", action="append", default=[])
    ap.add_argument("--format", choices=("9x16", "16x9"), default="9x16")
    ap.add_argument("--music", default="")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--xml-only", action="store_true")
    ap.add_argument("--hf", default="")
    a = ap.parse_args()
    if not KIT:
        fail("the kit's youtube-edit scripts were not found (install the kit or set KIT_SCRIPTS)")
    import nle_xml as X
    import reels_lib as L
    P = os.path.abspath(a.project)
    name = os.path.basename(P.rstrip("/"))
    sections = [os.path.abspath(s) for s in a.section] or [P]
    ing = H.load(os.path.join(P, "ingest.json"))
    if not ing or not ing.get("clips"):
        fail("no ingest.json with clips in %s: the hand-off lays the cut on the camera files it lists (run ingest.py)" % P)
    clips = ing["clips"]
    if a.format == "9x16":
        W, Hh, fps, export = 1080, 1920, 60, "1080x1920, 60 fps, H.264, -14 LUFS"
    else:
        W, Hh, fps = int(clips[0].get("width", 3840)), int(clips[0].get("height", 2160)), fps_of(clips[0])
        export = "%dx%d, %s fps, H.264, -14 LUFS" % (W, Hh, ("%.3f" % fps).rstrip("0").rstrip("."))
    for s in sections:
        for need in ("cut-list.json", os.path.join("public", "index.html")):
            if not os.path.isfile(os.path.join(s, need)):
                fail("no %s in %s" % (need, s))

    # the cards as transparent clips, per section
    for s in sections:
        r = subprocess.run([sys.executable, os.path.join(KIT, "layer-pages.py"), "--index", os.path.join(s, "public", "index.html")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            fail(r.stdout.strip() or r.stderr.strip())
        if not a.no_render:
            cmd = [sys.executable, os.path.join(KIT, "render-layers.py"), "--public", os.path.join(s, "public"), "--out", os.path.join(s, "layers")]
            r = subprocess.run(cmd + (["--hf", a.hf] if a.hf else []), capture_output=True, text=True, encoding="utf-8", errors="replace")
            print(r.stdout.rstrip())
            if r.returncode != 0:
                fail("the card clips of %s did not all render (see above)" % os.path.basename(s))
    missing = []
    for s in sections:
        for l in H.load(os.path.join(s, "public", "layers.json"), []):
            if l["kind"] in ("host", "captions", "brand") and not os.path.isfile(os.path.join(s, "layers", l["name"] + "." + l.get("ext", "mov"))):
                missing.append("%s/%s" % (os.path.basename(s), l["name"]))
    if missing:
        fail("no clip for %s: make them with python3 \"%s\" --public <section>/public --out <section>/layers"
             % (", ".join(missing), os.path.join(KIT, "render-layers.py")))

    edit = os.path.join(P, "edit")
    try:
        with H.staged(edit) as aside:
            media = os.path.join(edit, "media")
            for sub in ("gfx", "b-roll", "sfx"):
                os.makedirs(os.path.join(media, sub))
            tl = X.Timeline(name, W, Hh, fps)
            v_foot, v_broll, v_cards, v_caps = (tl.video_track("footage"), tl.video_track("b-roll"), tl.video_track("cards"),
                                                tl.video_track("captions (styled)", enabled=False))
            a_foot, a_music, a_sfx = tl.audio_track("footage audio"), tl.audio_track("music"), tl.audio_track("sfx")
            card_lanes, cap_lanes = [v_cards], [v_caps]
            markers, words, off = [(0.0, "Hook", "the promise: on screen by 0.3 s, whole by 1.0 s")], [], 0.0
            for s in sections:
                sname = os.path.basename(s) if s != P else ""
                tag = (sname + "-") if sname else ""
                if a.format == "16x9":
                    markers.append((off, "Chapter: %s" % (sname or name), ""))
                face = H.load(os.path.join(s, "face-x.json"), {}) or {}
                for i, (flat, s0, s1) in enumerate(segments(s)):
                    t = off + flat
                    for c, i0, i1 in to_camera(s0, s1, clips):
                        scale, pos = framing(c, W, Hh, face.get(str(i)))
                        v_foot.clip(c["path"], t, t + (i1 - i0), src_in=i0, duration=c["duration"], name=c["file"], position=pos, scale=scale)
                        a_foot.clip(c["path"], t, t + (i1 - i0), src_in=i0, duration=c["duration"], name=c["file"])
                        t += i1 - i0
                pub = os.path.join(s, "public")
                with open(os.path.join(pub, "index.html"), encoding="utf-8") as f:
                    page = f.read()
                D = float(re.search(r'id="stage"[^>]*data-duration="([\d.]+)"', page).group(1))
                for tagm in re.findall(r"<video\b[^>]*>", page):
                    if "cutaway-video" not in tagm:
                        continue
                    src = os.path.join(pub, attr(tagm, "src"))
                    dst = shutil.copy(src, os.path.join(media, "b-roll", tag + os.path.basename(src)))
                    t0, dur = float(attr(tagm, "data-start")), float(attr(tagm, "data-duration"))
                    v_broll.clip(dst, off + t0, off + t0 + dur, src_in=float(attr(tagm, "data-media-start") or 0), duration=H.media_seconds(dst))
                for tagm in re.findall(r"<audio\b[^>]*>", page):
                    src = os.path.join(pub, attr(tagm, "src"))
                    if not os.path.isfile(src):
                        continue
                    dst = os.path.join(media, "sfx", tag + os.path.basename(src))
                    if not os.path.exists(dst):
                        shutil.copy(src, dst)
                    t0, dur, vol = float(attr(tagm, "data-start")), float(attr(tagm, "data-duration")), float(attr(tagm, "data-volume") or 1)
                    sec = H.media_seconds(dst) or dur
                    a_sfx.clip(dst, off + t0, off + t0 + min(dur, sec), duration=sec, name=os.path.basename(src),
                               level_db=20 * math.log10(max(vol, 1e-4)))
                for l in H.load(os.path.join(pub, "layers.json"), []):
                    if l["kind"] not in ("host", "captions", "brand"):
                        continue
                    fn = l["name"] + "." + l.get("ext", "mov")
                    dst = H.link_or_copy(os.path.join(s, "layers", fn), os.path.join(media, "gfx", tag + fn))
                    H.place(tl, cap_lanes if l["kind"] == "captions" else card_lanes, dst, off + l["t_in"], off + l["t_out"],
                            duration=l["t_out"] - l["t_in"], name=l["name"])
                for n in H.load(os.path.join(s, "notes.json"), []) or []:
                    markers.append((off + float(n["t"]), n.get("name", "Note"), n.get("comment", "")))
                words += [dict(w, start=w["start"] + off, end=w["end"] + off) for w in (H.load(os.path.join(s, "transcript.json"), {}) or {}).get("words", [])]
                off += D
            if s != P:
                for n in H.load(os.path.join(P, "notes.json"), []) or []:
                    markers.append((float(n["t"]), n.get("name", "Note"), n.get("comment", "")))
            if a.music:
                dst = shutil.copy(a.music, os.path.join(media, os.path.basename(a.music)))
                sec = H.media_seconds(dst) or off
                a_music.clip(dst, 0.0, min(sec, off), duration=sec, level_db=-18)
            for t, mname, c in markers:
                tl.marker(t, mname, c)
            probs = tl.validate()
            if probs:
                fail("; ".join(probs))
            xml = tl.write(os.path.join(edit, name + ".xml"))
            srt = os.path.join(edit, "captions.srt")
            with open(srt, "w", encoding="utf-8") as f:
                f.write(L.to_srt(L.chunk_words(words)) if words else "")
            fcproj = None if a.xml_only else H.make_project(xml, srt, os.path.join(edit, name + ".fcproj"))
            legend = [("V1", "footage", "your camera files, cut by word (%d clips)" % len(v_foot.clips)),
                      ("V2", "b-roll", "%d cutaways" % len(v_broll.clips)),
                      ("V3", "cards", "%d cards, each a transparent clip%s" % (sum(len(t.clips) for t in card_lanes),
                                                                               " (overlaps on the lanes above)" if len(card_lanes) > 1 else "")),
                      ("V4", "captions (styled)", "the reel's own caption look (off)"), ("A1", "footage audio", "the camera sound"),
                      ("A2", "music", os.path.basename(a.music) if a.music else "(none: add yours)"), ("A3", "sfx", "%d sound effects" % len(a_sfx.clips))]
            H.write_handoff_md(os.path.join(edit, "HANDOFF.md"), name, legend, markers, fcproj, export, "longform" if a.format == "16x9" else "reels",
                               "The styled captions (V4) are switched off: turn them on for the reel's caption look, or use the editable caption "
                               "track from `captions.srt` instead.")
    except H.HandoffError as e:
        fail(str(e))
    print("HANDOFF PASS: %s (%d footage clips, %d cards, %d markers%s)%s"
          % (edit, len(v_foot.clips), sum(len(t.clips) for t in card_lanes), len(markers), ", filmcraft project" if fcproj else "",
             ("; the last hand-off is kept as %s" % aside) if aside else ""))


if __name__ == "__main__":
    main()
