"""video-card: a video player on light paper, a thumbnail with a play button, a progress bar and a timecode, the
video's title and its channel under it. On the play word the button turns to pause and the video plays: the bar and
the timecode run (in real time) and the picture drifts slowly in while the card holds. For "this video",
"I hit play on the tutorial":

  {"type": "video-card", "src": "thumb.jpg", "title": "Colour grading in ten minutes", "channel": "Studio Notes",
   "meta": "1.2M views", "duration": "10:24", "start": "0:00", "play": {"at": "word:6"}}

`duration` and `start` are m:ss; `meta` is an optional line under the channel. `src` (a PNG or JPG next to
storyboard.json) is optional: without it the thumbnail is a built-in picture. The timecode, the duration and the meta
line are the mock-up's furniture (DECOR_KEYS); a number in the title still needs a source.
"""
import math
import explainer_lib as E
from scenes import js_obj, line_px, need, widest
from scenes import _vg

TYPE = "video-card"
DECOR_KEYS = {"duration", "start", "meta"}
TH, RADIUS = 330, 30                     # the thumbnail, the card's corners
BTN = 112                                # the play button
BAR_H, KNOB = 8, 20                      # the progress bar along the thumbnail's foot, its scrubber
TC_SIZE, TC_H, TC_PAD, TC_IN = 28, 42, 12, 16   # the timecode chip: JetBrains Mono 500
PAD_X, PAD_T, PAD_B = 28, 22, 26         # the info under the thumbnail
T_SIZE, T_LINE = 36, 44                  # title, DM Sans 700
ROW_GAP, AV = 16, 56                     # title to channel row, the avatar
C_SIZE, C_LINE, M_SIZE, M_LINE = 30, 36, 28, 34   # channel (DM Sans 500), meta (DM Sans 500)
AV_GAP = 16

CSS = """
  .vc { position:relative; width:100%%; border-radius:%dpx; overflow:hidden; opacity:0; }
  .vc-th { position:relative; width:100%%; height:%dpx; overflow:hidden; }
  .vc-pic { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .vc-btn { position:absolute; left:50%%; top:50%%; width:%dpx; height:%dpx; margin:-%dpx 0 0 -%dpx; border-radius:50%%; }
  .vc-btn svg { position:absolute; left:30%%; top:30%%; width:40%%; height:40%%; }
  .vc-btn .vc-pa { opacity:0; }
  .vc-track { position:absolute; left:0; bottom:0; width:100%%; height:%dpx; }
  .vc-fill { position:absolute; left:0; top:0; height:100%%; }
  .vc-knob { position:absolute; top:-%dpx; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:50%%; }
  .vc-tc { position:absolute; right:%dpx; bottom:%dpx; height:%dpx; padding:0 %dpx; border-radius:10px; display:flex;
    align-items:center; font-family: var(--label); font-weight:500; font-size:%dpx; white-space:nowrap;
    font-variant-numeric: tabular-nums; }
  .vc-tc b { font-weight:500; display:inline-block; text-align:right; }
  .vc-info { padding:%dpx %dpx %dpx; }
  .vc-t { font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:-.01em; }
  .vc-row { display:flex; align-items:center; gap:%dpx; margin-top:%dpx; }
  .vc-av { flex:none; width:%dpx; height:%dpx; border-radius:50%%; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:%dpx; line-height:1; }
  .vc-ch { font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .vc-m { font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
""" % (RADIUS, TH, BTN, BTN, BTN // 2, BTN // 2, BAR_H, (KNOB - BAR_H) // 2, KNOB, KNOB, KNOB // 2, TC_IN, BAR_H + TC_IN - 4,
       TC_H, TC_PAD, TC_SIZE, PAD_T, PAD_X, PAD_B, T_SIZE, T_LINE, AV_GAP, ROW_GAP, AV, AV, C_SIZE, C_SIZE, C_LINE, M_SIZE,
       M_LINE) + _vg.CSS


def validate(scene):
    errs = need(scene, ["title", "channel", "duration", "play"])
    d = _vg.parse_clock(scene.get("duration"))
    if scene.get("duration") is not None and not d:
        errs.append("duration is m:ss, more than 0:00 (got %r)" % scene.get("duration"))
    if scene.get("start") is not None:
        s = _vg.parse_clock(scene["start"])
        if s is None or (d and s >= d):
            errs.append("start is m:ss, before the duration (got %r)" % scene.get("start"))
    pl = scene.get("play")
    if pl is not None and (not isinstance(pl, dict) or pl.get("at") is None):
        errs.append("play needs at (the word that starts the video)")
    if scene.get("meta") is not None and not str(scene["meta"]).strip():
        errs.append("meta is empty")
    e = _vg.check_src(scene.get("src"))
    return errs + ([e] if e else [])


def _row_h(scene):
    return max(AV, C_LINE + (M_LINE if scene.get("meta") else 0))


def height(scene, width):
    lines = E.text_lines(scene["title"], T_SIZE, width - 2 * PAD_X, spacing=-0.01)
    return TH + PAD_T + lines * T_LINE + ROW_GAP + _row_h(scene) + PAD_B


