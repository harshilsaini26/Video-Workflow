"""bars-3d: a 3D bar chart on a tilted floor; each bar rises on its word (LBO, MERGER, a three-statement model).

  {"type": "bars-3d", "bars": [{"label": "MERGER", "value": 60, "at": "word:6"}, {"label": "LBO", "value": 100, "at": "word:8"}],
   "floor": "THREE-STATEMENT MODEL"}

2 to 4 bars; `text` shows instead of the value above a bar, `hi` gives a bar the accent (else the tallest has it), and
`floor` is a caption under the floor. CSS 3D, orthographic: each bar is three shaded faces (top, front, side) whose height is
a CSS variable tweened on the timeline, so any frame can be sought; the labels sit flat over the 3D, where they were
projected, so gate E5 reads them.
"""
import math
import explainer_lib as E
from scenes import need

TYPE = "bars-3d"
NEEDS_SOURCE = True
ASPECT = 0.85                  # the scene's height, a share of its width
FLOOR, TILT, TURN = 0.6, 58, -40         # the floor's side (a share of the width), its tilt and turn (degrees)
H_MAX = 0.6                              # the tallest bar, a share of the scene's height (shorter if the labels need it)
L_SIZE, V_SIZE, F_SIZE = 34, 28, 30      # a bar's label, its value (DM Sans 700) and the floor's caption (the label face)
L_GAP = 18                               # between a label and whatever is under it
MAX_LABEL = 10
MAX_FLOOR = 24                           # a short caption under the floor

CSS = """
  .b3 { position:relative; width:100%%; }
  .b3-floor { position:absolute; transform-style:preserve-3d; border-radius:28px; opacity:0; }
  .b3-box { position:absolute; transform-style:preserve-3d; --h:0; }
  .b3-f { position:absolute; }
  .b3-top { left:0; top:0; width:100%%; height:100%%; transform:translateZ(calc(var(--h) * 1px)); filter:brightness(1.18); }
  .b3-s { left:0; top:100%%; width:100%%; height:calc(var(--h) * 1px); transform-origin:top; transform:rotateX(90deg); }
  .b3-e { left:100%%; top:0; width:calc(var(--h) * 1px); height:100%%; transform-origin:left; transform:rotateY(-90deg); filter:brightness(.78); }
  .b3-cap { position:absolute; left:0; right:0; text-align:center; font-family: var(--label); font-weight:500;
    letter-spacing:.06em; white-space:nowrap; opacity:0; }
  .b3-labels { position:absolute; left:0; top:0; width:100%%; height:100%%; pointer-events:none; }
  .b3-l { position:absolute; text-align:center; white-space:nowrap; opacity:0; }
  .b3-l b { display:block; font-weight:700; line-height:1.1; }
  .b3-l span { display:block; font-weight:700; font-size:%dpx; line-height:1.1; font-variant-numeric: tabular-nums; }
""" % V_SIZE


def validate(scene):
    errs = need(scene, ["bars"])
    bars = scene.get("bars") or []
    if not 2 <= len(bars) <= 4:
        errs.append("bars-3d takes 2 to 4 bars (got %d): their labels need the room" % len(bars))
    for i, b in enumerate(bars):
        if not b.get("label"):
            errs.append("bar %d has no label" % i)
        elif len(str(b["label"])) > MAX_LABEL:
            errs.append("bar %d label %r: at most %d characters" % (i, b["label"], MAX_LABEL))
        v = b.get("value")
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0:
            errs.append("bar %d value %r must be a number >= 0" % (i, v))
        if b.get("at") is None:
            errs.append("bar %d has no at" % i)
    if bars and not errs and max(b["value"] for b in bars) <= 0:
        errs.append("at least one value must be above 0")
    if scene.get("floor") is not None and not 0 < len(str(scene["floor"])) <= MAX_FLOOR:
        errs.append("floor is a short caption, 1 to %d characters (it sits under the floor)" % MAX_FLOOR)
    return errs



def _need(scene, size):
    """The width at which neighbouring labels at `size` px stand clear of each other (bars sit 0.43 W apart in all)."""
    bars = scene["bars"]
    w = [max(E.text_width(str(b["label"]), size), E.text_width(str(b.get("text", "")), V_SIZE)) for b in bars]
    pair = max((a + b) / 2.0 for a, b in zip(w, w[1:])) + 12
    return (len(bars) - 1) * pair / (FLOOR * 0.72)


def label_size(scene):
    """The labels' size: L_SIZE, or smaller (to 28 px, the smallest text) when even the narrow column (780 px) is too narrow."""
    return next((s for s in range(L_SIZE, 27, -2) if _need(scene, s) <= 780), 28)


def min_width(scene):
    return int(max(600, min(780, _need(scene, label_size(scene)))))   # the narrow column: every scene must fit it


def project(x, y, z):
    """A point on the floor (relative to its centre, z up) as it lands on the screen: turned, then tilted (orthographic)."""
    t, a = math.radians(TURN), math.radians(TILT)
    x1, y1 = x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)
    return x1, y1 * math.cos(a) - z * math.sin(a)


