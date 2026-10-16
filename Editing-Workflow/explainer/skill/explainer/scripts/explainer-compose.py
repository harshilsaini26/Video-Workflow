#!/usr/bin/env python3
"""explainer-compose.py: build public/index.html for an explainer reel (1080x1920, 60 fps) from storyboard.json (gate E3).

  explainer-compose.py --spec videos/<p>/storyboard.json --out videos/<p>/public [--vendor DIR] [--kit DIR]

The page has three layers (SPEC §6.1): a background that cross-fades when a scene's `bg` changes, one scene at a time
centred in the scene area (x 65 to 1015, y 520 to 1248; 780 px wide when it reaches below y 960), and word captions in
the band at y 330 to 470. Scene times are word anchors ("word:N" in transcript.json); an entrance lands 0.2 s before
its word. Each scene exits on its `out` while the next one enters, overlapping by the exit's 0.28 s.

The markup is the kit's: card-host clips with data-anchor, items with data-at, the caption layer marked cap-layer, the
voice as an <audio> clip, one paused GSAP timeline in window.__timelines, so beat-check.py, gap-scan.py, snap-beats.py
and verify-render.py read it unchanged.

Fails (exit 1, "E3 FAIL: <scene id>: ...") on: an unknown type or bad id, a scene that does not fit the scene area or
has a word wider than its column, an anchor that does not resolve or runs backwards, an item outside its scene, a
number with no source, more than 0.3 s with no scene (at the start, between scenes or at the end), or two scenes
overlapping by more than 0.3 s.
"""
import argparse, html, json, os, random, re, shutil, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explainer_lib as E
import sound
import transitions as X
from scenes import REGISTRY, Ctx, SceneError, js_obj, js_str

L = E.L
WIDE = (L.SAFE["left"], L.SAFE["right"] - L.SAFE["left"])          # 65, 950
NARROW = (L.NARROW["left"], L.NARROW["right"] - L.NARROW["left"])  # 150, 780
CENTRE = (E.SCENE["top"] + E.SCENE["bottom"]) // 2                 # 884
GAP_MAX = 0.3
GSAP_CDN = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
FONTS = os.path.join(HERE, "..", "assets", "fonts")
FONT_FILES = ("DMSans-500.woff2", "DMSans-700.woff2", "JetBrainsMono-500.woff2")
CAP_SIZE = 64


def fail(msg):
    print("E3 FAIL: " + msg)
    sys.exit(1)


RESERVED = re.compile(r"^(stage|captions|voice|bg\d+|cap\d+)$")
NOT_SHOWN = {"type", "id", "bg", "in", "out", "at", "source", "icon", "html", "build", "tex", "style", "unit",
             "n", "size", "decimals", "point", "row", "cell", "box", "hi", "value", "points",
             "card", "side", "transition", "badge", "logo", "src", "screenshot"}   # settings, indexes, step numbers, files
BAD_DATA = (TypeError, ValueError, KeyError, AttributeError, IndexError)


def shows_number(node, key=None):
    """True when any text the scene puts on screen has a digit, %, or a currency sign (formula TeX aside)."""
    if key in NOT_SHOWN:
        return False
    if isinstance(node, str):
        return bool(re.search(r"[\d%$€£₹]", node))
    if isinstance(node, (int, float)) and not isinstance(node, bool):   # 1500000 in a sheet is on screen too
        return True
    if isinstance(node, dict):
        return any(shows_number(v, k) for k, v in node.items())
    if isinstance(node, list):
        return any(shows_number(v, key) for v in node)
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


