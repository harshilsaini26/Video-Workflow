#!/usr/bin/env python3
"""nle_xml.py: the editor hand-off's timeline as Final Cut Pro 7 XML (xmeml version 4), which filmcraft, Premiere Pro
and DaVinci Resolve import natively (File > Import). Standard library only.

  tl = Timeline("my-reel", 1080, 1920, 60)            # 29.97 / 59.94: timebase 30 / 60 with ntsc TRUE
  v1 = tl.video_track("scenes"); a1 = tl.audio_track("voice")
  v1.clip("/abs/media/gfx/l0.mov", start=0.0, end=2.8, duration=2.8)
  a1.clip("/abs/media/voice.wav", 0.0, 32.5, duration=32.5, level_db=0)
  tl.marker(0.0, "Hook", "whole by 1.0 s")
  problems = tl.validate(); tl.write("edit/my-reel.xml")
  parse("edit/my-reel.xml")                           # back to a dict (tests, handoff-check)

Times are seconds in, frames out. A clip's source in/out are its frames in the source file; media is referenced by an
absolute file:// URL, never copied.
"""
import os, re, urllib.parse
import xml.etree.ElementTree as ET

NTSC = {29.97: (30, 30000 / 1001.0), 59.94: (60, 60000 / 1001.0), 23.976: (24, 24000 / 1001.0)}


def to_pathurl(path):
    """file:///... with every unsafe character percent-encoded (UTF-8); a Windows path keeps its drive letter."""
    p = str(path)
    if not (re.match(r"^[A-Za-z]:[\\/]", p) or p.startswith("\\\\")):
        p = os.path.abspath(p)                   # on Windows this gives C:\\..., handled below
    if p.startswith("\\\\"):                       # UNC: \\server\share\x -> file://server/share/x
        return "file://" + urllib.parse.quote(p[2:].replace("\\", "/"), safe="/:")
    if re.match(r"^[A-Za-z]:[\\/]", p):
        p = "/" + p.replace("\\", "/")
    return "file://" + urllib.parse.quote(p, safe="/:")


class Track:
    def __init__(self, tl, kind, name, enabled):
        self.tl, self.kind, self.name, self.enabled, self.clips = tl, kind, name, enabled, []

    def clip(self, path, start, end, src_in=0.0, name=None, duration=None, opacity=None, level_db=None, position=None, scale=None):
        self.clips.append({"path": str(path), "start": float(start), "end": float(end), "src_in": float(src_in),
                           "name": name or os.path.basename(str(path)), "duration": duration, "opacity": opacity,
                           "level_db": level_db, "position": position, "scale": scale})
        return self


