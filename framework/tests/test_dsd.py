import os
import tempfile
import unittest
from pathlib import Path

from kaleido import dsd
from kaleido.process import CommandError
from tests.support import git

PATCH = """diff --git a/{name}/f b/{name}/f
--- a/{name}/f
+++ b/{name}/f
@@ -1 +1 @@
-old
+new
"""


class ApplyPatchTest(unittest.TestCase):
    """dsd's sources live under .cache/, inside Kaleido's own repository."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.outer = Path(self._temp.name) / "kaleido"
        self.outer.mkdir()
        git("init", "-q", cwd=self.outer)
        self.root = self.outer / ".cache" / "dsd"
        for name in ("one", "two"):
            checkout = self.root / name
            checkout.mkdir(parents=True)
            git("init", "-q", cwd=checkout)
            (checkout / "f").write_text("old\n")
            git("add", "f", cwd=checkout)
            git("commit", "-q", "-m", "f", cwd=checkout)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def write_patch(self, *names: str) -> Path:
        patch = Path(self._temp.name) / "change.patch"
        patch.write_text("".join(PATCH.format(name=name) for name in names))
        return patch

    def test_applies_inside_another_repository(self) -> None:
        dsd.apply_patch(self.root, self.write_patch("one", "two"), ["one", "two"])
        self.assertEqual((self.root / "one" / "f").read_text(), "new\n")
        self.assertEqual((self.root / "two" / "f").read_text(), "new\n")

    def test_a_patch_that_misses_a_checkout_fails(self) -> None:
        with self.assertRaisesRegex(CommandError, "changed nothing in two"):
            dsd.apply_patch(self.root, self.write_patch("one"), ["one", "two"])


@unittest.skipIf(os.name == "nt", "the fake dsd is a shell script")
class HasFlagTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.base = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def fake_dsd(self, help_text: str) -> Path:
        path = self.base / "dsd"
        path.write_text(f"#!/bin/sh\necho '{help_text}'\n")
        path.chmod(0o755)
        return path

    def test_reads_the_rom_build_help(self) -> None:
        self.assertTrue(dsd.has_flag(self.fake_dsd("--config <PATH>  --allow-stale-secure-area")))
        self.assertFalse(dsd.has_flag(self.fake_dsd("--config <PATH>")))
        self.assertFalse(dsd.has_flag(self.base / "missing"))


if __name__ == "__main__":
    unittest.main()
