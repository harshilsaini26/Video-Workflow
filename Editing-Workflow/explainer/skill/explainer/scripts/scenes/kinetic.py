"""kinetic: the hook as kinetic type, from data, so no reel needs Claude-written code for its first seconds (PLAYBOOK §E4,
MOTION.md §4). A big hero token (a number or a short capital word, the accent), one or two words stacked beside it, an
optional claim line under a rule, a strike that crosses out one word of the line (a red rule, the word dims), and a
punch that lands last (the accent). Every piece rises out of its own mask on the word that says it:

  {"type": "kinetic", "big": {"text": "3", "at": "word:1"}, "words": [{"text": "STEP", "at": ...}, {"text": "TRICK", ...}],
   "line": {"text": "AI INVENTS", "at": ...}, "strike": {"word": "INVENTS", "at": ...}, "punch": {"text": "LESS", "at": ...}}

Each mask is exactly as tall as the font's content area (ascent plus descent), so no letter is ever clipped, and the
stacked masks tuck into each other's empty descender space so the type sits tight. The type sizes itself to the width it
is given and the height of the column it sits in (sizes()): it grows up to 1.8x where there is room and shrinks where a
long hook needs it, and brings its own box (place()): the wide column when it is short enough to stay above y 960, else
the narrow one, whichever gives the bigger type.
"""
import math, re
import explainer_lib as E
from scenes import js_obj, need

TYPE = "kinetic"
GROW = 1.8                        # the hook is the reel's biggest moment: it may grow as far as any scene
BAKED = True                      # its sizes are worked out for the width it is given: measured at that width
WIDE_W, NARROW_W = E.L.SAFE["right"] - E.L.SAFE["left"], E.L.NARROW["right"] - E.L.NARROW["left"]   # 950, 780
ASC, DESC = 0.992, 0.310          # DM Sans 700: the content area is (ASC + DESC) x size
TRACK = -0.02                     # letter-spacing, em
BIG, WORD, LINE, PUNCH = 360, 120, 96, 180
GAP_X = 28                        # big to the words beside it
RULE_T, RULE_H, RULE_B = 36, 8, 22
BIG_RE = re.compile(r"^[0-9A-Z$€£₹%+.,×#-]{1,4}$")


def lh(size):
    return int(math.ceil((ASC + DESC) * size))


def tuck(size):
    return int(round(0.26 * size))   # how far the next mask tucks up into this one's descender space


def _rows(scene):
    """The natural width of each row: the top row (big and words), the line, the punch."""
    w = lambda text, size: E.text_width(text, size, spacing=TRACK)
    top = max([w(x["text"], WORD) for x in scene.get("words") or []] or [0])
    if scene.get("big"):
        top += w(scene["big"]["text"], BIG) + (GAP_X if scene.get("words") else 0)
    return {"top": top, "line": w(scene["line"]["text"], LINE) if scene.get("line") else 0,
            "punch": w(scene["punch"]["text"], PUNCH) if scene.get("punch") else 0}


def budget(width):
    """The height the hook may take at this width: the wide column stays above y 960, the narrow one has the area."""
    room = 2 * E.IDLE_ROOM
    if width > NARROW_W:
        return E.L.RIGHT_COL_TOP - E.SCENE["top"] - room
    return E.SCENE["bottom"] - E.SCENE["top"] - room


def _sizes(k):
    z = lambda v, r: int(round(v * k[r]))
    return {"big": z(BIG, "top"), "word": z(WORD, "top"), "gap": z(GAP_X, "top"), "line": z(LINE, "line"), "punch": z(PUNCH, "punch"),
            "rule_t": z(RULE_T, "top"), "rule_h": max(4, z(RULE_H, "top")), "rule_b": z(RULE_B, "top")}


def sizes(scene, width):
    """Every size at this width: each row grows (to GROW) or shrinks (to half) to fit the width on its own, so a long
    top row does not make the line and the punch small too; then all of them shrink together until the hook fits the
    column's height (budget())."""
    rows = _rows(scene)
    k = {r: max(0.5, min(GROW, (width - 4) / v)) if v else 1.0 for r, v in rows.items()}
    cap = budget(width)
    for _ in range(6):                     # whole-pixel rounding: a few passes settle it
        h = _height(scene, _sizes(k))
        if h <= cap:
            break
        f = cap / float(h) * 0.995
        k = {r: v * f for r, v in k.items()}
    return _sizes(k)


