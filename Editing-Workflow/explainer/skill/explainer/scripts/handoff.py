#!/usr/bin/env python3
"""handoff.py: the explainer's end point, the editor hand-off. No rendered reel: an editable project the creator
finishes in filmcraft (or Premiere, or Resolve), with every layer on its own track.

  python3 handoff.py --project videos/<p> [--no-render] [--xml-only] [--hf "npx --yes hyperframes@0.8.171"]

It reads what compose already wrote (public/index.html, moments.json, voice.wav, music.wav, sfx.wav), the
transcript and storyboard, and notes.json (the agents' "check this" notes: [{t, name, comment}]), then:
  1. layer-pages.py and render-layers.py (the kit): each layer as a transparent clip in <project>/layers/
     (--no-render: use the clips already there);
  2. writes <project>/edit/: <p>.xml (FCP 7 XML), <p>.fcproj (filmcraft, when filmcraft-cli is installed and not
     --xml-only), captions.srt, HANDOFF.md, media/ (voice, music, sfx, gfx/<layer>.mov).
A re-run moves the old edit/ aside as edit.v<N>/ (the creator may have saved work in it).

Tracks: V1 ground, V2 thread, V3 scenes, V4 transitions (burst sprays, brush bands), V5 brand, V6 captions (styled; off), A1 voice,
A2 music, A3 sfx (scenes that overlap at a handover get a lane above).
Markers: the hook window, each scene on its word with its source, and every note.
"""
import argparse, json, os, re, shutil, subprocess, sys, wave
import explainer_lib as E

VIDEO = (("ground", ("ground",)), ("thread", ("thread",)), ("scenes", ("host",)), ("transitions", ("tx",)), ("brand", ("brand",)),
         ("captions (styled)", ("captions",)))
AUDIO = (("voice", "voice.wav"), ("music", "music.wav"), ("sfx", "sfx.wav"))


def fail(msg):
    print("HANDOFF FAIL: " + msg)
    sys.exit(1)


def wav_seconds(path):
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def word_at(anchor, words):
    m = re.match(r"word:(\d+)", str(anchor or ""))
    return words[int(m.group(1))]["text"] if m and int(m.group(1)) < len(words) else str(anchor or "")


