"""title-card: a cinematic chapter card. A small mono kicker ("PART 2", "STEP 3") with thin rules that draw out from it
to each side, a big title whose words rise out of their own masks, and an optional subtitle. For the turn between two
parts of a reel: "part two: building the model".

  {"type": "title-card", "kicker": "PART 2", "title": "Build the model", "subtitle": {"text": "Three statements, one sheet", "at": "word:5"}}

The kicker, the rules and the title land as one moment on the scene's own word; the subtitle lands with them, or on its
own word when it is {"text", "at"}. The kicker is a chapter mark, not a claim (DECOR_KEYS): "PART 2" needs no source.
"""
import math
import explainer_lib as E
from scenes import js_obj, line_px, need, widest

TYPE = "title-card"
DECOR_KEYS = {"kicker"}               # a chapter number is furniture, not a claim
HERO = 150                            # the title grows to this size at most
K_SIZE, K_LH, K_TRACK = 30, 40, 0.24  # kicker: JetBrains Mono 500, letter-spaced
RULE_H, RULE_GAP, RULE_MAX, RULE_MIN = 3, 28, 200, 48
T_SIZE, T_LH, T_TRACK = 104, 1.06, -0.02   # title: DM Sans 700
K_GAP = 36                            # kicker row to title
S_SIZE, S_LH, S_GAP = 44, 1.3, 30     # subtitle: DM Sans 500
MAX_KICKER = 24

CSS = """
  .tc { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .tc-row { width:100%%; height:%dpx; display:flex; align-items:center; justify-content:center; gap:%dpx; }
  .tc-rule { flex:1 1 0; max-width:%dpx; min-width:%dpx; height:%dpx; border-radius:2px; transform:scaleX(0); }
  .tc-rule.l { transform-origin:100%% 50%%; } .tc-rule.r { transform-origin:0 50%%; }
  .tc-k { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:%sem; white-space:nowrap;
    text-transform:uppercase; margin-right:-%sem; opacity:0; }
  .tc-t { width:100%%; margin-top:%dpx; text-wrap:balance; font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:%sem; text-align:center; }
  .tc-t .w { display:inline-block; }
  .tc-s { width:100%%; margin-top:%dpx; text-wrap:balance; font-weight:500; font-size:%dpx; line-height:%dpx; text-align:center; opacity:0; }
""" % (K_LH, RULE_GAP, RULE_MAX, RULE_MIN, RULE_H, K_SIZE, K_LH, K_TRACK, K_TRACK,
       K_GAP, T_SIZE, line_px(T_SIZE, T_LH), T_TRACK, S_GAP, S_SIZE, line_px(S_SIZE, S_LH))


def max_scale(scene):
    return max(1.0, HERO / float(T_SIZE))


def _sub(scene):
    s = scene.get("subtitle")
    if isinstance(s, dict):
        return s.get("text"), s.get("at")
    return s, None


def validate(scene):
    errs = need(scene, ["kicker", "title"])
    k = str(scene.get("kicker") or "")
    if len(k) > MAX_KICKER:
        errs.append("kicker: at most %d characters, a chapter mark like PART 2 (got %d)" % (MAX_KICKER, len(k)))
    if len(str(scene.get("title") or "").split()) > 6:
        errs.append("title: at most six words on a chapter card (got %r)" % scene.get("title"))
    s = scene.get("subtitle")
    if s is not None and not (isinstance(s, str) and s.strip()) and not (isinstance(s, dict) and str(s.get("text") or "").strip()):
        errs.append("subtitle is a line of text, or {text, at}")
    if isinstance(s, dict) and s.get("at") is None:
        errs.append("subtitle {text, at} needs at (or give the text alone to land it with the card)")
    return errs


def _kicker_w(scene):
    return int(math.ceil(len(str(scene["kicker"])) * K_SIZE * (0.6 + K_TRACK)))


def height(scene, width):
    h = K_LH + K_GAP + line_px(T_SIZE, T_LH) * E.text_lines(scene["title"], T_SIZE, width, spacing=T_TRACK)
    text, _ = _sub(scene)
    if text:
        h += S_GAP + line_px(S_SIZE, S_LH) * E.text_lines(text, S_SIZE, width, "display500")
    return h


def min_width(scene):
    text, _ = _sub(scene)
    words = max(widest([(scene["title"], T_SIZE)]) + 2, widest([(text, S_SIZE)]) + 2 if text else 0)
    return max(words, _kicker_w(scene) + 2 * (RULE_GAP + RULE_MIN) + 4)


def render(scene, ctx, box):
    c, mo, sid = ctx.c, ctx.tokens["motion"], ctx.id
    t0 = ctx.t_in
    words = str(scene["title"]).split()
    row = ('<div class="tc-row"><i class="tc-rule l" id="%s-rl" style="background:%s"></i><span class="tc-k" id="%s-k" style="color:%s">%s</span>'
           '<i class="tc-rule r" id="%s-rr" style="background:%s"></i></div>'
           % (sid, c["line"], sid, c["accent"], ctx.esc(scene["kicker"]), sid, c["line"]))
    title = '<div class="tc-t" style="color:%s">%s</div>' % (ctx.ink, " ".join('<span class="w">%s</span>' % ctx.esc(w) for w in words))
    js = [ctx.enter("#%s-k" % sid, t0, {"y": 14}),
          "tl.fromTo('#%s-rl, #%s-rr', { scaleX: 0 }, %s, %.3f);" % (sid, sid, js_obj({"scaleX": 1, "duration": 0.8, "ease": "power3.out",
                                                                                     "immediateRender": False}), t0 + 0.12)]
    # each word rises out of its own mask: a clip that travels with it, so the word appears from its baseline up; the
    # clip reaches past the box (glyphs overhang a tight line box) and is off once the word has landed
    hide = {"yPercent": 100, "clipPath": "inset(-30% -12% 100% -12%)"}
    js.append("tl.set('#%s .tc-t .w', %s, 0);" % (sid, js_obj(hide)))
    stagger = round(min(0.08 * (len(words) - 1), mo["stagger_total_max"]), 3)
    show = {"yPercent": 0, "clipPath": "inset(-30% -12% -30% -12%)", "duration": 0.7, "ease": "expo.out", "immediateRender": False}
    if stagger:
        show["stagger"] = {"amount": stagger}
    js.append("tl.fromTo('#%s .tc-t .w', %s, %s, %.3f);" % (sid, js_obj(hide), js_obj(show), t0 + 0.18))
    html = row + title
    text, at = _sub(scene)
    if text:
        ts, attrs = ctx.item(at) if at is not None else (t0 + 0.55, "")
        html += '<div class="tc-s" id="%s-s"%s style="color:%s">%s</div>' % (sid, attrs, c["dim"], ctx.esc(text))
        js.append(ctx.enter("#%s-s" % sid, ts, {"y": 18}))
    return '<div class="tc">%s</div>' % html, js
