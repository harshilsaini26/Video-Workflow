"""browser: a mock browser window drops in, its page contents stagger in (SPEC §6.2). Nothing on it links anywhere.

With `screenshot` (a PNG next to storyboard.json, taken with snap-page.py) the window shows the real page instead, in a
fixed 400 px view showing the top of the page, and the title sits under the window. With `focus` ({"y": a pixel row
in the screenshot, "at": its word}) the page holds still, then punches in (1.25x) on that row when the word is said,
never pulling the page's edge into the view.
"""
import math
import explainer_lib as E
from scenes import js_obj, line_px, mono_lines, need, png_size, stagger_for, widest

TYPE = "browser"
BAR = 64                                  # the window's top bar (dots and the address)
PAD = 40                                  # page padding
T_SIZE, T_LH = 60, 1.15                   # page title, DM Sans 700
S_SIZE, S_LH, S_GAP = 36, 1.3, 16         # subtitle, DM Sans 500
B_SIZE, B_H, B_GAP, B_PADX, B_SP = 28, 52, 24, 22, 12   # badges: mono pills, wrapping
BTN_H, BTN_GAP, BTN_SIZE = 84, 32, 36     # the button
U_SIZE = 26                               # the address text
VIEW, CAP_GAP = 400, 30                   # a screenshot's view, and the gap to the title under the window
FOCUS_ZOOM = 1.25                         # the punch-in on a screenshot's focus line