class Timeline:
    def __init__(self, name, width, height, fps):
        self.name, self.width, self.height = name, int(width), int(height)
        key = round(float(fps), 3)
        if key in NTSC:
            self.timebase, self.fps_exact, self.ntsc = NTSC[key][0], NTSC[key][1], True
        else:
            self.timebase, self.fps_exact, self.ntsc = int(round(float(fps))), float(round(float(fps))), False
        self.video, self.audio, self.markers = [], [], []

    def frames(self, t):
        return int(round(float(t) * self.fps_exact))

    def video_track(self, name, enabled=True):
        self.video.append(Track(self, "video", name, enabled))
        return self.video[-1]

    def audio_track(self, name, enabled=True):
        self.audio.append(Track(self, "audio", name, enabled))
        return self.audio[-1]

    def marker(self, t, name, comment=""):
        self.markers.append((float(t), name, comment))

    def duration(self):
        ends = [c["end"] for tr in self.video + self.audio for c in tr.clips]
        return max(ends) if ends else 0.0

    def validate(self):
        probs = []
        for tr in self.video + self.audio:
            prev = None
            for c in sorted(tr.clips, key=lambda c: c["start"]):
                where = "%s on %s" % (c["name"], tr.name)
                if not os.path.exists(c["path"]):
                    probs.append("%s: no file at %s" % (where, c["path"]))
                if c["end"] <= c["start"]:
                    probs.append("%s: ends before it starts" % where)
                if c["duration"] is not None:
                    out = self.frames(c["src_in"]) + self.frames(c["end"]) - self.frames(c["start"])
                    if out > self.frames(c["duration"]):
                        probs.append("%s: runs %d frames past the end of its source" % (where, out - self.frames(c["duration"])))
                if prev and self.frames(c["start"]) < self.frames(prev["end"]):
                    probs.append("%s: overlaps %s" % (where, prev["name"]))
                prev = c
        return probs

    # ---- writing ----------------------------------------------------------------------------------------------------
    def _rate(self, parent):
        r = ET.SubElement(parent, "rate")
        ET.SubElement(r, "timebase").text = str(self.timebase)
        ET.SubElement(r, "ntsc").text = "TRUE" if self.ntsc else "FALSE"

    def _file(self, parent, c, ids, kind):
        url = to_pathurl(c["path"])
        if url in ids:
            ET.SubElement(parent, "file", id=ids[url])
            return
        ids[url] = "file-%d" % (len(ids) + 1)
        f = ET.SubElement(parent, "file", id=ids[url])
        ET.SubElement(f, "name").text = os.path.basename(c["path"])
        ET.SubElement(f, "pathurl").text = url
        self._rate(f)
        if c["duration"] is not None:
            ET.SubElement(f, "duration").text = str(self.frames(c["duration"]))
        m = ET.SubElement(f, "media")
        if kind == "video":
            sc = ET.SubElement(ET.SubElement(m, "video"), "samplecharacteristics")
            ET.SubElement(sc, "width").text = str(self.width)
            ET.SubElement(sc, "height").text = str(self.height)
        else:
            ET.SubElement(ET.SubElement(m, "audio"), "channelcount").text = "2"

    def _clipitem(self, track_el, c, n, ids, kind):
        ci = ET.SubElement(track_el, "clipitem", id="clipitem-%d" % n)
        ET.SubElement(ci, "name").text = c["name"]
        ET.SubElement(ci, "enabled").text = "TRUE"
        if c["duration"] is not None:
            ET.SubElement(ci, "duration").text = str(self.frames(c["duration"]))
        self._rate(ci)
        s, e, i = self.frames(c["start"]), self.frames(c["end"]), self.frames(c["src_in"])
        for tag, v in (("start", s), ("end", e), ("in", i), ("out", i + e - s)):
            ET.SubElement(ci, tag).text = str(v)
        self._file(ci, c, ids, kind)
        motion = ([("scale", "Scale", float(c["scale"]))] if c.get("scale") is not None else []) + \
                 ([("center", "Center", c["position"])] if c["position"] is not None else [])
        if motion:
            self._filter(ci, "Basic Motion", "basic", "motion", motion)
        if c["opacity"] is not None:
            self._filter(ci, "Opacity", "opacity", "motion", [("opacity", "opacity", 100.0 * c["opacity"])])
        if c["level_db"] is not None:
            self._filter(ci, "Audio Levels", "audiolevels", "audiolevels", [("level", "Level", 10 ** (c["level_db"] / 20.0))])

    def _filter(self, ci, name, eid, cat, params):
        eff = ET.SubElement(ET.SubElement(ci, "filter"), "effect")
        ET.SubElement(eff, "name").text = name
        ET.SubElement(eff, "effectid").text = eid
        ET.SubElement(eff, "effectcategory").text = cat
        ET.SubElement(eff, "effecttype").text = "motion" if cat == "motion" else "audiolevels"
        ET.SubElement(eff, "mediatype").text = "video" if cat == "motion" else "audio"
        for pid, pname, val in params:
            p = ET.SubElement(eff, "parameter")
            ET.SubElement(p, "parameterid").text = pid
            ET.SubElement(p, "name").text = pname
            v = ET.SubElement(p, "value")
            if isinstance(val, tuple):
                ET.SubElement(v, "horiz").text = "%.4f" % val[0]
                ET.SubElement(v, "vert").text = "%.4f" % val[1]
            else:
                v.text = "%.4f" % val

    def write(self, path):
        root = ET.Element("xmeml", version="4")
        seq = ET.SubElement(root, "sequence", id="sequence-1")
        ET.SubElement(seq, "name").text = self.name
        ET.SubElement(seq, "duration").text = str(self.frames(self.duration()))
        self._rate(seq)
        media = ET.SubElement(seq, "media")
        video = ET.SubElement(media, "video")
        sc = ET.SubElement(ET.SubElement(video, "format"), "samplecharacteristics")
        self._rate(sc)
        ET.SubElement(sc, "width").text = str(self.width)
        ET.SubElement(sc, "height").text = str(self.height)
        audio = ET.SubElement(media, "audio")
        ids, n = {}, 0
        for parent, tracks, kind in ((video, self.video, "video"), (audio, self.audio, "audio")):
            for tr in tracks:
                tel = ET.SubElement(parent, "track")
                for c in sorted(tr.clips, key=lambda c: c["start"]):
                    n += 1
                    self._clipitem(tel, c, n, ids, kind)
                ET.SubElement(tel, "enabled").text = "TRUE" if tr.enabled else "FALSE"
                ET.SubElement(tel, "name").text = tr.name
        for t, name, comment in self.markers:
            m = ET.SubElement(seq, "marker")
            ET.SubElement(m, "name").text = name
            ET.SubElement(m, "comment").text = comment
            ET.SubElement(m, "in").text = str(self.frames(t))
            ET.SubElement(m, "out").text = "-1"
        ET.indent(root, "  ")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n')
            f.write(ET.tostring(root, encoding="unicode"))
            f.write("\n")
        return path


