"""The map chunks' size budget (ADR 0003), checked after a build. The field reads a chunk, a file of a/0/0/8, whole into
a buffer the size of its map type's chunkBufferSize (MAP_CONFIGS in src/ov036/fieldmap.c), and nothing checks the
length (src/ov012/field_g3d_map.c), so a larger chunk overwrites the heap past the buffer.

A zone loads its matrix with its own map type, and walking on through the matrix keeps it, so every chunk a matrix can
show must fit the smallest buffer of the zones that load it. A matrix shows its cells' models, the models that
res/field/matrices/replacements.json swaps in, and the models of the matrices it swaps in whole."""

import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from kaleido.process import CommandError

ARCHIVE = "build/b2_us/files/a/0/0/8"
MAP_CONFIGS = "src/ov036/fieldmap.c"
# An entry of MAP_CONFIGS ends its mapper config with chunkBufferSize and one more number, then names its control
BUFFER_SIZE = re.compile(r"(0x[0-9a-fA-F]+|\d+), \d+ \}, &FIELDMAP_CTRL_\w+")


@dataclass(frozen=True)
class OverBudget:
    model: str
    size: int
    budget: int
    map_type: int
    zone: str
    matrix: str

    def __str__(self) -> str:
        return (
            f"{self.model} is {self.size:,} bytes, over the {self.budget:,} of map type {self.map_type}, "
            f"which {self.zone} loads {self.matrix} with"
        )


def buffer_sizes(source: str) -> list[int]:
    """Each map type's chunkBufferSize, from fieldmap.c's MAP_CONFIGS, in map type order."""
    start = source.find("MAP_CONFIGS[] = {")
    table = source[start : source.find("};", start)] if start >= 0 else ""
    sizes = [int(size, 0) for size in BUFFER_SIZE.findall(table)]
    if not sizes or len(sizes) != table.count("&FIELDMAP_CTRL_"):
        raise CommandError(f"{MAP_CONFIGS}: can't read each map type's chunkBufferSize from MAP_CONFIGS")
    return sizes


def narc_file_sizes(data: bytes) -> list[int]:
    """The length of each file of a NARC archive, from its file allocation table (BTAF)."""
    if data[:4] != b"NARC":
        raise CommandError("not a NARC archive")
    table = struct.unpack_from("<H", data, 12)[0]
    if data[table : table + 4] != b"BTAF":
        raise CommandError("a NARC archive without its file allocation table")
    count = struct.unpack_from("<H", data, table + 8)[0]
    return [end - start for start, end in struct.iter_unpack("<II", data[table + 12 : table + 12 + 8 * count])]


def list_values(text: str) -> dict[str, int]:
    """A generated/ list's constants and their numbers, by upstream's rule (tools/data/gen_constants.py): one more
    than the last, or the number after "="."""
    values, value = {}, -1
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, _, given = line.partition("=")
        value = int(given.strip(), 0) if given else value + 1
        values[name.strip()] = value
    return values


def _names(values: dict[str, int]) -> dict[int, str]:
    names = {}
    for name, value in values.items():
        names.setdefault(value, name)
    return names


def check(tree: Path) -> list[OverBudget]:
    """Every chunk of the tree's built a/0/0/8 that a zone's matrix can show, against the zone's buffer."""
    sizes = buffer_sizes((tree / MAP_CONFIGS).read_text(encoding="utf-8"))
    lengths = narc_file_sizes((tree / ARCHIVE).read_bytes())
    models = list_values((tree / "generated" / "map_models.txt").read_text(encoding="utf-8"))
    model_names = _names(models)
    matrix_names = _names(list_values((tree / "generated" / "map_matrices.txt").read_text(encoding="utf-8")))
    matrices_dir = tree / "res" / "field" / "matrices"

    def matrix_name(matrix: str | int) -> str:
        return matrix_names[matrix] if isinstance(matrix, int) else matrix

    def model_id(model: str | int) -> int:
        return model if isinstance(model, int) else models[model]

    swapped_models: dict[str, set[int]] = {}
    swapped_matrices: dict[str, set[str]] = {}
    for entry in json.loads((matrices_dir / "replacements.json").read_text(encoding="utf-8"))["replacements"]:
        values = entry["values"].values()
        if entry["kind"] == "map_model":
            swapped_models.setdefault(matrix_name(entry["matrix"]), set()).update(model_id(v) for v in values)
        else:
            swapped_matrices.setdefault(matrix_name(entry["matrix"]), set()).update(matrix_name(v) for v in values)

    # The smallest buffer each matrix is loaded with: (size, map type, zone)
    loads: dict[str, tuple[int, int, str]] = {}
    for path in sorted((tree / "res" / "field" / "zones").glob("*.json")):
        if path.name.endswith(".schema.json"):
            continue
        zone = json.loads(path.read_text(encoding="utf-8"))
        if zone.get("matrix") is None or zone.get("map_type") is None:
            continue
        matrix, map_type = matrix_name(zone["matrix"]), zone["map_type"]
        if matrix not in loads or sizes[map_type] < loads[matrix][0]:
            loads[matrix] = (sizes[map_type], map_type, "ZONE_" + path.stem.upper())

    problems = []
    for matrix, (budget, map_type, zone) in sorted(loads.items()):
        shown = set()
        for shown_matrix in {matrix, *swapped_matrices.get(matrix, ())}:
            path = matrices_dir / (shown_matrix.removeprefix("MAP_MATRIX_").lower() + ".json")
            rows = json.loads(path.read_text(encoding="utf-8"))["maps"]
            shown |= {model_id(cell) for row in rows for cell in row if cell is not None}
            shown |= swapped_models.get(shown_matrix, set())
        for model in sorted(shown):
            if model >= len(lengths):
                raise CommandError(f"{matrix} shows map model {model}, which {ARCHIVE} doesn't have")
            if lengths[model] > budget:
                name = model_names.get(model, f"map model {model}")
                problems.append(OverBudget(name, lengths[model], budget, map_type, zone, matrix))
    return problems
