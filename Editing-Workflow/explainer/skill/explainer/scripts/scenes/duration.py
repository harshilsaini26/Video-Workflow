"""duration: a clock hand or a dial sweeps while the number of hours, days or weeks counts up (SPEC §6.2)."""
import explainer_lib as E
from scenes import js_str, need, widest

TYPE = "duration"
NEEDS_SOURCE = True
UNITS = ("hours", "days", "weeks")
STYLES = ("clock", "dial")
FACE = 300                    # the clock or dial, px square
GAP = 30
V_SIZE = 120                  # "6 weeks", line height 1
SWEEP = 1.4

CSS = """
  .d-face { position:relative; width:%dpx; height:%dpx; opacity:0; flex:none; }
  .d-face svg { position:absolute; inset:0; }
  .d-hand { position:absolute; left:50%%; top:50%%; width:10px; height:118px; margin-left:-5px; margin-top:-118px;
    border-radius:5px; transform-origin:50%% 100%%; }
  .d-value { font-weight:700; font-size:%dpx; line-height:%dpx; margin-top:%dpx; white-space:nowrap; letter-spacing:-.02em;
    font-variant-numeric: tabular-nums; opacity:0; }
  .d-unit { font-weight:500; margin-left:.25em; font-size:.5em; line-height:0; }   /* adds nothing to the line box */
""" % (FACE, FACE, V_SIZE, V_SIZE, GAP)


def decimals(v):
    """Decimals the number is shown with: 1.5 hours stays 1.5, never rounds to 2."""
    return 0 if float(v) == int(v) else min(2, len(repr(float(v)).split(".")[1]))


def validate(scene):
    errs = need(scene, ["value", "unit"])
    if scene.get("unit") not in UNITS:
        errs.append("unit %r is not one of %s" % (scene.get("unit"), ", ".join(UNITS)))
    if scene.get("style", "clock") not in STYLES:
        errs.append("style %r is not one of %s" % (scene.get("style"), ", ".join(STYLES)))
    v = scene.get("value")
    if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
        errs.append("value %r must be a number above 0" % (v,))
    return errs


def height(scene, width):
    return FACE + GAP + V_SIZE


def min_width(scene):
    return max(FACE, int(E.text_width(str(scene["value"]), V_SIZE) + E.text_width(" " + scene["unit"], V_SIZE / 2)) + 1)


def render(scene, ctx, box):
    c = ctx.tokens["colors"]
    sid = ctx.id
    acc = c["magenta"] if ctx.light else c["cyan"]
    ring = "rgba(11,12,16,.12)" if ctx.light else "rgba(255,255,255,.16)"
    r = FACE / 2 - 14
    circ = round(2 * 3.14159265 * r, 1)
    lead = min(0.2, (ctx.t_out - ctx.t_in) / 4)
    sweep_t = max(0.1, min(SWEEP, ctx.t_out - ctx.t_in - lead - 0.1))   # done before the scene exits, however short
    if scene.get("style", "clock") == "clock":
        ticks = "".join('<line x1="%d" y1="22" x2="%d" y2="44" stroke="%s" stroke-width="6" stroke-linecap="round" transform="rotate(%d %d %d)"/>'
                        % (FACE // 2, FACE // 2, ctx.ink, k * 30, FACE // 2, FACE // 2) for k in range(12))
        face = ('<svg width="%d" height="%d"><circle cx="%d" cy="%d" r="%s" fill="none" stroke="%s" stroke-width="10"/>%s</svg>'
                '<div class="d-hand" id="%s-hand" style="background:%s"></div>' % (FACE, FACE, FACE // 2, FACE // 2, r, ring, ticks, sid, acc))
        sweep = "tl.fromTo('#%s-hand', { rotation: 0 }, { rotation: 720, duration: %.3f, ease: 'power2.inOut', immediateRender: false }, %.3f);" % (sid, sweep_t, ctx.t_in + lead)
    else:
        face = ('<svg width="%d" height="%d"><circle cx="%d" cy="%d" r="%s" fill="none" stroke="%s" stroke-width="22"/>'
                '<circle id="%s-arc" cx="%d" cy="%d" r="%s" fill="none" stroke="%s" stroke-width="22" stroke-linecap="round"'
                ' stroke-dasharray="%s" stroke-dashoffset="%s" transform="rotate(-90 %d %d)"/></svg>'
                % (FACE, FACE, FACE // 2, FACE // 2, r, ring, sid, FACE // 2, FACE // 2, r, acc, circ, circ, FACE // 2, FACE // 2))
        sweep = "tl.to('#%s-arc', { strokeDashoffset: 0, duration: %.3f, ease: 'power2.inOut' }, %.3f);" % (sid, sweep_t, ctx.t_in + lead)
    html = ('<div class="d-face">%s</div><div class="d-value" style="color:%s"><span id="%s-v">0</span><span class="d-unit">%s</span></div>'
            % (face, ctx.ink, sid, ctx.esc(scene["unit"])))
    js = [ctx.enter("#%s .d-face" % sid, ctx.t_in, {"scale": 0.8}), ctx.enter("#%s .d-value" % sid, ctx.t_in + 0.12, {"y": 24}), sweep,
          "countUp('#%s-v', 0, %s, %.3f, %.3f, '', '', %d);" % (sid, scene["value"], ctx.t_in + lead, sweep_t, decimals(scene["value"]))]
    return html, js
