"""comment-drop: comments drop in one by one and stack like a feed, the newest on top pushing the others down, each on
its word. Each is a light paper card (on any ground): an avatar circle with the name's initial, the @name, the text, and a
heart with a count. For what people say: "and the comments were all the same: this saved me hours".

  {"type": "comment-drop", "comments": [{"name": "sarah.k", "text": "This saved me hours", "likes": 1204, "at": "word:2"},
                                        {"name": "dev_mike", "text": "Why did nobody tell me this", "likes": 87, "time": "2h", "at": ...}]}

The name, the like count and the time are mock-up furniture (DECOR_KEYS); a digit in a comment's text needs a source.
"""
import math, re
import explainer_lib as E
from scenes import js_obj, line_px, need, widest

TYPE = "comment-drop"
DECOR_KEYS = {"name", "likes", "time"}
MAX_SCALE = 1.4                         # a feed reads as a phone's feed: grown, never so far that a short comment wraps word by word
PAD_X, PAD_Y, GAP = 28, 24, 18          # a card's padding, the gap between two cards
AV, AV_SIZE, AV_GAP = 76, 34, 22        # the avatar and its initial (DM Sans 700)
N_SIZE, N_LH, N_GAP = 30, 38, 4         # @name (700) and the time (500)
T_SIZE, T_LH = 38, 48                   # the comment (500)
H_W, H_ICON, H_GAP = 66, 40, 22         # the heart column, the heart, the gap to the text
C_SIZE, C_LH = 30, 36                   # the like count (500)
DROP = 70                               # a new card drops this far into place
MAX_COMMENTS = 4

CSS = """
  .cd { width:100%%; display:flex; flex-direction:column-reverse; gap:%dpx; }
  .cd-c { width:100%%; flex:none; border-radius:30px; display:flex; align-items:flex-start; padding:%dpx %dpx; opacity:0; }
  .cd-av { width:%dpx; height:%dpx; flex:none; border-radius:50%%; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; line-height:1; margin-right:%dpx; }
  .cd-body { flex:1 1 0; min-width:0; }
  .cd-n { height:%dpx; display:flex; align-items:center; white-space:nowrap; font-weight:700; font-size:%dpx; line-height:%dpx; }
  .cd-tm { font-weight:500; margin-left:14px; }
  .cd-t { margin-top:%dpx; font-weight:500; font-size:%dpx; line-height:%dpx; }
  .cd-h { width:%dpx; flex:none; margin-left:%dpx; display:flex; flex-direction:column; align-items:center; }
  .cd-h svg { width:%dpx; height:%dpx; display:block; }
  .cd-ct { font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
""" % (GAP, PAD_Y, PAD_X, AV, AV, AV_SIZE, AV_GAP, N_LH, N_SIZE, N_LH, N_GAP, T_SIZE, T_LH,
       H_W, H_GAP, H_ICON, H_ICON, C_SIZE, C_LH)

# Lucide's heart (ISC), drawn here so the scene needs no icon file
HEART = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 '
         '2.3 1.5 4.05 3 5.5l7 7Z"/></svg>')


def validate(scene):
    errs = need(scene, ["comments"])
    cs = scene.get("comments") or []
    if not isinstance(cs, list):
        return errs + ["comments is a list of {name, text, at}"]
    if not 2 <= len(cs) <= MAX_COMMENTS:
        errs.append("a comment-drop takes 2 to %d comments (got %d)" % (MAX_COMMENTS, len(cs)))
    for i, cm in enumerate(cs):
        if not isinstance(cm, dict):
            errs.append("comment %d is {name, text, at}" % i)
            continue
        if not str(cm.get("name") or "").strip("@ ") or not re.search(r"\w", str(cm.get("name"))):
            errs.append("comment %d has no name" % i)
        if not str(cm.get("text") or "").strip():
            errs.append("comment %d has no text" % i)
        elif len(str(cm["text"]).split()) > 14:
            errs.append("comment %d: at most 14 words (got %d); a comment on screen is a line or two" % (i, len(str(cm["text"]).split())))
        if cm.get("at") is None:
            errs.append("comment %d has no at" % i)
        lk = cm.get("likes")
        if lk is not None and not (isinstance(lk, (int, str)) and not isinstance(lk, bool)):
            errs.append("comment %d: likes is a whole number or a short label like \"1.2k\"" % i)
    return errs


