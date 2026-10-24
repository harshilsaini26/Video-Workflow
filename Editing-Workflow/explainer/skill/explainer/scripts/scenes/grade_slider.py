"""grade-slider: a picture on a light paper panel with one to three grading sliders under it, like a photo editor's.
On each slider's word its label lights up, its knob runs from `from` to `to` (on a -100 to 100 scale, the readout
counting with it) and the picture's grade follows: contrast, saturation and exposure as CSS filters, temperature as a
warm (peach) or cool (blue) soft-light tint. For "it's the contrast that does it", "pull the saturation down":

  {"type": "grade-slider", "src": "shot.jpg",
   "sliders": [{"kind": "contrast", "from": 0, "to": 40, "at": "word:6"},
               {"kind": "temperature", "label": "Warmth", "from": 0, "to": 55, "at": "word:9"}]}

`src` (a PNG or JPG next to storyboard.json) is optional: without it the panel shows a built-in landscape. The slider
values are the mock-up's furniture (DECOR_KEYS), not claims.
"""
import math
import explainer_lib as E
from scenes import js_obj, line_px, need, stagger_for, widest, is_num
from scenes import _vg

TYPE = "grade-slider"
DECOR_KEYS = {"from", "to"}
KINDS = {"contrast": "Contrast", "saturation": "Saturation", "exposure": "Exposure", "temperature": "Temperature"}
PIC_H = {1: 380, 2: 360, 3: 330}         # the picture, by slider count (fewer sliders, a taller picture)
PAD_X, PAD_T, PAD_B = 30, 26, 28         # the slider block's padding
ROW, ROW_GAP = 52, 14                    # a slider row, and the gap between rows
L_SIZE, V_SIZE = 30, 30                  # label (DM Sans 500), readout (JetBrains Mono 500)
GAP_X, TRACK_MIN = 22, 180               # label to track to readout; the shortest track
KNOB, TRACK_H = 34, 8
RADIUS = 30
TINT = 0.85                              # a temperature of +-100 is this strong a tint
MOVE = 0.7                               # how long a knob takes to reach its value

CSS = """
  .gs { position:relative; width:100%%; border-radius:%dpx; overflow:hidden; opacity:0; }
  .gs-pic { position:relative; width:100%%; overflow:hidden; }
  .gs-f { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .gs-tint { position:absolute; left:0; top:0; width:100%%; height:100%%; mix-blend-mode:soft-light; opacity:0; }
  .gs-rows { padding:%dpx %dpx %dpx; display:flex; flex-direction:column; gap:%dpx; }
  .gs-row { height:%dpx; display:flex; align-items:center; gap:%dpx; opacity:0; }
  .gs-l { flex:none; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .gs-tr { position:relative; flex:1 1 0; min-width:0; height:%dpx; }
  .gs-line { position:absolute; left:0; right:0; top:%dpx; height:%dpx; border-radius:%dpx; }
  .gs-mid { position:absolute; left:50%%; top:%dpx; width:4px; height:%dpx; margin-left:-2px; border-radius:2px; }
  .gs-fill { position:absolute; top:%dpx; height:%dpx; border-radius:%dpx; }
  .gs-k { position:absolute; top:0; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:50%%; }
  .gs-v { flex:none; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; text-align:right;
    white-space:nowrap; font-variant-numeric: tabular-nums; }
""" % (RADIUS, PAD_T, PAD_X, PAD_B, ROW_GAP, ROW, GAP_X, L_SIZE, line_px(L_SIZE, 1.25), KNOB, (KNOB - TRACK_H) // 2, TRACK_H,
       TRACK_H // 2, (KNOB - 18) // 2, 18, (KNOB - TRACK_H) // 2, TRACK_H, TRACK_H // 2, KNOB, KNOB, KNOB // 2, V_SIZE,
       line_px(V_SIZE, 1.25)) + _vg.CSS


def _label(s):
    return s.get("label") or KINDS.get(s.get("kind"), "")



