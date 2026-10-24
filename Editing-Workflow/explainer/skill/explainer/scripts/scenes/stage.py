"""stage: one picture that keeps changing instead of a cut per idea (the 3Blue1Brown style). Library scenes are its
objects, each in its own box; they come in and leave on their words, and on a word an object moves and resizes to a new
box (the network shrinks into a corner while the loss curves come in beside it).

  {"type": "stage", "objects": [
     {"id": "eq", "scene": {"type": "formula", "tex": "e = \\\\hat{y} - y"}, "box": [175, 0, 600], "out": "word:10"},
     {"id": "net", "scene": {"type": "network", "layers": [4, 6, 6, 10], "forward": "word:6"}, "box": [175, 200, 600]}],
   "moves": [{"obj": "net", "at": "word:10", "box": [0, 0, 300]}]}

A box is [x, y, width] in px from the scene area's top left (950 wide, 760 tall; below y 615 only the narrow column,
x 85 to 865); the object is laid out at its own width (at least its min_width) and scaled to the box. Every box, where
it starts and wherever it moves, stays in the area with the object's words at 28 px or more (a scene with no words, a
network without labels, may shrink freely). `in` and `out` (optional) are the object's words; a move is one tween of
its place and size on the timeline (seek-safe). A stage cannot hold a stage, a custom scene or one that places itself.
"""
import math, re
import explainer_lib as E
from scenes import Ctx, js_obj

TYPE = "stage"
DECOR_KEYS = ("objects", "moves")           # each object's own claims are checked as that scene's (subscenes)
MOVE = 0.9
MAX_OBJECTS = 12
AREA_W = E.SCENE["right"] - E.SCENE["left"]
AREA_H = E.SCENE["bottom"] - E.SCENE["top"]
CSS = """
  .st { position:relative; width:100%; }
  .st-obj { position:absolute; transform-origin:0 0; }
  .st-fit { transform-origin:0 0; }
"""
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def _reg():
    from scenes import REGISTRY
    return REGISTRY


def subscenes(scene):
    """The scenes it holds, for the composer's source check and CSS."""
    return [o["scene"] for o in scene.get("objects") or [] if isinstance(o, dict) and isinstance(o.get("scene"), dict)]


def modules(scene):
    return [_reg()[s["type"]] for s in subscenes(scene) if s.get("type") in _reg()]


def min_text(mod, sub):
    if hasattr(mod, "min_text"):
        return mod.min_text(sub)
    fonts = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", getattr(mod, "CSS", "") or "")]
    return min(fonts) if fonts else None


def layout(mod, sub, w):
    """(inner width, inner height, scale) of an object drawn `w` px wide."""
    iw = max(mod.min_width(sub), int(w))
    s = w / float(iw)
    return iw, mod.height(sub, iw), s


def _check_box(oid, mod, sub, box, errs, what="box"):
    if not isinstance(box, list) or len(box) != 3 or any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in box) or box[2] <= 0:
        errs.append("%s: %s is [x, y, width]" % (oid, what))
        return None
    iw, ih, s = layout(mod, sub, box[2])
    left, top = E.SCENE["left"] + box[0], E.SCENE["top"] + box[1]
    if box[0] < 0 or box[1] < 0 or left + box[2] > E.SCENE["right"] or top + ih * s > E.SCENE["bottom"] or not E.inside_scene(left, top, box[2], ih * s):
        errs.append("%s: the %s %s (%d px tall) is outside the scene area (950 x 760; below y 615 only x 85 to 865)"
                    % (oid, what, box, ih * s))
    t = min_text(mod, sub)
    if t is not None and t * s < E.MIN_TEXT - 1e-6:
        errs.append("%s: at the %s %s its words draw at %.0f px, under 28 px; make it at least %d px wide"
                    % (oid, what, box, t * s, int(math.ceil(E.MIN_TEXT / float(t) * mod.min_width(sub)))))
    return s


