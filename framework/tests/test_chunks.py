import json
import struct
import tempfile
import unittest
from pathlib import Path

from kaleido import chunks
from kaleido.process import CommandError

# Two map types, laid out as fieldmap.c's MAP_CONFIGS is: buffers of 0x100 and 0x80 bytes
FIELDMAP = (
    "static const FieldMapConfig MAP_CONFIGS[] = {\n"
    "    { { 0x200000, 0x400000, 2, 2, 1, 8, 1, 1, 1, NULL, FALSE, { 0, 0 }, { 0, 2 }, "
    "0x100, 1 }, &FIELDMAP_CTRL_GRID, TRUE, 0x136800 },\n"
    "    { { 0x800000, 0x800000, 2, 3, 0, 8, 2, 3, 1, NULL, FALSE, { 0, 0 }, { 0xffffffff, 0xffffffff }, "
    "0x80, 1 }, &FIELDMAP_CTRL_NOGRID, TRUE, 0x136800 },\n"
    "};\n"
)


def narc(sizes: list[int]) -> bytes:
    """A NARC archive of files of these sizes: its header, file allocation table, an empty name table and the data."""
    offsets, start = [], 0
    for size in sizes:
        offsets.append((start, start + size))
        start += (size + 3) & ~3
    btaf = b"BTAF" + struct.pack("<IHH", 12 + 8 * len(sizes), len(sizes), 0)
    btaf += b"".join(struct.pack("<II", *pair) for pair in offsets)
    btnf = b"BTNF" + struct.pack("<IIHH", 16, 4, 0, 1)
    gmif = b"GMIF" + struct.pack("<I", 8 + start) + bytes(start)
    body = btaf + btnf + gmif
    return b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, 16 + len(body), 16, 3) + body


def put(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


class ChunksTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.tree = Path(self._temp.name)
        put(self.tree / chunks.MAP_CONFIGS, FIELDMAP)
        put(
            self.tree / "generated/map_models.txt", "# Models\nMAP_MODEL_A = 0\nMAP_MODEL_B\nMAP_MODEL_C\nMAP_MODEL_D\n"
        )
        put(self.tree / "generated/map_matrices.txt", "# Matrices\nMAP_MATRIX_ONE = 0\nMAP_MATRIX_TWO\n")
        # Zone y loads matrix one with the smaller buffer
        put(self.tree / "res/field/zones/x.json", {"map_type": 0, "matrix": "MAP_MATRIX_ONE"})
        put(self.tree / "res/field/zones/y.json", {"map_type": 1, "matrix": 0})
        put(self.tree / "res/field/zones/zone.schema.json", {})
        put(self.tree / "res/field/matrices/one.json", {"maps": [["MAP_MODEL_A", None], [1, None]]})
        put(self.tree / "res/field/matrices/two.json", {"maps": [["MAP_MODEL_D"]]})
        self.replacements([])

    def tearDown(self) -> None:
        self._temp.cleanup()

    def replacements(self, entries: list[dict]) -> None:
        put(self.tree / "res/field/matrices/replacements.json", {"replacements": entries})

    def sizes(self, sizes: list[int]) -> None:
        put(self.tree / chunks.ARCHIVE, narc(sizes))

    def test_buffer_sizes_reads_each_map_type(self) -> None:
        self.assertEqual(chunks.buffer_sizes(FIELDMAP), [0x100, 0x80])

    def test_buffer_sizes_needs_the_table(self) -> None:
        with self.assertRaises(CommandError):
            chunks.buffer_sizes("static const int OTHER[] = { 1 };")

    def test_narc_file_sizes(self) -> None:
        self.assertEqual(chunks.narc_file_sizes(narc([5, 0, 0x80])), [5, 0, 0x80])

    def test_list_values_follows_upstreams_rule(self) -> None:
        values = chunks.list_values("# list\nA = 0\nB  # comment\nC = 0x10\nD\n")
        self.assertEqual(values, {"A": 0, "B": 1, "C": 16, "D": 17})

    def test_chunks_that_fit(self) -> None:
        self.sizes([0x80, 0x10, 0x200, 0x200])
        self.assertEqual(chunks.check(self.tree), [])

    def test_a_cell_over_the_smallest_buffer_of_its_zones(self) -> None:
        self.sizes([0x81, 0x10, 0x10, 0x10])
        self.assertEqual(
            chunks.check(self.tree),
            [chunks.OverBudget("MAP_MODEL_A", 0x81, 0x80, 1, "ZONE_Y", "MAP_MATRIX_ONE")],
        )

    def test_a_model_a_replacement_swaps_in(self) -> None:
        self.sizes([0x10, 0x10, 0x90, 0x10])
        self.replacements(
            [
                {
                    "matrix": "MAP_MATRIX_ONE",
                    "kind": "map_model",
                    "condition": "season",
                    "values": {"spring": "MAP_MODEL_A", "winter": "MAP_MODEL_C"},
                }
            ]
        )
        self.assertEqual([problem.model for problem in chunks.check(self.tree)], ["MAP_MODEL_C"])

    def test_the_models_of_a_matrix_swapped_in(self) -> None:
        self.sizes([0x10, 0x10, 0x10, 0x90])
        self.replacements(
            [
                {
                    "matrix": 0,
                    "kind": "matrix",
                    "condition": 3,
                    "values": {"unset": "MAP_MATRIX_ONE", "set": "MAP_MATRIX_TWO"},
                }
            ]
        )
        self.assertEqual([problem.model for problem in chunks.check(self.tree)], ["MAP_MODEL_D"])

    def test_a_model_the_archive_lacks(self) -> None:
        self.sizes([0x10])
        with self.assertRaises(CommandError):
            chunks.check(self.tree)

    def test_the_message_names_the_sizes_and_the_zone(self) -> None:
        problem = chunks.OverBudget("MAP_MODEL_A", 90000, 86020, 3, "ZONE_Y", "MAP_MATRIX_ONE")
        self.assertEqual(
            str(problem),
            "MAP_MODEL_A is 90,000 bytes, over the 86,020 of map type 3, which ZONE_Y loads MAP_MATRIX_ONE with",
        )


if __name__ == "__main__":
    unittest.main()
