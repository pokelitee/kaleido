"""Generated maps (ADR 0006, docs/plan/09-generated-maps.md): a Gen 3 map's layout as a Gen 5 map chunk.

A chunk is a template's model with its geometry drawn again: the converter keeps the template's draw calls and
materials, which the packer can't add to (docs/research/generated-maps-spike.md §1), and puts each kind of tile in the
material a kit names for it. The kit is Kaleido's data about one template: its materials, heights, tree, props and
tile types. The labels give each metatile of the source's tilesets its kind; the layout gives each tile its metatile
and collision. Positions stay on the source's grid, offset by the map's origin in the chunk.

The chunk's tiles outside the map are blocked grass, and water at the map's edge runs on to the chunk's."""

import copy
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

from extractors.gba_gen3_layout import Layout
from kaleido.config import ConfigError

TILE = 16
CHUNK_TILES = 32
HALF = CHUNK_TILES * TILE // 2
# Each kind of tile: the surface under it, and what stands on it
KINDS = {
    "grass": ("grass", None),
    "path": ("path", None),
    "water": ("water", None),
    "flowers": ("grass", "flowers"),
    "tree": ("grass", "tree"),
    "fence": ("grass", "fence"),
    "sign": ("grass", "sign"),
    "mailbox": ("grass", "mailbox"),
    "building": ("path", "building"),
}
SURFACES = ("grass", "path", "water", "flowers")
SIDES = {(0, -1): "north", (0, 1): "south", (-1, 0): "west", (1, 0): "east"}
# The packer re-encodes a vertex as a color, a normal, a UV and a position, 36 bytes, and each draw call as a begin
# and an end command (map_model_data.py's topology_display_list)
VERTEX_BYTES, DRAW_CALL_BYTES = 36, 12
FLOAT, UNSIGNED_INT = 5126, 5125
GLB_MAGIC, GLB_JSON, GLB_BIN = 0x46546C67, 0x4E4F534A, 0x004E4942
PROP_NODE = "bw2_prop_{:04d}_id_{:05d}"