def validate(scene):
    errs = need(scene, ["sliders"])
    sl = scene.get("sliders") or []
    if not isinstance(sl, list) or not 1 <= len(sl) <= 3:
        return errs + ["a grade-slider takes 1 to 3 sliders (got %s)" % (len(sl) if isinstance(sl, list) else sl,)]
    for i, s in enumerate(sl):
        if not isinstance(s, dict):
            errs.append("slider %d is an object" % i)
            continue
        if s.get("kind") not in KINDS:
            errs.append("slider %d: kind is one of %s (got %r)" % (i, ", ".join(KINDS), s.get("kind")))
        for k in ("from", "to"):
            if not is_num(s.get(k)) or not -100 <= s[k] <= 100:
                errs.append("slider %d: %s is a number from -100 to 100 (got %r)" % (i, k, s.get(k)))
        if is_num(s.get("from")) and is_num(s.get("to")) and s["from"] == s["to"]:
            errs.append("slider %d: from and to are the same, so nothing moves" % i)
        if s.get("at") is None:
            errs.append("slider %d has no at" % i)
        if s.get("label") is not None and not str(s["label"]).strip():
            errs.append("slider %d: label is empty" % i)
    e = _vg.check_src(scene.get("src"))
    return errs + ([e] if e else [])


def height(scene, width):
    n = len(scene["sliders"])
    return PIC_H[n] + PAD_T + n * ROW + (n - 1) * ROW_GAP + PAD_B


def _label_w(scene):
    return int(math.ceil(max(E.text_width(_label(s), L_SIZE, "display500") for s in scene["sliders"]))) + 2


def _value_w():
    return int(math.ceil(max(E.text_width(x, V_SIZE, "mono500") for x in ("-100", "+100")))) + 2


def min_width(scene):
    return 2 * PAD_X + _label_w(scene) + 2 * GAP_X + TRACK_MIN + _value_w()


def _shown(v):
    v = int(round(v))
    return ("+%d" % v) if v > 0 else str(v)


def _filter(kind, v):
    return {"contrast": "contrast(%s)", "saturation": "saturate(%s)", "exposure": "brightness(%s)"}[kind] % \
        _vg._num(round(1 + v / (200.0 if kind == "exposure" else 100.0), 3))


def _bar(v):
    """The fill's left and width in % of the track: from the middle to the knob."""
    k = (v + 100) / 2.0
    return {"left": "%s%%" % _vg._num(round(min(50.0, k), 2)), "width": "%s%%" % _vg._num(round(abs(k - 50.0), 2))}


