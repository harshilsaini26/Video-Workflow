"""logo-card: a brand's real mark on a white app-icon card, with its name under it and an optional number badge; the
card springs in and then floats (PLAYBOOK §E4). For naming a company, a school, a course or a product.

The mark comes from simple-icons (CC0 data; `logo` is its slug, e.g. "coursera"), coloured with the brand's own hex,
or from the creator's own image (`src`, next to storyboard.json). A logo is the brand's trademark: show it only to
name the brand, never to suggest it endorses the reel; the composer prints each brand used, with its guidelines link.
"""
import json, os, re, unicodedata
import explainer_lib as E
from scenes import js_obj, need

TYPE = "logo-card"
INSTALL = "npm pack simple-icons@13.21.0, then unpack its icons/ and _data/ to assets/vendor/simple-icons/"
CARD, MARK, RADIUS = 400, 240, 76
TOP = 26                         # room above the card for the badge
N_GAP, N_SIZE, N_LINE = 34, 60, 70
S_SIZE, S_LINE = 36, 46
BADGE = 88
_DATA = {}


def slug(title):
    """simple-icons' own titleToSlug: "Coursera" -> "coursera", "Dot.net" -> "dotdotnet"."""
    s = title.lower().replace("+", "plus").replace(".", "dot").replace("&", "and")
    for a, b in (("đ", "d"), ("ħ", "h"), ("ı", "i"), ("ĸ", "k"), ("ŀ", "l"), ("ł", "l"), ("ß", "ss"), ("ŧ", "t")):
        s = s.replace(a, b)
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", s)


def brand(vendor_dir, name):
    """The data entry for a slug ({"title", "hex", "guidelines"?, "license"?}), or None."""
    path = os.path.join(vendor_dir, "simple-icons", "_data", "simple-icons.json")
    if path not in _DATA:
        _DATA[path] = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for it in json.load(f).get("icons", []):
                    _DATA[path][it.get("slug") or slug(it["title"])] = it
    return _DATA[path].get(name)


CSS = """
  .lc { position:relative; width:100%%; display:flex; flex-direction:column; align-items:center; }
  .lc-card { position:relative; width:%dpx; height:%dpx; margin-top:%dpx; border-radius:%dpx; display:flex;
    align-items:center; justify-content:center; opacity:0; }
  .lc-mark { width:%dpx; height:%dpx; display:flex; align-items:center; justify-content:center; }
  .lc-mark svg, .lc-mark img { width:100%%; height:100%%; object-fit:contain; display:block; }
  .lc-badge { position:absolute; right:-24px; top:-%dpx; width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center;
    justify-content:center; font-weight:700; font-size:46px; line-height:1; opacity:0; }
  .lc-name { margin-top:%dpx; height:%dpx; font-weight:700; font-size:%dpx; line-height:%dpx; white-space:nowrap; opacity:0; }
  .lc-sub { height:%dpx; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; opacity:0; }
""" % (CARD, CARD, TOP, RADIUS, MARK, MARK, TOP, BADGE, BADGE, N_GAP, N_LINE, N_SIZE, N_LINE, S_LINE, S_SIZE, S_LINE)


def validate(scene):
    errs = []
    if bool(scene.get("logo")) == bool(scene.get("src")):
        errs.append("a logo card takes one of logo (a simple-icons slug) or src (an image next to storyboard.json)")
    if scene.get("src") and not scene.get("name"):
        errs.append("a logo card from src needs a name")
    if scene.get("badge") is not None and not 1 <= len(str(scene["badge"])) <= 2:
        errs.append("badge is 1 or 2 characters")
    return errs


def height(scene, width):
    return TOP + CARD + N_GAP + N_LINE + S_LINE


def min_width(scene):
    name = scene.get("name") or scene.get("logo") or ""
    return max(CARD + 60, int(max(E.text_width(name, N_SIZE), E.text_width(scene.get("sub", ""), S_SIZE, "display500"))) + 1)


def readable(hexcol, ink):
    """The brand colour, or the theme's ink when it would vanish on the light card."""
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (0, 2, 4))
    return "#" + hexcol if 0.2126 * r + 0.7152 * g + 0.0722 * b < 225 else ink


def render(scene, ctx, box):
    c, mo = ctx.c, ctx.tokens["motion"]
    sid = ctx.id
    if scene.get("logo"):
        name_ = str(scene["logo"])
        path = os.path.join(ctx.vendor_dir, "simple-icons", "icons", "%s.svg" % name_)
        if not re.match(r"^[a-z0-9]+$", name_) or not os.path.exists(path):
            ctx.fail("unknown logo %r: no vendor/simple-icons/icons/%s.svg (find the slug at simpleicons.org; get the set with: %s)"
                     % (name_, name_, INSTALL))
        with open(path, encoding="utf-8") as f:
            svg = f.read().strip()
        if not svg.startswith("<svg") or re.search(r"<script|on\w+=|href", svg, re.I):
            ctx.fail("vendor/simple-icons/icons/%s.svg is not a plain SVG mark" % name_)
        info = brand(ctx.vendor_dir, name_) or {"title": name_, "hex": ctx.pc["ink"][1:]}
        svg = re.sub(r"<title>.*?</title>", "", svg, flags=re.S).replace("<svg ", '<svg fill="%s" ' % readable(info["hex"], ctx.pc["ink"]), 1)
        mark = svg
        title = scene.get("name") or info["title"]
        print("note: %s: %s is a trademark of its owner; show it only to name the brand%s"
              % (sid, info["title"], " (guidelines: %s)" % info["guidelines"] if info.get("guidelines") else ""))
    else:
        rel, _ = ctx.asset(scene["src"])
        mark = '<img src="%s" alt="" />' % ctx.esc(rel)
        title = scene["name"]
    badge = ('<div class="lc-badge" id="%s-b" style="background:%s;color:%s">%s</div>'
             % (sid, c["fill"], c["on_fill"], ctx.esc(scene["badge"])) if scene.get("badge") is not None else "")
    sub = '<div class="lc-sub" id="%s-s" style="color:%s">%s</div>' % (sid, c["dim"], ctx.esc(scene["sub"])) \
        if scene.get("sub") else '<div class="lc-sub"></div>'
    html = ('<div class="lc"><div class="lc-card" id="%s-card" style="%s"><div class="lc-mark">%s</div>%s</div>'
            '<div class="lc-name" id="%s-n" style="color:%s">%s</div>%s</div>'
            % (sid, ctx.paper_card(), mark, badge, sid, ctx.ink, ctx.esc(title), sub))     # the mark on light paper
    t = ctx.t_in
    js = ["tl.fromTo('#%s-card', %s, %s, %.3f);" % (sid, js_obj({"opacity": 0, "scale": 0.6, "y": 60, "rotation": -8}),
                                                    js_obj({"opacity": 1, "scale": 1, "y": 0, "rotation": 0, "duration": 0.6,
                                                            "ease": "expo.out", "immediateRender": False}), t),
          ctx.enter("#%s-n" % sid, t + 0.2, {"y": 20})]
    if scene.get("sub"):
        js.append(ctx.enter("#%s-s" % sid, t + 0.3, {"y": 16}))
    if badge:
        js.append("tl.fromTo('#%s-b', %s, %s, %.3f);" % (sid, js_obj({"opacity": 0, "scale": 0}), js_obj(
            {"opacity": 1, "scale": 1, "duration": mo["enter"], "ease": "expo.out", "immediateRender": False}), t + 0.45))
    ctx.idle("#%s-card" % sid, t + 0.7, ctx.t_out, {"y": -12, "rotation": 2}, every=1.8)
    return html, js
