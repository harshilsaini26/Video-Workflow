"""surface: a loss surface, a bowl seen from above and to one side, blue at the bottom and red up the walls; a ball sits
on it and, on a word, steps down hill one gradient step at a time ("gradient descent rolls the weights to the bottom").

  {"type": "surface", "label": "LOSS", "start": [-0.85, 0.75], "descend": {"at": "word:8", "steps": 6}, "lr": 0.18}

The bowl is L = x^2 + 0.7 y^2 + 0.25 x y over the unit disc, projected in Python into a mesh of quads painted back to front
(SVG, no library); `start` is where the ball begins (inside the rim: x^2 + y^2 under 1), `lr` the step size. Each step is the true gradient
step, a tween of the ball on the timeline (seek-safe); a dot marks every place it lands.
"""
import math
from scenes import need

TYPE = "surface"
BAKED = True                    # drawn in Python at the width it is given
DECOR_KEYS = ("start", "descend", "lr")     # where a ball starts and how it steps: geometry, not a claim
ASPECT = 0.8
RINGS, SEGS = 10, 36                        # the round bowl's mesh: rings out from the bottom, segments around
YAW, PITCH = 35, 42                         # the view (degrees)
A, B, C = 1.0, 0.7, 0.25
HOP = 0.45
START = [-0.6, 0.55]
L_SIZE, MAX_LABEL = 34, 16

CSS = """
  .sf { position:relative; width:100%%; }
  .sf svg { position:absolute; left:0; top:0; overflow:visible; }
  .sf-label { position:absolute; left:0; width:100%%; text-align:center; font-family: var(--label); font-weight:500;
    font-size:%dpx; letter-spacing:.1em; line-height:1; opacity:0; }
""" % L_SIZE


def z(x, y):
    return A * x * x + B * y * y + C * x * y


def validate(scene):
    errs = need(scene, ["descend"])
    d = scene.get("descend")
    if not isinstance(d, dict) or d.get("at") is None or not isinstance(d.get("steps"), int) or not 1 <= d["steps"] <= 10:
        errs.append("descend is {at, steps: 1 to 10 steps}")
    st = scene.get("start")
    if st is not None and (not isinstance(st, list) or len(st) != 2 or any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in st)
                           or st[0] ** 2 + st[1] ** 2 > 0.9):
        errs.append("start is [x, y], inside the rim (x^2 + y^2 at most 0.9)")
    lr = scene.get("lr")
    if lr is not None and (not isinstance(lr, (int, float)) or not 0.05 <= lr <= 0.45):
        errs.append("lr is 0.05 to 0.45 (got %r)" % (lr,))
    if scene.get("label") is not None and not 0 < len(str(scene["label"])) <= MAX_LABEL:
        errs.append("label: 1 to %d characters" % MAX_LABEL)
    return errs


def height(scene, width):
    return int(math.ceil(width * ASPECT))


def min_width(scene):
    return 600


def min_text(scene):
    """The smallest text it draws (px), or None: only its label is a word."""
    return L_SIZE if scene.get("label") else None


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    top = (L_SIZE + 30) if scene.get("label") else 10
    yaw, pitch = math.radians(YAW), math.radians(PITCH)
    r = 18

    def raw(x, y):                         # the view at unit scale: (across, down, depth)
        xr, yr = x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw)
        return xr, yr * math.sin(pitch) - z(x, y) * 1.0 * math.cos(pitch), yr

    disc = lambda i, j: (i / float(RINGS) * math.cos(2 * math.pi * j / SEGS), i / float(RINGS) * math.sin(2 * math.pi * j / SEGS))
    edge = [raw(*disc(RINGS, j)) for j in range(SEGS)] + [raw(0, 0)]
    x0, x1 = min(p[0] for p in edge), max(p[0] for p in edge)
    y0, y1 = min(p[1] for p in edge), max(p[1] for p in edge)
    head = 2 * r + 12                      # room above the rim for a ball that starts on it
    k_ = min((Wd - 40) / (x1 - x0), (H - top - head - 10) / (y1 - y0))
    ox, oy = Wd / 2.0 - k_ * (x0 + x1) / 2.0, top + head - k_ * y0

    def proj(x, y):
        a_, b_, d_ = raw(x, y)
        return ox + a_ * k_, oy + b_ * k_, d_

    zmax = max(z(*disc(RINGS, j)) for j in range(SEGS))
    quads = []
    for i in range(RINGS):
        for j in range(SEGS):
            corners = [disc(i, j), disc(i + 1, j), disc(i + 1, j + 1), disc(i, j + 1)]
            pts = [proj(x, y) for x, y in corners]
            h = sum(z(x, y) for x, y in corners) / 4.0 / zmax
            quads.append((sum(p[2] for p in pts) / 4.0, " ".join("%.1f,%.1f" % p[:2] for p in pts), h))
    quads.sort()
    mesh = "".join('<polygon class="sf-q" data-d="%.4f" points="%s" fill="%s" stroke="%s" stroke-opacity="0.3" stroke-width="1"/>'
                   '<polygon points="%s" fill="%s" fill-opacity="%.2f"/>' % (d, p, c["accent"], c["bg"], p, c["bad"], min(0.9, 0.15 + h))
                   for d, p, h in quads)
    x, y = scene.get("start") or START
    lr = scene.get("lr", 0.18)
    path = []
    for _ in range(scene["descend"]["steps"]):
        x, y = x - lr * (2 * A * x + C * y), y - lr * (2 * B * y + C * x)
        path.append((x, y))
    bx, by, _ = proj(*(scene.get("start") or START))
    t, attrs = ctx.item(scene["descend"]["at"])
    trail, js = [], [ctx.enter("#%s-sf" % sid, ctx.t_in, {"scale": 0.94}), ctx.enter("#%s-ball" % sid, ctx.t_in + 0.4, {"scale": 0.5})]
    for k, (px, py) in enumerate(path):
        sx, sy, _ = proj(px, py)
        trail.append('<circle class="sf-trail" data-z="%.4f" id="%s-s%d" cx="%.1f" cy="%.1f" r="6" fill="%s" opacity="0"/>'
                     % (z(px, py), sid, k, sx, sy, c["accent2"]))
        js.append("tl.to('#%s-ball', { x: %.1f, y: %.1f, duration: %.2f, ease: 'power2.inOut' }, %.3f);" % (sid, sx - bx, sy - by, HOP - 0.05, t + k * HOP))
        js.append(ctx.enter("#%s-s%d" % (sid, k), t + k * HOP + HOP - 0.1, dur=0.2))
    ball = ('<g id="%s-ball"><ellipse cx="%.1f" cy="%.1f" rx="%d" ry="%d" fill="%s" fill-opacity="0.35"/>'
            '<circle cx="%.1f" cy="%.1f" r="%d" fill="%s" stroke="%s" stroke-width="5"/></g>'
            % (sid, bx, by + 4, r, r // 3, c["bg"], bx, by - r, r, c["ink"], c["accent2"]))
    label = ('<div class="sf-label" id="%s-lab" style="top:0;color:%s">%s</div>' % (sid, c["dim"], ctx.esc(scene["label"]))
             if scene.get("label") else "")
    if label:
        js.append(ctx.enter("#%s-lab" % sid, ctx.t_in + 0.2, {"y": 10}))
    html = ('<div class="sf" id="%s-sf" style="height:%dpx;aspect-ratio:1 / %s"><svg width="%.0f" height="%d">%s%s%s</svg>%s<i%s></i></div>'
            % (sid, H, ASPECT, Wd, H, mesh, "".join(trail), ball, label, attrs))
    return html, js
