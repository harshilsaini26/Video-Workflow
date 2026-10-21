#!/usr/bin/env python3
"""render-layers.py: each layer page from layer-pages.py as a transparent clip (ProRes 4444 with alpha, HyperFrames
`render --format mov`) for the editor hand-off. These are short pieces of the reel, never the reel itself.

  python3 render-layers.py --public videos/<p>/public --out videos/<p>/edit/media/gfx [--only l0,l3] [--workers 2]
      [--hf "npx --yes hyperframes@0.8.171"]      # default: $HYPERFRAMES_CMD, else "npx --no-install hyperframes"

Writes <out>/<name>.mov per layer and checks each one has an alpha channel (pix_fmt yuva*); a layer that fails is
named and the script exits 1 after trying the rest.
"""
import argparse, json, os, re, shlex, subprocess, sys


def pix_fmt(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=pix_fmt", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--public", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", default="2")
    ap.add_argument("--hf", default=os.environ.get("HYPERFRAMES_CMD") or "npx --no-install hyperframes")
    a = ap.parse_args()
    lj = os.path.join(a.public, "layers.json")
    if not os.path.isfile(lj):
        print("RENDER-LAYERS FAIL: no %s (run layer-pages.py --index %s first)" % (lj, os.path.join(a.public, "index.html")))
        sys.exit(1)
    with open(lj, encoding="utf-8") as f:
        layers = json.load(f)
    with open(os.path.join(a.public, "index.html"), encoding="utf-8") as f:
        m = re.search(r'data-fps="(\d+)"', f.read())
    fps = m.group(1) if m else "60"
    only = [x for x in a.only.split(",") if x]
    os.makedirs(a.out, exist_ok=True)
    bad = []
    for l in layers:
        if only and l["name"] not in only:
            continue
        dst = os.path.abspath(os.path.join(a.out, l["name"] + ".mov"))
        cmd = shlex.split(a.hf) + ["render", os.path.abspath(a.public), "-c", l["page"], "--format", "mov", "--fps", fps,
                                   "-o", dst, "--workers", str(a.workers), "--quiet"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        pf = pix_fmt(dst) if os.path.isfile(dst) else ""
        if r.returncode != 0 or not pf.startswith("yuva"):
            bad.append(l["name"])
            print("  %-10s FAIL %s" % (l["name"], (r.stderr or r.stdout).strip().splitlines()[-1:] if r.returncode else "no alpha (pix_fmt %s)" % pf))
        else:
            print("  %-10s %6.2f s  %s  %s" % (l["name"], l["t_out"] - l["t_in"], pf, dst))
    if bad:
        print("RENDER-LAYERS FAIL: %s" % ", ".join(bad))
        sys.exit(1)
    print("RENDER-LAYERS PASS")


if __name__ == "__main__":
    main()
