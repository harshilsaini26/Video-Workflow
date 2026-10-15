"""The shipped fonts are real DM Sans: Chromium draws every printable ASCII character from them, never from a fallback.

The page sets each weight twice, as "DM Sans", monospace and "DM Sans", serif. When the font holds every glyph the two
widths are identical; a missing glyph falls back to a different face in each and the widths differ. Needs a Chromium
(CHROME, /opt/pw-browsers/chromium, or chromium / google-chrome on PATH); skipped without one."""
import os, re, shutil, subprocess, unittest
from .helpers import SCRIPTS, scratch, write

FONTS = os.path.join(SCRIPTS, "..", "assets", "fonts")
CHROME = next((c for c in (os.environ.get("CHROME"), "/opt/pw-browsers/chromium", shutil.which("chromium"),
                           shutil.which("chromium-browser"), shutil.which("google-chrome")) if c and os.path.exists(c)), None)
TEXT = "".join(chr(c) for c in range(33, 127)).replace("<", "").replace("&", "")

PAGE = """<!doctype html><meta charset="utf-8"><style>%s
span { position:absolute; white-space:pre; font-size:200px; }</style><body><script>
const out = [];
Promise.all([...document.fonts].map(f => f.load())).then(() => {
  for (const w of [400, 500, 700]) {
    const m = (fam) => { const s = document.createElement('span'); s.style.fontFamily = fam; s.style.fontWeight = w;
      s.textContent = %s; document.body.appendChild(s); const x = s.getBoundingClientRect().width; s.remove(); return x; };
    out.push(w + ':' + m('"DM Sans", monospace').toFixed(2) + ':' + m('"DM Sans", serif').toFixed(2));
  }
  document.title = 'R ' + out.join(' ');
}).catch(e => { document.title = 'ERR ' + e; });
</script></body>"""


class Fonts(unittest.TestCase):
    @unittest.skipUnless(CHROME, "no Chromium to render with")
    def test_every_ascii_glyph_comes_from_dm_sans(self):
        d = scratch(self)
        faces = "\n".join('@font-face { font-family: "DM Sans"; src: url("file://%s") format("woff2"); font-weight: %d; }'
                          % (os.path.abspath(os.path.join(FONTS, "DMSans-%d.woff2" % w)), w) for w in (400, 500, 700))
        page = write(os.path.join(d, "fonts.html"), PAGE % (faces, repr(TEXT)))
        r = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files",
                            "--virtual-time-budget=10000", "--dump-dom", "file://" + page], capture_output=True, text=True, timeout=120)
        title = re.search(r"<title>(.*?)</title>", r.stdout)
        self.assertTrue(title and title.group(1).startswith("R "), r.stdout[-500:] + r.stderr[-500:])
        for row in title.group(1)[2:].split():
            w, mono, serif = row.split(":")
            self.assertEqual(mono, serif, "DM Sans %s lacks glyphs: they fall back (%s px against %s px)" % (w, mono, serif))
