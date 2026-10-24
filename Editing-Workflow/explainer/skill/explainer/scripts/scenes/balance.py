"""balance: a scale weighs two sides; a weight drops into each pan on its word, and the beam tips toward the side that
wins on another (cost against value, risk against return, "does the deal make sense?").

  {"type": "balance", "left": {"label": "COST", "at": "word:6"}, "right": {"label": "VALUE", "at": "word:8"},
   "tip": {"to": "right", "at": "word:11"}, "note": {"text": "WORTH IT", "at": "word:13"}}

`tip` (optional) sends one side down; without it the scale stays level. `note` is a short line above the beam. Drawn in
2.5D (an elliptical base and pans, a beam on a pivot); the pans hang straight while the beam turns: the tip is a rotation
and two moves tweened on the timeline (seek-safe). The words sit flat on chips under the pans for gate E5.
"""
import math
import explainer_lib as E
from scenes import need

TYPE = "balance"
ASPECT = 0.85
PIVOT, FOOT = 0.3, 0.86              # the pivot's and the base's heights (shares of the scene's height)
BEAM, PAN, HANG = 0.74, 0.26, 0.24   # the beam's length, a pan's width (shares of the width), the strings' drop (of the height)
TILT = 8                             # the tip (degrees)
L_SIZE, N_SIZE, MAX_LABEL, MAX_NOTE = 34, 32, 12, 24

CSS = """
  .bl { position:relative; width:100%%; opacity:0; }
  .bl > div, .bl-pan > div, .bl-pan svg { position:absolute; }
  .bl-pan { position:absolute; width:0; height:0; }
  .bl-w { opacity:0; border-radius:10px; }
  .bl-chip { white-space:nowrap; border-radius:12px; padding:6px 16px; font-weight:700; font-size:%dpx; transform:translateX(-50%%); opacity:0; }
  .bl-note { left:0; width:100%%; text-align:center; font-family: var(--label); font-weight:500; font-size:%dpx; letter-spacing:.08em;
    white-space:nowrap; opacity:0; }
""" % (L_SIZE, N_SIZE)


def _side(scene, key, errs):
    s = scene.get(key)
    if not isinstance(s, dict) or not s.get("label") or s.get("at") is None:
        errs.append("%s is {label, at}" % key)
    elif len(str(s["label"])) > MAX_LABEL:
        errs.append("%s label %r: at most %d characters" % (key, s["label"], MAX_LABEL))


def validate(scene):
    errs = []
    _side(scene, "left", errs)
    _side(scene, "right", errs)
    tip = scene.get("tip")
    if tip is not None and (not isinstance(tip, dict) or tip.get("to") not in ("left", "right") or tip.get("at") is None):
        errs.append("tip is {to: left or right, at}")
    note = scene.get("note")
    if note is not None and (not isinstance(note, dict) or not 0 < len(str(note.get("text") or "")) <= MAX_NOTE or note.get("at") is None):
        errs.append("note is {text (1 to %d characters), at}" % MAX_NOTE)
    return errs


def height(scene, width):
    return int(math.ceil(width * ASPECT))


def min_width(scene):
    return 600