CSS = """
  .kn { width:max-content; max-width:100%%; margin:0 auto; display:flex; flex-direction:column; align-items:flex-start; }
  .kn-row { display:flex; align-items:flex-end; }
  .kn-stack { display:flex; flex-direction:column; }
  .kn-m { overflow:hidden; white-space:nowrap; }
  .kn-m > span { display:block; font-weight:700; letter-spacing:%sem; }
  .kn-rule { width:100%%; transform:scaleX(0); transform-origin:0 50%%; }
  .kn-xw { position:relative; }
  .kn-x { position:absolute; left:-.06em; right:-.06em; height:.11em; transform:scaleX(0); transform-origin:0 50%%; }
""" % TRACK


def normalize(scene):
    """A hero token written into the words ("5 STEPS", "3") becomes the big one: the reel's biggest moment is never set
    at word size because the writer typed it in one line. A big already given is kept."""
    ws = scene.get("words") or []
    if scene.get("big") or not ws or not isinstance(ws[0], dict):
        return scene
    head, _, rest = str(ws[0].get("text", "")).strip().partition(" ")
    if BIG_RE.match(head) and any(ch.isdigit() for ch in head):
        scene["big"] = {"text": head, "at": ws[0].get("at")}
        if rest.strip():
            ws[0] = dict(ws[0], text=rest.strip())
        else:
            ws.pop(0)
        if not ws:
            scene.pop("words", None)
    return scene


def validate(scene):
    errs = []
    if not scene.get("big") and not scene.get("words"):
        errs.append("a kinetic scene needs big or words")
    b = scene.get("big")
    if b and not BIG_RE.match(str(b.get("text", ""))):
        errs.append("big is one short token: a number or capitals, at most 4 characters (got %r)" % b.get("text"))
    ws = scene.get("words") or []
    if scene.get("words") is not None and not 1 <= len(ws) <= 2:
        errs.append("words: one or two (got %d)" % len(ws))
    errs += ["word %d has no text" % i for i, w in enumerate(ws) if not w.get("text")]
    errs += ["word %d has no at" % i for i, w in enumerate(ws) if w.get("at") is None]
    for key in ("line", "punch"):
        part = scene.get(key)
        if part is not None and (not part.get("text") or part.get("at") is None):
            errs.append("%s needs text and at" % key)
    if scene.get("punch") and len(str(scene["punch"].get("text", "")).split()) > 2:
        errs.append("punch: at most two words (got %r)" % scene["punch"]["text"])
    st = scene.get("strike")
    if st:
        line_words = [E.L.norm(w) for w in str((scene.get("line") or {}).get("text", "")).split()]
        if st.get("at") is None or E.L.norm(st.get("word", "")) not in line_words:
            errs.append("strike needs a word of the line and an at (got %r)" % st.get("word"))
    return errs


def _row1(scene, z):
    words = scene.get("words") or []
    stack = len(words) * lh(z["word"]) - max(0, len(words) - 1) * tuck(z["word"])
    if scene.get("big"):
        return max(lh(z["big"]), stack + int(round(DESC * (z["big"] - z["word"]))))   # the words' baseline sits on the big token's
    return stack


def height(scene, width):
    return _height(scene, sizes(scene, width))


def _height(scene, z):
    h = _row1(scene, z)
    if scene.get("line"):
        h += z["rule_t"] + z["rule_h"] + z["rule_b"] + lh(z["line"])
    if scene.get("punch"):
        h += lh(z["punch"]) - tuck(z["line"] if scene.get("line") else z["word"])
    return h


def min_width(scene):
    return int(math.ceil(max(_rows(scene).values()) * 0.5)) + 4


