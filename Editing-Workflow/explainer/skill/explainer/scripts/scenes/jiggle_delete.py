"""jiggle-delete: a home screen of app tiles (an icon and a label) on light paper. The tiles start to jiggle (a few
degrees each way, neighbours out of step) and delete badges appear; on each chosen tile's word its badge turns red and
the tile shrinks away, and the tiles after it slide up into the gap; then Done is pressed and the jiggle settles:

  {"type": "jiggle-delete", "jiggle": {"at": "word:2"},
   "tiles": [{"label": "Notes", "icon": "book"}, {"label": "Timer", "icon": "clock", "at": "word:5"},
             {"label": "Budget", "icon": "calculator"}, {"label": "Mail", "at": "word:8"}, {"label": "Photos"}],
   "done": {"at": "word:12"}}

A tile with `at` is deleted on that word; `icon` is a Lucide name (without one the tile shows its label's first letter).
3 to 8 tiles, in rows of up to four. Without `jiggle` the jiggle starts just after the scene does; without `done` it
settles 1.5 s after the last delete. Tile rows have fixed heights, so the height never depends on the width.
"""
import explainer_lib as E
from scenes import js_obj, need, stagger_for

TYPE = "jiggle-delete"
MAX_SCALE = 1.4
PAD, RADIUS = 36, 44              # the panel
TOP_H, TOP_GAP = 52, 24           # the Done button's row
DONE_SIZE, DONE_PADX = 30, 26     # Done: DM Sans 700
ICON, ICON_R = 116, 30            # an app icon
L_GAP, L_SIZE, L_LH = 12, 30, 40  # its label: DM Sans 500
CELL_H = ICON + L_GAP + L_LH
ROW_GAP, COL_GAP = 28, 24
BADGE, BADGE_OFF = 40, 12         # the delete badge, over the icon's top-left corner
TURN, STEP = 2.2, 0.13            # the jiggle: degrees each way, seconds a swing
MONO_SIZE = 52
MIN_TILES, MAX_TILES = 3, 8

CSS = """
  .jd { position:relative; width:100%%; border-radius:%dpx; padding:%dpx; opacity:0; }
  .jd-top { height:%dpx; margin-bottom:%dpx; display:flex; justify-content:flex-end; }
  .jd-done { height:%dpx; padding:0 %dpx; border-radius:%dpx; display:flex; align-items:center; font-weight:700; font-size:%dpx;
    line-height:1; white-space:nowrap; opacity:0; }
  .jd-grid { position:relative; }
  .jd-tile { position:absolute; height:%dpx; display:flex; flex-direction:column; align-items:center; opacity:0; }
  .jd-icon { position:relative; width:%dpx; height:%dpx; border-radius:%dpx; flex:none; display:flex; align-items:center;
    justify-content:center; font-weight:700; font-size:%dpx; line-height:1; }
  .jd-icon svg { width:50%%; height:50%%; }
  .jd-badge { position:absolute; left:-%dpx; top:-%dpx; width:%dpx; height:%dpx; border-radius:50%%; display:flex;
    align-items:center; justify-content:center; opacity:0; }
  .jd-badge i { width:44%%; height:4px; border-radius:2px; }
  .jd-label { margin-top:%dpx; height:%dpx; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
""" % (RADIUS, PAD, TOP_H, TOP_GAP, TOP_H, DONE_PADX, TOP_H // 2, DONE_SIZE, CELL_H, ICON, ICON, ICON_R, MONO_SIZE,
       BADGE_OFF, BADGE_OFF, BADGE, BADGE, L_GAP, L_LH, L_SIZE, L_LH)


def cols(n):
    return n if n <= 4 else (3 if n <= 6 else 4)


