"""photo-grid: one to four of the creator's photos, each credited, as the editorial reels lay them out. The photos slide
in one by one on their words (expo.out; 0.12 s apart when they share a word or have none), with rounded corners
(24 px) and a soft shadow; each drifts a few pixels while the grid holds and its picture pushes in slowly, so nothing
is still. A credit chip (JetBrains Mono 28 px, the paper on the ink at 0.8, letter-spacing .06em) sits bottom-left
inside each photo; an optional tag chip (a word or two) top-left. Notes (scenes/_annotate.py) mark the first photo.

  {"type": "photo-grid", "layout": "grid",
   "photos": [{"src": "assets/before.jpg", "credit": "Photo: J. Rivera", "tag": "BEFORE", "at": "word:3"},
              {"src": "assets/after.jpg", "credit": "stand-in image", "tag": "AFTER", "at": "word:6"}],
   "notes": [{"x": 0.3, "y": 0.4, "label": "THE PLUG", "at": "word:8", "mark": "circle", "side": "right"}]}

Every photo needs its credit (who took it, or "stand-in image"): E3 names a photo without one, and one whose credit
is wider than its photo. A photo's `at` lands it on its word; without one it follows the photo before it.

The layouts keep fixed proportions (the picture is cropped to them: object-fit cover), sized for the width the scene
is given (BAKED; never scaled, so the chips stay 28 px):
  stack    1 to 3 photos in one column, full width: 4:3 for one, 2.3:1 for two, 3.5:1 for three
  grid     1 to 4 photos, two columns of 4:3 cells (one photo takes the full width; an odd last one is centred)
  collage  2 to 4 photos: a tall 1:1.3 photo beside a square one (two), beside two stacked (three), or a checkerboard
           of a wide and a narrow cell over a narrow and a wide one (four)
"""
import math
import explainer_lib as E
from scenes import SceneError, js_obj, need, word_index
from scenes import _annotate

TYPE = "photo-grid"
BAKED = True                         # the cells are worked out for the width it is given
MAX_SCALE = 1.0                      # never scaled: the chips are drawn at 28 px
DECOR_KEYS = ("credit", "x", "y")    # who took it, a note's place: not claims

IMAGE_RE = (".png", ".jpg", ".jpeg", ".webp")
LAYOUTS = {"stack": (1, 3), "grid": (1, 4), "collage": (2, 4)}
GAP, RADIUS = 20, 24
STACK = {1: 4 / 3.0, 2: 2.3, 3: 3.5}     # a stacked photo's width / height, by count
CELL = 0.75                               # a grid cell's height / width (4:3)
BIG = 0.56                                # the collage's wide share of the width
TALL, ROW = 1.3, 0.72                     # the collage's tall photo (height / width), its checkerboard rows
INSET = 16                                # the chips' inset from the photo's edges
CHIP_H, CR_SIZE, CR_PAD, CR_SPACING = 44, 28, 14, 0.06
TAG_SIZE, TAG_PAD, TAG_SPACING = 28, 16, 0.02
MAX_CREDIT, MAX_TAG = 40, 20
STAGGER = 0.12
SLIDE, SLIDE_Y = 0.6, 60
DRIFT, DRIFT_LEG = 4, 2.2                 # each photo drifts this far, a leg this long
PUSH = 1.06                               # each picture pushes in this much inside its photo, over the hold

