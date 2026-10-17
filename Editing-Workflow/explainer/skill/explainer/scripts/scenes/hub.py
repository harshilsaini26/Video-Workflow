"""hub: one idea in the middle and two to six around it; each spoke draws and its node lands on its word (PLAYBOOK §E4).
For "the parts of X", "what X connects".

The geometry is computed, never drawn by eye (layout()): the nodes sit on the narrowest ring (a circle, or an ellipse
taller than wide, as a portrait frame allows) where every node clears the middle disc and every other node by GAP, and
the scene is as tall and as wide as that ring needs, so nothing overlaps, crosses a label or leaves the box. Nothing spins; the middle keeps one slow pulse while it holds."""
import math
import explainer_lib as E
from scenes import SLOT, js_obj, need

TYPE = "hub"
DISC = 220                       # the middle disc
GAP = 30                         # the least space between a node and the disc, and between two nodes
C_SIZE, C_ROOM = 52, 190         # the middle label (DM Sans 700) and the room it has inside the disc
N_SIZE, N_H, N_PAD = 44, 88, 30  # a node: label (DM Sans 700, one line), height, padding a side
PAD = 8                          # room above and below the drawing

CSS = """
  .hb { position:relative; width:100%%; }
  .hb svg { position:absolute; left:0; top:0; }
  .hb-pill { position:absolute; height:%dpx; padding:0 %dpx; border-radius:%dpx; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
  .hb-centre { position:absolute; width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center;
    justify-content:center; font-weight:700; font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
""" % (N_H, N_PAD, N_H // 2, N_SIZE, DISC, DISC, C_SIZE)


def validate(scene):
    errs = need(scene, ["center", "items"])
    items = scene.get("items") or []
    if not 2 <= len(items) <= 6:
        errs.append("a hub takes 2 to 6 items (got %d)" % len(items))
    errs += ["item %d has no label" % i for i, it in enumerate(items) if not it.get("label")]
    errs += ["item %d has no at" % i for i, it in enumerate(items) if it.get("at") is None]
    if scene.get("center") and E.text_width(scene["center"], C_SIZE) > C_ROOM:
        errs.append("center %r is too long for the middle disc (about %d px of %d at %d px): one short word"
                    % (scene["center"], E.text_width(scene["center"], C_SIZE), C_ROOM, C_SIZE))
    return errs


def pill_w(label):
    return math.ceil(E.text_width(label, N_SIZE)) + 2 * N_PAD


SHRINK_WIDTH = True    # its width is the ring's geometry, not a word: the composer may shrink it (labels stay over 28 px)
COL = E.L.NARROW["right"] - E.L.NARROW["left"]       # 780: a hub reaches below y 960, so it lives in the narrow column
AREA = E.SCENE["bottom"] - E.SCENE["top"]            # 715


def _fits(cs):
    for i, (x, y, w, h) in enumerate(cs):
        dx, dy = max(abs(x) - w / 2.0, 0), max(abs(y) - h / 2.0, 0)
        if math.hypot(dx, dy) < DISC / 2.0 + GAP:
            return False
        for x2, y2, w2, h2 in cs[:i]:
            if max(abs(x - x2) - (w + w2) / 2.0, abs(y - y2) - (h + h2) / 2.0) < GAP:
                return False
    return True


def _ring(scene):
    """(radius, [(dx, dy, w, h)] node centres from the middle). Node k sits at -90 + 360k/n degrees (the first one
    straight above) on an ellipse: for each height-to-width ratio from a circle up to 2.2, the smallest ring where every
    node clears the disc and every other node by GAP; of those, the one the composer can scale up the most in the
    narrow column (a portrait frame has height to spare, not width)."""
    items = scene["items"]
    n = len(items)
    sizes = [(pill_w(it["label"]), N_H) for it in items]
    angles = [math.radians(-90 + 360.0 * k / n) for k in range(n)]
    best = None
    for q in [1.0 + 0.1 * j for j in range(13)]:
        r = DISC / 2.0 + GAP + N_H / 2.0
        while True:
            cs = [(r * math.cos(a), q * r * math.sin(a), w, h) for a, (w, h) in zip(angles, sizes)]
            if _fits(cs):
                break
            r += 2
        width = 2 * max(abs(x) + w / 2.0 for x, y, w, h in cs)
        height = 2 * max(abs(y) + h / 2.0 for x, y, w, h in cs) + 2 * PAD
        fill = min(COL / width, AREA / height)       # how far the composer can scale it up in the narrow column
        fits = width <= COL and height <= AREA       # a ring that fits unscaled beats one that only fits shrunk
        if best is None or (fits, fill) > (best[0], best[1] + 1e-6):
            best = (fits, fill, r, cs)
    return best[2], best[3]


def _extent(scene):
    r, cs = _ring(scene)
    half_w = max([abs(x) + w / 2.0 for x, y, w, h in cs] + [DISC / 2.0])
    half_h = max([abs(y) + h / 2.0 for x, y, w, h in cs] + [DISC / 2.0])
    return r, cs, half_w, half_h


def height(scene, width):
    return int(math.ceil(2 * _extent(scene)[3])) + 2 * PAD


def min_width(scene):
    return int(math.ceil(2 * _extent(scene)[2])) + 2


def layout(scene, width):
    """([(x, y, w, h)] each node's box, cx, cy) in the scene box of this width."""
    _, cs, _, _ = _extent(scene)
    cx, cy = width / 2.0, height(scene, width) / 2.0
    return [(cx + x - w / 2.0, cy + y - h / 2.0, w, h) for x, y, w, h in cs], cx, cy


def render(scene, ctx, box):
    c, mo = ctx.c, ctx.tokens["motion"]
    sid, items, W = ctx.id, scene["items"], box[2]
    H = height(scene, W)
    nodes, cx, cy = layout(scene, W)
    spokes, pills, js = [], [], []
    for k, (it, (x, y, w, h)) in enumerate(zip(items, nodes)):
        t, attrs = ctx.item(it["at"])
        nx, ny = x + w / 2.0, y + h / 2.0
        a = math.atan2(ny - cy, nx - cx)
        x1, y1 = cx + (DISC / 2.0 + 6) * math.cos(a), cy + (DISC / 2.0 + 6) * math.sin(a)
        length = int(math.ceil(math.hypot(nx - x1, ny - y1)))
        # the spoke runs from the disc's edge to the node's middle; the node, drawn on top, hides its end
        spokes.append('<line id="%s-k%d" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="6" stroke-linecap="round" '
                      'stroke-dasharray="%d" stroke-dashoffset="%d"/>' % (sid, k, x1, y1, nx, ny, c["accent"], length, length))
        pills.append('<div class="hb-pill" id="%s-n%d"%s style="left:%.1fpx;top:%.1fpx;width:%dpx;%s;color:%s"><span class="gt">%s</span></div>'
                     % (sid, k, attrs, x, y, w, ctx.card(), ctx.ink, ctx.esc(it["label"])))
        js += ctx.slot("#%s-n%d" % (sid, k), {"scale": 0.85})     # the empty spot waits as an outline until its word
        js.append("tl.fromTo('#%s-k%d', { strokeDashoffset: %d }, %s, %.3f);"
                  % (sid, k, length, js_obj({"strokeDashoffset": 0, "duration": 0.35, "ease": "power2.out", "immediateRender": False}),
                     max(ctx.t_in, t - 0.2)))
        js.append(ctx.enter("#%s-n%d" % (sid, k), t, {"opacity": SLOT, "scale": 0.85}))
        js.append(ctx.fill("#%s-n%d" % (sid, k), t))
    centre = ('<div class="hb-centre" id="%s-c" style="left:%.1fpx;top:%.1fpx;background:%s;color:%s;box-shadow:0 0 0 14px %s">%s</div>'
              % (sid, cx - DISC / 2.0, cy - DISC / 2.0, c["accent"], c["on_accent"], c["accent_soft"], ctx.esc(scene["center"])))
    js.append(ctx.enter("#%s-c" % sid, ctx.t_in, {"scale": 0.5}))
    ctx.idle("#%s-c" % sid, ctx.t_in + 0.6, ctx.t_out, {"scale": 1.04}, every=1.2)    # the one alive thing while it holds
    html = ('<div class="hb" style="height:%dpx"><svg width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>%s%s</div>'
            % (H, W, H, W, H, "".join(spokes), centre, "".join(pills)))
    return html, js
