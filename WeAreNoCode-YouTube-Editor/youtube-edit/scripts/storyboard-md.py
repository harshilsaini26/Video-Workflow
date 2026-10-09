#!/usr/bin/env python3
"""storyboard-md.py: render the delivery STORYBOARD.md (time / beat / what is on screen) from one or more
storyboard.json files, so the review document is generated from the same source the composition is built from.

Usage: python3 storyboard-md.py --title "Hook v2" --note "what changed" --project videos/<p>/C0001:01-hook:"Part 1" ... --out videos/<p>/STORYBOARD.md

Every format compose.py builds is described, whatever shape its items take ([text, t], [text, t, "anchor"],
{"text": .., "at": ..}, the dock's [src, label, t], the stats' {"value", "label"}). A format this script doesn't know
is listed by its type and whatever text it carries, never a crash.
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--title", required=True)
ap.add_argument("--note", action="append", default=[])
ap.add_argument("--concern", action="append", default=[])
ap.add_argument("--project", action="append", required=True, help="<dir>:<slug>:<title>")
ap.add_argument("--out", required=True)
args = ap.parse_args()

MEDIA = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4", ".mov", ".webm")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def fmt_num(v):
    return ("%g" % v) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)


def words(v):
    """The readable text of one item, whatever its shape."""
    if v is None or isinstance(v, bool):
        return ""
    if isinstance(v, (int, float)):
        return fmt_num(v)
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        if "value" in v:   # a stat tile: 250+ Videos
            return ("%s%s%s %s" % (v.get("prefix", ""), fmt_num(v["value"]), v.get("suffix", ""), words(v.get("label")))).strip()
        for k in ("text", "label", "title", "query", "head", "center"):
            if v.get(k):
                return words(v[k])
        return ""
    if isinstance(v, (list, tuple)):
        # the first string that isn't a media path ([text, t], [text, t, "anchor"], the dock's [src, label, t]);
        # "-" (no anchor) and "em" (an equation term's emphasis flag) are markers, not words. A label that is itself
        # a file name ("demo.mp4") is skipped for the next string: none of compose.py's item shapes put one first.
        for x in v:
            if isinstance(x, str) and x not in ("-", "em") and not x.lower().endswith(MEDIA):
                return x
        return ""
    return str(v)


def join(items, sep=", "):
    return sep.join(w for w in (words(i) for i in (items or [])) if w)


def lead(*parts):
    """'Eyebrow: rest', skipping the empty parts."""
    parts = [p for p in parts if p]
    return ": ".join(parts)


def base(p):
    return os.path.basename(p) if isinstance(p, str) else ""


WHAT = {
    "line": lambda b: "lower line (%s%s)" % (b.get("color", "cyan"), ", shimmer" if b.get("shimmer") else ""),
    "logo": lambda b: "logo card + pop", "list": lambda b: "glass list card", "bullets": lambda b: "pushed-over bullets",
    "chip": lambda b: "punchline chip", "vignette": lambda b: "vignette + grain (deadpan)", "pointer": lambda b: "description pointer",
    "site": lambda b: "full-screen site cutaway (%s)" % b.get("domain", ""), "grid": lambda b: "thumbnail grid + cursor click",
    "scene": lambda b: "animated scene: %s" % b.get("kind", ""),
    "browser3d": lambda b: "3D floating browser (%s) [DRAFT]" % b.get("domain", ""),
    "fan3d": lambda b: "3D fan of screenshots [DRAFT]", "stats": lambda b: "stat tiles, count-up [DRAFT]",
    "growth": lambda b: "growth card%s [DRAFT]" % (", bars morph to a line" if b.get("morph") else ""),
    "bars": lambda b: "bar comparison [DRAFT]", "pipeline": lambda b: "pipeline [DRAFT]", "hub": lambda b: "hub and spokes [DRAFT]",
    "equation": lambda b: "equation [DRAFT]", "wall": lambda b: "slot wall [DRAFT]", "popout": lambda b: "glass pop-out [DRAFT]",
    "flow": lambda b: "flowing paths [DRAFT]", "dashzoom": lambda b: "dashboard zoom [DRAFT]", "lens": lambda b: "glass focus [DRAFT]",
    "search": lambda b: "search → results [DRAFT]", "dock": lambda b: "magnetic dock [DRAFT]", "masktitle": lambda b: "masked title [DRAFT]",
    "player": lambda b: "button → player [DRAFT]", "image": lambda b: "image reveal (%s) [DRAFT]" % b.get("frame", "card"),
    "layers": lambda b: "exploded layers [DRAFT]",
    "world": lambda b: "world: camera over a canvas (%d nodes)" % len(b.get("nodes") or []),
    "deck": lambda b: "deck: numbered parts", "pills": lambda b: "pills (%s)" % b.get("layout", "sides"),
    "chat": lambda b: "chat (%s)" % b.get("frame", "float"), "doc": lambda b: "doc read (%s)" % b.get("domain", ""),
    "clip": lambda b: "video cutaway",
}

TEXT = {
    "logo": lambda b: base(b.get("src")),
    "site": lambda b: base(b.get("src")),
    "grid": lambda b: "%d of the channel's own thumbnails, click on tile %d" % (len(b.get("images") or []), int(num(b.get("click_index"))) + 1),
    "fan3d": lambda b: lead(b.get("label"), "%d screenshots" % len(b.get("images") or [])),
    "browser3d": lambda b: lead(b.get("label"), base(b.get("src"))),
    "growth": lambda b: lead(b.get("eyebrow"), ("%s%s%s %s" % (b.get("prefix", ""), fmt_num(b.get("value", "")), b.get("suffix", ""), b.get("sub", ""))).strip()),
    "bars": lambda b: lead(b.get("title"), join(["%s %s" % (words(r.get("label")), words(r.get("text") or r.get("value"))) for r in b.get("rows") or [] if isinstance(r, dict)])),
    "pipeline": lambda b: lead(b.get("title"), join(b.get("steps"), " → ")),
    "hub": lambda b: lead(b.get("center"), join(b.get("spokes"))),
    "equation": lambda b: join(b.get("terms"), " "),
    "wall": lambda b: join(b.get("slots")),
    "flow": lambda b: " → ".join(x for x in (words(b.get("source")), join(b.get("outputs")), words(b.get("result"))) if x),
    "dashzoom": lambda b: words((b.get("card") or {}).get("label")) + (" " + fmt_num((b.get("card") or {}).get("value")) if (b.get("card") or {}).get("value") is not None else ""),
    "lens": lambda b: lead(b.get("title"), join([" ".join(words(x) for x in r) if isinstance(r, (list, tuple)) else words(r) for r in b.get("rows") or []])),
    "search": lambda b: lead('"%s"' % b.get("query", ""), join(b.get("results"))),
    "masktitle": lambda b: lead(b.get("eyebrow"), " · ".join(x for x in (b.get("text"), b.get("sub")) if x)),
    "player": lambda b: lead(b.get("label"), b.get("title")),
    "image": lambda b: b.get("label") or base(b.get("src")),
    "layers": lambda b: lead(b.get("title"), join(b.get("layers"))),
    "world": lambda b: lead(b.get("title") or b.get("label"), join(b.get("nodes"))),
    "deck": lambda b: lead(b.get("head"), join(b.get("cards"))),
    "chat": lambda b: " / ".join("%s: %s" % (m[0], m[1]) for m in b.get("messages") or [] if isinstance(m, (list, tuple)) and len(m) > 1),
    "doc": lambda b: lead(b.get("title"), join(['"%s"' % words(m) for m in b.get("marks") or [] if words(m)])),
    "clip": lambda b: lead(b.get("label"), join(b.get("items"))) or base(b.get("src")),
}


def text_of(b):
    t = b.get("type")
    if t in TEXT:
        return TEXT[t](b)
    if b.get("text"): return words(b["text"])
    if b.get("items"): return lead(b.get("eyebrow") or b.get("title"), join(b["items"]))
    if b.get("label"): return words(b["label"])
    if b.get("images"): return "%d images" % len(b["images"])
    if b.get("src"): return base(b["src"])
    return ""


def cell(s):
    """Safe inside a markdown table cell."""
    return " ".join(str(s).split()).replace("|", "\\|")


out = ["# " + args.title, ""]
if args.note:
    out += ["## What changed", ""] + ["- " + n for n in args.note] + [""]
if args.concern:
    out += ["## Concerns to check", ""] + ["- " + c for c in args.concern] + [""]
for spec in args.project:
    d, slug, title = spec.split(":", 2)
    with open(os.path.join(d, "storyboard.json")) as f:
        s = json.load(f)
    out += ["## %s: %s (%s, %.1f s)" % (slug, title, s.get("id", "?"), num(s.get("duration"))), "", "| Time | Beat | On screen |", "|---|---|---|"]
    if s.get("tag"):
        t = s["tag"]
        out.append("| %.1f - %.1f | progress tag | %s of %s · %s |" % (num(t.get("in")), num(t.get("out")), t.get("n", "?"), t.get("of", "?"), cell(t.get("label", ""))))
    for b in s.get("beats", []):
        tr = (" · " + str(b["transition"]) + " cut") if b.get("transition") else ""
        what = WHAT.get(b.get("type"), lambda b: str(b.get("type", "?")))(b)
        out.append("| %.1f - %.1f | %s%s | %s |" % (num(b.get("in")), num(b.get("out")), cell(what), tr, cell(text_of(b))))
    moves = [op for op in s.get("camera", []) if isinstance(op, (list, tuple)) and len(op) > 1 and op[0] != "set"]
    out.append("| camera | %d moves | %s |" % (len(moves), ", ".join("%s %.1f" % (op[0], num(op[1])) for op in moves)))
    out.append("")
with open(args.out, "w") as f:
    f.write("\n".join(out))
print("wrote", args.out, len(out), "lines")
