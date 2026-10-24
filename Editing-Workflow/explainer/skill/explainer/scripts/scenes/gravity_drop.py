"""gravity-drop: words or chips fall from above and land in a pile, the first at the bottom, each on its own word. For
a heap of things that add up: "Excel, then accounting, then valuation, then the models".

  {"type": "gravity-drop", "style": "chips", "items": [{"text": "Excel", "at": "word:2"}, {"text": "Accounting", "at": ...}]}

The motion is physics, not an overshoot ease: each piece falls under gravity (power2.in: from rest, speeding up), hits,
and rebounds twice, each rebound a short power2.out rise and a power2.in fall, smaller than the last. A piece dropped from
higher falls for longer (the time goes with the square root of the height). It lands slightly tilted, as a heap does,
and the newest one wears the accent. `style` "chips" (the default) puts each on a card; "words" drops bare big type.

The pile is laid out here, row by row from the bottom, for the width it is given (BAKED: measured at that width).
"""
import math
import explainer_lib as E
from scenes import js_obj, need

TYPE = "gravity-drop"
BAKED = True                         # the rows are worked out for the width it is given
STYLES = {
    #          size, row height, padding a side, gap across, gap between rows, border, letter-spacing
    "chips": dict(size=50, h=100, pad=34, gx=16, gy=16, border=3, track=0.0),
    "words": dict(size=96, h=110, pad=0, gx=34, gy=4, border=0, track=-0.02),
}
TILT = [-2.4, 1.8, -1.2, 2.6, -1.9, 1.3, -2.2, 0.9]     # degrees: a heap never lands square
GRAVITY = 6200.0                     # px/s^2 in the scene's own pixels: a 600 px drop takes 0.44 s
LIFT = 40                            # every piece starts this far above the top of the box
MAX_ITEMS = 8
ROOM = 10                            # kept clear at each side: a piece lands tilted, and the camera turns the scene

CSS = """
  .gd { position:relative; width:100%%; }
  .gd-p { position:absolute; display:flex; align-items:center; justify-content:center; white-space:nowrap; font-weight:700;
    line-height:1; opacity:0; will-change:transform; }
  .gd-chip { border-radius:22px; border-style:solid; font-size:%dpx; }
  .gd-word { font-size:%dpx; }
""" % (STYLES["chips"]["size"], STYLES["words"]["size"])


def style(scene):
    return STYLES.get(scene.get("style") or "chips", STYLES["chips"])


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items") or []
    if not isinstance(items, list):
        return errs + ["items is a list of {text, at}"]
    if not 2 <= len(items) <= MAX_ITEMS:
        errs.append("a gravity-drop takes 2 to %d items (got %d)" % (MAX_ITEMS, len(items)))
    if (scene.get("style") or "chips") not in STYLES:
        errs.append("style is one of %s (got %r)" % (", ".join(sorted(STYLES)), scene.get("style")))
    for i, it in enumerate(items):
        if not isinstance(it, dict) or not str(it.get("text") or "").strip():
            errs.append("item %d has no text" % i)
        elif len(str(it["text"]).split()) > 3:
            errs.append("item %d: at most three words on a piece (got %r)" % (i, it["text"]))
        if not isinstance(it, dict) or it.get("at") is None:
            errs.append("item %d has no at" % i)
    return errs


def piece_w(text, st):
    return int(math.ceil(E.text_width(text, st["size"], spacing=st["track"]))) + 2 * (st["pad"] + st["border"]) + 4


def layout(scene, width):
    """[(left, top, w)] for each item, and the box height. The items fill rows from the bottom in time order (a later
    piece never lands under an earlier one, so nothing falls through the pile), each row centred. Of the ways to break
    them into rows that fit, the fewest rows win, then the one that reads most like a heap: each row no wider than the
    one under it, as far as the order allows."""
    st = style(scene)
    ws = [piece_w(it["text"], st) for it in scene["items"]]
    n = len(ws)
    span = lambda a, b: sum(ws[a:b]) + st["gx"] * (b - a - 1)
    width = width - 2 * ROOM
    best = None
    for mask in range(1 << (n - 1)):          # bit k set: a new row starts after item k (at most 8 items: 128 ways)
        cuts = [0] + [k + 1 for k in range(n - 1) if mask >> k & 1] + [n]
        widths = [span(a, b) for a, b in zip(cuts, cuts[1:])]
        if any(w > width for w, (a, b) in zip(widths, zip(cuts, cuts[1:])) if b - a > 1):
            continue
        over = sum(max(0, hi - lo) for lo, hi in zip(widths, widths[1:]))     # how far a row overhangs the one under it
        key = (len(widths), over, [-w for w in widths])
        if best is None or key < best[0]:
            best = (key, cuts)
    cuts = best[1]
    rows = [[(i, ws[i]) for i in range(a, b)] for a, b in zip(cuts, cuts[1:])]
    h = len(rows) * st["h"] + (len(rows) - 1) * st["gy"]
    out = [None] * len(scene["items"])
    for r, row in enumerate(rows):
        total = sum(w for _, w in row) + st["gx"] * (len(row) - 1)
        left = ROOM + (width - total) / 2.0
        top = h - st["h"] - r * (st["h"] + st["gy"])
        for i, w in row:
            out[i] = (int(round(left)), top, w)
            left += w + st["gx"]
    return out, h