def validate(scene):
    errs = []
    objs = scene.get("objects")
    if not isinstance(objs, list) or not 1 <= len(objs) <= MAX_OBJECTS:
        return ["a stage holds 1 to %d objects (they come and go: a formula that changes is a new one)" % MAX_OBJECTS]
    reg, ids = _reg(), {}
    for o in objs:
        if not isinstance(o, dict) or not _ID.match(str(o.get("id", ""))) or not isinstance(o.get("scene"), dict):
            errs.append("each object is {id (letters and digits), scene, box}")
            continue
        oid, sub = o["id"], o["scene"]
        if oid in ids:
            errs.append("%s: the object id is used twice" % oid)
        mod = reg.get(sub.get("type"))
        if mod is None:
            errs.append("%s: unknown scene type %r" % (oid, sub.get("type")))
            continue
        if mod.TYPE in ("stage", "custom") or hasattr(mod, "place"):
            errs.append("%s: a stage cannot hold a %s scene" % (oid, mod.TYPE))
            continue
        if hasattr(mod, "normalize"):
            mod.normalize(sub)
        sub_errs = mod.validate(sub)
        errs += ["%s: %s" % (oid, e) for e in sub_errs]
        ids[oid] = mod
        if not sub_errs:
            _check_box(oid, mod, sub, o.get("box"), errs)
    by = {o["id"]: o for o in objs if isinstance(o, dict) and o.get("id") in ids}
    for m in scene.get("moves") or []:
        if not isinstance(m, dict) or m.get("at") is None:
            errs.append("each move is {obj, at, box}")
        elif m.get("obj") not in by:
            errs.append("a move names no object %r (the objects: %s)" % (m.get("obj"), ", ".join(by)))
        else:
            _check_box(m["obj"], ids[m["obj"]], by[m["obj"]]["scene"], m.get("box"), errs, "move to")
    return errs


def place(scene):
    """The wide band of the scene area; objects may reach into the narrow column below it (checked per box)."""
    return E.SCENE["left"], E.SCENE["top"], AREA_W, E.L.RIGHT_COL_TOP - E.SCENE["top"]


def height(scene, width):
    return E.L.RIGHT_COL_TOP - E.SCENE["top"]


def min_width(scene):
    return AREA_W


def travels(scene):
    return True


def render(scene, ctx, box):
    reg, sid = _reg(), ctx.id
    html, js, marks = [], [], []
    for o in scene["objects"]:
        mod, sub = reg[o["scene"]["type"]], dict(o["scene"], id="%s_%s" % (sid, o["id"]))
        t_in = ctx.at(o["in"]) if o.get("in") is not None else ctx.t_in
        t_out = ctx.at(o["out"]) if o.get("out") is not None else ctx.t_out
        sc = Ctx(sub, t_in, t_out, ctx.words, ctx.tokens, ctx.vendor_dir, ctx.out_dir, ctx.bg, ctx.head, ctx.spec_dir)
        x, y, w = o["box"]
        iw, ih, s = layout(mod, sub, w)
        inner, lines = mod.render(sub, sc, (0, 0, iw))
        ctx.ambient_lines += sc.ambient_lines
        wid = "%s-obj" % sub["id"]
        later = o.get("in") is not None and t_in > ctx.t_in + 1e-6     # unseen until its word (its entrances bring in only parts)
        # GSAP moves the wrapper (no CSS transform on it, or GSAP would drop it); the fit to the box is the inner scale
        html.append('<div class="st-obj" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx%s"><div class="st-fit" style="width:%dpx;height:%dpx;'
                    'transform:scale(%s)"><div class="box" id="%s" style="position:relative;width:%dpx;height:%dpx">%s</div></div></div>'
                    % (wid, x, y, w, int(math.ceil(ih * s)), ";visibility:hidden" if later else "", iw, ih, ("%.4f" % s).rstrip("0").rstrip("."),
                       sub["id"], iw, ih, inner))
        if later:
            js.append("tl.set('#%s', { visibility: 'visible' }, %.3f);" % (wid, t_in))
        js += lines
        for m in [m for m in scene.get("moves") or [] if m["obj"] == o["id"]]:
            t, attrs = ctx.item(m["at"])
            marks.append("<i%s></i>" % attrs)
            nx, ny, nw = m["box"]
            js.append("tl.to('#%s', %s, %.3f);" % (wid, js_obj({"x": nx - x, "y": ny - y, "scale": round(nw / float(w), 4), "duration": MOVE,
                                                                "ease": "power3.inOut"}), t))
        if o.get("out") is not None:
            marks.append("<i%s></i>" % ctx.item(o["out"])[1])
            js.append("tl.to('#%s', %s, %.3f);" % (wid, js_obj({"opacity": 0, "duration": E.EXIT, "ease": "power3.in"}), t_out - E.EXIT))
    return '<div class="st" id="%s-st" style="height:%dpx">%s%s</div>' % (sid, height(scene, AREA_W), "".join(html), "".join(marks)), js
