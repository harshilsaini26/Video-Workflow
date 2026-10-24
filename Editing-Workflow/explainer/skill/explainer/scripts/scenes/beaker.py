"""beaker: a glass that fills in layers, each on its word, labelled beside it (how a deal is paid for: 60% debt, 40%
equity; what a price is made of).

  {"type": "beaker", "layers": [{"label": "DEBT", "value": 60, "at": "word:6"}, {"label": "EQUITY", "value": 40, "at": "word:9"}],
   "source": "s1"}

1 to 4 layers from the bottom up; each `value` is its share of the glass (they add up to 100 at most); `text` shows
instead of "<value>%". A cylinder drawn in 2.5D (an elliptical rim and surface on each layer); each layer grows from its
own floor with a tween on the timeline (seek-safe); the labels sit flat to the right, never on the glass.
"""
import explainer_lib as E
from scenes import need

TYPE = "beaker"
NEEDS_SOURCE = True
ASPECT = 0.85
GLASS = (0.14, 0.36, 0.12, 0.7)        # left, width (shares of the scene's width); top, height (shares of its height)
RIM = 0.26                             # the rim's ellipse, a share of the glass's width
L_SIZE, V_SIZE, L_GAP = 40, 34, 14     # a layer's label and its value (DM Sans 700); between two labels
MAX_LABEL, MAX_TEXT = 10, 8

CSS = """
  .bk { position:relative; width:100%%; opacity:0; }
  .bk-body, .bk-liq, .bk-out, .bk-rim { position:absolute; }
  .bk-layer { position:absolute; left:0; width:100%%; transform-origin:50%% 100%%; }
  .bk-top { position:absolute; left:0; width:100%%; border-radius:50%%; filter:brightness(1.16); }
  .bk-l { position:absolute; white-space:nowrap; opacity:0; }
  .bk-l b { display:block; font-weight:700; font-size:%dpx; line-height:1.1; }
  .bk-l span { display:block; font-weight:700; font-size:%dpx; line-height:1.1; font-variant-numeric: tabular-nums; }
""" % (L_SIZE, V_SIZE)


def validate(scene):
    errs = need(scene, ["layers"])
    layers = scene.get("layers") or []
    if not 1 <= len(layers) <= 4:
        errs.append("a beaker takes 1 to 4 layers (got %d)" % len(layers))
    for i, l in enumerate(layers):
        if not isinstance(l, dict):
            errs.append("layer %d is {label, value, at}" % i)
            continue
        if not l.get("label") or len(str(l["label"])) > MAX_LABEL:
            errs.append("layer %d label: 1 to %d characters" % (i, MAX_LABEL))
        v = l.get("value")
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            errs.append("layer %d value %r must be a number > 0 (its share of the glass)" % (i, v))
        if l.get("text") is not None and not 0 < len(str(l["text"])) <= MAX_TEXT:
            errs.append("layer %d text: 1 to %d characters" % (i, MAX_TEXT))
        if l.get("at") is None:
            errs.append("layer %d has no at" % i)
    if layers and not errs and sum(l["value"] for l in layers) > 100 + 1e-9:
        errs.append("the layers add up to %g: a glass holds 100 at most" % sum(l["value"] for l in layers))
    return errs




def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    gx, G, gy, Hg = Wd * GLASS[0], Wd * GLASS[1], H * GLASS[2], H * GLASS[3]
    e = G * RIM
    top = gy + e / 2.0                       # the body's top edge (the rim's middle)
    curve = "border-bottom-left-radius:50%% %.1fpx;border-bottom-right-radius:50%% %.1fpx;" % (e / 2, e / 2)
    layers, labels, js = [], [], [ctx.enter("#%s-bk" % sid, ctx.t_in, {"scale": 0.92, "y": 30})]
    floor, mids = 0.0, []
    for i, l in enumerate(scene["layers"]):
        t, attrs = ctx.item(l["at"])
        h = round(Hg * 0.9 * l["value"] / 100.0, 1)
        fill = c["series"][i % len(c["series"])][0]
        layers.append('<div class="bk-layer" id="%s-k%d" data-h="%s"%s style="bottom:%.1fpx;height:%.1fpx;background:%s;%s">'
                      '<div class="bk-top" style="top:%.1fpx;height:%.1fpx;background:%s"></div></div>'
                      % (sid, i, h, attrs, floor, h, fill, curve if i == 0 else "", -e / 2, e, fill))
        js.append("tl.fromTo('#%s-k%d', { scaleY: 0 }, { scaleY: 1, duration: 0.8, ease: '%s', immediateRender: false }, %.3f);"
                  % (sid, i, ctx.tokens["motion"]["enter_ease"], t))
        mids.append([top + Hg - floor - h / 2.0, i, t, attrs])
        floor += h
    lh = L_SIZE * 1.1 + V_SIZE * 1.1
    placed = []
    for m in sorted(mids, key=lambda m: -m[0]):         # bottom up: a label never sits on the one under it
        y = m[0] - lh / 2.0
        if placed and y + lh + L_GAP > placed[-1]:
            y = placed[-1] - lh - L_GAP
        placed.append(y)
        l = scene["layers"][m[1]]
        labels.append('<div class="bk-l" id="%s-l%d" style="left:%.1fpx;top:%.1fpx;color:%s"><b>%s</b><span style="color:%s">%s</span></div>'
                      % (sid, m[1], gx + G + 44, y, ctx.ink, ctx.esc(l["label"]), c["dim"], ctx.esc(l.get("text", "%g%%" % l["value"]))))
        js.append(ctx.enter("#%s-l%d" % (sid, m[1]), m[2] + 0.3, {"x": -16}))
    glass = ('<div class="bk-body" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;background:%s;%s"></div>'
             '<div class="bk-liq" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx">%s</div>'
             '<div class="bk-out" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;box-shadow:inset 0 0 0 5px %s;%s"></div>'
             '<div class="bk-rim" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:50%%;box-shadow:inset 0 0 0 5px %s"></div>'
             % (gx, top, G, Hg, c["track"], curve, gx, top, G, Hg, "".join(layers), gx, top, G, Hg, c["line"], curve,
                gx, gy, G, e, c["line"]))
    html = '<div class="bk" id="%s-bk" style="aspect-ratio:1 / %s">%s%s</div>' % (sid, ASPECT, glass, "".join(labels))
    last = max(ctx.at(l["at"]) for l in scene["layers"])
    ctx.idle("#%s-bk" % sid, last + 1.0, ctx.t_out - E.EXIT - 0.2, {"y": -8}, every=2.4)
    return html, js