def rows(n):
    return -(-n // cols(n))


def validate(scene):
    errs = need(scene, ["tiles"])
    tiles = scene.get("tiles") or []
    if not MIN_TILES <= len(tiles) <= MAX_TILES:
        errs.append("a home screen shows %d to %d tiles (got %d)" % (MIN_TILES, MAX_TILES, len(tiles)))
    for i, t in enumerate(tiles):
        if not isinstance(t, dict) or not str(t.get("label") or "").strip():
            errs.append("tile %d has no label" % i)
        elif len(t["label"]) > 14:
            errs.append("tile %d's label is %d characters; an app name is short (at most 14)" % (i, len(t["label"])))
    gone = [t for t in tiles if isinstance(t, dict) and t.get("at") is not None]
    if tiles and not gone:
        errs.append("no tile is deleted: give the tiles to delete an at (the word they go on)")
    if tiles and len(gone) == len(tiles):
        errs.append("every tile is deleted: keep at least one")
    for k in ("jiggle", "done"):
        if scene.get(k) is not None and (not isinstance(scene[k], dict) or scene[k].get("at") is None):
            errs.append("%s needs at" % k)
    return errs


def height(scene, width):
    r = rows(len(scene["tiles"]))
    return 2 * PAD + TOP_H + TOP_GAP + r * CELL_H + (r - 1) * ROW_GAP


def min_width(scene):
    n = len(scene["tiles"])
    cell = max([ICON + 2 * BADGE_OFF + 4] + [E.text_width(t["label"], L_SIZE, "display500") + 6 for t in scene["tiles"]])
    return int(cols(n) * cell + (cols(n) - 1) * COL_GAP + 2 * PAD) + 1


def render(scene, ctx, box):
    c, mo = ctx.pc, ctx.tokens["motion"]
    sid = ctx.id
    tiles = scene["tiles"]
    n, nc = len(tiles), cols(len(tiles))
    cell_w = (box[2] - 2 * PAD - (nc - 1) * COL_GAP) / float(nc)
    slot = lambda k: ((k % nc) * (cell_w + COL_GAP), (k // nc) * (CELL_H + ROW_GAP))
    looks = [c["series"][0], c["series"][1], c["series"][2], c["series"][3], (c["ink"], c["card"]), (c["chrome"], c["ink"])]
    js, parts = [], []
    js.append(ctx.enter("#%s-panel" % sid, ctx.t_in, {"y": 40}))

    # when it jiggles, which tiles go and when, when it settles
    if scene.get("jiggle"):
        t_j, j_attrs = ctx.item(scene["jiggle"]["at"])
    else:
        t_j, j_attrs = ctx.t_in + 0.6, ""
    dels = []
    for i, t in enumerate(tiles):
        if t.get("at") is not None:
            td, attrs = ctx.item(t["at"])
            dels.append((td, i))
    dels.sort()
    if dels[0][0] < t_j + 0.3:
        ctx.fail("the first tile is deleted at %.2f s, before the tiles start to jiggle (%.2f s); jiggle a word earlier" % (dels[0][0], t_j))
    if any(b[0] - a[0] < 0.35 for a, b in zip(dels, dels[1:])):
        ctx.fail("two deletes come too close together (under 0.35 s): give each its own word")
    if scene.get("done"):
        t_s, d_attrs = ctx.item(scene["done"]["at"])
    else:
        t_s, d_attrs = min(dels[-1][0] + 1.5, ctx.t_out - 0.6), ""
    if t_s < dels[-1][0] + 0.8:
        ctx.fail("done at %.2f s comes before the last tile has gone and the rest moved up (%.2f s)" % (t_s, dels[-1][0] + 0.8))

    for i, t in enumerate(tiles):
        fill, on = looks[i % len(looks)]
        x, y = slot(i)
        mark = ctx.icon(t["icon"]) if t.get("icon") else ctx.esc(t["label"].strip()[0].upper())
        attrs = ctx.item(t["at"])[1] if t.get("at") is not None else ""
        parts.append('<div class="jd-tile %s" id="%s-t%d"%s style="left:%.1fpx;top:%dpx;width:%.1fpx">'
                     '<div class="jd-icon" style="background:%s;color:%s">%s<span class="jd-badge" id="%s-b%d" style="background:%s">'
                     '<i style="background:%s"></i></span></div><div class="jd-label" style="color:%s">%s</div></div>'
                     % ("ev" if (i % nc + i // nc) % 2 == 0 else "od", sid, i, attrs, x, y, cell_w, fill, on, mark, sid, i, c["line"],
                        c["ink"], c["ink"], ctx.esc(t["label"])))
    js.append(ctx.enter("#%s .jd-tile" % sid, ctx.t_in + 0.1, {"scale": 0.9}, stagger=stagger_for(n, 0.05)))

    # edit mode: the badges and Done appear, and the jiggle runs until Done
    js.append(ctx.enter("#%s .jd-badge" % sid, t_j, {"scale": 0.4}, stagger=stagger_for(n, 0.03), dur=0.3))
    js.append(ctx.enter("#%s-done" % sid, t_j, {"y": -10}))
    t, k = t_j, 0
    while t + STEP <= t_s:
        a = TURN if k % 2 == 0 else -TURN
        for grp, sign in (("ev", 1), ("od", -1)):
            ctx.ambient("tl.to('#%s .jd-tile.%s', %s, %.3f);" % (sid, grp, js_obj({"rotation": sign * a, "duration": STEP, "ease": "sine.inOut"}), t))
        t, k = t + STEP, k + 1
    js.append("tl.to('#%s .jd-tile', %s, %.3f);" % (sid, js_obj({"rotation": 0, "duration": 0.2, "ease": mo["enter_ease"]}), t_s))

    # each delete: the badge goes red, the tile shrinks away, the tiles after it move up a place
    order = list(range(n))
    where = {i: (0.0, 0.0) for i in range(n)}            # each tile's offset from its first place
    for td, i in dels:
        js.append("tl.to('#%s-b%d', %s, %.3f);" % (sid, i, js_obj({"backgroundColor": c["bad"], "scale": 1.15, "duration": 0.12,
                                                                  "ease": mo["enter_ease"]}), td))
        js.append("tl.to('#%s-t%d', %s, %.3f);" % (sid, i, js_obj({"scale": 0, "opacity": 0, "duration": 0.3, "ease": mo["exit_ease"]}), td + 0.12))
        order.remove(i)
        for k, j in enumerate(order):
            x0, y0 = slot(j)
            x1, y1 = slot(k)
            to = (round(x1 - x0, 1), round(y1 - y0, 1))
            if to != where[j]:
                js.append("tl.fromTo('#%s-t%d', %s, %s, %.3f);" % (sid, j, js_obj({"x": where[j][0], "y": where[j][1]}),
                                                                   js_obj({"x": to[0], "y": to[1], "duration": 0.5, "ease": "expo.out",
                                                                           "immediateRender": False}), td + 0.38 + 0.03 * k))
                where[j] = to

    # Done: pressed, it leaves with the badges, and the tiles hold still
    js.append("tl.fromTo('#%s-done', { scale: 1 }, %s, %.3f);" % (sid, js_obj({"scale": 0.9, "duration": 0.1, "ease": "power2.out",
                                                                               "immediateRender": False}), t_s))
    js.append("tl.to('#%s-done', %s, %.3f);" % (sid, js_obj({"opacity": 0, "scale": 1, "duration": 0.3, "ease": mo["exit_ease"]}), t_s + 0.1))
    js.append("tl.to('#%s .jd-badge', %s, %.3f);" % (sid, js_obj({"opacity": 0, "scale": 0.4, "duration": 0.25, "ease": mo["exit_ease"]}), t_s + 0.05))
    r = rows(n)
    grid_h = r * CELL_H + (r - 1) * ROW_GAP
    top = ('<div class="jd-top"><span class="jd-done" id="%s-done"%s style="background:%s;color:%s">%s</span></div>'
           % (sid, d_attrs, c["accent_soft"], c["accent"], ctx.esc(scene.get("done_label") or "Done")))
    html = ('<div class="jd" id="%s-panel" style="%s">%s<div class="jd-grid" id="%s-grid"%s style="height:%dpx">%s</div></div>'
            % (sid, ctx.paper_card(), top, sid, j_attrs, grid_h, "".join(parts)))
    return html, js
