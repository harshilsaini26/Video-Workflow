"""hub: one idea in the middle and two to six around it; each spoke draws and its node pops on its word, and the ring
turns slowly while it holds, its labels staying upright (PLAYBOOK §E4). For "the parts of X", "what X connects"."""
import math
import explainer_lib as E
from scenes import GHOST, js_obj, need

TYPE = "hub"
H = 680                          # the scene's height
R = 230                          # node centres from the middle
CENTRE_D = 200                   # the middle disc
C_SIZE, C_ROOM = 44, 176         # the middle label (DM Sans 700) and the room it has inside the disc
N_SIZE, N_H, N_PAD = 36, 76, 26  # a node: label (DM Sans 700, one line), height, padding a side
SPIN = 2.4                       # degrees a second the ring turns

CSS = """
  .hb { position:relative; width:100%%; }
  .hb-ring { position:absolute; inset:0; }
  .hb-ring svg { position:absolute; inset:0; width:100%%; height:100%%; overflow:visible; }
  .hb-pos { position:absolute; width:0; height:0; }
  .hb-node { position:absolute; transform:translate(-50%%, -50%%); }
  .hb-pill { height:%dpx; padding:0 %dpx; border-radius:%dpx; display:flex; align-items:center; font-weight:700; font-size:%dpx;
    line-height:1; white-space:nowrap; opacity:0; }
  .hb-centre { position:absolute; width:%dpx; height:%dpx; margin:-%dpx 0 0 -%dpx; border-radius:50%%; display:flex; align-items:center;
    justify-content:center; font-weight:700; font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
""" % (N_H, N_PAD, N_H // 2, N_SIZE, CENTRE_D, CENTRE_D, CENTRE_D // 2, CENTRE_D // 2, C_SIZE)


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


def height(scene, width):
    return H


def pill_w(label):
    return E.text_width(label, N_SIZE) + 2 * N_PAD


def min_width(scene):
    return 2 * R + int(max(pill_w(it["label"]) for it in scene["items"])) + 20


def render(scene, ctx, box):
    c, mo = ctx.c, ctx.tokens["motion"]
    sid, items, W = ctx.id, scene["items"], box[2]
    acc, face, line = c["accent"], ctx.card(), c["line"]
    cx, cy = W / 2.0, H / 2.0
    n = len(items)
    spokes = ['<circle cx="%.0f" cy="%.0f" r="%d" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="4 10"/>' % (cx, cy, R, line)]
    nodes, js = [], []
    for k, it in enumerate(items):
        t, attrs = ctx.item(it["at"])
        a = math.radians(-90 + 360.0 * k / n)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        x1, y1 = cx + (CENTRE_D / 2.0 + 8) * math.cos(a), cy + (CENTRE_D / 2.0 + 8) * math.sin(a)
        length = int(round(math.hypot(x - x1, y - y1)))
        spokes.append('<line id="%s-k%d" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="5" stroke-linecap="round" '
                      'stroke-dasharray="%d" stroke-dashoffset="%d"/>' % (sid, k, x1, y1, x, y, acc, length, length))
        nodes.append('<div class="hb-pos" style="left:%.1fpx;top:%.1fpx"><div class="hb-node"><div class="hb-pill" id="%s-n%d"%s '
                     'style="%s;color:%s">%s</div></div></div>' % (x, y, sid, k, attrs, face, ctx.ink, ctx.esc(it["label"])))
        js.append("tl.fromTo('#%s-k%d', { strokeDashoffset: %d }, %s, %.3f);"
                  % (sid, k, length, js_obj({"strokeDashoffset": 0, "duration": 0.35, "ease": "power2.out", "immediateRender": False}),
                     max(ctx.t_in, t - 0.2)))
        js.append(ctx.ghost("#%s-n%d" % (sid, k), {"scale": 0.85}))     # the empty spot shows dimmed until its word
        js.append(ctx.enter("#%s-n%d" % (sid, k), t, {"opacity": GHOST, "scale": 0.85}))
    centre = '<div class="hb-centre" id="%s-c" style="left:%.0fpx;top:%.0fpx;background:%s;color:%s;box-shadow:0 0 0 16px %s">%s</div>' % (
        sid, cx, cy, acc, c["on_accent"], c["accent_soft"], ctx.esc(scene["center"]))
    js.append(ctx.enter("#%s-c" % sid, ctx.t_in, {"scale": 0.5}))
    # while it holds: the ring turns slowly (its labels turn back, so they stay upright) and the middle breathes
    dur = round(ctx.t_out - ctx.t_in, 3)
    spin = round(SPIN * dur, 2)
    ctx.ambient("tl.fromTo('#%s-ring', { rotation: 0 }, %s, %.3f);"
                % (sid, js_obj({"rotation": spin, "duration": dur, "ease": "none", "immediateRender": False}), ctx.t_in))
    ctx.ambient("tl.fromTo('#%s .hb-pos', { rotation: 0 }, %s, %.3f);"
                % (sid, js_obj({"rotation": -spin, "duration": dur, "ease": "none", "immediateRender": False}), ctx.t_in))
    ctx.idle("#%s-c" % sid, ctx.t_in + 0.6, ctx.t_out, {"scale": 1.06}, every=1.2)
    html = ('<div class="hb" style="height:%dpx"><div class="hb-ring" id="%s-ring"><svg viewBox="0 0 %d %d">%s</svg>%s</div>%s</div>'
            % (H, sid, W, H, "".join(spokes), "".join(nodes), centre))
    return html, js