def render(scene, ctx, box):
    p, sid = ctx.pc, ctx.id              # the editor is light paper on any ground
    sl = scene["sliders"]
    n = len(sl)
    pal = ctx.tokens["palette"]
    # the picture inside one wrapper per slider: each slider grades through its own filter (or tint), so two sliders
    # never fight over one filter string
    inner = _vg.picture(ctx, scene.get("src"), "p", seed=1)
    for i, s in enumerate(sl):
        if s["kind"] == "temperature":
            v = s["from"]
            inner += ('<i class="gs-tint" id="%s-w%d" style="background:%s;opacity:%s"></i><i class="gs-tint" id="%s-c%d" '
                      'style="background:%s;opacity:%s"></i>' % (sid, i, pal["peach"], _vg._num(round(max(0, v) / 100.0 * TINT, 3)),
                                                                 sid, i, pal["blue"], _vg._num(round(max(0, -v) / 100.0 * TINT, 3))))
    for i in reversed(range(n)):
        s = sl[i]
        style = "" if s["kind"] == "temperature" else ' style="filter:%s"' % _filter(s["kind"], s["from"])
        inner = '<div class="gs-f" id="%s-f%d"%s>%s</div>' % (sid, i, style, inner)
    rows, js = [], []
    lw, vw = _label_w(scene), _value_w()
    for i, s in enumerate(sl):
        t, attrs = ctx.item(s["at"])
        a, b = s["from"], s["to"]
        bar = _bar(a)
        rows.append('<div class="gs-row" id="%s-r%d"><span class="gs-l" id="%s-l%d" style="width:%dpx;color:%s">%s</span>'
                    '<div class="gs-tr"><i class="gs-line" style="background:%s"></i><i class="gs-mid" style="background:%s"></i>'
                    '<i class="gs-fill" id="%s-b%d" style="left:%s;width:%s;background:%s"></i>'
                    '<i class="gs-k" id="%s-k%d"%s style="left:%s%%;background:%s;box-shadow:inset 0 0 0 4px %s, 0 4px 12px %s"></i></div>'
                    '<span class="gs-v" id="%s-v%d" style="width:%dpx;color:%s">%s</span></div>'
                    % (sid, i, sid, i, lw, p["ink"], ctx.esc(_label(s)), p["line"], p["muted"], sid, i, bar["left"], bar["width"],
                       p["accent"], sid, i, attrs, _vg._num((a + 100) / 2.0), p["card"], p["accent"], E.rgba(p["ink"], 0.18),
                       sid, i, vw, p["dim"], _shown(a)))
        ease = ctx.tokens["motion"]["enter_ease"]
        # on its word: the label lights, the knob runs, the readout counts, the picture follows
        js.append(_vg.tween("#%s-l%d" % (sid, i), {"color": p["ink"]}, {"color": p["accent"], "duration": 0.3, "ease": ease}, t))
        js.append(_vg.tween("#%s-v%d" % (sid, i), {"color": p["dim"]}, {"color": p["ink"], "duration": 0.3, "ease": ease}, t))
        if i:   # the slider before it hands the light over
            js.append(_vg.tween("#%s-l%d" % (sid, i - 1), {"color": p["accent"]}, {"color": p["ink"], "duration": 0.3, "ease": ease}, t))
        js.append(_vg.tween("#%s-k%d" % (sid, i), {"left": "%s%%" % _vg._num((a + 100) / 2.0)},
                            {"left": "%s%%" % _vg._num((b + 100) / 2.0), "duration": MOVE, "ease": "power3.inOut"}, t))
        js.append(_vg.tween("#%s-b%d" % (sid, i), _bar(a), dict(_bar(b), duration=MOVE, ease="power3.inOut"), t))
        js.append(_vg.ticker("%s-v%d" % (sid, i), t, MOVE, a, b, "(Math.round(v) > 0 ? '+' : '') + Math.round(v)", "power3.inOut"))
        if s["kind"] == "temperature":
            for tag, sign in (("w", 1), ("c", -1)):
                o0, o1 = (round(max(0, sign * v) / 100.0 * TINT, 3) for v in (a, b))
                if o0 != o1:
                    js.append(_vg.tween("#%s-%s%d" % (sid, tag, i), {"opacity": o0}, {"opacity": o1, "duration": MOVE, "ease": "power3.inOut"}, t))
        else:
            js.append(_vg.tween("#%s-f%d" % (sid, i), {"filter": _filter(s["kind"], a)},
                                {"filter": _filter(s["kind"], b), "duration": MOVE, "ease": "power3.inOut"}, t))
    html = ('<div class="gs" id="%s-panel" style="height:%dpx;%s"><div class="gs-pic" style="height:%dpx;background:%s">%s</div>'
            '<div class="gs-rows">%s</div></div>' % (sid, height(scene, box[2]), ctx.paper_card(), PIC_H[n], p["chrome"], inner, "".join(rows)))
    js = [ctx.enter("#%s-panel" % sid, ctx.t_in, {"y": 40, "scale": 0.96}),
          ctx.enter("#%s .gs-row" % sid, ctx.t_in + 0.15, {"y": 12}, stagger=stagger_for(n, 0.08))] + js
    ctx.idle("#%s-panel" % sid, ctx.t_in + 0.7, ctx.t_out, {"y": -6}, every=1.8)
    return html, js
