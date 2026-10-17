"""prompt-bar: an AI prompt box on light paper. It waits with its placeholder and a blinking caret; on its word the
prompt types in character by character (the caret steps along after the last letter), the send button lights up as soon
as there is text and presses on its word, and an optional reply streams in, word by word, under the box:

  {"type": "prompt-bar", "placeholder": "Ask anything",
   "prompt": {"text": "Write a hook for my reel about index funds", "at": "word:2"},
   "send": {"at": "word:9"}, "reply": {"text": "Three hooks that stop the scroll", "at": "word:11"}}

The text is wrapped here, at the width the scene is given, and drawn line by line (BAKED), so the box never reflows as
the letters arrive. The caret is a bar after the last typed letter (its ::after): it sits exactly where the browser drew it.
"""
import explainer_lib as E
from scenes import SLOT, js_obj, line_px, need, stagger_for, widest

TYPE = "prompt-bar"
BAKED = True                         # lines are wrapped for the width it is given: measured at that width
MAX_SCALE = 1.4                      # a prompt box reads as UI, not as a poster
PAD, RADIUS = 36, 40                 # the box
P_SIZE, P_LH = 44, 60                # the prompt (and the placeholder), DM Sans 500
ROW_GAP, BTN = 28, 76                # the button row: attach on the left, send on the right
CARET_W, CARET_H = 4, 50
CARET_TOP = (int(P_SIZE * 1.302) - CARET_H) // 2   # inside a letter's content area (DM Sans: 1.302 em)
R_GAP, R_PAD, R_RADIUS = 24, 30, 32  # the reply card under the box
R_SIZE, R_LH = 38, 52                # reply text, DM Sans 500
MARK, MARK_GAP = 52, 22              # the reply's mark (the assistant)
SLACK = 10                           # wrap a little short of the edge: the browser's widths and ours differ by a pixel or two
MAX_PROMPT, MAX_REPLY, MAX_PH = 120, 100, 32
BLINK = 0.5
MIN_W = 480                          # narrower than this it stops reading as a prompt box

CSS = """
  .pb { width:100%%; }
  .pb-box { width:100%%; border-radius:%dpx; padding:%dpx; opacity:0; }
  .pb-field { position:relative; }
  .pb-line { height:%dpx; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .pb-ch { position:relative; opacity:0; }
  .pb-ch::after { content:""; position:absolute; left:100%%; top:%dpx; width:%dpx; height:%dpx; margin-left:1px; border-radius:2px;
    background:var(--caret); opacity:var(--on, 0); }
  .pb-ph { position:absolute; left:0; top:0; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .pb-caret { position:absolute; left:0; width:%dpx; height:%dpx; border-radius:2px; opacity:0; }
  .pb-row { height:%dpx; margin-top:%dpx; display:flex; align-items:center; justify-content:space-between; }
  .pb-btn { position:relative; width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center; justify-content:center; flex:none; }
  .pb-btn svg { width:44%%; height:44%%; }
  .pb-ring { position:absolute; inset:0; border-radius:50%%; border:4px solid; opacity:0; }
  .pb-reply { margin-top:%dpx; border-radius:%dpx; padding:%dpx; display:flex; gap:%dpx; align-items:flex-start; opacity:0; }
  .pb-mark { width:%dpx; height:%dpx; border-radius:50%%; flex:none; display:flex; align-items:center; justify-content:center; }
  .pb-mark svg { width:58%%; height:58%%; }
  .pb-rline { height:%dpx; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
""" % (RADIUS, PAD, P_LH, P_SIZE, P_LH, CARET_TOP, CARET_W, CARET_H, P_SIZE, P_LH, CARET_W, CARET_H, BTN, ROW_GAP, BTN, BTN,
       R_GAP, R_RADIUS, R_PAD, MARK_GAP, MARK, MARK, R_LH, R_SIZE, R_LH)

ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M12 19V5"/><path d="M5.5 11.5L12 5l6.5 6.5"/></svg>')
PLUS = ('<svg viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="2.4" stroke-linecap="round">'
        '<path d="M12 5v14"/><path d="M5 12h14"/></svg>')
SPARK = '<svg viewBox="0 0 24 24"><path d="M12 2.5l2.2 7.3 7.3 2.2-7.3 2.2L12 21.5l-2.2-7.3L2.5 12l7.3-2.2z" fill="%s"/></svg>'


def wrap(text, size, width):
    """The lines the text takes at `width`, word by word (DM Sans 500), a little short of the edge (SLACK)."""
    gap = E.text_width(" ", size, "display500")
    lines, cur, w = [], [], 0.0
    for word in str(text).split():
        ww = E.text_width(word, size, "display500")
        if cur and w + gap + ww > width - SLACK:
            lines.append(" ".join(cur))
            cur, w = [word], ww
        else:
            w = w + gap + ww if cur else ww
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def _text_w(width):
    return width - 2 * PAD


