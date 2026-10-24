"""morph: one object becomes the next, the way 3Blue1Brown never cuts (the Transform). A set of pieces takes one form
after another on the voice's words: pixels in a grid become a column of input neurons, the column folds into one
neuron ("a weighted sum"), bars become a ring.

  {"type": "morph", "n": 16, "values": [0.2, 0.9, ...],
   "steps": [{"form": "grid", "at": "word:5", "label": "Pixels"},
             {"form": "column", "at": "word:8", "label": "Input neurons", "color": "accent2"},
             {"form": "merge", "at": "word:11", "label": "One weighted sum"}],
   "indicate": {"piece": 5, "at": "word:13"}}

Forms: grid (squares), column, row and ring (circles), bars (`heights`, one 0 to 1 per piece) and merge (every piece
on one circle). Every piece is one path of POINTS points that starts at its top left and runs clockwise in every form,
so a Transform moves each point straight to its partner and nothing twists (after manim's Transform and
huashu-art-motion's DG.rectPts / DG.circlePts, MIT). `values` (0 to 1 a piece) set each piece's fill strength, like an
activation; `color` is a role (accent by default). The move is manim's `smooth` ease (6t^5 - 15t^4 + 10t^3: no speed
and no acceleration at either end), lagged a little piece by piece; the label hands over upward (FadeOut and FadeIn
with a shift). `indicate` grows one piece to 1.2 in the highlight colour and lets it go (manim's Indicate). Between
moves the picture holds still, as in the original: the motion is the next Transform.
"""
import math
import explainer_lib as E
from scenes import need, is_num

TYPE = "morph"
DECOR_KEYS = ("n", "values", "heights", "piece", "color")   # how many pieces, how strong, how tall, which role: not a claim
BAKED = True                       # drawn at the width it is given
BEATS = True                       # gate E5 looks at each form once it has settled, before the next move
FORMS = ("grid", "column", "row", "ring", "bars", "merge")
ROLES = ("accent", "accent2", "fill", "good", "bad", "warn", "ink")
POINTS = 24
LANE = 12                          # a column or row of more pieces wraps into lanes of this many
DRAW = 0.7                         # the drawing's height over the box width
L_SIZE, MAX_LABEL = 44, 28
LAB_H = 96                         # the label band under the drawing
MOVE, MOVE_MIN, LAG_TOTAL = 1.2, 0.5, 0.6
LABEL_SWAP = 0.2                   # the old label lifts away on the word, the new one rises in once it has gone
SMOOTH = "window.smoothEase = function (t) { return t * t * t * (t * (6 * t - 15) + 10); };"

CSS = """
  .mo { position:relative; width:100%%; }
  .mo svg { position:absolute; left:0; top:0; overflow:visible; }
  .mo-p { opacity:0; transform-box:fill-box; transform-origin:center; }
  .mo-label { position:absolute; left:0; width:100%%; text-align:center; font-weight:700; font-size:%dpx; line-height:1.2;
    white-space:nowrap; opacity:0; }
""" % L_SIZE


def validate(scene):
    errs = need(scene, ["steps"])
    n = scene.get("n", 16)
    if not isinstance(n, int) or isinstance(n, bool) or not 4 <= n <= 64:
        errs.append("n is 4 to 64 pieces (got %r)" % (n,))
        n = None
    steps = scene.get("steps")
    if steps is not None and (not isinstance(steps, list) or not 2 <= len(steps) <= 6):
        errs.append("2 to 6 steps (one form each)")
    for k, st in enumerate(steps if isinstance(steps, list) else []):
        if not isinstance(st, dict) or st.get("at") is None:
            errs.append("step %d needs its word (at)" % k)
            continue
        if st.get("form") not in FORMS:
            errs.append("step %d: form is one of %s (got %r)" % (k, ", ".join(FORMS), st.get("form")))
        if st.get("color") is not None and st["color"] not in ROLES:
            errs.append("step %d: color is a role: %s" % (k, ", ".join(ROLES)))
        if st.get("label") is not None and not 0 < len(str(st["label"])) <= MAX_LABEL:
            errs.append("step %d: label: 1 to %d characters" % (k, MAX_LABEL))
        if st.get("form") == "bars":
            h = st.get("heights")
            if not isinstance(h, list) or (n and len(h) != n) or any(not is_num(v) or not 0 <= v <= 1 for v in h):
                errs.append("step %d: bars needs heights, one 0 to 1 per piece" % k)
    v = scene.get("values")
    if v is not None and n and (not isinstance(v, list) or len(v) != n or any(not is_num(x) or not 0 <= x <= 1 for x in v)):
        errs.append("values: one 0 to 1 per piece (%d)" % n)
    ind = scene.get("indicate")
    if ind is not None:
        if not isinstance(ind, dict) or ind.get("at") is None:
            errs.append("indicate is {piece, at}")
        elif n and (not isinstance(ind.get("piece"), int) or not 0 <= ind["piece"] < n):
            errs.append("indicate.piece is 0 to %d" % (n - 1))
    return errs


