"""comment-cta: "Comment KEYWORD". A small mono kicker, the keyword big on an accent chip, a comment box (light paper UI,
on any ground) where the keyword types in character by character, and one line saying what the viewer gets. For the
call to action at the end of a reel: "comment GUIDE and I'll send you the checklist".

  {"type": "comment-cta", "keyword": {"text": "GUIDE", "at": "word:3"}, "gets": {"text": "The free checklist, in your DMs", "at": "word:6"}}

On the keyword's word the chip lands and the keyword types into the box, a character every TYPE_STEP seconds, the caret
riding after it; once it is typed, Post turns to the accent. The caret blinks while the box waits and while it holds.
`kicker` (default "COMMENT") and `placeholder` (default "Add a comment…") may be changed.
"""
import math, re
import explainer_lib as E
from scenes import js_obj, line_px, need, widest

TYPE = "comment-cta"
DECOR_KEYS = {"placeholder"}
K_SIZE, K_LH, K_TRACK, K_GAP = 30, 40, 0.24, 24       # kicker: JetBrains Mono 500
C_SIZE, C_MIN, C_H, C_PAD, C_TRACK = 96, 64, 150, 56, 0.01   # the keyword chip: DM Sans 700, smaller for a long word
B_GAP, B_H, B_PAD = 46, 120, 22                       # the comment box, a pill
AV, AV_GAP = 76, 22                                   # the avatar in it
T_SIZE, P_SIZE = 42, 38                               # typed keyword (700), placeholder (500)
CARET_W, CARET_H, CARET_GAP = 4, 50, 4
POST_SIZE, POST_GAP = 34, 24                          # Post, at the right
G_GAP, G_SIZE, G_LH = 42, 46, 1.25                    # what the viewer gets: DM Sans 700
TYPE_STEP = 0.07
MAX_KEY = 14
_KEY = re.compile(r"^\S+$")

CSS = """
  .cc { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .cc-k { height:%dpx; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:%sem;
    margin-right:-%sem; text-transform:uppercase; white-space:nowrap; opacity:0; }
  .cc-chip { height:%dpx; margin-top:%dpx; padding:0 %dpx; border-radius:40px; display:flex; align-items:center; font-weight:700;
    line-height:1; letter-spacing:%sem; white-space:nowrap; opacity:0; }
  .cc-box { width:100%%; height:%dpx; margin-top:%dpx; border-radius:%dpx; display:flex; align-items:center; padding:0 %dpx 0 %dpx;
    gap:%dpx; opacity:0; }
  .cc-av { width:%dpx; height:%dpx; flex:none; border-radius:50%%; display:flex; align-items:center; justify-content:center; }
  .cc-av svg { width:44px; height:44px; }
  .cc-in { position:relative; flex:1 1 0; min-width:0; height:100%%; display:flex; align-items:center; white-space:nowrap; }
  .cc-ph { position:absolute; left:%dpx; top:0; height:100%%; display:flex; align-items:center; font-weight:500; font-size:%dpx; }
  .cc-typed { font-weight:700; font-size:%dpx; line-height:1; }
  .cc-typed > span { display:none; }
  .cc-caret { width:%dpx; height:%dpx; margin-left:%dpx; flex:none; border-radius:2px; opacity:0; }
  .cc-post { flex:none; font-weight:700; font-size:%dpx; line-height:1; }
  .cc-g { width:100%%; margin-top:%dpx; text-wrap:balance; font-weight:700; font-size:%dpx; line-height:%dpx; text-align:center; opacity:0; }
""" % (K_LH, K_SIZE, K_LH, K_TRACK, K_TRACK,
       C_H, K_GAP, C_PAD, C_TRACK,
       B_H, B_GAP, B_H // 2, B_PAD + 14, B_PAD, AV_GAP,
       AV, AV,
       CARET_W + CARET_GAP + 6, P_SIZE,
       T_SIZE,
       CARET_W, CARET_H, CARET_GAP,
       POST_SIZE,
       G_GAP, G_SIZE, line_px(G_SIZE, G_LH))

# Lucide's user (ISC): the viewer's own avatar in the box
USER_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>')


def _part(scene, key):
    p = scene.get(key)
    return (p.get("text"), p.get("at")) if isinstance(p, dict) else (None, None)


def validate(scene):
    errs = need(scene, ["keyword", "gets"])
    kw, kat = _part(scene, "keyword")
    if scene.get("keyword") is not None:
        if not kw or kat is None:
            errs.append("keyword is {text, at}: the word to comment, on the word the voice says it")
        elif not _KEY.match(str(kw)) or len(str(kw)) > MAX_KEY:
            errs.append("keyword: one word of at most %d characters (got %r)" % (MAX_KEY, kw))
    g, gat = _part(scene, "gets")
    if scene.get("gets") is not None and (not g or gat is None):
        errs.append("gets is {text, at}: what the viewer gets, on its word")
    elif g and len(str(g).split()) > 9:
        errs.append("gets: one short line, at most nine words (got %r)" % g)
    if len(str(scene.get("kicker") or "")) > 20:
        errs.append("kicker: at most 20 characters")
    return errs


def _kicker(scene):
    return str(scene.get("kicker") or "COMMENT")


