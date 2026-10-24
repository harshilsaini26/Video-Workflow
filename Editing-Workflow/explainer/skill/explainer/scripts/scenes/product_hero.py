"""product-hero: the product itself, large, with depth. Its title is set big behind it in the look's hero face, and the
creator's cut-out rises in over the letters (expo.out, 0.7 s, a soft shadow under it), so the product crosses its own
name as the editorial reels do it. Then it floats while it holds (y 8 px up and down, sine.inOut, for the scene's
life) and pushes in slowly; notes (scenes/_annotate.py) draw on over it on their words.

  {"type": "product-hero", "src": "assets/earbuds.png", "alt": "an earbud on its side", "aspect": 1.0,
   "title": "No wire", "title_at": "word:3", "at": "word:4", "float": true,
   "notes": [{"x": 0.72, "y": 0.2, "label": "WAIT... A WIRE?", "at": "word:7", "mark": "circle", "side": "left"}]}

- src: the creator's image, relative to storyboard.json (a PNG with alpha is best: a cut-out; a JPEG shows as a
  rectangle, and E3 refuses one under a title, which it would hide: use a "headline" instead); alt says what it shows.
- aspect: the image's width / height. The scene's height is known before any file is read (the composer places it
  first, and height() sees only the data), so the box is laid out from `aspect` (1 when it is not given). The image is
  then fitted inside that box from its real size (read from its header), never stretched, so any picture fits; when
  the file's aspect is not the box's, the composer prints a note with the value to set.
- The box: as wide as the column it is given (less the push-in's growth; 80% of it under a title, so the letters
  show past even an opaque photo) and as tall as the aspect asks, up to the scene area's height (less
  under a headline: the scene reads its own headline for that). A box too tall for the full width is the composer's
  cue to use the narrow column, where a tall or square product is drawn larger; when the title fits only the full
  width, the box keeps to the full width's height instead.
- title: up to 40 characters, uppercase unless "case" is "as-is", at 200 px down to 124 (at least 120 drawn, under the
  camera's push), one line when it fits at 152 or more, else up to three lines. Each line rises through its mask on
  title_at, 0.08 s apart. It carries data-depth="behind": gate E5 lets this scene's image cover it (Ruling 6), and
  checks everything else about it as usual.
- at: the image's entrance (the scene's start when not given); float: false keeps it still (the push-in stays).

The scene is laid out in pixels for the width it is given (BAKED) and never scaled (MAX_SCALE 1): its sizes are
the sizes drawn.
"""
import math, os
import explainer_lib as E
import headline as HL
from scenes import SceneError, js_obj, need
from scenes import _annotate

TYPE = "product-hero"
HERO_CSS = ".ph-tl"                    # the title, in the look's hero face (E.hero()), measured with its glyphs
BAKED = True                           # the box and the title's size are worked out for the width it is given
MAX_SCALE = 1.0                        # never scaled: the title's size and the image's box are what is drawn
DECOR_KEYS = ("alt", "aspect", "x", "y", "float")   # a description, a shape, a note's place: not claims

IMAGE_RE = (".png", ".jpg", ".jpeg", ".webp", ".gif")
SIZES = list(range(200, 123, -4))      # the title: the largest that fits (124 is 123 px drawn under the camera's 0.995)
ONE_LINE = 152                         # one line when it fits at this size or more, else two, else three
MAX_LINES, MAX_CHARS = 3, 40
LINE = 1.04                            # the title's line height, in ems (its masks are this tall)
FIT = 0.98                             # a line takes at most this share of the width (kerning, rounding)
RISE, RISE_Y = 0.7, 90                 # the image's entrance
FLOAT_Y, FLOAT_LEG = 8, 1.8            # the float: up and down this far, a leg this long
PUSH = 1.025                           # the slow push-in, over the scene
TITLED = 0.8                           # with a title, the image keeps to this share of the width: the letters show past it
STAGGER = 0.08
MIN_W = 300
NARROW_W = E.L.NARROW["right"] - E.L.NARROW["left"]     # 780, the narrow column
SHADOW = "drop-shadow(0 30px 40px %s)"

CSS = """
  .ph { position:relative; }
  .ph-t { position:absolute; left:0; width:100%%; z-index:1; display:flex; flex-direction:column; align-items:center; }
  .ph-m { overflow:hidden; }
  .ph-tl { display:block; white-space:nowrap; text-align:center; }
  .ph-img { position:absolute; z-index:2; opacity:0; }
  .ph-fl { position:relative; width:100%%; height:100%%; }
  .ph-fl > img { position:absolute; left:0; top:0; width:100%%; height:100%%; display:block; object-fit:contain; }
""" % () + _annotate.CSS


def shown(scene):
    t = str(scene.get("title") or "").strip()
    return t if scene.get("case") == "as-is" else t.upper()


