"""timeline: two to five steps down a rail; each step lights its dot on its word and the progress line grows to it,
and the newest dot pulses while it waits for the next (PLAYBOOK §E4). For a plan or a history: "week 1, week 2"."""
import explainer_lib as E
from scenes import js_obj, need

TYPE = "timeline"
STEP_H = 132                     # one step: its label line, its sub line and the space under them
RAIL_X, DOT = 40, 30             # the rail's x and a dot's size
TEXT_X = 104                     # the labels' left edge
L_SIZE, L_LINE = 50, 60          # label: DM Sans 700, one line
S_SIZE, S_LINE = 32, 42          # sub: DM Sans 500, one line

CSS = """
  .tm { position:relative; width:100%%; }
  .tm-rail, .tm-prog { position:absolute; left:%dpx; width:6px; margin-left:-3px; border-radius:3px; }
  .tm-prog { height:0; }
  .tm-dot { position:absolute; left:%dpx; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:50%%; border:5px solid; }
  .tm-halo { position:absolute; left:%dpx; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:50%%; opacity:0; }
  .tm-step { position:absolute; left:%dpx; right:0; opacity:0; }
  .tm-l { font-weight:700; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .tm-s { font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
""" % (RAIL_X, RAIL_X, DOT, DOT, DOT // 2, RAIL_X, DOT + 26, DOT + 26, (DOT + 26) // 2, TEXT_X, L_SIZE, L_LINE, S_SIZE, S_LINE)


def validate(scene):
    errs = need(scene, ["steps"])
    steps = scene.get("steps") or []
    if not 2 <= len(steps) <= 5:
        errs.append("a timeline takes 2 to 5 steps (got %d)" % len(steps))
    errs += ["step %d has no label" % i for i, s in enumerate(steps) if not s.get("label")]
    errs += ["step %d has no at" % i for i, s in enumerate(steps) if s.get("at") is None]
    return errs


def height(scene, width):
    return len(scene["steps"]) * STEP_H


def min_width(scene):
    return TEXT_X + max(int(max(E.text_width(s["label"], L_SIZE), E.text_width(s.get("sub", ""), S_SIZE, "display500"))) + 1
                        for s in scene["steps"])


def render(scene, ctx, box):
    c, mo = ctx.c, ctx.tokens["motion"]
    sid, acc, dim, rail = ctx.id, c["accent"], c["dim"], c["line"]
    steps = scene["steps"]
    cy = lambda i: i * STEP_H + L_LINE // 2           # a step's dot centre, level with its label
    parts = ['<div class="tm-rail" style="top:%dpx;height:%dpx;background:%s"></div>' % (cy(0), cy(len(steps) - 1) - cy(0), rail),
             '<div class="tm-prog" id="%s-prog" style="top:%dpx;background:%s"></div>' % (sid, cy(0), acc)]
    # the rail and its empty dots come in with the scene, so the plan is on screen before its first step is said
    js, times = [ctx.enter("#%s .tm-rail, #%s .tm-dot" % (sid, sid), ctx.t_in, {"y": -16}, stagger=0.3)], []
    for i, s in enumerate(steps):
        t, attrs = ctx.item(s["at"])
        times.append(t)
        sub = '<div class="tm-s" style="color:%s">%s</div>' % (dim, ctx.esc(s["sub"])) if s.get("sub") else ""
        parts.append('<i class="tm-halo" id="%s-h%d" style="top:%dpx;background:%s"></i>' % (sid, i, cy(i) - (DOT + 26) // 2, acc))
        parts.append('<i class="tm-dot" id="%s-d%d" style="top:%dpx;border-color:%s;background:%s"></i>'
                     % (sid, i, cy(i) - DOT // 2, rail, c["bg"]))
        parts.append('<div class="tm-step" id="%s-s%d"%s style="top:%dpx"><div class="tm-l" style="color:%s">%s</div>%s</div>'
                     % (sid, i, attrs, i * STEP_H, ctx.ink, ctx.esc(s["label"]), sub))
        js.append(ctx.enter("#%s-s%d" % (sid, i), t, {"x": -30}))
        js.append("tl.to('#%s-d%d', %s, %.3f);" % (sid, i, js_obj({"borderColor": acc, "backgroundColor": acc, "duration": 0.3,
                                                                   "ease": mo["enter_ease"]}), t))
        js.append("tl.fromTo('#%s-d%d', { scale: 0.5 }, %s, %.3f);" % (sid, i, js_obj({"scale": 1, "duration": mo["enter"], "ease": "expo.out",
                                                                                       "immediateRender": False}), t))
        if i:
            js.append("tl.to('#%s-prog', %s, %.3f);" % (sid, js_obj({"height": cy(i) - cy(0), "duration": 0.5, "ease": mo["enter_ease"]}), t - 0.1))
    for i, t in enumerate(times):   # the newest dot breathes until the next one lights
        end = times[i + 1] if i + 1 < len(times) else ctx.t_out
        if end <= t + 0.3:
            continue
        ctx.ambient("tl.set('#%s-h%d', { opacity: 0.35 }, %.3f);" % (sid, i, t + 0.3))
        ctx.idle("#%s-h%d" % (sid, i), t + 0.3, end, {"scale": 1.5}, every=0.8)
        ctx.ambient("tl.set('#%s-h%d', { opacity: 0 }, %.3f);" % (sid, i, end))
    return '<div class="tm" style="height:%dpx">%s</div>' % (height(scene, box[2]), "".join(parts)), js
