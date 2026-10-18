"""The scene library: one module per scene type (SPEC §6.2).

Each module has
  TYPE                          the storyboard "type"
  CSS                           its styles (scoped by class; the composer adds each used module's CSS once)
  NEEDS_SOURCE                  optional, True when the scene shows a number or a claim
  DECOR_KEYS                    optional, keys whose values are UI furniture (a timecode, a like count): no source needed
  MAX_SCALE / max_scale(scene)  optional, how far the composer may scale it up (default 1.8)
  place(scene)                  optional, its own box (left, top, width, height): never scaled, only checked
  BAKED                         optional, True when its sizes depend on the width it is given (measured at that width)
  travels(scene)                optional, True when its camera moves to each new item (E4 lets it hold longer)
  SHRINK_WIDTH                  optional, True when its width is geometry, not a word (the composer may shrink it to fit)
  validate(scene) -> [str]      data-shape errors
  height(scene, width) -> int   the box height at that width, from the module's own CSS constants
  min_width(scene) -> int       the widest text that cannot wrap, plus padding
  render(scene, ctx, box) -> (html, [js])
                                the HTML inside <div class="box" id="<scene id>">, and GSAP lines for the shared `tl`

Every entrance is an opacity 0 -> 1 fromTo with the enter ease (ctx.enter); exits belong to the composer. Staggers
are written as { amount: total } and never pass tokens.motion.stagger_total_max. A build's pieces wait as empty slots
(ctx.slot, ctx.fill; their words in .gt). Colours come only from ctx.c (this ground) and ctx.pc (light paper, for a UI
mock-up on any ground), never as hex. All text is drawn at 28 px or more (the composer never scales a scene's smallest
CSS font-size under that), and holds 3:1 against what is behind it (gate E5).
"""
import html as _html, importlib, importlib.util, json, math, os, re, shutil, struct

import explainer_lib as E


class SceneError(Exception):
    pass


class Ctx:
    """What a scene needs from the composer: its times, the word anchors, the look, the vendor folder."""

    def __init__(self, scene, t_in, t_out, words, tokens, vendor_dir, out_dir, bg, head=None, spec_dir="."):
        self.spec_dir = spec_dir
        self.scene, self.id = scene, scene["id"]
        self.head = head if head is not None else []   # tags for <head> (stylesheets, library scripts), shared by all scenes
        self.t_in, self.t_out = t_in, t_out
        self.words, self.tokens = words, tokens
        self.vendor_dir, self.out_dir = vendor_dir, out_dir
        self.bg = bg
        self.c = E.theme(tokens, bg)          # the colours, by role (explainer_lib.theme), on this ground
        self.pc = E.theme(tokens, "base")     # light paper: inside a UI mock-up (a window, a sheet, a chat) on any ground
        self.ink = self.c["ink"]
        self.ambient_lines = []   # idle motion (a float, a pulse, a slow turn): on the page, but not a change for pace-check

    def card(self):
        """The style of a card on this background: the card fill, a hairline (an inset ring, so no height changes) and a
        soft shadow."""
        c = self.c
        return "background:%s;box-shadow:inset 0 0 0 2px %s, %s" % (c["card"], c["card_line"], c["shadow"])

    def paper_card(self):
        """A light paper surface on any ground (a window, a sheet, a chat): the paper fill, its hairline, the ground's
        shadow."""
        p = self.pc
        return "background:%s;box-shadow:inset 0 0 0 2px %s, %s" % (p["card"], p["card_line"], self.c["shadow"])

    def ambient(self, line):
        self.ambient_lines.append(line)

    def fail(self, msg):
        raise SceneError(msg)

    def esc(self, s):
        return _html.escape(str(s), quote=True)

    def at(self, ref):
        """An item time: its word minus the lead, inside the scene's [in, out]."""
        try:
            t = max(0.0, E.resolve(ref, self.words, lead=True))   # clamped like the scene's own in
        except ValueError as e:
            self.fail(str(e))
        if not self.t_in - 1e-6 <= t <= self.t_out + 1e-6:
            self.fail("an item at %s (%.2f s) is outside the scene (%.2f to %.2f s)" % (ref, t, self.t_in, self.t_out))
        last = self.t_out - E.EXIT - SEEN
        if t > last + 1e-6 and last > self.t_in:
            self.fail("an item at %s (%.2f s) lands too close to the scene's end to be seen (the exit starts at %.2f s): "
                      "anchor it by %.2f s, or end the scene on a later word" % (ref, t, self.t_out - E.EXIT, last))
        return t

    def item(self, ref):
        """data-at and data-anchor for an item that lands on a word (the kit's beat-check reads both)."""
        t = self.at(ref)
        word = E.anchor_text(ref, self.words)
        return t, (' data-at="%.3f" data-unanchored="1"' % t if word == "-" else ' data-at="%.3f" data-anchor="%s"' % (t, self.esc(word)))

    def vendor(self, name, install=None):
        """Stage vendor/<name> next to the page and return its relative path, or fail naming the file and its install."""
        src = os.path.join(self.vendor_dir, name)
        if not os.path.exists(src):
            self.fail("needs vendor/%s (looked in %s)%s" % (name, self.vendor_dir, "; get it with: %s" % install if install else ""))
        dst = os.path.join(self.out_dir, "vendor", name)
        if os.path.isdir(src):
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
        return "vendor/" + name

    def icon(self, name):
        """A Lucide icon's SVG, inlined from vendor/lucide/<name>.svg (ISC), or fail naming the icon and the install."""
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", str(name)):
            self.fail("icon %r is not a Lucide icon name (lowercase words joined by -)" % (name,))
        path = os.path.join(self.vendor_dir, "lucide", "%s.svg" % name)
        if not os.path.exists(path):
            self.fail("unknown icon %r: no vendor/lucide/%s.svg (browse lucide.dev/icons; get the set with: %s)" % (name, name, LUCIDE_INSTALL))
        with open(path, encoding="utf-8") as f:
            svg = re.sub(r"^(\s*<!--.*?-->)*\s*", "", f.read(), flags=re.S).strip()   # Lucide files open with a licence comment
        if not svg.startswith("<svg") or re.search(r"<script|on\w+=", svg, re.I):
            self.fail("vendor/lucide/%s.svg is not a plain SVG icon" % name)
        return svg

    def slot(self, sel, extra=None):
        """`sel` waits as an empty slot from the scene's in: its outline at opacity SLOT, its words (every `.gt` inside
        it) hidden, so a build that waits for its words never leaves the stage bare and never shows faint text. Its
        entrance then starts from SLOT (ctx.enter(sel, t, {"opacity": SLOT, ...})) and ctx.fill brings the words in."""
        m = self.tokens["motion"]
        return ["tl.set(%s, { opacity: 0 }, 0);" % sel_js(sel + " .gt"),
                "tl.to(%s, %s, %.3f);" % (sel_js(sel), js_obj(dict({"opacity": SLOT}, **dict(extra or {}, duration=m["enter"], ease=m["enter_ease"]))), self.t_in)]

    def fill(self, sel, t):
        """The words of a slot arrive, just after the slot itself fills on its word."""
        m = self.tokens["motion"]
        return "tl.fromTo(%s, { opacity: 0 }, %s, %.3f);" % (sel_js(sel + " .gt"), js_obj({"opacity": 1, "duration": 0.3, "ease": m["enter_ease"],
                                                                                         "immediateRender": False}), t + 0.08)

    def idle(self, sel, t0, t1, props, every=1.6):
        """An idle back-and-forth while a scene holds (ambient: not a change): from t0 to t1, `sel` eases to `props` and
        back every `every` seconds ({"y": -8} floats; {"scale": 1.08} pulses)."""
        t, k = t0, 0
        rest = {p: (1 if p == "scale" else 0) for p in props}
        while t + every <= t1 + 1e-6:
            self.ambient("tl.to(%s, %s, %.3f);" % (sel_js(sel), js_obj(dict(props if k % 2 == 0 else rest, duration=every, ease="sine.inOut")), t))
            t, k = t + every, k + 1

    def asset(self, rel):
        """Copy a project file (a path relative to storyboard.json) next to the page as assets/<id>-<name>; returns
        (the page's relative path, the source's full path), or fails naming the missing file."""
        src = rel if os.path.isabs(rel) else os.path.join(self.spec_dir, rel)
        if not os.path.isfile(src):
            self.fail("no file at %s (paths are relative to storyboard.json: %s)" % (rel, src))
        name = "%s-%s" % (self.id, os.path.basename(src))
        os.makedirs(os.path.join(self.out_dir, "assets"), exist_ok=True)
        shutil.copy(src, os.path.join(self.out_dir, "assets", name))
        return "assets/" + name, src

    def add_head(self, tag):
        if tag not in self.head:
            self.head.append(tag)

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


