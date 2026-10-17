"""stack: two to five slabs drop onto a pile, the first at the bottom, each on its word; the pile bobs while it holds
(PLAYBOOK §E4). For things that build on each other: "time value, then risk, then the cost of capital"."""
import explainer_lib as E
from scenes import SLOT, js_obj, need

TYPE = "stack"
SLAB, GAP, THICK = 92, 14, 14    # a slab, the gap between two, the bottom slab's thickness shadow
STEP = 44                        # each slab is this much narrower than the one under it
PAD, SIZE = 30, 44               # label: DM Sans 700, one line

CSS = """
  .sk { position:relative; width:100%%; }
  .sk-slab { position:absolute; height:%dpx; border-radius:18px; display:flex; align-items:center; justify-content:center;
    padding:0 %dpx; font-weight:700; font-size:%dpx; line-height:1; letter-spacing:.01em; white-space:nowrap; opacity:0; }
""" % (SLAB, PAD, SIZE)


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items") or []
    if not 2 <= len(items) <= 5:
        errs.append("a stack takes 2 to 5 items (got %d)" % len(items))
    errs += ["item %d has no label" % i for i, it in enumerate(items) if not it.get("label")]
    errs += ["item %d has no at" % i for i, it in enumerate(items) if it.get("at") is None]
    return errs


def height(scene, width):
    n = len(scene["items"])
    return n * SLAB + (n - 1) * GAP + THICK


def min_width(scene):
    return max(int(E.text_width(it["label"], SIZE)) + 1 + 2 * PAD + i * STEP for i, it in enumerate(scene["items"]))


def render(scene, ctx, box):
    sid, items = ctx.id, scene["items"]
    h = height(scene, box[2])
    parts, js = [], []
    for i, it in enumerate(items):
        t, attrs = ctx.item(it["at"])
        fill, ink = ctx.c["series"][i % len(ctx.c["series"])]     # the theme's series: fill and the text on it
        edge = E.rgba(ctx.c["ink"], 0.28)                          # the slab's thickness: a darker ledge under it
        top = h - THICK - SLAB - i * (SLAB + GAP)
        parts.append('<div class="sk-slab" id="%s-s%d"%s style="top:%dpx;left:%dpx;right:%dpx;background:%s;color:%s;'
                     'box-shadow:0 %dpx 0 %s, %s"><span class="gt">%s</span></div>'
                     % (sid, i, attrs, top, i * STEP // 2, i * STEP // 2, fill, ink, THICK, edge, ctx.c["shadow"], ctx.esc(it["label"])))
        js += ctx.slot("#%s-s%d" % (sid, i))
        js.append("tl.fromTo('#%s-s%d', %s, %s, %.3f);"
                  % (sid, i, js_obj({"opacity": SLOT, "y": -240}), js_obj({"opacity": 1, "y": 0, "duration": 0.55, "ease": "expo.out", "immediateRender": False}), t))
        js.append(ctx.fill("#%s-s%d" % (sid, i), t))
    ctx.idle("#%s .sk" % sid, ctx.t_in + 0.6, ctx.t_out, {"y": -10})
    return '<div class="sk" style="height:%dpx">%s</div>' % (h, "".join(parts)), js