def height(scene, width):
    return layout(scene, width)[1]


def min_width(scene):
    st = style(scene)
    return max(piece_w(it["text"], st) for it in scene["items"]) + 2 * ROOM


def fall(t, drop):
    """The tweens of one landing: (start, duration, y, ease) from rest at -drop, two rebounds, each smaller."""
    d = math.sqrt(2.0 * drop / GRAVITY)
    h1 = max(14.0, min(44.0, 0.065 * drop))
    h2 = 0.3 * h1
    u1, u2 = math.sqrt(2.0 * h1 / GRAVITY), math.sqrt(2.0 * h2 / GRAVITY)
    return [(t, d, 0, "power2.in"),
            (t + d, u1, -h1, "power2.out"), (t + d + u1, u1, 0, "power2.in"),
            (t + d + 2 * u1, u2, -h2, "power2.out"), (t + d + 2 * u1 + u2, u2, 0, "power2.in")]


def render(scene, ctx, box):
    c, mo, sid = ctx.c, ctx.tokens["motion"], ctx.id
    name = scene.get("style") or "chips"
    st = STYLES[name]
    places, h = layout(scene, box[2])
    rest_col, acc = (c["line"], c["accent"]) if name == "chips" else (ctx.ink, c["accent"])
    parts, js, prev, last_t = [], [], None, None
    for i, it in enumerate(scene["items"]):
        t, attrs = ctx.item(it["at"])
        if last_t is not None and t < last_t - 1e-6:
            ctx.fail("item %d lands before item %d: a pile builds in order (anchor the items in time order)" % (i, i - 1))
        last_t = t
        left, top, w = places[i]
        sel = "#%s-p%d" % (sid, i)
        tilt = TILT[i % len(TILT)] * (1.0 if name == "chips" else 0.7)
        if name == "chips":
            look = "%s;border-width:%dpx;border-color:%s;color:%s;padding:0 %dpx" % (ctx.card(), st["border"], rest_col, ctx.ink, st["pad"])
            cls = "gd-chip"
        else:
            look = "color:%s;letter-spacing:%sem" % (ctx.ink, st["track"])
            cls = "gd-word"
        parts.append('<div class="gd-p %s" id="%s-p%d"%s style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;%s">%s</div>'
                     % (cls, sid, i, attrs, left, top, w, st["h"], look, ctx.esc(it["text"])))
        drop = top + st["h"] + LIFT                       # from just above the box to its place in the pile
        js.append("tl.fromTo('%s', { opacity: 0 }, %s, %.3f);" % (sel, js_obj({"opacity": 1, "duration": 0.12, "ease": mo["enter_ease"],
                                                                                "immediateRender": False}), t))
        for k, (t0, dur, y, ease) in enumerate(fall(t, drop)):
            if k == 0:
                js.append("tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj({"y": -drop, "rotation": round(tilt * 2.2, 2)}),
                                                              js_obj({"y": 0, "rotation": round(tilt * 2.2, 2), "duration": round(dur, 3),
                                                                      "ease": ease, "immediateRender": False}), t0))
            else:     # the first rebound settles the tilt
                props = {"y": round(y, 2), "duration": round(dur, 3), "ease": ease}
                if k == 1:
                    props = dict(props, rotation=tilt)
                js.append("tl.to('%s', %s, %.3f);" % (sel, js_obj(props), t0))
        land = fall(t, drop)[1][0]                         # the newest piece wears the accent from its impact
        key = "borderColor" if name == "chips" else "color"
        js.append("tl.to('%s', %s, %.3f);" % (sel, js_obj({key: acc, "duration": 0.25, "ease": mo["enter_ease"]}), land))
        if prev is not None:
            js.append("tl.to('%s', %s, %.3f);" % (prev, js_obj({key: rest_col, "duration": 0.3, "ease": mo["enter_ease"]}), land))
        prev = sel
    return '<div class="gd" style="height:%dpx">%s</div>' % (h, "".join(parts)), js
