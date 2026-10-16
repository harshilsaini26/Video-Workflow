"""sheet: a small spreadsheet; rows stagger in, a row or cell lights up on its word (SPEC §6.2)."""
import explainer_lib as E
from scenes import js_obj, need, stagger_for

TYPE = "sheet"
MAX_ROWS = 8
ROW, SIZE = 64, 34            # row height; cell text, DM Sans 500 (the first row 700)
FX, FX_GAP, FX_SIZE = 64, 16, 30
CELL_PAD = 18

CSS = """
  .sh { width:100%%; opacity:0; }
  .sh-fx { height:%dpx; margin-bottom:%dpx; border-radius:14px; display:flex; align-items:center; padding:0 22px; gap:18px;
    font-family: var(--label); font-weight:500; font-size:%dpx; white-space:nowrap; overflow:hidden; }
  .sh-fx b { font-style:italic; opacity:.6; }
  .sh-grid { position:relative; border-radius:14px; overflow:hidden; }
  .sh-row { display:flex; height:%dpx; opacity:0; }
  .sh-cell { flex:1 1 0; min-width:0; display:flex; align-items:center; padding:0 %dpx; font-size:%dpx; font-weight:500;
    white-space:nowrap; font-variant-numeric: tabular-nums; }
  .sh-row.head .sh-cell { font-weight:700; }
  .sh-hl { position:absolute; border:5px solid; border-radius:8px; opacity:0; pointer-events:none; }
""" % (FX, FX_GAP, FX_SIZE, ROW, CELL_PAD, SIZE)


def _cols(scene):
    return max(len(r) for r in scene["rows"])


def validate(scene):
    errs = need(scene, ["rows"])
    rows = scene.get("rows") or []
    if not 1 <= len(rows) <= MAX_ROWS:
        errs.append("a sheet shows 1 to %d rows (got %d)" % (MAX_ROWS, len(rows)))
    if any(not isinstance(r, list) or not r for r in rows):
        errs.append("each row is a list of cells")
        return errs
    hl = scene.get("highlight")
    if hl:
        if hl.get("at") is None:
            errs.append("highlight needs at")
        if "row" in hl:
            if not isinstance(hl["row"], int) or not 0 <= hl["row"] < len(rows):
                errs.append("highlight row %r is not one of the %d rows" % (hl["row"], len(rows)))
        elif "cell" in hl:
            rc = hl["cell"]
            if not (isinstance(rc, list) and len(rc) == 2 and 0 <= rc[0] < len(rows) and 0 <= rc[1] < len(rows[rc[0]])):
                errs.append("highlight cell %r is not in the sheet" % (rc,))
        else:
            errs.append("highlight names a row or a cell")
    return errs


def height(scene, width):
    return (FX + FX_GAP if scene.get("formula") else 0) + ROW * len(scene["rows"])


def min_width(scene):
    widest_cell = max(E.text_width(str(c), SIZE) for r in scene["rows"] for c in r)
    return int(_cols(scene) * (widest_cell + 2 * CELL_PAD)) + 1


def render(scene, ctx, box):
    c = ctx.c
    sid, width = ctx.id, box[2]
    ncol = _cols(scene)
    grid_bg, head_bg, line = c["card"], c["bg"], c["line"]
    rows = []
    for i, r in enumerate(scene["rows"]):
        cells = "".join('<div class="sh-cell" style="border-right:1px solid %s">%s</div>' % (line, ctx.esc(r[k]) if k < len(r) else "")
                        for k in range(ncol))
        rows.append('<div class="sh-row%s" style="background:%s;border-bottom:1px solid %s;color:%s">%s</div>'
                    % (" head" if i == 0 else "", head_bg if i == 0 else "transparent", line, ctx.ink, cells))
    fx = ""
    if scene.get("formula"):
        fx = '<div class="sh-fx" style="background:%s;color:%s"><b>fx</b>%s</div>' % (head_bg, ctx.ink, ctx.esc(scene["formula"]))
    js = [ctx.enter("#%s .sh" % sid, ctx.t_in, {"y": 30}),
          ctx.enter("#%s .sh-row" % sid, ctx.t_in + 0.12, {"y": 12}, stagger=stagger_for(len(rows), 0.07))]
    hl_html = ""
    hl = scene.get("highlight")
    if hl:
        t = ctx.at(hl["at"])
        cw = width / ncol
        if "row" in hl:
            x, y, w = 0, hl["row"] * ROW, width
        else:
            x, y, w = hl["cell"][1] * cw, hl["cell"][0] * ROW, cw
        hl_html = ('<div class="sh-hl" id="%s-hl" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-color:%s;background:%s"></div>'
                   % (sid, x, y, w, ROW, c["accent"], c["accent_soft"]))
        js.append(ctx.enter("#%s-hl" % sid, t, {"scale": 1.08}))
    html = '<div class="sh">%s<div class="sh-grid" style="background:%s">%s%s</div></div>' % (fx, grid_bg, "".join(rows), hl_html)
    return html, js
