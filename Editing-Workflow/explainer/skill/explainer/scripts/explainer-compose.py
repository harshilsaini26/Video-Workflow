#!/usr/bin/env python3
"""explainer-compose.py: build public/index.html for an explainer reel (1080x1920, 60 fps) from storyboard.json (gate E3).

  explainer-compose.py --spec videos/<p>/storyboard.json --out videos/<p>/public [--vendor DIR] [--kit DIR]

The page has three layers (SPEC §6.1): a background that cross-fades when a scene's `bg` changes, one scene at a time
scaled up to fill the scene area (x 65 to 1015, y 345 to 1105; 780 px wide when it reaches below y 960), and word captions,
small, in the band at y 1130 to 1235. Scene times are word anchors ("word:N" in transcript.json); an entrance lands 0.2 s before
its word. Each scene's exit runs over the 0.2 s before its `out` and the next one enters on it: one scene on screen at a
time (SOP S9).

The markup is the kit's: card-host clips with data-anchor, items with data-at, the caption layer marked cap-layer, the
voice as an <audio> clip, one paused GSAP timeline in window.__timelines, so beat-check.py, gap-scan.py, snap-beats.py
and verify-render.py read it unchanged.

Fails (exit 1, "E3 FAIL: <scene id>: ...") on: an unknown type or bad id, a scene that does not fit the scene area or
has a word wider than its column, an anchor that does not resolve or runs backwards, an item outside its scene, a
number with no source, more than 0.3 s with no scene (at the start, between scenes or at the end), or two scenes
overlapping by more than 0.3 s, a voice over the 90 s ceiling, or a hook item that lands after 0.8 s (SOP S8).
"""
import argparse, html, json, math, os, random, re, shutil, sys, wave
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explainer_lib as E
import sound
import transitions as X
import headline as HL
import paper
import thread as TH
from scenes import REGISTRY, Ctx, SceneError, js_obj, js_str

L = E.L
WIDE = (L.SAFE["left"], L.SAFE["right"] - L.SAFE["left"])          # 65, 950
NARROW = (L.NARROW["left"], L.NARROW["right"] - L.NARROW["left"])  # 150, 780
CENTRE = (E.SCENE["top"] + E.SCENE["bottom"]) // 2                 # 725: every scene centres here (E.centre_top)
GAP_MAX = 0.3
GSAP_CDN = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
FONTS = os.path.join(HERE, "..", "assets", "fonts")
FONT_FILES = ("DMSans-500.woff2", "DMSans-700.woff2", "JetBrainsMono-500.woff2", "Archivo-wdth.woff2", "InstrumentSerif-Italic.woff2")
CAP_SIZE = E.CAPTION_SIZE
BRAND_TOP, BRAND_H = 281, 40           # the handle and the series part: inside the safe area, above the scene area


NUMBER_TYPES = {"stat", "count-up", "price-sticker", "number"}   # a number needs time on screen (pace-check's read floor)
VOID = {"br", "img", "input", "hr", "meta", "link", "source", "wbr", "path", "circle", "rect", "line", "polyline", "use", "stop"}


class Reads(HTMLParser):
    """[(t, text)]: every element with a data-at, and the words inside it."""
    def __init__(self, markup):
        super().__init__()
        self.out, self.open = [], []          # open: [tag, index into out or None]
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        at = dict(attrs).get("data-at")
        if at is not None:
            self.out.append([float(at), ""])
        if tag not in VOID:
            self.open.append([tag, len(self.out) - 1 if at is not None else None])

    def handle_endtag(self, tag):
        while self.open and self.open.pop()[0] != tag:
            pass

    def handle_data(self, data):
        for _, k in self.open:
            if k is not None:
                self.out[k][1] += data


def fail(msg):
    print("E3 FAIL: " + msg)
    sys.exit(1)


RESERVED = re.compile(r"^(stage|captions|voice|bg\d+|cap\d+)$")
NOT_SHOWN = {"type", "id", "bg", "in", "out", "at", "source", "icon", "html", "build", "tex", "style", "unit",
             "n", "size", "decimals", "point", "row", "cell", "box", "hi", "value", "points",
             "card", "side", "transition", "badge", "logo", "src", "screenshot", "focus", "aside_at", "title_at", "case"}   # settings, indexes, step numbers, files
BAD_DATA = (TypeError, ValueError, KeyError, AttributeError, IndexError)


def shows_number(node, key=None, decor=()):
    """True when any text the scene puts on screen has a digit, %, or a currency sign (formula TeX aside). `decor` names
    a scene's UI furniture (its module's DECOR_KEYS: a timecode, a like count in a mock-up): not a claim, no source."""
    if key in NOT_SHOWN or key in decor:
        return False
    if isinstance(node, str):
        return bool(re.search(r"[\d%$€£₹]", node))
    if isinstance(node, (int, float)) and not isinstance(node, bool):   # 1500000 in a sheet is on screen too
        return True
    if isinstance(node, dict):
        return any(shows_number(v, k, decor) for k, v in node.items())
    if isinstance(node, list):
        return any(shows_number(v, key, decor) for v in node)
    return False


def line_span(line):
    """(start, end) of the change one of the composer's own timeline lines makes, or None (a comment, a katex call)."""
    m = re.match(r"countUp\('[^']*', [^,]+, [^,]+, ([\d.]+), ([\d.]+),", line)
    if m:
        return float(m.group(1)), float(m.group(1)) + float(m.group(2))
    m = re.match(r"tl\.(?:fromTo|to|set)\(.*, ([\d.]+)\);$", line)
    if m:
        t = float(m.group(1))
        d = re.findall(r"duration: ([\d.]+)", line)
        amount = re.findall(r"amount: ([\d.]+)", line)
        return t, t + (float(d[-1]) if d else 0.0) + (float(amount[-1]) if amount else 0.0)
    return None


