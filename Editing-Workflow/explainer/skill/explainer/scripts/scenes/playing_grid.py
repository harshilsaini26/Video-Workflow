"""playing-grid: a wall of video tiles, 2x2 to 3x3, each waiting as an empty frame until its word, then landing with its
picture and a progress bar that keeps running while the grid holds. On the pick's word one tile lifts (it grows a
little and takes the accent ring) and the others dim. For "out of all these clips", "the one that worked was this one":

  {"type": "playing-grid", "src": "frames.jpg",
   "tiles": [{"label": "Vlog", "at": "word:3"}, {"label": "Tutorial", "at": "word:4"}, {"at": "word:5"}, {"at": "word:6"}],
   "pick": {"tile": 1, "at": "word:9"}}

Two columns up to 4 tiles, three above (`cols` sets it: 2 or 3); at most three rows. A tile's own `src`, else the
scene's `src` (each tile showing another part of it), else a built-in picture; every picture is a PNG or JPG next to
storyboard.json. `label` is an optional short name on a chip (a word or two: in three columns a chip has about
200 px of a 780 px column).
"""
import math
import explainer_lib as E
from scenes import SLOT, js_obj, need
from scenes import _vg

TYPE = "playing-grid"
DECOR_KEYS = {"cols", "tile"}
PAD, GAP, RADIUS = 16, 18, 22            # room for the lift, between tiles, the tiles' corners
TILE_H = {2: 250, 3: 176}                # a tile's height, by row count
LIFT = 1.06                              # the picked tile grows this much
DIM = 0.38                               # the others dim to this
C_SIZE, C_H, C_PAD, C_IN = 28, 42, 14, 12   # the label chip: DM Sans 500, its height, padding, inset
BAR_H, BAR_IN = 6, 14                    # the progress bar and its inset from the tile's edges
TILE_MIN = 132
CROPS = ["20% 30%", "80% 40%", "45% 75%", "60% 15%", "10% 85%", "90% 80%", "35% 50%", "70% 60%", "50% 25%"]

