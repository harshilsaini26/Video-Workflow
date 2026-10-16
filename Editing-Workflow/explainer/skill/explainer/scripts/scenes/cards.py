"""cards: one to four numbered cards are dealt into a fan, each on its word, with the newest card's title under the fan;
a focus can lift one card on a word (the others dim); each card floats while it holds (PLAYBOOK §E4). For "three
certificates", "two courses": things to count and name."""
import explainer_lib as E
from scenes import GHOST, js_obj, need

TYPE = "cards"
CW, CH = 250, 320                # a card
FAN = 50                         # room for the fan's tilt and lift
OFF, OFF_MIN = 170, 110          # card to card, at most and at least
GAP = 36                         # fan to title
T_SIZE, T_LINE = 50, 60          # title: DM Sans 700, one line
S_SIZE, S_LINE = 32, 42          # sub: DM Sans 500, one line

CSS = """
  .cd { position:relative; width:100%%; }
  .cd-card { position:absolute; width:%dpx; height:%dpx; opacity:0; }
  .cd-face { position:absolute; inset:0; border-radius:24px; padding:26px; overflow:hidden; }
  .cd-tag { font-family: var(--label); font-weight:500; font-size:20px; letter-spacing:.14em; opacity:.7; }
  .cd-n { font-weight:700; font-style:italic; font-size:150px; line-height:1; margin-top:10px; letter-spacing:-.04em; }
  .cd-bar { height:12px; border-radius:6px; margin-top:16px; opacity:.28; }
  .cd-star { position:absolute; right:22px; top:20px; width:46px; height:46px; border-radius:50%%; border:4px solid; }
  .cd-t, .cd-s { position:absolute; left:0; right:0; text-align:center; white-space:nowrap; opacity:0; }
  .cd-t { font-weight:700; font-size:%dpx; line-height:%dpx; }
  .cd-s { font-weight:500; font-size:%dpx; line-height:%dpx; }
""" % (CW, CH, T_SIZE, T_LINE, S_SIZE, S_LINE)


def validate(scene):
    errs = need(scene, ["cards"])
    cards = scene.get("cards") or []
    if not 1 <= len(cards) <= 4:
        errs.append("cards take 1 to 4 cards (got %d)" % len(cards))
    errs += ["card %d has no title" % i for i, c in enumerate(cards) if not c.get("title")]
    errs += ["card %d has no at" % i for i, c in enumerate(cards) if c.get("at") is None]
    f = scene.get("focus")
    if f and (not isinstance(f.get("card"), int) or not 0 <= f["card"] < len(cards) or f.get("at") is None):
        errs.append("focus needs a card (0 to %d) and an at" % (len(cards) - 1))
    return errs


def height(scene, width):
    return CH + FAN + GAP + T_LINE + S_LINE


def min_width(scene):
    n = len(scene["cards"])
    text = max(max(E.text_width(c["title"], T_SIZE), E.text_width(c.get("sub", ""), S_SIZE, "display500")) for c in scene["cards"])
    return max(CW + 40 + (n - 1) * OFF_MIN, int(text) + 1)


def render(scene, ctx, box):
    mo = ctx.tokens["motion"]
    sid, cards, W = ctx.id, scene["cards"], box[2]
    dim = ctx.c["dim"]
    n = len(cards)
    off = min(OFF, (W - CW - 40) / max(1, n - 1)) if n > 1 else 0
    mid = (n - 1) / 2.0
    parts, titles, js, times = [], [], [], []
    for i, cd in enumerate(cards):
        t, attrs = ctx.item(cd["at"])
        times.append(t)
        fill, ink = ctx.c["series"][i % len(ctx.c["series"])]
        left = W / 2.0 - CW / 2.0 + (i - mid) * off
        top = FAN / 2.0 + abs(i - mid) * 16
        bars = "".join('<div class="cd-bar" style="width:%d%%;background:%s"></div>' % (w, ink) for w in (86, 70, 54))
        parts.append('<div class="cd-card" id="%s-c%d"%s style="left:%.0fpx;top:%.0fpx;z-index:%d"><div class="cd-face" id="%s-f%d" '
                     'style="background:%s;color:%s;box-shadow:%s"><div class="cd-tag">No. %d</div><div class="cd-n">%d</div>%s'
                     '<i class="cd-star" style="border-color:%s"></i></div></div>'
                     % (sid, i, attrs, left, top, i + 1, sid, i, fill, ink, ctx.c["shadow"], i + 1, i + 1, bars, ink))
        js.append(ctx.ghost("#%s-c%d" % (sid, i), {"rotation": round((i - mid) * 8, 2)}))   # its place in the fan, dimmed
        js.append("tl.fromTo('#%s-c%d', %s, %s, %.3f);" % (
            sid, i, js_obj({"opacity": GHOST, "x": 320, "y": 420, "rotation": 40}),
            js_obj({"opacity": 1, "x": 0, "y": 0, "rotation": round((i - mid) * 8, 2), "duration": 0.6, "ease": mo["enter_ease"],
                    "immediateRender": False}), t))
        ty = CH + FAN + GAP
        titles.append('<div class="cd-t" id="%s-t%d" style="top:%dpx;color:%s">%s</div>' % (sid, i, ty, ctx.ink, ctx.esc(cd["title"])))
        if cd.get("sub"):
            titles.append('<div class="cd-s" id="%s-u%d" style="top:%dpx;color:%s">%s</div>' % (sid, i, ty + T_LINE, dim, ctx.esc(cd["sub"])))

    def show(i, t, prev):
        sel = "#%s-t%d" % (sid, i) + (", #%s-u%d" % (sid, i) if cards[i].get("sub") else "")
        out = [ctx.enter(sel, t + 0.1, {"y": 20})]
        if prev is not None:
            psel = "#%s-t%d" % (sid, prev) + (", #%s-u%d" % (sid, prev) if cards[prev].get("sub") else "")
            out.append("tl.to('%s', %s, %.3f);" % (psel, js_obj({"opacity": 0, "y": -16, "duration": 0.2, "ease": mo["exit_ease"]}), t))
        return out
    for i, t in enumerate(times):
        js += show(i, t, i - 1 if i else None)
    shown = n - 1
    f = scene.get("focus")
    if f:
        t = ctx.at(f["at"])
        k = f["card"]
        js.append("tl.to('#%s-c%d', %s, %.3f);" % (sid, k, js_obj({"scale": 1.12, "y": -30, "duration": mo["enter"], "ease": mo["enter_ease"]}), t))
        others = ", ".join("#%s-c%d" % (sid, i) for i in range(n) if i != k)
        if others:
            js.append("tl.to('%s', %s, %.3f);" % (others, js_obj({"opacity": 0.45, "duration": 0.4, "ease": mo["enter_ease"]}), t))
        if k != shown:
            js += show(k, t, shown)
    for i, t in enumerate(times):   # each card floats on its own beat while it holds
        ctx.idle("#%s-f%d" % (sid, i), t + 0.6, ctx.t_out, {"y": -10}, every=1.4 + 0.2 * i)
    return '<div class="cd" style="height:%dpx">%s%s</div>' % (height(scene, W), "".join(parts), "".join(titles)), js
