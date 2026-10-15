"""list-cards: two to four cards, each arriving on its word (SPEC §6.2)."""
import explainer_lib as E
from scenes import line_px, need, widest

TYPE = "list-cards"
SIZE, LH = 56, 1.15            # card label: DM Sans 700
PAD_Y, PAD_X, BAR, GAP = 26, 36, 8, 22   # card padding, accent bar, gap between cards


CSS = """
  .l-card { width:100%%; display:flex; align-items:center; border-radius:22px; padding:%dpx %dpx %dpx %dpx;
    border-left:%dpx solid; font-weight:700; font-size:%dpx; line-height:%dpx; opacity:0; }
  .l-card + .l-card { margin-top:%dpx; }
""" % (PAD_Y, PAD_X, PAD_Y, PAD_X - BAR, BAR, SIZE, line_px(SIZE, LH), GAP)


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items") or []
    if not 2 <= len(items) <= 4:
        errs.append("list-cards take 2 to 4 items (got %d)" % len(items))
    errs += ["item %d has no label" % i for i, it in enumerate(items) if not it.get("label")]
    errs += ["item %d has no at" % i for i, it in enumerate(items) if it.get("at") is None]
    return errs


def height(scene, width):
    inner = width - 2 * PAD_X
    rows = [2 * PAD_Y + line_px(SIZE, LH) * E.text_lines(it["label"], SIZE, inner) for it in scene["items"]]
    return sum(rows) + GAP * (len(rows) - 1)


def min_width(scene):
    return widest([(it.get("label"), SIZE) for it in scene["items"]], pad=2 * PAD_X)


def render(scene, ctx, box):
    c = ctx.tokens["colors"]
    face = "background:#FFFFFF;box-shadow:0 14px 40px rgba(11,12,16,.12)" if ctx.light else "background:rgba(255,255,255,.10)"
    html, js = [], []
    for i, it in enumerate(scene["items"]):
        t, attrs = ctx.item(it["at"])
        html.append('<div class="l-card" id="%s-c%d"%s style="%s;border-left-color:%s;color:%s">%s</div>'
                    % (ctx.id, i, attrs, face, c["cyan"] if not ctx.light else c["magenta"], ctx.ink, ctx.esc(it["label"])))
        js.append(ctx.enter("#%s-c%d" % (ctx.id, i), t, {"x": -60, "scale": 0.96}))
    return "".join(html), js