SEEN = 0.3          # an item is on screen at least this long before its scene's exit begins
SLOT = 0.4        # how strong a piece's empty outline is before its word (its words stay hidden until then)
LUCIDE_INSTALL = "npm pack lucide-static@0.454.0, then copy its icons/*.svg to assets/vendor/lucide/"


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


def png_size(path):
    """(width, height) from a PNG's header, or None when the file is not a PNG."""
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def stagger_for(n, each=0.06):
    """The stagger total for n items at `each` apart (the cap is applied in ctx.enter)."""
    return round(each * (n - 1), 3) if n > 1 else None


def line_px(size, lh):
    """The CSS line height in whole pixels (the scenes write line-height in px, so heights add up exactly)."""
    return int(round(size * lh))


def widest(pairs, pad=0, font="display700", spacing=0.0):
    """The width of the widest single word among [(text, font size)], plus padding (font: a glyphs() table, such as
    E.hero()["glyphs"] for words set in the look's hero face)."""
    best = 0
    for text, size in pairs:
        for w in str(text or "").split():
            best = max(best, E.text_width(w, size, font, spacing=spacing))
    return int(math.ceil(best)) + pad


def mono_lines(text, size, width, spacing=0.12):
    """Lines a mono label needs: 0.6 em a character plus the letter spacing."""
    return max(1, math.ceil(len(text) * size * (0.6 + spacing) / width))


def need(scene, keys):
    return ["missing %r" % k for k in keys if scene.get(k) in (None, "", [])]


def discover(folder, package="scenes"):
    """{TYPE: module} for every scenes module in `folder`: each <name>.py (not _private) that sets TYPE. A new scene is a
    new file; nothing else to edit. Files without a TYPE (helpers, notes) are left alone."""
    found = {}
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".py") or f.startswith("_"):
            continue
        name = f[:-3]
        if package == "scenes":
            mod = importlib.import_module("scenes." + name)
        else:
            spec = importlib.util.spec_from_file_location("%s.%s" % (package, name), os.path.join(folder, f))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        if isinstance(getattr(mod, "TYPE", None), str):
            if mod.TYPE in found:
                raise ImportError("two scene modules say TYPE %r: %s and %s" % (mod.TYPE, found[mod.TYPE].__name__, mod.__name__))
            found[mod.TYPE] = mod
    return found


REGISTRY = discover(os.path.dirname(os.path.abspath(__file__)))
