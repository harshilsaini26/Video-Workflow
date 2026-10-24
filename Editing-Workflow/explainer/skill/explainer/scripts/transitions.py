"""transitions.py: how one scene hands over to the next (PLAYBOOK §E6).

The composer picks a transition for every scene unless the storyboard names one ("transition": "<kind>" on the scene
coming in): the first scene fades up, a scene on a new background is wiped in (the new background opens as a circle),
and the rest alternate between a zoom and a push, so the picture never just swaps. Transitions move the scene's box
(#<id>); the scene's fit-to-area scale sits on its .live wrapper, so the two never fight over one transform. Every cut is
velocity-matched (MOTION.md): the exit accelerates into the cut and the entrance decelerates out of it.

  fade   the scene's own entrances only; the old scene lifts and fades
  push   a whip: the old scene flies up and blurs, the new one lands from below out of a blur
  zoom   HyperFrames' zoom-through: the old scene rushes past the viewer (1 to 1.2, blur 10 px, power3.in 0.2 s), the new
         one lands from behind (0.75 to 1, blur 8 to 0 px, expo.out 0.5 s)
  wipe   the new background opens as a circle from the scene area; used at a background change
  burst  a spray of coloured squares from the centre; the new scene grows from 0.7 (for a hook or a reveal)
  cut    nothing moves: the old scene is gone on the frame the new one starts
  leak   a wide soft streak of light (the accent and the second accent, screen-blended) sweeps across over the cut; never
         picked on its own: name it for a jolt of energy or a reveal
  brush  five ragged ink bands sweep across and cover the frame on the cut, then sweep off (the paper look's wipe at a
         new ground; after ClaudeAnimationBase's brush wipe, MIT)

The last scene leaves too (close()): over the first half of the last CLOSE seconds; the hook's ground wipes in over the
second half, ending exactly at the end, so the loop seams back into the hook.
"""
import math, random

import explainer_lib as E
from scenes import js_obj

