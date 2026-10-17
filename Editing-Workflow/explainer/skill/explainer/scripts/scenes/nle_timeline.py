"""nle-timeline: a video editor's timeline on light paper: a ruler with timecodes, one to three tracks (V1, V2, A1) of
coloured clips with their labels, and a playhead that plays along while it holds. On each cut's word the playhead jumps
to the cut, the razor marks it, the cut-out piece lifts away and everything after it on that track ripples left to close
the gap; a cut with no length only splits the clip in two:

  {"type": "nle-timeline",
   "tracks": [{"kind": "video", "clips": [{"label": "Hook", "length": 3}, {"label": "Interview", "length": 8},
                                          {"label": "B-roll", "length": 4}]},
              {"kind": "audio", "clips": [{"label": "Music", "length": 14}]}],
   "cuts": [{"track": 0, "time": 6, "length": 2.5, "at": "word:4"}]}

Times and lengths are in the timeline's seconds, as the clips were first laid out (before any cut). Video tracks are named
V1 (the lowest) up, audio tracks A1 down; `name` replaces a track's name. Timecodes, times, lengths and track names are
UI furniture (DECOR_KEYS). A clip's label sits on its first piece, which must be long enough to show it (the composer
then scales the timeline to fit). Every piece is placed for the width the scene is given (BAKED).
"""
import math
import explainer_lib as E
from scenes import js_obj, need

TYPE = "nle-timeline"
BAKED = True
MAX_SCALE = 1.3
DECOR_KEYS = {"time", "length", "track", "name"}
PAD, RADIUS = 24, 30               # the panel
HEAD_W, LANE_GAP = 84, 14          # the track names' column, and the gap to the lanes
RULER, TC_H, TICK_TOP = 64, 36, 42 # the ruler: timecodes on top, ticks under them (where the playhead's head runs)
TC_SIZE = 30                       # timecodes and track names: JetBrains Mono 500
TRACK_H, TGAP, INSET = 84, 10, 6   # a track, the gap between two, a clip's inset from its track
CLIP_R, JOIN = 12, 4               # a clip's corner; the gap between two clips
L_SIZE, L_H, L_PADX, L_X = 30, 38, 8, 8   # a clip's label: DM Sans 700 on a chip of the clip's colour
WAVE_TOP = 40                      # an audio clip: its label on top, its waveform under it from here
TAIL = 0.08                        # the empty end of the view, where the playhead parks
STEPS = (1, 2, 5, 10, 15, 30, 60, 120, 300)
MAX_TRACKS, MAX_CLIPS, MAX_CUTS = 3, 5, 3

CSS = """
  .nl { width:100%%; border-radius:%dpx; padding:%dpx; opacity:0; }
  .nl-in { position:relative; }
  .nl-name { position:absolute; left:0; width:%dpx; height:%dpx; border-radius:14px; display:flex; align-items:center;
    justify-content:center; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:1; white-space:nowrap; }
  .nl-lanes { position:absolute; top:0; }
  .nl-tc { position:absolute; top:0; height:%dpx; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx;
    white-space:nowrap; }
  .nl-tick { position:absolute; width:2px; border-radius:1px; }
  .nl-lane { position:absolute; left:0; right:0; height:%dpx; border-radius:14px; }
  .nl-piece { position:absolute; height:%dpx; overflow:hidden; }
  .nl-piece svg { position:absolute; left:0; top:0; }
  .nl-label { position:absolute; height:%dpx; padding:0 %dpx; border-radius:8px; font-weight:700; font-size:%dpx; line-height:%dpx;
    white-space:nowrap; }
  .nl-ph { position:absolute; left:-11px; top:%dpx; width:22px; }
  .nl-ph-head { width:22px; height:24px; border-radius:6px 6px 11px 11px; }
  .nl-ph-line { width:4px; margin-left:9px; border-radius:2px; }
  .nl-razor { position:absolute; width:4px; margin-left:-2px; border-radius:2px; opacity:0; }
""" % (RADIUS, PAD, HEAD_W, TRACK_H, TC_SIZE, TC_H, TC_SIZE, TC_H, TRACK_H, TRACK_H - 2 * INSET, L_H, L_PADX, L_SIZE, L_H, TICK_TOP)


