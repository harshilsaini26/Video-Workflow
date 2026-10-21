#!/usr/bin/env python3
"""layer-pages.py: a composed page (explainer, reels, long-form: the kit markup) as one page per layer, for the editor
hand-off. Each layer page shows its layer alone on a transparent ground, timed from 0 to the layer's length, so
render-layers.py can write it as a transparent clip (ProRes 4444) that sits on its own track in the editor.

Layers: ground (.bg), thread (svg.thread), brand (#brand), captions (.cap-layer without #brand), and one per
.card-host (its id without "host-"), each only when the page has it. Footage (<video>) and sound (<audio>) are taken
out of every layer page: they reach the editor as their own clips.

  python3 layer-pages.py --index videos/<p>/public/index.html
  -> public/layer-<name>.html (next to index.html, so its relative asset paths still resolve) and public/layers.json:
     [{"name", "kind": "ground|thread|brand|captions|host", "t_in", "t_out", "page", "ext": "mov|mp4"}]
     (the ground is opaque and runs the whole reel, so it is H.264 .mp4; every other layer is transparent ProRes .mov)
"""
import argparse, json, os, re, sys

GROUPS = (("ground", 'class="bg"', ".bg", None), ("thread", 'class="thread"', "svg.thread", None),
          ("brand", 'id="brand"', "#brand", None), ("captions", "cap-layer", ".cap-layer", "#brand"))
HOST = re.compile(r'class="card-host[^"]*" id="host-([^"]+)"[^>]*?data-start="([-\d.]+)"[^>]*?data-duration="([\d.]+)"')
STAGE = re.compile(r'(<div id="stage" data-composition-id="([^"]+)") data-start="[-\d.]+" data-duration="([\d.]+)"')
REG = re.compile(r'window\.__timelines\[(["\'])(.+?)\1\]\s*=\s*(\w+);')


def fail(msg):
    print("LAYERS FAIL: " + msg)
    sys.exit(1)


def layer_page(page, cid, var, sel, t_in, t_out, minus=None):
    s = re.sub(r"\s*<audio\b[^>]*>\s*</audio>", "", page)
    s = re.sub(r"\s*<video\b[^>]*>\s*</video>", "", s)
    css = ["#stage *:not(:is(%s, %s *)) { visibility:hidden !important; }" % (sel, sel), "%s { visibility:visible; }" % sel,
           "html, body, #stage { background:transparent !important; }"]
    if minus:
        css.append("%s, %s * { visibility:hidden !important; }" % (minus, minus))
    s = s.replace("</head>", "<style>\n  %s\n</style>\n</head>" % "\n  ".join(css), 1)
    s = re.sub(r'(?<!id="stage" data-composition-id="%s" )data-start="([-\d.]+)"' % re.escape(cid),
               lambda m: 'data-start="%.3f"' % (float(m.group(1)) - t_in), s)
    s = STAGE.sub(lambda m: '%s data-start="0" data-duration="%.3f"' % (m.group(1), t_out - t_in), s, count=1)
    s = REG.sub(lambda m: 'const M = window.gsap.timeline({ paused: true }); M.add(%s.tweenFromTo(%.3f, %.3f, { ease: "none" }), 0); '
                          'window.__timelines["%s"] = M;' % (var, t_in, t_out, cid), s, count=1)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--index", required=True)
    a = ap.parse_args()
    if not os.path.isfile(a.index):
        fail("no page at %s (compose first)" % a.index)
    with open(a.index, encoding="utf-8") as f:
        page = f.read()
    st, reg = STAGE.search(page), REG.search(page)
    if not st:
        fail("%s has no composition root (<div id=\"stage\" data-composition-id ...>)" % a.index)
    if not reg:
        fail("%s registers no timeline (window.__timelines[...] = tl;)" % a.index)
    cid, D, var = st.group(2), float(st.group(3)), reg.group(3)
    layers = [(name, kind, sel, 0.0, D, minus) for name, mark, sel, minus in GROUPS for kind in [name] if mark in page]
    layers += [(hid, "host", "#host-" + hid, float(t0), round(float(t0) + float(dur), 3), None) for hid, t0, dur in HOST.findall(page)]
    pub = os.path.dirname(os.path.abspath(a.index))
    out = []
    for name, kind, sel, t_in, t_out, minus in layers:
        rel = "layer-%s.html" % name
        with open(os.path.join(pub, rel), "w", encoding="utf-8") as f:
            f.write(layer_page(page, cid, var, sel, t_in, t_out, minus))
        out.append({"name": name, "kind": kind, "t_in": round(t_in, 3), "t_out": round(t_out, 3), "page": rel,
                    "ext": "mp4" if kind == "ground" else "mov"})   # the ground is opaque and long: H.264, not ProRes 4444
    with open(os.path.join(pub, "layers.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("LAYERS: %d pages (%s) in %s" % (len(out), ", ".join(l["name"] for l in out), pub))


if __name__ == "__main__":
    main()
