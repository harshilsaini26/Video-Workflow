"""title: a headline whose words rise in, with a small mono kicker above it (SPEC §6.2)."""
import explainer_lib as E
from scenes import line_px, mono_lines, need, stagger_for, widest

TYPE = "title"
HERO = 150                       # the composer scales a title up to fill the frame, to this size at most
SIZE, LH = 104, 1.08          # headline: DM Sans 700
K_SIZE, K_LH, K_GAP = 30, 1.3, 22   # kicker: the mono label font, letter-spaced
MIN_SIZE, MAX_SIZE = 72, 132

CSS = """
  .t-kicker { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:.12em;
    text-transform:uppercase; text-align:center; margin-bottom:%dpx; opacity:0; }
  .t-text { font-weight:700; letter-spacing:-.015em; text-align:center; }
  .t-text .w { display:inline-block; opacity:0; }
""" % (K_SIZE, line_px(K_SIZE, K_LH), K_GAP)


def size(scene):
    return int(scene.get("size", SIZE))


def max_scale(scene):
    """A title grows to a hero size (120 px or more reads as a headline on a phone) and no further."""
    return max(1.0, HERO / float(size(scene)))


def validate(scene):
    errs = need(scene, ["text"])
    if not MIN_SIZE <= size(scene) <= MAX_SIZE:
        errs.append("size %d is outside %d to %d px" % (size(scene), MIN_SIZE, MAX_SIZE))
    return errs


def height(scene, width):
    h = line_px(size(scene), LH) * E.text_lines(scene["text"], size(scene), width, spacing=-0.015)
    if scene.get("kicker"):
        h += line_px(K_SIZE, K_LH) * mono_lines(scene["kicker"], K_SIZE, width) + K_GAP
    return h


def min_width(scene):
    return widest([(scene["text"], size(scene))])


def render(scene, ctx, box):
    s = size(scene)
    words = scene["text"].split()
    kick = ""
    if scene.get("kicker"):
        col = ctx.tokens["colors"]["dim_light" if ctx.light else "cyan"]
        kick = '<div class="t-kicker" style="color:%s">%s</div>' % (col, ctx.esc(scene["kicker"]))
    text = '<div class="t-text" style="font-size:%dpx;line-height:%dpx;color:%s">%s</div>' % (
        s, line_px(s, LH), ctx.ink, " ".join('<span class="w">%s</span>' % ctx.esc(w) for w in words))
    js = [ctx.enter("#%s .t-text .w" % ctx.id, ctx.t_in, {"y": 40}, stagger=stagger_for(len(words)))]
    if kick:
        js.append(ctx.enter("#%s .t-kicker" % ctx.id, ctx.t_in + 0.1))
    return kick + text, js