def place(scene):
    """Its own box: the column (wide above y 960, else narrow) that gives the bigger type, centred like any scene."""
    best = None
    for left, width in ((E.L.SAFE["left"], WIDE_W), (E.L.NARROW["left"], NARROW_W)):
        if min_width(scene) > width:
            continue
        z, h = sizes(scene, width), height(scene, width)
        if h > budget(width):
            continue
        lead = z["big"] if scene.get("big") else z["word"] if scene.get("words") else z["line"]
        if best is None or lead > best[0]:
            centre = (E.SCENE["top"] + (E.L.RIGHT_COL_TOP if width > NARROW_W else E.SCENE["bottom"])) // 2
            best = (lead, (left, int(round(centre - h / 2.0)), width, h))
    if best is None:
        if min_width(scene) > NARROW_W:
            raise ValueError("a row of it is about %d px wide at half size, wider than the %d px column; shorten it"
                             % (min_width(scene), NARROW_W))
        raise ValueError("the hook does not fit the scene area at half its size: shorten it")
    return best[1]


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    z = sizes(scene, box[2])
    js = []

    def rise(sel, at, size, color, cls, text, extra=""):
        t, attrs = ctx.item(at) if at is not None else (ctx.t_in, "")
        # below its mask from the start (set through GSAP: a CSS translate would be read as pixels and never undone)
        js.append("tl.set('%s', { yPercent: 110 }, 0);" % sel)
        js.append("tl.fromTo('%s', { yPercent: 110 }, %s, %.3f);" % (sel, js_obj({"yPercent": 0, "duration": 0.6, "ease": "expo.out",
                                                                               "immediateRender": False}), t))
        return t, ('<div class="kn-m" style="height:%dpx%s"><span class="%s" id="%s"%s style="color:%s;font-size:%dpx;line-height:%dpx">%s</span></div>'
                   % (lh(size), extra, cls, sel[1:], attrs, color, size, lh(size), text))

    words = scene.get("words") or []
    stack = []
    for i, w in enumerate(words):
        _, h = rise("#%s-w%d" % (sid, i), w["at"], z["word"], ctx.ink, "kn-w", ctx.esc(w["text"]),
                    ";margin-top:-%dpx" % tuck(z["word"]) if i else "")
        stack.append(h)
    row = []
    if scene.get("big"):
        _, h = rise("#%s-b" % sid, scene["big"].get("at"), z["big"], c["accent"], "kn-big", ctx.esc(scene["big"]["text"]))
        row.append(h)
    if stack:
        pad = int(round(DESC * (z["big"] - z["word"]))) if scene.get("big") else 0
        row.append('<div class="kn-stack" style="padding-bottom:%dpx;margin-left:%dpx">%s</div>'
                   % (pad, z["gap"] if scene.get("big") else 0, "".join(stack)))
    parts = ['<div class="kn-row" style="height:%dpx">%s</div>' % (_row1(scene, z), "".join(row))]
    if scene.get("line"):
        ln, st = scene["line"], scene.get("strike")
        text = []
        for w in ln["text"].split():
            if st and E.L.norm(w) == E.L.norm(st["word"]):
                ts, attrs = ctx.item(st["at"])
                mid = int(round((ASC - 0.36) * z["line"]))     # the middle of the letters, from the top of the mask
                text.append('<span class="kn-xw" id="%s-xw">%s<i class="kn-x" id="%s-x"%s style="top:%dpx;background:%s"></i></span>'
                            % (sid, ctx.esc(w), sid, attrs, mid, c["bad"]))
                js.append("tl.fromTo('#%s-x', { scaleX: 0 }, %s, %.3f);" % (sid, js_obj({"scaleX": 1, "duration": 0.32, "ease": "power3.inOut",
                                                                                      "immediateRender": False}), ts))
                js.append("tl.to('#%s-xw', %s, %.3f);" % (sid, js_obj({"color": c["muted"], "duration": 0.3, "ease": "power3.out"}), ts + 0.15))
            else:
                text.append(ctx.esc(w))
        t_line, h = rise("#%s-l" % sid, ln["at"], z["line"], ctx.ink, "kn-l", " ".join(text))
        rule_t = max(ctx.t_in, t_line - 0.25)
        parts.append('<div class="kn-rule" id="%s-r" style="height:%dpx;margin:%dpx 0 %dpx;background:%s"></div>'
                     % (sid, z["rule_h"], z["rule_t"], z["rule_b"], c["line"]))
        js.append("tl.fromTo('#%s-r', { scaleX: 0 }, %s, %.3f);" % (sid, js_obj({"scaleX": 1, "duration": 0.5, "ease": "power3.out",
                                                                              "immediateRender": False}), rule_t))
        parts.append(h)
    if scene.get("punch"):
        _, h = rise("#%s-p" % sid, scene["punch"]["at"], z["punch"], c["accent"], "kn-p", ctx.esc(scene["punch"]["text"]),
                    ";margin-top:-%dpx" % tuck(z["line"] if scene.get("line") else z["word"]))
        parts.append(h)
    return '<div class="kn" style="height:%dpx">%s</div>' % (height(scene, box[2]), "".join(parts)), js
