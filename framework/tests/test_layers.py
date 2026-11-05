import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from kaleido import layers
from kaleido.config import ConfigError, Paths


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


class LayersTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name))
        self.content = self.paths.root / "content"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def layer(self, layer_id: str, kind: str, entries: list | None = None, files: dict | None = None) -> None:
        write(self.content / layer_id / "layer.json", {"kind": kind})
        if entries is not None:
            write(self.content / layer_id / "provenance.json", {"entries": entries})
        for path, data in (files or {}).items():
            write(self.content / layer_id / path, data)

    def test_every_content_file_has_exactly_one_category(self) -> None:
        self.layer(
            "games/g", "game", [{"paths": ["res/text/*"], "category": "original"}], {"res/text/a.txt.merge.json": "{}"}
        )
        self.assertEqual(layers.load(self.paths, "games/g").category_of("res/text/a.txt.merge.json"), "original")
        self.layer("games/h", "game", [], {"res/x.json": "{}"})
        with self.assertRaisesRegex(ConfigError, "no provenance entry"):
            layers.load(self.paths, "games/h")
        self.layer(
            "games/i",
            "game",
            [{"paths": ["res/*"], "category": "original"}, {"paths": ["res/x*"], "category": "original"}],
            {"res/x.json": "{}"},
        )
        with self.assertRaisesRegex(ConfigError, "2 provenance entries"):
            layers.load(self.paths, "games/i")

    def test_extracted_content_is_never_committed(self) -> None:
        self.layer(
            "families/f",
            "family",
            [{"paths": ["res/e.json"], "category": "extracted", "recipe": "extract/e.json"}],
            {"res/e.json": "{}"},
        )
        with self.assertRaisesRegex(ConfigError, "must not be committed"):
            layers.load(self.paths, "families/f")

    def test_an_extracted_path_names_its_recipe(self) -> None:
        self.layer(
            "families/f", "family", [{"paths": ["res/e.json"], "category": "extracted", "recipe": "extract/e.json"}]
        )
        layer = layers.load(self.paths, "families/f")
        self.assertEqual(layer.category_of("res/e.json", "extract/e.json"), "extracted")
        with self.assertRaisesRegex(ConfigError, "with that recipe"):
            layer.category_of("res/e.json", "extract/other.json")

    def test_third_party_entries_record_their_license(self) -> None:
        self.layer("games/g", "game", [{"paths": ["res/a.png"], "category": "third-party", "license": "CC0-1.0"}])
        with self.assertRaisesRegex(ConfigError, "license, author and source"):
            layers.load(self.paths, "games/g")

    def test_a_layer_sits_under_its_kinds_directory(self) -> None:
        self.layer("families/f", "game")
        with self.assertRaisesRegex(ConfigError, "doesn't fit"):
            layers.load(self.paths, "families/f")

    def test_stacks_go_region_family_game(self) -> None:
        self.layer("regions/r", "region")
        self.layer("games/g", "game")
        self.assertEqual(
            [layer.kind for layer in layers.load_stack(self.paths, ["regions/r", "games/g"])], ["region", "game"]
        )
        with self.assertRaisesRegex(ConfigError, "regions come before"):
            layers.load_stack(self.paths, ["games/g", "regions/r"])

    def test_regions_map_locations_to_zones(self) -> None:
        self.layer("regions/r", "region", files={"zones.json": {"locations": {"route_1": "ZONE_ROUTE_19"}}})
        stack = layers.load_stack(self.paths, ["regions/r"])
        self.assertEqual(layers.zone_of(stack, "route_1"), "ZONE_ROUTE_19")
        with self.assertRaisesRegex(ConfigError, "no region layer maps"):
            layers.zone_of(stack, "route_2")

    def test_git_ignores_nothing_under_content(self) -> None:
        # A rule meant for the root's extracted files once hid every layer's extract/ recipes
        root = Path(__file__).resolve().parents[2]
        files = [path.relative_to(root).as_posix() for path in (root / "content").rglob("*") if path.is_file()]
        result = subprocess.run(["git", "check-ignore", "--no-index", *files], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.stdout.split(), [])

    def test_the_repository_layers_load(self) -> None:
        root = Paths(Path(__file__).resolve().parents[2])
        stack = layers.load_stack(root, ["regions/kanto", "families/frlg", "games/firered"])
        self.assertEqual(
            stack[1].recipes(),
            ["extract/map_text.json", "extract/place_names.json", "extract/route_1_encounters.json"],
        )


if __name__ == "__main__":
    unittest.main()