def parse(path):
    """The sequence back as a dict: {name, width, height, timebase, ntsc, duration, video:[{name, enabled, clips}], audio, markers}."""
    root = ET.parse(path).getroot()
    seq = root.find("sequence")
    sc = seq.find("media/video/format/samplecharacteristics")
    urls = {}
    for f in root.iter("file"):
        if f.find("pathurl") is not None:
            urls[f.get("id")] = f.findtext("pathurl")
    integer = lambda el, tag: int(el.findtext(tag))

    def tracks(kind):
        out = []
        for t in seq.findall("media/%s/track" % kind):
            clips = []
            for ci in t.findall("clipitem"):
                f = ci.find("file")
                clips.append({"name": ci.findtext("name"), "start": integer(ci, "start"), "end": integer(ci, "end"),
                              "in": integer(ci, "in"), "out": integer(ci, "out"), "pathurl": urls.get(f.get("id")) if f is not None else None,
                              "duration": int(ci.findtext("duration")) if ci.find("duration") is not None else None,
                              "effects": [e.findtext("effectid") for e in ci.findall("filter/effect")]})
            out.append({"name": t.findtext("name"), "enabled": t.findtext("enabled") != "FALSE", "clips": clips})
        return out
    return {"name": seq.findtext("name"), "width": int(sc.findtext("width")), "height": int(sc.findtext("height")),
            "timebase": int(seq.findtext("rate/timebase")), "ntsc": seq.findtext("rate/ntsc") == "TRUE",
            "duration": int(seq.findtext("duration")), "video": tracks("video"), "audio": tracks("audio"),
            "markers": [{"frame": integer(m, "in"), "name": m.findtext("name"), "comment": m.findtext("comment") or ""}
                        for m in seq.findall("marker")]}


def path_from_url(url):
    """The local path a pathurl points at (file:///C:/x for a Windows path)."""
    p = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    return p[1:] if re.match(r"^/[A-Za-z]:/", p) else p
