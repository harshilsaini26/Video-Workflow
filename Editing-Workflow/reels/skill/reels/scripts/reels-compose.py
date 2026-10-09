#!/usr/bin/env python3
"""reels-compose.py: build public/index.html for a vertical Reel (1080x1920, 60 fps) from a storyboard.json.

The vertical sibling of the kit's compose.py. It writes the same structure the kit's checkers read (#stage, #video-wrap /
#video-zoom, card-host hosts with data-anchor or data-unanchored, items with data-at, cutaway videos, one paused GSAP
timeline in window.__timelines), so beat-check.py, gap-scan.py, snap-beats.py and verify-render.py work unchanged.
What is new: a 1080x1920 stage at 60 fps, burned-in word captions built from the transcript, and nine vertical formats
placed inside the platform safe zone by construction (reels_lib.SAFE; PLAYBOOK §R3). The house look stays: DM Sans 700,
light glass, cyan key words, amber money, magenta punchlines.

Usage:
  python3 reels-compose.py --spec videos/<p>/storyboard.json --out videos/<p>/public [--shared videos/_shared] [--kit .claude/skills/youtube-edit]

storyboard.json:
{
  "id": "reel-01", "duration": 34.5, "fps": 60, "video": "input-video.mp4",
  "video_position": "50% 50%",          # object-position of the footage (choose the crop of a 16:9 source: "38% 50%")
  "origin": "50% 28%",                  # camera zoom anchor: keep the face in frame
  "glass_bg": "rgba(255,255,255,0.18)", # a bright room: "rgba(17,17,17,0.55)"
  "captions": {"transcript": "transcript.json", "max_words": 3, "max_chars": 18, "size": 84,
               "em": ["free", "$1,000"], "money": ["$1,000"], "off": [[0.0, 2.6]], "case": "as-is|upper",
               "terms": ["HyperFrames", "Parakeet"], "replace": {"parakeat": "Parakeet"}},   # or "captions": false
  "beats": [
    {"type": "hook",  "id": "h1", "text": "I edit with zero paid tools", "em": [3, 4], "in": 0.0, "out": 2.6, "anchor": "-", "pos": "top", "box": false},
    {"type": "headline", "id": "hd", "text": "...", "em": [..], "in": .., "out": .., "anchor": "..", "pos": "top|mid|low"},
    {"type": "point", "id": "pt", "text": "Step 1", "sub": "Record vertical", "color": "cyan|amber|white", "in", "out", "anchor", "pos"},
    {"type": "steps", "id": "st", "title": "3 free tools", "items": [["OBS", t], ["Parakeet", t, "parakeet"]], "in", "out", "anchor", "pos"},
    {"type": "pills", "id": "pl", "items": [["Free", t], {"text": "No watermark", "at": t, "tone": "cyan|amber", "anchor": ".."}], "in", "out", "anchor", "pos"},
    {"type": "logo",  "id": "lg", "src": "img/obs.svg", "pop": t, "in", "out", "anchor", "pos"},
    {"type": "chip",  "id": "ch", "text": "it's actually free", "em": [2, 3], "in", "out", "anchor", "pos": "low"},
    {"type": "stat",  "id": "sn", "value": 1000, "prefix": "$", "suffix": "", "decimals": 0, "label": "saved a month", "color": "amber", "count_at": t, "in", "out", "anchor", "pos"},
    {"type": "clip",  "id": "c1", "src": "broll/desk.mp4", "media_start": 0, "drift": true, "label": "..", "in", "out", "anchor"},
    {"type": "image", "id": "im", "src": "img/page.png", "in", "out", "anchor", "push": 1.05}
  ],
  "camera": [["set", t, 1.0], ["creep", t0, t1, 1.10], ["punch", t, 1.18], ["release", t, 0.5]],
  "sounds": [{"src": "sfx/click.mp3", "at": t, "dur": 0.5, "volume": 0.28}],
  "loop": {"note": "the last line leads back into the first"},   # informational: checked at Checkpoint B
  "raw_html": "", "raw_js": ""
}
Every beat has type, id, in, out and anchor (the spoken words, or "-" for a deliberate unanchored beat). Items carry
their own time and anchor. Exit codes: 0 built, 1 a rule broke (the message names it).
"""
import argparse, glob, html, json, math, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--spec", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--shared", default="")
ap.add_argument("--kit", default="", help="the kit's youtube-edit folder (fonts, GSAP); found automatically when installed")
args = ap.parse_args()

def fail(msg):
    print("FAIL " + msg, file=sys.stderr)
    sys.exit(1)

S = json.load(open(args.spec))
SPEC_DIR = os.path.dirname(os.path.abspath(args.spec))
OUT = args.out
os.makedirs(OUT, exist_ok=True)
D = float(S["duration"])
FPS = int(S.get("fps", 60))
esc = lambda s: html.escape(str(s), quote=True)

# ---- the kit: fonts and GSAP ----------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
kit_cands = [args.kit] if args.kit else []
kit_cands += [os.path.join(HERE, "..", "..", "youtube-edit"),                                   # installed side by side
              os.path.join(os.getcwd(), ".claude", "skills", "youtube-edit"),
              os.path.join(HERE, "..", "..", "..", "..", "kit", "youtube-edit")]   # this repository (Editing-Workflow/kit)
