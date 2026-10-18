"""stat: a hero figure ("8 HOURS", "+$363", "2 WEEKS"): a giant number counts up from zero on its word, the unit inline
beside it and a label line under it.

Every digit sits in a cell as wide as the widest digit, and the figure is right-aligned in a box as wide as the final
number: the count never jumps, nothing beside it moves, and its widest moment is its final width. Leading cells stay
out of the row until the count reaches them, so the prefix hugs the first digit. The number is 260 px when it fits the
narrow column, smaller (down to 150 px: the paper look's wide face) when it is long; the composer then scales it up
(at most 1.4x, to 320 px) on the frame.

  {"type": "stat", "value": 363, "prefix": "+$", "unit": "a month", "label": "what the average user saves",
   "at": "word:5", "source": "s1"}
"""
import json
import explainer_lib as E
from scenes import js_obj, line_px, need, widest

TYPE = "stat"
HERO_CSS = ".stat-fig, .stat-unit"   # the figure, in the look's hero face (E.hero()), measured with its glyphs
NEEDS_SOURCE = True
SIZES = (260, 250, 240, 230, 220, 210, 200, 190, 180, 170, 160, 150)   # the number, the hero face, line height 1: the largest that fits
NARROW, WIDE = 780, 950
DRAWN_MAX = 320                  # the most the number is drawn at, after the composer's scale
UNIT = 84 / 260.0                # the unit, inline on the number's baseline, at this share of its size
U_GAP = 0.1                      # number to unit, in the number's em
L_SIZE, L_LH, L_GAP = 48, 1.2, 26
COUNT = 1.2                      # seconds the count takes (shorter when the scene is)
SLACK = 2                        # px of room in the figure's box, for the browser's rounding

CSS = """
  .stat { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .stat-line { display:flex; align-items:baseline; justify-content:center; white-space:nowrap; opacity:0; }
  .stat-fig { flex:none; display:flex; justify-content:flex-end; align-items:baseline; font-weight:700; letter-spacing:0; }
  .stat-fig span { flex:none; display:inline-block; }
  .stat-c { text-align:center; }
  .stat-unit { flex:none; font-weight:700; }
  .stat-label { width:100%%; font-weight:500; font-size:%dpx; line-height:%dpx; margin-top:%dpx; text-align:center; opacity:0; }
""" % (L_SIZE, line_px(L_SIZE, L_LH), L_GAP)


def _final(scene):
    return ("{:,.%df}" % int(scene.get("decimals", 0))).format(float(scene["value"]))


def _cell(ch):
    """The width of a cell, in em: a digit's is the widest digit's, so the count never moves."""
    g = E.glyphs()[E.hero()["glyphs"]]
    return max(g[d] for d in "0123456789") if ch.isdigit() else g.get(ch, 0.6)


def _unit(size):
    return int(round(size * UNIT)), int(round(size * U_GAP))


def fig_width(scene, size):
    """The figure's box: the prefix, one cell per character of the final number, the suffix (px)."""
    cells = sum(_cell(c) for c in _final(scene)) * size
    f = E.hero()["glyphs"]
    return int(cells + E.text_width(scene.get("prefix", ""), size, f) + E.text_width(scene.get("suffix", ""), size, f)) + SLACK


def line_width(scene, size):
    """The figure and its unit: the same at every moment of the count."""
    w = fig_width(scene, size)
    if scene.get("unit"):
        u, gap = _unit(size)
        w += gap + int(E.text_width(scene["unit"], u, E.hero()["glyphs"])) + 1
    return w


def size(scene):
    """The number's size: the largest that fits the narrow column, else the largest that fits the full width."""
    for col in (NARROW, WIDE):
        for s in SIZES:
            if line_width(scene, s) <= col:
                return s
    return SIZES[-1]


def max_scale(scene):
    return min(1.4, DRAWN_MAX / float(size(scene)))


def validate(scene):
    errs = need(scene, ["value"])
    if errs:
        return errs
    try:
        v = float(scene["value"])
    except (TypeError, ValueError):
        return ["value %r is not a number" % (scene["value"],)]
    if v < 0:
        errs.append("value is 0 or more (a sign goes in prefix: \"+$\", \"-\")")
    if not 0 <= int(scene.get("decimals", 0)) <= 3:
        errs.append("decimals is 0 to 3")
    for k, most in (("prefix", 3), ("suffix", 3), ("unit", 14)):
        if len(str(scene.get(k, ""))) > most:
            errs.append("%s is at most %d characters (got %r)" % (k, most, scene[k]))
    if any(c.isdigit() for c in str(scene.get("prefix", "")) + str(scene.get("suffix", "")) + str(scene.get("unit", ""))):
        errs.append("the digits go in value; prefix, suffix and unit are words and signs")
    return errs


