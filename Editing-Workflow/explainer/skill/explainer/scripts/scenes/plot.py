"""plot: loss curves, one per panel (1 to 6, small multiples), each with a point on it; on a word every point shows its
tangent, and on another the points slide down to the minimum, the tangent turning flat as they go ("the slope tells
each weight which way is down").

  {"type": "plot", "x": "w", "y": "L", "tangent": "word:6", "descend": "word:9",
   "panels": [{"from": 0.9, "min": 0.1}, {"from": -0.7, "min": 0.3}]}

Each panel draws L = (w - min)^2 over w in -1.3 to 1.3; its point starts at `from` (-1 to 1). `tangent` and `descend`
are optional (without `tangent`, the tangent comes in with the descent). The slide is one tween of a number on the
timeline whose onUpdate places the point and turns the tangent (plotAt): seek-safe, the same frame at any seek.
"""
import math
from scenes import need

TYPE = "plot"
BAKED = True                    # drawn in Python at the width it is given
DECOR_KEYS = ("panels", "tangent", "descend")   # geometry and word anchors, not a claim
SPAN = 1.3                       # the w axis runs -SPAN to SPAN
ASPECT, GAP = 0.72, 24           # a panel's height (share of its width); between panels
PAD = 44                         # room for the axis letters inside a panel
A_SIZE, MAX_AXIS = 36, 3
TAN, DOT = 0.42, 14              # the tangent's length (share of the panel's width); the point's radius
SLIDE = 1.4

CSS = """
  .pl { position:relative; width:100%%; }
  .pl-panel { position:absolute; opacity:0; }
  .pl-panel svg { position:absolute; left:0; top:0; overflow:visible; }
  .pl-ax { position:absolute; font-family:"Instrument Serif", serif; font-style:italic; font-size:%dpx; line-height:1; }
""" % A_SIZE


def _grid(n):
    cols = 1 if n == 1 else (2 if n <= 4 else 3)
    return cols, int(math.ceil(n / float(cols)))


def validate(scene):
    errs = need(scene, ["panels"])
    ps = scene.get("panels") or []
    if not 1 <= len(ps) <= 6:
        errs.append("a plot takes 1 to 6 panels (got %d)" % len(ps))
    for i, p in enumerate(ps):
        if not isinstance(p, dict) or any(not isinstance(p.get(k), (int, float)) or isinstance(p.get(k), bool) or not -1 <= p[k] <= 1
                                          for k in ("from", "min")):
            errs.append("panel %d is {from, min}, each -1 to 1" % i)
        elif abs(p["from"] - p["min"]) < 0.05:
            errs.append("panel %d: from and min differ (or the point has nowhere to go)" % i)
    for k in ("x", "y"):
        if scene.get(k) is not None and not 0 < len(str(scene[k])) <= MAX_AXIS:
            errs.append("%s %r: at most %d characters (an axis letter)" % (k, scene[k], MAX_AXIS))
    return errs


def _panel_w(scene, width):
    cols, _ = _grid(len(scene["panels"]))
    return (width - GAP * (cols - 1)) / float(cols)


def height(scene, width):
    _, rows = _grid(len(scene["panels"]))
    return int(math.ceil(_panel_w(scene, width) * ASPECT)) * rows + GAP * (rows - 1)


def min_width(scene):
    cols, _ = _grid(len(scene["panels"]))
    return 600 if cols == 1 else cols * 290 + GAP * (cols - 1)


