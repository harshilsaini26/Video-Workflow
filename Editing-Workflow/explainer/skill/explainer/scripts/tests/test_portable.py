"""Windows-ready (SOP S3): the RAG reel ran on Windows, where Python reads and writes text in the system code page
unless told otherwise (49 test failures until UTF-8 mode), `npx` is npx.cmd (a bare "npx" cannot be started without a
shell), and "file://" + a C:\\ path is not a URL. Every script here names UTF-8 for its text, finds npx on PATH, and
builds file URLs with pathToFileURL."""
import ast, os, re, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sources(ext):
    for d, dirs, files in os.walk(HERE):
        dirs[:] = [x for x in dirs if x not in ("__pycache__", "node_modules", "vendor")]
        for f in files:
            if f.endswith(ext):
                yield os.path.join(d, f)


class Portable(unittest.TestCase):
    def test_text_files_and_pipes_are_utf8(self):
        bad = []
        for p in sources(".py"):
            with open(p, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for n in ast.walk(tree):
                if not isinstance(n, ast.Call):
                    continue
                kws = {k.arg for k in n.keywords}
                if isinstance(n.func, ast.Name) and n.func.id == "open" and "encoding" not in kws:
                    mode = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else \
                        next((k.value.value for k in n.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)), "r")
                    if "b" not in str(mode):
                        bad.append("%s:%d open() without encoding" % (os.path.relpath(p, HERE), n.lineno))
                if any(k.arg in ("text", "universal_newlines") and isinstance(k.value, ast.Constant) and k.value.value is True
                       for k in n.keywords) and "encoding" not in kws:
                    bad.append("%s:%d text=True without encoding" % (os.path.relpath(p, HERE), n.lineno))
        self.assertEqual(bad, [])

    def test_npx_is_found_on_path(self):
        bad = []
        for p in sources(".py"):
            with open(p, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if re.search(r"""\[\s*["']npx["']""", line):
                        bad.append("%s:%d" % (os.path.relpath(p, HERE), i))
        self.assertEqual(bad, [], "use shutil.which('npx') or 'npx': on Windows it is npx.cmd")

    def test_file_urls_are_built_from_paths(self):
        bad = []
        for p in sources(".mjs"):
            with open(p, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if re.search(r"""["']file://["']\s*\+""", line):
                        bad.append("%s:%d" % (os.path.relpath(p, HERE), i))
        self.assertEqual(bad, [], "use url.pathToFileURL(path).href: a C:\\ path is not a file URL")


if __name__ == "__main__":
    unittest.main()
