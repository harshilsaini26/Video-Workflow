"""doc: a document page on light paper, a title and its paragraphs (real text, or grey bars standing in for filler). On
its word a passage lights up: a highlighter sweeps behind its lines, one line after the next, and a source tag lands on
the passage's corner. For "the retriever found this paragraph".

  {"type": "doc", "name": "leave-policy.pdf", "title": "Annual leave", "source": "s1", "blocks": [
     {"text": "Leave is earned monthly from your first day."},
     {"filler": 2},
     {"text": "Full-time staff get 24 days of paid leave a year.", "at": "word:5", "tag": "Section 3.2"},
     {"filler": 3}]}

A block with `at` is a passage that highlights on that word (one to three of them); `tag` is the label it gets. The
file's name, the tags and the filler counts are furniture (DECOR_KEYS); a digit in the text is a claim and needs the scene's source.
"""
import explainer_lib as E
from scenes import js_obj, line_px, need, stagger_for, widest

TYPE = "doc"
DECOR_KEYS = ("name", "tag", "filler")   # the file, the labels, a count of grey lines
MAX_SCALE = 1.25                  # a page, not a poster: 32 px text is drawn at 40 px at most
BAR, B_ICON, B_SIZE = 68, 32, 30  # the viewer's bar: an icon and the file name, JetBrains Mono 500
PAD_T, PAD_X, PAD_B = 32, 40, 36
T_SIZE, T_LH, T_GAP = 48, 1.2, 24             # the title, DM Sans 700, and its gap to the first block
P_SIZE, P_LINE, B_GAP = 32, 46, 20            # a paragraph, DM Sans 500; the gap between blocks
BAR_H = 18                                     # a filler line's bar, centred in its line
TAG_H, TAG_GAP, TAG_SIZE, TAG_PAD = 44, 8, 30, 18
FILLER = (0.96, 0.9, 0.98, 0.86, 0.93, 0.89)   # a filler block's bar widths; its last line is short
MAX_BLOCKS, MAX_FILLER, MAX_MARKS = 8, 6, 3
# kerning and ligatures are off on the page, so Chromium wraps lines exactly where the glyph widths (text_lines) say