def _wrap(words, size, width):
    g = E.hero()
    fits = lambda s: E.text_width(s, size, g["glyphs"], spacing=g["spacing"]) <= width * FIT
    lines, cur = [], []
    for w in words:
        if not fits(w):
            return None
        if cur and not fits(" ".join(cur + [w])):
            lines.append(cur)
            cur = []
        cur.append(w)
    return lines + [cur] if cur else lines


def title_layout(scene, width):
    """{size, lines: [str], line_h, height} for the title at this width, or None when it needs more than three lines
    at the smallest size (or a word is wider than the width)."""
    words = shown(scene).split()
    if not words:
        return {"size": 0, "lines": [], "line_h": 0, "height": 0}
    for n, least in ((1, ONE_LINE), (2, SIZES[-1]), (MAX_LINES, SIZES[-1])):
        for size in SIZES:
            if size < least:
                break
            lines = _wrap(words, size, width)
            if lines is not None and len(lines) <= n:
                lh = int(round(size * LINE))
                return {"size": size, "lines": [" ".join(l) for l in lines], "line_h": lh, "height": lh * len(lines)}
    return None


def _top(scene):
    """Where the scene area starts: under the scene's own headline, when it has one."""
    hl = scene.get("headline")
    if not hl:
        return E.SCENE["top"]
    try:
        return E.SCENE["top"] + HL.layout(hl)["height"] + HL.GAP
    except (ValueError, TypeError, AttributeError):
        return E.SCENE["top"]


def _room(scene, width):
    """The tallest box the column can hold: the narrow column's height, or, when only the full width can take the
    title, the full width's (it ends above the action column)."""
    top = _top(scene)
    if width > NARROW_W and min_width(scene) > NARROW_W:
        return E.L.RIGHT_COL_TOP - top - 2 * E.IDLE_ROOM
    return E.SCENE["bottom"] - top - 2 * E.IDLE_ROOM


def aspect(scene):
    return float(scene.get("aspect") or 1.0)


def layout(scene, width):
    """{iw, ih (the image's box), title (title_layout), height}: the box at this width."""
    a, room = aspect(scene), _room(scene, width)
    cap = width / PUSH * (TITLED if scene.get("title") else 1)      # the push-in never carries it past the column
    iw = int(min(math.floor(cap), math.floor(room * a)))
    ih = min(room, int(round(iw / a)))
    t = title_layout(scene, width) or {"size": SIZES[-1], "lines": [], "line_h": 0, "height": 0}
    return {"iw": iw, "ih": ih, "title": t, "height": max(ih, t["height"])}


def validate(scene):
    errs = need(scene, ["src", "alt"])
    src = scene.get("src")
    if src and (not isinstance(src, str) or not src.lower().endswith(IMAGE_RE)):
        errs.append("src is the image: a PNG, JPEG, WebP or GIF next to storyboard.json (got %r)" % (src,))
    elif not src:
        errs.append("src is the image: a PNG, JPEG, WebP or GIF next to storyboard.json")
    if scene.get("alt") is not None and (not isinstance(scene["alt"], str) or not scene["alt"].strip() or len(scene["alt"]) > 120):
        errs.append("alt says what the image shows, in a few words (120 characters at most)")
    a = scene.get("aspect")
    if a is not None and (not isinstance(a, (int, float)) or isinstance(a, bool) or not 0.2 <= a <= 5):
        errs.append("aspect is the image's width / height, 0.2 to 5 (got %r)" % (a,))
    if scene.get("float") is not None and not isinstance(scene["float"], bool):
        errs.append("float is true or false")
    title = scene.get("title")
    if title is not None:
        if not isinstance(title, str) or not title.strip() or len(title) > MAX_CHARS:
            errs.append("title is a short name, %d characters at most" % MAX_CHARS)
        else:
            g = E.hero()
            wide = E.L.SAFE["right"] - E.L.SAFE["left"]
            for w in shown(scene).split():
                if E.text_width(w, SIZES[-1], g["glyphs"], spacing=g["spacing"]) > wide * FIT:
                    errs.append("a word of the title (%s) is wider than the full width at %d px, the smallest a title "
                                "behind a product takes: shorten it" % (w, SIZES[-1]))
                    break
            else:
                if title_layout(scene, wide) is None:
                    errs.append("the title needs more than %d lines at %d px: shorten it" % (MAX_LINES, SIZES[-1]))
    elif scene.get("title_at") is not None:
        errs.append("title_at needs a title")
    if scene.get("notes") is not None:
        errs += _annotate.validate(scene["notes"])
    return errs


def height(scene, width):
    return layout(scene, width)["height"]


def min_width(scene):
    """The widest title word at the smallest size; a title the narrow column cannot hold in three lines asks for more
    than the narrow column, so the composer gives it the full width."""
    if not scene.get("title"):
        return MIN_W
    g = E.hero()
    word = max(E.text_width(w, SIZES[-1], g["glyphs"], spacing=g["spacing"]) for w in shown(scene).split())
    need_w = max(MIN_W, int(math.ceil(word / FIT)) + 1)
    if need_w <= NARROW_W and title_layout(scene, NARROW_W) is None:
        need_w = NARROW_W + 1
    return need_w