CSS = """
  .pg { position:relative; width:100%%; }
  .pg-t { position:absolute; border-radius:%dpx; overflow:hidden; opacity:0; }
  .pg-pic { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .pg-bar { position:absolute; left:%dpx; right:%dpx; bottom:%dpx; height:%dpx; border-radius:%dpx; overflow:hidden; }
  .pg-fill { position:absolute; left:0; top:0; height:100%%; border-radius:%dpx; }
  .pg-chip { position:absolute; left:%dpx; top:%dpx; height:%dpx; padding:0 %dpx; border-radius:%dpx; display:flex;
    align-items:center; font-weight:500; font-size:%dpx; line-height:1; white-space:nowrap; }
  .pg-ring { position:absolute; left:0; top:0; width:100%%; height:100%%; border-radius:%dpx; opacity:0; pointer-events:none; }
""" % (RADIUS, BAR_IN, BAR_IN, BAR_IN, BAR_H, BAR_H // 2, BAR_H // 2, C_IN, C_IN, C_H, C_PAD, C_H // 2, C_SIZE, RADIUS) + _vg.CSS


def cols(scene):
    return scene.get("cols") or (2 if len(scene["tiles"]) <= 4 else 3)


def rows(scene):
    return int(math.ceil(len(scene["tiles"]) / float(cols(scene))))


def validate(scene):
    errs = need(scene, ["tiles"])
    tiles = scene.get("tiles") or []
    if not isinstance(tiles, list) or not 4 <= len(tiles) <= 9:
        return errs + ["a playing-grid takes 4 to 9 tiles, a 2x2 to a 3x3 (got %s)" % (len(tiles) if isinstance(tiles, list) else tiles,)]
    c = scene.get("cols")
    if c is not None and c not in (2, 3):
        errs.append("cols is 2 or 3 (got %r)" % (c,))
    elif not 2 <= int(math.ceil(len(tiles) / float(c or (2 if len(tiles) <= 4 else 3)))) <= 3:
        errs.append("%d tiles in %d columns make %d rows; a grid has 2 or 3" % (len(tiles), c, math.ceil(len(tiles) / float(c))))
    for i, t in enumerate(tiles):
        if not isinstance(t, dict):
            errs.append("tile %d is an object" % i)
            continue
        if t.get("at") is None:
            errs.append("tile %d has no at" % i)
        if t.get("label") is not None and not str(t["label"]).strip():
            errs.append("tile %d: label is empty" % i)
        e = _vg.check_src(t.get("src"), "tile %d: src" % i)
        if e:
            errs.append(e)
    pk = scene.get("pick")
    if pk is not None:
        if not isinstance(pk, dict) or not isinstance(pk.get("tile"), int) or isinstance(pk.get("tile"), bool) \
                or not 0 <= pk["tile"] < len(tiles) or pk.get("at") is None:
            errs.append("pick needs tile (an index, 0 to %d) and at (its word)" % (len(tiles) - 1))
    e = _vg.check_src(scene.get("src"))
    return errs + ([e] if e else [])


def height(scene, width):
    r = rows(scene)
    return 2 * PAD + r * TILE_H[r] + (r - 1) * GAP


def _tile_min(scene):
    chips = [int(math.ceil(E.text_width(t["label"], C_SIZE, "display500"))) + 2 * C_PAD + 2 * C_IN for t in scene["tiles"] if t.get("label")]
    return max([TILE_MIN] + chips)


def min_width(scene):
    c = cols(scene)
    return 2 * PAD + c * _tile_min(scene) + (c - 1) * GAP


def layout(scene, width):
    """[(left, top, width, height)] of each tile: rows left to right, a short last row centred."""
    c, r, n = cols(scene), rows(scene), len(scene["tiles"])
    th = TILE_H[r]
    tw = (width - 2 * PAD - (c - 1) * GAP) / float(c)
    out = []
    for i in range(n):
        row, col = divmod(i, c)
        in_row = min(c, n - row * c)
        off = (c - in_row) * (tw + GAP) / 2.0
        out.append((round(PAD + off + col * (tw + GAP), 2), PAD + row * (th + GAP), round(tw, 2), th))
    return out


def progress(i):
    """Where tile i's video starts (% of its length) and how fast it runs (% a second): each its own, so the bars never
    march in step."""
    return 6 + (i * 17) % 34, 2.5 + (i * 7) % 5 * 0.6


def render(scene, ctx, box):
    pc, sid, W = ctx.pc, ctx.id, box[2]
    mo = ctx.tokens["motion"]
    tiles = scene["tiles"]
    track = E.rgba(pc["card"], 0.45)
    parts, js, times = [], [], []
    for i, (tile, (x, y, w, h)) in enumerate(zip(tiles, layout(scene, W))):
        t, attrs = ctx.item(tile["at"])
        times.append(t)
        src = tile.get("src") or scene.get("src")
        pic = _vg.picture(ctx, src, "t%d" % i, seed=i, pos=CROPS[i % len(CROPS)])
        p0, rate = progress(i)
        chip = ('<span class="pg-chip gt" style="background:%s;color:%s">%s</span>' % (pc["card"], pc["ink"], ctx.esc(tile["label"]))
                if tile.get("label") else "")
        parts.append('<div class="pg-t" id="%s-t%d"%s style="left:%spx;top:%dpx;width:%spx;height:%dpx;background:%s;box-shadow:inset 0 0 0 2px %s">'
                     '<div class="pg-pic gt">%s</div><div class="pg-bar gt" style="background:%s"><i class="pg-fill" id="%s-f%d" '
                     'style="width:%d%%;background:%s"></i></div>%s<i class="pg-ring" id="%s-r%d" style="box-shadow:inset 0 0 0 5px %s"></i></div>'
                     % (sid, i, attrs, x, y, w, h, pc["chrome"], pc["line"], pic, track, sid, i, p0, pc["card"], chip, sid, i, pc["accent"]))
        js += ctx.slot("#%s-t%d" % (sid, i))
        js.append(ctx.enter("#%s-t%d" % (sid, i), t, {"opacity": SLOT, "scale": 0.92}))
        js.append(ctx.fill("#%s-t%d" % (sid, i), t))
        # it plays while the grid holds: its bar runs on (ambient: the hold's one alive thing)
        t0 = t + 0.4
        if t0 < ctx.t_out:
            p1 = min(97.0, p0 + rate * (ctx.t_out - t0))
            ctx.ambient(_vg.tween("#%s-f%d" % (sid, i), {"width": "%d%%" % p0},
                                  {"width": "%s%%" % _vg._num(round(p1, 2)), "duration": round(ctx.t_out - t0, 3), "ease": "none"}, t0))
    pk = scene.get("pick")
    if pk:
        tp, attrs = ctx.item(pk["at"])
        if tp < max(times):
            ctx.fail("the pick (%.2f s) comes before every tile has landed (the last at %.2f s); pick after the last tile" % (tp, max(times)))
        k = pk["tile"]
        parts[k] = parts[k].replace('<i class="pg-ring" id="%s-r%d"' % (sid, k), '<i class="pg-ring" id="%s-r%d"%s' % (sid, k, attrs), 1)
        js.append("tl.set('#%s-t%d', { zIndex: 2 }, %.3f);" % (sid, k, tp))
        js.append(_vg.tween("#%s-t%d" % (sid, k), {"scale": 1}, {"scale": LIFT, "duration": 0.5, "ease": mo["enter_ease"]}, tp))
        js.append(_vg.tween("#%s-r%d" % (sid, k), {"opacity": 0}, {"opacity": 1, "duration": 0.3, "ease": mo["enter_ease"]}, tp))
        others = ", ".join("#%s-t%d" % (sid, i) for i in range(len(tiles)) if i != k)
        js.append(_vg.tween(others, {"opacity": 1}, {"opacity": DIM, "duration": 0.4, "ease": mo["enter_ease"]}, tp))
    return '<div class="pg" style="height:%dpx">%s</div>' % (height(scene, W), "".join(parts)), js
