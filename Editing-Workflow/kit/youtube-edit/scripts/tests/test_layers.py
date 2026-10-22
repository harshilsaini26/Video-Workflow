"""layer-pages / render-layers: any composed page (explainer, reels, long-form: the kit markup) as transparent clips,
one per layer, for the editor hand-off. Each layer page shows its layer alone on a transparent ground, timed from 0."""
import json, os, re, shutil, subprocess, unittest
from .helpers import load, read, run, scratch, write

PAGE = """<!doctype html>
<html><head><style>body { background:#EFEAE3; }</style>
</head>
<body>
  <div id="stage" data-composition-id="demo" data-start="0" data-duration="6.000" data-fps="60" data-width="1080" data-height="1920">
    <div class="bg" id="bg0" style="background:#EFEAE3;opacity:1"></div>
    <svg class="thread" data-thread="1" width="1080" height="1920"><path id="th-p" d="M0 0"/></svg>
    <video id="bg-video" src="input-video.mp4" data-start="0" data-duration="6.000" data-track-index="1"></video>
    <div class="card-host clip" id="host-l0" data-start="0.000" data-duration="2.500" data-track-index="5"><div class="card">A</div></div>
    <div class="card-host clip" id="host-l1" data-start="2.500" data-duration="3.500" data-track-index="6"><div class="card">B</div></div>
    <div class="clip cap-layer" id="captions" data-start="0" data-duration="6.000" data-track-index="2">
      <div class="brand" id="brand"><span>@me</span><span>PART 3</span></div>
      <div class="cap" id="cap0">hello</div>
    </div>
    <audio id="voice" src="voice.wav" data-start="0" data-duration="5.500" data-track-index="1" data-volume="1"></audio>
    <audio id="bed" src="bed.wav" data-start="0" data-duration="6.000" data-track-index="40" data-volume="1"></audio>
    <script src="vendor/gsap.min.js"></script>
    <script>
      (function () {
        const tl = window.gsap.timeline({ paused: true });
        tl.fromTo('#host-l0 .card', { opacity: 0 }, { opacity: 1, duration: 0.5 }, 0);
        tl.fromTo('#host-l1 .card', { opacity: 0 }, { opacity: 1, duration: 0.5 }, 2.5);
        tl.to({}, { duration: 6.000 }, 0);
        window.__timelines = window.__timelines || {};
        window.__timelines["demo"] = tl;
      })();
    </script>
  </div>
</body>
</html>
"""


def make(test):
    d = scratch(test)
    write(os.path.join(d, "public", "index.html"), PAGE)
    r = run("layer-pages.py", "--index", os.path.join(d, "public", "index.html"))
    test.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    return d, load(os.path.join(d, "public", "layers.json"))