def kit_script(name):
    return os.path.join(E.kit_dir(), name)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--xml-only", action="store_true")
    ap.add_argument("--hf", default="")
    a = ap.parse_args()
    P = os.path.abspath(a.project)
    name = os.path.basename(P.rstrip("/"))
    pub = os.path.join(P, "public")
    index = os.path.join(pub, "index.html")
    if not os.path.isfile(index):
        fail("no composed page at %s (compose first: explainer-compose.py)" % index)
    if not E.kit_dir():
        fail("the kit's youtube-edit scripts were not found (install the kit or set KIT_SCRIPTS)")
    X, H = E.find_kit("nle_xml"), E.find_kit("handoff_lib")
    try:
        with open(index, encoding="utf-8") as f:
            page = f.read()
        D = float(re.search(r'id="stage"[^>]*data-duration="([\d.]+)"', page).group(1))
        m = re.search(r'data-fps="(\d+)"', page)
        fps = float(m.group(1)) if m else 60.0
        moments = H.load(os.path.join(pub, "moments.json"), {}) or {}
        words = (H.load(os.path.join(P, "transcript.json"), {}) or {}).get("words", [])
        board = H.load(os.path.join(P, "storyboard.json"), {}) or {}
        notes = H.load(os.path.join(P, "notes.json"), []) or []
    except (H.HandoffError, AttributeError) as e:
        fail(str(e) if isinstance(e, H.HandoffError) else "%s has no composition root with a duration (compose again)" % index)
    by_id = {s.get("id"): s for s in board.get("scenes", [])}

    # 1. the layer clips
    r = subprocess.run([sys.executable, kit_script("layer-pages.py"), "--index", index], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        fail(r.stdout.strip() or r.stderr.strip())
    layers = H.load(os.path.join(pub, "layers.json"), [])
    work = os.path.join(P, "layers")
    if not a.no_render:
        cmd = [sys.executable, kit_script("render-layers.py"), "--public", pub, "--out", work] + (["--hf", a.hf] if a.hf else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout.rstrip())
        if r.returncode != 0:
            fail("the layer clips did not all render (see above)")
    clip = lambda l: l["name"] + "." + l.get("ext", "mov")
    missing = [l["name"] for l in layers if not os.path.isfile(os.path.join(work, clip(l)))]
    if missing:
        fail("no clip for %s in %s: make them with python3 \"%s\" --public \"%s\" --out \"%s\""
             % (", ".join(missing), work, kit_script("render-layers.py"), pub, work))
    if not os.path.isfile(os.path.join(pub, "voice.wav")):
        fail("no voice.wav in %s (compose first)" % pub)

    # 2. the edit folder: built with the last one kept aside, which comes back if anything fails
    edit = os.path.join(P, "edit")
    try:
        with H.staged(edit) as aside:
            media, gfx = os.path.join(edit, "media"), os.path.join(edit, "media", "gfx")
            os.makedirs(gfx)
            tl = X.Timeline(name, 1080, 1920, fps)
            legend = []
            for k, (tname, kinds) in enumerate(VIDEO, 1):
                lanes = [tl.video_track(tname, enabled=tname != "captions (styled)")]
                here = [l for l in layers if l["kind"] in kinds]
                for l in here:                      # scenes may overlap at a handover: the overlap goes to a lane above
                    H.check_clip(os.path.join(work, clip(l)), l["t_out"] - l["t_in"])
                    dst = H.link_or_copy(os.path.join(work, clip(l)), os.path.join(gfx, clip(l)))
                    H.place(tl, lanes, dst, l["t_in"], l["t_out"], duration=l["t_out"] - l["t_in"], name=l["name"])
                legend.append(("V%d" % k, tname, ", ".join(l["name"] for l in here) or "(empty)"))
            for k, (tname, fn) in enumerate(AUDIO, 1):
                src = os.path.join(pub, fn)
                tr = tl.audio_track(tname)
                if os.path.isfile(src):
                    dst = shutil.copy(src, os.path.join(media, fn))
                    sec = wav_seconds(dst)
                    tr.clip(dst, 0.0, min(sec, D), duration=sec, name=fn)
                legend.append(("A%d" % k, tname, fn if os.path.isfile(src) else "(none)"))
            markers = [(0.0, "Hook", "the promise, whole on screen by 1.0 s")]
            for s in moments.get("scenes", []):
                sc = by_id.get(s["id"], {})
                comment = "on \u201c%s\u201d" % word_at(sc.get("in"), words)
                if sc.get("source"):
                    comment += " \u00b7 source: %s" % sc["source"]
                markers.append((float(s["in"]), "%s \u00b7 %s" % (s["id"], s.get("type", "")), comment))
            markers += [(float(n["t"]), n.get("name", "Note"), n.get("comment", "")) for n in notes]
            for t, mname, c in markers:
                tl.marker(t, mname, c)
            probs = tl.validate()
            if probs:
                raise H.HandoffError("; ".join(probs))
            xml = tl.write(os.path.join(edit, name + ".xml"))
            L = E.L
            with open(os.path.join(edit, "captions.srt"), "w", encoding="utf-8") as f:
                f.write(L.to_srt(L.chunk_words(words)))
            fcproj = None if a.xml_only else H.make_project(xml, os.path.join(edit, "captions.srt"), os.path.join(edit, name + ".fcproj"))
            H.write_handoff_md(os.path.join(edit, "HANDOFF.md"), name, legend, markers, fcproj, "1080x1920, 60 fps, H.264, -14 LUFS", "explainer",
                               "The styled captions (the last track) are switched off: turn them on for the reel's own caption look, or "
                               "use the editable caption track from `captions.srt` instead. Burst transitions are on their own track.")
    except H.HandoffError as e:
        fail(str(e))
    print("HANDOFF PASS: %s (%d video tracks, %d audio, %d markers%s)%s"
          % (edit, len(tl.video), len(AUDIO), len(markers), ", filmcraft project" if fcproj else "",
             ("; the last hand-off is kept as %s" % aside) if aside else ""))

if __name__ == "__main__":
    main()