def handle(cm):
    return "@" + str(cm["name"]).strip().lstrip("@")


def initial(cm):
    m = re.search(r"[A-Za-z0-9]", str(cm["name"]))
    return (m.group(0) if m else str(cm["name"]).strip().lstrip("@")[:1]).upper()


def likes(cm):
    v = cm.get("likes", 0)
    if isinstance(v, str):
        return v
    for div, unit in ((1000000, "M"), (1000, "k")):
        if v >= div:
            return ("%.1f" % (v / float(div))).rstrip("0").rstrip(".") + unit
    return str(v)


def _text_w(width):
    return width - 2 * PAD_X - AV - AV_GAP - H_GAP - H_W


def card_h(cm, width):
    lines = E.text_lines(cm["text"], T_SIZE, _text_w(width), "display500")
    return 2 * PAD_Y + max(AV, N_LH + N_GAP + lines * T_LH, H_ICON + C_LH)


def height(scene, width):
    cs = scene["comments"]
    return sum(card_h(cm, width) for cm in cs) + GAP * (len(cs) - 1)


def min_width(scene):
    head = max(E.text_width(handle(cm), N_SIZE) + (14 + E.text_width(str(cm["time"]), N_SIZE, "display500") if cm.get("time") else 0)
               for cm in scene["comments"])
    words = widest([(cm["text"], T_SIZE) for cm in scene["comments"]])     # 700 widths: a little over the 500 face
    return int(math.ceil(max(head, words))) + 2 * PAD_X + AV + AV_GAP + H_GAP + H_W + 4


def render(scene, ctx, box):
    p, mo, sid = ctx.pc, ctx.tokens["motion"], ctx.id
    cs = scene["comments"]
    hs = [card_h(cm, box[2]) for cm in cs]
    times, parts, js = [], [], []
    for i, cm in enumerate(cs):
        t, attrs = ctx.item(cm["at"])
        if times and t < times[-1] - 1e-6:
            ctx.fail("comment %d lands before comment %d: a feed grows in order (anchor the comments in time order)" % (i, i - 1))
        times.append(t)
        fill, on = p["series"][i % len(p["series"])]
        tm = '<span class="cd-tm" style="color:%s">%s</span>' % (p["dim"], ctx.esc(cm["time"])) if cm.get("time") else ""
        parts.append('<div class="cd-c" id="%s-c%d"%s style="%s"><div class="cd-av" style="background:%s;color:%s">%s</div>'
                     '<div class="cd-body"><div class="cd-n" style="color:%s">%s%s</div><div class="cd-t" style="color:%s">%s</div></div>'
                     '<div class="cd-h" style="color:%s">%s<span class="cd-ct">%s</span></div></div>'
                     % (sid, i, attrs, ctx.paper_card(), fill, on, ctx.esc(initial(cm)), p["ink"], ctx.esc(handle(cm)), tm,
                        p["ink"], ctx.esc(cm["text"]), p["dim"], HEART, ctx.esc(likes(cm))))
    # the feed reads newest first: the cards lie in their final places (column-reverse), and until a later comment
    # arrives each one is lifted by the cards still to come, so the newest always drops in at the top
    above = lambda j: sum(hs[m] + GAP for m in range(j + 1, len(cs)))
    for i, t in enumerate(times):
        sel = "#%s-c%d" % (sid, i)
        js.append("tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj({"opacity": 0, "y": -above(i) - DROP}),
                                                      js_obj({"opacity": 1, "y": -above(i), "duration": 0.55, "ease": mo["enter_ease"],
                                                              "immediateRender": False}), t))
        for j in range(i + 1, len(cs)):     # each later comment pushes this one down by its own height
            js.append("tl.to('%s', %s, %.3f);" % (sel, js_obj({"y": -above(j), "duration": 0.55, "ease": mo["enter_ease"]}), times[j]))
    return '<div class="cd">%s</div>' % "".join(parts), js
