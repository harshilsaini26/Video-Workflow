"""transitions.py: how one scene hands over to the next (PLAYBOOK §E6).

The composer picks a transition for every scene unless the storyboard names one ("transition": "<kind>" on the scene
coming in): the first scene fades up, a scene on a new background is wiped in (the new background opens as a circle),
and the rest alternate between a zoom and a push, so the picture never just swaps. Transitions move the scene's box
(#<id>); the living layer's slow push-in moves its .live wrapper, so the two never fight over one transform.

  fade   the scene's own entrances only; the old scene lifts and fades
  push   the new scene rises from below; the old one leaves upwards
  zoom   the new scene grows from 0.86; the old one swells past the viewer
  wipe   the new background opens as a circle from the scene area; used at a background change
  burst  a spray of coloured squares from the centre; the new scene grows from 0.7 (for a hook or a reveal)
  cut    nothing moves: the old scene is gone on the frame the new one starts
"""
import random

from scenes import js_obj

KINDS = ("fade", "push", "zoom", "wipe", "burst", "cut")
ENTER, EXIT = 0.5, 0.28          # exits stay within tokens.motion.exit
WIPE, BURST = 0.55, 0.9
WIPE_FROM, WIPE_TO = "circle(0% at 50% 60%)", "circle(150% at 50% 60%)"
CENTRE = (540, 884)              # the scene area's centre
PARTICLES = 28


def pick(index, prev_bg, bg, explicit):
    """The way scene `index` comes in: the storyboard's choice, else fade first, wipe on a new background, then zoom and
    push in turn."""
    if explicit:
        return explicit
    if index == 0:
        return "fade"
    if prev_bg is not None and prev_bg != bg:
        return "wipe"
    return "push" if index % 2 == 0 else "zoom"


def _from(sel, frm, to, t):
    to = dict(to, duration=ENTER, ease="power3.out", immediateRender=False)
    return "tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj(frm), js_obj(to), t)


def enter(kind, sid, t):
    """Tweens on the incoming scene's box (its own elements still make their entrances)."""
    sel = "#" + sid
    if kind == "push":
        return [_from(sel, {"y": 160}, {"y": 0}, t)]
    if kind == "zoom":
        return [_from(sel, {"scale": 0.86}, {"scale": 1}, t)]
    if kind == "wipe":
        return [_from(sel, {"scale": 0.94}, {"scale": 1}, t)]
    if kind == "burst":
        return [_from(sel, {"scale": 0.7}, {"scale": 1}, t)]
    return []


def exit(kind, sid, t):
    """The outgoing scene's exit, matched to the way the next one comes in."""
    sel = "#" + sid
    if kind == "cut":
        return ["tl.set('%s', { opacity: 0 }, %.3f);" % (sel, t)]
    move = {"push": {"y": -160}, "zoom": {"scale": 1.18}, "burst": {"scale": 1.3}}.get(kind, {"y": -24})
    return ["tl.to('%s', %s, %.3f);" % (sel, js_obj(dict({"opacity": 0}, **dict(move, duration=EXIT, ease="power2.in"))), t)]


def wipe_bg(bg_id, t):
    """Open background `bg_id` as a growing circle (it was hidden until now)."""
    return ["tl.set('#%s', { opacity: 1 }, %.3f);" % (bg_id, t),
            "tl.fromTo('#%s', %s, %s, %.3f);" % (bg_id, js_obj({"clipPath": WIPE_FROM}),
                                                 js_obj({"clipPath": WIPE_TO, "duration": WIPE, "ease": "power2.inOut",
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
