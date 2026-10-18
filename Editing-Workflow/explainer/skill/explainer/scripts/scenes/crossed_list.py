"""crossed-list: what is not there ("NO CHARGING CASE / NO BATTERY / NO WIRES"). Two to five rows in the look's hero face,
left-aligned, each rising through its own mask on its word, a small mono prefix in the accent over each one. On a row's
strike word a 6 px accent line draws through its words (left to right, line after line when it wraps) and the row greys
to the muted role. While it holds, the list floats gently, so nothing on it is ever still for long.

  {"type": "crossed-list", "prefix": "NO", "items": [{"text": "CHARGING CASE", "at": "word:3", "strike": "word:5"},
                                                     {"text": "BATTERY", "at": "word:7"}]}

The rows land in order, top to bottom; a strike comes on or after its own row's word.
"""
import math
import explainer_lib as E
from scenes import js_obj, line_px, need, widest

TYPE = "crossed-list"
DECOR_KEYS = {"strike"}               # a strike's word anchor ("word:5") is not on screen
HERO_CSS = ".cl-t"                    # the rows, in the look's hero face (E.hero()), measured with its glyphs
MAX_SCALE = 1.6                       # two short rows grow to about 110 px, never poster-sized
R_SIZE, R_LH, TRACK = 68, 1.1, -0.02  # a row: the hero face, letter-spaced like kinetic
P_SIZE, P_LH, P_GAP, P_TRACK = 30, 36, 4, 0.18   # the prefix: JetBrains Mono 500, letter-spaced
ROW_GAP = 24
MASK = 12                             # px the mask reaches past each row's box (no glyph is clipped at rest)
RISE = 120                            # the row waits this far below its mask (yPercent: past the mask's reach)
STRIKE = 6                            # the line through a struck row, px
MAX_PREFIX, MAX_WORDS = 12, 6

CSS = """
  .cl { width:max-content; max-width:100%%; margin:0 auto; display:flex; flex-direction:column; align-items:flex-start; gap:%dpx; }
  .cl-m { overflow:hidden; padding:%dpx %dpx; margin:-%dpx -%dpx; max-width:calc(100%% + %dpx); }
  .cl-p { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:%sem; white-space:nowrap;
    margin-bottom:%dpx; }
  .cl-x { font-size:%dpx; line-height:%dpx; }
  .cl-t { font-weight:700; letter-spacing:%sem; background-repeat:no-repeat; background-position:0 52%%; background-size:0%% %dpx; }
""" % (ROW_GAP, MASK, MASK, MASK, MASK, 2 * MASK, P_SIZE, P_LH, P_TRACK, P_GAP, R_SIZE, line_px(R_SIZE, R_LH), TRACK, STRIKE)


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items") or []
    if not isinstance(items, list) or not 2 <= len(items) <= 5:
        return errs + ["crossed-list takes 2 to 5 items (got %d)" % (len(items) if isinstance(items, list) else 0)]
    for i, it in enumerate(items):
        if not isinstance(it, dict) or not str(it.get("text") or "").strip() or it.get("at") is None:
            errs.append("item %d needs text and at" % i)
            continue
        if len(str(it["text"]).split()) > MAX_WORDS:
            errs.append("item %d: at most %d words (got %r)" % (i, MAX_WORDS, it["text"]))
    p = scene.get("prefix")
    if p is not None and (not str(p).strip() or len(str(p)) > MAX_PREFIX):
        errs.append("prefix: a short label over each row, 1 to %d characters (got %r)" % (MAX_PREFIX, p))
    return errs


def _lines(text, width):
    return E.text_lines(text, R_SIZE, width, E.hero()["glyphs"], spacing=TRACK)


def _prefix_w(scene):
    return int(math.ceil(len(str(scene.get("prefix") or "")) * P_SIZE * (0.6 + P_TRACK)))


def height(scene, width):
    head = P_LH + P_GAP if scene.get("prefix") else 0
    rows = [head + line_px(R_SIZE, R_LH) * _lines(it["text"], width) for it in scene["items"]]
    return sum(rows) + ROW_GAP * (len(rows) - 1)


def min_width(scene):
    return max(widest([(it["text"], R_SIZE) for it in scene["items"]], 4, font=E.hero()["glyphs"], spacing=TRACK), _prefix_w(scene) + 4)


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    rows, js, prev = [], [], None
    first = None
    for i, it in enumerate(scene["items"]):
        t, attrs = ctx.item(it["at"])
        if prev is not None and t < prev[0] - 1e-6:
            ctx.fail("the items land in order, top to bottom: item %d (%s) lands before item %d (%s)" % (i, it["at"], prev[1], prev[2]))
        prev = (t, i, it["at"])
        first = t if first is None else first
        head = ('<div class="cl-p" style="color:%s">%s</div>' % (c["accent"], ctx.esc(scene["prefix"]))) if scene.get("prefix") else ""
        s_attrs = ""
        if it.get("strike") is not None:
            ts, s_attrs = ctx.item(it["strike"])
            if ts < t - 1e-6:
                ctx.fail("item %d's strike (%s) comes before it lands (%s)" % (i, it["strike"], it["at"]))
            # the line draws through the words on the strike word, then the words grey
            js.append("tl.fromTo('#%s-t%d', { backgroundSize: '0%% %dpx' }, %s, %.3f);"
                      % (sid, i, STRIKE, js_obj({"backgroundSize": "100%% %dpx" % STRIKE, "duration": 0.3, "ease": "power3.inOut",
                                                 "immediateRender": False}), ts))
            js.append("tl.to('#%s-t%d', %s, %.3f);" % (sid, i, js_obj({"color": c["muted"], "duration": 0.35, "ease": "power3.out"}), ts + 0.15))
        text = ('<span class="cl-t" id="%s-t%d"%s style="color:%s;background-image:linear-gradient(%s, %s)">%s</span>'
                % (sid, i, s_attrs, ctx.ink, c["accent"], c["accent"], ctx.esc(it["text"])))
        rows.append('<div class="cl-m"><div class="cl-r" id="%s-r%d"%s>%s<div class="cl-x">%s</div></div></div>' % (sid, i, attrs, head, text))
        # below its mask from the start (through GSAP, so the probe and every seek agree), then up on its word
        js.append("tl.set('#%s-r%d', { yPercent: %d }, 0);" % (sid, i, RISE))
        js.append("tl.fromTo('#%s-r%d', { yPercent: %d }, %s, %.3f);" % (sid, i, RISE, js_obj({"yPercent": 0, "duration": 0.6, "ease": "expo.out",
                                                                                            "immediateRender": False}), t))
    # while it holds: the list floats, a slow back-and-forth to the scene's end
    ctx.idle("#%s .cl" % sid, first + 0.6, ctx.t_out, {"y": -8})
    return '<div class="cl">%s</div>' % "".join(rows), js
