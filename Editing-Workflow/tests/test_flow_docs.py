"""The flow, as the docs tell it: every profile ends at the editor hand-off (gate H1) and the creator edits; the render
is opt-in; Checkpoint A offers hook angles; the brief asks for a voice profile; the post caption is a draft run through
post-check; the Cutter runs the wording check; the three repositories the ideas came from are credited; every script
the reels and long-form docs cite exists."""
import glob, os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # Editing-Workflow
SKILLS = {"explainer": "explainer/skill/explainer/SKILL.md", "reels": "reels/skill/reels/SKILL.md",
          "longform": "longform/skill/youtube-longform/SKILL.md"}
ROOTS = {"SK": "kit/youtube-edit/scripts", "RS": "reels/skill/reels/scripts", "ES": "explainer/skill/explainer/scripts"}
REPOS = ("sergebulaev/instagram-skills", "Jakeschincariol/instagram-agent-skill", "Anil-matcha/AI-Youtube-Shorts-Generator")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def stage_rows(text):
    return [l for l in text.splitlines() if re.match(r"^\| *[0-9A-Z][0-9a-z]* *\|", l)]


class Flow(unittest.TestCase):
    def test_every_profile_ends_at_the_handoff(self):
        for prof, rel in SKILLS.items():
            rows = stage_rows(read(rel))
            hand = [r for r in rows if "Hand-off" in r]
            self.assertTrue(hand, "%s: no Hand-off stage" % prof)
            self.assertIn("H1", hand[0], prof)
            for r in rows:
                if re.search(r"\| *Render", r):
                    self.assertIn("opt-in", r, "%s: %s" % (prof, r))
            text = read(rel)
            self.assertIn("handoff", text.lower(), prof)
            self.assertIn("filmcraft", text, prof)

    def test_checkpoint_a_offers_hook_angles_and_the_brief_asks_for_a_voice_profile(self):
        for prof, rel in SKILLS.items():
            text = read(rel)
            self.assertRegex(text, r"hook angles", prof)
            self.assertRegex(text, r"voice profile", prof)
        writer = read("explainer/agents/explainer-writer.md")
        for phrase in ("hook angles", "voice profile", "wording"):
            self.assertIn(phrase, writer)

    def test_the_post_caption_is_a_checked_draft(self):
        for rel in ("reels/agents/reels-packager.md", "explainer/skill/explainer/SKILL.md"):
            self.assertIn("post-check.py", read(rel), rel)

    def test_the_cutter_runs_the_wording_check(self):
        for rel in ("reels/agents/reels-cutter.md", "longform/agents/longform-cutter.md"):
            self.assertIn("wording.py", read(rel), rel)

    def test_the_render_agents_are_opt_in(self):
        for rel in ("reels/agents/reels-renderer.md", "longform/agents/longform-renderer.md", "longform/agents/longform-assembler.md"):
            self.assertIn("opt-in", read(rel), rel)

    def test_the_playbooks_carry_the_new_rules(self):
        ep = read("explainer/skill/explainer/PLAYBOOK.md")
        self.assertIn("Plain spoken words", ep)
        self.assertIn("over-correct", ep)
        rp = read("reels/skill/reels/PLAYBOOK.md")
        self.assertRegex(rp, r"(?s)§R13.*one call to action.*reason")
        self.assertRegex(rp, r"(?s)§R13.*2 to 3 niche")

    def test_the_repositories_are_credited(self):
        for rel in ("explainer/RESEARCH.md", "reels/RESEARCH.md", "longform/RESEARCH.md"):
            text = read(rel)
            for repo in REPOS:
                self.assertIn(repo, text, "%s: no credit for %s" % (rel, repo))

    def test_cited_scripts_exist(self):
        docs = glob.glob(os.path.join(ROOT, "reels", "agents", "*.md")) + glob.glob(os.path.join(ROOT, "longform", "agents", "*.md")) + \
            [os.path.join(ROOT, r) for r in SKILLS.values()]
        for p in docs:
            with open(p, encoding="utf-8") as f:
                text = f.read()
            for root, name in re.findall(r"\$(SK|RS|ES)/scripts/([\w.-]+\.(?:py|mjs))", text):
                self.assertTrue(os.path.exists(os.path.join(ROOT, ROOTS[root], name)), "%s cites $%s/scripts/%s" % (p, root, name))

    def test_readmes_tell_the_new_end(self):
        for rel in ("README.md", "explainer/README.md", "reels/README.md", "longform/README.md", os.path.join("..", "README.md")):
            text = read(rel)
            self.assertIn("filmcraft", text, rel)
            self.assertIn("wf.py", text, rel)


if __name__ == "__main__":
    unittest.main()
