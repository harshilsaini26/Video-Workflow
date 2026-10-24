"""outputs: what a model answered against what was right, one row per answer: its guess as a bar, the right answer
outlined, the error of each row as a bar under it, and the loss as a square ("it says 8; it should say 3; square the
gaps, add them up").

  {"type": "outputs", "labels": ["0", ..., "9"], "guess": [0.1, ..., 0.6, 0.25], "at": "word:5",
   "target": {"row": 3, "at": "word:7"}, "error": "word:9", "loss": "word:12"}

2 to 10 rows; each guess 0 to 1. The truth is 1 on the target row and 0 elsewhere; a row's error bar is its gap to the
truth, and the loss square's area is the sum of the squared gaps. Bars grow from the left with tweens on the timeline
(seek-safe). `target`, `error` and `loss` are optional, in that order.
"""
import math
from scenes import need

TYPE = "outputs"
DECOR_KEYS = ("labels", "guess", "target", "error", "loss")   # a model's outputs, drawn to explain: not a claim
ROW, GUESS_H, ERR_H, LABEL_W = 46, 18, 12, 60
L_SIZE, MAX_LABEL = 30, 3
LOSS_MAX, LOSS_GAP = 200, 30

CSS = """
  .op { position:relative; width:100%%; }
  .op-row { position:relative; height:%dpx; }
  .op-label { position:absolute; left:0; top:2px; width:%dpx; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:1; }
  .op-track { position:absolute; left:%dpx; right:0; top:4px; height:%dpx; }
  .op-guess, .op-err { position:absolute; left:0; transform-origin:0 50%%; }
  .op-target { position:absolute; left:%dpx; right:0; opacity:0; border-radius:4px; }
  .op-loss { position:absolute; left:%dpx; transform-origin:0 0; }
  .op-loss-l { position:absolute; font-family: var(--label); font-weight:500; font-size:%dpx; letter-spacing:.1em; opacity:0; }
""" % (ROW, LABEL_W, L_SIZE, LABEL_W, GUESS_H + 4 + ERR_H, LABEL_W, LABEL_W, L_SIZE)


def validate(scene):
    errs = need(scene, ["labels", "guess", "at"])
    labels, guess = scene.get("labels") or [], scene.get("guess") or []
    if not 2 <= len(labels) <= 10 or any(not 0 < len(str(x)) <= MAX_LABEL for x in labels):
        errs.append("outputs take 2 to 10 labels of 1 to %d characters" % MAX_LABEL)
    if len(guess) != len(labels):
        errs.append("one guess per label (%d labels, %d guesses)" % (len(labels), len(guess)))
    elif any(not isinstance(g, (int, float)) or isinstance(g, bool) or not 0 <= g <= 1 for g in guess):
        errs.append("each guess is 0 to 1")
    tg = scene.get("target")
    if tg is not None and (not isinstance(tg, dict) or not isinstance(tg.get("row"), int) or not 0 <= tg["row"] < len(labels) or tg.get("at") is None):
        errs.append("target row: {row (0 to %d), at}" % (len(labels) - 1))
    if (scene.get("error") is not None or scene.get("loss") is not None) and tg is None:
        errs.append("error and loss need a target (the right answer)")
    return errs


def height(scene, width):
    return ROW * len(scene["labels"]) + (LOSS_GAP + LOSS_MAX if scene.get("loss") is not None else 0)


def min_width(scene):
    return 480


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    labels, guess = scene["labels"], [float(g) for g in scene["guess"]]
    tg = scene.get("target")
    truth = [1.0 if tg and i == tg["row"] else 0.0 for i in range(len(labels))]
    ease = ctx.tokens["motion"]["enter_ease"]
    t, attrs = ctx.item(scene["at"])
    marks, js = ["<i%s></i>" % attrs], [ctx.enter("#%s-op .op-label" % sid, ctx.t_in, {"x": -10}, stagger=0.4)]
    rows = []
    for i, (lab, g) in enumerate(zip(labels, guess)):
        hot = tg and i == tg["row"]
        rows.append('<div class="op-row"><div class="op-label" style="color:%s">%s</div><div class="op-track">'
                    '<div class="op-guess" id="%s-g%d" style="width:%.2f%%;top:0;height:%dpx;background:%s"></div>'
                    '<div class="op-err" id="%s-e%d" style="width:%.2f%%;top:%dpx;height:%dpx;background:%s;transform:scaleX(0)"></div></div></div>'
                    % (c["ink"] if hot else c["dim"], ctx.esc(lab), sid, i, round(g * 100, 2), GUESS_H, c["accent"],
                       sid, i, round(abs(truth[i] - g) * 100, 2), GUESS_H + 4, ERR_H, c["bad"]))
        js.append("tl.fromTo('#%s-g%d', { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: '%s', immediateRender: false }, %.3f);" % (sid, i, ease, t + 0.04 * i))
    js.insert(1, "tl.set('#%s-op .op-guess', { scaleX: 0 }, 0);" % sid)
    extra = ""
    if tg:
        tt, attrs = ctx.item(tg["at"])
        marks.append("<i%s></i>" % attrs)
        extra += ('<div class="op-target" id="%s-target" style="top:%dpx;height:%dpx;box-shadow:inset 0 0 0 4px %s"></div>'
                  % (sid, tg["row"] * ROW, GUESS_H + 8, c["good"]))
        js.append(ctx.enter("#%s-target" % sid, tt, {"scale": 1.08}))
    if scene.get("error") is not None:
        te, attrs = ctx.item(scene["error"])
        marks.append("<i%s></i>" % attrs)
        js += ["tl.fromTo('#%s-e%d', { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: '%s', immediateRender: false }, %.3f);" % (sid, i, ease, te + 0.04 * i)
               for i in range(len(labels))]
    if scene.get("loss") is not None:
        tl_, attrs = ctx.item(scene["loss"])
        marks.append("<i%s></i>" % attrs)
        loss = sum((a - b) ** 2 for a, b in zip(truth, guess))
        side = LOSS_MAX * min(1.0, math.sqrt(loss / 2.0))
        top = ROW * len(labels) + LOSS_GAP
        extra += ('<div class="op-loss" id="%s-loss" data-loss="%.4f" style="top:%dpx;width:%.1fpx;height:%.1fpx;background:%s;transform:scale(0)"></div>'
                  '<div class="op-loss-l" id="%s-ll" style="left:%.1fpx;top:%.1fpx;color:%s">LOSS</div>'
                  % (sid, loss, top, side, side, c["bad"], sid, LABEL_W + side + 24, top + side / 2.0 - L_SIZE / 2.0, c["dim"]))
        js.append("tl.fromTo('#%s-loss', { scale: 0 }, { scale: 1, duration: 0.7, ease: '%s', immediateRender: false }, %.3f);" % (sid, ease, tl_))
        js.append(ctx.enter("#%s-ll" % sid, tl_ + 0.4, {"x": -10}))
    return ('<div class="op" id="%s-op" style="height:%dpx">%s%s%s</div>' % (sid, height(scene, box[2]), "".join(rows), extra, "".join(marks))), js