IDLE_ROOM = E.IDLE_ROOM
SCALE_MAX, SCALE_STEP = 1.8, 0.05   # how far a template scene is blown up to fill the scene area (MOTION.md: fill the frame)
SCALE_MIN = 0.8                      # and how far one that is too tall may shrink (the probe's 28 px floor still holds)


def place(sid, mod, scene, area_top=None):
    """(left, top, width, height, inner width, inner height, scale): the scene laid out at inner width and scaled by
    `scale` to fill the scene area, the largest scale (up to SCALE_MAX, or the module's MAX_SCALE) that keeps it inside
    the area, every word inside its column, and its box in the narrow column wherever it reaches below y 960.
    A scene that brings its own box (custom) is only checked, and never scaled."""
    sa = E.SCENE
    if hasattr(mod, "place"):
        left, top, width, h = mod.place(scene)
        if not E.inside_scene(left, top, width, h):
            fail("%s: the box %d,%d %dx%d is outside the scene area (x %d to %d, y %d to %d; x %d to %d below y %d)"
                 % (sid, left, top, width, h, sa["left"], sa["right"], sa["top"], sa["bottom"], L.NARROW["left"], L.NARROW["right"], L.RIGHT_COL_TOP))
        return left, top, width, h, width, h, 1.0
    top0 = sa["top"] if area_top is None else area_top          # under a headline, the area starts below it
    area_h = sa["bottom"] - top0 - 2 * IDLE_ROOM
    need = mod.min_width(scene)
    fonts = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", getattr(mod, "CSS", "") or "")]
    floor = E.MIN_TEXT / float(min(fonts)) if fonts else SCALE_MIN      # never scale its smallest text under 28 px
    cap = min(SCALE_MAX, mod.max_scale(scene) if hasattr(mod, "max_scale") else getattr(mod, "MAX_SCALE", SCALE_MAX))
    cap = math.floor(cap * 100 + 1e-6) / 100.0          # the page draws scale(%.2f): size the box with exactly that
    steps = int(math.floor((cap - 1.0) / SCALE_STEP + 1e-9))
    shrink = [round(1.0 - SCALE_STEP * k, 2) for k in range(1, int(round((1.0 - SCALE_MIN) / SCALE_STEP)) + 1)]
    for s in [cap] + [round(1.0 + SCALE_STEP * k, 2) for k in range(steps, -1, -1) if 1.0 + SCALE_STEP * k < cap - 1e-9] + shrink:
        if s < floor - 1e-9:
            continue
        for col_left, col_w in (WIDE, NARROW):
            iw = int(col_w / s)
            if need > iw or (need > col_w and not getattr(mod, "SHRINK_WIDTH", False)):
                continue                     # shrinking is for height: a word wider than the column never fits
            ih = mod.height(scene, iw)
            w, h = int(math.floor(iw * s)), int(math.ceil(ih * s))
            if col_w == WIDE[1] and h > L.RIGHT_COL_TOP - top0 - 2 * IDLE_ROOM:
                continue            # the full width only above the action column
            top = E.centre_top(h, col_w == WIDE[1], top0)
            if h > area_h:
                continue
            left = col_left + (col_w - w) // 2
            if E.inside_scene(left, top - IDLE_ROOM, w, h + 2 * IDLE_ROOM) and top - IDLE_ROOM >= top0:
                return left, top, w, h, iw, ih, round(s, 2)
    # nothing fits even unscaled: say why, as before
    left, width = NARROW
    if need > width:
        fail("%s: a word or a number in it (at its widest as it counts) is about %d px wide, wider than the %d px column; "
             "shorten it or use a smaller size" % (sid, need, width))
    if area_top is not None:
        fail("%s: the headline leaves %d px for the scene, and it needs %d px at a size its smallest text can take; shorten "
             "the headline or drop an item" % (sid, area_h, mod.height(scene, width)))
    fail("%s: the scene is %d px tall, taller than the scene area (%d px) at a size its smallest text can take; drop a "
         "row or an item (captions carry the words), never split it for height (SOP S9)" % (sid, mod.height(scene, width), area_h))


