"""file-drop: an upload panel on light paper. A dashed drop zone waits; on each file's word its card (a type tile and the
name) drops into the zone, which lights up while files arrive; then a progress bar fills beside the status and, on the done
word, the status turns to done and a check lands:

  {"type": "file-drop", "label": "Drop files here",
   "files": [{"name": "interview.mp4", "size": "1.2 GB", "at": "word:2"}, {"name": "broll.mov", "at": "word:4"}],
   "done": {"label": "Uploaded", "at": "word:9"}}

The tile shows the file's extension, coloured by kind (video, image, audio, document); `icon` (a Lucide name) draws that
icon instead. `name` and `size` are UI furniture (DECOR_KEYS: no source needed). Without `done`, the bar
fills over the 1.6 s after the last file and the check lands then. Every row has a fixed height, so the panel's height never depends on its width.
"""
import explainer_lib as E
from scenes import js_obj, need

TYPE = "file-drop"
DECOR_KEYS = {"size", "name"}
MAX_SCALE = 1.4
PAD, RADIUS = 28, 36               # the panel
BORDER, Z_PAD, Z_RADIUS = 4, 20, 28   # the dashed zone
HEAD, ARROW, HEAD_GAP = 56, 46, 16    # the zone's head: an upload arrow and its label
L_SIZE = 34                        # the zone's label and the status, DM Sans 500
LIST_GAP, ROW, ROW_GAP = 16, 80, 10   # the file rows
TILE_W, TILE_H, R_PAD, R_GAP = 80, 58, 12, 18
N_SIZE, S_SIZE = 34, 30            # the name (DM Sans 500), the size (JetBrains Mono 500)
FOOT_GAP, STATUS, CHECK = 22, 52, 52  # the status line: its words, the progress bar, the check
BAR, BAR_GAP = 12, 22
MAX_FILES, MAX_NAME = 4, 28
KINDS = {"video": ("mp4", "mov", "webm", "mkv", "avi", "m4v"), "image": ("png", "jpg", "jpeg", "gif", "webp", "heic", "svg", "tif", "tiff"),
         "audio": ("mp3", "wav", "m4a", "aac", "flac", "aif", "aiff"),
         "doc": ("pdf", "doc", "docx", "txt", "md", "csv", "xls", "xlsx", "ppt", "pptx", "key", "json", "srt")}
SERIES = {"doc": 0, "video": 1, "image": 2, "audio": 3}    # the paper series: blue, mauve, teal, yellow

