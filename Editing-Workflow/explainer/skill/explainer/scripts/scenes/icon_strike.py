"""icon-strike: one big featured Lucide icon in a highlight disc; on its word a strike in the bad role crosses it
diagonally and the icon dims. An optional label sits under it, and an optional replacement lands after: the struck icon
steps aside, smaller, and the new one takes the stage. For "you don't need the paid tools: the free ones do it".

  {"type": "icon-strike", "icon": "credit-card", "label": "Paid tools", "at": "word:2", "strike": {"at": "word:4"},
   "replacement": {"icon": "gift", "label": "Free tools", "at": "word:7"}}

`at` (the icon's own word) is optional: without it the icon arrives with the scene.
"""
import math, re
import explainer_lib as E
from scenes import js_obj, line_px, need

TYPE = "icon-strike"
DISC, ICON = 300, 150                 # the featured disc and the icon in it
L_SIZE, L_LH, L_GAP = 52, 1.2, 34     # the label under the disc: DM Sans 700, one line
OVER = 22                             # the strike reaches this far past the disc's square on each end
STROKE, HALO = 18, 34                 # the strike, and the ground-coloured halo that lifts it off the disc
SHRINK = 0.6                          # the struck icon's size once its replacement is in
ARROW, A_GAP = 72, 34                 # the arrow between the two, and the room either side of it
DIM = 0.38                            # how bright the struck disc stays
_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

CSS = """
  .is { position:relative; width:100%%; }
  .is-col { position:absolute; top:0; display:flex; flex-direction:column; align-items:center; opacity:0; }
  .is-disc { position:relative; width:%dpx; height:%dpx; border-radius:50%%; flex:none; display:flex; align-items:center;
    justify-content:center; }
  .is-disc > span { width:%dpx; height:%dpx; display:flex; }
  .is-disc > span svg { width:100%%; height:100%%; }
  .is-x { position:absolute; left:-%dpx; top:-%dpx; width:%dpx; height:%dpx; overflow:visible; pointer-events:none; }
  .is-label { margin-top:%dpx; font-weight:700; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .is-arrow { position:absolute; width:%dpx; height:%dpx; opacity:0; }
""" % (DISC, DISC, ICON, ICON, OVER, OVER, DISC + 2 * OVER, DISC + 2 * OVER, L_GAP, L_SIZE, line_px(L_SIZE, L_LH), ARROW, ARROW)

# Lucide's arrow-right (ISC), drawn here so the scene needs no second icon file
ARROW_SVG = ('<svg class="is-arrow" id="%s" style="left:%dpx;top:%dpx;color:%s" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>')


def validate(scene):
    errs = need(scene, ["icon", "strike"])
    if scene.get("icon") is not None and not _NAME.match(str(scene.get("icon"))):
        errs.append("icon %r is not a Lucide name (lower-case words joined by -)" % (scene.get("icon"),))
    st = scene.get("strike")
    if st is not None and (not isinstance(st, dict) or st.get("at") is None):
        errs.append("strike needs at: the word that crosses the icon out ({\"at\": \"word:N\"})")
    rep = scene.get("replacement")
    if rep is not None:
        if not isinstance(rep, dict) or not _NAME.match(str(rep.get("icon", ""))) or rep.get("at") is None:
            errs.append("replacement needs a Lucide icon and at (and may have a label)")
    for key, part in (("label", scene.get("label")), ("replacement label", (rep or {}).get("label") if isinstance(rep, dict) else None)):
        if part is not None and len(str(part).split()) > 3:
            errs.append("%s: at most three words (got %r)" % (key, part))
    return errs


def _label_w(text):
    return int(math.ceil(E.text_width(text, L_SIZE))) + 2 if text else 0


def _cols(scene):
    """The two column widths at full size: the struck one and its replacement (0 when there is none)."""
    rep = scene.get("replacement")
    old = max(DISC, _label_w(scene.get("label")))
    new = max(DISC, _label_w(rep.get("label"))) if rep else 0
    return old, new


def height(scene, width):
    rep = scene.get("replacement") or {}
    return DISC + (L_GAP + line_px(L_SIZE, L_LH) if scene.get("label") or rep.get("label") else 0)


def min_width(scene):
    old, new = _cols(scene)
    if not new:
        return old + 2 * OVER
    return int(math.ceil(old * SHRINK)) + 2 * A_GAP + ARROW + new + 4