KIT = next((os.path.abspath(k) for k in kit_cands if k and os.path.isdir(k)), None)

def stage(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)

fonts = []
if KIT:
    fonts = sorted(glob.glob(os.path.join(KIT, "assets", "fonts", "*.woff2"))) or sorted(glob.glob(os.path.join(KIT, "assets", "*.woff2")))
for f in fonts:
    stage(f, os.path.join(OUT, "fonts", os.path.basename(f)))
if not fonts:
    print("WARN no DM Sans .woff2 found in the kit (assets/fonts/ or assets/): text falls back to the system sans")
GSAP_CDN = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
for cand in [os.path.join(HERE, "..", "assets", "vendor", "gsap.min.js")] + ([os.path.join(KIT, "assets", "vendor", "gsap.min.js")] if KIT else []):
    if os.path.exists(cand):          # a local copy renders offline (get one with: npm pack gsap@3.14.2)
        stage(cand, os.path.join(OUT, "vendor", "gsap.min.js"))
        break
GSAP_SRC = "vendor/gsap.min.js" if os.path.exists(os.path.join(OUT, "vendor", "gsap.min.js")) else GSAP_CDN
if GSAP_SRC == GSAP_CDN:
    print("note: no local gsap.min.js; the page loads GSAP from the CDN (the first render needs internet)")
if args.shared:
    for sub in ("img", "sfx"):
        for f in glob.glob(os.path.join(args.shared, sub, "*")):
            if os.path.isfile(f):
                stage(f, os.path.join(OUT, sub, os.path.basename(f)))

# ---- layout: everything inside the safe zone --------------------------------------------------------------------
WIDE_L, WIDE_W = L.SAFE["left"], L.SAFE["right"] - L.SAFE["left"]          # 65, 950
NAR_L, NAR_W = L.NARROW["left"], L.NARROW["right"] - L.NARROW["left"]       # 150, 780

placed = []   # (id, top, bottom) of every block, for the caption-slot check after the captions are built

def place(bid, pos, height):
    """(left, top, width) for a block at slot `pos`; narrow when it reaches the action column band.

    `height` is px, or a function of the width for text that wraps: the narrow column fits fewer characters a line,
    so the height is measured again at the width the block actually gets."""
    if pos not in L.SLOTS:
        fail("%s: unknown pos %r (one of: %s)" % (bid, pos, ", ".join(L.SLOTS)))
    h_at = height if callable(height) else (lambda w: height)
    top = L.SLOTS[pos]
    left, width = WIDE_L, WIDE_W
    h = h_at(width)
    if top + h > L.RIGHT_COL_TOP:
        left, width = NAR_L, NAR_W
        h = h_at(width)
    if not L.inside_safe(left, top, width, h):
        fail("%s: a %d px tall block at pos %r ends at y %d, past the safe zone (bottom %d). Use a higher pos or less text"
             % (bid, h, pos, top + h, L.SAFE["bottom"]))
    placed.append((bid, top, top + h))
    return left, top, width

def text_lines(text, size, width):
    return max(1, math.ceil(len(text) * size * 0.56 / width))   # DM Sans 700 averages about 0.56 em per character

def text_width(text, size):
    return len(text) * size * 0.56

# Box heights, measured in Chromium with DM Sans 700 (the CSS below): "normal" line height is about 1.31 em, the glass
# border 3 px a side. Each takes the column width it is given, so wrapped text is counted at the width the block gets.
def h_steps(title, items, w):
    inner = w - 86                                             # 40 px padding + 3 px border, each side
    t = (22 + 63 * text_lines(title, 48, inner)) if title else 0          # title: 48 px, line 63, margin 22
    rows = sum(max(64, 63 * text_lines(it, 60, inner - 86)) + 22 for it in items)   # 64 px number + 22 gap; text 60 px, line 63
    return 6 + 30 + 18 + t + rows

def h_pills(n):
    return 121 * n                                             # 16 + 63 + 16 padding, 6 border, 20 margin each

def h_point(text, size, sub, w):
    return size * text_lines(text, size, w) + ((14 + 58 * text_lines(sub, 52, w)) if sub else 0)

def h_stat(label, w):
    return 150 + ((16 + 68 * text_lines(label, 52, w)) if label else 0)

def h_chip(text, w):
    return 78 * text_lines(text, 72, w - 68) + 40

origin = S.get("origin", "50% 28%")
vpos = S.get("video_position", "50% 50%")
GLASS = S.get("glass_bg", "rgba(255,255,255,0.18)")

