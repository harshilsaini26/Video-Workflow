"""count-up: a number counts up from zero in full digits, with a line under it (SPEC §6.2)."""
import json
import explainer_lib as E
from scenes import js_str, line_px, need, widest

TYPE = "count-up"
MAX_SCALE = 1.3                  # the number is already 170 px
NEEDS_SOURCE = True
V_SIZE = 170                    # the number: DM Sans 700, tabular digits, line height 1
S_SIZE, S_LH, S_GAP = 52, 1.15, 20
COUNT = 1.2                     # seconds the count takes (shorter when the scene is)
MONEY = ("$", "€", "£", "₹")


CSS = """
  .c-value { font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:-.02em; font-variant-numeric: tabular-nums;
    text-align:center; white-space:nowrap; opacity:0; }
  .c-sub { font-weight:500; font-size:%dpx; line-height:%dpx; margin-top:%dpx; text-align:center; opacity:0; }
""" % (V_SIZE, V_SIZE, S_SIZE, line_px(S_SIZE, S_LH), S_GAP)


def validate(scene):
    errs = need(scene, ["value"])
    if not errs:
        try:
            float(scene["value"])
        except (TypeError, ValueError):
            errs.append("value %r is not a number" % (scene["value"],))
    if not 0 <= int(scene.get("decimals", 0)) <= 3:
        errs.append("decimals is 0 to 3")
    return errs


def height(scene, width):
    h = V_SIZE
    if scene.get("sub"):
        h += S_GAP + line_px(S_SIZE, S_LH) * E.text_lines(scene["sub"], S_SIZE, width, "display500")
    return h


def min_width(scene):
    # the widest value on the way, not only the final one: digits are proportional ($1,111,111 passes $1,000,000)
    count = E.L.count_width(float(scene["value"]), V_SIZE, scene.get("prefix", ""), scene.get("suffix", ""), int(scene.get("decimals", 0)))
    return max(int(count) + 1, widest([(scene.get("sub"), S_SIZE)]))


def render(scene, ctx, box):
    c = ctx.tokens["colors"]
    money = str(scene.get("prefix", "")) in MONEY
    col = ctx.ink if ctx.light else c["amber" if money else "cyan"]
    dec = int(scene.get("decimals", 0))
    vid = "%s-v" % ctx.id
    zero = E.L.full_digits(0, scene.get("prefix", ""), scene.get("suffix", ""), dec)
    out = '<div class="c-value" id="%s" style="color:%s">%s</div>' % (vid, col, ctx.esc(zero))
    js = [ctx.enter("#%s" % vid, ctx.t_in, {"y": 30})]
    if scene.get("sub"):
        out += '<div class="c-sub" style="color:%s">%s</div>' % (ctx.ink, ctx.esc(scene["sub"]))
        js.append(ctx.enter("#%s .c-sub" % ctx.id, ctx.t_in + 0.18, {"y": 20}))
    dur = max(0.3, min(COUNT, ctx.t_out - ctx.t_in - 0.4))
    js.append("countUp('#%s', 0, %s, %.3f, %.3f, %s, %s, %d);" % (vid, json.dumps(float(scene["value"])), ctx.t_in + 0.1, dur,
                                                              js_str(scene.get("prefix", "")), js_str(scene.get("suffix", "")), dec))
    return out, js