def place(sid, mod, scene):
    """(left, top, width, height): centred in the scene area, narrow when it reaches the action column band.
    A scene that brings its own box (custom) is only checked."""
    if hasattr(mod, "place"):
        left, top, width, h = mod.place(scene)
        sa = E.SCENE
        if left < sa["left"] or top < sa["top"] or left + width > sa["right"] or top + h > sa["bottom"] or not L.inside_safe(left, top, width, h):
            fail("%s: the box %d,%d %dx%d is outside the scene area (x %d to %d, y %d to %d; x %d to %d below y %d)"
                 % (sid, left, top, width, h, sa["left"], sa["right"], sa["top"], sa["bottom"], L.NARROW["left"], L.NARROW["right"], L.RIGHT_COL_TOP))
        return left, top, width, h
    left, width = WIDE
    h = mod.height(scene, width)
    if CENTRE + h / 2 > L.RIGHT_COL_TOP:
        left, width = NARROW
        h = mod.height(scene, width)
    top = int(round(CENTRE - h / 2))
    if h > E.SCENE["bottom"] - E.SCENE["top"]:
        fail("%s: the scene is %d px tall, taller than the scene area (%d px); use less text or split it"
             % (sid, h, E.SCENE["bottom"] - E.SCENE["top"]))
    if not L.inside_safe(left, top, width, h):
        fail("%s: the box %d,%d %dx%d is outside the safe zone" % (sid, left, top, width, h))
    need = mod.min_width(scene)
    if need > width:
        fail("%s: a word or a number in it (at its widest as it counts) is about %d px wide, wider than the %d px column; "
             "shorten it or use a smaller size" % (sid, need, width))
    return left, top, width, h


