"""The Producer skill, the playbook and the four agents: frontmatter that parses, scripts that exist, § references that
resolve."""
import os, re, unittest

try:
    import yaml
except ImportError:   # PyYAML is the kit's dependency too
    yaml = None

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ES = os.path.dirname(SCRIPTS)
PROFILE = os.path.dirname(os.path.dirname(ES))                     # Editing-Workflow/explainer
AGENTS = [os.path.join(PROFILE, "agents", "explainer-%s.md" % n) for n in ("writer", "voice", "director", "animator")]
SKILL, PLAYBOOK = os.path.join(ES, "SKILL.md"), os.path.join(ES, "PLAYBOOK.md")
ROOTS = {"ES": SCRIPTS,
         "RS": os.path.join(PROFILE, "..", "reels", "skill", "reels", "scripts"),
         "SK": os.path.join(PROFILE, "..", "kit", "youtube-edit", "scripts")}
SECTIONS = ["Paths", "Your brief gives you", "Procedure", "Done when", "Never", "Report"]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def frontmatter(p):
    m = re.match(r"^---\n(.*?)\n---\n", read(p), re.S)
    return yaml.safe_load(m.group(1)) if m else None


class Docs(unittest.TestCase):
    @unittest.skipUnless(yaml, "PyYAML not installed")
    def test_frontmatter_parses(self):
        for p in AGENTS:
            fm = frontmatter(p)
            self.assertIsInstance(fm, dict, p)
            for k in ("name", "description", "tools", "model"):
                self.assertTrue(fm.get(k), "%s: no %s" % (p, k))
            self.assertEqual(fm["name"], os.path.basename(p)[:-3])
            self.assertEqual(fm["model"], "inherit")
        fm = frontmatter(SKILL)
        self.assertEqual(fm["name"], "explainer")
        self.assertTrue(fm["description"])

    def test_agent_sections(self):
        for p in AGENTS:
            heads = re.findall(r"^## (.+)$", read(p), re.M)
            for s in SECTIONS:
                self.assertTrue(any(h.startswith(s) for h in heads), "%s: no section %r" % (p, s))

    def test_cited_scripts_exist(self):
        for p in AGENTS + [SKILL, PLAYBOOK]:
            for root, name in re.findall(r"\$(ES|RS|SK)/scripts/([\w.-]+\.(?:py|mjs))", read(p)):
                self.assertTrue(os.path.exists(os.path.join(ROOTS[root], name)), "%s cites $%s/scripts/%s" % (p, root, name))

    def test_playbook_references_resolve(self):
        heads = set(re.findall(r"^#+ (§E\d+)\b", read(PLAYBOOK), re.M))
        self.assertEqual(heads, {"§E%d" % i for i in range(9)})
        for p in AGENTS + [SKILL, PLAYBOOK]:
            for ref in re.findall(r"§E\d+", read(p)):
                self.assertIn(ref, heads, "%s cites %s" % (p, ref))

    def test_the_motion_doctrine_is_read_first(self):
        self.assertTrue(os.path.exists(os.path.join(ES, "MOTION.md")))
        for p in [SKILL, PLAYBOOK, AGENTS[2], AGENTS[3]]:          # the skill, the playbook, the director, the animator
            self.assertIn("MOTION.md", read(p), p)

    def test_reused_reels_agents_named(self):
        text = read(SKILL)
        for a in ("reels-renderer", "reels-qa", "reels-packager", "reels-librarian", "reels-analyst"):
            self.assertIn(a, text)

    def test_readme_links_resolve(self):
        for p in (os.path.join(PROFILE, "README.md"), os.path.join(PROFILE, "RESEARCH.md")):
            self.assertTrue(os.path.exists(p), p)
            for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", read(p)):
                if not re.match(r"^[a-z]+://", link):
                    self.assertTrue(os.path.exists(os.path.join(os.path.dirname(p), link)), "%s links %s" % (p, link))

    def test_mermaid_blocks_fenced(self):
        for p in (os.path.join(PROFILE, "README.md"), os.path.join(PROFILE, "..", "README.md")):
            text = read(p)
            fenced = re.findall(r"```mermaid\n(.*?)```", text, re.S)
            self.assertTrue(fenced, p)
            bare = re.sub(r"```.*?```", "", text, flags=re.S)
            self.assertNotRegex(bare, r"(?m)^\s*(flowchart|graph|sequenceDiagram)\b", p)

    def test_status_has_voice_row(self):
        status = read(os.path.join(PROFILE, "..", "templates", "STATUS.md"))
        self.assertRegex(status, r"\| \*\*Language\*\* \|.*\n\| \*\*Voice\*\* \|")

    def test_reels_qa_briefed_on_explainer_differences(self):
        text = read(SKILL)
        brief = text[text.index("- `reels-qa`"):text.index("- `reels-packager`")]
        for needle in ("first frame", "caption slot", "transcript.json", "asr.json"):
            self.assertIn(needle, brief)
        pack = text[text.index("`reels-packager`:"):text.index("`reels-librarian`:")]
        self.assertIn("captions.srt` from `$W/transcript.json`", pack)

    def test_the_packager_makes_a_small_upload_copy(self):
        # the RAG reel was delivered at 120 MB and had to be compressed by hand: flat motion graphics at CRF 18 are about
        # a tenth of the 20 Mb/s master and look the same (SSIM 0.998 on the RAG demo)
        text = read(SKILL)
        pack = text[text.index("`reels-packager`:"):text.index("`reels-librarian`:")]
        for needle in ("reel-upload.mp4", "-crf 18", "ssim", "reel.mp4"):
            self.assertIn(needle, pack)
