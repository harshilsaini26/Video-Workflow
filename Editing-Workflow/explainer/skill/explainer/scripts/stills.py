#!/usr/bin/env python3
"""stills.py: the Checkpoint B stills, as the reel will show them (SOP S10).

  stills.py --index videos/<p>/public/index.html --out videos/<p>/snaps/stills

The RAG reel's creator approved stills taken mid-entrance, so half-empty scenes looked approved. Here every scene gets
one full-size still at its settled moment (everything in it arrived, just before its exit), the hook gets three (0.3,
0.7 and 1.0 s: it must be whole by 1.0 s), and a contact sheet (sheet.png, with FFmpeg) puts them side by side.
The folder is emptied first, so no still from an earlier build survives. STILLS.md lists every still with its time.
Uses the puppeteer and Chrome that gate E5 uses (layout_check.find_puppeteer / find_chrome).
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout_check as LC

HOOK = (0.3, 0.7, 1.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.isdir(a.out):                          # stills are rewritten fresh, so their folder holds nothing else
        other = sorted(n for n in os.listdir(a.out) if not (n.endswith(".png") or n == "STILLS.md"))
        if other:
            sys.exit("%s holds other work (%s): give stills their own folder, such as snaps/stills" % (a.out, ", ".join(other[:5])))
    pub = os.path.dirname(os.path.abspath(a.index))
    mp = os.path.join(pub, "moments.json")
    if not os.path.exists(mp):
        sys.exit("no moments.json next to %s: compose the page first" % a.index)
    with open(mp, encoding="utf-8") as f:
        moments = json.load(f)
    pdir, chrome = LC.find_puppeteer(), LC.find_chrome()
    if not (shutil.which("node") and pdir and chrome):
        sys.exit("needs node, puppeteer and Chrome: install HyperFrames (npx hyperframes browser ensure)")
    if os.path.isdir(a.out):
        for n in os.listdir(a.out):
            os.remove(os.path.join(a.out, n))
    os.makedirs(a.out, exist_ok=True)
    shots, rows = [], []
    for t in HOOK:
        name = "hook-%.2f.png" % t
        shots.append({"t": t, "file": os.path.join(a.out, name)})
        rows.append((name, t, moments["scenes"][0]["id"], "the hook at %.1f s" % t))
    for k, (s, smp) in enumerate(zip(moments["scenes"], LC.samples(moments)), 1):
        name = "%02d-%s.png" % (k, s["id"])
        shots.append({"t": smp["t"], "file": os.path.join(a.out, name)})
        rows.append((name, smp["t"], s["id"], "settled (%s, %.2f to %.2f s)" % (s.get("type", "?"), s["in"], s["out"])))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"index": os.path.abspath(a.index), "shots": shots, "puppeteer_dir": pdir, "chrome": chrome}, f)
        job = f.name
    try:
        r = subprocess.run([shutil.which("node"), os.path.join(HERE, "stills.mjs"), job], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
    finally:
        os.unlink(job)
    if r.returncode:
        sys.exit("stills.mjs failed: " + (r.stderr or r.stdout)[-800:])
    sheet = ""
    if shutil.which("ffmpeg"):
        files = [s["file"] for s in shots]
        cols = 6
        rows_n = (len(files) + cols - 1) // cols
        args = ["ffmpeg", "-v", "error", "-y"]
        for p in files:
            args += ["-i", p]
        pads = "".join("[%d]scale=270:480[s%d];" % (i, i) for i in range(len(files)))
        stack = "".join("[s%d]" % i for i in range(len(files)))
        blanks = cols * rows_n - len(files)
        if blanks:
            pads += "color=c=gray:s=270x480:d=1[b];[b]split=%d%s;" % (blanks, "".join("[e%d]" % i for i in range(blanks)))
            stack += "".join("[e%d]" % i for i in range(blanks))
        layout = "|".join("%d_%d" % ((i % cols) * 270, (i // cols) * 480) for i in range(cols * rows_n))
        fc = pads + stack + "xstack=inputs=%d:layout=%s[out]" % (cols * rows_n, layout)
        sheet_path = os.path.join(a.out, "sheet.png")
        sr = subprocess.run(args + ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", sheet_path], capture_output=True, text=True, encoding="utf-8", errors="replace")
        sheet = "sheet.png" if sr.returncode == 0 else ""
    with open(os.path.join(a.out, "STILLS.md"), "w", encoding="utf-8") as f:
        f.write("# Checkpoint B stills\n\nEvery scene once it has settled (all of it arrived), and the hook at 0.3, 0.7 and 1.0 s."
                " Look at each full-size still, not only the sheet.\n\n| Still | Time | Scene | Moment |\n|---|---|---|---|\n")
        f.write("".join("| %s | %.2f s | %s | %s |\n" % row for row in rows))
        if sheet:
            f.write("\nThe sheet: %s\n" % sheet)
    print("wrote %d stills%s to %s" % (len(shots), " and the sheet" if sheet else "", a.out))


if __name__ == "__main__":
    main()
