"""film-look: a picture turns cinematic on one word. Letterbox bars slide in to a 2.39:1 frame, a warm grade settles
over it, a vignette closes in, film grain starts to crawl (an SVG feTurbulence whose seed steps on the timeline, so
every render is the same) and a light leak sweeps across once; a small chip in the corner turns from BEFORE to AFTER.
For "and that's the film look", "three things make it feel like cinema":

  {"type": "film-look", "src": "still.jpg", "at": "word:7", "title": "The film look"}

`before` and `after` rename the chip (one or two short words each). `src` (a PNG or JPG next to storyboard.json) is
optional: without it the frame shows a built-in landscape at dusk. `title` sits under the picture, on the ground.
"""
import math
import explainer_lib as E
from scenes import js_obj, need, widest
from scenes import _vg

TYPE = "film-look"
PIC_H, RADIUS = 320, 28                  # the picture and its corners
T_GAP, T_SIZE, T_LINE = 26, 40, 48       # the title under it: DM Sans 700
C_SIZE, C_H, C_PAD, C_IN = 28, 46, 16, 18   # the chip: JetBrains Mono 500 capitals, its height, padding, inset
WIDE = 2.39                              # the letterbox's aspect
GRAIN_FPS = 12                           # grain steps this often a second (film is 24; every other frame reads as grain)
GRADE = ("sepia(0) saturate(1) contrast(1) brightness(1) hue-rotate(0deg)",
         "sepia(0.3) saturate(1.3) contrast(1.12) brightness(0.97) hue-rotate(-6deg)")

