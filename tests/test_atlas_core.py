import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.atlas_init import install
from scripts.atlas_check import check, _valid_skill_metadata

class AtlasCoreInstallerTests(unittest.TestCase):
    def test_codex_install_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            created, skipped = install(project, "codex")
            self.assertTrue(created)
            self.assertFalse(skipped)
            self.assertEqual(check(project, "codex"), [])
            self.assertTrue((project / ".agents/skills/investigate-bug/SKILL.md").exists())

    def test_preserves_existing_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "AGENTS.md").write_text("Existing rules\n")
            _, skipped = install(project, "codex")
            self.assertIn("AGENTS.md", skipped)
            self.assertEqual((project / "AGENTS.md").read_text(), "Existing rules\n")

    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            created, _ = install(project, "codex", dry_run=True)
            self.assertTrue(created)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_repeat_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            install(project, "codex")
            created, skipped = install(project, "codex")
            self.assertFalse(created)
            self.assertTrue(skipped)

    def test_missing_file_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(check(Path(tmp), "codex"))

    def test_claude_and_cursor(self):
        for client in ("claude", "cursor"):
            with self.subTest(client=client), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                install(project, client)
                self.assertEqual(check(project, client), [])

    def test_dangling_symlink_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            external = project.parent / (project.name + "-external-instructions")
            (project / "AGENTS.md").symlink_to(external)
            _, skipped = install(project, "codex")
            self.assertIn("AGENTS.md", skipped)
            self.assertTrue((project / "AGENTS.md").is_symlink())
            self.assertFalse(external.exists())

    def test_symlinked_parent_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            project = Path(tmp)
            (project / ".agents").symlink_to(outside, target_is_directory=True)
            _, skipped = install(project, "codex")
            self.assertIn(".agents/skills/investigate-bug/SKILL.md", skipped)
            self.assertFalse((Path(outside) / "skills").exists())

    def test_concurrent_creation_is_preserved(self):
        from scripts import atlas_init
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            real_copy = atlas_init._copy_exclusive
            def racing_copy(src, dest):
                if dest.name == "AGENTS.md":
                    dest.write_text("created concurrently\n")
                    return real_copy(src, dest)
                return real_copy(src, dest)
            with patch.object(atlas_init, "_copy_exclusive", side_effect=racing_copy):
                _, skipped = install(project, "codex")
            self.assertIn("AGENTS.md", skipped)
            self.assertEqual((project / "AGENTS.md").read_text(), "created concurrently\n")

    def test_metadata_rejects_prefix_and_description_outside_frontmatter(self):
        bad = "---\nname: investigate-bug-extra\n---\nBody description: example\n"
        self.assertFalse(_valid_skill_metadata(bad, "investigate-bug"))
        self.assertFalse(_valid_skill_metadata("---\nname: investigate-bug\n---\ndescription: outside\n", "investigate-bug"))
        self.assertTrue(_valid_skill_metadata("---\nname: investigate-bug\ndescription: Investigate bugs\n---\n", "investigate-bug"))

    def test_checker_rejects_invalid_installed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            install(project, "codex")
            skill = project / ".agents/skills/investigate-bug/SKILL.md"
            skill.write_text("---\nname: investigate-bug-extra\n---\ndescription: outside\n")
            self.assertTrue(any("INVALID SKILL METADATA" in error for error in check(project, "codex")))

if __name__ == "__main__":
    unittest.main()