CSS = """
  .fd { width:100%%; border-radius:%dpx; padding:%dpx; opacity:0; }
  .fd-zone { border:%dpx dashed; border-radius:%dpx; padding:%dpx; }
  .fd-head { height:%dpx; display:flex; align-items:center; justify-content:center; gap:%dpx; font-weight:500; font-size:%dpx;
    line-height:1; white-space:nowrap; }
  .fd-up { width:%dpx; height:%dpx; flex:none; display:flex; }
  .fd-up svg { width:100%%; height:100%%; }
  .fd-list { margin-top:%dpx; display:flex; flex-direction:column; gap:%dpx; }
  .fd-row { height:%dpx; border-radius:18px; display:flex; align-items:center; gap:%dpx; padding:0 %dpx; opacity:0; }
  .fd-tile { width:%dpx; height:%dpx; border-radius:14px; flex:none; display:flex; align-items:center; justify-content:center;
    font-family: var(--label); font-weight:500; font-size:30px; line-height:1; }
  .fd-tile svg { width:52%%; height:52%%; }
  .fd-name { flex:1; min-width:0; font-weight:500; font-size:%dpx; line-height:1.2; white-space:nowrap; }
  .fd-size { flex:none; font-family: var(--label); font-weight:500; font-size:%dpx; white-space:nowrap; }
  .fd-status { height:%dpx; margin-top:%dpx; display:flex; align-items:center; gap:%dpx; opacity:0; }
  .fd-st { display:grid; font-size:%dpx; line-height:1.2; white-space:nowrap; }
  .fd-st > span { grid-area:1 / 1; }
  .fd-check { width:%dpx; height:%dpx; border-radius:50%%; flex:none; display:flex; align-items:center; justify-content:center; opacity:0; }
  .fd-check svg { width:56%%; height:56%%; }
  .fd-bar { flex:1; height:%dpx; border-radius:%dpx; overflow:hidden; }
  .fd-fill { width:100%%; height:100%%; border-radius:%dpx; transform:scaleX(0); transform-origin:0 50%%; }
""" % (RADIUS, PAD, BORDER, Z_RADIUS, Z_PAD, HEAD, HEAD_GAP, L_SIZE, ARROW, ARROW, LIST_GAP, ROW_GAP, ROW, R_GAP, R_PAD, TILE_W, TILE_H,
       N_SIZE, S_SIZE, STATUS, FOOT_GAP, BAR_GAP, L_SIZE, CHECK, CHECK, BAR, BAR // 2, BAR // 2)

UPLOAD = ('<svg viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M12 15V4"/><path d="M7 8.5L12 4l5 4.5"/><path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/></svg>')
TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'


def ext(name):
    name = str(name)
    return name.rsplit(".", 1)[1][:4].upper() if "." in name.strip(".") else "FILE"


def kind(name):
    e = ext(name).lower()
    return next((k for k, v in KINDS.items() if e in v), None)


def validate(scene):
    errs = need(scene, ["files"])
    files = scene.get("files") or []
    if not 1 <= len(files) <= MAX_FILES:
        errs.append("a file drop takes 1 to %d files (got %d)" % (MAX_FILES, len(files)))
    for i, f in enumerate(files):
        if not isinstance(f, dict):
            errs.append("file %d is not an object" % i)
            continue
        if not str(f.get("name") or "").strip():
            errs.append("file %d has no name" % i)
        elif len(f["name"]) > MAX_NAME:
            errs.append("file %d's name is %d characters; at most %d" % (i, len(f["name"]), MAX_NAME))
        if f.get("at") is None:
            errs.append("file %d has no at" % i)
        if f.get("size") is not None and len(str(f["size"])) > 8:
            errs.append("file %d: size is a short label (\"24 MB\")" % i)
    d = scene.get("done")
    if d is not None and (not isinstance(d, dict) or d.get("at") is None):
        errs.append("done needs at (the word the upload finishes on)")
    return errs


def height(scene, width):
    n = len(scene["files"])
    zone = 2 * BORDER + 2 * Z_PAD + HEAD + LIST_GAP + n * ROW + (n - 1) * ROW_GAP
    return 2 * PAD + zone + FOOT_GAP + STATUS


def min_width(scene):
    rows = max(TILE_W + R_GAP + E.text_width(f["name"], N_SIZE, "display500") +
               ((R_GAP + E.text_width(str(f["size"]), S_SIZE, "mono500")) if f.get("size") else 0) for f in scene["files"]) + 2 * R_PAD
    head = ARROW + HEAD_GAP + E.text_width(scene.get("label") or "Drop files here", L_SIZE, "display500")
    status = max(E.text_width(scene.get("status") or "Uploading", L_SIZE, "display500"),
                 E.text_width((scene.get("done") or {}).get("label") or "Done", L_SIZE)) + 2 * BAR_GAP + 120 + CHECK
    return int(max(rows + 8, head + 8, status) + 2 * (PAD + BORDER + Z_PAD)) + 1


def render(scene, ctx, box):
    c, mo = ctx.pc, ctx.tokens["motion"]
    sid = ctx.id
    rest = E.rgba(c["accent"], 0)
    rows, js, times = [], [], []
    js.append(ctx.enter("#%s-panel" % sid, ctx.t_in, {"y": 40}))
    for i, f in enumerate(scene["files"]):
        t, attrs = ctx.item(f["at"])
        times.append(t)
        k = kind(f["name"])
        fill, on = c["series"][SERIES[k]] if k else (c["ink"], c["card"])
        mark = ctx.icon(f["icon"]) if f.get("icon") else ctx.esc(ext(f["name"]))
        size = '<span class="fd-size" style="color:%s">%s</span>' % (c["dim"], ctx.esc(f["size"])) if f.get("size") else ""
        rows.append('<div class="fd-row" id="%s-r%d"%s style="%s"><span class="fd-tile" style="background:%s;color:%s">%s</span>'
                    '<span class="fd-name" style="color:%s">%s</span>%s</div>'
                    % (sid, i, attrs, ctx.paper_card(), fill, on, mark, c["ink"], ctx.esc(f["name"]), size))
        # it drops in from above the zone and settles in its row
        js.append("tl.fromTo('#%s-r%d', %s, %s, %.3f);" % (sid, i, js_obj({"opacity": 0, "y": -150, "scale": 0.94}),
                                                           js_obj({"opacity": 1, "y": 0, "scale": 1, "duration": 0.55, "ease": mo["enter_ease"],
                                                                   "immediateRender": False}), t))
        js.append("tl.fromTo('#%s-up', { y: 0 }, %s, %.3f);" % (sid, js_obj({"y": 8, "duration": 0.18, "ease": "power2.out",
                                                                            "immediateRender": False}), t + 0.3))
        js.append("tl.to('#%s-up', %s, %.3f);" % (sid, js_obj({"y": 0, "duration": 0.35, "ease": mo["enter_ease"]}), t + 0.48))
    if any(b < a for a, b in zip(times, times[1:])):
        ctx.fail("the files drop in the order they are listed: each one's at after the one before")
    t_last = times[-1]
    # the zone lights up as the first file comes over it
    js.append("tl.to('#%s-zone', %s, %.3f);" % (sid, js_obj({"borderColor": c["accent"], "backgroundColor": c["accent_soft"],
                                                             "duration": 0.25, "ease": mo["enter_ease"]}), times[0]))
    # the upload: the bar fills after the last file, the status turns to done and the check lands
    d_attrs = ""
    if scene.get("done"):
        t_done, d_attrs = ctx.item(scene["done"]["at"])
    else:
        t_done = min(t_last + 0.45 + 1.6, ctx.t_out - 0.5)
    t_bar = t_last + 0.45
    if t_done - t_bar < 0.5:
        ctx.fail("done at %.2f s leaves the upload no time after the last file (%.2f s); put it a word or two later" % (t_done, t_last))
    dur = min(3.0, t_done - t_bar)
    js.append(ctx.enter("#%s-status" % sid, t_bar, {"y": 10}, dur=0.3))
    js.append("tl.fromTo('#%s-fill', { scaleX: 0 }, %s, %.3f);" % (sid, js_obj({"scaleX": 1, "duration": dur, "ease": "power2.inOut",
                                                                                "immediateRender": False}), t_done - dur))
    js.append("tl.to('#%s-st0', %s, %.3f);" % (sid, js_obj({"opacity": 0, "duration": 0.15, "ease": mo["exit_ease"]}), t_done))
    js.append(ctx.enter("#%s-st1" % sid, t_done + 0.08, {"y": 12}))
    js.append(ctx.enter("#%s-check" % sid, t_done, {"scale": 0.4}, dur=0.5))
    js.append("tl.to('#%s-fill', %s, %.3f);" % (sid, js_obj({"backgroundColor": c["good"], "duration": 0.3, "ease": mo["enter_ease"]}), t_done))
    js.append("tl.to('#%s-zone', %s, %.3f);" % (sid, js_obj({"borderColor": c["line"], "backgroundColor": rest, "duration": 0.4,
                                                             "ease": mo["enter_ease"]}), t_done))
    status = ('<div class="fd-status" id="%s-status"%s><span class="fd-st"><span id="%s-st0" style="font-weight:500;color:%s">%s</span>'
              '<span id="%s-st1" style="font-weight:700;color:%s;opacity:0">%s</span></span>'
              '<span class="fd-bar" style="background:%s"><span class="fd-fill" id="%s-fill" style="display:block;background:%s"></span></span>'
              '<span class="fd-check" id="%s-check" style="background:%s">%s</span></div>'
              % (sid, d_attrs, sid, c["dim"], ctx.esc(scene.get("status") or "Uploading"), sid, c["ink"],
                 ctx.esc((scene.get("done") or {}).get("label") or "Done"), c["track"], sid, c["accent"], sid, c["good"], TICK % c["on_accent"]))
    zone = ('<div class="fd-zone" id="%s-zone" style="border-color:%s;background:%s"><div class="fd-head" style="color:%s">'
            '<span class="fd-up" id="%s-up">%s</span><span>%s</span></div><div class="fd-list">%s</div></div>'
            % (sid, c["line"], rest, c["dim"], sid, UPLOAD % c["accent"], ctx.esc(scene.get("label") or "Drop files here"), "".join(rows)))
    return '<div class="fd" id="%s-panel" style="%s">%s%s</div>' % (sid, ctx.paper_card(), zone, status), js
