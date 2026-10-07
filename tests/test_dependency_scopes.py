"""Reject stale recursive evidence and unsafe requirement include paths."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.dependency_scopes import manifest_hashes


class ManifestInputsTest(unittest.TestCase):
    def test_pip_include_aliases_cannot_hide_changed_child(self):
        for option in ("-r", "--requirement=", "-c", "--constraint="):
            with self.subTest(option=option), TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "requirements-ci.txt").write_text(option + "child.txt\n")
                child = root / "child.txt"
                child.write_text("pytest==9.1.1\n")
                before = manifest_hashes("test", root)
                child.write_text("pytest==8.3.4\n")
                after = manifest_hashes("test", root)
                self.assertIn("child.txt", after)
                self.assertNotEqual(before, after)

    def test_included_manifest_edit_changes_evidence_without_changing_entry(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements-ci.txt").write_text("-r requirements-test.txt\n")
            (root / "requirements-test.txt").write_text("-r requirements.txt\npytest==8.3.4\n")
            (root / "requirements.txt").write_text("fastapi==0.115.6\n")
            before = manifest_hashes("test", root)
            (root / "requirements-test.txt").write_text("-r requirements.txt\npytest==9.1.1\n")
            after = manifest_hashes("test", root)
            self.assertEqual(before["requirements-ci.txt"], after["requirements-ci.txt"])
            self.assertNotEqual(before, after, "An unchanged entry file must not hide a stale child")
            self.assertIn("requirements.txt", after)

    def test_cycle_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements.txt").write_text("-r requirements.txt\n")
            with self.assertRaisesRegex(ValueError, "Cyclic"):
                manifest_hashes("runtime", root)

    def test_include_outside_owned_root_is_rejected_before_read(self):
        with TemporaryDirectory() as directory:
            owned = Path(directory)
            root = owned / "checkout"
            root.mkdir()
            (root / "requirements.txt").write_text("-r ../outside.txt\n")
            # The outside path deliberately does not exist: containment should
            # fail before file contents could be accessed.
            with self.assertRaises(ValueError):
                manifest_hashes("runtime", root)


if __name__ == "__main__":
    unittest.main()