PLOT_AT = ("window.plotAt = function (id, u) { var p = document.getElementById(id), d = p.dataset, m = +d.m, "
           "x = +d.ox + u * d.sx, y = +d.oy - (u - m) * (u - m) * d.sy, a = Math.atan(2 * (u - m) * d.sy / d.sx) * 180 / Math.PI; "
           "p.querySelector('.pl-dot').setAttribute('transform', 'translate(' + x + ' ' + y + ')'); "
           "p.querySelector('.pl-tan').setAttribute('transform', 'translate(' + x + ' ' + y + ') rotate(' + (-a) + ')'); };")


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    ps = scene["panels"]
    cols, rows = _grid(len(ps))
    pw = _panel_w(scene, Wd)
    ph = int(math.ceil(pw * ASPECT))
    curve, tan = c["accent"], c["accent2"]
    panels, js = [], [PLOT_AT]
    t_tan = ctx.at(scene["tangent"]) if scene.get("tangent") is not None else None
    t_down = ctx.at(scene["descend"]) if scene.get("descend") is not None else None
    marks = "".join("<i%s></i>" % ctx.item(scene[k])[1] for k in ("tangent", "descend") if scene.get(k) is not None)
    for i, p in enumerate(ps):
        m, u = float(p["min"]), float(p["from"])
        sx = (pw - 2 * PAD) / (2 * SPAN)
        sy = (ph - 2 * PAD) * 0.92 / max((SPAN + m) ** 2, (SPAN - m) ** 2)
        ox, oy = pw / 2.0, ph - PAD
        pts = " ".join("%.1f,%.1f" % (ox + w * sx, oy - (w - m) ** 2 * sy) for w in [-SPAN + k * SPAN / 30.0 for k in range(61)])
        a = math.degrees(math.atan(2 * (u - m) * sy / sx))
        x, y = ox + u * sx, oy - (u - m) ** 2 * sy
        half = pw * TAN / 2.0
        svg = ('<svg width="%.0f" height="%d"><path d="M%d %.1f H%.1f M%.1f %.1f V%d" stroke="%s" stroke-width="3" fill="none"/>'
               '<polyline class="pl-curve" points="%s" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round" pathLength="1" '
               'stroke-dasharray="1" stroke-dashoffset="1"/>'
               '<g class="pl-tan" id="%s-t%d" transform="translate(%.1f %.1f) rotate(%.2f)" opacity="0"><line x1="%.1f" x2="%.1f" y1="0" y2="0" '
               'stroke="%s" stroke-width="5" stroke-linecap="round"/></g>'
               '<g class="pl-dot" transform="translate(%.1f %.1f)"><circle r="%d" fill="none" stroke="%s" stroke-width="5" class="pl-ring" '
               'id="%s-d%d" opacity="0"/></g></svg>'
               % (pw, ph, PAD // 2, oy, pw - PAD // 2, ox, oy, PAD // 2, c["line"], pts, curve, sid, i, x, y, -a, -half, half, tan,
                  x, y, DOT, tan, sid, i))
        left, top = (i % cols) * (pw + GAP), (i // cols) * (ph + GAP)
        panels.append('<div class="pl-panel" id="%s-p%d" data-m="%s" data-u="%s" data-ox="%.1f" data-oy="%.1f" data-sx="%.3f" data-sy="%.3f" '
                      'style="left:%.1fpx;top:%.1fpx;width:%.0fpx;height:%dpx">%s'
                      '<div class="pl-ax" style="left:%.1fpx;top:%dpx;color:%s">%s</div><div class="pl-ax" style="right:0;top:%.1fpx;color:%s">%s</div></div>'
                      % (sid, i, m, u, ox, oy, sx, sy, left, top, pw, ph, svg, ox + 10, 0, c["dim"], ctx.esc(scene.get("y", "L")),
                         oy - A_SIZE - 8, c["dim"], ctx.esc(scene.get("x", "w"))))
        t_in = ctx.t_in + 0.12 * i
        js.append(ctx.enter("#%s-p%d" % (sid, i), t_in, {"y": 20}))
        js.append("tl.fromTo('#%s-p%d .pl-curve', { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.8, ease: '%s', immediateRender: false }, %.3f);"
                  % (sid, i, ctx.tokens["motion"]["enter_ease"], t_in + 0.1))
        show = t_tan if t_tan is not None else t_down
        if show is not None:
            js.append(ctx.enter("#%s-t%d" % (sid, i), show + 0.08 * i))
            js.append(ctx.enter("#%s-d%d" % (sid, i), show + 0.08 * i))
        if t_down is not None:
            js.append("tl.fromTo({ u: %s }, { u: %s }, { u: %s, duration: %s, ease: 'power2.inOut', immediateRender: false, "
                      "onUpdate: function () { plotAt('%s-p%d', this.targets()[0].u); } }, %.3f);"
                      % (u, u, m, SLIDE, sid, i, max(t_down, (show or 0) + 0.3) + 0.08 * i))
    H = rows * ph + GAP * (rows - 1)
    return '<div class="pl" id="%s-pl" style="height:%dpx">%s%s</div>' % (sid, H, "".join(panels), marks), js
