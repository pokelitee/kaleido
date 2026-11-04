import os
import unittest

from kaleido import engine
from kaleido.config import Paths
from kaleido.roms import BASE, ENGINE_BASEROM
from tests.support import Fixture, git


class SeriesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.paths = Paths(self.fixture.root)
        self.engine = self.paths.engine

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def subjects(self) -> list[str]:
        return git("log", "--format=%s", f"{self.fixture.pin}..HEAD", cwd=self.engine).splitlines()

    def test_pin_is_the_submodule_commit(self) -> None:
        self.assertEqual(engine.pin(self.paths), self.fixture.pin)

    def test_applies_the_series_in_order_on_its_branch(self) -> None:
        self.fixture.make_patch("one", "1\n")
        self.fixture.make_patch("two", "2\n")
        self.assertTrue(engine.apply_series(self.paths))
        self.assertEqual(self.subjects(), ["add two", "add one"])
        self.assertEqual(git("branch", "--show-current", cwd=self.engine), engine.BRANCH)
        self.assertEqual((self.engine / "two.txt").read_text(), "2\n")
        self.assertTrue(engine.state(self.paths).applied)

    def test_a_second_run_changes_nothing(self) -> None:
        self.fixture.make_patch("one", "1\n")
        engine.apply_series(self.paths)
        head = git("rev-parse", "HEAD", cwd=self.engine)
        self.assertFalse(engine.apply_series(self.paths))
        self.assertEqual(git("rev-parse", "HEAD", cwd=self.engine), head)

    def test_the_series_gives_the_same_commits_every_time(self) -> None:
        self.fixture.make_patch("one", "1\n")
        engine.apply_series(self.paths)
        head = git("rev-parse", "HEAD", cwd=self.engine)
        # As on another machine: the pin checked out, nothing applied yet
        git("switch", "-q", "--detach", self.fixture.pin, cwd=self.engine)
        (self.paths.cache / "engine-series.json").unlink()
        self.assertTrue(engine.apply_series(self.paths))
        self.assertEqual(git("rev-parse", "HEAD", cwd=self.engine), head)

    def test_a_changed_series_is_applied_again(self) -> None:
        self.fixture.make_patch("one", "1\n")
        engine.apply_series(self.paths)
        self.fixture.make_patch("two", "2\n")
        self.assertFalse(engine.state(self.paths).applied)
        self.assertTrue(engine.apply_series(self.paths))
        self.assertEqual(self.subjects(), ["add two", "add one"])

    def test_refuses_uncommitted_engine_changes(self) -> None:
        self.fixture.make_patch("one", "1\n")
        engine.apply_series(self.paths)
        (self.engine / "configure.py").write_text("changed\n")
        with self.assertRaisesRegex(engine.EngineError, "uncommitted"):
            engine.apply_series(self.paths)

    def test_refuses_engine_commits_not_in_the_series_unless_forced(self) -> None:
        self.fixture.make_patch("one", "1\n")
        engine.apply_series(self.paths)
        (self.engine / "local.txt").write_text("work\n")
        git("add", "-A", cwd=self.engine)
        git("commit", "-q", "-m", "local work", cwd=self.engine)
        self.fixture.make_patch("two", "2\n")
        with self.assertRaisesRegex(engine.EngineError, "export"):
            engine.apply_series(self.paths)
        self.assertTrue(engine.apply_series(self.paths, force=True))
        self.assertEqual(self.subjects(), ["add two", "add one"])

    def test_a_patch_that_does_not_apply_leaves_the_engine_usable(self) -> None:
        (self.paths.patches / "0001-broken.patch").write_text("From 0 Mon Sep 17 00:00:00 2001\nnot a patch\n")
        with self.assertRaises(engine.EngineError):
            engine.apply_series(self.paths)
        git("status", cwd=self.engine)
        self.assertFalse(engine.state(self.paths).applied)


@unittest.skipIf(os.name == "nt", "symbolic links need Linux, where Kaleido builds")
class BaseRomTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.paths = Paths(self.fixture.root)

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_says_when_the_rom_is_missing(self) -> None:
        self.assertIn("no orig/black2.nds", engine.link_base_rom(self.paths))

    def test_links_the_rom_relatively_once(self) -> None:
        self.paths.orig.mkdir()
        (self.paths.orig / BASE.file).write_bytes(b"synthetic")
        self.assertIn("linked", engine.link_base_rom(self.paths))
        link = self.paths.engine / ENGINE_BASEROM
        self.assertFalse(os.path.isabs(os.readlink(link)))
        self.assertEqual(link.read_bytes(), b"synthetic")
        self.assertEqual(engine.link_base_rom(self.paths), "already linked")

    def test_leaves_a_copied_rom_alone(self) -> None:
        self.paths.orig.mkdir()
        (self.paths.orig / BASE.file).write_bytes(b"synthetic")
        link = self.paths.engine / ENGINE_BASEROM
        link.parent.mkdir(parents=True)
        link.write_bytes(b"copy")
        self.assertIn("a file, not a link", engine.link_base_rom(self.paths))
        self.assertEqual(link.read_bytes(), b"copy")


if __name__ == "__main__":
    unittest.main()
