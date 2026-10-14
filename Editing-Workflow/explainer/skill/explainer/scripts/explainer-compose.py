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
import argparse, glob, html, json, os, re, shutil, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import explainer_lib as E
from scenes import REGISTRY, Ctx, SceneError, js_obj, js_str

L = E.L
WIDE = (L.SAFE["left"], L.SAFE["right"] - L.SAFE["left"])          # 65, 950
NARROW = (L.NARROW["left"], L.NARROW["right"] - L.NARROW["left"])  # 150, 780
CENTRE = (E.SCENE["top"] + E.SCENE["bottom"]) // 2                 # 884
GAP_MAX = 0.3
GSAP_CDN = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
CAP_SIZE = 64


def fail(msg):
    print("E3 FAIL: " + msg)
    sys.exit(1)


def place(sid, mod, scene):
    """(left, top, width, height): centred in the scene area, narrow when it reaches the action column band."""
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
        fail("%s: a word in it is about %d px wide, wider than the %d px column; shorten it or use a smaller size" % (sid, need, width))
    return left, top, width, h


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--vendor", default=os.path.join(HERE, "..", "assets", "vendor"),
                    help="GSAP, KaTeX, Lucide, three.js and the label font (default: the skill's assets/vendor)")
    ap.add_argument("--kit", default="", help="the kit's youtube-edit folder (DM Sans); found automatically when installed")
    a = ap.parse_args()

    with open(a.spec) as f:
        S = json.load(f)
    spec_dir = os.path.dirname(os.path.abspath(a.spec))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(spec_dir, p)
    out = a.out
    os.makedirs(out, exist_ok=True)
    tok = E.load_tokens()
    mo = tok["motion"]

    tpath, vpath = rel(S.get("transcript", "transcript.json")), rel(S.get("voice", "voice.wav"))
    if not os.path.exists(tpath):
        fail("no transcript at %s: run align-script.py first" % tpath)
    if not os.path.exists(vpath):
        fail("no voice at %s: run tts-kokoro.py first" % vpath)
    words = L.load_words(tpath)
    with wave.open(vpath) as w:
        voice_len = w.getnframes() / float(w.getframerate())
    D = round(voice_len + E.TAIL, 3)
    shutil.copy(vpath, os.path.join(out, "voice.wav"))

    # ---- fonts and GSAP -------------------------------------------------------------------------------------------
    kits = [a.kit] if a.kit else []
    kits += [os.path.join(HERE, "..", "..", "youtube-edit"), os.path.join(os.getcwd(), ".claude", "skills", "youtube-edit"),
             os.path.join(HERE, "..", "..", "..", "..", "kit", "youtube-edit")]
    kit = next((os.path.abspath(k) for k in kits if k and os.path.isdir(k)), None)
    fonts = sorted(glob.glob(os.path.join(kit, "assets", "fonts", "DMSans-*.woff2"))) if kit else []
    for f in fonts:
        os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
        shutil.copy(f, os.path.join(out, "fonts", os.path.basename(f)))
    if not fonts:
        print("WARN no DM Sans .woff2 in the kit (assets/fonts/): text falls back to the system sans")
    label = os.path.join(a.vendor, tok["fonts"]["label_file"])
    if os.path.exists(label):
        os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
        shutil.copy(label, os.path.join(out, tok["fonts"]["label_file"]))
    else:
        print("WARN no label font at %s (%s): labels fall back to the system mono" % (label, tok["fonts"]["label_install"]))
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
    seen, timed = set(), []
    bg = None
    for sc in scenes:
        sid = sc.get("id")
        if not sid or not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", str(sid)):
            fail("%r: an id starts with a letter and holds only letters, digits, - and _" % (sid,))
        if sid in seen:
            fail("%s: the id is used twice" % sid)
        seen.add(sid)
        mod = REGISTRY.get(sc.get("type"))
        if not mod:
            fail("%s: unknown scene type %r (one of: %s)" % (sid, sc.get("type"), ", ".join(sorted(REGISTRY))))
        bg = sc.get("bg", bg or "blue")
        if bg not in tok["backgrounds"]:
            fail("%s: unknown bg %r (one of: %s)" % (sid, bg, ", ".join(tok["backgrounds"])))
        if getattr(mod, "NEEDS_SOURCE", False) and not sc.get("source"):
            fail("%s: a %s scene shows a number and needs a source (a key in SOURCES.md)" % (sid, sc["type"]))
        errs = mod.validate(sc)
        if errs:
            fail("%s: %s" % (sid, "; ".join(errs)))
        try:
            t_in = max(0.0, E.resolve(sc["in"], words, lead=True))
            t_out = min(D, E.resolve(sc["out"], words, lead=True))
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

    css, hosts, js = {}, [], []
    for k, (sc, mod, sbg, t_in, t_out, end) in enumerate(timed):
        sid = sc["id"]
        left, top, width, h = place(sid, mod, sc)
        ctx = Ctx(sc, t_in, t_out, words, tok, a.vendor, out, sbg)
        try:
            inner, lines = mod.render(sc, ctx, (left, top, width))
        except SceneError as e:
            fail("%s: %s" % (sid, e))
        css[mod.TYPE] = mod.CSS
        word = E.anchor_text(sc["in"], words)
        anchor = ' data-unanchored="1"' if word == "-" else ' data-anchor="%s"' % html.escape(word, quote=True)
        hosts.append('    <div class="card-host clip" id="host-%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s\n'
                     '      style="left:0;top:0;width:1080px;height:1920px;visibility:hidden;">'
                     '<div class="box" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</div></div>\n'
                     % (sid, t_in, end - t_in, 3 + k, anchor, sid, left, top, width, h, inner))
        js.append("// %s (%s) %.2f to %.2f s" % (sid, mod.TYPE, t_in, t_out))
        js.extend(lines)
        if t_out < D - 1e-6:
            js.append("tl.to('#%s', %s, %.3f);" % (sid, js_obj({"opacity": 0, "y": -24, "duration": mo["exit"], "ease": mo["exit_ease"]}), t_out))

    # ---- backgrounds ----------------------------------------------------------------------------------------------
    bgs, bg_js = [], []
    for sc, _, sbg, t_in, _, _ in timed:
        if not bgs or bgs[-1][0] != sbg:
            if bgs:
                bg_js.append("tl.to('#bg%d', { opacity: 1, duration: %.3f, ease: 'power1.inOut' }, %.3f);" % (len(bgs), E.BG_FADE, t_in))
            bgs.append((sbg, t_in))
    bg_html = "".join('    <div class="bg" id="bg%d" style="background:%s;opacity:%d"></div>\n' % (i, tok["backgrounds"][b], 0 if i else 1)
                      for i, (b, _) in enumerate(bgs))

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
  .card-host { position:absolute; pointer-events:none; overflow:hidden; z-index:10; }
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
    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>%s</style>
</head>
<body>
  <div id="stage" data-composition-id="%s" data-start="0" data-duration="%.3f" data-fps="60" data-width="1080" data-height="1920">
%s    <audio id="voice" src="voice.wav" data-start="0" data-duration="%.3f" data-track-index="1" data-volume="1"></audio>
%s%s
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
""" % (CSS, html.escape(str(S["id"]), quote=True), D, bg_html, D, "".join(hosts), cap_html, gsap_src, HELPERS,
       "\n        ".join(bg_js), "\n        ".join(js), "\n        ".join(cap_js), D, js_str(S["id"]))
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(page)
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