def _reply_w(width):
    return width - 2 * R_PAD - MARK - MARK_GAP


def validate(scene):
    errs = need(scene, ["prompt"])
    p = scene.get("prompt")
    if p is not None:
        if not isinstance(p, dict) or not str(p.get("text") or "").strip() or p.get("at") is None:
            errs.append("prompt needs text (what is typed) and at (the word it starts typing on)")
        elif len(p["text"]) > MAX_PROMPT:
            errs.append("the prompt is %d characters; at most %d (it types in under two seconds)" % (len(p["text"]), MAX_PROMPT))
    ph = scene.get("placeholder")
    if ph is not None and (not isinstance(ph, str) or len(ph) > MAX_PH):
        errs.append("placeholder is one short line (at most %d characters)" % MAX_PH)
    s = scene.get("send")
    if s is not None and (not isinstance(s, dict) or s.get("at") is None):
        errs.append("send needs at (the word the button is pressed on)")
    r = scene.get("reply")
    if r is not None:
        if not isinstance(r, dict) or not str(r.get("text") or "").strip() or r.get("at") is None:
            errs.append("reply needs text and at")
        elif len(r["text"]) > MAX_REPLY:
            errs.append("the reply is %d characters; at most %d" % (len(r["text"]), MAX_REPLY))
    return errs


def height(scene, width):
    h = 2 * PAD + P_LH * len(wrap(scene["prompt"]["text"], P_SIZE, _text_w(width))) + ROW_GAP + BTN
    if scene.get("reply"):
        h += R_GAP + 2 * R_PAD + max(MARK, R_LH * len(wrap(scene["reply"]["text"], R_SIZE, _reply_w(width))))
    return h


def min_width(scene):
    ph = E.text_width(scene.get("placeholder") or "Ask anything", P_SIZE, "display500")
    need_w = max(widest([(scene["prompt"]["text"], P_SIZE)]) + SLACK, ph + 4) + 2 * PAD
    if scene.get("reply"):
        need_w = max(need_w, widest([(scene["reply"]["text"], R_SIZE)]) + SLACK + 2 * R_PAD + MARK + MARK_GAP)
    return int(max(need_w, MIN_W)) + 1