def tc(s):
    s = int(round(s))
    return "%d:%02d" % (s // 60, s % 60)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def names(scene):
    tracks = scene["tracks"]
    nv = sum(1 for t in tracks if t.get("kind", "video") == "video")
    out, v, a = [], 0, 0
    for t in tracks:
        if t.get("kind", "video") == "video":
            out.append(t.get("name") or "V%d" % (nv - v))
            v += 1
        else:
            a += 1
            out.append(t.get("name") or "A%d" % a)
    return out


def layout(scene):
    """The timeline in seconds: each track's clips (start, end), the cuts in time order with their clip, and the view."""
    tracks = []
    for t in scene["tracks"]:
        x, clips = 0.0, []
        for c in t["clips"]:
            clips.append((x, x + float(c["length"])))
            x += float(c["length"])
        tracks.append(clips)
    total = max(cl[-1][1] for cl in tracks)
    cuts = []
    for i, c in enumerate(scene.get("cuts") or []):
        tr = int(c.get("track", 0))
        t0 = float(c["time"])
        t1 = t0 + float(c.get("length") or 0)
        k = next((j for j, (a, b) in enumerate(tracks[tr]) if a < t0 < b), None) if 0 <= tr < len(tracks) else None
        cuts.append({"i": i, "track": tr, "from": t0, "to": t1, "clip": k})
    return tracks, cuts, total / (1.0 - TAIL)


def pieces(scene):
    """Each track cut into its pieces: (start, end, clip, the cut that removes it or None), in seconds."""
    tracks, cuts, _ = layout(scene)
    out = []
    for tr, clips in enumerate(tracks):
        ps = []
        for k, (a, b) in enumerate(clips):
            pts = sorted({a, b} | {p for c in cuts if c["track"] == tr and c["clip"] == k for p in (c["from"], c["to"])})
            for s, e in zip(pts, pts[1:]):
                gone = next((c["i"] for c in cuts if c["track"] == tr and c["from"] <= s and e <= c["to"] and c["to"] > c["from"]), None)
                ps.append((s, e, k, gone))
        out.append(ps)
    return out


def _label_need(text):
    return E.text_width(text, L_SIZE) + 2 * L_PADX + L_X + 6


def lane_need(scene):
    """The lane width every clip's first piece needs to show its label, and the clip that needs the most."""
    tracks, _, view = layout(scene)
    best, who = 0.0, None
    for tr, ps in enumerate(pieces(scene)):
        for k, (a, b) in enumerate(tracks[tr]):
            first = next(p for p in ps if p[2] == k)
            w = _label_need(scene["tracks"][tr]["clips"][k]["label"]) * view / (first[1] - first[0])
            if w > best:
                best, who = w, scene["tracks"][tr]["clips"][k]["label"]
    return best, who


def validate(scene):
    errs = need(scene, ["tracks"])
    tracks = scene.get("tracks") or []
    if not 1 <= len(tracks) <= MAX_TRACKS:
        return errs + ["a timeline has 1 to %d tracks (got %d)" % (MAX_TRACKS, len(tracks))]
    for i, t in enumerate(tracks):
        if not isinstance(t, dict) or t.get("kind", "video") not in ("video", "audio"):
            errs.append("track %d: kind is video or audio" % i)
            continue
        clips = t.get("clips") or []
        if not 1 <= len(clips) <= MAX_CLIPS:
            errs.append("track %d has 1 to %d clips (got %d)" % (i, MAX_CLIPS, len(clips)))
        for j, c in enumerate(clips):
            if not isinstance(c, dict) or not str(c.get("label") or "").strip():
                errs.append("track %d clip %d has no label" % (i, j))
            elif not _num(c.get("length")) or c["length"] <= 0:
                errs.append("track %d clip %d needs a length in seconds" % (i, j))
        if t.get("name") is not None and len(str(t["name"])) > 3:
            errs.append("track %d: name is at most 3 characters (V1, A2)" % i)
    if errs:
        return errs
    cuts = scene.get("cuts") or []
    if len(cuts) > MAX_CUTS:
        errs.append("at most %d cuts (got %d)" % (MAX_CUTS, len(cuts)))
    for i, c in enumerate(cuts):
        if not isinstance(c, dict) or c.get("at") is None or not _num(c.get("time")):
            errs.append("cut %d needs time (seconds on the timeline) and at" % i)
        elif c.get("length") is not None and (not _num(c["length"]) or c["length"] < 0):
            errs.append("cut %d: length is the seconds it removes (0 or more)" % i)
        elif not isinstance(c.get("track", 0), int) or not 0 <= c.get("track", 0) < len(tracks):
            errs.append("cut %d: track %r is not one of the %d tracks" % (i, c.get("track"), len(tracks)))
    if errs:
        return errs
    tracks_s, cs, _ = layout(scene)
    for c in cs:
        if c["clip"] is None:
            errs.append("cut %d at %s s is not inside a clip on track %d" % (c["i"], c["from"], c["track"]))
        elif c["to"] > tracks_s[c["track"]][c["clip"]][1] + 1e-9:
            errs.append("cut %d runs past the end of its clip (a cut removes part of one clip)" % c["i"])
    for a in cs:
        for b in cs:
            if a["i"] < b["i"] and a["track"] == b["track"] and a["from"] <= b["to"] and b["from"] <= a["to"]:
                errs.append("cuts %d and %d overlap on track %d" % (a["i"], b["i"], a["track"]))
    if not errs:
        lane, who = lane_need(scene)
        if lane + HEAD_W + LANE_GAP + 2 * PAD > E.L.SAFE["right"] - E.L.SAFE["left"]:
            errs.append("clip %r is too short on the timeline to show its label (or a cut lands too close to its start); "
                        "lengthen it, cut later, or shorten the label" % who)
    return errs


def height(scene, width):
    n = len(scene["tracks"])
    return 2 * PAD + RULER + n * TRACK_H + (n - 1) * TGAP


def min_width(scene):
    return int(math.ceil(lane_need(scene)[0])) + HEAD_W + LANE_GAP + 2 * PAD + 1


def render(scene, ctx, box):
    c, mo = ctx.pc, ctx.tokens["motion"]
    sid = ctx.id
    lw = box[2] - 2 * PAD - HEAD_W - LANE_GAP
    tracks, cuts, view = layout(scene)
    pps = lw / view
    X = lambda s: s * pps
    n = len(tracks)
    lane_top = lambda tr: RULER + tr * (TRACK_H + TGAP)
    inner_h = RULER + n * TRACK_H + (n - 1) * TGAP
    kinds = [t.get("kind", "video") for t in scene["tracks"]]
    vcol = [c["series"][0], c["series"][1], c["series"][3]]       # video tracks: blue, mauve, yellow
    cols, v = [], 0
    for k in kinds:
        if k == "video":
            cols.append(vcol[v % len(vcol)])
            v += 1
        else:
            cols.append(c["series"][2])                           # audio: teal
    html = []

    # ---- the track names and the ruler -------------------------------------------------------------------------
    for tr, nm in enumerate(names(scene)):
        html.append('<div class="nl-name" style="top:%dpx;background:%s;color:%s">%s</div>' % (lane_top(tr), c["chrome"], c["dim"], ctx.esc(nm)))
    tc_w = E.text_width(tc(view), TC_SIZE, "mono500") + 6
    step = next((s for s in STEPS if s * pps >= tc_w + 26), STEPS[-1])
    lanes = []
    s = 0
    while s <= view + 1e-9:
        x = X(s)
        lanes.append('<i class="nl-tick" style="left:%.1fpx;top:%dpx;height:%dpx;background:%s"></i>' % (x - 1, TICK_TOP, RULER - TICK_TOP - 4, c["line"]))
        if x + 6 + tc_w <= lw:
            lanes.append('<span class="nl-tc" style="left:%.1fpx;color:%s">%s</span>' % (x + 6, c["dim"], tc(s)))
        for m in range(1, 5):                                      # minor ticks between
            xm = X(s + step * m / 5.0)
            if xm < lw - 2 and step * pps / 5.0 >= 12:
                lanes.append('<i class="nl-tick" style="left:%.1fpx;top:%dpx;height:%dpx;background:%s"></i>'
                             % (xm - 1, TICK_TOP + 10, RULER - TICK_TOP - 14, c["line"]))
        s += step
    for tr in range(n):
        lanes.append('<div class="nl-lane" style="top:%dpx;background:%s"></div>' % (lane_top(tr), c["track"]))

    # ---- the pieces, and where each one is after every cut -------------------------------------------------------
    order = sorted(cuts, key=lambda cu: ctx.at(scene["cuts"][cu["i"]]["at"]))
    times = {cu["i"]: ctx.item(scene["cuts"][cu["i"]]["at"]) for cu in cuts}
    if [cu["i"] for cu in order] != [cu["i"] for cu in cuts]:
        ctx.fail("the cuts happen in the order they are listed: each one's at after the one before")
    shift_of = {}
    for cu in cuts:
        clip_end = tracks[cu["track"]][cu["clip"]][1]
        ends = abs(cu["to"] - clip_end) < 1e-9
        shift_of[cu["i"]] = X(cu["to"] - cu["from"]) - (2 if ends else JOIN)

    def moved(tr, start, upto):
        """How far left a piece starting at `start` on track `tr` has moved once cuts 0..upto (inclusive) are made."""
        return sum(shift_of[cu["i"]] for cu in cuts if cu["i"] <= upto and cu["track"] == tr and start >= cu["to"] - 1e-9)

    labels, js, segs = [], [], []
    for tr, ps in enumerate(pieces(scene)):
        fill, on = cols[tr]
        clips = tracks[tr]
        for j, (a, b, k, gone) in enumerate(ps):
            ca, cb = clips[k]
            left = X(a) + (JOIN / 2.0 if abs(a - ca) < 1e-9 else 0)
            right = X(b) - (JOIN / 2.0 if abs(b - cb) < 1e-9 else 0)
            rl = CLIP_R if abs(a - ca) < 1e-9 else 0
            rr = CLIP_R if abs(b - cb) < 1e-9 else 0
            pid = "%s-p%d-%d" % (sid, tr, j)
            wave = ""
            if kinds[tr] == "audio":                    # a waveform under the label: bars of a fixed, repeatable pattern
                bars, x = [], 4.0
                hh = TRACK_H - 2 * INSET
                band = hh - WAVE_TOP - 4
                while x < right - left - 4:
                    g = int(round((X(a) + x) / 7.0))
                    amp = 0.25 + 0.75 * abs(math.sin(g * 1.7) * math.cos(g * 0.43))
                    bh = band * amp
                    bars.append('<rect x="%.1f" y="%.1f" width="3" height="%.1f" rx="1.5"/>' % (x, WAVE_TOP + (band - bh) / 2.0, bh))
                    x += 7.0
                wave = '<svg width="%.1f" height="%d" fill="%s">%s</svg>' % (right - left, hh, E.rgba(on, 0.45), "".join(bars))
            html_piece = ('<div class="nl-piece" id="%s" style="left:%.1fpx;top:%dpx;width:%.1fpx;background:%s;border-radius:%dpx %dpx %dpx %dpx">%s</div>'
                          % (pid, left, lane_top(tr) + INSET, right - left, fill, rl, rr, rr, rl, wave))
            segs.append(html_piece)
            lid = None
            if abs(a - ca) < 1e-9:                       # the clip's label rides on its first piece
                lid = "%s-l%d-%d" % (sid, tr, j)
                labels.append('<span class="nl-label" id="%s" style="left:%.1fpx;top:%dpx;background:%s;color:%s">%s</span>'
                              % (lid, left + L_X, lane_top(tr) + (INSET + 2 if kinds[tr] == "audio" else (TRACK_H - L_H) // 2), fill, on,
                                 ctx.esc(scene["tracks"][tr]["clips"][k]["label"])))
            # the ripple: each cut on this track that ends at or before this piece moves it left
            prev = 0.0
            for cu in cuts:
                if cu["track"] != tr or a < cu["to"] - 1e-9 or (gone is not None and cu["i"] >= gone):
                    continue
                now = moved(tr, a, cu["i"])
                t = times[cu["i"]][0]
                for el in filter(None, ("#" + pid, "#" + lid if lid else None)):
                    js.append("tl.fromTo('%s', { x: %.1f }, %s, %.3f);" % (el, -prev, js_obj({"x": round(-now, 1), "duration": 0.5, "ease": "expo.out",
                                                                                                 "immediateRender": False}), t + 0.55))
                prev = now
            if gone is not None:                         # the cut-out piece lifts away
                t = times[gone][0]
                js.append("tl.to('#%s', %s, %.3f);" % (pid, js_obj({"y": -18, "opacity": 0, "duration": 0.3, "ease": mo["exit_ease"]}), t + 0.3))
            # a piece's open edge at a cut rounds off as the clip comes apart
            for cu in cuts:
                if cu["track"] != tr or cu["clip"] != k:
                    continue
                t = times[cu["i"]][0]
                if abs(b - cu["from"]) < 1e-9 and gone is None:
                    js.append("tl.to('#%s', %s, %.3f);" % (pid, js_obj({"borderTopRightRadius": CLIP_R, "borderBottomRightRadius": CLIP_R,
                                                                        "duration": 0.2, "ease": mo["enter_ease"]}), t + 0.3))
                if abs(a - cu["to"]) < 1e-9 and gone is None:
                    js.append("tl.to('#%s', %s, %.3f);" % (pid, js_obj({"borderTopLeftRadius": CLIP_R, "borderBottomLeftRadius": CLIP_R,
                                                                        "duration": 0.2, "ease": mo["enter_ease"]}), t + 0.3))

    # ---- the razor marks and the playhead --------------------------------------------------------------------------
    razors = []
    finals = []
    for tr in range(n):
        last = max(cu["i"] for cu in cuts) if cuts else -1
        kept = [p for p in pieces(scene)[tr] if p[3] is None]
        end = max(X(p[1]) - moved(tr, p[0], last) for p in kept)
        finals.append(end)
    park = min(lw - 6, max(finals) + 18)
    ph = "#%s-ph" % sid
    t_cur, x_cur = ctx.t_in + 0.5, 0.0
    v = pps                                             # it plays at 1x: a second of the ruler each second

    def play(t0, x0, t1, speed):
        """Play from x0 at t0 towards the park until t1; returns where it is at t1 (ambient: playback is the hold)."""
        if t1 - t0 < 0.05 or x0 >= park - 0.5:
            return x0
        x1 = min(park, x0 + speed * (t1 - t0))
        dur = (x1 - x0) / speed
        ctx.ambient("tl.fromTo('%s', { x: %.1f }, %s, %.3f);" % (ph, x0, js_obj({"x": round(x1, 1), "duration": round(dur, 3), "ease": "none",
                                                                                 "immediateRender": False}), t0))
        return x1
    for cu in cuts:
        t, attrs = times[cu["i"]]
        tr = cu["track"]
        x_cut = X(cu["from"]) - moved(tr, cu["from"], cu["i"] - 1)
        x_at = play(t_cur, x_cur, t, v)
        js.append("tl.fromTo('%s', { x: %.1f }, %s, %.3f);" % (ph, x_at, js_obj({"x": round(x_cut, 1), "duration": 0.3, "ease": "expo.out",
                                                                                "immediateRender": False}), t))
        marks = [cu["from"]] + ([cu["to"]] if cu["to"] > cu["from"] else [])
        for m, pt in enumerate(marks):
            rid = "%s-k%d-%d" % (sid, cu["i"], m)
            razors.append('<i class="nl-razor" id="%s"%s style="left:%.1fpx;top:%dpx;height:%dpx;background:%s"></i>'
                          % (rid, attrs if m == 0 else "", X(pt) - moved(tr, pt, cu["i"] - 1), lane_top(tr) - 4, TRACK_H + 8, c["bad"]))
            js.append("tl.fromTo('#%s', { opacity: 0, scaleY: 0.3 }, %s, %.3f);" % (rid, js_obj({"opacity": 1, "scaleY": 1, "duration": 0.15,
                                                                                               "ease": mo["enter_ease"], "immediateRender": False}), t + 0.12))
            js.append("tl.to('#%s', %s, %.3f);" % (rid, js_obj({"opacity": 0, "duration": 0.25, "ease": mo["exit_ease"]}), t + 0.75))
        t_cur, x_cur = t + 1.1, x_cut
    # after the last cut it plays on to the end of the edit and parks in the empty tail, clear of every label
    t_end = ctx.t_out - 0.7
    if x_cur < park - 0.5:
        if t_end - t_cur > 0.3:
            play(t_cur, x_cur, t_end, max(v, (park - x_cur) / (t_end - t_cur)))
        else:
            js.append("tl.to('%s', %s, %.3f);" % (ph, js_obj({"x": round(park, 1), "duration": 0.3, "ease": mo["enter_ease"]}), t_cur))
    head = ('<div class="nl-ph" id="%s-ph"><div class="nl-ph-head" style="background:%s"></div><div class="nl-ph-line" style="height:%dpx;background:%s"></div></div>'
            % (sid, c["ink"], inner_h - TICK_TOP - 24, c["ink"]))
    body = ('<div class="nl-lanes" style="left:%dpx;width:%dpx;height:%dpx">%s%s%s%s%s</div>'
            % (HEAD_W + LANE_GAP, lw, inner_h, "".join(lanes), "".join(segs), head, "".join(razors), "".join(labels)))
    js.insert(0, ctx.enter("#%s-tl" % sid, ctx.t_in, {"y": 40}))
    return ('<div class="nl" id="%s-tl" style="%s"><div class="nl-in" style="height:%dpx">%s%s</div></div>'
            % (sid, ctx.paper_card(), inner_h, "".join(html), body)), js
