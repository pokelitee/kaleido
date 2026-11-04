import tempfile
import unittest
from pathlib import Path

from kaleido.config import ConfigError, Paths, load_engine_config

ENGINE_TOML = """
[upstream]
url = "https://example.invalid/engine.git"

[baseline]
black2_sha1 = "0000000000000000000000000000000000000000"

[dsd]
patch = "dsd/change.patch"

[dsd.ds_rom]
url = "https://example.invalid/ds-rom.git"
commit = "1111111111111111111111111111111111111111"

[dsd.ds_decomp]
url = "https://example.invalid/ds-decomp.git"
commit = "2222222222222222222222222222222222222222"

[tools]
wibo = "abc"
"""


class EngineConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name))
        (self.paths.root / "engine").mkdir()

    def tearDown(self) -> None:
        self._temp.cleanup()

    def write(self, text: str) -> None:
        self.paths.engine_toml.write_text(text, encoding="utf-8")

    def test_reads_every_field(self) -> None:
        self.write(ENGINE_TOML)
        config = load_engine_config(self.paths)
        self.assertEqual(config.mirror_url, "")
        self.assertEqual(config.dsd_patch, self.paths.root / "engine" / "dsd" / "change.patch")
        self.assertEqual(config.ds_decomp.commit, "2" * 40)
        self.assertEqual(config.tool_hashes, {"wibo": "abc"})

    def test_names_the_missing_key(self) -> None:
        self.write(ENGINE_TOML.replace('commit = "1111111111111111111111111111111111111111"', ""))
        with self.assertRaisesRegex(ConfigError, r"\[dsd\.ds_rom\]: missing 'commit'"):
            load_engine_config(self.paths)

    def test_reports_invalid_toml(self) -> None:
        self.write("[upstream\n")
        with self.assertRaisesRegex(ConfigError, "engine.toml"):
            load_engine_config(self.paths)

    def test_the_repository_file_loads(self) -> None:
        config = load_engine_config(Paths(Path(__file__).resolve().parents[2]))
        self.assertEqual(config.black2_sha1, "e51e6dfb8678a3d19dcd2a10691b96a569ca0abb")
        self.assertTrue(config.dsd_patch.exists())


if __name__ == "__main__":
    unittest.main()
