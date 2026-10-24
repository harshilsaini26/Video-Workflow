"""_annotate.py: notes drawn over an image (a helper for product-hero and photo-grid, not a scene: the leading underscore
keeps discover() off it). The editorial reels point at the thing the voice names: a hand-drawn circle around it, a
short leader line, a pill label in the accent ("WAIT... A WIRE?", "+ USB-C").

  {"x": 0.72, "y": 0.78, "label": "WAIT... A WIRE?", "at": "word:3", "mark": "circle", "side": "left"}

x and y are fractions of the image's box; mark is circle (r 56, drawn on), dot (a 18 px dot that pops) or none; the
label sits left or right of the mark at the end of a 56 px leader and must fit inside the box (E3 names one that
cannot). The circle draws on its word (0.45 s), the leader 0.3 s later, the label 0.15 s after that.
"""
import math
import explainer_lib as E
from scenes import SceneError, js_obj

MARKS = {"circle": 56, "dot": 9, "none": 0}
STROKE = 6
LEAD = 56                 # the leader line's length
LABEL, LABEL_H, PAD_X = 28, 44, 16
SPACING = 0.06
MAX_NOTES, MAX_CHARS = 4, 32

CSS = """
  .an { position:absolute; left:0; top:0; pointer-events:none; }
  .an svg { position:absolute; overflow:visible; }
  .an-l { position:absolute; height:4px; border-radius:2px; transform:scaleX(0); }
  .an-d { position:absolute; border-radius:50%%; transform:scale(0); }
  .an-t { position:absolute; height:%dpx; line-height:%dpx; padding:0 %dpx; border-radius:%dpx; font-family: var(--label);
    font-weight:500; font-size:%dpx; letter-spacing:%sem; white-space:nowrap; opacity:0; }
""" % (LABEL_H, LABEL_H, PAD_X, LABEL_H // 2, LABEL, SPACING)


def validate(notes):
    if not isinstance(notes, list) or len(notes) > MAX_NOTES:
        return ["notes is a list of at most %d {x, y, label, at, mark, side}" % MAX_NOTES]
    errs = []
    for i, n in enumerate(notes):
        if not isinstance(n, dict):
            errs.append("note %d is {x, y, label, at}" % i)
            continue
        for k in ("x", "y"):
            v = n.get(k)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 1:
                errs.append("note %d: %s is a fraction of the image, 0 to 1" % (i, k))
        if not isinstance(n.get("label"), str) or not n["label"].strip() or len(n["label"]) > MAX_CHARS:
            errs.append("note %d: label is a short line (%d characters at most)" % (i, MAX_CHARS))
        if n.get("mark", "circle") not in MARKS:
            errs.append("note %d: mark is circle, dot or none" % i)
        if n.get("side", "right") not in ("left", "right"):
            errs.append("note %d: side is left or right" % i)
    return errs


def label_w(text):
    return int(math.ceil(E.text_width(text, LABEL, "mono500", spacing=SPACING))) + 2 * PAD_X + 2


def render(notes, ctx, w, h, sid):
    """(html, js): the notes over an image box w x h (the scene's own pixels, before its scale)."""
    c = ctx.c
    parts, js = [], []
    for i, n in enumerate(notes):
        mark, side = n.get("mark", "circle"), n.get("side", "right")
        r = MARKS[mark]
        px, py = n["x"] * w, n["y"] * h
        lw = label_w(n["label"])
        if side == "right":
            l_left, t_left = px + r, px + r + LEAD
        else:
            l_left, t_left = px - r - LEAD, px - r - LEAD - lw
        if t_left < 0 or t_left + lw > w or py - LABEL_H / 2.0 < 0 or py + LABEL_H / 2.0 > h:
            raise SceneError("note %r does not fit %s of its point inside the image (%d px wide): put it on the other side, "
                             "move the point or shorten it" % (n["label"], side == "right" and "right" or "left", w))
        t, attrs = ctx.item(n["at"]) if n.get("at") else (ctx.t_in, "")
        if mark == "circle":
            circ = 2 * math.pi * r
            parts.append('<svg style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><circle id="%s-n%dc" class="%s" cx="%d" cy="%d" r="%d" fill="none" '
                         'stroke="%s" stroke-width="%d" stroke-linecap="round" style="stroke-dasharray:%.1f;stroke-dashoffset:%.1f"/></svg>'
                         % (px - r - STROKE, py - r - STROKE, 2 * (r + STROKE), 2 * (r + STROKE), sid, i, ctx.boil.strip(), r + STROKE, r + STROKE, r,
                            c["accent"], STROKE, circ, circ))
            js.append("tl.fromTo('#%s-n%dc', %s, %s, %.3f);" % (sid, i, js_obj({"strokeDashoffset": round(circ, 1)}),
                                                              js_obj({"strokeDashoffset": 0, "duration": 0.45, "ease": "power2.inOut",
                                                                      "immediateRender": False}), t))
        elif mark == "dot":
            parts.append('<i class="an-d" id="%s-n%dc" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s"></i>'
                         % (sid, i, px - r, py - r, 2 * r, 2 * r, c["accent"]))
            js.append("tl.fromTo('#%s-n%dc', %s, %s, %.3f);" % (sid, i, js_obj({"scale": 0}), js_obj({"scale": 1, "duration": 0.2,
                                                                                                     "ease": "power3.out", "immediateRender": False}), t))
        parts.append('<i class="an-l%s" id="%s-n%dl" style="left:%dpx;top:%dpx;width:%dpx;background:%s;transform-origin:%s 50%%"></i>'
                     % (ctx.boil, sid, i, l_left, py - 2, LEAD, c["accent"], "0" if side == "right" else "100%"))
        js.append("tl.fromTo('#%s-n%dl', %s, %s, %.3f);" % (sid, i, js_obj({"scaleX": 0}), js_obj({"scaleX": 1, "duration": 0.2,
                                                                                                "ease": "power2.out", "immediateRender": False}), t + 0.3))
        parts.append('<div class="an-t" id="%s-n%dt"%s style="left:%dpx;top:%dpx;background:%s;color:%s">%s</div>'
                     % (sid, i, attrs, t_left, py - LABEL_H / 2.0, c["fill"], c["on_fill"], ctx.esc(n["label"])))
        js.append("tl.fromTo('#%s-n%dt', %s, %s, %.3f);" % (sid, i, js_obj({"opacity": 0, "x": 12 if side == "left" else -12}),
                                                          js_obj({"opacity": 1, "x": 0, "duration": 0.3, "ease": "power3.out",
                                                                  "immediateRender": False}), t + 0.45))
    return '<div class="an" style="width:%dpx;height:%dpx">%s</div>' % (w, h, "".join(parts)), js