def min_width(scene):
    labels = [str(s.get("label") or "") for s in scene["steps"]]
    return max([600] + [int(math.ceil(E.text_width(l, L_SIZE, "display700"))) + 40 for l in labels])


def height(scene, width):
    return int(math.ceil(width * DRAW)) + LAB_H


def min_text(scene):
    return L_SIZE if any(s.get("label") for s in scene["steps"]) else None


def _rect(cx, cy, w, h):
    """POINTS points round a rectangle, from its top-left corner, clockwise, evenly along the perimeter."""
    per = 2 * (w + h)
    out = []
    for i in range(POINTS):
        d = per * i / POINTS
        if d < w:
            out.append((cx - w / 2 + d, cy - h / 2))
        elif d < w + h:
            out.append((cx + w / 2, cy - h / 2 + d - w))
        elif d < 2 * w + h:
            out.append((cx + w / 2 - (d - w - h), cy + h / 2))
        else:
            out.append((cx - w / 2, cy + h / 2 - (d - 2 * w - h)))
    return out


def _circle(cx, cy, r):
    """POINTS points round a circle, from its top left (-135 degrees), clockwise on screen."""
    return [(cx + r * math.cos(-3 * math.pi / 4 + 2 * math.pi * i / POINTS),
             cy + r * math.sin(-3 * math.pi / 4 + 2 * math.pi * i / POINTS)) for i in range(POINTS)]