def _placeholder(scene):
    return str(scene.get("placeholder") or "Add a comment…")


def chip_size(kw, width):
    """The keyword's size on its chip: C_SIZE, or as large as fits the width (down to C_MIN; the chip's height stays)."""
    room = (width - 2 * C_PAD - 4) / max(1e-6, E.text_width(kw, 1.0, spacing=C_TRACK))
    return int(max(C_MIN, min(C_SIZE, math.floor(room))))


def height(scene, width):
    g, _ = _part(scene, "gets")
    return K_LH + K_GAP + C_H + B_GAP + B_H + G_GAP + line_px(G_SIZE, G_LH) * E.text_lines(g, G_SIZE, width)


def min_width(scene):
    kw, _ = _part(scene, "keyword")
    g, _ = _part(scene, "gets")
    chip = int(math.ceil(E.text_width(kw, C_MIN, spacing=C_TRACK))) + 2 * C_PAD + 4
    inner = max(E.text_width(kw, T_SIZE) + CARET_GAP + CARET_W, CARET_W + CARET_GAP + 6 + E.text_width(_placeholder(scene), P_SIZE, "display500"))
    box = int(math.ceil(B_PAD + 14 + AV + AV_GAP + inner + AV_GAP + E.text_width("Post", POST_SIZE) + B_PAD)) + 6
    kick = int(math.ceil(len(_kicker(scene)) * K_SIZE * (0.6 + K_TRACK)))
    return max(chip, box, kick, widest([(g, G_SIZE)]) + 2)


def render(scene, ctx, box):
    c, p, mo, sid = ctx.c, ctx.pc, ctx.tokens["motion"], ctx.id
    kw, kat = _part(scene, "keyword")
    g, gat = _part(scene, "gets")
    tk, k_attrs = ctx.item(kat)
    tg, g_attrs = ctx.item(gat)
    if tg < tk - 1e-6:
        ctx.fail("gets (%s) comes before the keyword (%s): say the keyword first" % (gat, kat))
    chars = "".join('<span id="%s-c%d">%s</span>' % (sid, i, ctx.esc(ch)) for i, ch in enumerate(kw))
    html = ('<div class="cc-k" id="%s-k" style="color:%s">%s</div>'
            '<div class="cc-chip" id="%s-chip"%s style="font-size:%dpx;background:%s;color:%s;box-shadow:%s">%s</div>'
            '<div class="cc-box" id="%s-box" style="%s">'
            '<div class="cc-av" style="background:%s;color:%s">%s</div>'
            '<div class="cc-in"><span class="cc-ph" id="%s-ph" style="color:%s">%s</span>'
            '<span class="cc-typed" id="%s-typed" style="color:%s">%s</span><i class="cc-caret" id="%s-caret" style="background:%s"></i></div>'
            '<span class="cc-post" id="%s-post" style="color:%s">Post</span></div>'
            '<div class="cc-g" id="%s-g"%s style="color:%s">%s</div>'
            % (sid, c["dim"], ctx.esc(_kicker(scene)),
               sid, k_attrs, chip_size(kw, box[2]), c["fill"], c["on_fill"], c["shadow"], ctx.esc(kw),
               sid, ctx.paper_card(),
               p["accent_soft"], p["accent"], USER_SVG,
               sid, p["dim"], ctx.esc(_placeholder(scene)),
               sid, p["ink"], chars, sid, p["accent"],
               sid, p["muted"],
               sid, g_attrs, ctx.ink, ctx.esc(g)))
    t0 = ctx.t_in
    js = [ctx.enter("#%s-k" % sid, t0, {"y": 14}),
          ctx.enter("#%s-box" % sid, t0 + 0.1, {"y": 30}),
          "tl.set('#%s-caret', { opacity: 1 }, %.3f);" % (sid, t0 + 0.3)]
    # the keyword: the chip lands as its first letter types in
    js.append(ctx.enter("#%s-chip" % sid, tk, {"y": 30, "scale": 0.86}, dur=0.5))
    js.append("tl.set('#%s-ph', { opacity: 0 }, %.3f);" % (sid, tk))
    for i in range(len(kw)):
        js.append("tl.set('#%s-c%d', { display: 'inline' }, %.3f);" % (sid, i, tk + i * TYPE_STEP))
    typed = tk + len(kw) * TYPE_STEP
    js.append("tl.to('#%s-post', %s, %.3f);" % (sid, js_obj({"color": p["accent"], "duration": 0.25, "ease": mo["enter_ease"]}), typed + 0.1))
    js.append(ctx.enter("#%s-g" % sid, tg, {"y": 20}))
    # the caret blinks while the box waits for its word and while the card holds (ambient: never a change)
    for a, b in ((t0 + 0.8, tk - 0.1), (typed + 0.6, ctx.t_out - 0.2)):
        t = a
        while t + 1.0 <= b:
            ctx.ambient("tl.to('#%s-caret', { opacity: 0, duration: 0.08, ease: 'power1.inOut' }, %.3f);" % (sid, t))
            ctx.ambient("tl.to('#%s-caret', { opacity: 1, duration: 0.08, ease: 'power1.inOut' }, %.3f);" % (sid, t + 0.5))
            t += 1.0
    return '<div class="cc">%s</div>' % html, js
