"""coin: a thick coin spins in on its word and lands face on, a short mark on its face and a line under it (EPS, ROI,
"does it pay?").

  {"type": "coin", "text": "EPS", "dir": "up", "sub": "earnings per share", "at": "word:6"}

`text` is up to 4 characters (the look's hero face), never a figure; `dir` (up or down) adds an arrow above it; `sub`
is a short line under the coin. CSS 3D: two faces and a rim of thin strips; the spin is a rotation tweened on the
timeline (seek-safe); the line under it sits flat for gate E5.
"""
import math
import explainer_lib as E
from scenes import need

TYPE = "coin"
DECOR_KEYS = ("text",)          # a coin's mark is a name (EPS), not a figure: $ and % are refused below
HERO_CSS = ".cn-text"
ASPECT = 0.75
R, THICK, STRIPS = 0.27, 0.05, 36     # the radius and thickness (shares of the width), the rim's strips
SPIN = -720
T_SIZE, S_SIZE, MAX_SUB = 120, 36, 22

CSS = """
  .cn { position:relative; width:100%%; perspective:2400px; }
  .cn-coin { position:absolute; transform-style:preserve-3d; opacity:0; }
  .cn-face { position:absolute; left:0; top:0; width:100%%; height:100%%; border-radius:50%%; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:10px; backface-visibility:hidden; }
  .cn-edge { position:absolute; left:50%%; top:50%%; }
  .cn-text { font-weight:700; line-height:1; }
  .cn-arrow { width:0; height:0; border-left:26px solid transparent; border-right:26px solid transparent; }
  .cn-sub { position:absolute; left:0; width:100%%; text-align:center; font-weight:700; font-size:%dpx; white-space:nowrap; opacity:0; }
""" % S_SIZE


def validate(scene):
    errs = need(scene, ["text", "at"])
    t = str(scene.get("text") or "")
    if scene.get("text") is not None:
        if any(ch in t for ch in "$%€£₹"):
            errs.append("text %r is a figure: show it with a stat or count-up and its source" % t)
        elif not 0 < len(t) <= 4:
            errs.append("text %r: at most 4 characters (a short mark, like EPS)" % t)
    if scene.get("dir") is not None and scene["dir"] not in ("up", "down"):
        errs.append("dir is up or down (got %r)" % scene["dir"])
    if scene.get("sub") is not None and not 0 < len(str(scene["sub"])) <= MAX_SUB:
        errs.append("sub: 1 to %d characters" % MAX_SUB)
    return errs


def height(scene, width):
    return int(math.ceil(width * ASPECT))


def min_width(scene):
    return 600


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    r, T = Wd * R, Wd * THICK
    fill, on = c["fill"], c["on_fill"]
    cx, cy = Wd / 2.0, H * 0.42
    size = int(min(T_SIZE, r * 1.5 / max(1e-6, E.text_width(str(scene["text"]), 1, E.hero()["glyphs"]))))
    arrow = ""
    if scene.get("dir"):
        side = "border-bottom" if scene["dir"] == "up" else "border-top"
        arrow = '<div class="cn-arrow" style="%s:40px solid %s"></div>' % (side, on)
    face = '%s<div class="cn-text" style="font-size:%dpx">%s</div>' % (arrow, size, ctx.esc(scene["text"]))
    seg = 2 * math.pi * r / STRIPS + 1.5
    edges = "".join('<div class="cn-edge" style="width:%.1fpx;height:%.1fpx;margin:%.1fpx 0 0 %.1fpx;background:%s;filter:brightness(%.2f);'
                    'transform:rotateZ(%.2fdeg) translateY(%.1fpx) rotateX(90deg)"></div>'
                    % (seg, T, -T / 2, -seg / 2, fill, 0.62 + 0.18 * abs(math.cos(math.radians(k * 360.0 / STRIPS))), k * 360.0 / STRIPS, -r)
                    for k in range(STRIPS))
    t, attrs = ctx.item(scene["at"])
    html = ('<div class="cn" id="%s-cn" style="aspect-ratio:1 / %s"><div class="cn-coin" id="%s-coin"%s style="left:%.1fpx;top:%.1fpx;width:%.1fpx;'
            'height:%.1fpx">%s<div class="cn-face" style="background:%s;color:%s;transform:translateZ(%.1fpx)">%s</div>'
            '<div class="cn-face" style="background:%s;transform:rotateY(180deg) translateZ(%.1fpx)"></div></div>'
            % (sid, ASPECT, sid, attrs, cx - r, cy - r, 2 * r, 2 * r, edges, fill, on, T / 2, face, fill, T / 2))
    js = ["tl.fromTo('#%s-coin', { opacity: 0, y: -260, rotationY: %d }, { opacity: 1, y: 0, rotationY: 0, duration: 1.1, ease: '%s', "
          "immediateRender: false }, %.3f);" % (sid, SPIN, ctx.tokens["motion"]["enter_ease"], t)]
    if scene.get("sub"):
        html += '<div class="cn-sub" id="%s-sub" style="top:%.1fpx;color:%s">%s</div>' % (sid, cy + r + 44, ctx.ink, ctx.esc(scene["sub"]))
        js.append(ctx.enter("#%s-sub" % sid, t + 0.7, {"y": 14}))
    html += "</div>"
    ctx.idle("#%s-coin" % sid, t + 1.4, ctx.t_out - E.EXIT - 0.2, {"y": -10}, every=2.4)
    return html, js
