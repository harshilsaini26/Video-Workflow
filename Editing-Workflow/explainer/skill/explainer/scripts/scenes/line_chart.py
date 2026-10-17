"""line-chart: the line draws point by point on its words, points pop, the value counts up in step (SPEC §6.2)."""
import explainer_lib as E
from scenes import js_str, line_px, mono_lines, need, widest

TYPE = "line-chart"
NEEDS_SOURCE = True
L_SIZE, L_LH, L_GAP = 30, 1.3, 18      # the mono label on top
V_SIZE, V_GAP = 96, 12                 # the value readout (line height 1)
CHART = 400                            # the plot, px tall
X_SIZE, X_LH, X_GAP = 28, 1.3, 10      # the x labels under it (at the 28 px floor)
DOT = 22
DRAW = 0.6                             # seconds a segment takes to draw

CSS = """
  .c-label { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:.12em;
    text-align:center; margin-bottom:%dpx; opacity:0; }
  .c-read { font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:-.02em; font-variant-numeric: tabular-nums;
    white-space:nowrap; margin-bottom:%dpx; opacity:0; }
  .c-plot { position:relative; width:100%%; height:%dpx; opacity:0; }
  .c-plot svg { position:absolute; inset:0; overflow:visible; }
  .c-dot { position:absolute; width:%dpx; height:%dpx; margin:-%dpx 0 0 -%dpx; border-radius:50%%; border:5px solid; opacity:0; }
  .c-x { display:flex; justify-content:space-between; width:100%%; margin-top:%dpx; font-family: var(--label);
    font-weight:500; font-size:%dpx; line-height:%dpx; opacity:0; }
""" % (L_SIZE, line_px(L_SIZE, L_LH), L_GAP, V_SIZE, V_SIZE, V_GAP, CHART, DOT, DOT, DOT // 2, DOT // 2,
       X_GAP, X_SIZE, line_px(X_SIZE, X_LH))


def fmt(scene, v):
    return E.L.full_digits(v, scene.get("prefix", ""), scene.get("suffix", ""), int(scene.get("decimals", 0)))


def validate(scene):
    errs = need(scene, ["points", "x"])
    pts, xs = scene.get("points") or [], scene.get("x") or []
    if len(pts) < 2:
        errs.append("a line needs at least 2 points")
    if len(pts) != len(xs):
        errs.append("points (%d) and x (%d) must have the same length" % (len(pts), len(xs)))
    for r in scene.get("reveal", []):
        if not isinstance(r.get("point"), int) or not 0 <= r["point"] < len(pts):
            errs.append("reveal point %r is not one of the %d points" % (r.get("point"), len(pts)))
    if any(not isinstance(p, (int, float)) for p in pts):
        errs.append("points must be numbers")
    return errs


def height(scene, width):
    h = V_SIZE + V_GAP + CHART + X_GAP + line_px(X_SIZE, X_LH)
    if scene.get("label"):
        h += line_px(L_SIZE, L_LH) * mono_lines(scene["label"], L_SIZE, width) + L_GAP
    return h


def min_width(scene):
    # the readout counts from point to point: its widest moment on the way, not only the points (digits are proportional)
    count = max(E.L.count_width(p, V_SIZE, scene.get("prefix", ""), scene.get("suffix", ""), int(scene.get("decimals", 0)))
                for p in scene["points"])
    xs = sum(E.text_width(str(x), X_SIZE) for x in scene["x"]) + 16 * len(scene["x"])
    return int(max(count, xs)) + 1


def render(scene, ctx, box):
    c = ctx.c
    left, top, width = box
    pts = [float(p) for p in scene["points"]]
    lo, hi = min(0.0, min(pts)), max(pts)
    span = (hi - lo) or 1.0
    xy = [(round(DOT + i * (width - 2 * DOT) / (len(pts) - 1), 1), round(CHART - DOT - (p - lo) / span * (CHART - 2 * DOT), 1))
          for i, p in enumerate(pts)]
    seg = [((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 for (x1, y1), (x2, y2) in zip(xy, xy[1:])]
    total = round(sum(seg), 1)
    upto = lambda k: round(sum(seg[:k]), 1)
    line_col = c["accent"]
    reveals = sorted(((ctx.at(r["at"]), r["point"]) for r in scene.get("reveal", [])))
    if not reveals:
        reveals = [(ctx.t_in + 0.2, len(pts) - 1)]
    sid = ctx.id
    parts = []
    if scene.get("label"):
        parts.append('<div class="c-label" style="color:%s">%s</div>' % (c["dim"], ctx.esc(scene["label"])))
    first = pts[0]
    if [p for _, p in reveals] != sorted(set(p for _, p in reveals)):
        ctx.fail("reveal points must move forward in time (got %s)" % [p for _, p in reveals])
    parts.append('<div class="c-read" id="%s-v" data-final="%s" style="color:%s">%s</div>'
                 % (sid, ctx.esc(fmt(scene, pts[reveals[-1][1]])), ctx.ink, ctx.esc(fmt(scene, first))))
    path = "M" + " L".join("%s %s" % p for p in xy)
    dots = "".join('<div class="c-dot" id="%s-d%d" style="left:%spx;top:%spx;border-color:%s;background:%s"></div>'
                   % (sid, i, x, y, line_col, c["card"]) for i, (x, y) in enumerate(xy))
    parts.append('<div class="c-plot" id="%s-plot"><svg width="%d" height="%d" viewBox="0 0 %d %d">'
                 '<path id="%s-line" d="%s" fill="none" stroke="%s" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"'
                 ' stroke-dasharray="%s" stroke-dashoffset="%s"/></svg>%s</div>'
                 % (sid, width, CHART, width, CHART, sid, path, line_col, total, total, dots))
    parts.append('<div class="c-x" style="color:%s">%s</div>' % (c["dim"],
                                                                 "".join("<span>%s</span>" % ctx.esc(x) for x in scene["x"])))
    js = [ctx.enter("#%s .c-label, #%s-v, #%s-plot, #%s .c-x" % (sid, sid, sid, sid), ctx.t_in, {"y": 24}, stagger=0.15),
          ctx.enter("#%s-d0" % sid, ctx.t_in + 0.1, {"scale": 0.4})]
    shown, value = 0, first
    for t, p in reveals:
        dur = DRAW + 0.12 * (p - shown - 1)
        js.append("tl.to('#%s-line', { strokeDashoffset: %s, duration: %.3f, ease: '%s' }, %.3f);"
                  % (sid, round(total - upto(p), 1), dur, ctx.tokens["motion"]["enter_ease"], t))
        for k in range(shown + 1, p + 1):
            js.append(ctx.enter("#%s-d%d" % (sid, k), t + dur * (upto(k) - upto(shown)) / max(1e-6, upto(p) - upto(shown)) - 0.1, {"scale": 0.4}, dur=0.3))
        js.append("countUp('#%s-v', %s, %s, %.3f, %.3f, %s, %s, %d);" % (sid, value, pts[p], t, dur, js_str(scene.get("prefix", "")),
                                                                        js_str(scene.get("suffix", "")), int(scene.get("decimals", 0))))
        shown, value = p, pts[p]
    return "".join(parts), js
