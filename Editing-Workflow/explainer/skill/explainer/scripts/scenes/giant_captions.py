"""giant-captions: the voice's own words, one to three at a time, huge in the middle of the frame, each word landing on
its own time (the reels look where the words are the picture). The caption band steps aside while it runs (the
composer leaves those phrases out), so the words are never on screen twice.

  {"type": "giant-captions", "keywords": ["RAG"]}

The words come from transcript.json between the scene's in and out; a phrase breaks after punctuation, at three words,
or when the next word would make it too wide to stay large. Keywords take the accent; the rest the ground's ink.
"""
import re
import explainer_lib as E
from explainer_lib import norm
from scenes import js_obj

TYPE = "giant-captions"
HERO_CSS = ".gc-c"                   # set in the look's hero face (E.hero()), measured with its glyphs
MAX_SCALE = 1.0                  # it sizes itself to its width
BAKED = True                     # its sizes depend on the width it is given: measured there
BIG, SMALL = 200, 120            # a phrase's size: as big as its width allows, between these
H = 240                          # one line at the biggest size, with room above and below
MAX_WORDS = 3
DECOR_KEYS = {"keywords"}       # they only colour what the voice says (its numbers are sourced in the script)

CSS = """
  .gc { position:relative; width:100%%; }
  .gc-c { position:absolute; left:0; right:0; top:0; height:%dpx; display:flex; align-items:center; justify-content:center;
    gap:0 .22em; font-weight:700; line-height:1; letter-spacing:-.03em; white-space:nowrap; visibility:hidden; }
  .gc-w { display:inline-block; opacity:0; }
""" % H



def validate(scene):
    kw = scene.get("keywords", [])
    if not isinstance(kw, list) or not all(isinstance(k, str) for k in kw):
        return ["keywords is a list of words"]
    return []


def phrases(words, width):
    """[(size, [(index, word)])]: the words split into phrases that each stay at SMALL or larger at this width."""
    out, cur = [], []
    fits = lambda ws: E.text_width(" ".join(w["text"] for _, w in ws), SMALL, E.hero()["glyphs"], spacing=-0.03) <= width - 8
    for i, w in words:
        if cur and (len(cur) >= MAX_WORDS or not fits(cur + [(i, w)]) or re.search(r"[.,!?;:]$", cur[-1][1]["text"])):
            out.append(cur)
            cur = []
        cur.append((i, w))
    if cur:
        out.append(cur)
    sized = []
    for ws in out:
        w1 = E.text_width(" ".join(w["text"] for _, w in ws), 100, E.hero()["glyphs"], spacing=-0.03) / 100.0
        sized.append((max(SMALL, min(BIG, int((width - 8) / max(w1, 1e-6)))), ws))
    return sized


def height(scene, width):
    return H


def min_width(scene):
    return 300


def render(scene, ctx, box):
    sid, c = ctx.id, ctx.c
    keys = {norm(k) for k in scene.get("keywords", [])}
    words = [(i, w) for i, w in enumerate(ctx.words) if ctx.t_in - 1e-6 <= float(w["start"]) < ctx.t_out]
    groups = phrases(words, box[2])
    parts, js = [], []
    for k, (size, ws) in enumerate(groups):
        start = max(ctx.t_in, float(ws[0][1]["start"]) - 0.05)
        end = max(start + 0.1, float(groups[k + 1][1][0][1]["start"]) - 0.05) if k + 1 < len(groups) else ctx.t_out
        spans = "".join('<span class="gc-w" id="%s-w%d" style="color:%s">%s</span>'
                        % (sid, i, c["accent"] if norm(w["text"]) in keys else c["ink"], ctx.esc(w["text"])) for i, w in ws)
        parts.append('<div class="gc-c" id="%s-c%d" style="font-size:%dpx">%s</div>' % (sid, k, size, spans))
        js.append("tl.set('#%s-c%d', { visibility: 'visible' }, %.3f);" % (sid, k, start))
        for i, w in ws:
            js.append("tl.fromTo('#%s-w%d', %s, %s, %.3f);" % (sid, i, js_obj({"opacity": 0, "y": 40, "scale": 0.9}),
                                                               js_obj({"opacity": 1, "y": 0, "scale": 1, "duration": 0.25,
                                                                       "ease": "power3.out", "immediateRender": False}),
                                                               max(ctx.t_in, float(w["start"]) - 0.05)))
        if k + 1 < len(groups):
            js.append("tl.set('#%s-c%d', { visibility: 'hidden' }, %.3f);" % (sid, k, end))
    return '<div class="gc" style="height:%dpx">%s</div>' % (H, "".join(parts)), js
