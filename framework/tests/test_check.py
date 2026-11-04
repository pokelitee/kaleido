import json
import tempfile
import unittest
from pathlib import Path

from kaleido import check
from kaleido.config import Paths
from tests.support import git


def nds_header() -> bytes:
    """Zeros with the two fields the check reads: the logo's CRC and a header CRC that matches."""
    header = bytearray(0x200)
    header[0x15C:0x15E] = b"\x56\xcf"
    header[0x15E:0x160] = check._crc16(bytes(header[:0x15E])).to_bytes(2, "little")
    return bytes(header)


def gba_header() -> bytes:
    header = bytearray(0xC0)
    header[0x03], header[0xB2] = 0xEA, 0x96
    header[0xA0:0xAC] = b"SYNTHETIC   "
    header[0xBD] = (-(sum(header[0xA0:0xBD]) + 0x19)) & 0xFF
    return bytes(header)


def gb_header() -> bytes:
    header = bytearray(0x150)
    header[0x134:0x13C] = b"SYNTHETI"
    checksum = 0
    for byte in header[0x134:0x14D]:
        checksum = (checksum - byte - 1) & 0xFF
    header[0x14D] = checksum
    return bytes(header)


class RomKindTest(unittest.TestCase):
    def test_recognizes_each_header(self) -> None:
        self.assertEqual(check.rom_kind(nds_header(), 0x200), "a DS ROM")
        self.assertEqual(check.rom_kind(gba_header(), 0xC0), "a GBA ROM")
        self.assertEqual(check.rom_kind(gb_header(), 0x8000), "a Game Boy ROM")
        self.assertEqual(check.rom_kind(bytes([0xD6, 0xC3, 0xC4, 0, 5]), 5), "a VCDIFF (xdelta) patch")

    def test_a_wrong_checksum_is_not_a_rom(self) -> None:
        for header, size, offset in (
            (nds_header(), 0x200, 0x20),
            (gba_header(), 0xC0, 0xA0),
            (gb_header(), 0x8000, 0x134),
        ):
            broken = bytearray(header)
            broken[offset] ^= 0x01
            self.assertIsNone(check.rom_kind(bytes(broken), size))

    def test_a_game_boy_header_needs_its_size(self) -> None:
        self.assertIsNone(check.rom_kind(gb_header(), 0x8001))

    def test_text_and_zeros_are_not_roms(self) -> None:
        self.assertIsNone(check.rom_kind(b"# Kaleido\n" * 100, 1000))
        self.assertIsNone(check.rom_kind(bytes(0x200), 0x8000))


class GuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        git("init", "-q", cwd=self.root)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def put(self, path: str, data: bytes) -> None:
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)

    def test_tracked_files_leave_out_submodules(self) -> None:
        self.put("docs/a.md", b"a\n")
        git("add", "docs/a.md", cwd=self.root)
        git("update-index", "--add", "--cacheinfo", f"160000,{'1' * 40},engine/pokebw2", cwd=self.root)
        self.assertEqual(check.tracked_files(self.root), ["docs/a.md"])

    def test_flags_roms_saves_and_their_directories(self) -> None:
        files = {
            "orig/notes.txt": b"x",
            "extract/b2/arm9.bin": b"x",
            "content/games/g/extract/recipe.json": b"{}",
            "game.GBA": b"x",
            "black2.sav": b"x",
            "e6b/title.dst": b"x",
            "fixtures/header.bin": nds_header(),
            "art/big.png": bytes(check.MAX_BYTES + 1),
            "docs/fine.md": b"# Fine\n",
        }
        for path, data in files.items():
            self.put(path, data)
        problems = check.guard(self.root, sorted(files))
        flagged = sorted({problem.split(":")[0] for problem in problems})
        expected = [
            "art/big.png",
            "black2.sav",
            "e6b/title.dst",
            "extract/b2/arm9.bin",
            "fixtures/header.bin",
            "game.GBA",
        ]
        self.assertEqual(flagged, sorted([*expected, "orig/notes.txt"]))


class LayerProblemsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name))

    def tearDown(self) -> None:
        self._temp.cleanup()

    def put(self, path: str, data) -> None:
        file = self.paths.root / "content" / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data), encoding="utf-8")

    def test_reports_every_layer_and_game_that_fails_to_load(self) -> None:
        self.put(
            "games/g/game.json",
            {"name": "G", "layers": ["regions/r", "games/g"], "defines": {"KALEIDO_SAVE_MAGIC": "0x12345678"}},
        )
        self.put("games/g/layer.json", {"kind": "game"})
        self.put("regions/r/layer.json", {"kind": "region"})
        self.assertEqual(check.layer_problems(self.paths), [])
        self.put("regions/r/res/data/a.json", {})
        self.put("families/unused/layer.json", {"kind": "family"})
        self.put("families/unused/extract/x.json", {"kind": "unknown"})
        problems = check.layer_problems(self.paths)
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("res/data/a.json has no provenance entry", problems[0])
        self.assertIn("kind 'unknown'", problems[1])


class BrokenLinksTest(unittest.TestCase):
    def test_reports_links_to_files_that_do_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "b c.md").write_text("# B\n", encoding="utf-8")
            (root / "README.md").write_text("[top](README.md)\n", encoding="utf-8")
            (root / "docs" / "a.md").write_text(
                "[b](b%20c.md#b) [readme](../README.md) [root](/README.md) [web](https://example.com/x.md)\n"
                "[here](#a) [gone](missing.md) `[code](nope.md)`\n"
                "```\n[fenced](nope.md)\n```\n",
                encoding="utf-8",
            )
            problems = check.broken_links(root, ["README.md", "docs/a.md", "docs/b c.md"])
            self.assertEqual(problems, ["docs/a.md: link to missing.md, which doesn't exist"])


if __name__ == "__main__":
    unittest.main()
