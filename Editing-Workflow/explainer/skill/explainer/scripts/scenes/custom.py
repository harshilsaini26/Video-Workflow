"""custom: a Claude-written scene in its own box, kept to that box and offline (SPEC §6.4).

The storyboard names an HTML file (relative to storyboard.json) holding <style>, markup and a <script> that defines
build(tl, root, t0, t1). The composer puts the file inside <div class="box" id="<id>"> and calls the function with the
shared timeline, that div, and the scene's times. A lint over the file fails the build when it styles or selects
anything outside #<id>, touches document.body, reaches the network, breaks MOTION.md (a back, elastic or bounce ease,
repeat, yoyo, Math.random), or lacks the function. Libraries: GSAP (always
there), KaTeX and three.js from the local vendor folder.
"""
import os, re
from scenes import js_str, need
from scenes import formula as F

TYPE = "custom"
CSS = ""                      # the file brings its own, scoped under #<id>
THREE = "three/three.module.min.js"
THREE_INSTALL = "npm pack three@0.169.0, then copy its build/three.module.min.js to assets/vendor/three/"
_IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_NETWORK = [(r"\bfetch\s*\(", "fetch("), (r"https?://", "a web address"), (r"\bimport\s*\(", "import()"),
            (r"\bXMLHttpRequest\b", "XMLHttpRequest"), (r"\bWebSocket\b", "WebSocket"), (r"\bsendBeacon\b", "sendBeacon"),
            (r"<\s*(iframe|object|embed)\b", "an embedded page"), (r"\b(eval|Function)\s*\(", "eval / Function"),
            (r"@import\b", "CSS @import"),
            # "//host/x" in a string, url(), or an attribute loads over the web too; a // comment follows a space or a newline
            (r"[('\"`=]\s*//[\w-]+(\.[\w-]+)+", "a web address (//...)")]
# MOTION.md's rules hold here too: no overshoot ease, no endless loop, nothing random (every render must be the same)
_DOCTRINE = [(r"['\"`](back|elastic|bounce)(\.\w+)?(\([^)]*\))?['\"`]", "a %s ease: it overshoots and reads as cheap; use power3 or expo"),
             (r"\brepeat\s*:", "repeat: an endless loop is lazy motion; move only when the voice gives a reason"),
             (r"\byoyo\s*:", "yoyo: a back-and-forth is lazy motion; move only when the voice gives a reason"),
             (r"\bMath\s*\.\s*random\b", "Math.random: a render must be the same every time; use fixed values")]
_MODULE = r"<script\b[^>]*\btype\s*=\s*['\"]?module\b[^>]*>(.*?)</script>"
_DOC = [(r"\bdocument\s*\.\s*body\b", "document.body"), (r"\bdocument\s*\.\s*documentElement\b", "document.documentElement")]
_DOC_SELECT = r"\bdocument\s*\.\s*(querySelector(All)?|getElementById|getElementsBy\w+)\s*\("
_TWEEN_SELECT = r"\b(?:tl|gsap)\s*\.\s*(?:to|from|fromTo|set)\s*\(\s*(['\"`])(.*?)\1"


def validate(scene):
    errs = need(scene, ["box", "html", "build"])
    b = scene.get("box") or {}
    if any(not isinstance(b.get(k), int) for k in ("x", "y", "w", "h")):
        errs.append("box needs whole-pixel x, y, w and h")
    if scene.get("build") and not _IDENT.match(str(scene["build"])):
        errs.append("build %r is not a function name" % scene["build"])
    return errs


def place(scene):
    b = scene["box"]
    return b["x"], b["y"], b["w"], b["h"]


def height(scene, width):
    return scene["box"]["h"]


def min_width(scene):
    return 0


def lint(src, sid, build):
    """The contract's failures, one message each (empty when the file keeps to its box)."""
    errs = []
    scan = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", src)          # an SVG namespace is a name, not a request
    for pat, what in _NETWORK:
        if re.search(pat, scan):
            errs.append("uses %s: a custom scene renders offline, with no network" % what)
    for pat, what in _DOCTRINE:
        m = re.search(pat, src)
        if m:
            errs.append("uses " + (what % m.group(1) if "%s" in what else what))
    for pat, what in _DOC:
        if re.search(pat, src):
            errs.append("touches %s: work inside root (#%s) only" % (what, sid))
    if re.search(_DOC_SELECT, src):
        errs.append("selects from the whole document, outside #%s: use root.querySelector(...) instead" % sid)
    for m in re.finditer(_TWEEN_SELECT, src):
        for sel in m.group(2).split(","):
            if not re.match(r"^\s*#%s\b" % re.escape(sid), sel):
                errs.append("animates %r, outside #%s: pass root.querySelectorAll(...) or a '#%s ...' selector" % (sel.strip(), sid, sid))
    for style in re.findall(r"<style[^>]*>(.*?)</style>", src, re.S | re.I):
        style = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
        for sels in re.findall(r"([^{}]+)\{", style):
            sels = sels.strip()
            if not sels or sels.startswith("@"):
                continue
            for sel in sels.split(","):
                sel = sel.strip()
                if re.match(r"^(from|to|\d+(\.\d+)?%)$", sel):
                    continue
                if not re.match(r"^#%s\b" % re.escape(sid), sel):
                    errs.append("styles %r, outside #%s: start every selector with #%s" % (sel, sid, sid))
    defines = r"\bfunction\s+%s\s*\(|\b%s\s*=\s*(function\b|\()" % (re.escape(build), re.escape(build))
    if not re.search(defines, src):
        errs.append("defines no function %s(tl, root, t0, t1)" % build)
    elif (any(re.search(defines, m) for m in re.findall(_MODULE, src, re.S | re.I))
          and not re.search(r"\bwindow\s*\.\s*%s\s*=" % re.escape(build), src)):
        # a module's top-level names are its own: the page calls window.<build>, which would be undefined
        errs.append("defines %s inside a module script, where the page cannot call it: add window.%s = %s;" % (build, build, build))
    return errs


def render(scene, ctx, box):
    path = scene["html"] if os.path.isabs(scene["html"]) else os.path.join(ctx.spec_dir, scene["html"])
    if not os.path.exists(path):
        ctx.fail("no custom file at %s" % path)
    with open(path) as f:
        src = f.read()
    errs = lint(src, ctx.id, scene["build"])
    if errs:
        ctx.fail("; ".join(dict.fromkeys(errs)))
    if re.search(r"""from\s+['"]three['"]|\bTHREE\b""", src):
        three = ctx.vendor(THREE, THREE_INSTALL)
        ctx.add_head('<script type="importmap">{"imports": {"three": "./%s"}}</script>' % three)
    if re.search(r"\bkatex\s*\.", src):
        ctx.add_head('<link rel="stylesheet" href="%s" />' % ctx.vendor("katex/katex.min.css", F.INSTALL))
        ctx.vendor("katex/fonts", F.INSTALL)
        ctx.add_head('<script src="%s"></script>' % ctx.vendor("katex/katex.min.js", F.INSTALL))
    call = "window.%s(tl, document.getElementById(%s), %.3f, %.3f)" % (scene["build"], js_str(ctx.id), ctx.t_in, ctx.t_out)
    # a module script runs after this one, but before DOMContentLoaded: build then
    js = ["if (window.%s) { %s; } else { document.addEventListener('DOMContentLoaded', function () { %s; }); }" % (scene["build"], call, call)]
    return "\n" + src + "\n", js
