import json
import struct
import tempfile
import unittest
from pathlib import Path

from extractors import gba_gen3
from kaleido import extract, layers
from kaleido.config import ConfigError, Paths
from kaleido.games import Game

BASE = gba_gen3.ROM_BASE


SECTION_NAMES = ["PALLET TOWN", "ROUTE 1"] + [f"PLACE {i}" for i in range(2, gba_gen3.KANTO_MAPSEC_COUNT)]


def synthetic_rom(route_species: int = 19) -> bytes:
    """A small image shaped like the structures the reader looks for, with made-up values: a table of map section names
    and a longer decoy that starts with the same name, two map headers in two groups and a shorter decoy of the groups'
    table, and wild encounter headers for both maps."""
    rom = bytearray(0x3000)

    def put(offset: int, data: bytes) -> None:
        rom[offset : offset + len(data)] = data

    def pointer(offset: int) -> bytes:
        return struct.pack("<I", BASE + offset)

    strings = []
    for i, name in enumerate(SECTION_NAMES):
        strings.append(0x1000 + i * 16)
        put(strings[-1], gba_gen3.encode(name))
    put(0x2000, b"".join(pointer(s) for s in strings))  # the names, from KANTO_MAPSEC_START
    put(0x2400, b"".join(pointer(strings[i % 3]) for i in range(120)))  # a longer run of names, like the region map's
    for offset, section in ((0x300, 0x58), (0x340, 0x59)):  # map headers: three pointers, no connections
        put(offset, pointer(0x800) * 3)
        rom[offset + gba_gen3.MAP_SECTION_OFFSET] = section
    put(0x400, pointer(0x300) + pointer(0x340))  # group 0 = [Pallet Town], group 1 = [Route 1], back to back
    put(0x408, pointer(0x400) + pointer(0x404))  # the table of groups, right after the last group's table
    put(0x480, pointer(0x340))  # a table shaped like a group's that lists Route 1 too
    put(0x500, pointer(0x480))  # and a shorter table of groups that points to it

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

    def test_lists_only_the_maps_of_the_table_of_groups(self) -> None:
        rom = gba_gen3.Rom(synthetic_rom())
        self.assertEqual(gba_gen3.map_groups(rom), [0x400, 0x404])
        self.assertEqual(gba_gen3.map_ids(rom, 0x58), [(0, 0)])
        self.assertEqual(gba_gen3.map_ids(rom, 0x59), [(1, 0)])
        # The table of groups points to tables that also pass for map headers, so it ends the last group's table
        self.assertEqual(gba_gen3.group_headers(rom, 1), [0x340])
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no map group 2"):
            gba_gen3.group_headers(rom, 2)

    def test_reads_the_maps_land_encounters(self) -> None:
        land = gba_gen3.land_encounters(gba_gen3.Rom(synthetic_rom()), "ROUTE 1")
        self.assertEqual(land.rate, 21)
        self.assertEqual(land.slots[0], gba_gen3.Slot(19, 2, 3))
        self.assertEqual(len(land.slots), gba_gen3.LAND_SLOTS)

    def test_species_past_251_are_refused(self) -> None:
        with self.assertRaisesRegex(gba_gen3.ExtractError, "national order"):
            gba_gen3.land_encounters(gba_gen3.Rom(synthetic_rom(route_species=277)), "ROUTE 1")

    def test_an_unknown_name_is_an_error(self) -> None:
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no map section named"):
            gba_gen3.map_section(gba_gen3.Rom(synthetic_rom()), "ROUTE 2")

    def test_encodes_capitals_digits_and_spaces(self) -> None:
        self.assertEqual(gba_gen3.encode("A 1"), bytes([0xBB, 0x00, 0xA2, 0xFF]))

    def test_decodes_letters_punctuation_and_line_breaks(self) -> None:
        data = bytes([0xC2, 0xD9, 0xB4, 0xE7, 0x00, 0xE0, 0x1B, 0xAB, 0xFE, 0xA2, 0xB5, 0xFF])
        self.assertEqual(gba_gen3.decode(data, 0), "He’s lé!\n1♂")

    def test_control_codes_and_unended_strings_are_refused(self) -> None:
        with self.assertRaisesRegex(gba_gen3.ExtractError, "0xfc"):
            gba_gen3.decode(bytes([0xBB, 0xFC, 0x01, 0xFF]), 0)
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no end"):
            gba_gen3.decode(bytes([0xBB] * 8), 0, limit=4)

    def test_finds_the_map_section_names_without_knowing_one(self) -> None:
        self.assertEqual(gba_gen3.section_names(gba_gen3.Rom(synthetic_rom())), SECTION_NAMES)


class PlaceNamesTest(unittest.TestCase):
    def test_names_the_place_of_each_locations_zone(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = Paths(Path(temp))
            for zone, place in (("aspertia_city", "PLACE_ASPERTIA_CITY"), ("route_19", "PLACE_ROUTE_19")):
                header = paths.engine / f"res/field/zones/{zone}.json"
                header.parent.mkdir(parents=True, exist_ok=True)
                header.write_text(json.dumps({"place": place}))
            region = paths.root / "content/regions/r"
            region.mkdir(parents=True)
            (region / "layer.json").write_text('{"kind": "region"}')
            zones = {"locations": {"pallet": "ZONE_ASPERTIA_CITY", "road": "ZONE_ROUTE_19"}}
            (region / "zones.json").write_text(json.dumps(zones))
            stack = layers.load_stack(paths, ["regions/r"])
            game = Game("g", "G", {}, ("regions/r",), ("firered",))
            recipe = {"kind": "gba_gen3_place_names", "source": "firered", "places": {"pallet": 0x58, "road": 0x59}}
            roms = {"firered": gba_gen3.Rom(synthetic_rom())}
            outputs = extract.KINDS["gba_gen3_place_names"](paths, game, stack, recipe, roms)
            self.assertEqual(
                [(path, json.loads(content)) for path, content in outputs],
                [
                    ("res/field/places/aspertia_city.json.merge.json", {"name": "Pallet Town"}),
                    ("res/field/places/route_19.json.merge.json", {"name": "Route 1"}),
                ],
            )
            recipe["places"] = {"pallet": 0x58 + gba_gen3.KANTO_MAPSEC_COUNT}
            with self.assertRaisesRegex(ConfigError, "isn't one of the source's 109 names"):
                extract.KINDS["gba_gen3_place_names"](paths, game, stack, recipe, roms)


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