def height(scene, width):
    h = size(scene)
    if scene.get("label"):
        h += L_GAP + line_px(L_SIZE, L_LH) * E.text_lines(scene["label"], L_SIZE, width, "display500")
    return h


def min_width(scene):
    return max(line_width(scene, size(scene)), widest([(scene.get("label"), L_SIZE)]))


def render(scene, ctx, box):
    sid = ctx.id
    s = size(scene)
    u, gap = _unit(s)
    dec = int(scene.get("decimals", 0))
    final = _final(scene)
    zero = ("{:,.%df}" % dec).format(0)
    cells = []
    for k, ch in enumerate(final):
        j = k - (len(final) - len(zero))
        cells.append('<span class="stat-c" id="%s-c%d" style="width:%.2fpx%s">%s</span>' % (sid, k, _cell(ch) * s, "" if j >= 0 else ";display:none",
                                                                                            ctx.esc(zero[j]) if j >= 0 else ""))
    fig = '<span>%s</span>%s<span>%s</span>' % (ctx.esc(scene.get("prefix", "")), "".join(cells), ctx.esc(scene.get("suffix", "")))
    if scene.get("at") is not None:
        t, attrs = ctx.item(scene["at"])
    else:
        t, attrs = ctx.t_in, ""
    html = ('<div class="stat"><div class="stat-line" id="%s-v"%s style="height:%dpx"><span class="stat-fig" '
            'style="width:%dpx;font-size:%dpx;line-height:%dpx;color:%s">%s</span>'
            % (sid, attrs, s, fig_width(scene, s), s, s, ctx.c["accent"], fig))     # the number is what the voice is talking about
    if scene.get("unit"):
        html += '<span class="stat-unit" style="font-size:%dpx;line-height:%dpx;margin-left:%dpx;color:%s">%s</span>' % (
            u, u, gap, ctx.ink, ctx.esc(scene["unit"]))
    html += "</div>"
    js = [ctx.enter("#%s-v" % sid, t, {"y": 30})]
    if scene.get("label"):
        html += '<div class="stat-label" style="color:%s">%s</div>' % (ctx.c["dim"], ctx.esc(scene["label"]))
        js.append(ctx.enter("#%s .stat-label" % sid, t + 0.15, {"y": 20}))
    html += "</div>"
    start = t + 0.05
    dur = round(max(0.3, min(COUNT, ctx.t_out - start - 0.4)), 3)
    # each frame writes the count into the cells from the right; the cells it has not reached yet stay out of the row
    js.append("const %s_cells = Array.prototype.slice.call(document.querySelectorAll('#%s-v .stat-c'));" % (sid, sid))
    js.append("const %s_set = function (v) { const s = v.toLocaleString('en-US', { minimumFractionDigits: %d, maximumFractionDigits: %d }); "
              "const n = %s_cells.length; for (let i = 0; i < n; i++) { const k = i - (n - s.length); const c = %s_cells[i]; "
              "c.textContent = k >= 0 ? s.charAt(k) : ''; c.style.display = k >= 0 ? '' : 'none'; } };" % (sid, dec, dec, sid, sid))
    js.append("const %s_n = { v: 0 };" % sid)
    js.append("tl.to(%s_n, { v: %s, duration: %.3f, ease: '%s', onUpdate: function () { %s_set(%s); } }, %.3f);"
              % (sid, json.dumps(float(scene["value"])), dur, ctx.tokens["motion"]["enter_ease"], sid,
                 "%s_n.v" % sid if dec else "Math.round(%s_n.v)" % sid, start))
    # counted: each cell closes to its own digit's width (DM Sans has no tabular figures; "24" must not read "2 4")
    g = E.glyphs()[E.hero()["glyphs"]]
    for k, ch in enumerate(final):
        natural = round(g.get(ch, _cell(ch)) * s, 2)
        if natural < _cell(ch) * s - 0.01:
            js.append("tl.fromTo('#%s-c%d', %s, %s, %.3f);" % (sid, k, js_obj({"width": round(_cell(ch) * s, 2)}),
                                                               js_obj({"width": natural, "duration": 0.35, "ease": "power3.out",
                                                                       "immediateRender": False}), start + dur))
    return html, js