CSS = """
  .fl-wrap { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .fl { position:relative; width:100%%; height:%dpx; border-radius:%dpx; overflow:hidden; opacity:0; }
  .fl-g, .fl-vig, .fl-grain { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .fl-vig { opacity:0; }
  .fl-grain { mix-blend-mode:overlay; opacity:0; }
  .fl-leak { position:absolute; left:0; top:-20%%; width:50%%; height:140%%; mix-blend-mode:screen; opacity:0; }
  .fl-bar { position:absolute; left:0; width:100%%; transform:scaleY(0); }
  .fl-ring { position:absolute; left:0; top:0; width:100%%; height:100%%; border-radius:%dpx; pointer-events:none; }
  .fl-chip { position:absolute; left:%dpx; top:%dpx; height:%dpx; border-radius:%dpx; overflow:hidden; }
  .fl-chip span { position:absolute; left:0; top:0; width:100%%; height:100%%; display:flex; align-items:center;
    justify-content:center; font-family: var(--label); font-weight:500; font-size:%dpx; letter-spacing:.08em; white-space:nowrap; }
  .fl-t { width:100%%; margin-top:%dpx; font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:-.01em;
    text-align:center; opacity:0; }
""" % (PIC_H, RADIUS, RADIUS, C_IN, C_IN, C_H, C_H // 2, C_SIZE, T_GAP, T_SIZE, T_LINE) + _vg.CSS


def _words(scene):
    return [str(scene.get("before") or "Before").upper(), str(scene.get("after") or "After").upper()]


def validate(scene):
    errs = need(scene, ["at"])
    for k in ("before", "after"):
        v = scene.get(k)
        if v is not None and (not str(v).strip() or len(str(v).split()) > 2 or len(str(v)) > 14):
            errs.append("%s is one or two short words, at most 14 characters (got %r)" % (k, v))
    if scene.get("title") is not None and not str(scene["title"]).strip():
        errs.append("title is empty")
    e = _vg.check_src(scene.get("src"))
    return errs + ([e] if e else [])


def _title_lines(scene, width):
    return E.text_lines(scene["title"], T_SIZE, width, spacing=-0.01) if scene.get("title") else 0


def height(scene, width):
    n = _title_lines(scene, width)
    return PIC_H + (T_GAP + n * T_LINE if n else 0)


def _chip_w(scene):
    return int(math.ceil(max(E.text_width(w, C_SIZE, "mono500", spacing=0.08) for w in _words(scene)))) + 2 * C_PAD


def min_width(scene):
    return max(_chip_w(scene) + 2 * C_IN + 120, widest([(scene.get("title"), T_SIZE)], 1))


def grain_seed(k):
    """The grain's seed at its k-th step: a fixed walk, so a render and its re-render are the same frame for frame."""
    return (k * 7919 + 13) % 997 + 1


def render(scene, ctx, box):
    pc, sid, W = ctx.pc, ctx.id, box[2]
    pal, mo = ctx.tokens["palette"], ctx.tokens["motion"]
    t, attrs = ctx.item(scene["at"])
    bar = max(18, int(round((PIC_H - W / WIDE) / 2.0)))
    before, after = _words(scene)
    leak = "linear-gradient(90deg, transparent 0%%, %s 38%%, %s 62%%, transparent 100%%)" % (E.rgba(pal["peach"], 0.6), E.rgba(pal["yellow"], 0.5))
    vig = "radial-gradient(ellipse at center, transparent 50%%, %s 100%%)" % E.rgba(pal["text"], 0.6)
    grain = ('<svg class="fl-grain" id="%s-gr" preserveAspectRatio="none"><filter id="%s-gf" x="0" y="0" width="100%%" height="100%%">'
             '<feTurbulence id="%s-turb" type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="%d" stitchTiles="stitch"/>'
             '<feColorMatrix type="saturate" values="0"/></filter><rect width="100%%" height="100%%" filter="url(#%s-gf)"/></svg>'
             % (sid, sid, sid, grain_seed(0), sid))
    chip = ('<div class="fl-chip" style="width:%dpx;background:%s"><span id="%s-b" style="color:%s">%s</span>'
            '<span id="%s-a"%s style="color:%s;opacity:0">%s</span></div>'
            % (_chip_w(scene), pc["card"], sid, pc["dim"], ctx.esc(before), sid, attrs, pc["accent"], ctx.esc(after)))
    pic = ('<div class="fl" id="%s-pic" style="background:%s;box-shadow:%s"><div class="fl-g" id="%s-g" style="filter:%s">%s</div>'
           '<i class="fl-vig" id="%s-v" style="background:%s"></i>%s<i class="fl-leak" id="%s-lk" style="background:%s"></i>'
           '<i class="fl-bar" id="%s-bt" style="top:0;height:%dpx;background:%s;transform-origin:50%% 0"></i>'
           '<i class="fl-bar" id="%s-bb" style="bottom:0;height:%dpx;background:%s;transform-origin:50%% 100%%"></i>'
           '<i class="fl-ring" style="box-shadow:inset 0 0 0 2px %s"></i>%s</div>'
           % (sid, pc["chrome"], ctx.c["shadow"], sid, GRADE[0], _vg.picture(ctx, scene.get("src"), "p", seed=0),
              sid, vig, grain, sid, leak, sid, bar, pc["ink"], sid, bar, pc["ink"], ctx.c["card_line"], chip))
    title = ('<div class="fl-t" id="%s-t" style="color:%s">%s</div>' % (sid, ctx.ink, ctx.esc(scene["title"]))) if scene.get("title") else ""
    js = [ctx.enter("#%s-pic" % sid, ctx.t_in, {"y": 40, "scale": 0.96})]
    if title:
        js.append(ctx.enter("#%s-t" % sid, ctx.t_in + 0.15, {"y": 16}))
    # on the word: the chip turns, the bars close in, the grade warms, the vignette and the grain arrive
    js += [_vg.tween("#%s-b" % sid, {"opacity": 1, "y": 0}, {"opacity": 0, "y": -24, "duration": 0.3, "ease": mo["exit_ease"]}, t),
           _vg.tween("#%s-a" % sid, {"opacity": 0, "y": 24}, {"opacity": 1, "y": 0, "duration": 0.4, "ease": mo["enter_ease"]}, t + 0.1),
           _vg.tween("#%s-bt, #%s-bb" % (sid, sid), {"scaleY": 0}, {"scaleY": 1, "duration": 0.7, "ease": "expo.out"}, t),
           _vg.tween("#%s-g" % sid, {"filter": GRADE[0]}, {"filter": GRADE[1], "duration": 0.9, "ease": "power2.inOut"}, t),
           _vg.tween("#%s-v" % sid, {"opacity": 0}, {"opacity": 1, "duration": 0.9, "ease": "power2.inOut"}, t),
           _vg.tween("#%s-gr" % sid, {"opacity": 0}, {"opacity": 0.4, "duration": 0.5, "ease": "power2.out"}, t),
           # one light leak sweeps across, once
           _vg.tween("#%s-lk" % sid, {"xPercent": -120, "skewX": -12}, {"xPercent": 230, "skewX": -12, "duration": 1.8, "ease": "power2.inOut"}, t + 0.2),
           _vg.tween("#%s-lk" % sid, {"opacity": 0}, {"opacity": 1, "duration": 0.45, "ease": "power2.out"}, t + 0.2),
           _vg.tween("#%s-lk" % sid, {"opacity": 1}, {"opacity": 0, "duration": 0.6, "ease": "power2.in"}, t + 1.4)]
    # the grain crawls while it holds: its seed steps on the timeline (ambient: idle texture, not a change)
    k, step = 1, 1.0 / GRAIN_FPS
    while t + k * step <= ctx.t_out + 1e-6:
        ctx.ambient("tl.set('#%s-turb', %s, %.3f);" % (sid, js_obj({"attr": {"seed": grain_seed(k)}}), t + k * step))
        k += 1
    return '<div class="fl-wrap">%s%s</div>' % (pic, title), js     # its height is its content's: the title wraps at the width it is given
