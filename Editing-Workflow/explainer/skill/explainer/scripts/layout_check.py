"""layout_check.py: gate E5, run by layout-check.py. Every scene is looked at in Chromium on this machine, at the moment
it is fully built (just before its exit), by two checks that cost no tokens:

  layout-probe.mjs        text over text, text covered by or crossing a shape that is not its card, text spilling out of
                          its card, text or shapes outside the safe area, text drawn under MIN_PX
  hyperframes check       HyperFrames' own layout and WCAG AA contrast pass at the same moments; kept: text overlap,
                          text overflowing or clipped by its box, and contrast failures (captions included)

Puppeteer and Chrome are the ones HyperFrames installed (npm's npx cache, `npx hyperframes browser path`), or
$PUPPETEER_DIR and $CHROME.
"""
import glob, json, os, re, shutil, subprocess, tempfile

import explainer_lib as E

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_PX = 28          # the smallest text a phone viewer reads on the 1080 px frame (labels are 34 px or more by design)
KEEP = ("content_overlap", "text_box_overflow", "clipped_text", "contrast_aa_failure")


def area():
    L = E.L
    return {"left": E.SCENE["left"], "top": E.SCENE["top"], "right": E.SCENE["right"], "bottom": E.SCENE["bottom"],
            "col_top": L.RIGHT_COL_TOP, "narrow_left": L.NARROW["left"], "narrow_right": L.NARROW["right"]}


def npx_dirs():
    dirs = []
    try:
        cache = subprocess.run(["npm", "config", "get", "cache"], capture_output=True, text=True, timeout=30).stdout.strip()
        if cache:
            dirs += sorted(glob.glob(os.path.join(cache, "_npx", "*", "node_modules")), key=os.path.getmtime, reverse=True)
    except (OSError, subprocess.SubprocessError):
        pass
    return dirs + sorted(glob.glob(os.path.expanduser("~/.npm/_npx/*/node_modules")), key=os.path.getmtime, reverse=True)


def find_puppeteer():
    """A folder whose node_modules has puppeteer-core or puppeteer: $PUPPETEER_DIR, this folder, or HyperFrames' npx cache."""
    cands = [os.environ.get("PUPPETEER_DIR", ""), HERE, os.getcwd()] + npx_dirs()
    for c in cands:
        if not c:
            continue
        for mod in ("puppeteer-core", "puppeteer"):
            for base in (os.path.join(c, "node_modules", mod), os.path.join(c, mod)):
                if os.path.exists(os.path.join(base, "package.json")):
                    return c if base.startswith(os.path.join(c, "node_modules")) else os.path.dirname(c)
    return None


def find_chrome():
    """$CHROME, the Chrome HyperFrames renders with (`npx hyperframes browser path`), or a Chromium on PATH."""
    if os.environ.get("CHROME") and os.path.exists(os.environ["CHROME"]):
        return os.environ["CHROME"]
    try:
        r = subprocess.run(["npx", "--no-install", "hyperframes", "browser", "path"], capture_output=True, text=True, timeout=120)
        p = (r.stdout.strip().splitlines() or [""])[-1].strip()
        if p and os.path.exists(p):
            return p
    except (OSError, subprocess.SubprocessError):
        pass
    for c in ["/opt/pw-browsers/chromium"] + [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chromium-browser")]:
        if c and os.path.exists(c):
            return c
    return None


def samples(moments):
    """One moment per scene: just before it starts to leave, when everything in it has arrived."""
    out = []
    for s in moments["scenes"]:
        t = s["out"] - 0.1 if s["out"] - s["in"] > 0.7 else (s["in"] + s["out"]) / 2.0
        out.append({"id": s["id"], "t": round(t, 3)})
    return out


def probe(index, smp):
    pdir, chrome = find_puppeteer(), find_chrome()
    if not (shutil.which("node") and pdir and chrome):
        raise RuntimeError("needs node, puppeteer and Chrome: install HyperFrames (npx hyperframes browser ensure), or set "
                           "PUPPETEER_DIR and CHROME")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"index": index, "samples": smp, "area": area(), "min_px": MIN_PX, "puppeteer_dir": pdir, "chrome": chrome}, f)
        job = f.name
    try:
        r = subprocess.run(["node", os.path.join(HERE, "layout-probe.mjs"), job], capture_output=True, text=True, timeout=600)
    finally:
        os.unlink(job)
    if r.returncode:
        raise RuntimeError("layout-probe failed: " + (r.stderr or r.stdout)[-800:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def hf_findings(report, scenes):
    """The HyperFrames check issues that matter here (KEEP), each named with its scene ("captions" for a caption word)."""
    found = []

    def walk(o):
        if isinstance(o, dict):
            if "code" in o and "severity" in o:
                yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    ids = sorted((s["id"] for s in scenes), key=len, reverse=True)
    for i in walk(report):
        sel = str(i.get("selector", ""))
        if i["code"] not in KEEP or re.match(r"#bg\d", sel):
            continue
        if re.match(r"#(cw|cap)\d", sel):
            scene = "captions"
        else:
            scene = next((sid for sid in ids if re.match(r"#%s(\b|-)" % re.escape(sid), sel)), None)
            if scene is None:
                t = i.get("time")
                scene = next((s["id"] for s in scenes if t is not None and s["in"] <= t <= s["out"]), "page")
        found.append(dict(i, scene=scene))
    return found


def hf_check(pub, smp):
    r = subprocess.run(["npx", "--no-install", "hyperframes", "check", pub, "--json", "--at", ",".join("%.2f" % s["t"] for s in smp)],
                       capture_output=True, text=True, timeout=1200)
    try:
        return json.loads(r.stdout)
    except ValueError:
        raise RuntimeError("hyperframes check gave no report: " + (r.stderr or r.stdout)[-800:])
