"""icon-row: two to four Lucide icons (ISC, inlined from the local copy) pop in with their labels (SPEC §6.2)."""
import os, re
import explainer_lib as E
from scenes import line_px, need, widest

TYPE = "icon-row"
TILE, ICON = 150, 84
L_SIZE, L_LH, L_GAP = 36, 1.2, 20
COL_GAP = 24
INSTALL = "npm pack lucide-static@0.454.0, then copy its icons/*.svg to assets/vendor/lucide/"
_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

CSS = """
  .ic-row { width:100%%; display:flex; justify-content:center; gap:%dpx; }
  .ic-col { flex:1 1 0; min-width:0; display:flex; flex-direction:column; align-items:center; }
  .ic-tile { width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center; justify-content:center; opacity:0; flex:none; }
  .ic-tile svg { width:%dpx; height:%dpx; }
  .ic-label { font-weight:700; font-size:%dpx; line-height:%dpx; margin-top:%dpx; text-align:center; opacity:0; }
""" % (COL_GAP, TILE, TILE, ICON, ICON, L_SIZE, line_px(L_SIZE, L_LH), L_GAP)


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items") or []
    if not 2 <= len(items) <= 4:
        errs.append("icon-row takes 2 to 4 items (got %d)" % len(items))
    for i, it in enumerate(items):
        if not _NAME.match(str(it.get("icon", ""))):
            errs.append("item %d icon %r is not a Lucide name (lower-case, hyphens)" % (i, it.get("icon")))
        if not it.get("label") or it.get("at") is None:
            errs.append("item %d needs a label and at" % i)
    return errs


def _col(scene, width):
    n = len(scene["items"])
    return (width - COL_GAP * (n - 1)) / n


def height(scene, width):
    col = _col(scene, width)
    return TILE + L_GAP + line_px(L_SIZE, L_LH) * max(E.text_lines(it["label"], L_SIZE, col) for it in scene["items"])


def min_width(scene):
    n = len(scene["items"])
    return max(TILE, widest([(it["label"], L_SIZE) for it in scene["items"]])) * n + COL_GAP * (n - 1)


def render(scene, ctx, box):
    c = ctx.tokens["colors"]
    sid = ctx.id
    acc = c["magenta"] if ctx.light else c["cyan"]
    tile_bg = "#FFFFFF" if ctx.light else "rgba(255,255,255,.10)"
    cols, js = [], []
    for i, it in enumerate(scene["items"]):
        name = "lucide/%s.svg" % it["icon"]
        if not os.path.exists(os.path.join(ctx.vendor_dir, name)):
            ctx.fail("unknown icon %r: no vendor/%s (browse lucide.dev/icons; get the set with: %s)" % (it["icon"], name, INSTALL))
        with open(os.path.join(ctx.vendor_dir, name)) as f:
            svg = f.read().strip()
        if not svg.startswith("<svg") or re.search(r"<script|on\w+=", svg, re.I):
            ctx.fail("vendor/%s is not a plain SVG icon" % name)
        t, attrs = ctx.item(it["at"])
        cols.append('<div class="ic-col"%s><div class="ic-tile" id="%s-i%d" style="background:%s;color:%s">%s</div>'
                    '<div class="ic-label" id="%s-l%d" style="color:%s">%s</div></div>'
                    % (attrs, sid, i, tile_bg, acc, svg, sid, i, ctx.ink, ctx.esc(it["label"])))
        js.append(ctx.enter("#%s-i%d" % (sid, i), t, {"scale": 0.5}))
        js.append(ctx.enter("#%s-l%d" % (sid, i), t + 0.1, {"y": 16}))
    return '<div class="ic-row">%s</div>' % "".join(cols), js
