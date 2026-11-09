import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from kaleido import extract, layers
from kaleido.config import ConfigError, Paths
from kaleido.games import Game

MATRIX_FILE = "res/field/matrices/overworld.json"


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def map_entry(model: str, cell: list) -> dict:
    return {
        "map": [3, 0],
        "model": model,
        "kit": "families/f/maps/kits/k.json",
        "labels": [],
        "origin": [0, 0],
        "buildings": [],
        "cell": cell,
    }


def recipe(*maps: dict, clear: list | None = None) -> dict:
    found = {"kind": "gba_gen3_map_model", "source": "firered", "matrix": "MAP_MATRIX_OVERWORLD", "maps": list(maps)}
    if clear is not None:
        found["clear"] = clear
    return found


class PlaceInMatrixTest(unittest.TestCase):
    def test_places_each_model_and_empties_the_clear_cells(self) -> None:
        grid = [["A", "B"], ["C", "D"]]
        placed = extract.place_in_matrix(grid, "M", {"MAP_MODEL_X": (0, 1), "MAP_MODEL_Y": (1, 1)}, [[1, 0]])
        self.assertEqual(placed, [["A", None], ["MAP_MODEL_X", "MAP_MODEL_Y"]])
        self.assertEqual(grid, [["A", "B"], ["C", "D"]])

    def test_refuses_a_cell_outside_the_matrix(self) -> None:
        with self.assertRaisesRegex(ConfigError, r"M has no cell \[2, 0\]"):
            extract.place_in_matrix([["A", "B"]], "M", {"MAP_MODEL_X": (2, 0)}, [])

    def test_refuses_a_cell_taken_twice(self) -> None:
        with self.assertRaisesRegex(ConfigError, "both MAP_MODEL_X and MAP_MODEL_Y"):
            extract.place_in_matrix([["A", "B"]], "M", {"MAP_MODEL_X": (0, 0), "MAP_MODEL_Y": (0, 0)}, [])
        with self.assertRaisesRegex(ConfigError, "both cleared and MAP_MODEL_X"):
            extract.place_in_matrix([["A", "B"]], "M", {"MAP_MODEL_X": (0, 0)}, [[0, 0]])


class MapModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name))
        self.game = Game("g", "G", {}, ("games/g",), ("firered",))
        write(self.paths.engine / MATRIX_FILE, {"maps": [["A", "B", "C"], ["D", "E", "F"]]})

    def tearDown(self) -> None:
        self._temp.cleanup()

    def layer(self, layer_id: str, files: dict) -> layers.Layer:
        kind = {"games": "game", "families": "family"}[layer_id.split("/")[0]]
        write(self.content(layer_id) / "layer.json", {"kind": kind})
        write(self.content(layer_id) / "provenance.json", {"entries": [{"paths": ["res/*"], "category": "original"}]})
        for path, data in files.items():
            write(self.content(layer_id) / path, data)
        return layers.load(self.paths, layer_id)

    def content(self, layer_id: str) -> Path:
        return self.paths.root / "content" / layer_id

    def run_recipe(self, found: dict) -> dict:
        def generate(paths, game, source, entry, roms):
            return [(f"res/field/maps/models/{entry['model']}/model.glb", b"glb")]

        with mock.patch.object(extract, "_generate_map", generate):
            outputs = extract.KINDS["gba_gen3_map_model"](self.paths, self.game, [], found, {})
        return dict(outputs)

    def test_two_maps_share_one_matrix_patch_and_one_list(self) -> None:
        outputs = self.run_recipe(
            recipe(map_entry("MAP_MODEL_P", [0, 1]), map_entry("MAP_MODEL_Q", [1, 1]), clear=[[2, 0]])
        )
        self.assertEqual(outputs["generated/map_models.txt"], "MAP_MODEL_P\nMAP_MODEL_Q\n")
        self.assertEqual(
            json.loads(outputs[MATRIX_FILE + ".merge.json"]),
            {"maps": [["A", "B", None], ["MAP_MODEL_P", "MAP_MODEL_Q", "F"]]},
        )
        self.assertIn("res/field/maps/models/MAP_MODEL_P/model.glb", outputs)
        self.assertIn("res/field/maps/models/MAP_MODEL_Q/model.glb", outputs)

    def test_refuses_a_model_listed_twice(self) -> None:
        with self.assertRaisesRegex(ConfigError, "MAP_MODEL_P appear more than once"):
            self.run_recipe(recipe(map_entry("MAP_MODEL_P", [0, 1]), map_entry("MAP_MODEL_P", [1, 1])))

    def test_reading_checks_each_maps_fields(self) -> None:
        entry = map_entry("MAP_MODEL_P", [0, 1])
        del entry["cell"]
        layer = self.layer("games/g", {"extract/m.json": recipe(entry)})
        with self.assertRaisesRegex(ConfigError, "map 0 is missing cell"):
            extract.read_recipe(layer, "extract/m.json")
        layer = self.layer("games/h", {"extract/m.json": recipe()})
        with self.assertRaisesRegex(ConfigError, "maps is empty"):
            extract.read_recipe(layer, "extract/m.json")

    def test_finds_a_lower_layer_that_changes_the_same_matrix(self) -> None:
        found = recipe(map_entry("MAP_MODEL_P", [0, 1]))
        game = self.layer("games/g", {"extract/m.json": found})
        by_recipe = self.layer("families/f", {"extract/n.json": recipe(map_entry("MAP_MODEL_Q", [1, 1]))})
        self.assertEqual(extract.matrix_changed_below([by_recipe, game], game, found), "families/f/extract/n.json")
        by_file = self.layer("families/e", {MATRIX_FILE + ".merge.json": {"maps": []}})
        self.assertEqual(
            extract.matrix_changed_below([by_file, game], game, found), f"families/e/{MATRIX_FILE}.merge.json"
        )
        other = self.layer("families/d", {"res/field/matrices/other.json.merge.json": {"maps": []}})
        self.assertIsNone(extract.matrix_changed_below([other, game], game, found))
        self.assertIsNone(extract.matrix_changed_below([game, by_recipe], game, found))


if __name__ == "__main__":
    unittest.main()
