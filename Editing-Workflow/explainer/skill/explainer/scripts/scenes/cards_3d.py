"""cards-3d: up to four thick cards standing at an angle, each dropping in on its word ("1, 2, 3", "A, B", the steps).

  {"type": "cards-3d", "cards": [{"text": "1", "at": "word:6"}, {"text": "2", "at": "word:8"}, {"text": "3", "sub": "the core", "at": "word:10"}]}

`text` is the card's big mark (a number or up to 3 characters, in the look's hero face), `sub` a short line under it.
CSS 3D: a face and two shaded edges per card, the row turned toward the viewer; each card falls in on its word with a
small spin (a tween on the timeline, seek-safe), then the row floats.
"""
import explainer_lib as E
from scenes import need

TYPE = "cards-3d"
DECOR_KEYS = ("text",)        # a card's mark is a step (1, 2, 3), not a claim: a figure ($, %) is refused below
HERO_CSS = ".c3-n"
ASPECT = 0.62
DEPTH = 26                    # a card's thickness
TURN = (8, -20)               # the row's tilt and turn (degrees)
N_SIZE, S_SIZE = 150, 34      # the mark (hero face) and the line under a card (DM Sans 700)
MAX_SUB = 16

CSS = """
  .c3 { position:relative; width:100%%; perspective:2200px; }
  .c3-row { position:absolute; left:0; top:0; width:100%%; height:100%%; transform-style:preserve-3d; }
  .c3-card { position:absolute; transform-style:preserve-3d; opacity:0; }
  .c3-face { position:absolute; left:0; top:0; width:100%%; height:100%%; border-radius:26px; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:22px; }
  .c3-n { font-weight:700; line-height:1; }
  .c3-lines i { display:block; height:12px; border-radius:6px; margin:10px auto 0; opacity:.75; }
  .c3-edge { position:absolute; border-radius:10px; }
  .c3-r { top:6px; height:calc(100%% - 12px); width:%dpx; left:calc(100%% - 2px); transform-origin:left; transform:rotateY(90deg); filter:brightness(.72); }
  .c3-b { left:6px; width:calc(100%% - 12px); height:%dpx; top:calc(100%% - 2px); transform-origin:top; transform:rotateX(-90deg); filter:brightness(.58); }
  .c3-sub { position:absolute; left:0; width:100%%; text-align:center; font-weight:700; line-height:1.15; opacity:0; }
""" % (DEPTH, DEPTH)


def validate(scene):
    errs = need(scene, ["cards"])
    cards = scene.get("cards") or []
    if not 1 <= len(cards) <= 4:
        errs.append("cards-3d takes 1 to 4 cards (got %d)" % len(cards))
    for i, cd in enumerate(cards):
        if not isinstance(cd, dict) or not str(cd.get("text", "")).strip():
            errs.append("card %d has no text" % i)
            continue
        if any(ch in str(cd["text"]) for ch in "$%€£₹"):
            errs.append("card %d text %r is a figure: show it with a stat or count-up and its source" % (i, cd["text"]))
        elif len(str(cd["text"])) > 3:
            errs.append("card %d text %r: at most 3 characters (a number or a short mark)" % (i, cd["text"]))
        if cd.get("sub") is not None and not 0 < len(str(cd["sub"])) <= MAX_SUB:
            errs.append("card %d sub: 1 to %d characters" % (i, MAX_SUB))
        if cd.get("at") is None:
            errs.append("card %d has no at" % i)
    return errs




def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    cards = scene["cards"]
    n = len(cards)
    gap = int(Wd * 0.05)
    cw = int(min((Wd * 0.9 - gap * (n - 1)) / n, Wd * 0.34))
    ch = int(min(cw * 1.38, H - 2 * S_SIZE - 60))
    x0 = (Wd - (cw * n + gap * (n - 1))) / 2.0
    y0 = (H - ch) / 2.0 - S_SIZE
    big = int(min(N_SIZE, cw * 0.48))                 # the mark fits its card
    small = S_SIZE if n < 4 else 28                   # four cards: the line under each one takes the smallest size
    html, js = [], []
    for i, cd in enumerate(cards):
        t, attrs = ctx.item(cd["at"])
        fill, on = c["series"][i % len(c["series"])]
        lines = "".join('<i style="width:%dpx;background:%s"></i>' % (int(cw * w), on) for w in (0.55, 0.42, 0.3))
        sub = ('<div class="c3-sub" id="%s-s%d" style="top:%dpx;font-size:%dpx;color:%s">%s</div>' % (sid, i, ch + 30, small, ctx.ink, ctx.esc(cd["sub"]))
               if cd.get("sub") else "")
        html.append('<div class="c3-card" id="%s-c%d"%s style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">'
                    '<div class="c3-edge c3-r" style="background:%s"></div><div class="c3-edge c3-b" style="background:%s"></div>'
                    '<div class="c3-face" style="background:%s;color:%s"><div class="c3-n" style="font-size:%dpx">%s</div><div class="c3-lines">%s</div></div>%s</div>'
                    % (sid, i, attrs, x0 + i * (cw + gap), y0, cw, ch, fill, fill, fill, on, big, ctx.esc(cd["text"]), lines, sub))
        js.append("tl.fromTo('#%s-c%d', { opacity: 0, y: -320, rotation: %d }, { opacity: 1, y: 0, rotation: 0, duration: 0.6, ease: '%s', "
                  "immediateRender: false }, %.3f);" % (sid, i, -10 if i % 2 else 8, ctx.tokens["motion"]["enter_ease"], t))
        if cd.get("sub"):
            js.append(ctx.enter("#%s-s%d" % (sid, i), t + 0.35, {"y": 12}))
    out = ('<div class="c3" id="%s-3d" style="aspect-ratio:1 / %s"><div class="c3-row" style="transform:rotateX(%ddeg) rotateY(%ddeg)">%s</div></div>'
           % (sid, ASPECT, TURN[0], TURN[1], "".join(html)))
    last = max(ctx.at(cd["at"]) for cd in cards)
    ctx.idle("#%s-3d" % sid, last + 0.8, ctx.t_out - E.EXIT - 0.2, {"y": -10}, every=2.4)
    return out, js