def _legs(ctx, sel, t0, t1, amp, leg):
    """An idle float from t0 to t1: up to -amp, then down to +amp and back, sine.inOut (ambient: not a change)."""
    t, k = t0, 0
    while True:
        d = leg / 2.0 if k == 0 else leg
        if t + d > t1 + 1e-6:
            break
        ctx.ambient("tl.to('%s', %s, %.3f);" % (sel, js_obj({"y": -amp if k % 2 == 0 else amp, "duration": round(d, 3), "ease": "sine.inOut"}), t))
        t, k = t + d, k + 1


def render(scene, ctx, box):
    sid, c = ctx.id, ctx.c
    W = box[2]
    lay = layout(scene, W)
    H = lay["height"]
    page, rw, rh = ctx.image(scene["src"])
    if scene.get("title"):
        import imagesize
        if not imagesize.alpha(os.path.join(ctx.out_dir, page)):
            ctx.fail("%s has no transparency (a JPEG, or a PNG or WebP without alpha), so the title behind it would be "
                     "hidden: give a cut-out (a PNG or WebP with alpha), or drop the title and put the words in a "
                     "\"headline\" (it sits above the scene)" % scene["src"])
    real = rw / float(rh)
    a = aspect(scene)
    if abs(real - a) > 0.02 * real:
        print("note: %s: %s is %dx%d (aspect %.3f); set \"aspect\": %.3f so its box fits it exactly" % (sid, scene["src"], rw, rh, real, real))
    iw, ih = lay["iw"], lay["ih"]
    if real >= a:                                   # fitted inside its box from its real size: never stretched
        dw, dh = iw, int(round(iw / real))
    else:
        dw, dh = int(round(ih * real)), ih
    left, top = (W - dw) // 2, (H - dh) // 2
    t, attrs = ctx.item(scene["at"]) if scene.get("at") is not None else (ctx.t_in, "")
    js, parts = [], []

    tl = lay["title"]
    if scene.get("title"):
        if title_layout(scene, W) is None:
            raise SceneError("the title needs more than %d lines at %d px in the %d px column: shorten it" % (MAX_LINES, SIZES[-1], W))
        tt, t_attrs = ctx.item(scene["title_at"]) if scene.get("title_at") is not None else (t, "")
        hero = E.hero()
        lines = "".join('<div class="ph-m" style="height:%dpx"><div class="ph-tl" id="%s-t%d" style="font-size:%dpx;line-height:%dpx;%s">%s</div></div>'
                        % (tl["line_h"], sid, i, tl["size"], tl["line_h"], hero["css"], ctx.esc(ln)) for i, ln in enumerate(tl["lines"]))
        parts.append('<div class="ph-t" id="%s-t" data-depth="behind"%s style="top:%dpx;height:%dpx;color:%s">%s</div>'
                     % (sid, t_attrs, (H - tl["height"]) // 2, tl["height"], ctx.ink, lines))
        for i in range(len(tl["lines"])):
            js.append("tl.set('#%s-t%d', { yPercent: 110 }, 0);" % (sid, i))
            js.append("tl.fromTo('#%s-t%d', { yPercent: 110 }, %s, %.3f);" % (sid, i, js_obj({"yPercent": 0, "duration": 0.6, "ease": "expo.out",
                                                                                            "immediateRender": False}), tt + STAGGER * i))
    notes_html, notes_js = _annotate.render(scene.get("notes") or [], ctx, dw, dh, sid) if scene.get("notes") else ("", [])
    shadow = SHADOW % E.rgba(ctx.pc["ink"], 0.28)        # a dark shadow on any ground (the paper ink)
    parts.append('<div class="ph-img" id="%s-img"%s style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><div class="ph-fl" id="%s-fl">'
                 '<img id="%s-pic" src="%s" alt="%s" style="filter:%s" />%s</div></div>'
                 % (sid, attrs, left, top, dw, dh, sid, sid, ctx.esc(page), ctx.esc(scene["alt"]), shadow, notes_html))
    js.append("tl.fromTo('#%s-img', %s, %s, %.3f);" % (sid, js_obj({"opacity": 0, "y": RISE_Y}),
                                                       js_obj({"opacity": 1, "y": 0, "duration": RISE, "ease": "expo.out", "immediateRender": False}), t))
    js += notes_js
    # held: a slow push-in over the scene, and the float (ambient: idle motion, never a change for pace-check)
    ctx.ambient("tl.fromTo('#%s-fl', %s, %s, %.3f);" % (sid, js_obj({"scale": 1}), js_obj({"scale": PUSH, "duration": round(ctx.t_out - t, 3),
                                                                                           "ease": "none", "immediateRender": False}), t))
    if scene.get("float", True):
        _legs(ctx, "#%s-fl" % sid, t + RISE, ctx.t_out, FLOAT_Y, FLOAT_LEG)
    return '<div class="ph" style="width:%dpx;height:%dpx">%s</div>' % (W, H, "".join(parts)), js
