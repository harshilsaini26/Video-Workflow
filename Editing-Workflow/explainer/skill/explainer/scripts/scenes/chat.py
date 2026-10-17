"""chat: a chat window on light paper. The question bubble is sent on its word, the assistant types (three dots), then
its answer streams in on its word, with an optional cited source chip that lands on its own word. One to three
exchanges; when they outgrow the window it scrolls like a real chat, and what leaves the top fades away.

  {"type": "chat", "name": "HR Assistant", "source": "s1", "messages": [
     {"role": "user", "text": "How many leave days do I get?", "at": "word:2"},
     {"role": "assistant", "text": "24 days a year, plus public holidays.", "at": "word:6",
      "cite": {"text": "Leave policy.pdf", "at": "word:9"}}]}

The window's name, its placeholder and a cited file's name are furniture (DECOR_KEYS); a digit in a message is a claim
and needs the scene's source.
"""
import explainer_lib as E
from scenes import js_obj, need, widest

TYPE = "chat"
DECOR_KEYS = ("name", "placeholder", "cite")
MAX_SCALE = 1.25                  # a window, not a poster: 34 px text is drawn at 42 px at most
BAR, AV, AV_SIZE, N_SIZE = 84, 52, 30, 34         # the title bar: its avatar (a monogram or an icon) and the name
PAD_T, PAD_B, PAD_X, GAP = 28, 24, 28, 18         # the conversation's padding and the gap between messages
M_SIZE, M_LINE, BP_Y, BP_X = 34, 44, 18, 26       # a message: DM Sans 500, and its bubble's padding
U_MAX, A_MAX = 0.8, 0.88                          # how wide a bubble may grow, of the conversation's width
CITE_GAP, CITE_H, C_SIZE, C_ICON, C_PADL, C_PADR, C_IGAP = 12, 54, 30, 30, 16, 22, 10
DOTS_W, DOTS_H, DOT = 124, 80, 14                 # the typing bubble: as tall as a one-line message
IN_H, IN_PAD, P_SIZE, SEND = 64, 20, 30, 48       # the input field under the conversation
VIEW_MAX = 600 - BAR - IN_H - IN_PAD              # the conversation's most height before it scrolls
TYPING = 0.5                                      # the dots start this long after the question lands
MAX_MESSAGES = 6
# kerning and ligatures are off in the window, so Chromium wraps lines exactly where the glyph widths (text_lines) say