CSS = """
  .pgr { position:relative; }
  .pgr-p { position:absolute; opacity:0; }
  .pgr-d { position:absolute; left:0; top:0; width:100%%; height:100%%; border-radius:%dpx; overflow:hidden; }
  .pgr-i { position:absolute; left:0; top:0; width:100%%; height:100%%; display:block; object-fit:cover; }
  .pgr-cr { position:absolute; left:%dpx; bottom:%dpx; height:%dpx; line-height:%dpx; padding:0 %dpx; border-radius:10px;
    font-family: var(--label); font-weight:500; font-size:%dpx; letter-spacing:.06em; white-space:nowrap; }
  .pgr-tag { position:absolute; left:%dpx; top:%dpx; height:%dpx; line-height:%dpx; padding:0 %dpx; border-radius:%dpx;
    font-weight:700; font-size:%dpx; letter-spacing:.02em; white-space:nowrap; }
""" % (RADIUS, INSET, INSET, CHIP_H, CHIP_H, CR_PAD, CR_SIZE, INSET, INSET, CHIP_H, CHIP_H, TAG_PAD, CHIP_H // 2, TAG_SIZE) + _annotate.CSS


def layout_of(scene):
    return scene.get("layout") or "grid"


def cells(scene, width):
    """([(x, y, w, h)] one per photo, the scene's height) at this width."""
    n, lay, W, G = len(scene["photos"]), layout_of(scene), int(width), GAP
    out = []
    if lay == "stack":
        h = int(round(W / STACK[n]))
        out = [(0, i * (h + G), W, h) for i in range(n)]
    elif lay == "grid":
        if n == 1:
            out = [(0, 0, W, int(round(W * CELL)))]
        else:
            cw = (W - G) // 2
            ch = int(round(cw * CELL))
            for i in range(n):
                r, k = divmod(i, 2)
                x = (W - cw) // 2 if (i == n - 1 and n % 2) else k * (cw + G)
                out.append((x, r * (ch + G), cw, ch))
    else:
        bw = int(round((W - G) * BIG))
        sw = W - G - bw
        if n == 4:
            rh = int(round(bw * ROW))
            out = [(0, 0, bw, rh), (bw + G, 0, sw, rh), (0, rh + G, sw, rh), (sw + G, rh + G, bw, rh)]
        else:
            H = int(round(bw * TALL))
            out = [(0, 0, bw, H)]
            if n == 2:
                out.append((bw + G, H - sw, sw, sw))
            else:
                h1 = (H - G) // 2
                out += [(bw + G, 0, sw, h1), (bw + G, h1 + G, sw, H - G - h1)]
    return out, max(y + h for _, y, _, h in out)


def validate(scene):
    photos = scene.get("photos")
    if not isinstance(photos, list) or not 1 <= len(photos) <= 4:
        return ["a photo-grid holds 1 to 4 photos {src, credit, tag, at} (got %s)" % (len(photos) if isinstance(photos, list) else photos,)]
    errs = []
    lay = layout_of(scene)
    if lay not in LAYOUTS:
        return ["layout is stack, grid or collage (got %r)" % (lay,)]
    lo, hi = LAYOUTS[lay]
    if not lo <= len(photos) <= hi:
        errs.append("a %s holds %d to %d photos (got %d)" % (lay, lo, hi, len(photos)))
    last = None
    for i, p in enumerate(photos):
        if not isinstance(p, dict):
            errs.append("photo %d is {src, credit, tag, at}" % i)
            continue
        src = p.get("src")
        if not isinstance(src, str) or not src.lower().endswith(IMAGE_RE):
            errs.append("photo %d: src is a PNG, JPG or WebP next to storyboard.json (got %r)" % (i, src))
        cr = p.get("credit")
        if not isinstance(cr, str) or not cr.strip():
            errs.append("photo %d (%s) has no credit: every photo needs one (who took it, or \"stand-in image\")" % (i, src))
        elif len(cr) > MAX_CREDIT:
            errs.append("photo %d (%s): its credit is %d characters at most" % (i, src, MAX_CREDIT))
        if p.get("tag") is not None and (not isinstance(p["tag"], str) or not p["tag"].strip() or len(p["tag"]) > MAX_TAG):
            errs.append("photo %d (%s): tag is a word or two (%d characters at most)" % (i, src, MAX_TAG))
        if p.get("at") is not None:
            n = word_index(p["at"])
            if last is not None and n is not None and n < last:
                errs.append("photos land in order: photo %d's at (%s) is before the photo ahead of it" % (i, p["at"]))
            last = n if n is not None else last
    if scene.get("notes") is not None:
        errs += _annotate.validate(scene["notes"])
    return errs



def height(scene, width):
    return cells(scene, width)[1]


def min_width(scene):
    return 2 * 128 + GAP


def credit_w(text):
    return int(math.ceil(E.text_width(text, CR_SIZE, "mono500", spacing=CR_SPACING))) + 2 * CR_PAD + 2


def tag_w(text):
    return int(math.ceil(E.text_width(text, TAG_SIZE, "display700", spacing=TAG_SPACING))) + 2 * TAG_PAD + 2


def _sway(ctx, sel, t0, t1, prop, amp, leg):
    """An idle drift from t0 to t1 on one axis: to +amp, then -amp and back, sine.inOut (ambient: not a change)."""
    t, k = t0, 0
    while True:
        d = leg / 2.0 if k == 0 else leg
        if t + d > t1 + 1e-6:
            break
        ctx.ambient("tl.to('%s', %s, %.3f);" % (sel, js_obj({prop: amp if k % 2 == 0 else -amp, "duration": round(d, 3), "ease": "sine.inOut"}), t))
        t, k = t + d, k + 1


def render(scene, ctx, box):
    sid, p = ctx.id, ctx.pc                # the chips sit on the photo, not the ground: the paper roles on any ground
    W = box[2]
    boxes, H = cells(scene, W)
    parts, js = [], []
    prev = None
    for i, (ph, (x, y, w, h)) in enumerate(zip(scene["photos"], boxes)):
        cw = credit_w(ph["credit"])
        if INSET + cw > w - INSET:
            raise SceneError("photo %d (%s): its credit %r is wider than the photo (%d px of %d): shorten it, or give the photo a "
                             "wider cell (another layout)" % (i, ph["src"], ph["credit"], cw, w - 2 * INSET))
        if ph.get("tag") and INSET + tag_w(ph["tag"]) > w - INSET:
            raise SceneError("photo %d (%s): its tag %r is wider than the photo: shorten it" % (i, ph["src"], ph["tag"]))
        if ph.get("tag") and 2 * INSET + 2 * CHIP_H + 8 > h:
            raise SceneError("photo %d (%s) is too short for a tag and a credit: drop the tag" % (i, ph["src"]))
        if ph.get("at") is not None:
            word_t, attrs = ctx.item(ph["at"])
        else:
            word_t, attrs = (ctx.t_in if prev is None else prev), ""
        t = word_t if prev is None else max(word_t, prev + STAGGER)
        prev = t
        rel, _ = ctx.asset(ph["src"])
        notes_html = ""
        if i == 0 and scene.get("notes"):
            notes_html, notes_js = _annotate.render(scene["notes"], ctx, w, h, sid)
            js += notes_js
        tag = ('<div class="pgr-tag" id="%s-g%d" style="background:%s;color:%s">%s</div>' % (sid, i, p["fill"], p["on_fill"], ctx.esc(ph["tag"]))
               if ph.get("tag") else "")
        parts.append('<div class="pgr-p" id="%s-p%d"%s style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">'
                     '<div class="pgr-d" id="%s-d%d" style="box-shadow:%s"><img class="pgr-i" id="%s-i%d" src="%s" alt="" />%s%s'
                     '<div class="pgr-cr" id="%s-c%d" style="background:%s;color:%s">%s</div></div></div>'
                     % (sid, i, attrs, x, y, w, h, sid, i, ctx.c["shadow"], sid, i, ctx.esc(rel), notes_html, tag,
                        sid, i, E.rgba(p["ink"], 0.8), p["paper"], ctx.esc(ph["credit"])))
        js.append("tl.fromTo('#%s-p%d', %s, %s, %.3f);" % (sid, i, js_obj({"opacity": 0, "y": SLIDE_Y}),
                                                         js_obj({"opacity": 1, "y": 0, "duration": SLIDE, "ease": "expo.out", "immediateRender": False}), t))
        # held: the photo drifts up and down (vertically only: the column's sides have no room; its own direction and
        # pace, from its index: the same on every render) and its picture
        # pushes in inside the frame (ambient: idle motion, never a change for pace-check)
        _sway(ctx, "#%s-d%d" % (sid, i), t + SLIDE + 0.1 * (i % 3), ctx.t_out, "y", DRIFT if i % 2 == 0 else -DRIFT, DRIFT_LEG + 0.2 * (i % 2))
        ctx.ambient("tl.fromTo('#%s-i%d', %s, %s, %.3f);" % (sid, i, js_obj({"scale": 1}), js_obj({"scale": PUSH, "duration": round(ctx.t_out - t, 3),
                                                                                                "ease": "none", "immediateRender": False}), t))
    return '<div class="pgr" style="width:%dpx;height:%dpx">%s</div>' % (W, H, "".join(parts)), js
