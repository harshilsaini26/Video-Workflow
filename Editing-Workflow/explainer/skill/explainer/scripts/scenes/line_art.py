"""line-art: one big line drawing, drawn on. A Lucide icon, or the creator's own stroke-only SVG, fills the scene and is
drawn on its word (stroke-dashoffset, 1.2 s, power2.inOut); a caption in the aside face (Instrument Serif italic) fades
in under it, and may be struck through in the accent on its own word ("a library in your pocket", then "not really").
While it holds, the drawing floats gently, so the picture is never still for long.

  {"type": "line-art", "icon": "book", "caption": "a library in your pocket", "at": "word:3", "strike": "word:8"}
  {"type": "line-art", "svg": "art/usb-c.svg", "caption": "one cable for everything", "at": "word:3"}

`svg` is relative to storyboard.json. It must be line art: every shape stroked, none filled (fill="none" on each shape
or a group around it; SVG fills shapes black when nothing says otherwise), and only shapes (no text, images, scripts or
style sheets). The look's ink replaces its colours; its geometry and stroke widths are kept.
"""
import math, os, re
import xml.etree.ElementTree as ET
import explainer_lib as E
from scenes import js_obj, line_px, need

TYPE = "line-art"
DECOR_KEYS = {"svg", "icon", "strike"}   # a file name ("usb-c-2024.svg") and a word anchor are not on screen: no source
MAX_SCALE = 1.5
ART = 540                             # the drawing's square, px (the composer scales the scene to fill the area)
ICON_STROKE = 0.6                     # a Lucide icon's stroke at this size (its own 2 of 24 would be a 45 px line)
C_SIZE, C_LH, C_GAP = 60, 1.2, 32     # the caption: the aside face
STRIKE = 5
DRAW = 1.2
DASH = 1.02                           # one dash a little longer than the path (pathLength 1): a closed shape meets itself
MAX_WORDS = 14
SVGNS = "http://www.w3.org/2000/svg"
SHAPES = {"path", "line", "circle", "rect", "polyline", "polygon", "ellipse"}
DROP = {"title", "desc", "metadata", "defs"}           # notes and unused definitions: left out of the page
KEEP_ATTRS = {"d", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "points", "transform",
              "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "fill-rule"}
_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

CSS = """
  .la { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .la-art { width:%dpx; height:%dpx; flex:none; opacity:0; }
  .la-art svg { display:block; width:100%%; height:100%%; overflow:visible; }
  .la-s { stroke-dasharray:%s 3; stroke-dashoffset:%s; }
  .la-cap { width:100%%; margin-top:%dpx; font-size:%dpx; line-height:%dpx; text-align:center; text-wrap:balance; opacity:0; }
  .la-ct { background-repeat:no-repeat; background-position:0 58%%; background-size:0%% %dpx; }
""" % (ART, ART, DASH, DASH, C_GAP, C_SIZE, line_px(C_SIZE, C_LH), STRIKE)


def validate(scene):
    errs = need(scene, ["caption", "at"])
    icon, svg = scene.get("icon"), scene.get("svg")
    if icon is None and svg is None:
        errs.append("line-art needs an icon or an svg (a Lucide icon name, or the creator's stroke-only SVG file)")
    elif icon is not None and svg is not None:
        errs.append("line-art takes an icon or an svg, not both")
    elif icon is not None and not _NAME.match(str(icon)):
        errs.append("icon %r is not a Lucide name (lower-case words joined by -)" % (icon,))
    elif svg is not None and not str(svg).lower().endswith(".svg"):
        errs.append("svg is a .svg file, relative to storyboard.json (got %r)" % (svg,))
    if scene.get("caption") and len(str(scene["caption"]).split()) > MAX_WORDS:
        errs.append("caption: at most %d words, an aside (got %d)" % (MAX_WORDS, len(str(scene["caption"]).split())))
    return errs


def _lines(scene, width):
    a = E.aside()
    return E.text_lines(scene["caption"], C_SIZE, width, a["glyphs"], spacing=a["spacing"])


def height(scene, width):
    return ART + C_GAP + line_px(C_SIZE, C_LH) * _lines(scene, width)


def min_width(scene):
    a = E.aside()
    return max(ART, max(int(math.ceil(E.text_width(w, C_SIZE, a["glyphs"], spacing=a["spacing"]))) for w in str(scene["caption"]).split()) + 4)


def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _style(el):
    out = {}
    for part in (el.get("style") or "").split(";"):
        k, _, v = part.partition(":")
        if k.strip():
            out[k.strip().lower()] = v.strip()
    return out


def clean_svg(text, name, stroke_width=None):
    """The drawing as inline SVG markup: every shape stroked in currentColor, none filled, each with pathLength 1 (so
    one dash draws it on), or ValueError naming the file and what is wrong with it. `stroke_width` replaces the
    drawing's own (on its root, which its shapes inherit)."""
    if re.search(r"<!(DOCTYPE|ENTITY)", text, re.I):
        raise ValueError("%s: an SVG with a DOCTYPE or entities is not taken; export it as plain SVG" % name)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError("%s is not an SVG (it does not parse: %s)" % (name, e))
    if _local(root.tag) != "svg":
        raise ValueError("%s is not an SVG (no <svg> root)" % name)
    stroked = [0]

    def walk(el, fill, stroke):
        st = _style(el)
        fill = st.get("fill", el.get("fill", fill)).strip()
        stroke = st.get("stroke", el.get("stroke", stroke)).strip()
        tag = _local(el.tag)
        for k in list(el.attrib):
            if not k.startswith("{") and k.lower().startswith("on"):
                raise ValueError("%s: <%s> has an %s handler: line art is plain shapes" % (name, tag, k))
        if tag in SHAPES:
            if fill.lower() != "none":
                raise ValueError("%s: <%s> has fill %r%s: line art is stroke-only (fill=\"none\" on every shape, or on a group "
                                 "around them)" % (name, tag, fill, " (the SVG default)" if fill == "black" and "fill" not in st
                                                    and el.get("fill") is None else ""))
            if stroke.lower() not in ("none", "transparent"):
                stroked[0] += 1
        elif tag not in ("svg", "g") and tag not in DROP:
            raise ValueError("%s: <%s> is not a stroke shape: line art is stroke-only (paths, lines, circles, rectangles, "
                             "polylines, polygons, ellipses)" % (name, tag))
        keep = {}
        for k, v in el.attrib.items():
            if k in KEEP_ATTRS or (tag == "svg" and k in ("viewBox", "preserveAspectRatio")):
                keep[k] = v
        for k in ("stroke-width", "stroke-linecap", "stroke-linejoin"):
            if k in st:
                keep[k] = st[k]
        if tag == "svg":
            for k in ("width", "height"):
                keep.pop(k, None)
            if "viewBox" not in keep:
                w, h = (re.match(r"^\s*([\d.]+)\s*(px)?\s*$", el.get(k) or "") for k in ("width", "height"))
                if not (w and h):
                    raise ValueError("%s has no viewBox (and no width and height in px to make one from)" % name)
                keep["viewBox"] = "0 0 %s %s" % (w.group(1), h.group(1))
        el.attrib.clear()
        el.attrib.update(keep)
        if tag in SHAPES:
            el.set("fill", "none")
            el.set("stroke", "currentColor" if stroke.lower() not in ("none", "transparent") else "none")
            el.set("pathLength", "1")
            el.set("class", "la-s")
        el.text = None
        for ch in list(el):
            ch.tail = None
            if not isinstance(ch.tag, str) or _local(ch.tag) in DROP or not ch.tag.startswith("{%s}" % SVGNS) and ch.tag.startswith("{"):
                el.remove(ch)          # comments, notes, and an editor's own namespaced elements
                continue
            walk(ch, fill, stroke)

    walk(root, "black", "none")
    if not stroked[0]:
        raise ValueError("%s has no stroked shape: nothing to draw (give its shapes a stroke)" % name)
    if stroke_width is not None:
        root.set("stroke-width", str(stroke_width))
        root.set("stroke-linecap", "round")
        root.set("stroke-linejoin", "round")
    ET.register_namespace("", SVGNS)
    return ET.tostring(root, encoding="unicode")


def render(scene, ctx, box):
    c, sid, mo = ctx.c, ctx.id, ctx.tokens["motion"]
    t, attrs = ctx.item(scene["at"])
    if scene.get("icon") is not None:
        raw, name = ctx.icon(scene["icon"]), "vendor/lucide/%s.svg" % scene["icon"]
    else:
        rel = str(scene["svg"]).replace("\\", "/")
        path = rel if os.path.isabs(rel) else os.path.join(ctx.spec_dir, rel)
        if not os.path.isfile(path):
            ctx.fail("no file at %s (paths are relative to storyboard.json: %s)" % (scene["svg"], path))
        with open(path, encoding="utf-8") as f:
            raw, name = f.read(), os.path.basename(rel)
    try:       # Lucide draws at 2 of 24: thinner at this size, so it reads as line art; the creator's widths are kept
        svg = clean_svg(raw, name, ICON_STROKE if scene.get("icon") is not None else None)
    except ValueError as e:
        ctx.fail(str(e))
    html = ['<div class="la-art" id="%s-art"%s style="color:%s">%s</div>' % (sid, attrs, ctx.ink, svg)]
    js = [ctx.enter("#%s-art" % sid, t, dur=0.2),
          "tl.fromTo('#%s .la-s', { strokeDashoffset: %s }, %s, %.3f);" % (sid, DASH, js_obj({"strokeDashoffset": 0, "duration": DRAW, "ease": "power2.inOut",
                                                                                     "immediateRender": False}), t)]
    # the caption follows the drawing, and is on screen before any strike crosses it
    tc = t + 0.8
    s_attrs = ""
    if scene.get("strike") is not None:
        ts, s_attrs = ctx.item(scene["strike"])
        if ts < t + 0.3 - 1e-6:
            ctx.fail("the strike (%s) comes before the drawing (%s) and its caption are on screen: strike on a later word"
                     % (scene["strike"], scene["at"]))
        tc = min(tc, ts - 0.3)
        js.append("tl.fromTo('#%s-ct', { backgroundSize: '0%% %dpx' }, %s, %.3f);"
                  % (sid, STRIKE, js_obj({"backgroundSize": "100%% %dpx" % STRIKE, "duration": 0.3, "ease": "power3.inOut",
                                          "immediateRender": False}), ts))
    tc = max(t, min(tc, ctx.t_out - E.EXIT - 0.6))
    html.append('<div class="la-cap" id="%s-cap" style="color:%s;%s"><span class="la-ct" id="%s-ct"%s style="background-image:linear-gradient(%s, %s)">'
                '%s</span></div>' % (sid, c["dim"], E.aside()["css"], sid, s_attrs, c["accent"], c["accent"], ctx.esc(scene["caption"])))
    js.append(ctx.enter("#%s-cap" % sid, tc, {"y": 14}))
    # while it holds, the drawing floats
    ctx.idle("#%s-art" % sid, t + DRAW, ctx.t_out, {"y": -10})
    return '<div class="la">%s</div>' % "".join(html), js