def layout(scene, W):
    """Where everything goes, for a scene `W` wide: (floor side, centre, bar side, [(x, y, h) on the floor], [label box]).
    A label sits above its bar, lifted above any bar or label under it (so none crosses another); if the labels would
    leave the top of the scene, every bar is drawn shorter until they fit."""
    H = height(scene, W)
    size = label_size(scene)
    F = W * FLOOR
    front = max(project(a * F / 2.0, b * F / 2.0, 0)[1] for a in (-1, 1) for b in (-1, 1))   # the floor's front corner
    cx, cy = W / 2.0, H - front - (F_SIZE + 34 if scene.get("floor") else 12)     # the floor (and its caption) at the foot
    bars = scene["bars"]
    n = len(bars)
    top = max(b["value"] for b in bars)
    side = min(F / float(n) * 0.6, F * 0.22)
    ux, uy = math.cos(math.radians(-TURN)), math.sin(math.radians(-TURN))
    span = F * 0.36
    tall = H * H_MAX
    for _ in range(12):
        boxes, labels = [], []
        for i, b in enumerate(bars):
            k = (i - (n - 1) / 2.0) / max(1, (n - 1) / 2.0) * span
            x, y = F / 2.0 + k * ux - side / 2.0, F / 2.0 + k * uy - side / 2.0
            h = round(tall * b["value"] / float(top), 1)
            px, py = project(x + side / 2.0 - F / 2.0, y + side / 2.0 - F / 2.0, h)
            boxes.append((x, y, h, cx + px, cy + py - side * 0.75))      # on the floor; the top's screen centre and top edge
        for i, b in enumerate(bars):
            lines = [(str(b["label"]), size)] + ([(str(b.get("text", b["value"])), V_SIZE)] if b.get("text") else [])
            lw = max(E.text_width(t_, sz) for t_, sz in lines)
            lh = sum(sz * 1.1 for _, sz in lines)
            x0, x1 = boxes[i][3] - lw / 2.0, boxes[i][3] + lw / 2.0
            under = [bx[4] for bx in boxes if abs(bx[3] - boxes[i][3]) < lw / 2.0 + side * 0.8]
            labels.append([x0, x1, min(under) - L_GAP, lh])
        placed = []
        for i in sorted(range(n), key=lambda i: -labels[i][2]):          # the lowest first; a later one goes above
            x0, x1, bottom, lh = labels[i]
            for o in sorted(placed, key=lambda o: -o[2]):
                if x0 < o[1] + 12 and o[0] < x1 + 12 and bottom > o[2] - o[3] - L_GAP:
                    bottom = o[2] - o[3] - L_GAP
            labels[i][2] = bottom
            placed.append(labels[i])
        if min(l[2] - l[3] for l in labels) >= H * 0.04:       # clear of the top, with room for the float and the scale
            break
        tall *= 0.88
    return F, (cx, cy), side, [(x, y, h) for x, y, h, _, _ in boxes], [(l[0], l[2] - l[3], l[1] - l[0]) for l in labels], size


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    W = box[2]
    F, (cx, cy), side, boxes, labs, size = layout(scene, W)
    bars = scene["bars"]
    n = len(bars)
    hi = next((i for i, b in enumerate(bars) if b.get("hi")), max(range(n), key=lambda i: bars[i]["value"]))
    floor, labels, js = [], [], [ctx.enter("#%s-floor" % sid, ctx.t_in, {"scale": 0.9})]
    rest = [f for f, _ in c["series"] if f != c["fill"]] or [c["series"][0][0]]
    t = ctx.t_in
    for i, b in enumerate(bars):
        t, attrs = ctx.item(b["at"])
        x, y, h = boxes[i]
        col = c["fill"] if i == hi else rest[i % len(rest)]
        faces = "".join('<div class="b3-f b3-%s" style="background:%s"></div>' % (f, col) for f in ("top", "s", "e"))
        floor.append('<div class="b3-box" id="%s-b%d"%s data-h="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</div>'
                     % (sid, i, attrs, h, x, y, side, side, faces))
        js.append("tl.fromTo('#%s-b%d', { '--h': 0 }, { '--h': %s, duration: 0.7, ease: '%s', immediateRender: false }, %.3f);"
                  % (sid, i, h, ctx.tokens["motion"]["enter_ease"], t + 0.08))
        lx, ly, lw = labs[i]
        value = '<span style="color:%s">%s</span>' % (c["dim"], ctx.esc(b["text"])) if b.get("text") else ""
        labels.append('<div class="b3-l" id="%s-l%d" style="left:%dpx;top:%dpx;width:%dpx;color:%s"><b style="font-size:%dpx">%s</b>%s</div>'
                      % (sid, i, lx, ly, lw + 2, ctx.ink, size, ctx.esc(b["label"]), value))
        js.append(ctx.enter("#%s-l%d" % (sid, i), t + 0.45, {"y": 16}))
    floor_bottom = cy + max(project(a * F / 2.0, b * F / 2.0, 0)[1] for a in (-1, 1) for b in (-1, 1))
    cap = ('<div class="b3-cap" id="%s-cap" style="top:%dpx;font-size:%dpx;color:%s">%s</div>' % (sid, floor_bottom + 22, F_SIZE, c["dim"], ctx.esc(scene["floor"]))
           if scene.get("floor") else "")
    if cap:
        js.append(ctx.enter("#%s-cap" % sid, ctx.t_in + 0.25, {"y": 12}))
    html = ('<div class="b3" id="%s-3d" style="aspect-ratio:1 / %s"><div class="b3-floor" id="%s-floor" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;'
            'background:%s;box-shadow:inset 0 0 0 3px %s;transform:rotateX(%ddeg) rotateZ(%ddeg)">%s</div><div class="b3-labels">%s%s</div></div>'
            % (sid, ASPECT, sid, cx - F / 2.0, cy - F / 2.0, F, F, c["track"], c["line"], TILT, TURN, "".join(floor), "".join(labels), cap))
    ctx.idle("#%s-3d" % sid, max(t + 0.8, ctx.t_in + 0.8), ctx.t_out - E.EXIT - 0.2, {"y": -10}, every=2.4)
    return html, js
