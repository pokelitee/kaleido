import struct
import unittest

from extractors import gba_gen3, gba_gen3_layout
from extractors.gba_gen3 import ExtractError

BASE = gba_gen3.ROM_BASE


def pointer(offset: int) -> bytes:
    return struct.pack("<I", BASE + offset)


def synthetic_rom(width: int = 3, height: int = 2) -> bytes:
    """A map header at 0x100 whose layout is width x height, a 1x1 border, and two tilesets' attribute tables."""
    rom = bytearray(0x800)

    def put(offset: int, data: bytes) -> None:
        rom[offset : offset + len(data)] = data

    put(0x100, pointer(0x200) + pointer(0x300) + pointer(0x300) + bytes(4))
    put(0x200, struct.pack("<ii", width, height) + pointer(0x260) + pointer(0x240) + pointer(0x280) + pointer(0x2A0))
    put(0x218, bytes([1, 1]))
    # Metatile 1, metatile 1 that blocks, metatile 5 at elevation 3; then two of the secondary's and metatile 2
    put(0x240, struct.pack("<6H", 0x001, 0x401, 0x3005, 0x281, 0x002, 0x282))
    put(0x260, struct.pack("<H", 0x002))
    put(0x280 + gba_gen3_layout.TILESET_ATTRIBUTES, pointer(0x400))
    put(0x2A0 + gba_gen3_layout.TILESET_ATTRIBUTES, pointer(0x500))
    for metatile in (1, 2, 5):
        put(0x400 + 4 * metatile, struct.pack("<I", 0x20000000 | metatile))
    put(0x500 + 4, struct.pack("<I", 0x69))
    put(0x500 + 8, struct.pack("<I", 0x15))
    return bytes(rom)


class LayoutTest(unittest.TestCase):
    def test_reads_the_grid_its_cells_and_the_border(self) -> None:
        layout = gba_gen3_layout.layout(gba_gen3.Rom(synthetic_rom()), 0x100)
        self.assertEqual((layout.width, layout.height), (3, 2))
        self.assertEqual([layout.metatile(x, 0) for x in range(3)], [1, 1, 5])
        self.assertEqual([layout.collision(x, 0) for x in range(3)], [0, 1, 0])
        self.assertEqual(layout.elevation(2, 0), 3)
        self.assertEqual(layout.border, (0x002,))

    def test_reads_each_metatiles_attributes_from_its_tileset(self) -> None:
        layout = gba_gen3_layout.layout(gba_gen3.Rom(synthetic_rom()), 0x100)
        self.assertEqual(layout.behavior(5), 5)
        self.assertEqual(layout.layer_type(1), 1)
        self.assertEqual(layout.behavior(0x281), gba_gen3_layout.WARP_DOOR)
        self.assertEqual(layout.behavior(0x282), 0x15)
        self.assertEqual(set(layout.attributes), {1, 2, 5, 0x281, 0x282})

    def test_refuses_what_isnt_a_map_header(self) -> None:
        with self.assertRaises(ExtractError):
            gba_gen3_layout.layout(gba_gen3.Rom(synthetic_rom()), 0x104)

    def test_refuses_a_layout_of_no_maps_size(self) -> None:
        with self.assertRaises(ExtractError):
            gba_gen3_layout.layout(gba_gen3.Rom(synthetic_rom(width=0)), 0x100)


if __name__ == "__main__":
    unittest.main()
