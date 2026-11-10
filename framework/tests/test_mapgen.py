import struct
import unittest

from extractors.gba_gen3_layout import Layout
from kaleido import mapgen
from kaleido.config import ConfigError

MATERIALS = [
    "grass01ax",
    "michi01a",
    "michi01b",
    "ike01",
    "hana01_1",
    "gake1_1",
    "fence",
    "post",
    "forest",
    "ki02c",
    "ki03ax",
    "unused",
]
KIT = mapgen.Kit(
    template="MAP_MODEL_TEMPLATE",
    texture_set="MAP_TEXTURE_SET_T",
    texture_directory="t",
    textures={"post": "c12_post01"},
    ground_y=16,
    ground_height=51,
    water_y=8,
    water_height=169,
    surfaces={
        "grass": mapgen.Surface("grass01ax", (0.25, 0.25)),
        "path": mapgen.Surface("michi01b", (1, 1)),
        "water": mapgen.Surface("ike01", (0.5, 0.5)),
        "flowers": mapgen.Surface("hana01_1", (0.5, 1), 1),
    },
    edge=mapgen.Surface("michi01a", (0.5, 0.5), 0.25),
    bank=mapgen.Surface("gake1_1", (1, 1)),
    fence={"material": "fence", "height": 16, "offset": 12, "repeat": 1},
    billboards={"mailbox": {"material": "post", "width": 16, "height": 32, "offset": 12}},
    forest={"material": "forest", "height": 40, "repeat": 0.5},
    tree={"materials": ["ki02c", "ki03ax"], "box": [0, 0, 32, 32], "anchor": [0, 0, 0], "height": 64},
    tile_types={"walk": 0x800000, "block": 0x810001, "water": 0x16003F, "shore": 0xC30041},
    props={"sign": 152},
    doors={305: (0, 1)},
    footprints={305: (-35, -47.3, 55.5, 34.3)},
)
# Metatiles of the synthetic map and their kinds; 6 is a door
LABELS = {
    1: "grass",
    2: "path",
    3: "water",
    4: "tree",
    5: "building",
    6: "building",
    7: "sign",
    8: "flowers",
    9: "fence",
    10: "mailbox",
}
BLOCKS = {4, 5, 6, 7, 9, 10}
GRID = [
    [4, 4, 2, 2, 1, 1],
    [4, 4, 2, 5, 6, 1],
    [10, 8, 2, 2, 2, 9],
    [1, 1, 3, 3, 2, 7],
    [1, 1, 3, 3, 2, 1],
]


def layout(grid: list[list[int]] = GRID) -> Layout:
    cells = tuple(m | (1 << 10 if m in BLOCKS else 0) for row in grid for m in row)
    attributes = {m: (0x69 if m == 6 else 0) for row in grid for m in row}
    return Layout(len(grid[0]), len(grid), cells, 1, 1, (1,), attributes)


def template() -> bytes:
    """A template GLB: a primitive per material, the tree's two in the kit's box, the others a triangle elsewhere; a
    skeleton and a prop node, as Black 2's GLBs have them."""
    positions, uvs, normals, primitives = [], [], [], []
    binary = bytearray()
    views, accessors = [], []

    def add(values: list[tuple], kind: str, code: str, component: int) -> int:
        data = b"".join(struct.pack("<" + code * len(v), *v) for v in values)
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
        binary.extend(data)
        accessors.append({"bufferView": len(views) - 1, "componentType": component, "count": len(values), "type": kind})
        return len(accessors) - 1

    for index, material in enumerate(MATERIALS):
        x = 0.0 if material in ("ki02c", "ki03ax") else 100.0
        base = len(positions)
        positions += [(x, 3.0, 0.0), (x + 32, 3.0, 0.0), (x + 32, 40.0, 32.0)]
        uvs += [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
        normals += [(0.0, 1.0, 0.0)] * 3
        primitives.append((index, [(base,), (base + 1,), (base + 2,)]))
    attributes = {
        "POSITION": add(positions, "VEC3", "f", 5126),
        "TEXCOORD_0": add(uvs, "VEC2", "f", 5126),
        "NORMAL": add(normals, "VEC3", "f", 5126),
    }
    mesh_primitives = [
        {"attributes": attributes, "indices": add(indices, "SCALAR", "I", 5125), "material": material}
        for material, indices in primitives
    ]
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [1, 2]}],
        "nodes": [
            {"name": "skeleton"},
            {"mesh": 0, "skin": 0, "name": "tmpl", "children": [0]},
            {"name": "bw2_prop_0000_id_00001", "translation": [0, 16, 0]},
        ],
        "skins": [{"joints": [0]}],
        "meshes": [{"name": "tmpl", "primitives": mesh_primitives}],
        "materials": [
            {"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": i}}}
            for i, name in enumerate(MATERIALS)
        ],
        "textures": [{"source": i, "sampler": 0} for i in range(len(MATERIALS))],
        "images": [{"uri": f"../../textures/set/{name}.png"} for name in MATERIALS],
        "samplers": [{"wrapS": 10497, "wrapT": 10497}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
        "accessors": accessors,
    }
    return mapgen.write_glb(doc, bytes(binary))


