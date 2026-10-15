"""formula: a formula set with KaTeX (MIT, copied locally); its parts appear on their words (SPEC §6.2)."""
import re
import explainer_lib as E
from scenes import js_str, need

TYPE = "formula"
SIZE = 76                     # KaTeX scales from the font size
ROW = 230                     # the formula row: room for a fraction with an exponent
INSTALL = "npm pack katex@0.16.11, then unpack its dist/ (katex.min.js, katex.min.css, fonts/) to assets/vendor/katex/"

CSS = """
  .f-row { width:100%%; height:%dpx; display:flex; align-items:center; justify-content:center; gap:.3em; font-size:%dpx; white-space:nowrap; }
  .f-part { display:inline-block; opacity:0; }
""" % (ROW, SIZE)


def _visible(tex):
    """A rough count of the characters KaTeX draws: commands and braces dropped, a fraction counts its longer side."""
    t = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", lambda m: max(m.group(1), m.group(2), key=len), tex)
    t = re.sub(r"\\[a-zA-Z]+", "x", t)
    return re.sub(r"[{}^_\s]", "", t)


def _parts(scene):
    return scene.get("parts") or [{"tex": scene["tex"], "at": None}]


def validate(scene):
    errs = need(scene, ["tex"]) if not scene.get("parts") else []
    errs += ["part %d has no tex" % i for i, p in enumerate(scene.get("parts", [])) if not p.get("tex")]
    errs += ["part %d has no at" % i for i, p in enumerate(scene.get("parts", [])) if p.get("at") is None]
    return errs


def height(scene, width):
    return ROW


def min_width(scene):
    return int(sum(len(_visible(p["tex"])) for p in _parts(scene)) * SIZE * 0.55 + 0.3 * SIZE * (len(_parts(scene)) - 1)) + 1


def render(scene, ctx, box):
    kdir = "katex"
    js_path = ctx.vendor(kdir + "/katex.min.js", INSTALL)
    css_path = ctx.vendor(kdir + "/katex.min.css", INSTALL)
    ctx.vendor(kdir + "/fonts", INSTALL)
    ctx.add_head('<link rel="stylesheet" href="%s" />' % css_path)
    ctx.add_head('<script src="%s"></script>' % js_path)
    sid = ctx.id
    spans, js = [], []
    for i, p in enumerate(_parts(scene)):
        spans.append('<span class="f-part" id="%s-p%d"></span>' % (sid, i))
        js.append("katex.render(%s, document.getElementById(%s), { throwOnError: false, displayMode: false });"
                  % (js_str(p["tex"]), js_str("%s-p%d" % (sid, i))))
        t = ctx.at(p["at"]) if p.get("at") is not None else ctx.t_in
        js.append(ctx.enter("#%s-p%d" % (sid, i), t, {"y": 24}))
    return '<div class="f-row" style="color:%s">%s</div>' % (ctx.ink, "".join(spans)), js