CSS = """
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-400.woff2") format("woff2"); font-weight: 400; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-500.woff2") format("woff2"); font-weight: 500; font-display: block; }
  @font-face { font-family: "DM Sans"; src: url("fonts/DMSans-700.woff2") format("woff2"); font-weight: 700; font-display: block; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000;
    font-family: "DM Sans", ui-sans-serif, system-ui, sans-serif; }
  #stage { position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }
  :root { --cyan:#0AF0F0; --blue:#0005EE; --magenta:#CD00EE; --amber:#FFB904; --white:#FFFFFF; }
  .video-wrapper { position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; transform-origin:50% 0%; will-change:transform; }
  #video-zoom { position:absolute; inset:0; transform-origin:ORIGIN; will-change:transform; }
  #video-zoom video { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:VPOS; display:block; }
  #bg-video { z-index:1; }
  .card-host { position:absolute; pointer-events:none; overflow:hidden; z-index:10; }
  .box { position:absolute; display:flex; flex-direction:column; align-items:center; }
  .shadow { text-shadow: 0 3px 8px rgba(0,0,0,.85), 0 8px 36px rgba(0,0,0,.7); }
  .glass { border-radius:28px; background: rgba(255,255,255,0); backdrop-filter: blur(30px) saturate(1.25);
    -webkit-backdrop-filter: blur(30px) saturate(1.25); border: 3px solid rgba(255,255,255,0); box-shadow: 0 24px 80px rgba(0,0,0,0); }
  /* hook / headline: words rise in, centred, key words cyan (amber for money) */
  .hl { font-weight:700; line-height:1.08; letter-spacing:-.015em; color:#fff; text-align:center; font-size:0; padding:0 6px; }
  .hl .w { display:inline-block; opacity:0; }
  .hl .sp { display:inline-block; width:.26em; }
  .hl .w.em { color:var(--cyan); }
  .hl.amber .w.em { color:var(--amber); }
  .hl.boxed { background: rgba(17,17,17,0.55); border-radius:24px; padding:18px 28px; }
  /* point: one big word or number and a sub line */
  .pt-main { font-weight:700; line-height:1; color:#fff; text-align:center; letter-spacing:-.02em; opacity:0; }
  .pt-main.cyan { color:var(--cyan); } .pt-main.amber { color:var(--amber); }
  .pt-sub { font-weight:700; font-size:52px; line-height:1.1; color:#fff; text-align:center; margin-top:14px; opacity:0; }
  /* steps: a glass card, numbered items arrive on their words */
  .steps { width:100%; padding:30px 40px 18px; }
  .steps .inner { opacity:0; }
  .steps .ttl { font-weight:700; font-size:48px; color:rgba(255,255,255,.92); margin-bottom:22px; text-shadow: 0 2px 8px rgba(0,0,0,.8); }
  .steps .it { display:none; align-items:center; gap:22px; margin-bottom:22px; }
  .steps .n { width:64px; height:64px; border-radius:50%; background:var(--cyan); color:#111; font-weight:700; font-size:38px;
    display:flex; align-items:center; justify-content:center; flex:none; }
  .steps .t { font-weight:700; font-size:60px; line-height:1.05; color:#fff; text-shadow: 0 2px 8px rgba(0,0,0,.85); }
  /* pills: a centred column of glass labels */
  .pls { display:flex; align-items:center; gap:18px; padding:16px 34px; margin-bottom:20px; visibility:hidden; }
  .pls .inner { opacity:0; display:flex; align-items:center; gap:18px; }
  .pls .t { font-weight:700; font-size:48px; color:#fff; white-space:nowrap; text-shadow: 0 2px 8px rgba(0,0,0,.8); }
  .pls.cyan .t { color:var(--cyan); } .pls.amber .t { color:var(--amber); }
  /* logo plate */
  .lg { width:360px; height:360px; display:flex; align-items:center; justify-content:center; }
  .lg .inner { opacity:0; }
  .lg img { width:250px; height:240px; object-fit:contain; display:block; filter: drop-shadow(0 4px 14px rgba(0,0,0,.45)); }   /* a fixed box: an SVG without width/height otherwise collapses */
  /* chip: the punchline, magenta emphasis on dark glass */
  .chip { border-radius:20px; padding:20px 34px; background: rgba(17,17,17,0); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
  .chip .inner { opacity:0; font-weight:700; font-size:72px; line-height:1.08; color:#fff; text-align:center; }
  .chip .em { color:var(--magenta); }
  /* stat: a count-up in full digits */
  .sn-v { font-weight:700; font-size:150px; line-height:1; letter-spacing:-.02em; color:#fff; font-variant-numeric: tabular-nums;
    -webkit-text-stroke: 3px currentColor; opacity:0; }
  .sn-v.amber { color:var(--amber); } .sn-v.cyan { color:var(--cyan); }
  .sn-l { font-weight:700; font-size:52px; color:#fff; margin-top:16px; text-align:center; opacity:0; }
  /* full-frame cutaways: video clip and image on the dark wash */
  .cutaway-video { position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; z-index:20; }
  .cut-over { z-index:21 !important; }
  .wash { position:absolute; inset:0; background: radial-gradient(ellipse at 30% 20%, rgba(10,240,240,.14), transparent 55%),
    radial-gradient(ellipse at 80% 85%, rgba(205,0,238,.12), transparent 55%), #0b0c10; }
  .im-frame { position:absolute; left:40px; width:1000px; top:300px; height:900px; display:flex; align-items:center; justify-content:center; }
  .im-frame img { max-width:1000px; max-height:900px; border-radius:22px; box-shadow: 0 30px 90px rgba(0,0,0,.6); display:block; }
  /* captions: the spoken words, a few at a time; the word being said turns cyan */
  .cap-layer { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:30; pointer-events:none; }
  .cap { position:absolute; left:NAR_Lpx; width:NAR_Wpx; top:CAP_TOPpx; text-align:center; visibility:hidden;
    font-weight:700; line-height:1.1; letter-spacing:-.01em; color:#fff;
    text-shadow: 0 0 2px #000, 0 3px 6px rgba(0,0,0,.9), 0 8px 28px rgba(0,0,0,.75); }
  .cap .cw { display:inline-block; margin:0 .12em; }
  .cap .cw.em { color:var(--cyan); }
  .cap .cw.money { color:var(--amber); }
""".replace("ORIGIN", origin).replace("VPOS", vpos).replace("NAR_L", str(NAR_L)).replace("NAR_W", str(NAR_W)).replace("CAP_TOP", str(L.CAPTION_TOP))