def generate(grid: list[list[int]] = GRID, buildings=None, origin=(2, 3)) -> mapgen.Chunk:
    buildings = [mapgen.Building((4, 1), 305)] if buildings is None else buildings
    return mapgen.generate(layout(grid), LABELS, KIT, template(), origin, buildings, {0x69})


def terrain(chunk: mapgen.Chunk) -> dict[tuple[int, int], tuple[int, int]]:
    rows = chunk.terrain.splitlines()[1:]
    return {(int(r[0]), int(r[1])): (int(r[4]), int(r[5])) for r in (row.split(",") for row in rows)}


class RectanglesTest(unittest.TestCase):
    def test_cover_every_cell_once(self) -> None:
        cells = {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (5, 5)}
        found = mapgen.rectangles(cells)
        covered = [(x + i, z + j) for x, z, w, h in found for i in range(w) for j in range(h)]
        self.assertEqual(sorted(covered), sorted(cells))
        self.assertEqual(len(found), 3)

    def test_trees_stand_on_2x2_groups_and_center_on_a_pair(self) -> None:
        trees = {(0, 0), (1, 0), (0, 1), (1, 1), (5, 0), (5, 1)}
        self.assertEqual(mapgen.tree_spots(trees), [(0.0, 0.0), (4.5, 0.0)])


class TreeShapeTest(unittest.TestCase):
    def test_a_tree_with_open_ground_behind_it_is_shorter(self) -> None:
        # A tree whose base's top row is z = 10: open ground at z = 9, at z = 8, or neither
        self.assertEqual(mapgen.tree_shape((4.0, 10.0), lambda x, z: z == 9).height, 0.5)
        self.assertEqual(mapgen.tree_shape((4.0, 10.0), lambda x, z: z == 8).height, 0.75)
        self.assertEqual(mapgen.tree_shape((4.0, 10.0), lambda x, z: False).height, 1.0)
        # Ground behind another column doesn't count
        self.assertEqual(mapgen.tree_shape((4.0, 10.0), lambda x, z: x == 7 and z == 9).height, 1.0)

    def test_each_spot_varies_the_same_way_every_time(self) -> None:
        shapes = [mapgen.tree_shape((float(x), 10.0), lambda x, z: False) for x in range(0, 40, 2)]
        self.assertEqual(shapes, [mapgen.tree_shape((float(x), 10.0), lambda x, z: False) for x in range(0, 40, 2)])
        self.assertGreater(len({shape.turn for shape in shapes}), 5)
        for shape in shapes:
            self.assertLessEqual(abs(shape.turn), mapgen.TREE_TURN)
            self.assertLessEqual(abs(shape.size - 1), mapgen.TREE_SIZE_SPREAD + 1e-9)
            self.assertTrue(all(abs(d) <= mapgen.TREE_OFFSET for d in shape.offset))


