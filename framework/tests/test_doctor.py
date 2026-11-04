import hashlib
import tempfile
import unittest
from pathlib import Path

from kaleido import doctor
from kaleido.config import EngineConfig, Paths, Repo
from kaleido.hashing import tree_digest
from kaleido.roms import RomSpec


def config_with_tools(tool_hashes: dict[str, str]) -> EngineConfig:
    repo = Repo("https://example.invalid/repo.git", "0" * 40)
    return EngineConfig("https://example.invalid/engine.git", "", "0" * 40, Path("dsd.patch"), repo, repo, tool_hashes)


class EnvironmentChecksTest(unittest.TestCase):
    def test_only_linux_builds(self) -> None:
        self.assertEqual(doctor.check_platform("Windows", Path("/home/a/kaleido")).status, doctor.FAIL)
        self.assertEqual(doctor.check_platform("Linux", Path("/home/a/kaleido")).status, doctor.OK)

    def test_warns_about_windows_drives_under_wsl(self) -> None:
        self.assertEqual(doctor.check_platform("Linux", Path("/mnt/c/kaleido")).status, doctor.WARN)

    def test_needs_python_3_11(self) -> None:
        self.assertEqual(doctor.check_python((3, 10)).status, doctor.FAIL)
        self.assertEqual(doctor.check_python((3, 12)).status, doctor.OK)

    def test_missing_commands_fail_with_a_fix(self) -> None:
        checks = doctor.check_commands(lambda name: None if name == "ninja" else f"/usr/bin/{name}")
        ninja = next(check for check in checks if check.name == "command ninja")
        self.assertEqual(ninja.status, doctor.FAIL)
        self.assertIn("apt install", ninja.fix)

    def test_low_disk_warns(self) -> None:
        self.assertEqual(doctor.check_disk(1024**3).status, doctor.WARN)
        self.assertEqual(doctor.check_disk(100 * 1024**3).status, doctor.OK)


class FileChecksTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name))

    def tearDown(self) -> None:
        self._temp.cleanup()

    def spec(self, required: bool, content: bytes = b"synthetic") -> RomSpec:
        return RomSpec("game.bin", "Test Game", hashlib.sha1(content).hexdigest(), required)

    def put(self, relative: str, content: bytes) -> Path:
        path = self.paths.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_a_missing_required_rom_fails_and_an_optional_one_warns(self) -> None:
        self.assertEqual(doctor.check_rom(self.paths, self.spec(required=True)).status, doctor.FAIL)
        self.assertEqual(doctor.check_rom(self.paths, self.spec(required=False)).status, doctor.WARN)

    def test_a_rom_must_have_its_sha1(self) -> None:
        self.put("orig/game.bin", b"synthetic")
        self.assertEqual(doctor.check_rom(self.paths, self.spec(required=True)).status, doctor.OK)
        self.put("orig/game.bin", b"other")
        check = doctor.check_rom(self.paths, self.spec(required=True))
        self.assertEqual(check.status, doctor.FAIL)
        self.assertIn("unknown", check.detail)

    def test_tools_are_checked_against_recorded_hashes(self) -> None:
        self.put("engine/pokebw2/tools/wibo", b"wibo")
        self.put("engine/pokebw2/tools/mwccarm/dsi/mwccarm.exe", b"compiler")
        tools = self.paths.engine / "tools"
        recorded = {
            "wibo": hashlib.sha256(b"wibo").hexdigest(),
            "mwccarm": tree_digest(tools / "mwccarm"),
            "objdiff-cli": "0" * 64,
        }
        checks = {check.name: check for check in doctor.check_tools(self.paths, config_with_tools(recorded))}
        self.assertEqual(checks["tool wibo"].status, doctor.OK)
        self.assertEqual(checks["tool mwccarm"].status, doctor.OK)
        self.assertIn("not downloaded yet", checks["tool objdiff-cli"].detail)
        self.put("engine/pokebw2/tools/wibo", b"changed")
        checks = {check.name: check for check in doctor.check_tools(self.paths, config_with_tools(recorded))}
        self.assertEqual(checks["tool wibo"].status, doctor.FAIL)


if __name__ == "__main__":
    unittest.main()