CSS = """
  .br-win { width:100%%; border-radius:26px; overflow:hidden; opacity:0; }
  .br-bar { height:%dpx; display:flex; align-items:center; gap:12px; padding:0 24px; }
  .br-dot { width:16px; height:16px; border-radius:50%%; flex:none; }
  .br-url { flex:1; height:40px; margin-left:18px; border-radius:20px; display:flex; align-items:center; padding:0 20px;
    font-family: var(--label); font-weight:500; font-size:%dpx; white-space:nowrap; overflow:hidden; }
  .br-page { padding:%dpx; }
  .br-title { font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:-.015em; opacity:0; }
  .br-sub { font-weight:500; font-size:%dpx; line-height:%dpx; margin-top:%dpx; opacity:0; }
  .br-badges { display:flex; flex-wrap:wrap; gap:%dpx; margin-top:%dpx; }
  .br-badge { height:%dpx; display:flex; align-items:center; padding:0 %dpx; border-radius:%dpx; font-family: var(--label);
    font-weight:500; font-size:%dpx; white-space:nowrap; opacity:0; }
  .br-btn { height:%dpx; margin-top:%dpx; border-radius:18px; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; opacity:0; }
  .br-view { height:%dpx; overflow:hidden; }
  .br-view img { width:100%%; display:block; }
  .br-cap { width:100%%; margin-top:%dpx; text-align:center; }
""" % (BAR, U_SIZE, PAD, T_SIZE, line_px(T_SIZE, T_LH), S_SIZE, line_px(S_SIZE, S_LH), S_GAP, B_SP, B_GAP, B_H, B_PADX,
       B_H // 2, B_SIZE, BTN_H, BTN_GAP, BTN_SIZE, VIEW, CAP_GAP)


def _badge_w(b):
    return len(b) * B_SIZE * 0.6 + 2 * B_PADX


def bar_width(domain):
    """The address bar's width: its padding, three dots and their gaps, the address chip and the address in mono."""
    return 24 + 3 * 16 + 3 * 12 + 18 + 2 * 20 + int(math.ceil(len(str(domain)) * U_SIZE * 0.62)) + 24


def validate(scene):
    errs = need(scene, ["title"])
    if len(scene.get("badges", [])) > 6:
        errs.append("at most 6 badges")
    if scene.get("screenshot") and (scene.get("badges") or scene.get("button")):
        errs.append("with a screenshot the window shows the real page: drop badges and button")
    f = scene.get("focus")
    if f is not None:
        if not scene.get("screenshot"):
            errs.append("focus needs a screenshot")
        elif not isinstance(f, dict) or not isinstance(f.get("y"), int) or f["y"] < 0 or f.get("at") is None:
            errs.append("focus needs y (a whole pixel in the screenshot) and at (the word that names that line)")
    return errs


def height(scene, width):
    if scene.get("screenshot"):
        h = BAR + VIEW + CAP_GAP + line_px(T_SIZE, T_LH) * E.text_lines(scene["title"], T_SIZE, width, spacing=-0.015)
        if scene.get("subtitle"):
            h += S_GAP + line_px(S_SIZE, S_LH) * E.text_lines(scene["subtitle"], S_SIZE, width, "display500")
        return h
    inner = width - 2 * PAD
    h = BAR + 2 * PAD + line_px(T_SIZE, T_LH) * E.text_lines(scene["title"], T_SIZE, inner, spacing=-0.015)
    if scene.get("subtitle"):
        h += S_GAP + line_px(S_SIZE, S_LH) * E.text_lines(scene["subtitle"], S_SIZE, inner, "display500")
    if scene.get("badges"):
        rows, x = 1, 0
        for b in scene["badges"]:
            w = _badge_w(b)
            if x and x + B_SP + w > inner:
                rows, x = rows + 1, w
            else:
                x = x + (B_SP if x else 0) + w
        h += B_GAP + rows * B_H + (rows - 1) * B_SP
    if scene.get("button"):
        h += BTN_GAP + BTN_H
    return h


def min_width(scene):
    badges = max([_badge_w(b) for b in scene.get("badges", [])] or [0])
    page = int(max(widest([(scene["title"], T_SIZE), (scene.get("subtitle"), S_SIZE), (scene.get("button"), BTN_SIZE)]), badges)) + 2 * PAD
    return max(page, bar_width(scene.get("domain", "")))    # the address shows whole, never clipped


def render(scene, ctx, box):
    c = ctx.c
    sid = ctx.id
    page_bg, bar_bg, url_bg, dim = c["card"], c["chrome"], c["card"], c["dim"]
    dots = "".join('<i class="br-dot" style="background:%s"></i>' % col for col in (c["bad"], c["warn"], c["good"]))
    url = '<div class="br-url" style="background:%s;color:%s">%s</div>' % (url_bg, dim, ctx.esc(scene.get("domain", "")))
    if scene.get("screenshot"):
        return shot(scene, ctx, box, page_bg, bar_bg, dots, url, dim)
    parts = ['<div class="br-title" style="color:%s">%s</div>' % (ctx.ink, ctx.esc(scene["title"]))]
    if scene.get("subtitle"):
        parts.append('<div class="br-sub" style="color:%s">%s</div>' % (dim, ctx.esc(scene["subtitle"])))
    if scene.get("badges"):
        parts.append('<div class="br-badges">%s</div>' % "".join(
            '<span class="br-badge" style="background:%s;color:%s">%s</span>' % (c["accent_soft"], ctx.ink, ctx.esc(b)) for b in scene["badges"]))
    if scene.get("button"):
        parts.append('<div class="br-btn" style="background:%s;color:%s">%s</div>' % (c["accent"], c["on_accent"], ctx.esc(scene["button"])))
    html = ('<div class="br-win" id="%s-win" style="background:%s;box-shadow:inset 0 0 0 2px %s, %s"><div class="br-bar" style="background:%s">%s%s</div>'
            '<div class="br-page">%s</div></div>' % (sid, page_bg, c["card_line"], c["shadow"], bar_bg, dots, url, "".join(parts)))
    n = 1 + bool(scene.get("subtitle")) + len(scene.get("badges", [])) + bool(scene.get("button"))
    js = [ctx.enter("#%s-win" % sid, ctx.t_in, {"y": -60}),
          ctx.enter("#%s .br-title, #%s .br-sub, #%s .br-badge, #%s .br-btn" % (sid, sid, sid, sid), ctx.t_in + 0.2, {"y": 16},
                    stagger=stagger_for(n, 0.08))]
    return html, js


def shot(scene, ctx, box, page_bg, bar_bg, dots, url, dim):
    """The window with the real page in it, punching in on its focus line when there is one; the title under the window."""
    sid = ctx.id
    rel, src = ctx.asset(scene["screenshot"])
    size = png_size(src)
    if not size:
        ctx.fail("screenshot %s is not a PNG (take one with snap-page.py)" % scene["screenshot"])
    tall = int(round(size[1] * box[2] / float(size[0])))       # the page's height at the window's width
    cap = '<div class="br-title" style="color:%s">%s</div>' % (ctx.ink, ctx.esc(scene["title"]))
    if scene.get("subtitle"):
        cap += '<div class="br-sub" style="color:%s">%s</div>' % (dim, ctx.esc(scene["subtitle"]))
    html = ('<div class="br-win" id="%s-win" style="background:%s;box-shadow:inset 0 0 0 2px %s, %s"><div class="br-bar" style="background:%s">%s%s</div>'
            '<div class="br-view" style="background:%s"><img id="%s-shot" src="%s" alt="" /></div></div><div class="br-cap">%s</div>'
            % (sid, page_bg, ctx.c["card_line"], ctx.c["shadow"], bar_bg, dots, url, page_bg, sid, ctx.esc(rel), cap))
    js = [ctx.enter("#%s-win" % sid, ctx.t_in, {"y": -60, "scale": 0.94}),
          ctx.enter("#%s .br-title, #%s .br-sub" % (sid, sid), ctx.t_in + 0.25, {"y": 16}, stagger=0.08)]
    f = scene.get("focus")
    if f:   # the page holds still, then punches in on the line the voice names (MOTION.md: motion with a reason)
        if f["y"] >= size[1]:
            ctx.fail("focus y %d is below the screenshot's %d px" % (f["y"], size[1]))
        t, attrs = ctx.item(f["at"])
        html = html.replace('<div class="br-view" ', '<div class="br-view" id="%s-view"%s ' % (sid, attrs), 1)
        fy = round(f["y"] * box[2] / float(size[0]), 1)              # the line, at the window's width
        # the line to mid-view, but never so far that the page's top or bottom edge pulls into the view
        lo, hi = VIEW - fy - FOCUS_ZOOM * (tall - fy), (FOCUS_ZOOM - 1) * fy
        y = round(min(hi, max(lo, VIEW / 2.0 - fy)), 1) if lo <= hi else round(VIEW / 2.0 - fy, 1)
        js.append("tl.to('#%s-shot', %s, %.3f);" % (sid, js_obj({"y": y, "scale": FOCUS_ZOOM,
                                                                  "transformOrigin": "50%% %spx" % fy, "duration": 0.8, "ease": "expo.out"}), t))
    return html, js