class GenerateTest(unittest.TestCase):
    def test_keeps_the_templates_draw_calls_each_with_a_triangle(self) -> None:
        doc, _ = mapgen.read_glb(generate().glb)
        primitives = doc["meshes"][0]["primitives"]
        self.assertEqual([p["material"] for p in primitives], list(range(len(MATERIALS))))
        counts = [doc["accessors"][p["indices"]]["count"] for p in primitives]
        self.assertTrue(all(count >= 3 and count % 3 == 0 for count in counts))
        self.assertNotIn("skins", doc)
        self.assertNotIn("skin", doc["nodes"][1])

    def test_draws_each_kind_in_its_material(self) -> None:
        triangles = generate().triangles
        self.assertEqual(triangles["unused"], 0)
        # Each tree is the template's tree triangles once: the map's tree, and the forest's in front where needed
        self.assertEqual(triangles["ki02c"], triangles["ki03ax"])
        self.assertGreater(triangles["ki02c"], 1)
        for material in (
            "grass01ax",
            "michi01a",
            "michi01b",
            "ike01",
            "hana01_1",
            "gake1_1",
            "fence",
            "post",
            "forest",
        ):
            self.assertGreater(triangles[material], 0, material)

    def test_the_forest_starts_with_trees_where_the_maps_edge_has_none(self) -> None:
        # A 2x2 map: of grass, trees stand around it; of trees, only its own one stands
        grass = generate([[1, 1], [1, 1]], buildings=[], origin=(10, 10)).triangles["ki02c"]
        trees = generate([[4, 4], [4, 4]], buildings=[], origin=(10, 10)).triangles["ki02c"]
        self.assertEqual(trees, 1)
        self.assertEqual(grass, 4)

    def test_points_the_kits_materials_at_its_other_textures(self) -> None:
        doc, _ = mapgen.read_glb(generate().glb)
        post = next(material for material in doc["materials"] if material["name"] == "post")
        texture = doc["textures"][post["pbrMetallicRoughness"]["baseColorTexture"]["index"]]
        self.assertEqual(doc["images"][texture["source"]]["uri"], "../../textures/t/c12_post01.png")
        self.assertEqual(texture["sampler"], 0)

    def test_draws_a_mailbox_as_an_upright_quad_facing_south(self) -> None:
        doc, binary = mapgen.read_glb(generate().glb)
        index = MATERIALS.index("post")
        primitive = doc["meshes"][0]["primitives"][index]
        normals = mapgen.accessor_values(doc, binary, primitive["attributes"]["NORMAL"])
        self.assertEqual(set(normals), {(0.0, 0.0, 1.0)})
        self.assertEqual(len(normals), 6)

    def test_no_mailbox_stands_under_a_buildings_body(self) -> None:
        # A second mailbox at map (2, 1), under the building's body: only the first, at map (0, 2), is drawn
        grid = [row[:] for row in GRID]
        grid[1][2] = 10
        doc, binary = mapgen.read_glb(generate(grid).glb)
        primitive = doc["meshes"][0]["primitives"][MATERIALS.index("post")]
        self.assertEqual(len(mapgen.accessor_values(doc, binary, primitive["attributes"]["NORMAL"])), 6)

    def test_places_buildings_at_their_doors_and_signs_on_their_tiles(self) -> None:
        doc, _ = mapgen.read_glb(generate().glb)
        props = {node["name"]: node["translation"] for node in doc["nodes"] if node["name"].startswith("bw2_prop_")}
        # The door at map (4, 1) is chunk tile (6, 4); the prop's origin is a tile behind it
        self.assertEqual(props["bw2_prop_0000_id_00305"], [6 * 16 - 256, 16.0, 3 * 16 - 256])
        self.assertEqual(props["bw2_prop_0001_id_00152"], [7 * 16 - 256 + 8, 16.0, 6 * 16 - 256 + 8])
        self.assertNotIn("bw2_prop_0000_id_00001", props)

    def test_terrain_follows_the_maps_collision_and_water(self) -> None:
        tiles = terrain(generate())
        self.assertEqual(len(tiles), 32 * 32)
        self.assertEqual(tiles[0, 0], (51, KIT.tile_types["block"]))
        self.assertEqual(tiles[2 + 2, 3 + 2], (51, KIT.tile_types["walk"]))
        self.assertEqual(tiles[2 + 0, 3 + 0], (51, KIT.tile_types["block"]))
        self.assertEqual(tiles[2 + 2, 3 + 3], (169, KIT.tile_types["shore"]))
        # The water at the map's edge runs on to the chunk's
        self.assertEqual(tiles[2 + 3, 31][0], 169)

    def test_a_buildings_body_blocks_up_to_its_door_row(self) -> None:
        tiles = terrain(generate())
        # The path at map (2, 0) is under the building's body; map (2, 2), past its door row, isn't
        self.assertEqual(tiles[2 + 2, 3 + 0][1], KIT.tile_types["block"])
        self.assertEqual(tiles[2 + 2, 3 + 2][1], KIT.tile_types["walk"])

    def test_a_firered_building_tile_outside_every_body_is_open(self) -> None:
        # A building tile at map (0, 2), past the body's door row, which FireRed's collision blocks
        grid = [row[:] for row in GRID]
        grid[2][0] = 5
        tiles = terrain(generate(grid))
        self.assertEqual(tiles[2 + 0, 3 + 2][1], KIT.tile_types["walk"])
        # The building tile under the body, map (3, 1), stays blocked
        self.assertEqual(tiles[2 + 3, 3 + 1][1], KIT.tile_types["block"])

    def test_a_buildings_body_never_blocks_the_tile_in_front_of_a_door(self) -> None:
        # A second door at map (2, 0), whose front, map (2, 1), the first building's body would otherwise cover
        grid = [row[:] for row in GRID]
        grid[0][2] = 6
        buildings = [mapgen.Building((4, 1), 305), mapgen.Building((2, 0), 305)]
        tiles = terrain(generate(grid, buildings))
        self.assertEqual(tiles[2 + 2, 3 + 1][1], KIT.tile_types["walk"])
        self.assertEqual(terrain(generate())[2 + 2, 3 + 1][1], KIT.tile_types["block"])

    def test_needs_every_metatile_labeled(self) -> None:
        grid = [row[:] for row in GRID]
        grid[4][5] = 99
        with self.assertRaisesRegex(ConfigError, "0x063"):
            generate(grid)

    def test_needs_a_building_at_every_door(self) -> None:
        with self.assertRaisesRegex(ConfigError, "doors without a building"):
            generate(buildings=[])

    def test_needs_the_map_to_fit_the_chunk(self) -> None:
        with self.assertRaises(ConfigError):
            generate(origin=(30, 0))


if __name__ == "__main__":
    unittest.main()
