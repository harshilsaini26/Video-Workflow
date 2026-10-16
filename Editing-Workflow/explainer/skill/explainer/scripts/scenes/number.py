"""number: a round badge with a step number pops in, its name slides up under it (SPEC §6.2)."""
import explainer_lib as E
from scenes import line_px, need, widest

TYPE = "number"
MAX_SCALE = 1.3                  # the badge is already 200 px
BADGE, B_SIZE = 200, 112       # the badge circle and its digits
N_SIZE, N_LH, N_GAP = 72, 1.1, 32   # the name under it

CSS = """
  .n-badge { width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; line-height:1; opacity:0; flex:none; }
  .n-name { font-weight:700; font-size:%dpx; line-height:%dpx; margin-top:%dpx; text-align:center; letter-spacing:-.01em; opacity:0; }
""" % (BADGE, BADGE, B_SIZE, N_SIZE, line_px(N_SIZE, N_LH), N_GAP)


def validate(scene):
    errs = need(scene, ["n"])
    if E.text_width(str(scene.get("n", "")), B_SIZE) > BADGE - 24:
        errs.append("n %r is wider than the badge; use a 1 or 2 character step number" % (scene.get("n"),))
    return errs


def height(scene, width):
    h = BADGE
    if scene.get("name"):
        h += N_GAP + line_px(N_SIZE, N_LH) * E.text_lines(scene["name"], N_SIZE, width, spacing=-0.01)
    return h


def min_width(scene):
    return max(BADGE, widest([(scene.get("name"), N_SIZE)]))


def render(scene, ctx, box):
    badge = '<div class="n-badge" style="background:%s;color:%s">%s</div>' % (ctx.c["accent"], ctx.c["on_accent"], ctx.esc(scene["n"]))
    js = [ctx.enter("#%s .n-badge" % ctx.id, ctx.t_in, {"scale": 0.6})]
    name = ""
    if scene.get("name"):
        name = '<div class="n-name" style="color:%s">%s</div>' % (ctx.ink, ctx.esc(scene["name"]))
        js.append(ctx.enter("#%s .n-name" % ctx.id, ctx.t_in + 0.14, {"y": 30}))
    return badge + name, js
