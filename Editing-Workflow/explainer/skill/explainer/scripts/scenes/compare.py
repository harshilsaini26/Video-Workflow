"""compare: two columns side by side, a VS between their titles; each side's rows arrive on their words, and a winner
can be called on a word (it glows and gets a check, the other side dims) (PLAYBOOK §E4). For "instead of X, Y"."""
import explainer_lib as E
from scenes import SLOT, js_obj, need

TYPE = "compare"
HEAD, H_GAP, ROW, R_GAP, COL_GAP = 104, 22, 84, 14, 26
T_SIZE, R_SIZE = 50, 38          # title and row: DM Sans 700, one line each
PAD, MARK, M_GAP = 26, 16, 14    # row padding, the row's dot and its gap
BADGE_ROOM = 64 + 12 + 8         # the winner's check sits inside its head, at the right: room kept on both sides of the title
SIDES = ("left", "right")

CSS = """
  .cp { position:relative; width:100%%; display:grid; grid-template-columns:1fr 1fr; gap:0 %dpx; }
  .cp-col { position:relative; display:flex; flex-direction:column; }
  .cp-head { height:%dpx; margin-bottom:%dpx; border-radius:26px; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
  .cp-row { height:%dpx; border-radius:20px; display:flex; align-items:center; gap:%dpx; padding:0 %dpx; font-weight:700;
    font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
  .cp-row + .cp-row { margin-top:%dpx; }
  .cp-dot { width:%dpx; height:%dpx; border-radius:50%%; flex:none; }
  .cp-vs { position:absolute; left:50%%; top:%dpx; width:76px; height:76px; margin:-38px 0 0 -38px; border-radius:50%%; z-index:2;
    display:flex; align-items:center; justify-content:center; font-family: var(--label); font-weight:500; font-size:28px; opacity:0; }
  .cp-win { position:absolute; right:12px; top:%dpx; width:64px; height:64px; border-radius:50%%; display:flex; align-items:center;
    justify-content:center; font-weight:700; font-size:38px; opacity:0; z-index:3; }
""" % (COL_GAP, HEAD, H_GAP, T_SIZE, ROW, M_GAP, PAD, R_SIZE, R_GAP, MARK, MARK, HEAD // 2, (HEAD - 64) // 2)


def validate(scene):
    errs = []
    for side in SIDES:
        col = scene.get(side) or {}
        if not col.get("title"):
            errs.append("%s needs a title" % side)
        items = col.get("items") or []
        if not 1 <= len(items) <= 4:
            errs.append("%s takes 1 to 4 items (got %d)" % (side, len(items)))
        errs += ["%s item %d has no text" % (side, i) for i, it in enumerate(items) if not it.get("text")]
        errs += ["%s item %d has no at" % (side, i) for i, it in enumerate(items) if it.get("at") is None]
    w = scene.get("winner")
    if w and (w.get("side") not in SIDES or w.get("at") is None):
        errs.append("winner needs a side (left or right) and an at")
    return errs


def rows(scene):
    return max(len(scene[s]["items"]) for s in SIDES)


def height(scene, width):
    r = rows(scene)
    return HEAD + H_GAP + r * ROW + (r - 1) * R_GAP


def min_width(scene):
    col = 0
    for s in SIDES:
        col = max(col, E.text_width(scene[s]["title"], T_SIZE) + 2 * PAD,
                  *[E.text_width(it["text"], R_SIZE) + 2 * PAD + MARK + M_GAP for it in scene[s]["items"]])
    w = scene.get("winner")
    if w and w.get("side") in SIDES:   # the check inside the winner's head keeps clear of its title
        col = max(col, E.text_width(scene[w["side"]]["title"], T_SIZE) + 2 * BADGE_ROOM)
    return 2 * (int(col) + 1) + COL_GAP


def render(scene, ctx, box):
    c, mo = ctx.c, ctx.tokens["motion"]
    sid, acc = ctx.id, c["accent"]
    face = ctx.card()
    head = "background:%s;color:%s" % (c["ink"], c["bg"])
    cols, js = [], []
    for k, s in enumerate(SIDES):
        rows_html = []
        for i, it in enumerate(scene[s]["items"]):
            t, attrs = ctx.item(it["at"])
            rows_html.append('<div class="cp-row" id="%s-%s%d"%s style="%s;color:%s"><i class="cp-dot gt" style="background:%s"></i><span class="gt">%s</span></div>'
                             % (sid, s[0], i, attrs, face, ctx.ink, acc if k else c["muted"], ctx.esc(it["text"])))
            off = {"x": -40 if k == 0 else 40}       # an empty slot for the row, off to its side, until its word slides it in
            js += ctx.slot("#%s-%s%d" % (sid, s[0], i), off)
            js.append(ctx.enter("#%s-%s%d" % (sid, s[0], i), t, dict(off, opacity=SLOT)))
            js.append(ctx.fill("#%s-%s%d" % (sid, s[0], i), t))
        cols.append('<div class="cp-col" id="%s-c%d"><div class="cp-head" id="%s-h%d" style="%s">%s</div>%s</div>'
                    % (sid, k, sid, k, head, ctx.esc(scene[s]["title"]), "".join(rows_html)))
    js.append(ctx.enter("#%s-h0, #%s-h1" % (sid, sid), ctx.t_in, {"y": -24}, stagger=0.12))
    js.append(ctx.enter("#%s-vs" % sid, ctx.t_in + 0.2, {"scale": 0.4}))
    vs = '<div class="cp-vs" id="%s-vs" style="background:%s;color:%s">VS</div>' % (sid, c["fill"], c["on_fill"])
    win = ""
    w = scene.get("winner")
    if w:
        t = ctx.at(w["at"])
        k = SIDES.index(w["side"])
        win = '<div class="cp-win" id="%s-w" style="background:%s;color:%s">&#10003;</div>' % (sid, c["fill"], c["on_fill"])
        js.append("tl.to('#%s-h%d', %s, %.3f);" % (sid, k, js_obj({"backgroundColor": c["fill"], "color": c["on_fill"],
                                                                   "duration": 0.3, "ease": mo["enter_ease"]}), t))
        js.append("tl.to('#%s-c%d', %s, %.3f);" % (sid, 1 - k, js_obj({"opacity": 0.45, "duration": 0.4, "ease": mo["enter_ease"]}), t))
        js.append(ctx.enter("#%s-w" % sid, t + 0.1, {"scale": 0.3}))
        ctx.idle("#%s-w" % sid, t + 0.6, ctx.t_out, {"scale": 1.14}, every=0.8)
        cols[k] = cols[k].replace('<div class="cp-head"', win + '<div class="cp-head"', 1)
    ctx.idle("#%s .cp" % sid, ctx.t_in + 0.6, ctx.t_out, {"y": -8})
    return '<div class="cp">%s%s</div>' % ("".join(cols), vs), js