@dataclass(frozen=True)
class Kit:
    template: str
    ground_y: float
    ground_height: int
    water_y: float
    water_height: int
    # Surface: (material, texture repeats a tile, height above its level)
    surfaces: dict[str, tuple[str, float, float]]
    bank: tuple[str, float]
    fence: dict
    tree: dict
    tile_types: dict[str, int]
    props: dict[str, int]
    # A building prop's door, from its origin, in tiles
    doors: dict[int, tuple[int, int]]
    # A building prop's model's x and z bounds from its origin, in units: x0, z0, x1, z1
    footprints: dict[int, tuple[float, float, float, float]]

    @staticmethod
    def load(path: Path) -> "Kit":
        where = str(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            surfaces = {
                name: (value["material"], float(value["repeat"]), float(value.get("lift", 0)))
                for name, value in data["surfaces"].items()
            }
            kit = Kit(
                template=data["template"],
                ground_y=float(data["ground"]["y"]),
                ground_height=int(data["ground"]["height"]),
                water_y=float(data["water"]["y"]),
                water_height=int(data["water"]["height"]),
                surfaces=surfaces,
                bank=(data["bank"]["material"], float(data["bank"]["repeat"])),
                fence=data["fence"],
                tree=data["tree"],
                tile_types={name: int(value, 0) for name, value in data["tile_types"].items()},
                props={name: int(value) for name, value in data["props"].items()},
                doors={int(prop): (int(x), int(z)) for prop, (x, z) in data["doors"].items()},
                footprints={int(prop): tuple(float(v) for v in box) for prop, box in data["footprints"].items()},
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ConfigError(f"{where}: {error!r}") from error
        missing = [name for name in SURFACES if name not in kit.surfaces]
        missing += [name for name in ("walk", "block", "water", "shore") if name not in kit.tile_types]
        if missing:
            raise ConfigError(f"{where}: missing {', '.join(missing)}")
        return kit


@dataclass(frozen=True)
class Building:
    # The door's tile on the source map, and the prop to stand there
    door: tuple[int, int]
    prop: int


@dataclass(frozen=True)
class Chunk:
    glb: bytes
    terrain: str
    splits: str
    # Triangles a material, props, and the display lists' bytes the packer will write
    triangles: dict[str, int]
    props: int
    display_list_bytes: int


def load_labels(paths: list[Path]) -> dict[int, str]:
    """Each metatile's kind, from label files whose "kinds" map a metatile ("0x01c") to a kind."""
    labels: dict[int, str] = {}
    for path in paths:
        try:
            kinds = json.loads(path.read_text(encoding="utf-8"))["kinds"]
        except (OSError, json.JSONDecodeError, KeyError) as error:
            raise ConfigError(f"{path}: {error!r}") from error
        for key, kind in kinds.items():
            if kind not in KINDS:
                raise ConfigError(f"{path}: {key} is {kind!r}, not one of {', '.join(KINDS)}")
            metatile = int(key, 16)
            if metatile in labels:
                raise ConfigError(f"{path}: {key} has a label already")
            labels[metatile] = kind
    return labels


# --- GLB ------------------------------------------------------------------------------------------------------------


def read_glb(data: bytes) -> tuple[dict, bytes]:
    magic, _, _ = struct.unpack_from("<III", data, 0)
    length, kind = struct.unpack_from("<II", data, 12)
    if magic != GLB_MAGIC or kind != GLB_JSON:
        raise ConfigError("not a GLB")
    doc = json.loads(data[20 : 20 + length])
    binary = b""
    rest = 20 + length
    if rest < len(data):
        bin_length, bin_kind = struct.unpack_from("<II", data, rest)
        if bin_kind == GLB_BIN:
            binary = data[rest + 8 : rest + 8 + bin_length]
    return doc, binary


def write_glb(doc: dict, binary: bytes) -> bytes:
    text = json.dumps(doc, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    binary += bytes(-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    return (
        struct.pack("<III", GLB_MAGIC, 2, total)
        + struct.pack("<II", len(text), GLB_JSON)
        + text
        + struct.pack("<II", len(binary), GLB_BIN)
        + binary
    )


def accessor_values(doc: dict, binary: bytes, index: int) -> list[tuple]:
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    code = {5126: "f", 5121: "B", 5123: "H", 5125: "I"}[accessor["componentType"]]
    size = struct.calcsize("<" + code * width)
    step = view.get("byteStride") or size
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return [struct.unpack_from("<" + code * width, binary, start + i * step) for i in range(accessor["count"])]


# --- Geometry -------------------------------------------------------------------------------------------------------


@dataclass
class Geometry:
    """Triangles by material: three (position, uv, normal) vertices each."""

    triangles: dict[str, list[tuple]] = field(default_factory=dict)

    def triangle(self, material: str, vertices: tuple) -> None:
        self.triangles.setdefault(material, []).append(vertices)

    def quad(self, material: str, corners: list, uvs: list, normal: tuple) -> None:
        """A quad of four corners in front-facing (counterclockwise) order."""
        a, b, c, d = ((corners[i], uvs[i], normal) for i in range(4))
        self.triangle(material, (a, b, c))
        self.triangle(material, (a, c, d))


def tile_x(x: float) -> float:
    return x * TILE - HALF


def surface_quad(geometry: Geometry, surface: tuple[str, float, float], level: float, rect: tuple) -> None:
    material, repeat, lift = surface
    x0, z0, w, h = rect
    y = level + lift
    xs, zs = (tile_x(x0), tile_x(x0 + w)), (tile_x(z0), tile_x(z0 + h))
    # The texture runs on the chunk's coordinates, so that neighboring quads meet; less its whole repeats, to stay small
    u0, v0 = x0 * repeat, z0 * repeat
    u0, v0 = u0 - int(u0), v0 - int(v0)
    us, vs = (u0, u0 + w * repeat), (v0, v0 + h * repeat)
    corners = [(xs[0], y, zs[0]), (xs[0], y, zs[1]), (xs[1], y, zs[1]), (xs[1], y, zs[0])]
    uvs = [(us[0], vs[0]), (us[0], vs[1]), (us[1], vs[1]), (us[1], vs[0])]
    geometry.quad(material, corners, uvs, (0.0, 1.0, 0.0))


def rectangles(cells: set[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    """The cells as rectangles (x, z, width, height), greedily: each grows right, then down."""
    left = set(cells)
    found = []
    for x, z in sorted(cells, key=lambda cell: (cell[1], cell[0])):
        if (x, z) not in left:
            continue
        width = 1
        while (x + width, z) in left:
            width += 1
        height = 1
        while all((x + i, z + height) in left for i in range(width)):
            height += 1
        for i in range(width):
            for j in range(height):
                left.discard((x + i, z + j))
        found.append((x, z, width, height))
    return found


def wall(
    geometry: Geometry,
    material: str,
    repeat: float,
    side: str,
    line: float,
    start: float,
    end: float,
    bottom: float,
    top: float,
) -> None:
    """A vertical quad on a tile edge, facing the side named: at z = line (north, south) or x = line (west, east)."""
    length, height = (end - start) / TILE * repeat, (top - bottom) / TILE * repeat
    uvs = [(0.0, height), (length, height), (length, 0.0), (0.0, 0.0)]
    c, s, e = tile_x(line), tile_x(start), tile_x(end)
    if side == "south":
        corners, normal = [(s, bottom, c), (e, bottom, c), (e, top, c), (s, top, c)], (0.0, 0.0, 1.0)
    elif side == "north":
        corners, normal = [(e, bottom, c), (s, bottom, c), (s, top, c), (e, top, c)], (0.0, 0.0, -1.0)
    elif side == "east":
        corners, normal = [(c, bottom, e), (c, bottom, s), (c, top, s), (c, top, e)], (1.0, 0.0, 0.0)
    else:
        corners, normal = [(c, bottom, s), (c, bottom, e), (c, top, e), (c, top, s)], (-1.0, 0.0, 0.0)
    geometry.quad(material, corners, uvs, normal)


def template_tree(doc: dict, binary: bytes, kit: Kit) -> list[tuple[str, tuple]]:
    """The kit's tree from the template: its materials' triangles inside the kit's box, from its anchor up to its
    height, relative to its anchor."""
    x0, z0, x1, z1 = kit.tree["box"]
    ax, ay, az = kit.tree["anchor"]
    top = ay + kit.tree["height"]
    materials = set(kit.tree["materials"])
    found = []
    for primitive in doc["meshes"][0]["primitives"]:
        material = doc["materials"][primitive["material"]]["name"]
        if material not in materials:
            continue
        attributes = primitive["attributes"]
        positions = accessor_values(doc, binary, attributes["POSITION"])
        uvs = accessor_values(doc, binary, attributes["TEXCOORD_0"])
        normals = accessor_values(doc, binary, attributes["NORMAL"])
        indices = [value[0] for value in accessor_values(doc, binary, primitive["indices"])]
        for i in range(0, len(indices), 3):
            corners = indices[i : i + 3]
            if all(
                x0 <= positions[v][0] <= x1 and z0 <= positions[v][2] <= z1 and ay <= positions[v][1] <= top
                for v in corners
            ):
                found.append(
                    (
                        material,
                        tuple(
                            (
                                (positions[v][0] - ax, positions[v][1] - ay, positions[v][2] - az),
                                tuple(uvs[v]),
                                tuple(normals[v]),
                            )
                            for v in corners
                        ),
                    )
                )
    if not found:
        raise ConfigError(f"{kit.template}: no tree triangles in the kit's box {kit.tree['box']}")
    return found


def tree_spots(trees: set[tuple[int, int]]) -> list[tuple[float, float]]:
    """Where trees stand, their base's top-left tile: 2x2 groups of tree tiles, and a pair in a line half a tile out."""
    left = set(trees)
    spots = []
    for x, z in sorted(trees, key=lambda cell: (cell[1], cell[0])):
        if (x, z) not in left:
            continue
        if {(x + 1, z), (x, z + 1), (x + 1, z + 1)} <= left:
            spots.append((float(x), float(z)))
            left -= {(x, z), (x + 1, z), (x, z + 1), (x + 1, z + 1)}
        elif (x, z + 1) in left:
            spots.append((x - 0.5, float(z)))
            left -= {(x, z), (x, z + 1)}
        elif (x + 1, z) in left:
            spots.append((float(x), z - 0.5))
            left -= {(x, z), (x + 1, z)}
    return spots


# --- The chunk ------------------------------------------------------------------------------------------------------


def generate(
    layout: Layout,
    labels: dict[int, str],
    kit: Kit,
    template: bytes,
    origin: tuple[int, int],
    buildings: list[Building],
    door_behaviors: set[int],
) -> Chunk:
    ox, oz = origin
    if not (0 <= ox and ox + layout.width <= CHUNK_TILES and 0 <= oz and oz + layout.height <= CHUNK_TILES):
        raise ConfigError(f"a {layout.width}x{layout.height} map at {origin} doesn't fit a {CHUNK_TILES}-tile chunk")
    unlabeled = sorted({layout.metatile(x, z) for z in range(layout.height) for x in range(layout.width)} - set(labels))
    if unlabeled:
        raise ConfigError(f"metatiles without a label: {', '.join(f'{m:#05x}' for m in unlabeled)}")

    # Each chunk tile's kind and whether it blocks
    kinds: dict[tuple[int, int], str] = {}
    blocked: dict[tuple[int, int], bool] = {}
    for z in range(CHUNK_TILES):
        for x in range(CHUNK_TILES):
            mx, mz = x - ox, z - oz
            if 0 <= mx < layout.width and 0 <= mz < layout.height:
                kinds[x, z] = labels[layout.metatile(mx, mz)]
                blocked[x, z] = layout.collision(mx, mz) != 0
            else:
                # Beyond the map: water where the map's edge is water and straight out from it, else blocked grass
                ex, ez = min(max(mx, 0), layout.width - 1), min(max(mz, 0), layout.height - 1)
                outward = mx == ex or mz == ez
                edge_water = labels[layout.metatile(ex, ez)] == "water"
                kinds[x, z] = "water" if outward and edge_water else "grass"
                blocked[x, z] = True
    water = {cell for cell, kind in kinds.items() if kind == "water"}

    doc, binary = read_glb(template)
    geometry = Geometry()
    surfaces = {name: set() for name in SURFACES}
    for cell, kind in kinds.items():
        surface, standing = KINDS[kind]
        surfaces[surface].add(cell)
        if standing == "flowers":
            surfaces["flowers"].add(cell)
    for name in SURFACES:
        level = kit.water_y if name == "water" else kit.ground_y
        for rect in rectangles(surfaces[name]):
            surface_quad(geometry, kit.surfaces[name], level, rect)

    # The banks between the water and the ground, facing the water
    edges: dict[tuple[str, int], list[int]] = {}
    for x, z in water:
        for (dx, dz), side in SIDES.items():
            neighbor = (x + dx, z + dz)
            if neighbor in kinds and neighbor not in water:
                # The bank faces back into the water, away from the land
                facing = {"north": "south", "south": "north", "west": "east", "east": "west"}[side]
                line = z + max(dz, 0) if dz else x + max(dx, 0)
                edges.setdefault((facing, line), []).append(x if dz else z)
    for (facing, line), starts in sorted(edges.items()):
        run = sorted(starts)
        begin = previous = run[0]
        for value in run[1:] + [None]:
            if value != previous + 1:
                wall(geometry, kit.bank[0], kit.bank[1], facing, line, begin, previous + 1, kit.water_y, kit.ground_y)
                begin = value
            previous = value if value is not None else previous

    # Fences: each row's runs, as the template draws them, flat strips across the tile
    fence = kit.fence
    fences = {cell for cell, kind in kinds.items() if kind == "fence"}
    for x, z, width, height in rectangles(fences):
        for z_row in range(z, z + height):
            near, far = tile_x(z_row) + fence["depth"][0], tile_x(z_row) + fence["depth"][1]
            for strip in fence["strips"]:
                y = kit.ground_y + strip["y"]
                xs = (tile_x(x), tile_x(x + width))
                vs = (1.0, 1.0 + width * fence["repeat"])
                corners = [(xs[0], y, near), (xs[0], y, far), (xs[1], y, far), (xs[1], y, near)]
                uvs = [(strip["u"][0], vs[0]), (strip["u"][1], vs[0]), (strip["u"][1], vs[1]), (strip["u"][0], vs[1])]
                geometry.quad(fence["material"], corners, uvs, (0.0, 1.0, 0.0))

    # Trees, the template's copied to each spot
    tree = template_tree(doc, binary, kit)
    for x, z in tree_spots({cell for cell, kind in kinds.items() if kind == "tree"}):
        base = (tile_x(x), kit.ground_y, tile_x(z))
        for material, vertices in tree:
            geometry.triangle(
                material,
                tuple(
                    (tuple(b + p for b, p in zip(base, position, strict=True)), uv, normal)
                    for position, uv, normal in vertices
                ),
            )

    # Props: the buildings at their doors, and signs and mailboxes on their tiles
    props: list[tuple[int, tuple[float, float, float]]] = []
    doors = {
        (x, z)
        for z in range(layout.height)
        for x in range(layout.width)
        if layout.behavior(layout.metatile(x, z)) in door_behaviors
    }
    listed = {building.door for building in buildings}
    if doors != listed:
        missing, extra = sorted(doors - listed), sorted(listed - doors)
        raise ConfigError(f"doors without a building: {missing}; buildings on no door: {extra}")
    # The tile in front of each door stays as the map has it, so that a building's body never shuts another's door
    fronts = {(x + ox, z + oz + 1) for x, z in doors}
    for building in buildings:
        if building.prop not in kit.doors or building.prop not in kit.footprints:
            raise ConfigError(f"the kit has no door or footprint for prop {building.prop}")
        dx, dz = kit.doors[building.prop]
        x, z = building.door[0] + ox - dx, building.door[1] + oz - dz
        props.append((building.prop, (tile_x(x), kit.ground_y, tile_x(z))))
        # Black 2's building blocks the tiles its body covers, up to its door's row: it isn't FireRed's shape
        x0, z0, x1, z1 = kit.footprints[building.prop]
        for cell in kinds:
            cx, cz = cell[0] * TILE + TILE / 2 - x * TILE, cell[1] * TILE + TILE / 2 - z * TILE
            if cell not in water and cell not in fronts and cell[1] <= z + dz and x0 <= cx <= x1 and z0 <= cz <= z1:
                blocked[cell] = True
    for cell, kind in sorted(kinds.items(), key=lambda item: (item[0][1], item[0][0])):
        if kind in ("sign", "mailbox"):
            x, z = cell
            props.append((kit.props[kind], (tile_x(x) + TILE / 2, kit.ground_y, tile_x(z) + TILE / 2)))

    glb, triangles = _write_model(doc, geometry, props, kit.ground_y)
    terrain = _terrain(kinds, blocked, water, kit)
    splits = "index,unused,slope0,slope1,offset0,offset1\n"
    vertices = 3 * sum(triangles.values())
    display = vertices * VERTEX_BYTES + DRAW_CALL_BYTES * len(doc["meshes"][0]["primitives"])
    return Chunk(glb, terrain, splits, triangles, len(props), display)


def _terrain(kinds: dict, blocked: dict, water: set, kit: Kit) -> str:
    rows = ["x,z,shape,slope,offset,tile_type,diagonal"]
    for z in range(CHUNK_TILES):
        for x in range(CHUNK_TILES):
            if (x, z) in water:
                shore = any((x + dx, z + dz) in kinds and (x + dx, z + dz) not in water for dx, dz in SIDES)
                height, tile_type = kit.water_height, kit.tile_types["shore" if shore else "water"]
            else:
                height = kit.ground_height
                tile_type = kit.tile_types["block" if blocked[x, z] else "walk"]
            rows.append(f"{x},{z},0,0,{height},{tile_type},0")
    return "\n".join(rows) + "\n"


def _write_model(template: dict, geometry: Geometry, props: list, ground_y: float) -> tuple[bytes, dict[str, int]]:
    """The template's GLB with its primitives drawn from the geometry, in its order, and the props as its empties.
    A material with no geometry keeps a degenerate triangle, since a Nitro draw call needs one."""
    doc = copy.deepcopy(template)
    for key in ("buffers", "bufferViews", "accessors", "skins"):
        doc.pop(key, None)
    # The template's own props go; its other nodes stay, renumbered
    keep = [i for i, node in enumerate(doc["nodes"]) if not node.get("name", "").startswith("bw2_prop_")]
    renumber = {old: new for new, old in enumerate(keep)}
    nodes = []
    for old in keep:
        node = dict(doc["nodes"][old])
        node.pop("skin", None)
        if "children" in node:
            node["children"] = [renumber[child] for child in node["children"] if child in renumber]
        nodes.append(node)
    roots = [renumber[root] for root in doc["scenes"][doc.get("scene", 0)]["nodes"] if root in renumber]
    for number, (prop, position) in enumerate(props):
        roots.append(len(nodes))
        nodes.append({"name": PROP_NODE.format(number, prop), "translation": list(position)})
    doc["nodes"] = nodes
    doc["scenes"][doc.get("scene", 0)]["nodes"] = roots

    binary = bytearray()
    views: list[dict] = []
    accessors: list[dict] = []

    def add(values: list[tuple], kind: str, component: int, target: int | None, bounds: bool = False) -> int:
        code = "f" if component == FLOAT else "I"
        data = b"".join(struct.pack("<" + code * len(value), *value) for value in values)
        binary.extend(bytes(-len(binary) % 4))
        view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        binary.extend(data)
        views.append(view)
        accessor = {"bufferView": len(views) - 1, "componentType": component, "count": len(values), "type": kind}
        if bounds:
            accessor["min"] = [min(value[i] for value in values) for i in range(len(values[0]))]
            accessor["max"] = [max(value[i] for value in values) for i in range(len(values[0]))]
        accessors.append(accessor)
        return len(accessors) - 1

    counts: dict[str, int] = {}
    primitives = []
    for primitive in template["meshes"][0]["primitives"]:
        material = template["materials"][primitive["material"]]["name"]
        triangles = geometry.triangles.get(material, [])
        counts[material] = len(triangles)
        if not triangles:
            point = ((0.0, ground_y, 0.0), (0.0, 0.0), (0.0, 1.0, 0.0))
            triangles = [(point, point, point)]
        vertices = [vertex for triangle in triangles for vertex in triangle]
        attributes = {
            "POSITION": add([v[0] for v in vertices], "VEC3", FLOAT, 34962, bounds=True),
            "NORMAL": add([v[2] for v in vertices], "VEC3", FLOAT, 34962),
            "TEXCOORD_0": add([v[1] for v in vertices], "VEC2", FLOAT, 34962),
            "COLOR_0": add([(1.0, 1.0, 1.0)] * len(vertices), "VEC3", FLOAT, 34962),
        }
        indices = add([(i,) for i in range(len(vertices))], "SCALAR", UNSIGNED_INT, 34963)
        primitives.append({"attributes": attributes, "indices": indices, "material": primitive["material"]})
    doc["meshes"][0]["primitives"] = primitives
    doc["bufferViews"] = views
    doc["accessors"] = accessors
    doc["buffers"] = [{"byteLength": len(binary) + (-len(binary) % 4)}]
    return write_glb(doc, bytes(binary)), counts