HELPERS = """
        const glassIn = function (sel, t, from, dur) {
          tl.fromTo(sel, Object.assign({ backgroundColor: 'rgba(255,255,255,0)', borderColor: 'rgba(255,255,255,0)', boxShadow: '0 24px 80px rgba(0,0,0,0)' }, from || {}),
            { backgroundColor: 'GLASS', borderColor: 'rgba(255,255,255,0.58)', boxShadow: '0 24px 80px rgba(0,0,0,0.38)', x: 0, y: 0, duration: dur || 0.42, ease: 'power2.out' }, t);
        };
        const glassOut = function (sel, t, dur) {
          tl.to(sel, { backgroundColor: 'rgba(255,255,255,0)', borderColor: 'rgba(255,255,255,0)', boxShadow: '0 24px 80px rgba(0,0,0,0)', duration: dur || 0.35, ease: 'power2.in' }, t);
        };
        const wordsIn = function (sel, t) {
          tl.fromTo(sel + ' .w', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', stagger: 0.05, immediateRender: false }, t);
        };
        const countUp = function (sel, to, t, dur, prefix, suffix, dec) {
          const el = document.querySelector(sel); const o = { v: 0 };
          const fmt = function (v) { return prefix + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suffix; };
          el.textContent = fmt(0);
          tl.fromTo(o, { v: 0 }, { v: to, duration: dur, ease: 'power2.out', immediateRender: false,
            onUpdate: function () { el.textContent = fmt(dec ? o.v : Math.round(o.v)); } }, t);
        };
""".replace("GLASS", GLASS)

html_parts, js_parts, audio_parts = [], [], []
track, audio_track = 3, 40
def js(s): js_parts.append(s)

def attr_anchor(anchor):
    if anchor == "-":
        return ' data-unanchored="1"'
    return ' data-anchor="%s"' % esc(anchor) if anchor else ""

def host(bid, t_in, t_out, inner, anchor, extra_cls=""):
    global track
    h = ('    <div class="card-host clip%s" id="host-%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s\n'
         '      style="left:0;top:0;width:1080px;height:1920px;visibility:hidden;opacity:1;">%s</div>\n'
         % (extra_cls, bid, t_in, t_out - t_in, track, attr_anchor(anchor), inner))
    track += 1
    return h

def item_attrs(text, t, anchor):
    return ' data-at="%.3f"%s' % (float(t), attr_anchor(anchor))

def words_spans(text, em):
    em = set(em or [])
    ws = text.split(" ")
    out = []
    for i, w in enumerate(ws):
        if i:
            out.append('<span class="sp"></span>')
        out.append('<span class="w%s">%s</span>' % (" em" if i in em else "", esc(w)))
    return "".join(out)

def norm_item(it):
    if isinstance(it, dict):
        return {"text": it["text"], "at": float(it["at"]), "anchor": it.get("anchor", it["text"]), "tone": it.get("tone", "")}
    return {"text": it[0], "at": float(it[1]), "anchor": it[2] if len(it) > 2 else it[0], "tone": ""}

