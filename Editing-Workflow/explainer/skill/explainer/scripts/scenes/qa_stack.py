"""qa-stack: questions stack up on their words, key terms in the highlight box (SPEC §6.2)."""
import re
import explainer_lib as E
from scenes import line_px, need, widest

TYPE = "qa-stack"
SIZE, LH = 48, 1.2             # question text, DM Sans 700
PAD_Y, PAD_X, GAP = 22, 30, 18
MAX = 5

CSS = """
  .q-item { width:100%%; border-radius:22px; padding:%dpx %dpx; font-weight:700; font-size:%dpx; line-height:%dpx; opacity:0; }
  .q-item + .q-item { margin-top:%dpx; }
  .q-em { padding:0 .12em; border-radius:6px; }
""" % (PAD_Y, PAD_X, SIZE, line_px(SIZE, LH), GAP)


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items") or []
    if not 1 <= len(items) <= MAX:
        errs.append("a qa-stack holds 1 to at most %d items (got %d)" % (MAX, len(items)))
    errs += ["item %d has no text" % i for i, it in enumerate(items) if not it.get("text")]
    errs += ["item %d has no at" % i for i, it in enumerate(items) if it.get("at") is None]
    return errs


def height(scene, width):
    rows = [2 * PAD_Y + line_px(SIZE, LH) * E.text_lines(it["text"], SIZE, width - 2 * PAD_X) for it in scene["items"]]
    return sum(rows) + GAP * (len(rows) - 1)


def min_width(scene):
    return widest([(it["text"], SIZE) for it in scene["items"]], pad=2 * PAD_X)


def render(scene, ctx, box):
    hl = ctx.tokens["highlight"]
    face = "background:#FFFFFF;box-shadow:0 14px 40px rgba(11,12,16,.12)" if ctx.light else "background:rgba(255,255,255,.10)"
    html, js = [], []
    for i, it in enumerate(scene["items"]):
        t, attrs = ctx.item(it["at"])
        em = {E.L.norm(e) for e in it.get("em", [])}
        words = []
        for w in it["text"].split():
            core = E.L.clean_word(w).rstrip("?!")
            if core and E.L.norm(core) in em:
                words.append('<span class="q-em" style="background:%s;color:%s">%s</span>%s'
                             % (hl["fill"], hl["text"], ctx.esc(core), ctx.esc(w[len(core):])))
            else:
                words.append(ctx.esc(w))
        html.append('<div class="q-item" id="%s-q%d"%s style="%s;color:%s">%s</div>' % (ctx.id, i, attrs, face, ctx.ink, " ".join(words)))
        js.append(ctx.enter("#%s-q%d" % (ctx.id, i), t, {"y": 30}))
    return "".join(html), js