class Pages(unittest.TestCase):
    def test_one_page_per_host_and_per_group(self):
        d, layers = make(self)
        by = {l["name"]: l for l in layers}
        self.assertEqual(sorted(by), ["brand", "captions", "ground", "l0", "l1", "thread"])
        self.assertEqual((by["l0"]["kind"], by["l0"]["t_in"], by["l0"]["t_out"]), ("host", 0.0, 2.5))
        self.assertEqual((by["l1"]["t_in"], by["l1"]["t_out"]), (2.5, 6.0))
        self.assertEqual((by["ground"]["t_in"], by["ground"]["t_out"]), (0.0, 6.0))
        # the ground is opaque and runs the whole reel: H.264, not ProRes 4444 (a 33 s ground was 1.7 GB as 4444)
        self.assertEqual(by["ground"]["ext"], "mp4")
        self.assertTrue(all(l["ext"] == "mov" for l in layers if l["name"] != "ground"))
        for l in layers:
            self.assertTrue(os.path.isfile(os.path.join(d, "public", l["page"])), l)
            self.assertEqual(l["page"], "layer-%s.html" % l["name"])

    def test_burst_transitions_are_their_own_layer(self):
        d = scratch(self)
        write(os.path.join(d, "public", "index.html"), PAGE.replace('<div class="clip cap-layer"', '<div class="tx-layer" id="tx"><i class="spark"></i></div>\n    <div class="clip cap-layer"'))
        self.assertEqual(run("layer-pages.py", "--index", os.path.join(d, "public", "index.html")).returncode, 0)
        by = {l["name"]: l for l in load(os.path.join(d, "public", "layers.json"))}
        self.assertEqual((by["tx"]["kind"], by["tx"]["ext"]), ("tx", "mov"))

    def test_a_layer_page_shows_only_its_layer(self):
        d, _ = make(self)
        p = read(os.path.join(d, "public", "layer-l1.html"))
        self.assertIn("#stage *:not(:is(#host-l1, #host-l1 *)) { visibility:hidden !important; }", p)
        self.assertIn("#host-l1 { visibility:visible; }", p)
        self.assertRegex(p, r"html, body, #stage \{ background:transparent !important; \}")
        self.assertNotIn("<video", p)
        self.assertNotIn("<audio", p)
        cap = read(os.path.join(d, "public", "layer-captions.html"))
        self.assertIn("#brand, #brand * { visibility:hidden !important; }", cap)     # the brand is its own layer

    def test_times_are_shifted_to_the_layer(self):
        d, _ = make(self)
        p = read(os.path.join(d, "public", "layer-l1.html"))
        self.assertRegex(p, r'<div id="stage" data-composition-id="demo" data-start="0" data-duration="3.500"')
        self.assertIn('id="host-l1" data-start="0.000" data-duration="3.500"', p)
        self.assertIn('id="host-l0" data-start="-2.500"', p)
        self.assertIn('M.add(tl.tweenFromTo(2.500, 6.000, { ease: "none" }), 0); window.__timelines["demo"] = M;', p)

    def test_edge_layers_keep_first_and_last_frame(self):
        _, layers = make(self)
        by = {l["name"]: l for l in layers}
        self.assertEqual(by["l0"]["t_in"], 0.0)
        self.assertEqual(by["l1"]["t_out"], 6.0)

    def test_a_page_without_a_timeline_is_named(self):
        d = scratch(self)
        write(os.path.join(d, "index.html"), PAGE.replace('window.__timelines["demo"] = tl;', ""))
        r = run("layer-pages.py", "--index", os.path.join(d, "index.html"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("timeline", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)


class Render(unittest.TestCase):
    def test_render_writes_alpha_movs(self):
        hf, vendor = os.environ.get("HYPERFRAMES_CMD"), os.environ.get("EXPLAINER_VENDOR", "")
        gsap = os.path.join(vendor, "gsap.min.js")
        if not hf or not os.path.isfile(gsap) or not shutil.which("ffprobe"):
            self.skipTest("needs HYPERFRAMES_CMD, a local gsap.min.js (EXPLAINER_VENDOR) and ffprobe")
        d = scratch(self)
        short = PAGE.replace('data-duration="6.000"', 'data-duration="0.500"').replace("duration: 6.000", "duration: 0.500")
        short = re.sub(r'<div class="card-host clip" id="host-l1".*?</div></div>\n', "", short)
        short = short.replace('id="host-l0" data-start="0.000" data-duration="2.500"', 'id="host-l0" data-start="0.000" data-duration="0.500"')
        write(os.path.join(d, "public", "index.html"), short)
        os.makedirs(os.path.join(d, "public", "vendor"))
        shutil.copy(gsap, os.path.join(d, "public", "vendor", "gsap.min.js"))
        self.assertEqual(run("layer-pages.py", "--index", os.path.join(d, "public", "index.html")).returncode, 0)
        r = run("render-layers.py", "--public", os.path.join(d, "public"), "--out", os.path.join(d, "gfx"), "--only", "l0", "--workers", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=pix_fmt,duration", "-of", "json",
                              os.path.join(d, "gfx", "l0.mov")], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        s = json.loads(out)["streams"][0]
        self.assertTrue(s["pix_fmt"].startswith("yuva"), s)
        self.assertAlmostEqual(float(s["duration"]), 0.5, delta=1 / 60.0 + 1e-3)


if __name__ == "__main__":
    unittest.main()
