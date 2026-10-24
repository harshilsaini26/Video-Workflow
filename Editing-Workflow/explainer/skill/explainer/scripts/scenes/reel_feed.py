"""reel-feed: a phone (light paper) playing a reels feed. The current reel fills the screen: its picture, a column of
like, comment and share counts that keep ticking up while it holds, and its username and caption on a strip below.
On each next reel's word a thumb swipes up and the feed slides to it. For "you scroll past", "the next one hooks you":

  {"type": "reel-feed",
   "reels": [{"user": "@studio.notes", "caption": "Three grades every film uses", "likes": 12400, "comments": 318, "shares": 1200},
             {"user": "@colourlab", "caption": "Teal and orange, explained", "likes": 98000, "comments": 2100, "shares": 5400,
              "at": "word:9"}]}

Two or three reels; the first shows from the scene's start (its `at` is optional), each next one arrives on its own
word. A reel's own `src`, else the scene's `src` (each reel showing another part of it), else a built-in picture; every
picture is a PNG or JPG next to storyboard.json. The counts and usernames are furniture (DECOR_KEYS). A caption takes
at most two lines on the phone.
"""
import math
import explainer_lib as E
from scenes import js_obj, need
from scenes import _vg

TYPE = "reel-feed"
DECOR_KEYS = {"likes", "comments", "shares", "user"}
PHONE_W, PHONE_H, PHONE_R = 360, 600, 56  # the phone
BEZ, SCREEN_R = 12, 44                   # the bezel and the screen's corners
SW, SH = PHONE_W - 2 * BEZ, PHONE_H - 2 * BEZ    # the screen: 336 x 576
INFO_PAD, U_SIZE, U_LINE, AV = 16, 28, 36, 36    # the strip under the picture: padding, username (DM Sans 700), avatar
CAP_SIZE, CAP_LINE, CAP_GAP = 28, 34, 6  # the caption, DM Sans 500, two lines at most
INFO_H = INFO_PAD + U_LINE + CAP_GAP + 2 * CAP_LINE + INFO_PAD   # 160
PIC = SH - INFO_H
CAP_W = SW - 2 * INFO_PAD
ICON, N_SIZE, N_LINE = 34, 28, 34        # the action column: icon, count (DM Sans 700)
A_PAD, A_GAP, A_IN = 12, 10, 12          # its padding, the gap between actions, its inset from the screen's edge
ISLAND_W, ISLAND_H = 92, 26
DOT = 46                                 # the thumb's touch
SWIPE = 0.75