def forms(step, n, Wd, Hd):
    """Every piece's points in this step's form, inside a Wd x Hd drawing."""
    f = step["form"]
    if f == "grid":
        cols = int(math.ceil(math.sqrt(n)))
        rows = int(math.ceil(n / float(cols)))
        cell = min(Wd * 0.9 / cols, Hd * 0.92 / rows)
        x0, y0 = (Wd - cell * cols) / 2, (Hd - cell * rows) / 2
        return [_rect(x0 + cell * (i % cols + 0.5), y0 + cell * (i // cols + 0.5), cell * 0.86, cell * 0.86) for i in range(n)]
    if f in ("column", "row"):
        lanes = int(math.ceil(n / float(LANE)))         # past LANE pieces a column wraps into side-by-side columns
        per = int(math.ceil(n / float(lanes)))
        span = Hd * 0.92 if f == "column" else Wd * 0.92
        step_ = min(span / per, 110)
        r = step_ * 0.36
        out = []
        for i in range(n):
            lane, j = divmod(i, per)
            a = (Hd if f == "column" else Wd) / 2 - step_ * (per - 1) / 2 + step_ * j
            b = (Wd if f == "column" else Hd) / 2 + step_ * 1.6 * (lane - (lanes - 1) / 2.0)
            out.append(_circle(b, a, r) if f == "column" else _circle(a, b, r))
        return out
    if f == "ring":
        R = min(Wd, Hd) * 0.4
        r = min(R * math.sin(math.pi / n) * 0.8, 60)
        return [_circle(Wd / 2 + R * math.cos(-math.pi / 2 + 2 * math.pi * i / n), Hd / 2 + R * math.sin(-math.pi / 2 + 2 * math.pi * i / n), r)
                for i in range(n)]
    if f == "bars":
        slot = Wd * 0.9 / n
        base = Hd * 0.96
        out = []
        for i, h in enumerate(step["heights"]):
            bh = max(4.0, h * Hd * 0.88)
            out.append(_rect(Wd * 0.05 + slot * (i + 0.5), base - bh / 2, slot * 0.72, bh))
        return out
    one = _circle(Wd / 2, Hd / 2, min(Wd, Hd) * 0.3)     # merge: every piece on the same circle
    return [list(one) for _ in range(n)]


def _d(pts):
    return "M" + " L".join("%.1f,%.1f" % p for p in pts) + " Z"


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    Hd = int(math.ceil(Wd * DRAW))
    n = scene.get("n", 16)
    steps = scene["steps"]
    vals = scene.get("values") or [1.0] * n
    col = lambda st: c[st.get("color") or "accent"]
    times, anchors = [], []
    for st in steps:
        t, attrs = ctx.item(st["at"])
        times.append(t)
        anchors.append("<i%s></i>" % attrs)
    for a, b in zip(times, times[1:]):
        if b <= a + 0.3:
            ctx.fail("each step needs its own moment: two steps 0.3 s or less apart")
    shapes = [forms(st, n, Wd, Hd) for st in steps]
    lag = min(0.03, LAG_TOTAL / max(1, n - 1))
    fill0 = col(steps[0])
    paths = "".join('<path class="mo-p" id="%s-p%d" d="%s" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="2"/>'
                    % (sid, i, _d(shapes[0][i]), fill0, vals[i], c["ink"]) for i in range(n))
    js = [SMOOTH]
    for i in range(n):
        js.append(ctx.enter("#%s-p%d" % (sid, i), times[0] + lag * i, {"scale": 0.6}))
    ind = scene.get("indicate")
    t_ind = ctx.at(ind["at"]) if ind else None
    for k in range(1, len(steps)):
        nxt = [t_ for t_ in times[k + 1:k + 2] + ([t_ind] if t_ind is not None else []) if t_ > times[k]]
        gap = (min(nxt) if nxt else ctx.t_out - E.EXIT) - times[k]     # settled before the next step or the indicate
        dur = round(max(MOVE_MIN, min(MOVE, gap - lag * (n - 1) - 0.1)), 2)
        f = col(steps[k])
        for i in range(n):
            op = 1.0 if steps[k]["form"] == "merge" else vals[i]
            js.append("tl.to('#%s-p%d', { attr: { d: '%s' }, fill: '%s', fillOpacity: %s, duration: %s, ease: smoothEase }, %.3f);"
                      % (sid, i, _d(shapes[k][i]), f, ("%.2f" % op).rstrip("0").rstrip("."), dur, times[k] + lag * i))
    labels = []
    for k, st in enumerate(steps):
        if not st.get("label"):
            continue
        labels.append('<div class="mo-label" id="%s-l%d" style="top:%dpx;color:%s">%s</div>'
                      % (sid, k, Hd + 24, c["ink"], ctx.esc(st["label"])))
        js.append(ctx.enter("#%s-l%d" % (sid, k), times[k] + (LABEL_SWAP if k else 0), {"y": 30}))
        nxt = next((j for j in range(k + 1, len(steps)) if steps[j].get("label")), None)
        if nxt is not None:
            js.append("tl.to('#%s-l%d', { opacity: 0, y: -30, duration: %s, ease: 'power3.in' }, %.3f);" % (sid, k, LABEL_SWAP, times[nxt]))
    if ind:
        t, attrs = ctx.item(ind["at"])
        anchors.append("<i%s></i>" % attrs)
        now = max((k for k in range(len(steps)) if times[k] <= t), default=0)
        p = "#%s-p%d" % (sid, ind["piece"])
        js.append("tl.to('%s', { scale: 1.2, fill: '%s', duration: 0.4, ease: 'sine.inOut' }, %.3f);" % (p, c["highlight"]["fill"], t))
        js.append("tl.to('%s', { scale: 1, fill: '%s', duration: 0.4, ease: 'sine.inOut' }, %.3f);" % (p, col(steps[now]), t + 0.4))
    html = ('<div class="mo" id="%s-mo" style="height:%dpx"><svg width="%d" height="%d">%s</svg>%s%s</div>'
            % (sid, height(scene, Wd), Wd, Hd, paths, "".join(labels), "".join(anchors)))
    return html, js
