"""flow: two to four steps in a column, joined by connectors that draw as each step arrives; a pulse keeps running
down every drawn connector while the scene holds (PLAYBOOK §E4). For a process: "it retrieves, then augments, then
generates"."""
import explainer_lib as E
from scenes import js_obj, need

TYPE = "flow"
NODE, LINK = 112, 72             # a step's height, the connector between two steps
PAD, ICON, I_GAP = 34, 64, 22    # padding a side, the icon, icon to label
SIZE = 50                        # label: DM Sans 700, one line
BORDER = 3
PULSE = 18

CSS = """
  .fl { position:relative; width:100%%; }
  .fl-node { position:absolute; left:0; width:100%%; height:%dpx; border-radius:30px; display:flex; align-items:center;
    justify-content:center; gap:%dpx; padding:0 %dpx; border:%dpx solid; font-weight:700; font-size:%dpx; line-height:1;
    white-space:nowrap; opacity:0; }
  .fl-ic { width:%dpx; height:%dpx; flex:none; display:flex; }
  .fl-ic svg { width:100%%; height:100%%; }
  .fl-link { position:absolute; left:50%%; width:8px; margin-left:-4px; overflow:visible; }
  .fl-pulse { position:absolute; left:50%%; width:%dpx; height:%dpx; margin-left:-%dpx; border-radius:50%%; opacity:0; }
""" % (NODE, I_GAP, PAD, BORDER, SIZE, ICON, ICON, PULSE, PULSE, PULSE // 2)


def validate(scene):
    errs = need(scene, ["nodes"])
    nodes = scene.get("nodes") or []
    if not 2 <= len(nodes) <= 4:
        errs.append("a flow takes 2 to 4 nodes (got %d)" % len(nodes))
    errs += ["node %d has no label" % i for i, n in enumerate(nodes) if not n.get("label")]
    errs += ["node %d has no at" % i for i, n in enumerate(nodes) if n.get("at") is None]
    return errs


def height(scene, width):
    n = len(scene["nodes"])
    return n * NODE + (n - 1) * LINK


def min_width(scene):
    return max(int(E.text_width(n["label"], SIZE)) + 1 + 2 * (PAD + BORDER) + ((ICON + I_GAP) if n.get("icon") else 0)
               for n in scene["nodes"])


def render(scene, ctx, box):
    c, mo = ctx.tokens["colors"], ctx.tokens["motion"]
    sid, acc = ctx.id, (c["magenta"] if ctx.light else c["cyan"])
    face = "background:#FFFFFF;box-shadow:0 18px 50px rgba(11,12,16,.14)" if ctx.light else "background:rgba(255,255,255,.09)"
    rest = "rgba(11,12,16,.10)" if ctx.light else "rgba(255,255,255,.16)"
    nodes = scene["nodes"]
    parts, js, times = [], [], []
    for i, n in enumerate(nodes):
        t, attrs = ctx.item(n["at"])
        times.append(t)
        top = i * (NODE + LINK)
        icon = '<span class="fl-ic" style="color:%s">%s</span>' % (acc, ctx.icon(n["icon"])) if n.get("icon") else ""
        parts.append('<div class="fl-node" id="%s-n%d"%s style="top:%dpx;%s;border-color:%s;color:%s">%s<span>%s</span></div>'
                     % (sid, i, attrs, top, face, rest, ctx.ink, icon, ctx.esc(n["label"])))
        js.append(ctx.enter("#%s-n%d" % (sid, i), t, {"y": 30, "scale": 0.92}))
        js.append("tl.to('#%s-n%d', %s, %.3f);" % (sid, i, js_obj({"borderColor": acc, "duration": 0.3, "ease": mo["enter_ease"]}), t))
        if i:
            js.append("tl.to('#%s-n%d', %s, %.3f);" % (sid, i - 1, js_obj({"borderColor": rest, "duration": 0.3, "ease": mo["enter_ease"]}), t))
            ltop = top - LINK
            parts.append('<svg class="fl-link" style="top:%dpx;height:%dpx" viewBox="0 0 8 %d"><line x1="4" y1="6" x2="4" y2="%d" '
                         'stroke="%s" stroke-width="6" stroke-linecap="round" stroke-dasharray="%d" stroke-dashoffset="%d" id="%s-k%d"/></svg>'
                         '<i class="fl-pulse" id="%s-p%d" style="top:%dpx;background:%s;box-shadow:0 0 18px %s"></i>'
                         % (ltop, LINK, LINK, LINK - 6, acc, LINK, LINK, sid, i, sid, i, ltop, acc, acc))
            js.append("tl.fromTo('#%s-k%d', { strokeDashoffset: %d }, %s, %.3f);"
                      % (sid, i, LINK, js_obj({"strokeDashoffset": 0, "duration": 0.35, "ease": "power2.out", "immediateRender": False}),
                         max(ctx.t_in, t - 0.15)))
    # while it holds: a pulse runs down each drawn connector, and the column floats
    for i in range(1, len(nodes)):
        t = times[i] + 0.4
        while t + 0.9 <= ctx.t_out:
            ctx.ambient("tl.fromTo('#%s-p%d', { y: 0, opacity: 1 }, %s, %.3f);"
                        % (sid, i, js_obj({"y": LINK - PULSE, "opacity": 0, "duration": 0.9, "ease": "power1.in", "immediateRender": False}), t))
            t += 1.2
    ctx.idle("#%s .fl" % sid, ctx.t_in + 0.6, ctx.t_out, {"y": -8})
    return '<div class="fl" style="height:%dpx">%s</div>' % (height(scene, box[2]), "".join(parts)), js