CSS = """
  .rf { position:relative; width:100%%; display:flex; justify-content:center; }
  .rf-ph { position:relative; width:%dpx; height:%dpx; border-radius:%dpx; opacity:0; }
  .rf-sc { position:absolute; left:%dpx; top:%dpx; width:%dpx; height:%dpx; border-radius:%dpx; overflow:hidden; }
  .rf-strip { position:absolute; left:0; top:0; width:100%%; }
  .rf-reel { position:relative; width:100%%; height:%dpx; }
  .rf-pic { position:absolute; left:0; top:0; width:100%%; height:%dpx; overflow:hidden; }
  .rf-info { position:absolute; left:0; top:%dpx; width:100%%; height:%dpx; padding:%dpx; }
  .rf-u { display:flex; align-items:center; gap:10px; height:%dpx; font-weight:700; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .rf-av { flex:none; width:%dpx; height:%dpx; border-radius:50%%; }
  .rf-cap { margin-top:%dpx; font-weight:500; font-size:%dpx; line-height:%dpx; }
  .rf-act { position:absolute; right:%dpx; display:flex; flex-direction:column; align-items:center; gap:%dpx; padding:%dpx 0;
    border-radius:24px; }
  .rf-a { display:flex; flex-direction:column; align-items:center; }
  .rf-a svg { width:%dpx; height:%dpx; display:block; }
  .rf-n { font-weight:700; font-size:%dpx; line-height:%dpx; white-space:nowrap; text-align:center; }
  .rf-isl { position:absolute; left:50%%; top:%dpx; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:%dpx; }
  .rf-dot { position:absolute; left:50%%; top:0; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:50%%; opacity:0; }
""" % (PHONE_W, PHONE_H, PHONE_R, BEZ, BEZ, SW, SH, SCREEN_R, SH, PIC, PIC, INFO_H, INFO_PAD, U_LINE, U_SIZE, U_LINE, AV, AV,
       CAP_GAP, CAP_SIZE, CAP_LINE, A_IN, A_GAP, A_PAD, ICON, ICON, N_SIZE, N_LINE, BEZ + 10, ISLAND_W, ISLAND_H,
       ISLAND_W // 2, ISLAND_H // 2, DOT, DOT, DOT // 2) + _vg.CSS

COUNTS = ("likes", "comments", "shares")
GLYPH = {"likes": "heart", "comments": "comment", "shares": "send"}


def _count_ok(v):
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v < 1e9


def validate(scene):
    errs = need(scene, ["reels"])
    reels = scene.get("reels") or []
    if not isinstance(reels, list) or not 2 <= len(reels) <= 3:
        return errs + ["a reel-feed takes 2 or 3 reels (got %s)" % (len(reels) if isinstance(reels, list) else reels,)]
    for i, r in enumerate(reels):
        if not isinstance(r, dict):
            errs.append("reel %d is an object" % i)
            continue
        for k in ("user", "caption"):
            if not str(r.get(k) or "").strip():
                errs.append("reel %d has no %s" % (i, k))
        for k in COUNTS:
            if not _count_ok(r.get(k)):
                errs.append("reel %d: %s is a whole number (got %r)" % (i, k, r.get(k)))
        if i and r.get("at") is None:
            errs.append("reel %d has no at (the word the feed swipes to it)" % i)
        if r.get("caption") and E.text_lines(r["caption"], CAP_SIZE, CAP_W, "display500") > 2:
            errs.append("reel %d: the caption takes more than two lines on the phone; shorten it" % i)
        if r.get("user") and E.text_width(r["user"], U_SIZE) > CAP_W - AV - 10:
            errs.append("reel %d: the username is too wide for the phone; shorten it" % i)
        e = _vg.check_src(r.get("src"), "reel %d: src" % i)
        if e:
            errs.append(e)
    e = _vg.check_src(scene.get("src"))
    return errs + ([e] if e else [])


def height(scene, width):
    return PHONE_H


def min_width(scene):
    words = max(int(math.ceil(E.text_width(w, CAP_SIZE, "display500"))) for r in scene["reels"] for w in str(r["caption"]).split())
    return max(PHONE_W, words + 2 * INFO_PAD + 2 * BEZ)


def bump(v):
    """Where a count has ticked to by the time its reel leaves: a few per cent on, at least a handful."""
    return v + max(3, int(round(v * 0.03)))


def _act_w(scene):
    w = 0
    for r in scene["reels"]:
        for k in COUNTS:
            v0, v1 = r[k], bump(r[k])
            for v in sorted({v0, v1} | {int(v0 + (v1 - v0) * j / 40.0) for j in range(41)}):
                w = max(w, E.text_width(_vg.count(v), N_SIZE))
    return max(ICON, int(math.ceil(w))) + 2 * 14


def render(scene, ctx, box):
    pc, sid = ctx.pc, ctx.id
    mo = ctx.tokens["motion"]
    reels = scene["reels"]
    series = ctx.pc["series"]
    aw = _act_w(scene)
    act_h = 2 * A_PAD + 3 * (ICON + N_LINE) + 2 * A_GAP
    times = [ctx.t_in]
    for i, r in enumerate(reels):
        if i:
            t, _ = ctx.item(r["at"])
            if t < times[-1] + SWIPE:
                ctx.fail("reel %d arrives %.2f s after the one before it; give each reel at least %.2f s" % (i, t - times[-1], SWIPE))
            times.append(t)
    parts, js = [], []
    for i, r in enumerate(reels):
        attrs = ctx.item(r["at"])[1] if i else (ctx.item(r["at"])[1] if r.get("at") is not None else "")
        src = r.get("src") or scene.get("src")
        acts = []
        for k in COUNTS:
            acts.append('<div class="rf-a">%s<span class="rf-n" id="%s-%s%d" style="width:%dpx">%s</span></div>'
                        % (_vg.glyph(GLYPH[k], width=2.2), sid, k[0], i, aw - 2 * 14, _vg.count(r[k])))
        parts.append('<div class="rf-reel" id="%s-r%d"%s><div class="rf-pic" style="background:%s">%s</div>'
                     '<div class="rf-act" style="top:%dpx;width:%dpx;background:%s;color:%s">%s</div>'
                     '<div class="rf-info" style="background:%s"><div class="rf-u" style="color:%s"><i class="rf-av" style="background:%s"></i>%s</div>'
                     '<div class="rf-cap" style="color:%s">%s</div></div></div>'
                     % (sid, i, attrs, pc["chrome"], _vg.picture(ctx, src, "r%d" % i, seed=(1, 4, 0)[i], pos=("50% 30%", "30% 70%", "70% 50%")[i]),
                        (PIC - act_h) // 2 + 14, aw, pc["card"], pc["ink"], "".join(acts), pc["card"], pc["ink"], series[i][0],
                        ctx.esc(r["user"]), pc["dim"], ctx.esc(r["caption"])))
        # its counts tick up while it is on screen (ambient: the hold's one alive thing)
        t0 = times[i] + (0.5 if i == 0 else SWIPE)
        t1 = times[i + 1] if i + 1 < len(reels) else ctx.t_out
        if t1 - t0 > 0.3:
            for k in COUNTS:
                ctx.ambient(_vg.ticker("%s-%s%d" % (sid, k[0], i), t0, round(t1 - t0, 3), r[k], bump(r[k]), _vg.COUNT_JS))
        if i:   # the thumb swipes up and the feed follows it to this reel
            t = times[i]
            js.append(_vg.tween("#%s-dot" % sid, {"y": SH - 120, "opacity": 0}, {"y": SH - 170, "opacity": 1, "duration": 0.12, "ease": "power2.out"}, t - 0.12))
            js.append(_vg.tween("#%s-dot" % sid, {"y": SH - 170, "opacity": 1}, {"y": 140, "opacity": 0, "duration": 0.45, "ease": "power3.in"}, t))
            js.append(_vg.tween("#%s-strip" % sid, {"y": -(i - 1) * SH}, {"y": -i * SH, "duration": SWIPE, "ease": "expo.out"}, t))
    html = ('<div class="rf" style="height:%dpx"><div class="rf-ph" id="%s-ph" style="%s"><div class="rf-sc" style="background:%s">'
            '<div class="rf-strip" id="%s-strip" style="height:%dpx">%s</div><i class="rf-isl" style="background:%s"></i>'
            '<i class="rf-dot" id="%s-dot" style="background:%s;box-shadow:inset 0 0 0 3px %s"></i></div></div></div>'
            % (PHONE_H, sid, ctx.paper_card(), pc["chrome"], sid, SH * len(reels), "".join(parts), pc["ink"], sid,
               E.rgba(pc["card"], 0.7), pc["card"]))
    js = [ctx.enter("#%s-ph" % sid, ctx.t_in, {"y": 60, "scale": 0.96})] + js
    return html, js