CSS = """
  .doc { width:100%%; border-radius:28px; overflow:hidden; opacity:0; font-kerning:none; font-variant-ligatures:none; }
  .doc-bar { height:%dpx; display:flex; align-items:center; gap:14px; padding:0 30px; }
  .doc-bar svg { width:%dpx; height:%dpx; flex:none; }
  .doc-name { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:1; white-space:nowrap; }
  .doc-body { padding:%dpx %dpx %dpx; display:flex; flex-direction:column; gap:%dpx; }
  .doc-title { font-weight:700; font-size:%dpx; line-height:%dpx; letter-spacing:-.01em; margin-bottom:%dpx; opacity:0; }
  .doc-b { opacity:0; }
  .doc-p { font-weight:500; font-size:%dpx; line-height:%dpx; }
  .doc-mark { background-repeat:no-repeat; background-size:0%% 100%%; }
  .doc-fill { height:%dpx; display:flex; align-items:center; }
  .doc-fill i { display:block; height:%dpx; border-radius:%dpx; }
  .doc-tagrow { height:%dpx; margin-bottom:%dpx; display:flex; justify-content:flex-end; }
  .doc-tag { height:%dpx; padding:0 %dpx; border-radius:12px 12px 4px 12px; display:flex; align-items:center; font-weight:700;
    font-size:%dpx; line-height:1; white-space:nowrap; opacity:0; }
""" % (BAR, B_ICON, B_ICON, B_SIZE, PAD_T, PAD_X, PAD_B, B_GAP, T_SIZE, line_px(T_SIZE, T_LH), T_GAP - B_GAP, P_SIZE, P_LINE,
       P_LINE, BAR_H, BAR_H // 2, TAG_H, TAG_GAP, TAG_H, TAG_PAD, TAG_SIZE)


def validate(scene):
    errs = need(scene, ["blocks"])
    blocks = scene.get("blocks") or []
    if not isinstance(blocks, list):
        return errs + ["blocks is a list"]
    if not 1 <= len(blocks) <= MAX_BLOCKS:
        errs.append("a doc holds 1 to %d blocks (got %d)" % (MAX_BLOCKS, len(blocks)))
    marks = 0
    for i, b in enumerate(blocks):
        if not isinstance(b, dict):
            errs.append("block %d is not an object" % i)
            continue
        if "filler" in b:
            n = b["filler"]
            if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= MAX_FILLER:
                errs.append("block %d: filler is a number of grey lines, 1 to %d" % (i, MAX_FILLER))
            if b.get("text") or b.get("at") is not None:
                errs.append("block %d: a filler block has no text and no at (only a passage with text highlights)" % i)
            continue
        if not str(b.get("text", "")).strip():
            errs.append("block %d has no text (or give it \"filler\": a number of grey lines)" % i)
        if b.get("at") is not None:
            marks += 1
        elif b.get("tag"):
            errs.append("block %d has a tag but no at: the tag lands when the passage highlights" % i)
    if not 1 <= marks <= MAX_MARKS:
        errs.append("a doc highlights 1 to %d passages: give the passage the voice names an at (got %d)" % (MAX_MARKS, marks))
    return errs


def _title_lines(scene, inner):
    return E.text_lines(scene["title"], T_SIZE, inner, spacing=-0.01) if scene.get("title") else 0


def _block_h(b, inner):
    if "filler" in b:
        return P_LINE * b["filler"]
    h = P_LINE * E.text_lines(b["text"], P_SIZE, inner, "display500")
    return h + (TAG_H + TAG_GAP if b.get("tag") and b.get("at") is not None else 0)


def height(scene, width):
    inner = width - 2 * PAD_X
    h = (BAR if scene.get("name") else 0) + PAD_T + PAD_B
    if scene.get("title"):
        h += line_px(T_SIZE, T_LH) * _title_lines(scene, inner) + T_GAP
    blocks = scene["blocks"]
    return h + sum(_block_h(b, inner) for b in blocks) + B_GAP * (len(blocks) - 1)


def min_width(scene):
    w = widest([(b.get("text"), P_SIZE) for b in scene["blocks"]] + [(scene.get("title"), T_SIZE)], pad=2 * PAD_X)
    for b in scene["blocks"]:
        if b.get("tag"):
            w = max(w, int(E.text_width(b["tag"], TAG_SIZE)) + 1 + 2 * TAG_PAD + 2 * PAD_X)
    if scene.get("name"):
        w = max(w, 64 + B_ICON + 14 + int(E.text_width(scene["name"], B_SIZE, "mono500")) + 1)
    return w


def render(scene, ctx, box):
    p, mo = ctx.pc, ctx.tokens["motion"]        # a document is light paper on any ground
    sid = ctx.id
    hl = E.rgba(p["accent"], 0.22)              # the highlighter: what the voice is talking about
    parts, js = [], []
    if scene.get("title"):
        parts.append('<div class="doc-title" style="color:%s">%s</div>' % (p["ink"], ctx.esc(scene["title"])))
    inner = box[2] - 2 * PAD_X
    for i, b in enumerate(scene["blocks"]):
        if "filler" in b:
            n = b["filler"]
            bars = "".join('<div class="doc-fill"><i style="width:%d%%;background:%s"></i></div>'
                           % (round(100 * (0.58 if k == n - 1 and n > 1 else FILLER[(i + k) % len(FILLER)])), p["line"]) for k in range(n))
            parts.append('<div class="doc-b">%s</div>' % bars)
            continue
        if b.get("at") is None:
            parts.append('<div class="doc-b doc-p" style="color:%s">%s</div>' % (p["ink"], ctx.esc(b["text"])))
            continue
        t, attrs = ctx.item(b["at"])
        tag = ""
        if b.get("tag"):
            tag = '<div class="doc-tagrow"><div class="doc-tag" id="%s-t%d" style="background:%s;color:%s">%s</div></div>' % (
                sid, i, p["accent"], p["on_accent"], ctx.esc(b["tag"]))
        parts.append('<div class="doc-b">%s<div class="doc-p" style="color:%s"><span class="doc-mark" id="%s-m%d"%s '
                     'style="background-image:linear-gradient(%s, %s)">%s</span></div></div>'
                     % (tag, p["ink"], sid, i, attrs, hl, hl, ctx.esc(b["text"])))
        lines = E.text_lines(b["text"], P_SIZE, inner, "display500")
        # the highlighter runs along each line in turn (the mark's background is laid out as one long strip)
        js.append("tl.fromTo('#%s-m%d', %s, %s, %.3f);" % (sid, i, js_obj({"backgroundSize": "0% 100%"}), js_obj(
            {"backgroundSize": "100% 100%", "duration": round(min(1.0, 0.3 + 0.22 * lines), 3), "ease": "power1.inOut",
             "immediateRender": False}), t))
        if tag:
            js.append(ctx.enter("#%s-t%d" % (sid, i), t + 0.2, {"x": 24}))
    bar = ""
    if scene.get("name"):
        bar = '<div class="doc-bar" style="background:%s"><span style="color:%s;display:flex">%s</span><span class="doc-name" style="color:%s">%s</span></div>' % (
            p["chrome"], p["accent"], ctx.icon("file-text"), p["dim"], ctx.esc(scene["name"]))
    html = '<div class="doc" id="%s-page" style="%s">%s<div class="doc-body">%s</div></div>' % (sid, ctx.paper_card(), bar, "".join(parts))
    n = len(scene["blocks"]) + bool(scene.get("title"))
    js = [ctx.enter("#%s-page" % sid, ctx.t_in, {"y": 40}),
          ctx.enter("#%s .doc-title, #%s .doc-b" % (sid, sid), ctx.t_in + 0.15, {"y": 14}, stagger=stagger_for(n, 0.06))] + js
    return html, js