CSS = """
  .chat { width:100%%; border-radius:32px; overflow:hidden; opacity:0; font-kerning:none; font-variant-ligatures:none; }
  .chat-bar { height:%dpx; display:flex; align-items:center; gap:16px; padding:0 %dpx; }
  .chat-av { width:%dpx; height:%dpx; flex:none; border-radius:50%%; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; line-height:1; }
  .chat-av svg { width:30px; height:30px; }
  .chat-name { font-weight:700; font-size:%dpx; line-height:1; white-space:nowrap; letter-spacing:-.01em; }
  .chat-view { position:relative; overflow:hidden; }
  .chat-stack { display:flex; flex-direction:column; gap:%dpx; padding:%dpx %dpx %dpx; }
  .chat-row { position:relative; display:flex; flex-direction:column; }
  .chat-u { align-items:flex-end; }
  .chat-a { align-items:flex-start; }
  .chat-bub { padding:%dpx %dpx; font-weight:500; font-size:%dpx; line-height:%dpx; opacity:0; }
  .chat-u .chat-bub { max-width:%d%%; border-radius:30px 30px 10px 30px; transform-origin:100%% 100%%; }
  .chat-a .chat-bub { max-width:%d%%; border-radius:30px 30px 30px 10px; transform-origin:0 100%%; }
  .chat-w { opacity:0; }
  .chat-dots { position:absolute; left:0; top:0; width:%dpx; height:%dpx; border-radius:30px 30px 30px 10px; display:flex;
    align-items:center; justify-content:center; gap:12px; opacity:0; }
  .chat-dots b { width:%dpx; height:%dpx; border-radius:50%%; }
  .chat-cite { height:%dpx; margin-top:%dpx; display:flex; align-items:center; gap:%dpx; padding:0 %dpx 0 %dpx; border-radius:%dpx;
    font-weight:500; font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
  .chat-cite svg { width:%dpx; height:%dpx; flex:none; }
  .chat-in { padding:0 %dpx %dpx; }
  .chat-field { height:%dpx; border-radius:%dpx; display:flex; align-items:center; justify-content:space-between; padding:0 8px 0 28px;
    font-weight:500; font-size:%dpx; line-height:1; white-space:nowrap; }
  .chat-send { width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center; justify-content:center; flex:none; }
  .chat-send svg { width:26px; height:26px; }
""" % (BAR, PAD_X, AV, AV, AV_SIZE, N_SIZE, GAP, PAD_T, PAD_X, PAD_B, BP_Y, BP_X, M_SIZE, M_LINE, round(U_MAX * 100), round(A_MAX * 100),
       DOTS_W, DOTS_H, DOT, DOT, CITE_H, CITE_GAP, C_IGAP, C_PADR, C_PADL, CITE_H // 2, C_SIZE, C_ICON, C_ICON,
       PAD_X, IN_PAD, IN_H, IN_H // 2, P_SIZE, SEND, SEND)


def _word(ref):
    s = str(ref)
    return int(s[5:]) if s.startswith("word:") and s[5:].isdigit() else None


def validate(scene):
    errs = need(scene, ["messages"])
    msgs = scene.get("messages") or []
    if not isinstance(msgs, list):
        return errs + ["messages is a list"]
    if not 2 <= len(msgs) <= MAX_MESSAGES or len(msgs) % 2:
        errs.append("a chat holds 1 to 3 exchanges: 2, 4 or 6 messages, a question then its answer (got %d)" % len(msgs))
    for i, m in enumerate(msgs):
        if not isinstance(m, dict):
            errs.append("message %d is not an object" % i)
            continue
        want = "user" if i % 2 == 0 else "assistant"
        if m.get("role") != want:
            errs.append("message %d is the %s's (questions and answers take turns, the user first; got role %r)" % (i, want, m.get("role")))
        if not str(m.get("text", "")).strip():
            errs.append("message %d has no text" % i)
        if m.get("at") is None:
            errs.append("message %d has no at" % i)
        c = m.get("cite")
        if c is not None:
            if want != "assistant":
                errs.append("message %d: only an answer cites a source" % i)
            elif not isinstance(c, dict) or not str(c.get("text", "")).strip() or c.get("at") is None:
                errs.append("message %d: cite needs text (the source's name) and at" % i)
    words = [(_word(m.get("at")), i) for i, m in enumerate(msgs) if isinstance(m, dict)]
    for (a, i), (b, j) in zip(words, words[1:]):
        if a is not None and b is not None and b < a:
            errs.append("message %d (word:%d) comes before message %d (word:%d): an answer comes after its question" % (j, b, i, a))
    for i, m in enumerate(msgs):
        c = m.get("cite") if isinstance(m, dict) else None
        if isinstance(c, dict) and _word(c.get("at")) is not None and _word(m.get("at")) is not None and _word(c["at"]) < _word(m["at"]):
            errs.append("message %d: its cite (%s) lands before the answer (%s)" % (i, c["at"], m["at"]))
    return errs


def _bubble_h(m, width, i):
    frac = U_MAX if i % 2 == 0 else A_MAX
    text_w = frac * (width - 2 * PAD_X) - 2 * BP_X
    return 2 * BP_Y + M_LINE * E.text_lines(m["text"], M_SIZE, text_w, "display500")


def rows(scene, width):
    """[(top, bubble height, row height)] of each message in the conversation, and the conversation's full height."""
    out, y = [], PAD_T
    for i, m in enumerate(scene["messages"]):
        b = _bubble_h(m, width, i)
        h = b + (CITE_GAP + CITE_H if m.get("cite") else 0)
        out.append((y, b, h))
        y += h + GAP
    return out, y - GAP + PAD_B


def view(scene, width):
    """The conversation's height: all of it, or VIEW_MAX and a scroll (never less than its tallest message)."""
    rs, full = rows(scene, width)
    if full <= VIEW_MAX:
        return full, False
    return max(VIEW_MAX, max(PAD_T + h + PAD_B for _, _, h in rs)), True


def height(scene, width):
    return BAR + view(scene, width)[0] + IN_H + IN_PAD


def _cite_w(c):
    return C_PADL + C_ICON + C_IGAP + int(E.text_width(c["text"], C_SIZE, "display500")) + 1 + C_PADR


def min_width(scene):
    need_w = 2 * PAD_X + AV + 16 + int(E.text_width(scene.get("name", "Assistant"), N_SIZE, spacing=-0.01)) + 1
    for i, m in enumerate(scene["messages"]):
        frac = U_MAX if i % 2 == 0 else A_MAX
        need_w = max(need_w, int((widest([(m["text"], M_SIZE)]) + 2 * BP_X) / frac) + 1 + 2 * PAD_X)
        if m.get("cite"):
            need_w = max(need_w, _cite_w(m["cite"]) + 2 * PAD_X)
    field = 28 + int(E.text_width(scene.get("placeholder", "Ask anything"), P_SIZE, "display500")) + 24 + SEND + 8
    return max(need_w, field + 2 * PAD_X)


def render(scene, ctx, box):
    p, mo = ctx.pc, ctx.tokens["motion"]        # the window is light paper on any ground
    sid, width = ctx.id, box[2]
    msgs = scene["messages"]
    name = scene.get("name", "Assistant")
    av = ctx.icon(scene["icon"]) if scene.get("icon") else ctx.esc(name.strip()[:1].upper())
    head = ('<div class="chat-bar" style="background:%s"><div class="chat-av" style="background:%s;color:%s">%s</div>'
            '<div class="chat-name" style="color:%s">%s</div></div>' % (p["chrome"], p["accent"], p["on_accent"], av, p["ink"], ctx.esc(name)))
    rs, _ = rows(scene, width)
    view_h, scrolls = view(scene, width)
    times, parts, js, events = [], [], [], []
    js.append(ctx.enter("#%s-win" % sid, ctx.t_in, {"y": 40}))
    for i, m in enumerate(msgs):
        t, attrs = ctx.item(m["at"])
        if times and t < times[-1] - 1e-6:
            ctx.fail("message %d (%s) comes before message %d: an answer comes after its question" % (i, m["at"], i - 1))
        times.append(t)
        top, bub_h, row_h = rs[i]
        if i % 2 == 0:     # the question: sent whole, from the user's corner
            parts.append('<div class="chat-row chat-u" id="%s-r%d"><div class="chat-bub" id="%s-b%d"%s style="background:%s;color:%s">%s</div></div>'
                         % (sid, i, sid, i, attrs, p["accent"], p["on_accent"], ctx.esc(m["text"])))
            js.append(ctx.enter("#%s-b%d" % (sid, i), t, {"y": 24, "scale": 0.94}))
            events.append((t, top + bub_h))
            continue
        # the answer: the assistant types while the voice gets there, then its words stream in
        words = " ".join('<span class="chat-w">%s</span>' % ctx.esc(w) for w in m["text"].split())
        dots = ""
        t_dots = times[-2] + TYPING
        if t - t_dots >= 0.5:
            dots = '<i class="chat-dots" id="%s-d%d" style="background:%s">%s</i>' % (sid, i, p["chrome"], "".join(
                '<b style="background:%s"></b>' % p["muted"] for _ in range(3)))
            js.append(ctx.enter("#%s-d%d" % (sid, i), t_dots, {"y": 16}, dur=0.3))
            for k in range(3):   # the dots rise in a wave while it types (finite steps, ambient)
                ctx.idle("#%s-d%d b:nth-child(%d)" % (sid, i, k + 1), t_dots + 0.2 + 0.14 * k, t - 0.1, {"y": -9}, every=0.28)
            js.append("tl.to('#%s-d%d', %s, %.3f);" % (sid, i, js_obj({"opacity": 0, "duration": 0.15, "ease": mo["exit_ease"]}), max(t_dots + 0.3, t - 0.1)))
            events.append((t_dots, top + DOTS_H))
        cite = ""
        c = m.get("cite")
        if c:
            tc, cattrs = ctx.item(c["at"])
            if tc < t - 1e-6:
                ctx.fail("message %d: its cite (%s) lands before the answer (%s)" % (i, c["at"], m["at"]))
            cite = '<div class="chat-cite" id="%s-c%d"%s style="background:%s;color:%s"><span style="color:%s;display:flex">%s</span><span>%s</span></div>' % (
                sid, i, cattrs, p["accent_soft"], p["ink"], p["accent"], ctx.icon("file-text"), ctx.esc(c["text"]))
            js.append(ctx.enter("#%s-c%d" % (sid, i), tc, {"y": 14}))
            events.append((tc, top + row_h))
        parts.append('<div class="chat-row chat-a" id="%s-r%d">%s<div class="chat-bub" id="%s-b%d"%s style="background:%s;color:%s">%s</div>%s</div>'
                     % (sid, i, dots, sid, i, attrs, p["chrome"], p["ink"], words, cite))
        js.append(ctx.enter("#%s-b%d" % (sid, i), t, {"y": 24, "scale": 0.94}))
        n = len(m["text"].split())
        js.append(ctx.enter("#%s-b%d .chat-w" % (sid, i), t + 0.12, dur=0.3, stagger=0.045 * (n - 1) if n > 1 else None))
        events.append((t, top + bub_h))
    if scrolls:            # like a real chat: the newest message comes up from the bottom, what leaves the top fades
        y, gone = 0.0, set()
        for t, bottom in sorted(events):
            want = bottom + PAD_B - view_h
            if want <= y + 0.5:
                continue
            y = want
            js.append("tl.to('#%s-stack', %s, %.3f);" % (sid, js_obj({"y": -round(y, 1), "duration": 0.5, "ease": mo["enter_ease"]}), t))
            for j, (top, _, _) in enumerate(rs):
                if j not in gone and top < y + 2:
                    gone.add(j)
                    js.append("tl.to('#%s-r%d', %s, %.3f);" % (sid, j, js_obj({"opacity": 0, "duration": 0.3, "ease": mo["exit_ease"]}), t))
    field = ('<div class="chat-in"><div class="chat-field" style="background:%s;color:%s"><span>%s</span>'
             '<i class="chat-send" style="background:%s;color:%s">%s</i></div></div>'
             % (p["chrome"], p["dim"], ctx.esc(scene.get("placeholder", "Ask anything")), p["accent"], p["on_accent"], ctx.icon("send")))
    html = ('<div class="chat" id="%s-win" style="%s">%s<div class="chat-view"%s><div class="chat-stack" id="%s-stack">%s</div></div>%s</div>'
            % (sid, ctx.paper_card(), head, ' style="height:%dpx"' % view_h if scrolls else "", sid, "".join(parts), field))
    return html, js