def _column(ctx, cid, icon, label, disc_style, icon_col, label_col, left, w, attrs="", strike=""):
    lab = '<div class="is-label" id="%s-l" style="color:%s">%s</div>' % (cid, label_col, ctx.esc(label)) if label else ""
    return ('<div class="is-col" id="%s"%s style="left:%dpx;width:%dpx"><div class="is-disc" id="%s-d" style="%s"><span style="color:%s">%s</span>'
            '</div>%s%s</div>' % (cid, attrs, left, w, cid, disc_style, icon_col, ctx.icon(icon), strike, lab))


def render(scene, ctx, box):
    c, mo, sid = ctx.c, ctx.tokens["motion"], ctx.id
    W = box[2]
    hl = c["highlight"]
    old_w, new_w = _cols(scene)
    rep = scene.get("replacement")
    js = []
    # the struck column starts centred
    t_in, attrs = ctx.item(scene["at"]) if scene.get("at") is not None else (ctx.t_in, "")
    ts, s_attrs = ctx.item(scene["strike"]["at"])
    if ts < t_in - 1e-6:
        ctx.fail("the strike (%s) comes before the icon it crosses (%s)" % (scene["strike"]["at"], scene.get("at")))
    left0 = int(round((W - old_w) / 2.0))
    span = DISC + 2 * OVER
    a, b = OVER + DISC / 2.0 - DISC * 0.43, OVER + DISC / 2.0 + DISC * 0.43     # corner to corner, a little past the rim
    length = int(math.ceil(math.hypot(b - a, b - a))) + 2
    line = lambda w, col, i: ('<line id="%s-x%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%d" stroke-linecap="round" '
                              'stroke-dasharray="%d" stroke-dashoffset="%d"/>' % (sid, i, a, a, b, b, col, w, length, length))
    strike = ('<svg class="is-x" id="%s-x"%s style="left:%dpx" viewBox="0 0 %d %d">%s%s</svg>'
              % (sid, s_attrs, (old_w - DISC) // 2 - OVER, span, span, line(HALO, c["bg"], "h"), line(STROKE, c["bad"], "s")))
    disc = "background:%s;box-shadow:%s" % (hl["fill"], c["shadow"])
    html = [_column(ctx, "%s-o" % sid, scene["icon"], scene.get("label"), disc, hl["text"], ctx.ink, left0, old_w, attrs, strike)]
    js.append(ctx.enter("#%s-o" % sid, t_in, {"y": 40, "scale": 0.9}))
    # the strike draws corner to corner on its word, then the icon behind it dims
    js.append("tl.fromTo('#%s-xh, #%s-xs', { strokeDashoffset: %d }, %s, %.3f);"
              % (sid, sid, length, js_obj({"strokeDashoffset": 0, "duration": 0.36, "ease": "power3.inOut", "immediateRender": False}), ts))
    js.append("tl.to('#%s-o-d', %s, %.3f);" % (sid, js_obj({"opacity": DIM, "duration": 0.4, "ease": mo["enter_ease"]}), ts + 0.2))
    if scene.get("label"):
        js.append("tl.to('#%s-o-l', %s, %.3f);" % (sid, js_obj({"color": c["muted"], "duration": 0.4, "ease": mo["enter_ease"]}), ts + 0.2))
    if rep:
        tr, r_attrs = ctx.item(rep["at"])
        if tr < ts - 1e-6:
            ctx.fail("the replacement (%s) comes before the strike (%s)" % (rep["at"], scene["strike"]["at"]))
        small = int(math.ceil(old_w * SHRINK))
        total = small + 2 * A_GAP + ARROW + new_w
        x0 = (W - total) / 2.0
        old_centre, new_left = x0 + small / 2.0, x0 + small + 2 * A_GAP + ARROW
        js.append("tl.to('#%s-o', %s, %.3f);" % (sid, js_obj({"x": round(old_centre - (left0 + old_w / 2.0), 2), "scale": SHRINK,
                                                             "transformOrigin": "50%% %dpx" % (DISC // 2), "duration": 0.8, "ease": "expo.out"}), tr))
        html.append(ARROW_SVG % ("%s-a" % sid, int(round(x0 + small + A_GAP)), (DISC - ARROW) // 2, c["muted"]))
        js.append(ctx.enter("#%s-a" % sid, tr + 0.15, {"x": -24}))
        html.append(_column(ctx, "%s-n" % sid, rep["icon"], rep.get("label"), disc, hl["text"], ctx.ink, int(round(new_left)), new_w, r_attrs))
        js.append(ctx.enter("#%s-n" % sid, tr, {"y": 40, "scale": 0.9}, dur=0.6))
    return '<div class="is" style="height:%dpx">%s</div>' % (height(scene, W), "".join(html)), js
