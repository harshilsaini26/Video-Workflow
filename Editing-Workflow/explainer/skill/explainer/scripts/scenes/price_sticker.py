"""price-sticker: what it costs, said like a shop window. A sticker in the accent, turned -6 degrees, with the price in the
look's hero face, slams in on its word from 1.5x (expo.out, no overshoot) while its shadow tightens under it as if it
had just been pressed down; then it breathes a degree either way (sine) for the rest of the scene. A mono label sits
under it, and the creator's product image (any aspect) may stand behind it, the sticker overlapping its lower edge.

  {"type": "price-sticker", "price": "$99", "label": "FOR THE PAIR", "src": "assets/earbuds.png", "at": "word:4",
   "source": "s1"}

A price is a claim: the scene always needs a source (NEEDS_SOURCE). `src` is relative to storyboard.json.
"""
import math, re
import explainer_lib as E
from scenes import js_obj, need

TYPE = "price-sticker"
HERO_CSS = ".ps-price"                # the price, in the look's hero face (E.hero()), measured with its glyphs
NEEDS_SOURCE = True
MAX_SCALE = 1.5
P_SIZE, TRACK = 150, -0.02            # the price: the hero face, line height 1
PAD_X, PAD_Y, SLACK = 56, 34, 10      # the sticker around it; px of room for the browser's rounding
TILT = -6                             # degrees, at rest
BREATH, EVERY = 1, 1.6                # it turns this far either way, this many seconds a swing
L_SIZE, L_LH, L_GAP, L_TRACK = 34, 44, 30, 0.12   # the label: JetBrains Mono 500, one line
IMG_H, OVER = 420, 96                 # the image's area, and how far the sticker overlaps its lower edge
SLAM = 0.45
MAX_PRICE, MAX_LABEL = 8, 28

CSS = """
  .ps { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .ps-pic { width:100%%; height:%dpx; display:flex; align-items:flex-end; justify-content:center; flex:none; }
  .ps-img { display:block; flex:none; opacity:0; object-fit:contain; }
  .ps-wrap { position:relative; z-index:1; display:flex; align-items:center; justify-content:center; flex:none; }
  .ps-st { display:flex; align-items:center; justify-content:center; flex:none; border-radius:28px; opacity:0; }
  .ps-price { font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:%sem; white-space:nowrap; }
  .ps-label { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:%sem; white-space:nowrap;
    margin-top:%dpx; height:%dpx; opacity:0; }
""" % (IMG_H, P_SIZE, P_SIZE, TRACK, L_SIZE, L_LH, L_TRACK, L_GAP, L_LH)


def validate(scene):
    errs = need(scene, ["price", "at"])
    p = str(scene.get("price") or "")
    if p and not re.search(r"\d", p):
        errs.append("price %r has no number in it: a price is a number with its sign ($99, 49 EUR)" % p)
    if len(p) > MAX_PRICE:
        errs.append("price is at most %d characters, so it reads at a glance (got %r)" % (MAX_PRICE, p))
    lab = scene.get("label")
    if lab is not None and (not str(lab).strip() or len(str(lab)) > MAX_LABEL):
        errs.append("label is one short line, at most %d characters (got %r)" % (MAX_LABEL, lab))
    if scene.get("src") is not None and not str(scene["src"]).strip():
        errs.append("src is the product image's path (relative to storyboard.json)")
    return errs


def sticker(scene):
    """The sticker (w, h), and the box its -6 degree turn needs (bw, bh)."""
    w = int(math.ceil(E.text_width(str(scene["price"]), P_SIZE, E.hero()["glyphs"], spacing=TRACK))) + 2 * PAD_X + SLACK
    h = P_SIZE + 2 * PAD_Y
    a = math.radians(abs(TILT) + BREATH)
    return w, h, int(math.ceil(w * math.cos(a) + h * math.sin(a))) + 2, int(math.ceil(w * math.sin(a) + h * math.cos(a))) + 2


def _label_w(scene):
    return int(math.ceil(len(str(scene.get("label") or "")) * L_SIZE * (0.6 + L_TRACK))) + 4


def height(scene, width):
    h = sticker(scene)[3]
    if scene.get("src"):
        h += IMG_H - OVER
    if scene.get("label"):
        h += L_GAP + L_LH
    return h


def min_width(scene):
    return max(sticker(scene)[2], _label_w(scene) if scene.get("label") else 0)


def render(scene, ctx, box):
    c, sid, mo = ctx.c, ctx.id, ctx.tokens["motion"]
    W = box[2]
    w, h, bw, bh = sticker(scene)
    t, attrs = ctx.item(scene["at"])
    html, js = [], []
    if scene.get("src"):
        page, iw, ih = ctx.image(scene["src"])
        k = min(W / float(iw), IMG_H / float(ih))            # any aspect fits the area, never cropped
        dw, dh = max(1, int(math.floor(iw * k))), max(1, int(math.floor(ih * k)))
        shade = re.search(r"rgba\([^)]*\)", c["shadow"]).group(0)
        html.append('<div class="ps-pic"><img class="ps-img" id="%s-img" src="%s" alt="" style="width:%dpx;height:%dpx;filter:drop-shadow(0 22px 28px %s)">'
                    '</div>' % (sid, ctx.esc(page), dw, dh, shade))
        js.append(ctx.enter("#%s-img" % sid, ctx.t_in, {"y": 30}))
    shade = re.search(r"rgba\([^)]*\)", c["shadow"]).group(0)
    far, near = "0 64px 72px %s" % shade, "0 14px 22px %s" % shade
    html.append('<div class="ps-wrap" style="width:%dpx;height:%dpx%s"><div class="ps-st" id="%s-st"%s style="width:%dpx;height:%dpx;background:%s;'
                'box-shadow:%s"><span class="ps-price" id="%s-pr" style="color:%s">%s</span></div></div>'
                % (bw, bh, ";margin-top:-%dpx" % OVER if scene.get("src") else "", sid, attrs, w, h, c["accent"], near, sid,
                   c["on_accent"], ctx.esc(scene["price"])))
    # turned from the start; on its word it drops from 1.5x onto the page, the shadow closing in as it lands
    js.append("tl.set('#%s-st', %s, 0);" % (sid, js_obj({"rotation": TILT})))
    js.append("tl.fromTo('#%s-st', %s, %s, %.3f);" % (sid, js_obj({"opacity": 0, "scale": 1.5, "boxShadow": far}),
                                                     js_obj({"opacity": 1, "scale": 1, "boxShadow": near, "duration": SLAM, "ease": "expo.out",
                                                             "immediateRender": False}), t))
    if scene.get("label"):
        html.append('<div class="ps-label" id="%s-lb" style="color:%s">%s</div>' % (sid, ctx.ink, ctx.esc(scene["label"])))
        js.append(ctx.enter("#%s-lb" % sid, t + 0.2, {"y": 16}))
    # then it breathes, a degree either way of its tilt, to the scene's end
    k, at = 0, t + SLAM
    while at + EVERY <= ctx.t_out + 1e-6:
        ctx.ambient("tl.to('#%s-st', %s, %.3f);" % (sid, js_obj({"rotation": TILT + (BREATH if k % 2 == 0 else -BREATH), "duration": EVERY,
                                                                 "ease": "sine.inOut"}), at))
        k, at = k + 1, at + EVERY
    return '<div class="ps">%s</div>' % "".join(html), js