def orbs(D, bgs, amb, bg_js):
    """Three soft glows behind the scenes that drift for the whole reel (ambient: never a change for pace-check). Their
    path is fixed by a seed, so every render of the page is the same; their strength follows the background."""
    every = float(amb["drift_every"])
    html_ = []
    for k, col in enumerate(amb["orbs"]):
        rng = random.Random(7 + k)
        x0, y0 = rng.randint(-300, 480), rng.randint(-200, 1300)
        html_.append('<i class="orb" id="orb%d" style="left:%dpx;top:%dpx;background:radial-gradient(circle, %s 0%%, transparent 65%%)"></i>'
                     % (k, x0, y0, col))
        t = 0.0
        while t < D - 1e-6:
            bg_js.append("tl.to('#orb%d', %s, %.3f);" % (k, js_obj({"x": rng.randint(-260, 260), "y": rng.randint(-360, 360),
                                                                   "duration": every, "ease": "sine.inOut"}), t))
            t += every
    op = amb["orb_opacity"]
    for b, t_in in bgs[1:]:
        bg_js.append("tl.to('#orbs', %s, %.3f);" % (js_obj({"opacity": op[b], "duration": E.BG_FADE, "ease": "power1.inOut"}), t_in))
    return '    <div class="orbs" id="orbs" style="opacity:%s">%s</div>\n' % (op[bgs[0][0]], "".join(html_))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vendor", default=os.path.join(HERE, "..", "assets", "vendor"),
                    help="GSAP, KaTeX, Lucide and three.js (default: the skill's assets/vendor)")
    ap.add_argument("--kit", default="", help="the kit's youtube-edit folder (for its gsap.min.js); found automatically when installed")
    a = ap.parse_args()

    with open(a.spec) as f:
        S = json.load(f)
    spec_dir = os.path.dirname(os.path.abspath(a.spec))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(spec_dir, p)
    out = a.out
    os.makedirs(out, exist_ok=True)
    tok = E.load_tokens()
    mo, amb = tok["motion"], tok["ambient"]

    tpath, vpath = rel(S.get("transcript", "transcript.json")), rel(S.get("voice", "voice.wav"))
    spath = rel(S.get("script", "script.json"))
    source_keys = None
    if os.path.exists(spath):
        with open(spath) as f:
            source_keys = set((json.load(f).get("sources") or {}).keys())
    if not os.path.exists(tpath):
        fail("no transcript at %s: run align-script.py first" % tpath)
    if not os.path.exists(vpath):
        fail("no voice at %s: run tts-kokoro.py first" % vpath)
    words = L.load_words(tpath)
    with wave.open(vpath) as w:
        voice_len = round(w.getnframes() / float(w.getframerate()), 3)
    D = round(voice_len + E.TAIL, 3)
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
        bg = sc.get("bg", bg or "blue")
        if bg not in tok["backgrounds"]:
            fail("%s: unknown bg %r (one of: %s)" % (sid, bg, ", ".join(tok["backgrounds"])))
        if sc.get("transition") is not None and sc["transition"] not in X.KINDS:
            fail("%s: unknown transition %r (one of: %s)" % (sid, sc["transition"], ", ".join(X.KINDS)))
        if (getattr(mod, "NEEDS_SOURCE", False) or shows_number(sc)) and not sc.get("source"):
            fail("%s: the %s scene shows a number or a claim and needs a source (a key in SOURCES.md)" % (sid, sc["type"]))
        if sc.get("source") and source_keys is not None and sc["source"] not in source_keys:
            fail("%s: source %r is not in script.json's sources (%s)" % (sid, sc["source"], ", ".join(sorted(source_keys)) or "none"))
        try:
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
        timed.append((sc, mod, bg, t_in, t_out, min(D, t_out + mo["exit"])))

    for (a1, _, _, s1, _, e1), (a2, _, _, s2, _, e2) in zip(timed, timed[1:]):
        if s2 < s1:
            fail("%s: it starts before %s, the scene listed ahead of it; list scenes in time order" % (a2["id"], a1["id"]))
        if s2 - e1 > GAP_MAX:
            fail("no scene from %.2f to %.2f s (between %s and %s); every moment of the voice needs a scene" % (e1, s2, a1["id"], a2["id"]))
        if e1 - s2 > GAP_MAX + 1e-6:
            fail("%s and %s overlap by %.2f s (at most %.1f): end %s earlier" % (a1["id"], a2["id"], e1 - s2, GAP_MAX, a1["id"]))
    if timed[0][3] > GAP_MAX:
        fail("no scene from 0.00 to %.2f s: the first scene starts late" % timed[0][3])
    if timed[-1][5] < D - GAP_MAX:
        fail("no scene from %.2f to %.2f s: the last scene ends early (out at the end: %.3f)" % (timed[-1][5], D, D))

    # fonts load up front: a scene's text is hidden until its time, and a hidden face would load a frame late
    head = ['<link rel="preload" href="fonts/%s" as="font" type="font/woff2" crossorigin />' % f
            for f in sorted(os.listdir(os.path.join(out, "fonts")))] if os.path.isdir(os.path.join(out, "fonts")) else []
    css, hosts, js, tx_html, item_times = {}, [], [], [], []
    moments = {"duration": D, "scenes": [], "spans": []}   # every change on screen, for pace-check.py (gate E4)
    kinds, prev = [], None    # how each scene comes in (transitions.py): the storyboard's choice or the composer's
    for k, (sc, _, sbg, _, _, _) in enumerate(timed):
        kinds.append(X.pick(k, prev, sbg, sc.get("transition")))
        prev = sbg
    for k, (sc, mod, sbg, t_in, t_out, end) in enumerate(timed):
        sid = sc["id"]
        ctx = Ctx(sc, t_in, t_out, words, tok, a.vendor, out, sbg, head, spec_dir)
        try:
            left, top, width, h = place(sid, mod, sc)
            inner, lines = mod.render(sc, ctx, (left, top, width))
        except SceneError as e:
            fail("%s: %s" % (sid, e))
        except BAD_DATA as e:
            fail("%s: bad data in the %s scene (%s: %s)" % (sid, sc["type"], type(e).__name__, e))
        moments["scenes"].append({"id": sid, "type": mod.TYPE, "in": round(t_in, 3), "out": round(t_out, 3)})
        if mod.TYPE == "custom":   # it animates itself between in and out
            moments["spans"].append([round(t_in, 3), round(t_out, 3)])
        css[mod.TYPE] = mod.CSS
        item_times += [float(x) for x in re.findall(r'data-at="([\d.]+)"', inner)]
        lines = X.enter(kinds[k], sid, t_in) + lines
        if kinds[k] == "burst":
            c = tok["colors"]
            spray, spray_js = X.burst(k, t_in, [c["cyan"], c["amber"], c["magenta"], c["white"]])
            tx_html.append(spray)
            lines += spray_js
        word = E.anchor_text(sc["in"], words)
        anchor = ' data-unanchored="1"' if word == "-" else ' data-anchor="%s"' % html.escape(word, quote=True)
        hosts.append('    <div class="card-host clip" id="host-%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s\n'
                     '      style="left:0;top:0;width:1080px;height:1920px;visibility:hidden;">'
                     '<div class="box" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><div class="live" id="%s-live">%s</div></div></div>\n'
                     % (sid, t_in, end - t_in, 3 + k, anchor, sid, left, top, width, h, sid, inner))
        js.append("// %s (%s) %.2f to %.2f s" % (sid, mod.TYPE, t_in, t_out))
        js.extend(lines)
        # the living layer: the scene pushes in slowly for as long as it is on screen (ambient: not a change)
        js.append("tl.fromTo('#%s-live', { scale: 1 }, %s, %.3f);" % (sid, js_obj({"scale": amb["push"], "duration": round(end - t_in, 3),
                                                                                  "ease": "sine.inOut", "immediateRender": False}), t_in))
        js.extend(ctx.ambient_lines)
        if t_out < D - 1e-6:
            gone = X.exit(kinds[k + 1] if k + 1 < len(kinds) else "fade", sid, t_out)
            lines = lines + gone
            js.extend(gone)
        moments["spans"] += [[round(a_, 3), round(b_, 3)] for a_, b_ in filter(None, map(line_span, lines))]

    # ---- backgrounds ----------------------------------------------------------------------------------------------
    bgs, bg_js = [], []
    for k, (sc, _, sbg, t_in, _, _) in enumerate(timed):
        if not bgs or bgs[-1][0] != sbg:
            if bgs and kinds[k] == "wipe":     # the new background opens as a circle
                bg_js += X.wipe_bg("bg%d" % len(bgs), t_in)
            elif bgs:
                bg_js.append("tl.to('#bg%d', { opacity: 1, duration: %.3f, ease: 'power1.inOut' }, %.3f);" % (len(bgs), E.BG_FADE, t_in))
            bgs.append((sbg, t_in))
    bg_html = "".join('    <div class="bg" id="bg%d" style="background:%s;opacity:%d"></div>\n' % (i, tok["backgrounds"][b], 0 if i else 1)
                      for i, (b, _) in enumerate(bgs))
    bg_html += orbs(D, bgs, amb, bg_js)

    def bg_at(t):
        cur = timed[0][2]
        for _, _, sbg, t_in, _, _ in timed:
            if t_in <= t + 1e-6:
                cur = sbg
        return cur

    # ---- captions -------------------------------------------------------------------------------------------------
    C = S.get("captions", {}) or {}
    em = {L.norm(x) for x in C.get("emphasis", [])}
    hl = tok["highlight"]
    chunks = L.chunk_words([w for w in words if w["start"] < D], 4, 24)
    caps, cap_js = [], []
    for i, ch in enumerate(chunks):
        b = bg_at(ch["start"])
        dim = tok["colors"]["dim_light" if b == "light" else "dim"]
        on = tok["text_on"][b]
        spans = []
        for j, w in enumerate(ch["words"]):
            cid = "cw%d-%d" % (i, j)
            if L.norm(w["text"]) in em:
                spans.append('<span class="cw em" id="%s"><i class="hd a"></i><i class="hd b"></i>%s</span>' % (cid, html.escape(w["text"])))
                cap_js.append("tl.set('#%s', { backgroundColor: '%s', color: '%s' }, %.3f);" % (cid, hl["fill"], hl["text"], w["start"]))
                cap_js.append("tl.set('#%s .hd', { opacity: 1 }, %.3f);" % (cid, w["start"]))
            else:
                spans.append('<span class="cw" id="%s">%s</span>' % (cid, html.escape(w["text"])))
                cap_js.append("tl.set('#%s', { color: '%s' }, %.3f);" % (cid, on, w["start"]))
        caps.append('      <div class="cap%s" id="cap%d" style="color:%s">%s</div>\n' % (" on-light" if b == "light" else "", i, dim, " ".join(spans)))
        cap_js.append("tl.set('#cap%d', { visibility: 'visible' }, %.3f);" % (i, ch["start"]))
        cap_js.append("tl.fromTo('#cap%d', { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.12, ease: '%s', immediateRender: false }, %.3f);"
                      % (i, mo["enter_ease"], ch["start"]))
        cap_js.append("tl.set('#cap%d', { visibility: 'hidden' }, %.3f);" % (i, ch["end"]))

    band_top, band_bottom = E.CAPTION_BAND
    CSS = """
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-500.woff2") format("woff2"); font-weight: 500; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-700.woff2") format("woff2"); font-weight: 700; font-display: block; }
  @font-face { font-family: "JetBrains Mono"; src: url("%s") format("woff2"); font-weight: 500; font-display: block; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; width:100%%; height:100%%; overflow:hidden; background:#000; }
  #stage { position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family: %s; --label: %s; }
  .bg { position:absolute; inset:0; }
  .orbs { position:absolute; inset:0; z-index:1; pointer-events:none; }
  .orb { position:absolute; width:900px; height:900px; border-radius:50%%; will-change:transform; }
  .live { width:100%%; height:100%%; display:flex; flex-direction:column; align-items:center; justify-content:center; will-change:transform; }
  .card-host { position:absolute; pointer-events:none; overflow:hidden; z-index:10; }
  .tx-layer { position:absolute; inset:0; z-index:20; pointer-events:none; overflow:hidden; }
  .tx-p { position:absolute; opacity:0; border-radius:5px; will-change:transform; }
  .box { position:absolute; display:flex; flex-direction:column; align-items:center; justify-content:center; }
  .cap-layer { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:30; pointer-events:none; }
  .cap { position:absolute; left:%dpx; width:%dpx; top:%dpx; height:%dpx; display:flex; align-items:center; justify-content:center;
    flex-wrap:wrap; gap:0 .26em; visibility:hidden; font-weight:700; font-size:%dpx; line-height:1.1; letter-spacing:-.01em;
    text-align:center; text-shadow: 0 2px 10px rgba(0,0,0,.45); }
  .cap.on-light { text-shadow:none; }
  .cap .cw { position:relative; display:inline-block; padding:0 .14em; border-radius:6px; }
  .cap .hd { position:absolute; width:14px; height:14px; background:%s; border:3px solid %s; opacity:0; }
  .cap .hd.a { left:-7px; top:-7px; } .cap .hd.b { right:-7px; bottom:-7px; }
%s""" % (tok["fonts"]["label_file"], tok["fonts"]["display"], tok["fonts"]["label"], WIDE[0], WIDE[1], band_top,
         band_bottom - band_top, CAP_SIZE, hl["handle"], hl["handle_border"], "".join(css.values()))

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
        evs = sound.events([(kinds[k], timed[k][3]) for k in range(1, len(timed))], item_times) if want_sfx else []
        sound.mix_bed(os.path.join(out, "voice.wav"), None if music in (None, "none") else (sound.pad_file() if music == "pad" else music),
                      evs, D, os.path.join(out, "bed.wav"), float(snd.get("music_db", -22)))
        bed = ('    <audio id="bed" src="bed.wav" data-start="0" data-duration="%.3f" data-track-index="40" data-volume="1"></audio>\n' % D)
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
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page)
    moments["spans"].sort()
    with open(os.path.join(out, "moments.json"), "w") as f:
        json.dump(moments, f, indent=1)
    with open(os.path.join(out, "hyperframes.json"), "w") as f:
        json.dump({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                   "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                   "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                   "media": {"autoProxy": True}}, f, indent=2)
    print("E3 PASS: wrote %s/index.html: 1080x1920 at 60 fps, %.2f s, %d scenes, %d backgrounds, %d caption phrases"
          % (out, D, len(timed), len(bgs), len(chunks)))
    print("snapshot moments:", " ".join("%.2f" % min(D, t_in + 0.6) for _, _, _, t_in, _, _ in timed))


if __name__ == "__main__":
    main()
