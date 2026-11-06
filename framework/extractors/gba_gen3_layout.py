"""FireRed and LeafGreen's map layouts: a map's grid of metatiles, each cell's collision and elevation, its border, and
the attributes of the metatiles it uses (docs/plan/09-generated-maps.md, the converter's first stage).

The formats, from reading pret/pokefirered at ce6406d8 (nothing copied), are in docs/research/generated-maps-spike.md
§4:
- a map header's word 0 points to its layout: the width and height (32-bit), pointers to the border and the grid, to the
  primary and the secondary tileset, then the border's width and height (a byte each);
- a grid cell is 16 bits: the metatile in bits 0-9, the collision in 10-11 and the elevation in 12-15;
- a tileset's word 5, at 0x14, points to its metatiles' attributes, 32 bits each: the behavior in bits 0-8 and the
  layer type in 29-30. Metatiles 0 to 639 are the primary tileset's; from 640 on, the secondary's, from its first."""

import struct
from dataclasses import dataclass

from extractors.gba_gen3 import ExtractError, Rom, _is_map_header

PRIMARY_METATILES = 640
TOTAL_METATILES = 1024
METATILE_MASK = 0x3FF
COLLISION_SHIFT, COLLISION_MASK = 10, 0x3
ELEVATION_SHIFT = 12
BEHAVIOR_MASK = 0x1FF
LAYER_SHIFT, LAYER_MASK = 29, 0x3
TILESET_ATTRIBUTES = 0x14
# The behavior of a building's door, which warps as the player walks into it
WARP_DOOR = 0x69
# FireRed's largest maps are well under this on each side; a bigger value means the header isn't a layout's
MAX_SIDE = 256


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    # Raw grid cells, row by row
    cells: tuple[int, ...]
    border_width: int
    border_height: int
    border: tuple[int, ...]
    # The attribute word of each metatile the grid or the border uses
    attributes: dict[int, int]

    def cell(self, x: int, z: int) -> int:
        return self.cells[z * self.width + x]

    def metatile(self, x: int, z: int) -> int:
        return self.cell(x, z) & METATILE_MASK

    def collision(self, x: int, z: int) -> int:
        return self.cell(x, z) >> COLLISION_SHIFT & COLLISION_MASK

    def elevation(self, x: int, z: int) -> int:
        return self.cell(x, z) >> ELEVATION_SHIFT

    def behavior(self, metatile: int) -> int:
        return self.attributes[metatile] & BEHAVIOR_MASK

    def layer_type(self, metatile: int) -> int:
        return self.attributes[metatile] >> LAYER_SHIFT & LAYER_MASK


def _pointer(rom: Rom, value: int, what: str) -> int:
    if not rom.is_pointer(value):
        raise ExtractError(f"{what} isn't a pointer into the ROM: {value:#x}")
    return rom.at(value)


def _cells(rom: Rom, offset: int, count: int, what: str) -> tuple[int, ...]:
    if offset + 2 * count > len(rom.data):
        raise ExtractError(f"{what} runs past the ROM's end")
    return struct.unpack_from(f"<{count}H", rom.data, offset)


def layout(rom: Rom, header: int) -> Layout:
    """The layout of the map whose header is at header."""
    if not _is_map_header(rom, header):
        raise ExtractError(f"{header:#x} isn't a map header")
    at = _pointer(rom, rom.u32(header), "the map's layout")
    width, height, border, grid, primary, secondary = struct.unpack_from("<iiIIII", rom.data, at)
    if not (0 < width <= MAX_SIDE and 0 < height <= MAX_SIDE):
        raise ExtractError(f"the layout at {at:#x} is {width}x{height}, which isn't a map's size")
    border_width, border_height = rom.data[at + 24], rom.data[at + 25]
    cells = _cells(rom, _pointer(rom, grid, "the layout's grid"), width * height, "the grid")
    border_cells = _cells(rom, _pointer(rom, border, "the border"), border_width * border_height, "the border")
    tables = [
        _pointer(rom, rom.u32(_pointer(rom, tileset, f"the {which} tileset") + TILESET_ATTRIBUTES), "attributes")
        for which, tileset in (("primary", primary), ("secondary", secondary))
    ]
    attributes = {}
    for cell in (*cells, *border_cells):
        metatile = cell & METATILE_MASK
        if metatile >= TOTAL_METATILES:
            raise ExtractError(f"metatile {metatile:#x} is past the tilesets' {TOTAL_METATILES}")
        if metatile not in attributes:
            table, index = (
                (tables[0], metatile) if metatile < PRIMARY_METATILES else (tables[1], metatile - PRIMARY_METATILES)
            )
            attributes[metatile] = rom.u32(table + 4 * index)
    return Layout(width, height, cells, border_width, border_height, border_cells, attributes)
