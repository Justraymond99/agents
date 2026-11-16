import tempfile
import unittest
from pathlib import Path
from scripts.atlas_init import install
from scripts.atlas_check import check

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

if __name__ == "__main__":
    unittest.main()
