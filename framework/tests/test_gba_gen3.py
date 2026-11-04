import json
import struct
import tempfile
import unittest
from pathlib import Path

from extractors import gba_gen3
from kaleido import extract
from kaleido.config import Paths

BASE = gba_gen3.ROM_BASE


def synthetic_rom(route_species: int = 19) -> bytes:
    """A small image shaped like the structures the reader looks for, with made-up values: two map names, two map
    headers in two groups, and wild encounter headers for both maps."""
    rom = bytearray(0x1000)

    def put(offset: int, data: bytes) -> None:
        rom[offset : offset + len(data)] = data

    def pointer(offset: int) -> bytes:
        return struct.pack("<I", BASE + offset)

    put(0x100, gba_gen3.encode("PALLET TOWN"))
    put(0x120, gba_gen3.encode("ROUTE 1"))
    put(0x200, pointer(0x100) + pointer(0x120))  # names, from KANTO_MAPSEC_START
    for offset, section in ((0x300, 0x58), (0x340, 0x59)):  # map headers: three pointers, no connections
        put(offset, pointer(0x100) * 3)
        rom[offset + gba_gen3.MAP_SECTION_OFFSET] = section
    put(0x400, pointer(0x300) + pointer(0x340))  # group 0 = [Pallet Town], group 1 = [Route 1], back to back
    put(0x500, pointer(0x400) + pointer(0x404))  # the table of groups

    def header(group: int, number: int, land: int) -> bytes:
        return bytes([group, number, 0, 0]) + pointer(land) + bytes(12)

    put(0x600, header(0, 0, 0x700) + header(1, 0, 0x720) + b"\xff\xff" + bytes(18))
    put(0x700, bytes([10, 0, 0, 0]) + pointer(0x780))
    put(0x720, bytes([21, 0, 0, 0]) + pointer(0x740))
    slots = b"".join(struct.pack("<BBH", 2 + i % 4, 3 + i % 4, 16 if i % 2 else route_species) for i in range(12))
    put(0x740, slots)
    put(0x780, slots.replace(struct.pack("<H", route_species), struct.pack("<H", 1)))
    return bytes(rom)


class Gen3Test(unittest.TestCase):
    def test_finds_a_map_by_its_name(self) -> None:
        rom = gba_gen3.Rom(synthetic_rom())
        self.assertEqual(gba_gen3.map_section(rom, "ROUTE 1"), 0x59)
        self.assertEqual(gba_gen3.map_ids(rom, 0x59), [(1, 0)])
        self.assertEqual(gba_gen3.find_wild_headers(rom), 0x600)

    def test_reads_the_maps_land_encounters(self) -> None:
        land = gba_gen3.land_encounters(gba_gen3.Rom(synthetic_rom()), "ROUTE 1")
        self.assertEqual(land.rate, 21)
        self.assertEqual(land.slots[0], gba_gen3.Slot(19, 2, 3))
        self.assertEqual(len(land.slots), gba_gen3.LAND_SLOTS)

    def test_species_past_251_are_refused(self) -> None:
        with self.assertRaisesRegex(gba_gen3.ExtractError, "national order"):
            gba_gen3.land_encounters(gba_gen3.Rom(synthetic_rom(route_species=277)), "ROUTE 1")

    def test_an_unknown_name_is_an_error(self) -> None:
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no table names"):
            gba_gen3.map_section(gba_gen3.Rom(synthetic_rom()), "ROUTE 2")

    def test_encodes_capitals_digits_and_spaces(self) -> None:
        self.assertEqual(gba_gen3.encode("A 1"), bytes([0xBB, 0x00, 0xA2, 0xFF]))


class EncounterTablePathTest(unittest.TestCase):
    def test_follows_the_zone_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = Paths(Path(temp))
            header = paths.engine / "res/field/zones/route_19.json"
            header.parent.mkdir(parents=True)
            header.write_text(json.dumps({"encounters": "ENCOUNTERS_ROUTE_19"}))
            self.assertEqual(extract.encounter_table_path(paths, "ZONE_ROUTE_19"), "res/field/encounters/route_19.json")


if __name__ == "__main__":
    unittest.main()