# ---- beats -------------------------------------------------------------------------------------------------------
KNOWN = ("hook", "headline", "point", "steps", "pills", "logo", "chip", "stat", "clip", "image")
seen_ids, beat_times = set(), {}
for b in S.get("beats", []):
    t, bid = b.get("type"), b.get("id")
    if t not in KNOWN:
        fail("unknown beat type %r (one of: %s)" % (t, ", ".join(KNOWN)))
    if not bid or bid in seen_ids:
        fail("every beat needs a unique id (%r)" % bid)
    if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", str(bid)):
        fail("%s: an id starts with a letter and holds only letters, digits, - and _ (it becomes an HTML id and a selector)" % bid)
    seen_ids.add(bid)
    t_in, t_out = float(b["in"]), float(b["out"])
    beat_times[bid] = (t_in, t_out)
    if not (0 <= t_in < t_out <= D + 1e-6):
        fail("%s: in %.2f / out %.2f must satisfy 0 <= in < out <= duration %.2f" % (bid, t_in, t_out, D))
    if "anchor" not in b:
        fail("%s: every beat needs an anchor (the spoken words, or \"-\" for a deliberate unanchored beat)" % bid)
    anchor = b["anchor"]

    if t in ("hook", "headline"):
        text = b["text"]
        if t == "hook" and len(text) > 60:
            fail("%s: the hook is %d characters; keep it under 60 so it reads in about a second" % (bid, len(text)))
        size = int(b.get("size", 96 if t == "hook" else 84))
        if not 72 <= size <= 112:
            fail("%s: size %d is outside 72 to 112 px" % (bid, size))
        pos = b.get("pos", "top")
        pad = 36 if b.get("box") else 0
        left, top, width = place(bid, pos, lambda w: int(text_lines(text, size, w - 60) * size * 1.08 + pad))
        lines = text_lines(text, size, width - 60)
        if lines > 3:
            fail("%s: %r needs %d lines at %d px in a %d px column; three at most" % (bid, text, lines, size, width))
        cls = "hl shadow" + (" amber" if b.get("color") == "amber" else "") + (" boxed" if b.get("box") else "")
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="%s" id="%s" style="font-size:%dpx">%s</div></div>' % (
            left, top, width, cls, bid, size, words_spans(text, b.get("em")).replace('class="w', 'style="font-size:%dpx" class="w' % size).replace('class="sp"', 'class="sp" style="font-size:%dpx"' % size))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("wordsIn('#%s', %.3f);" % (bid, t_in + 0.02))
        js("tl.to('#%s .w', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
        js("tl.set('#%s .w', { opacity: 0 }, %.3f);" % (bid, t_out - 0.01))

    elif t == "point":
        size = int(b.get("size", 132))
        left, top, width = place(bid, b.get("pos", "mid"), lambda w: h_point(b["text"], size, b.get("sub"), w))
        col = b.get("color", "white")
        sub = '<div class="pt-sub shadow" id="%s-sub">%s</div>' % (bid, esc(b["sub"])) if b.get("sub") else ""
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="pt-main shadow %s" id="%s-main" style="font-size:%dpx">%s</div>%s</div>' % (
            left, top, width, col, bid, size, esc(b["text"]), sub)
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("tl.fromTo('#%s-main', { opacity: 0, y: 34, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in))
        if sub:
            js("tl.fromTo('#%s-sub', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.36, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in + 0.18))
        js("tl.to('#host-%s .pt-main, #host-%s .pt-sub', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, bid, t_out - 0.32))

    elif t == "steps":
        items = [norm_item(it) for it in b["items"]]
        if not 1 <= len(items) <= 5:
            fail("%s: steps take 1 to 5 items" % bid)
        for it in items:
            if len(it["text"]) > 22:
                fail("%s: step %r is over 22 characters" % (bid, it["text"]))
        left, top, width = place(bid, b.get("pos", "top"), lambda w: h_steps(b.get("title"), [it["text"] for it in items], w))
        rows = "".join('<div class="it" id="%s-i%d"%s><div class="n">%d</div><div class="t">%s</div></div>' % (
            bid, i, item_attrs(it["text"], it["at"], it["anchor"]), i + 1, esc(it["text"])) for i, it in enumerate(items))
        ttl = '<div class="ttl">%s</div>' % esc(b["title"]) if b.get("title") else ""
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="glass steps" id="%s-glass"><div class="inner" id="%s-inner">%s%s</div></div></div>' % (
            left, top, width, bid, bid, ttl, rows)
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("glassIn('#%s-glass', %.3f, { y: 30 });" % (bid, t_in))
        js("tl.fromTo('#%s-inner', { opacity: 0 }, { opacity: 1, duration: 0.36, immediateRender: false }, %.3f);" % (bid, t_in + 0.04))
        for i, it in enumerate(items):
            js("tl.set('#%s-i%d', { display: 'flex' }, %.3f);" % (bid, i, it["at"]))
            js("tl.fromTo('#%s-i%d', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, i, it["at"]))
        js("tl.to('#%s-inner', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.40))
        js("glassOut('#%s-glass', %.3f, 0.35);" % (bid, t_out - 0.35))

    elif t == "pills":
        items = [norm_item(it) for it in b["items"]]
        if not 1 <= len(items) <= 5:
            fail("%s: pills take 1 to 5 items" % bid)
        left, top, width = place(bid, b.get("pos", "top"), h_pills(len(items)))
        for it in items:   # a pill never wraps (white-space: nowrap), so a long one would run past the column
            if text_width(it["text"], 48) + 74 > width:
                fail("%s: pill %r is about %d px wide, wider than the %d px column; shorten it" % (bid, it["text"], text_width(it["text"], 48) + 74, width))
        pl = "".join('<div class="glass pls %s" id="%s-p%d"%s><div class="inner" id="%s-pi%d"><span class="t">%s</span></div></div>' % (
            it["tone"], bid, i, item_attrs(it["text"], it["at"], it["anchor"]), bid, i, esc(it["text"])) for i, it in enumerate(items))
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx">%s</div>' % (left, top, width, pl)
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        for i, it in enumerate(items):
            js("tl.set('#%s-p%d', { visibility: 'inherit' }, %.3f);" % (bid, i, it["at"]))
            js("glassIn('#%s-p%d', %.3f, { y: 20 });" % (bid, i, it["at"]))
            js("tl.fromTo('#%s-pi%d', { opacity: 0 }, { opacity: 1, duration: 0.36, immediateRender: false }, %.3f);" % (bid, i, it["at"] + 0.04))
        js("tl.to('#host-%s .pls .inner', { opacity: 0, duration: 0.28, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.40))
        for i in range(len(items)):
            js("glassOut('#%s-p%d', %.3f, 0.33);" % (bid, i, t_out - 0.35))

    elif t == "logo":
        left, top, width = place(bid, b.get("pos", "top"), 360)
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="glass lg" id="%s-glass"><div class="inner" id="%s-inner"><img src="%s" alt="" /></div></div></div>' % (
            left, top, width, bid, bid, esc(b["src"]))
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("glassIn('#%s-glass', %.3f, { y: 30 });" % (bid, t_in))
        js("tl.fromTo('#%s-inner', { opacity: 0 }, { opacity: 1, duration: 0.36, immediateRender: false }, %.3f);" % (bid, t_in + 0.04))
        js("tl.to('#%s-inner', { opacity: 0, duration: 0.28, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.38))
        js("glassOut('#%s-glass', %.3f, 0.33);" % (bid, t_out - 0.34))
        if b.get("pop") is not None:
            audio_parts.append('    <audio id="sfx-pop-%s" src="sfx/pop.mp3" data-start="%.3f" data-duration="0.72" data-track-index="%d" data-volume="0.34"></audio>\n'
                               % (bid, float(b["pop"]), audio_track))
            audio_track += 1

    elif t == "chip":
        left, top, width = place(bid, b.get("pos", "low"), lambda w: h_chip(b["text"], w))
        em = set(b.get("em", []))
        spans = " ".join('<span class="em">%s</span>' % esc(w) if i in em else esc(w) for i, w in enumerate(b["text"].split(" ")))
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="chip" id="%s-chip"><div class="inner" id="%s-inner">%s</div></div></div>' % (
            left, top, width, bid, bid, spans)
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        js("tl.fromTo('#%s-chip', { backgroundColor: 'rgba(17,17,17,0)', y: 18 }, { backgroundColor: 'rgba(17,17,17,0.45)', y: 0, duration: 0.4, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in))
        js("tl.fromTo('#%s-inner', { opacity: 0 }, { opacity: 1, duration: 0.32, immediateRender: false }, %.3f);" % (bid, t_in + 0.06))
        js("tl.to('#%s-inner', { opacity: 0, duration: 0.26, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.36))
        js("tl.to('#%s-chip', { backgroundColor: 'rgba(17,17,17,0)', duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))

    elif t == "stat":
        left, top, width = place(bid, b.get("pos", "mid"), lambda w: h_stat(b.get("label"), w))
        col = b.get("color", "white")
        dec = int(b.get("decimals", 0))
        final = L.full_digits(float(b["value"]), b.get("prefix", ""), b.get("suffix", ""), dec)
        if text_width(final, 150) > width:   # a number never wraps: it would run past the column
            fail("%s: %r is about %d px wide at 150 px, wider than the %d px column; use a shorter number or a headline"
                 % (bid, final, text_width(final, 150), width))
        lab = '<div class="sn-l shadow" id="%s-l">%s</div>' % (bid, esc(b["label"])) if b.get("label") else ""
        inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="sn-v shadow %s" id="%s-v">%s</div>%s</div>' % (
            left, top, width, col, bid, esc(final), lab)
        html_parts.append(host(bid, t_in, t_out, inner, anchor))
        cat = float(b.get("count_at", t_in + 0.1))
        js("tl.fromTo('#%s-v', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in))
        js("countUp('#%s-v', %s, %.3f, %.3f, %s, %s, %d);" % (bid, json.dumps(float(b["value"])), cat, float(b.get("count_dur", 1.2)),
                                                            json.dumps(b.get("prefix", "")), json.dumps(b.get("suffix", "")), dec))
        if lab:
            js("tl.fromTo('#%s-l', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.36, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in + 0.2))
        js("tl.to('#host-%s .sn-v, #host-%s .sn-l', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, bid, t_out - 0.32))

    elif t == "clip":
        html_parts.append('    <video class="cutaway-video clip" id="%s" src="%s" muted playsinline data-start="%.3f" data-duration="%.3f" data-media-start="%.3f" data-track-index="%d"%s></video>\n'
                          % (bid, esc(b["src"]), t_in, t_out - t_in, float(b.get("media_start", 0)), track, attr_anchor(anchor)))
        track += 1
        if b.get("drift", True):
            js("tl.fromTo('#%s', { scale: 1.0 }, { scale: 1.04, duration: %.3f, ease: 'none', immediateRender: false }, %.3f);" % (bid, t_out - t_in, t_in))
        if b.get("label"):
            size = 84
            label = b["label"]
            left, top, width = place(bid, "top", lambda w: int(text_lines(label, size, w - 60) * size * 1.08))
            inner = '<div class="box" style="left:%dpx;top:%dpx;width:%dpx"><div class="hl shadow" id="%s-label">%s</div></div>' % (
                left, top, width, bid, words_spans(b["label"], b.get("label_em")).replace('class="w', 'style="font-size:%dpx" class="w' % size).replace('class="sp"', 'class="sp" style="font-size:%dpx"' % size))
            html_parts.append(host(bid + "-over", t_in, t_out, inner, "-", " cut-over"))
            js("wordsIn('#%s-label', %.3f);" % (bid, t_in + 0.1))

    elif t == "image":
        inner = '<div class="wash"></div><div class="im-frame"><img id="%s-img" src="%s" alt="" /></div>' % (bid, esc(b["src"]))
        html_parts.append(host(bid, t_in, t_out, inner, anchor, " cut-over"))
        js("tl.fromTo('#%s-img', { scale: 1.0 }, { scale: %.3f, duration: %.3f, ease: 'power1.inOut', immediateRender: false }, %.3f);" % (bid, float(b.get("push", 1.05)), t_out - t_in, t_in))

# ---- captions ----------------------------------------------------------------------------------------------------
cap_html, cap_js, n_chunks = "", [], 0
C = S.get("captions", {})
if C is True or C is None:
    C = {}
if C is not False and not isinstance(C, dict):
    fail("\"captions\" is an object of settings, true, or false (got %r)" % (C,))
shown = []   # (start, end) of every caption on screen
if C is not False:
    tpath = C.get("transcript", "transcript.json")
    tpath = tpath if os.path.isabs(tpath) else os.path.join(SPEC_DIR, tpath)
    if not os.path.exists(tpath):
        fail("captions need the transcript at %s (or set \"captions\": false)" % tpath)
    words = L.load_words(tpath)
    # on screen, a misheard name is a visible mistake: "terms" fixes the spelling of a word ("hyperframes" -> "HyperFrames"),
    # "replace" fixes a word Parakeet heard wrong ({"parakeat": "Parakeet"}); the timing stays Parakeet's
    fixes = {L.norm(t): t for t in C.get("terms", [])}
    fixes.update({L.norm(k): v for k, v in C.get("replace", {}).items()})
    for w in words:
        k = L.norm(L.clean_word(w["text"]))
        if k in fixes:
            tail = w["text"][len(L.clean_word(w["text"])):]
            w["text"] = fixes[k] + tail
    off = [(float(a), float(z)) for a, z in C.get("off", [])]
    words = [w for w in words if w["start"] < D and not any(a <= w["start"] < z for a, z in off)]
    size = int(C.get("size", 84))
    if not 64 <= size <= 100:
        fail("captions size %d is outside 64 to 100 px" % size)
    chunks = L.chunk_words(words, int(C.get("max_words", 3)), int(C.get("max_chars", 18)))
    em = {L.norm(x) for x in C.get("em", [])}
    money = {L.norm(x) for x in C.get("money", [])}
    upper = C.get("case") == "upper"
    parts = []
    for i, ch in enumerate(chunks):
        end = ch["end"]
        for a, z in off:                 # a chunk never runs into an "off" range
            if ch["start"] < a < end:
                end = a
        shown.append((ch["start"], end))
        spans = []
        for j, w in enumerate(ch["words"]):
            k = L.norm(w["text"])
            cls = " money" if k in money else (" em" if k in em else "")
            spans.append('<span class="cw%s" id="cw%d-%d">%s</span>' % (cls, i, j, esc(w["text"].upper() if upper else w["text"])))
            if not cls:   # the word being said turns cyan, then back to white
                cap_js.append("tl.set('#cw%d-%d', { color: '#0AF0F0' }, %.3f);" % (i, j, w["start"]))
                nxt = ch["words"][j + 1]["start"] if j + 1 < len(ch["words"]) else end
                cap_js.append("tl.set('#cw%d-%d', { color: '#FFFFFF' }, %.3f);" % (i, j, max(w["start"] + 0.05, nxt)))
        parts.append('      <div class="cap" id="cap%d" style="font-size:%dpx">%s</div>\n' % (i, size, "".join(spans)))
        cap_js.append("tl.set('#cap%d', { visibility: 'visible' }, %.3f);" % (i, ch["start"]))
        cap_js.append("tl.fromTo('#cap%d', { y: 10, opacity: 0.6 }, { y: 0, opacity: 1, duration: 0.12, ease: 'power2.out', immediateRender: false }, %.3f);" % (i, ch["start"]))
        cap_js.append("tl.set('#cap%d', { visibility: 'hidden' }, %.3f);" % (i, end))
    n_chunks = len(chunks)
    # a block reaching into the caption slot while captions show would sit under (or over) them (PLAYBOOK §R14)
    for bid, top, bottom in placed:
        if bottom <= L.CAPTION_TOP:
            continue
        b_in, b_out = beat_times[bid]
        hit = next((st for st, en in shown if st < b_out and en > b_in), None)
        if hit is not None:
            fail("%s: the block ends at y %d, inside the caption slot (from y %d), while captions show at %.2f s. "
                 "Use a higher pos or less text, or switch captions off for this beat (\"off\": [[%.2f, %.2f]])"
                 % (bid, bottom, L.CAPTION_TOP, hit, b_in, b_out))
    cap_html = ('    <div class="clip cap-layer" id="captions" data-start="0" data-duration="%.3f" data-track-index="2">\n%s    </div>\n'
                % (D, "".join(parts)))

# ---- extra sounds --------------------------------------------------------------------------------------------------
for k, snd in enumerate(S.get("sounds", [])):
    v = float(snd.get("volume", 0.3))
    if not 0 < v <= 0.6:
        fail("sound %d: volume %.2f is outside 0 to 0.6" % (k, v))
    audio_parts.append('    <audio id="sfx-%d" src="%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-volume="%.2f"></audio>\n'
                       % (k, esc(snd["src"]), float(snd["at"]), float(snd.get("dur", 0.6)), audio_track, v))
    audio_track += 1

# ---- camera --------------------------------------------------------------------------------------------------------
cam = ["tl.set('#video-zoom', { scale: 1.0 }, 0);", "tl.set('#video-wrap', { scale: 1.0, x: 0 }, 0);"]
for op in S.get("camera", []):
    if op[0] == "set":
        cam.append("tl.set('#video-zoom', { scale: %.3f }, %.3f);" % (float(op[2]), float(op[1])))
    elif op[0] == "creep":
        cam.append("tl.to('#video-zoom', { scale: %.3f, duration: %.3f, ease: 'power1.inOut' }, %.3f);" % (float(op[3]), float(op[2]) - float(op[1]), float(op[1])))
    elif op[0] == "punch":
        cam.append("tl.to('#video-zoom', { scale: %.3f, duration: 0.32, ease: 'power2.out' }, %.3f);" % (float(op[2]), float(op[1])))
    elif op[0] == "release":
        cam.append("tl.to('#video-zoom', { scale: 1.00, duration: %.3f, ease: 'power2.inOut' }, %.3f);" % (float(op[2]), float(op[1])))
    else:
        fail("unknown camera op %r (set, creep, punch, release)" % (op,))
    if op[0] in ("creep", "punch") and float(op[-1]) > 1.6:
        fail("camera scale %.2f is over 1.6 (a 4K vertical source holds about 2.0; 1080p only about 1.12)" % float(op[-1]))

page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>%s</style>
</head>
<body>
  <div id="stage" data-composition-id="%s" data-start="0" data-duration="%.3f" data-fps="%d" data-width="1080" data-height="1920">

    <div class="video-wrapper" id="video-wrap">
      <div id="video-zoom">
        <video id="bg-video" src="%s" playsinline data-has-audio="true" data-start="0" data-duration="%.3f" data-track-index="1"></video>
      </div>
    </div>

%s%s%s%s
    <script src="%s"></script>
    <script>
      (function () {
        const tl = window.gsap.timeline({ paused: true });
%s
        // camera
        %s

        // beats
        %s

        // captions
        %s
%s
        tl.to({}, { duration: %.3f }, 0);
        window.__timelines = window.__timelines || {};
        window.__timelines[%s] = tl;
      })();
    </script>
  </div>
</body>
</html>
""" % (CSS, esc(S["id"]), D, FPS, esc(S.get("video", "input-video.mp4")), D, "".join(html_parts), cap_html, S.get("raw_html", ""),
       "".join(audio_parts), GSAP_SRC, HELPERS, "\n        ".join(cam), "\n        ".join(js_parts), "\n        ".join(cap_js),
       S.get("raw_js", ""), D, json.dumps(str(S["id"])).replace("</", "<\\/"))   # a JS string: the browser decodes the attribute, not script text
open(os.path.join(OUT, "index.html"), "w").write(page)
open(os.path.join(OUT, "hyperframes.json"), "w").write(json.dumps({
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
    "media": {"autoProxy": True}}, indent=2))

beats = S.get("beats", [])
print("wrote %s/index.html: 1080x1920 at %d fps, %.2f s, %d beats, %d caption chunks, %d camera ops, %d sounds"
      % (OUT, FPS, D, len(beats), n_chunks, len(S.get("camera", [])), len(audio_parts)))
print("snapshot moments:", " ".join("%.2f" % (float(b["in"]) + 0.6) for b in beats))
seq = sorted((float(b["in"]), b["type"]) for b in beats)
counts = {}
for _, ty in seq:
    counts[ty] = counts.get(ty, 0) + 1
print("format usage:", ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))))
for (t1, a), (t2, b2) in zip(seq, seq[1:]):
    if a == b2 and a not in ("headline",):
        print("WARN same device twice in a row: %s at %.2f and %.2f" % (a, t1, t2))
if beats and min(float(b["in"]) for b in beats) > 0.5:
    print("WARN nothing lands in the first 0.5 s: the first frame needs a reason to stay (PLAYBOOK §R2)")