def glows(i, bg, tok, cuts, bg_js):
    """The glows inside background layer i (tokens.ambient.glows: each background's own). They hold still while a scene
    holds and move only on a cut, travelling with it (expo.out over ambient.shift.duration): motion with a reason, not
    lazy breathing (MOTION.md). Each move is to a seeded spot around the glow's home, so every render is the same.
    Ambient: never a change for pace-check."""
    amb = tok["ambient"]
    sh = amb["shift"]
    out = []
    for k, g in enumerate(amb["glows"][bg]):
        rng = random.Random(97 * i + 7 + k)
        size, (cx, cy) = int(g["size"]), g["at"]
        out.append('<i class="orb" id="bg%d-o%d" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;'
                   'background:radial-gradient(circle, %s 0%%, transparent 65%%)"></i>' % (i, k, cx - size // 2, cy - size // 2, size, size, E.rgba(tok["palette"][g["color"]], g["alpha"])))
        at = (0, 0)   # each move starts where the last one ended, written out: a seek into an overlap draws the same frame
        for n, t in enumerate(cuts):
            sign = 1 if (n + k) % 2 == 0 else -1
            to = (sign * int(round(rng.uniform(0.5, 1.0) * sh["x"])), int(round(rng.uniform(-1.0, 1.0) * sh["y"])))
            bg_js.append("tl.fromTo('#bg%d-o%d', %s, %s, %.3f);" % (i, k, js_obj({"x": at[0], "y": at[1]}),
                                                                   js_obj({"x": to[0], "y": to[1], "duration": sh["duration"],
                                                                           "ease": "expo.out", "immediateRender": False}), t))
            at = to
    return "".join(out)


def particles(i, bg, tok, D, bg_js):
    """A field of small squares and dots inside background layer i, rising slowly for the whole reel (one linear tween
    each, seeded: every render is the same). Behind the scenes; ambient, never a change for pace-check."""
    pt = tok["ambient"]["particles"]
    rng = random.Random(pt["seed"] * 101 + i)
    cols = pt["colors"][bg]
    out = []
    for k in range(pt["count"]):
        size = rng.randint(pt["size"][0], pt["size"][1])
        x, y = rng.randint(20, 1060), rng.randint(120, 1880)
        name, alpha = cols[k % len(cols)]
        round_ = rng.random() < 0.5
        out.append('<i class="pt" id="bg%d-p%d" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s;border-radius:%s"></i>'
                   % (i, k, x, y, size, size, E.rgba(tok["palette"][name], alpha), "50%" if round_ else "3px"))
        dx = rng.randint(-pt["drift"], pt["drift"])
        rise = int(pt["rise"] * rng.uniform(0.6, 1.0))
        bg_js.append("tl.fromTo('#bg%d-p%d', %s, %s, 0);" % (i, k, js_obj({"x": 0, "y": 0, "rotation": 0}),
                                                             js_obj({"x": dx, "y": -rise, "rotation": rng.choice([-90, 90]),
                                                                     "duration": round(D, 3), "ease": "none", "immediateRender": False})))
    return "".join(out)


def cam_from(mod, scale, tok):
    """Where a scene's camera push starts: the token's depth (0.95), or shallower when the scene's smallest text, at its
    fit, would be drawn under 28 px there; never past the push's end."""
    cam = tok["ambient"]["camera"]
    fonts = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", getattr(mod, "CSS", "") or "")]
    need = E.MIN_TEXT / (min(fonts) * scale) if fonts else 0.0
    return min(cam["to"], max(cam["from"], math.ceil(need * 1000 - 1e-6) / 1000.0))   # rounded up: never a hair under


def camera(sid, k, t_in, t_out, tok, start=None):
    """The camera through a scene: a steady push-in and a slight turn over its whole life (the turn alternates scene to
    scene), on the scene's own .cam wrapper, between the transitions (on the box) and the fit (on .live). It pushes in
    from under the box's size to just under it (0.95 to 0.995, or from `start`: cam_from), so the turn never carries a
    word past the column's edge and never draws text under 28 px; linear, so it never comes to rest (an eased push
    stops at both ends, and gate E6 sees those ends still)."""
    cam = tok["ambient"]["camera"]
    yaw = cam["yaw"] * (1 if k % 2 == 0 else -1)
    return "tl.fromTo('#%s-cam', %s, %s, %.3f);" % (sid, js_obj({"scale": cam["from"] if start is None else start, "y": cam["y"], "rotationY": -yaw}),
                                                     js_obj({"scale": cam["to"], "y": -cam["y"], "rotationY": yaw, "duration": round(t_out - t_in, 3),
                                                             "ease": "none", "immediateRender": False}), t_in)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vendor", default=os.path.join(HERE, "..", "assets", "vendor"),
                    help="GSAP, KaTeX, Lucide and three.js (default: the skill's assets/vendor)")
    ap.add_argument("--kit", default="", help="the kit's youtube-edit folder (for its gsap.min.js); found automatically when installed")
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        S = json.load(f)
    spec_dir = os.path.dirname(os.path.abspath(a.spec))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(spec_dir, p)
    out = a.out
    os.makedirs(out, exist_ok=True)
    try:
        tok = E.load_tokens(look=S.get("look"))       # latte by default; paper, the editorial look
    except ValueError as e:
        fail(str(e))
    E.use_look(tok)                                   # hero() and aside(): the faces the big words are set in
    mo, amb = tok["motion"], tok["ambient"]

    tpath, vpath = rel(S.get("transcript", "transcript.json")), rel(S.get("voice", "voice.wav"))
    spath = rel(S.get("script", "script.json"))
    source_keys = None
    if os.path.exists(spath):
        with open(spath, encoding="utf-8") as f:
            source_keys = set((json.load(f).get("sources") or {}).keys())
    if not os.path.exists(tpath):
        fail("no transcript at %s: run align-script.py first" % tpath)
    if not os.path.exists(vpath):
        fail("no voice at %s: run tts-kokoro.py first" % vpath)
    words = L.load_words(tpath)
    with wave.open(vpath) as w:
        voice_len = round(w.getnframes() / float(w.getframerate()), 3)
    D = round(voice_len + E.TAIL, 3)
    if voice_len > E.MAX_VOICE + 1e-6:
        fail("the voice is %.1f s, over the 90 s ceiling: trim the script (script-check.py --voice lists the lines to cut)"
             % voice_len)
    shutil.copy(vpath, os.path.join(out, "voice.wav"))

    # ---- the sound bed (sound.py): the pad or the creator's music, ducked under the voice, plus sound effects -----
    snd = S.get("sound") or {}
    music = snd.get("music", "pad")
    if music not in (None, "none", "pad"):
        if not os.path.isfile(rel(music)):
            fail("sound: no music file at %s (paths are relative to storyboard.json)" % music)
        music = rel(music)
    want_sfx = bool(snd.get("sfx", True))

    # ---- fonts and GSAP -------------------------------------------------------------------------------------------
    # DM Sans 500/700 and JetBrains Mono 500 ship with the skill (OFL, assets/fonts/): the scene heights are measured
    # with exactly these files (the Reels skill's dev/measure-glyphs.mjs), so a different copy would move every line break
    os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
    for name in FONT_FILES:
        src = os.path.join(FONTS, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(out, "fonts", name))
        else:
            print("WARN no %s in %s: text falls back to the system font and scene heights will be off" % (name, FONTS))
    kits = [a.kit] if a.kit else []
    kits += [os.path.join(HERE, "..", "..", "youtube-edit"), os.path.join(os.getcwd(), ".claude", "skills", "youtube-edit"),
             os.path.join(HERE, "..", "..", "..", "..", "kit", "youtube-edit")]
    kit = next((os.path.abspath(k) for k in kits if k and os.path.isdir(k)), None)
    gsap_src = GSAP_CDN
    for cand in [os.path.join(a.vendor, "gsap.min.js")] + ([os.path.join(kit, "assets", "vendor", "gsap.min.js")] if kit else []):
        if os.path.exists(cand):
            os.makedirs(os.path.join(out, "vendor"), exist_ok=True)
            shutil.copy(cand, os.path.join(out, "vendor", "gsap.min.js"))
            gsap_src = "vendor/gsap.min.js"
            break
    if gsap_src == GSAP_CDN:
        print("note: no local gsap.min.js (npm pack gsap@3.14.2); the page loads GSAP from the CDN (the first render needs internet)")

    # ---- scenes ---------------------------------------------------------------------------------------------------
    scenes = S.get("scenes") or fail("the storyboard has no scenes")
    seen, timed, builds = set(), [], {}
    bg = None
    for sc in scenes:
        sid = sc.get("id")
        if not sid or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", str(sid)):
            fail("%r: an id starts with a letter and holds only letters, digits and _ (the page derives <id>-... ids from it)" % (sid,))
        if RESERVED.match(str(sid)):
            fail("%s: the id is the page's own (stage, captions, voice, bg<n>, cap<n>); pick another" % sid)
        if sid in seen:
            fail("%s: the id is used twice" % sid)
        seen.add(sid)
        mod = REGISTRY.get(sc.get("type"))
        if not mod:
            fail("%s: unknown scene type %r (one of: %s)" % (sid, sc.get("type"), ", ".join(sorted(REGISTRY))))
        bg = sc.get("bg", bg or next(iter(tok["backgrounds"])))
        if bg not in tok["backgrounds"]:
            fail("%s: unknown bg %r (one of: %s)" % (sid, bg, ", ".join(tok["backgrounds"])))
        if sc.get("transition") is not None and sc["transition"] not in X.KINDS:
            fail("%s: unknown transition %r (one of: %s)" % (sid, sc["transition"], ", ".join(X.KINDS)))
        if (getattr(mod, "NEEDS_SOURCE", False) or shows_number(sc, decor=set(getattr(mod, "DECOR_KEYS", ())))) and not sc.get("source"):
            fail("%s: the %s scene shows a number or a claim and needs a source (a key in SOURCES.md)" % (sid, sc["type"]))
        if sc.get("source") and source_keys is not None and sc["source"] not in source_keys:
            fail("%s: source %r is not in script.json's sources (%s)" % (sid, sc["source"], ", ".join(sorted(source_keys)) or "none"))
        try:
            if hasattr(mod, "normalize"):
                mod.normalize(sc)
            errs = mod.validate(sc)
        except BAD_DATA as e:
            fail("%s: bad data in the %s scene (%s: %s)" % (sid, sc["type"], type(e).__name__, e))
        if sc["type"] == "custom":
            if sc.get("build") in builds:
                fail("%s: the build function %r is used by both %s and %s; give each custom scene its own (build<Id>)"
                     % (sid, sc["build"], builds[sc["build"]], sid))
            builds[sc.get("build")] = sid
        if errs:
            fail("%s: %s" % (sid, "; ".join(errs)))
        try:
            t_in = max(0.0, E.resolve(sc["in"], words, lead=True))
            if sc["out"] == "end" and sc is not scenes[-1]:
                fail("%s: only the last scene can run to the end" % sid)
            t_out = D if sc["out"] == "end" else min(D, E.resolve(sc["out"], words, lead=True))
        except KeyError as e:
            fail("%s: missing %s" % (sid, e))
        except ValueError as e:
            fail("%s: %s" % (sid, e))
        if t_out <= t_in:
            fail("%s: out (%s, %.2f s) is not after in (%s, %.2f s)" % (sid, sc["out"], t_out, sc["in"], t_in))
        timed.append((sc, mod, bg, t_in, t_out, t_out))          # the exit is over by the cut

    for (a1, _, _, s1, _, e1), (a2, _, _, s2, _, e2) in zip(timed, timed[1:]):
        if s2 < s1:
            fail("%s: it starts before %s, the scene listed ahead of it; list scenes in time order" % (a2["id"], a1["id"]))
        if s2 - e1 > GAP_MAX:
            fail("no scene from %.2f to %.2f s (between %s and %s); every moment of the voice needs a scene" % (e1, s2, a1["id"], a2["id"]))
        if e1 - s2 > E.MAX_OVERLAP + 1e-6:
            fail("%s and %s overlap by %.2f s: a scene ends where the next begins (its out is the next one's in); end %s "
                 "earlier" % (a1["id"], a2["id"], e1 - s2, a1["id"]))
    # a title that says what the voice is saying adds nothing the captions don't (PLAYBOOK §E5.5); the hook is meant to
    for sc, _, _, t_in, t_out, _ in timed[1:]:      # be read, so the first scene may
        if sc["type"] != "title" or t_out - t_in <= 2.0:
            continue
        said = {L.norm(w["text"]) for w in words if t_in - 0.3 <= w["start"] <= t_out}
        mine = [L.norm(w) for w in str(sc.get("text", "")).split() if L.norm(w)]
        if len(mine) >= 2 and sum(w in said for w in mine) >= 0.8 * len(mine):
            print("WARN %s: the title repeats what the voice is saying for %.1f s; show a picture of it instead (PLAYBOOK §E5.5)"
                  % (sc["id"], t_out - t_in))
    for (a1, m1, _, _, _, _), (a2, m2, _, _, _, _) in zip(timed, timed[1:]):   # no two beats with the same layout (MOTION.md)
        if m1.TYPE == m2.TYPE and m1.TYPE != "custom":
            print("WARN %s: the same layout (%s) as the scene before; change the picture, or merge the two into one build"
                  % (a2["id"], m2.TYPE))
    if timed[0][3] > GAP_MAX:
        fail("no scene from 0.00 to %.2f s: the first scene starts late%s" % (timed[0][3], (
            "; the voice's first word starts at %.2f s: trim its leading silence (the hook must be on screen by 1.0 s)"
            % words[0]["start"]) if words and words[0]["start"] - E.LEAD > GAP_MAX else ""))
    if timed[-1][5] < D - GAP_MAX:
        fail("no scene from %.2f to %.2f s: the last scene ends early (out at the end: %.3f)" % (timed[-1][5], D, D))

    # fonts load up front: a scene's text is hidden until its time, and a hidden face would load a frame late
    head = ['<link rel="preload" href="fonts/%s" as="font" type="font/woff2" crossorigin />' % f
            for f in sorted(os.listdir(os.path.join(out, "fonts")))] if os.path.isdir(os.path.join(out, "fonts")) else []
    css, hosts, js, tx_html, item_times = {}, [], [], [], []
    moments = {"duration": D, "look": tok["look"], "scenes": [], "spans": [], "items": []}   # every change on screen, for pace-check.py (gate E4)
    kinds, prev = [], None    # how each scene comes in (transitions.py): the storyboard's choice or the composer's
    for k, (sc, _, sbg, _, _, _) in enumerate(timed):
        kinds.append(X.pick(k, prev, sbg, sc.get("transition"), tok["look"]))
        prev = sbg
    for k, (sc, mod, sbg, t_in, t_out, end) in enumerate(timed):
        sid = sc["id"]
        ctx = Ctx(sc, t_in, t_out, words, tok, a.vendor, out, sbg, head, spec_dir)
        try:
            hl = sc.get("headline")
            if hl is not None:
                errs = HL.validate(hl) or (["a %s scene places itself: give it no headline" % mod.TYPE] if hasattr(mod, "place") else [])
                if errs:
                    fail("%s: %s" % (sid, "; ".join(errs)))
                hl_h = HL.layout(hl)["height"]
                left, top, width, h, iw, ih, scale = place(sid, mod, sc, E.SCENE["top"] + hl_h + HL.GAP)
            else:
                left, top, width, h, iw, ih, scale = place(sid, mod, sc)
            inner, lines = mod.render(sc, ctx, (left, top, iw))
            hl_html = ""
            if hl is not None:      # top-left in the frame, inside the box (it leaves with the scene), outside the camera
                hl_html, hl_js = HL.render(hl, ctx, WIDE[0] - left, E.SCENE["top"] - top)
                lines = lines + hl_js
                css["headline"] = HL.CSS
        except SceneError as e:
            fail("%s: %s" % (sid, e))
        except BAD_DATA as e:
            fail("%s: bad data in the %s scene (%s: %s)" % (sid, sc["type"], type(e).__name__, e))
        moments["scenes"].append({"id": sid, "type": mod.TYPE, "in": round(t_in, 3), "out": round(t_out, 3),
                                  "box": [left, top, width, h], "scale": scale,
                                  "travels": bool(getattr(mod, "travels", lambda s: False)(sc))})
        if hl is not None:
            moments["scenes"][-1]["headline"] = [WIDE[0], E.SCENE["top"], HL.WIDTH, hl_h]
        if mod.TYPE == "custom":   # it animates itself between in and out
            moments["spans"].append([round(t_in, 3), round(t_out, 3)])
        css[mod.TYPE] = mod.CSS
        starts = [s_ for s_, _ in filter(None, map(line_span, lines))]
        if mod.TYPE != "custom" and starts and min(starts) - t_in > 0.8:   # the scene's own first change, not its transition
            print("WARN %s: nothing shows for %.1f s after the scene starts; put something on its first word (PLAYBOOK §E4.9)"
                  % (sid, min(starts) - t_in))
        mine = [float(x) for x in re.findall(r'data-at="([\d.]+)"', inner + hl_html)]
        if k == 0 and mine and max(mine) > E.HOOK_BY + 1e-6:
            late = words[0]["start"] - E.LEAD > E.HOOK_BY if words else False
            fail("%s: the hook is not whole on screen by 1.0 s: an item lands at %.2f s (every hook item by %.1f s); %s (SOP S8)"
                 % (sid, max(mine), E.HOOK_BY, "the voice's first word starts at %.2f s: trim its leading silence" % words[0]["start"]
                    if late else "anchor the hook's pieces to word 0 or 1"))
        item_times += mine
        reads = Reads(inner + hl_html).out or [(t_in, html.unescape(re.sub(r"<[^>]+>", " ", inner)))]   # no timed items: the scene is one read
        for t_, text_ in reads:                          # items landing together are one stagger, one read
            moments["items"].append({"scene": sid, "t": round(t_, 3), "text": " ".join(text_.split())[:80],
                                     "group": "%s@%.3f" % (sid, t_), "number": mod.TYPE in NUMBER_TYPES})
        lines = X.enter(kinds[k], sid, t_in) + lines
        if kinds[k] == "burst":
            spray, spray_js = X.burst(k, t_in, [f for f, _ in E.theme(tok, sbg)["series"]])
            tx_html.append(spray)
            lines += spray_js
        elif kinds[k] == "brush":
            th_ = E.theme(tok, timed[k - 1][2] if k else sbg)   # the outgoing ground's ink: the bands show over it
            bands, band_js = X.brush(k, t_in, [th_["accent"], th_["ink"]])
            tx_html.append(bands)
            lines += band_js
        word = E.anchor_text(sc["in"], words)
        anchor = ' data-unanchored="1"' if word == "-" else ' data-anchor="%s"' % html.escape(word, quote=True)
        hosts.append('    <div class="card-host clip" id="host-%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s\n'
                     '      style="left:0;top:0;width:1080px;height:1920px;visibility:hidden;">'
                     '<div class="box" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s<div class="cam" id="%s-cam"><div class="live" id="%s-live"%s style="width:%dpx;height:%dpx;transform:scale(%s)">%s</div></div></div></div>\n'
                     % (sid, t_in, end - t_in, 3 + k, anchor, sid, left, top, width, h, hl_html, sid, sid, ' data-baked="1"' if getattr(mod, "BAKED", False) else "", iw, ih, ("%.2f" % scale).rstrip("0").rstrip(".") if scale != 1 else "1", inner))
        js.append("// %s (%s) %.2f to %.2f s" % (sid, mod.TYPE, t_in, t_out))
        js.extend(lines)
        js.extend(ctx.ambient_lines)
        if mod.TYPE != "custom":         # a custom scene moves itself
            js.append(camera(sid, k, t_in, t_out, tok, cam_from(mod, scale, tok)))
        if t_out < D - 1e-6:
            gone = X.exit(kinds[k + 1] if k + 1 < len(kinds) else "fade", sid, t_out)
        else:                            # the last scene leaves too, onto the hook's ground (the loop seams into the hook)
            gone = X.close(sid, D)
        lines = lines + gone
        js.extend(gone)
        moments["spans"] += [[round(a_, 3), round(b_, 3)] for a_, b_ in filter(None, map(line_span, lines))]

    hero = E.hero()
    if hero["family"] != "DM Sans":       # the look's hero face on every scene's big words (latte keeps DM Sans 700)
        sel = sorted({m_.HERO_CSS for _, m_, _, _, _, _ in timed if getattr(m_, "HERO_CSS", None)})
        if sel:
            css["~hero"] = "  %s { font-family:'%s'; font-stretch:%s; font-weight:%d; }\n" % (", ".join(sel), hero["family"], hero["stretch"], hero["weight"])

    # ---- backgrounds ----------------------------------------------------------------------------------------------
    bgs, bg_js = [], []
    for k, (sc, _, sbg, t_in, _, _) in enumerate(timed):
        if not bgs or bgs[-1][0] != sbg:
            if bgs and kinds[k] == "wipe":     # the new background opens as a circle
                bg_js += X.wipe_bg("bg%d" % len(bgs), t_in)
            elif bgs and kinds[k] == "brush":  # the new background swaps under the bands' full cover
                bg_js.append("tl.set('#bg%d', { opacity: 1 }, %.3f);" % (len(bgs), t_in))
            elif bgs:
                bg_js.append("tl.to('#bg%d', { opacity: 1, duration: %.3f, ease: 'power1.inOut' }, %.3f);" % (len(bgs), E.BG_FADE, t_in))
            bgs.append((sbg, t_in))
    if bgs[-1][0] != bgs[0][0]:                  # the close ends on the hook's ground
        bg_js += X.wipe_bg("bg%d" % len(bgs), D - X.CLOSE, X.CLOSE)
        bgs.append((bgs[0][0], D - X.CLOSE))
    layer_of, cuts = [], {}
    for k, (sc, _, sbg, t_in, _, _) in enumerate(timed):     # the layer each scene is on, and the cuts inside each layer
        i = max(j for j, (_, t0) in enumerate(bgs) if t0 <= t_in + 1e-6)
        if k and layer_of[-1] == i:
            cuts.setdefault(i, []).append(t_in)
        layer_of.append(i)
    textured = tok["look"] == "paper" and any(b == "base" for b, _ in bgs)   # the paper look's base ground is paper
    if textured:
        os.makedirs(os.path.join(out, "assets"), exist_ok=True)
        shutil.copy(paper.SHIPPED if os.path.exists(paper.SHIPPED) else paper.texture(paper.SHIPPED), os.path.join(out, "assets", "paper.png"))
    bg_html = "".join('    <div class="bg" id="bg%d" style="background:%s%s;opacity:%d">%s%s</div>\n'
                      % (i, E.theme(tok, b)["bg"], " url(assets/paper.png) 0 0 / 1080px 1920px" if textured and b == "base" else "", 0 if i else 1, glows(i, b, tok, cuts.get(i, []), bg_js), particles(i, b, tok, D, bg_js))
                      for i, (b, _) in enumerate(bgs))

    def bg_at(t):
        cur = timed[0][2]
        for _, _, sbg, t_in, _, _ in timed:
            if t_in <= t + 1e-6:
                cur = sbg
        return cur

    # ---- the thread: one line through the reel, above the ground, under the scenes ------------------------------------
    if S.get("thread") is not None:
        errs = TH.validate(S["thread"], words)
        if errs:
            fail("thread: " + "; ".join(errs))
        th_html, th_js, th_spans = TH.render(S["thread"], words, tok, D, bg_at, [t_in for _, _, _, t_in, _, _ in timed])
        bg_html += th_html
        bg_js += th_js
        moments["spans"] += th_spans
        css["~thread"] = TH.CSS

    # ---- boil: strokes wobble as if drawn by hand (the paper look), an ambient seed walk, never on text -----------
    if tok["motion"].get("boil"):
        bg_html += ('    <svg width="0" height="0" style="position:absolute"><filter id="boil" x="-5%" y="-5%" width="110%" height="110%">'
                    '<feTurbulence id="boil-turb" type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="14"/>'
                    '<feDisplacementMap in="SourceGraphic" scale="2.5" xChannelSelector="R" yChannelSelector="G"/></filter></svg>\n')
        bg_js.append("tl.fromTo({ v: 0 }, { v: 0 }, { v: 1, duration: %.3f, ease: 'none', immediateRender: false, onUpdate: function () { "
                     "document.getElementById('boil-turb').setAttribute('seed', (Math.floor(tl.time() * 12) * 7919 + 13) %% 997 + 1); } }, 0);" % D)
        css["~boil"] = '  html:not([data-boil="off"]) .boil { filter:url(#boil); }\n'

    # ---- captions -------------------------------------------------------------------------------------------------
    C = S.get("captions", {}) or {}
    em = {L.norm(x) for x in C.get("emphasis", [])}
    chunks = L.chunk_words([w for w in words if w["start"] < D], 4, 24)
    giant = [(t_in, t_out) for sc, m_, _, t_in, t_out, _ in timed if m_.TYPE == "giant-captions"]
    # while giant captions run, the words are the picture: the band steps aside, never the same words twice
    chunks = [ch for ch in chunks if not any(a - 1e-3 <= ch["start"] < b - 1e-3 for a, b in giant)]
    caps, cap_js = [], []
    for i, ch in enumerate(chunks):
        b = bg_at(ch["start"])
        th = E.theme(tok, b)
        dim, on, hl = th["muted"], th["ink"], th["highlight"]      # a word not yet said, a word said, an emphasised word
        spans = []
        for j, w in enumerate(ch["words"]):
            cid = "cw%d-%d" % (i, j)
            if L.norm(w["text"]) in em:
                hd = ' style="background:%s;border-color:%s"' % (hl["handle"], hl["handle_border"])   # the chip's handles, on its ground
                spans.append('<span class="cw em" id="%s"><i class="hd a"%s></i><i class="hd b"%s></i>%s</span>' % (cid, hd, hd, html.escape(w["text"])))
                cap_js.append("tl.set('#%s', { backgroundColor: '%s', color: '%s' }, %.3f);" % (cid, hl["fill"], hl["text"], w["start"]))
                cap_js.append("tl.set('#%s .hd', { opacity: 1 }, %.3f);" % (cid, w["start"]))
            else:
                spans.append('<span class="cw" id="%s">%s</span>' % (cid, html.escape(w["text"])))
                cap_js.append("tl.set('#%s', { color: '%s' }, %.3f);" % (cid, on, w["start"]))
        halo = "text-shadow:0 0 18px %s, 0 0 6px %s" % (th["bg"], th["bg"])   # legible over a shape passing behind
        caps.append('      <div class="cap" id="cap%d" style="color:%s;%s">%s</div>\n' % (i, dim, halo, " ".join(spans)))
        cap_js.append("tl.set('#cap%d', { visibility: 'visible' }, %.3f);" % (i, ch["start"]))
        cap_js.append("tl.fromTo('#cap%d', { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.12, ease: '%s', immediateRender: false }, %.3f);"
                      % (i, mo["enter_ease"], ch["start"]))
        cap_js.append("tl.set('#cap%d', { visibility: 'hidden' }, %.3f);" % (i, ch["end"]))

    band_top, band_bottom = E.CAPTION_BAND
    stage_bg = E.theme(tok, timed[0][2])["bg"]
    CSS = """
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-500.woff2") format("woff2"); font-weight: 500; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-700.woff2") format("woff2"); font-weight: 700; font-display: block; }
  @font-face { font-family: "Archivo"; src: url("fonts/Archivo-wdth.woff2") format("woff2"); font-weight: 100 900; font-stretch: 62%% 125%%; font-display: block; }
  @font-face { font-family: "Instrument Serif"; src: url("fonts/InstrumentSerif-Italic.woff2") format("woff2"); font-weight: 400; font-style: italic; font-display: block; }
  @font-face { font-family: "JetBrains Mono"; src: url("%s") format("woff2"); font-weight: 500; font-display: block; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; width:100%%; height:100%%; overflow:hidden; background:%s; }
  #stage { position:relative; width:1080px; height:1920px; overflow:hidden; background:%s; font-family: %s; --label: %s; }
  .bg { position:absolute; inset:0; overflow:hidden; }
  .orb { position:absolute; border-radius:50%%; pointer-events:none; will-change:transform; }
  .pt { position:absolute; pointer-events:none; will-change:transform; }
  .cam { position:absolute; left:0; top:0; width:100%%; height:100%%; transform-origin:50%% 50%%; will-change:transform; }
  .live { position:absolute; left:0; top:0; transform-origin:0 0; display:flex; flex-direction:column; align-items:center; justify-content:center; will-change:transform; }
  .card-host { position:absolute; pointer-events:none; overflow:hidden; z-index:10; }
  .tx-layer { position:absolute; inset:0; z-index:20; pointer-events:none; overflow:hidden; }
  .tx-p { position:absolute; opacity:0; border-radius:5px; will-change:transform; }
  .box { position:absolute; display:flex; flex-direction:column; align-items:center; justify-content:center; perspective:1800px; }
  .brand { position:absolute; left:%dpx; width:%dpx; z-index:31; display:flex; align-items:center; justify-content:space-between;
    font-family: var(--label); font-weight:500; font-size:30px; letter-spacing:.06em; pointer-events:none; }
  .cap-layer { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:30; pointer-events:none; }
  .cap { position:absolute; left:%dpx; width:%dpx; top:%dpx; height:%dpx; display:flex; align-items:center; justify-content:center;
    flex-wrap:wrap; gap:0 .26em; visibility:hidden; font-weight:700; font-size:%dpx; line-height:52px; letter-spacing:-.01em;
    text-align:center; }
  .cap .cw { position:relative; display:inline-block; padding:0 .14em; border-radius:6px; }
  .cap .cw.em { transform: scale(1.12); margin:0 .1em; }
  .cap .hd { position:absolute; width:14px; height:14px; border:3px solid; opacity:0; }
  .cap .hd.a { left:-7px; top:-7px; } .cap .hd.b { right:-7px; bottom:-7px; }
%s""" % (tok["fonts"]["label_file"], stage_bg, stage_bg, tok["fonts"]["display"], tok["fonts"]["label"], WIDE[0], WIDE[1], NARROW[0], NARROW[1], band_top,
         band_bottom - band_top, CAP_SIZE, "".join(css.values()))

    HELPERS = """
        const countUp = function (sel, from, to, t, dur, prefix, suffix, dec) {   // the page starts at fmt(first from)
          const el = document.querySelector(sel); const o = { v: from };
          const fmt = function (v) { return prefix + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suffix; };
          tl.to(o, { v: to, duration: dur, ease: '%s', onUpdate: function () { el.textContent = fmt(dec ? o.v : Math.round(o.v)); } }, t);
        };""" % mo["enter_ease"]

    cap_html = ('    <div class="clip cap-layer" id="captions" data-start="0" data-duration="%.3f" data-track-index="2">\n%s    </div>\n'
                % (D, "".join(caps)))
    bed = ""
    if music in (None, "none") and not want_sfx:
        pass
    elif music not in (None, "none") and not shutil.which("ffmpeg"):
        print("WARN no ffmpeg on PATH: the reel has no music bed (install FFmpeg, or set \"sound\": {\"music\": \"none\"})")
    else:
        chimes = [E.resolve(sc["in"], words) for sc, _, _, _, _, _ in timed if sc.get("chime")]    # on the word itself
        evs = sound.events([(kinds[k], timed[k][3]) for k in range(1, len(timed))], item_times, chimes) if want_sfx else []
        moments["sounds"] = [[t, kind] for t, kind in evs]
        sound.mix_bed(os.path.join(out, "voice.wav"), None if music in (None, "none") else (sound.pad_file() if music == "pad" else music),
                      evs, D, os.path.join(out, "bed.wav"), float(snd.get("music_db", -22)), stems=out)
        bed = ('    <audio id="bed" src="bed.wav" data-start="0" data-duration="%.3f" data-track-index="40" data-volume="1"></audio>\n' % D)
    brand = S.get("brand") or {}
    if brand.get("handle") or brand.get("part"):
        # a visual identity on every frame and a series the viewer can follow: the handle left, "PART n" right, quiet,
        # in the safe area above the caption band
        part = ("PART %s" % brand["part"]) if brand.get("part") else ""
        cap_html = ('    <div class="brand" id="brand" style="top:%dpx;height:%dpx;color:%s"><span>%s</span><span>%s</span></div>\n'
                    % (BRAND_TOP, BRAND_H, E.theme(tok, timed[0][2])["muted"], html.escape(str(brand.get("handle", ""))),
                       html.escape(part))) + cap_html
        for b, t0 in bgs[1:]:          # it takes each ground's quiet colour as the ground changes (3:1 on all four)
            cap_js.append("tl.set('#brand', { color: '%s' }, %.3f);" % (E.theme(tok, b)["muted"], t0))
    if tx_html:   # transition sprays sit above the scenes, under the captions
        cap_html = '    <div class="tx-layer" id="tx">%s</div>\n' % "".join(tx_html) + cap_html
    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>%s</style>
%s</head>
<body>
  <div id="stage" data-composition-id="%s" data-start="0" data-duration="%.3f" data-fps="60" data-width="1080" data-height="1920">
%s    <audio id="voice" src="voice.wav" data-start="0" data-duration="%.3f" data-track-index="1" data-volume="1"></audio>
%s%s%s
    <script src="%s"></script>
    <script>
      (function () {
        const tl = window.gsap.timeline({ paused: true });
%s
        // backgrounds
        %s

        // scenes
        %s

        // captions
        %s

        tl.to({}, { duration: %.3f }, 0);
        window.__timelines = window.__timelines || {};
        window.__timelines[%s] = tl;
      })();
    </script>
  </div>
</body>
</html>
""" % (CSS, "".join(h + "\n" for h in head), html.escape(str(S["id"]), quote=True), D, bg_html, voice_len, bed, "".join(hosts), cap_html, gsap_src, HELPERS,
       "\n        ".join(bg_js), "\n        ".join(js), "\n        ".join(cap_js), D, js_str(S["id"]))
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    moments["spans"].sort()
    with open(os.path.join(out, "moments.json"), "w", encoding="utf-8") as f:
        json.dump(moments, f, indent=1)
    with open(os.path.join(out, "hyperframes.json"), "w", encoding="utf-8") as f:
        json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                   "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                   "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                   "media": {"autoProxy": True}}, f, indent=2)
    print("E3 PASS: wrote %s/index.html: 1080x1920 at 60 fps, %.2f s, %d scenes, %d backgrounds, %d caption phrases"
          % (out, D, len(timed), len(bgs), len(chunks)))
    print("snapshot moments:", " ".join("%.2f" % min(D, t_in + 0.6) for _, _, _, t_in, _, _ in timed))


if __name__ == "__main__":
    main()