KINDS = ("fade", "push", "zoom", "wipe", "burst", "cut", "brush", "leak")
ENTER, EXIT = 0.5, E.EXIT        # exits stay within tokens.motion.exit
IN_EASE, OUT_EASE = "expo.out", "power3.in"   # the exit accelerates into the cut, the entrance decelerates out of it
WIPE, BURST = 0.55, 0.9
WIPE_FROM, WIPE_TO = "circle(0% at 50% 60%)", "circle(150% at 50% 60%)"
CENTRE = (540, (E.SCENE["top"] + E.SCENE["bottom"]) // 2)   # the scene area's centre
PARTICLES = 28
BRUSH, UNCOVER, TILT = 0.35, 0.3, -0.1        # the cover (s), the uncover (s), the bands' tilt (radians)
STAGGER = (0, .14, .06, .18, .1)               # of the cover time: no two bands move as twins
CLOSE = E.CLOSE
LEAK, LEAK_W = 0.9, 1100       # the streak's sweep (s, centred on the cut) and its width (px)


def pick(index, prev_bg, bg, explicit, look=None):
    """The way scene `index` comes in: the storyboard's choice, else fade first, wipe on a new background (brush in the
    paper look), then zoom and push in turn."""
    if explicit:
        return explicit
    if index == 0:
        return "fade"
    if prev_bg is not None and prev_bg != bg:
        return "brush" if look == "paper" else "wipe"
    return "push" if index % 2 == 0 else "zoom"


def _from(sel, frm, to, t):
    to = dict(to, duration=ENTER, ease=IN_EASE, immediateRender=False)
    return "tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj(frm), js_obj(to), t)


def enter(kind, sid, t):
    """Tweens on the incoming scene's box (its own elements still make their entrances)."""
    sel = "#" + sid
    if kind == "push":
        return [_from(sel, {"y": 300, "filter": "blur(10px)"}, {"y": 0, "filter": "blur(0px)"}, t)]
    if kind == "zoom":
        return [_from(sel, {"scale": 0.75, "filter": "blur(8px)"}, {"scale": 1, "filter": "blur(0px)"}, t)]
    if kind in ("wipe", "brush"):
        return [_from(sel, {"scale": 0.94}, {"scale": 1}, t)]
    if kind == "leak":
        return [_from(sel, {"scale": 0.92, "filter": "blur(8px)"}, {"scale": 1, "filter": "blur(0px)"}, t)]
    if kind == "burst":
        return [_from(sel, {"scale": 0.7}, {"scale": 1}, t)]
    return []


def exit(kind, sid, cut):
    """The outgoing scene's exit, matched to the way the next one comes in. It runs over the EXIT seconds before the
    cut and is over on it, so the old scene and the new one are never on screen together (SOP S9)."""
    sel = "#" + sid
    if kind == "cut":
        return ["tl.set('%s', { opacity: 0 }, %.3f);" % (sel, cut)]
    move = {"push": {"y": -260, "filter": "blur(12px)"}, "zoom": {"scale": 1.2, "filter": "blur(10px)"},
            "burst": {"scale": 1.3, "filter": "blur(10px)"}, "leak": {"scale": 1.08, "filter": "blur(10px)"}}.get(kind, {"y": -24})
    return ["tl.to('%s', %s, %.3f);" % (sel, js_obj(dict({"opacity": 0}, **dict(move, duration=EXIT, ease=OUT_EASE))), max(0.0, cut - EXIT))]


def wipe_bg(bg_id, t, dur=WIPE):
    """Open background `bg_id` as a growing circle over `dur` seconds (it was hidden until now)."""
    return ["tl.set('#%s', { opacity: 1 }, %.3f);" % (bg_id, t),
            "tl.fromTo('#%s', %s, %s, %.3f);" % (bg_id, js_obj({"clipPath": WIPE_FROM}),
                                                 js_obj({"clipPath": WIPE_TO, "duration": dur, "ease": "power2.inOut",
                                                         "immediateRender": False}), t)]


def burst(k, t, colors):
    """28 squares thrown out from the centre of the scene area at `t`: (html, [js]). Seeded by `k`, so the same page
    renders the same spray every time."""
    rng = random.Random(1000 + k)
    html, js = [], []
    for i in range(PARTICLES):
        size = rng.randint(14, 46)
        html.append('<i class="tx-p" id="tx%d-%d" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s"></i>'
                    % (k, i, CENTRE[0] - size // 2, CENTRE[1] - size // 2, size, size, colors[i % len(colors)]))
        js.append("tl.fromTo('#tx%d-%d', %s, %s, %.3f);" % (
            k, i, js_obj({"x": 0, "y": 0, "rotation": 0, "opacity": 1}),
            js_obj({"x": rng.randint(-620, 620), "y": rng.randint(-900, 900), "rotation": rng.randint(-240, 240), "opacity": 0,
                    "duration": BURST, "ease": "power2.out", "immediateRender": False}), t))
    return "".join(html), js


def brush(k, t, colors):
    """Five ragged bands that cover the frame on the cut at `t` and uncover it after: (html, [js]). Seeded by `k`."""
    rng = random.Random(1000 + k)
    top, h, x0, x1 = -260, 500, -240, 1320          # tilted, five bands of 500 px still cover 1080x1920 edge to edge
    paths, js = [], []
    for i, f in enumerate(STAGGER):
        y = top + i * (h - 50)                       # 50 px of overlap: more than two edges' wander (2 x 22)
        xs = list(range(x0, x1 + 1, 60))
        edge = ["%d,%d" % (x, y + rng.randint(-22, 22)) for x in xs] + ["%d,%d" % (x, y + h + rng.randint(-22, 22)) for x in reversed(xs)]
        paths.append('<path class="tx-brush" id="txb%d-%d" d="M%sZ" fill="%s"/>' % (k, i, " L".join(edge), colors[i % len(colors)]))
        start = round(max(0.0, t - BRUSH + f * BRUSH), 3)   # never before 0: GSAP would shift the whole page later
        js.append("tl.set('#txb%d-%d', { scaleX: 0 }, 0);" % (k, i))      # hidden until it sweeps in
        js.append("tl.fromTo('#txb%d-%d', %s, %s, %.3f);" % (k, i, js_obj({"scaleX": 0}), js_obj(
            {"scaleX": 1, "duration": round(t - start, 3), "ease": "power3.in", "transformOrigin": "0% 50%", "immediateRender": False}), start))
        js.append("tl.to('#txb%d-%d', %s, %.3f);" % (k, i, js_obj({"scaleX": 0, "transformOrigin": "100% 50%", "duration": UNCOVER,
                                                                  "ease": "expo.out"}), t))
    svg = ('<svg class="tx-brushes" width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;left:0;top:0">'
           '<g transform="rotate(%.2f 540 960)">%s</g></svg>' % (math.degrees(TILT), "".join(paths)))
    return svg, js


def close(sid, end):
    """The last scene's exit, over the first half of the last CLOSE seconds: gone before the ground changes in the second
    half (the composer's wipe), so no words are ever read over a ground that is changing."""
    return ["tl.to('#%s', %s, %.3f);" % (sid, js_obj({"opacity": 0, "y": -24, "duration": CLOSE / 2, "ease": OUT_EASE}), end - CLOSE)]


def leak(k, t, colors):
    """A soft streak of light that sweeps across the frame over the cut at `t`: (html, [js]). Two palette colours."""
    a, b = (E.rgba(c, 0.85) for c in colors[:2])
    html = ('<div class="tx-leak" id="txl%d" style="position:absolute;left:%dpx;top:-30%%;width:%dpx;height:160%%;'
            'background:linear-gradient(90deg, transparent, %s 35%%, %s 65%%, transparent);filter:blur(70px);mix-blend-mode:screen;'
            'opacity:0"></div>' % (k, (1080 - LEAK_W) // 2, LEAK_W, a, b))
    span = 1080 + LEAK_W
    js = ["tl.fromTo('#txl%d', %s, %s, %.3f);" % (k, js_obj({"x": -span, "rotation": -18, "opacity": 1}),
                                                  js_obj({"x": span, "duration": LEAK, "ease": "power1.inOut", "immediateRender": False}),
                                                  t - LEAK / 2.0),
          "tl.set('#txl%d', { opacity: 0 }, %.3f);" % (k, t + LEAK / 2.0)]
    return html, js