def render(scene, ctx, box):
    c, mo = ctx.pc, ctx.tokens["motion"]
    sid, width = ctx.id, box[2]
    js = []

    # ---- the prompt, wrapped here and drawn line by line; every letter its own span --------------------------------
    t_type, p_attrs = ctx.item(scene["prompt"]["at"])
    lines = wrap(scene["prompt"]["text"], P_SIZE, _text_w(width))
    rows, chars = [], []          # chars: the id of each letter in typing order, None for the space between words
    k = 0
    for i, line in enumerate(lines):
        if i:
            chars.append(None)    # the space the wrap ate still takes a keystroke
        words = []
        for j, word in enumerate(line.split(" ")):
            if j:
                chars.append(None)
            spans = []
            for ch in word:
                spans.append('<span class="pb-ch" id="%s-c%d">%s</span>' % (sid, k, ctx.esc(ch)))
                chars.append("#%s-c%d" % (sid, k))
                k += 1
            words.append("".join(spans))
        rows.append('<div class="pb-line" style="color:%s">%s</div>' % (c["ink"], " ".join(words)))
    ph = ctx.esc(scene.get("placeholder") or "Ask anything")
    field = ('<div class="pb-field" id="%s-field"%s style="height:%dpx;--caret:%s"><div class="pb-ph" id="%s-ph" style="color:%s">%s</div>'
             '<i class="pb-caret" id="%s-caret" style="top:%dpx;background:%s"></i>%s</div>'
             % (sid, p_attrs, P_LH * len(lines), c["accent"], sid, c["muted"], ph, sid, (P_LH - CARET_H) // 2, c["accent"], "".join(rows)))

    # the typing: quick and even, done before the send (or the reply, or the scene's end) is due
    t_send = t_reply = None
    if scene.get("send"):
        t_send, s_attrs = ctx.item(scene["send"]["at"])
    if scene.get("reply"):
        t_reply, r_attrs = ctx.item(scene["reply"]["at"])
    nxt = min(x for x in (t_send, t_reply, ctx.t_out - 0.3) if x is not None)
    room = nxt - 0.25 - t_type
    if room < 0.4:
        ctx.fail("the prompt starts typing at %.2f s but has to be done by %.2f s; give it more words before the send or the reply"
                 % (t_type, nxt - 0.25))
    n = len(chars)
    dt = min(0.05, max(0.022, 2.0 / n), room / n)
    t_done = t_type + n * dt

    # before the word: the caret blinks at the start of the empty field
    t, on = ctx.t_in + 0.35, True
    while t < t_type - 0.05:
        ctx.ambient("tl.set('#%s-caret', { opacity: %d }, %.3f);" % (sid, 1 if on else 0, t))
        t, on = t + BLINK, not on
    js.append("tl.set('#%s-caret', { opacity: 0 }, %.3f);" % (sid, t_type))
    js.append("tl.to('#%s-ph', %s, %.3f);" % (sid, js_obj({"opacity": 0, "duration": 0.12, "ease": mo["exit_ease"]}), t_type))
    js.append("tl.to('#%s-send', %s, %.3f);" % (sid, js_obj({"backgroundColor": c["accent"], "duration": 0.25, "ease": mo["enter_ease"]}), t_type))
    prev = None
    for i, ch in enumerate(chars):
        if ch is None:
            continue
        ts = t_type + i * dt
        js.append("tl.set('%s', { opacity: 1, '--on': 1 }, %.3f);" % (ch, ts))
        if prev:
            js.append("tl.set('%s', { '--on': 0 }, %.3f);" % (prev, ts))
        prev = ch
    # after the last letter the caret blinks where it stopped, until the send (or the end)
    stop = (t_send if t_send is not None else ctx.t_out - 0.3)
    t, on = t_done + BLINK, False
    while t < stop - 0.05:
        ctx.ambient("tl.set('%s', { '--on': %d }, %.3f);" % (prev, 1 if on else 0, t))
        t, on = t + BLINK, not on

    # ---- the button row --------------------------------------------------------------------------------------------
    send_attrs = s_attrs if t_send is not None else ""
    row = ('<div class="pb-row"><div class="pb-btn" style="box-shadow:inset 0 0 0 3px %s">%s</div>'
           '<div class="pb-btn" id="%s-send"%s style="background:%s">%s<i class="pb-ring" id="%s-ring" style="border-color:%s"></i></div></div>'
           % (c["line"], PLUS % c["dim"], sid, send_attrs, c["line"], ARROW % c["on_accent"], sid, c["accent"]))
    if t_send is not None:
        if t_send < t_done + 0.1:
            ctx.fail("send at %.2f s comes before the prompt has typed in (%.2f s)" % (t_send, t_done))
        js.append("tl.set('%s', { '--on': 0 }, %.3f);" % (prev, t_send))
        js.append("tl.fromTo('#%s-send', { scale: 1 }, %s, %.3f);" % (sid, js_obj({"scale": 0.84, "duration": 0.1, "ease": "power2.out",
                                                                                   "immediateRender": False}), t_send))
        js.append("tl.to('#%s-send', %s, %.3f);" % (sid, js_obj({"scale": 1, "duration": 0.4, "ease": mo["enter_ease"]}), t_send + 0.1))
        js.append("tl.fromTo('#%s-ring', { scale: 1, opacity: 0.6 }, %s, %.3f);"
                  % (sid, js_obj({"scale": 1.45, "opacity": 0, "duration": 0.5, "ease": mo["enter_ease"], "immediateRender": False}), t_send + 0.05))

    box_html = ('<div class="pb-box" id="%s-box" style="%s">%s%s</div>' % (sid, ctx.paper_card(), field, row))
    js.insert(0, ctx.enter("#%s-box" % sid, ctx.t_in, {"y": 40}))

    # ---- the reply: an empty card that fills, its words streaming in -----------------------------------------------
    reply = ""
    if t_reply is not None:
        if t_reply < t_done + 0.1:
            ctx.fail("the reply at %.2f s comes before the prompt has typed in (%.2f s)" % (t_reply, t_done))
        rl = wrap(scene["reply"]["text"], R_SIZE, _reply_w(width))
        nw = 0
        out = []
        for line in rl:
            ws = []
            for w in line.split(" "):
                ws.append('<span class="pb-rw gt">%s</span>' % ctx.esc(w))
                nw += 1
            out.append('<div class="pb-rline" style="color:%s">%s</div>' % (c["ink"], " ".join(ws)))
        reply = ('<div class="pb-reply" id="%s-reply"%s style="%s;border-radius:%dpx"><div class="pb-mark gt" style="background:%s">%s</div>'
                 '<div class="pb-rt">%s</div></div>' % (sid, r_attrs, ctx.paper_card(), R_RADIUS, c["accent_soft"], SPARK % c["accent"], "".join(out)))
        js += ctx.slot("#%s-reply" % sid)
        js.append(ctx.enter("#%s-reply" % sid, t_reply, {"opacity": SLOT, "y": 24}))
        js.append(ctx.enter("#%s-reply .pb-mark" % sid, t_reply + 0.05, {"scale": 0.6}))
        js.append(ctx.enter("#%s-reply .pb-rw" % sid, t_reply + 0.12, {"y": 10}, stagger=stagger_for(nw, 0.07), dur=0.3))
    return '<div class="pb">%s%s</div>' % (box_html, reply), js
