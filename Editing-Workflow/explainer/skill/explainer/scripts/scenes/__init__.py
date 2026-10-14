"""The scene library: one module per scene type (SPEC §6.2).

Each module has
  TYPE                          the storyboard "type"
  CSS                           its styles (scoped by class; the composer adds each used module's CSS once)
  NEEDS_SOURCE                  optional, True when the scene shows a number or a claim
  validate(scene) -> [str]      data-shape errors
  height(scene, width) -> int   the box height at that width, from the module's own CSS constants
  min_width(scene) -> int       the widest text that cannot wrap, plus padding
  render(scene, ctx, box) -> (html, [js])
                                the HTML inside <div class="box" id="<scene id>">, and GSAP lines for the shared `tl`

Every entrance is an opacity 0 -> 1 fromTo with the enter ease (ctx.enter); exits belong to the composer. Staggers
are written as { amount: total } and never pass tokens.motion.stagger_total_max.
"""
import html as _html, importlib, json, math, os, re, shutil

import explainer_lib as E


class SceneError(Exception):
    pass


class Ctx:
    """What a scene needs from the composer: its times, the word anchors, the look, the vendor folder."""

    def __init__(self, scene, t_in, t_out, words, tokens, vendor_dir, out_dir, bg):
        self.scene, self.id = scene, scene["id"]
        self.t_in, self.t_out = t_in, t_out
        self.words, self.tokens = words, tokens
        self.vendor_dir, self.out_dir = vendor_dir, out_dir
        self.bg = bg
        self.ink = tokens["text_on"][bg]
        self.light = bg == "light"

    def fail(self, msg):
        raise SceneError(msg)

    def esc(self, s):
        return _html.escape(str(s), quote=True)

    def at(self, ref):
        """An item time: its word minus the lead, inside the scene's [in, out]."""
        try:
            t = E.resolve(ref, self.words, lead=True)
        except ValueError as e:
            self.fail(str(e))
        if not self.t_in - 1e-6 <= t <= self.t_out + 1e-6:
            self.fail("an item at %s (%.2f s) is outside the scene (%.2f to %.2f s)" % (ref, t, self.t_in, self.t_out))
        return max(0.0, t)

    def item(self, ref):
        """data-at and data-anchor for an item that lands on a word (the kit's beat-check reads both)."""
        t = self.at(ref)
        word = E.anchor_text(ref, self.words)
        return t, (' data-at="%.3f" data-unanchored="1"' % t if word == "-" else ' data-at="%.3f" data-anchor="%s"' % (t, self.esc(word)))

    def vendor(self, name):
        """Stage vendor/<name> next to the page and return its relative path, or fail naming the file."""
        src = os.path.join(self.vendor_dir, name)
        if not os.path.exists(src):
            self.fail("needs vendor/%s (looked in %s)" % (name, self.vendor_dir))
        dst = os.path.join(self.out_dir, "vendor", name)
        if os.path.isdir(src):
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
        return "vendor/" + name

    def enter(self, sel, t, frm=None, to=None, stagger=None, dur=None):
        m = self.tokens["motion"]
        f = dict({"opacity": 0}, **(frm or {}))
        g = dict({"opacity": 1}, **{k: 0 if k in ("x", "y") else 1 for k in (frm or {}) if k in ("x", "y", "scale")})
        g.update(to or {})
        g["duration"] = dur or m["enter"]
        g["ease"] = m["enter_ease"]
        if stagger:
            g["stagger"] = {"amount": round(min(stagger, m["stagger_total_max"]), 3)}
        g["immediateRender"] = False
        return "tl.fromTo(%s, %s, %s, %.3f);" % (sel_js(sel), js_obj(f), js_obj(g), t)


def js_str(s):
    """A JS string literal that cannot end the <script> it sits in."""
    return json.dumps(str(s)).replace("<", "\\u003c")


def sel_js(sel):
    return "'%s'" % sel.replace("\\", "\\\\").replace("'", "\\'")


def js_obj(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, dict):
            parts.append("%s: %s" % (k, js_obj(v)))
        elif isinstance(v, bool):
            parts.append("%s: %s" % (k, "true" if v else "false"))
        elif isinstance(v, (int, float)):
            parts.append("%s: %s" % (k, ("%.3f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else v))
        else:
            parts.append("%s: '%s'" % (k, str(v).replace("\\", "\\\\").replace("'", "\\'")))
    return "{ " + ", ".join(parts) + " }"


def stagger_for(n, each=0.06):
    """The stagger total for n items at `each` apart (the cap is applied in ctx.enter)."""
    return round(each * (n - 1), 3) if n > 1 else None


def line_px(size, lh):
    """The CSS line height in whole pixels (the scenes write line-height in px, so heights add up exactly)."""
    return int(round(size * lh))


def widest(pairs, pad=0):
    """The width of the widest single word among [(text, font size)], plus padding."""
    best = 0
    for text, size in pairs:
        for w in str(text or "").split():
            best = max(best, E.text_width(w, size))
    return int(math.ceil(best)) + pad


def mono_lines(text, size, width, spacing=0.12):
    """Lines a mono label needs: 0.6 em a character plus the letter spacing."""
    return max(1, math.ceil(len(text) * size * (0.6 + spacing) / width))


def need(scene, keys):
    return ["missing %r" % k for k in keys if scene.get(k) in (None, "", [])]


_MODULES = ["title", "number", "count_up"]
REGISTRY = {}
for _m in _MODULES:
    _mod = importlib.import_module("scenes." + _m)
    REGISTRY[_mod.TYPE] = _mod
