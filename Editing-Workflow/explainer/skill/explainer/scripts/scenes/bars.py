"""bars: horizontal bars grow on their words; the highlighted row is the accent (SPEC §6.2)."""
import explainer_lib as E
from scenes import line_px, need, widest

TYPE = "bars"
NEEDS_SOURCE = True
L_SIZE, L_LH = 40, 1.2         # row label (left) and value text (right), DM Sans 700
BAR, B_GAP, ROW_GAP = 52, 10, 26
T_GAP = 24                     # between the label and the value text

CSS = """
  .b-row { width:100%%; opacity:0; }
  .b-row + .b-row { margin-top:%dpx; }
  .b-head { display:flex; justify-content:space-between; align-items:flex-end; gap:%dpx; font-weight:700; font-size:%dpx;
    line-height:%dpx; margin-bottom:%dpx; }
  .b-text { white-space:nowrap; font-variant-numeric: tabular-nums; }
  .b-track { width:100%%; height:%dpx; border-radius:12px; overflow:hidden; }
  .b-fill { height:100%%; border-radius:12px; transform-origin:0 50%%; }
""" % (ROW_GAP, T_GAP, L_SIZE, line_px(L_SIZE, L_LH), B_GAP, BAR)


def validate(scene):
    errs = need(scene, ["rows"])
    rows = scene.get("rows") or []
    if not 2 <= len(rows) <= 5:
        errs.append("bars take 2 to 5 rows (got %d)" % len(rows))
    for i, r in enumerate(rows):
        if not r.get("label"):
            errs.append("row %d has no label" % i)
        v = r.get("value")
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0:
            errs.append("row %d value %r must be a number >= 0" % (i, v))
        if r.get("at") is None:
            errs.append("row %d has no at" % i)
    if rows and not errs and max(r["value"] for r in rows) <= 0:
        errs.append("at least one value must be above 0")
    return errs


def _text(r):
    return str(r.get("text", r["value"]))


def height(scene, width):
    h = 0
    for r in scene["rows"]:
        label_w = width - E.text_width(_text(r), L_SIZE) - T_GAP
        h += line_px(L_SIZE, L_LH) * E.text_lines(r["label"], L_SIZE, max(1, label_w)) + B_GAP + BAR
    return h + ROW_GAP * (len(scene["rows"]) - 1)


def min_width(scene):
    return max(widest([(r["label"], L_SIZE)]) + int(E.text_width(_text(r), L_SIZE)) + T_GAP for r in scene["rows"])


def render(scene, ctx, box):
    c = ctx.c
    width = box[2]
    top = max(r["value"] for r in scene["rows"])
    track, rest = c["track"], c["line"]
    html, js = [], []
    for i, r in enumerate(scene["rows"]):
        t, attrs = ctx.item(r["at"])
        fill = c["accent"] if r.get("hi") else rest
        w = int(round(width * r["value"] / top))
        html.append('<div class="b-row" id="%s-r%d"%s><div class="b-head" style="color:%s"><span>%s</span><span class="b-text">%s</span></div>'
                    '<div class="b-track" style="background:%s"><div class="b-fill" style="width:%dpx;background:%s"></div></div></div>'
                    % (ctx.id, i, attrs, ctx.ink, ctx.esc(r["label"]), ctx.esc(_text(r)), track, w, fill))
        js.append(ctx.enter("#%s-r%d" % (ctx.id, i), t, {"y": 20}))
        js.append(ctx.enter("#%s-r%d .b-fill" % (ctx.id, i), t + 0.08, {"scaleX": 0}, to={"scaleX": 1}, dur=0.6))
    return "".join(html), js