def _tc_parts(scene):
    d = _vg.parse_clock(scene["duration"])
    w = max(E.text_width(_vg.clock(v), TC_SIZE, "mono500") for v in list(range(0, d + 1, max(1, d // 50))) + [d])
    return d, int(math.ceil(w)) + 1


def _tc_w(scene):
    d, w = _tc_parts(scene)
    return w + int(math.ceil(E.text_width(" / " + _vg.clock(d), TC_SIZE, "mono500"))) + 2 * TC_PAD


def min_width(scene):
    words = widest([(scene["title"], T_SIZE)], 2 * PAD_X + 1)
    row = 2 * PAD_X + AV + AV_GAP + int(math.ceil(max(E.text_width(scene["channel"], C_SIZE, "display500"),
                                                       E.text_width(scene.get("meta") or "", M_SIZE, "display500")))) + 1
    return max(words, row, _tc_w(scene) + 2 * TC_IN + BTN)


def render(scene, ctx, box):
    pc, sid, W = ctx.pc, ctx.id, box[2]
    mo = ctx.tokens["motion"]
    d, tcw = _tc_parts(scene)
    s0 = _vg.parse_clock(scene.get("start") or "0:00")
    tp, attrs = ctx.item(scene["play"]["at"])
    hold = max(0.0, ctx.t_out - (tp + 0.2))
    s1 = min(float(d), s0 + hold)
    pct = lambda v: "%s%%" % _vg._num(round(100.0 * v / d, 2))
    letter = ctx.esc(str(scene["channel"]).strip()[:1].upper())
    btn = ('<div class="vc-btn" id="%s-btn"%s style="background:%s;color:%s;box-shadow:0 10px 28px %s">%s%s</div>'
           % (sid, attrs, E.rgba(pc["card"], 0.94), pc["ink"], E.rgba(pc["ink"], 0.25),
              _vg.glyph("play", "vc-pl", fill=True).replace("<svg ", '<svg id="%s-pl" ' % sid, 1),
              _vg.glyph("pause", "vc-pa", fill=True).replace("<svg ", '<svg id="%s-pa" ' % sid, 1)))
    bar = ('<div class="vc-track" style="background:%s"><i class="vc-fill" id="%s-f" style="width:%s;background:%s"></i>'
           '<i class="vc-knob" id="%s-k" style="left:%s;background:%s;box-shadow:inset 0 0 0 4px %s"></i></div>'
           % (E.rgba(pc["card"], 0.55), sid, pct(s0), pc["accent"], sid, pct(s0), pc["accent"], pc["card"]))
    tc = ('<div class="vc-tc" style="background:%s;color:%s"><b id="%s-tc" style="width:%dpx">%s</b>&nbsp;/ %s</div>'
          % (pc["ink"], pc["card"], sid, tcw, _vg.clock(s0), _vg.clock(d)))
    meta = '<div class="vc-m" style="color:%s">%s</div>' % (pc["dim"], ctx.esc(scene["meta"])) if scene.get("meta") else ""
    info = ('<div class="vc-info"><div class="vc-t" style="color:%s">%s</div><div class="vc-row" style="height:%dpx">'
            '<span class="vc-av" style="background:%s;color:%s">%s</span><div><div class="vc-ch" style="color:%s">%s</div>%s</div></div></div>'
            % (pc["ink"], ctx.esc(scene["title"]), _row_h(scene), pc["fill"], pc["on_fill"], letter, pc["ink"],
               ctx.esc(scene["channel"]), meta))
    # no fixed height: the card is as tall as its content, so the title wraps at whatever width it is given
    html = ('<div class="vc" id="%s-card" style="%s"><div class="vc-th" style="background:%s"><div class="vc-pic" id="%s-pic">%s</div>'
            '%s%s%s</div>%s</div>' % (sid, ctx.paper_card(), pc["chrome"], sid,
                                       _vg.picture(ctx, scene.get("src"), "p", seed=4), bar, tc, btn, info))
    js = [ctx.enter("#%s-card" % sid, ctx.t_in, {"y": 40, "scale": 0.96}),
          ctx.enter("#%s-btn" % sid, ctx.t_in + 0.2, {"scale": 0.7}),
          # on the word: a press, and play becomes pause
          _vg.tween("#%s-btn" % sid, {"scale": 1}, {"scale": 0.9, "duration": 0.12, "ease": "power2.out"}, tp),
          _vg.tween("#%s-btn" % sid, {"scale": 0.9}, {"scale": 1, "duration": 0.35, "ease": mo["enter_ease"]}, tp + 0.12),
          _vg.tween("#%s-pl" % sid, {"opacity": 1, "scale": 1}, {"opacity": 0, "scale": 0.6, "duration": 0.2, "ease": mo["exit_ease"]}, tp),
          _vg.tween("#%s-pa" % sid, {"opacity": 0, "scale": 0.6}, {"opacity": 1, "scale": 1, "duration": 0.3, "ease": mo["enter_ease"]}, tp + 0.12)]
    if hold > 0.3:   # it plays while the card holds: the bar and the timecode run in real time, the picture drifts in
        ctx.ambient(_vg.tween("#%s-f" % sid, {"width": pct(s0)}, {"width": pct(s1), "duration": round(hold, 3), "ease": "none"}, tp + 0.2))
        ctx.ambient(_vg.tween("#%s-k" % sid, {"left": pct(s0)}, {"left": pct(s1), "duration": round(hold, 3), "ease": "none"}, tp + 0.2))
        ctx.ambient(_vg.ticker("%s-tc" % sid, tp + 0.2, round(hold, 3), s0, s1, _vg.CLOCK_JS))
        ctx.ambient(_vg.tween("#%s-pic" % sid, {"scale": 1}, {"scale": 1.06, "duration": round(hold, 3), "ease": "sine.inOut"}, tp + 0.2))
    return html, js