def _pan(sid, side, x, y, P, S, metal, weight, chip, chip_on, label, attrs, ctx):
    rim, bowl = P * 0.22, P * 0.2
    lines = ('<svg width="%.0f" height="%.0f" style="left:%.1fpx;top:0;overflow:visible"><path d="M%.1f 0 L0 %.1f M%.1f 0 L%.1f %.1f" '
             'stroke="%s" stroke-width="4" fill="none"/></svg>' % (P, S, -P / 2, P / 2, S, P / 2, P, S, metal))
    return ('<div class="bl-pan" id="%s-p%s" style="left:%.1fpx;top:%.1fpx">%s'
            '<div class="bl-w" id="%s-w%s" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;background:%s"></div>'
            '<div style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:0 0 50%% 50%%;background:%s;filter:brightness(.7)"></div>'
            '<div style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:50%%;background:%s"></div>'
            '<div class="bl-chip" id="%s-c%s"%s style="left:0;top:%.1fpx;background:%s;color:%s">%s</div></div>'
            % (sid, side, x, y, lines, sid, side, -P * 0.21, S - P * 0.36 + rim * 0.2, P * 0.42, P * 0.36, weight,
               -P / 2, S + rim / 2, P, bowl, metal, -P / 2, S, P, rim, metal,
               sid, side, attrs, S + rim / 2 + bowl + 20, chip, chip_on, ctx.esc(label)))


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    cx, py, fy = Wd / 2.0, H * PIVOT, H * FOOT
    B, P, S = Wd * BEAM, Wd * PAN, H * HANG
    arm = B / 2.0 - P * 0.08
    metal = c["ink"]
    series = c["series"]
    sides, js = {}, [ctx.enter("#%s-bl" % sid, ctx.t_in, {"y": 30})]
    for side, key, k in (("l", "left", 1), ("r", "right", 2)):
        s = scene[key]
        t, attrs = ctx.item(s["at"])
        fill, on = series[k % len(series)]
        sides[side] = _pan(sid, side, cx + (-arm if side == "l" else arm), py, P, S, metal, fill, fill, on, s["label"], attrs, ctx)
        js.append("tl.fromTo('#%s-w%s', { opacity: 0, y: -220 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.in', immediateRender: false }, %.3f);"
                  % (sid, side, t))
        js.append(ctx.enter("#%s-c%s" % (sid, side), t + 0.35, {"y": 12}))
    marks = ""
    tip = scene.get("tip")
    if tip:
        t, attrs = ctx.item(tip["at"])
        marks += '<i%s></i>' % attrs
        a = TILT if tip["to"] == "right" else -TILT
        d = round(arm * math.sin(math.radians(abs(a))), 1)
        ease = "power3.inOut"
        js.append("tl.to('#%s-beam', { rotation: %d, duration: 0.9, ease: '%s' }, %.3f);" % (sid, a, ease, t))
        js.append("tl.to('#%s-pl', { y: %.1f, duration: 0.9, ease: '%s' }, %.3f);" % (sid, d if a < 0 else -d, ease, t))
        js.append("tl.to('#%s-pr', { y: %.1f, duration: 0.9, ease: '%s' }, %.3f);" % (sid, -d if a < 0 else d, ease, t))
    note = ""
    if scene.get("note"):
        t, attrs = ctx.item(scene["note"]["at"])
        note = '<div class="bl-note" id="%s-n"%s style="top:%.1fpx;color:%s">%s</div>' % (sid, attrs, H * 0.04, c["dim"], ctx.esc(scene["note"]["text"]))
        js.append(ctx.enter("#%s-n" % sid, t, {"y": 12}))
    base_w, base_h = Wd * 0.34, Wd * 0.07
    stand = ('<div style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:50%%;background:%s;filter:brightness(.7)"></div>'
             '<div style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:50%%;background:%s"></div>'
             '<div style="left:%.1fpx;top:%.1fpx;width:18px;height:%.1fpx;border-radius:9px;background:%s"></div>'
             % (cx - base_w / 2, fy - base_h / 2 + 14, base_w, base_h, metal, cx - base_w / 2, fy - base_h / 2, base_w, base_h, metal,
                cx - 9, py, fy - py, metal))
    beam = ('<div id="%s-beam" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:16px;border-radius:8px;background:%s"></div>'
            '<div style="left:%.1fpx;top:%.1fpx;width:36px;height:36px;border-radius:50%%;background:%s"></div>'
            % (sid, cx - B / 2, py - 8, B, c["fill"], cx - 18, py - 18, metal))
    html = ('<div class="bl" id="%s-bl" style="aspect-ratio:1 / %s">%s%s%s%s%s%s</div>'
            % (sid, ASPECT, stand, sides["l"], sides["r"], beam, note, marks))
    ctx.idle("#%s-bl" % sid, ctx.t_in + 0.8, ctx.t_out - E.EXIT - 0.2, {"y": -6}, every=2.6)
    return html, js
