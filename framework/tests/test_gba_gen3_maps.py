import json
import struct
import tempfile
import unittest
from pathlib import Path

from extractors import gba_gen3, gba_gen3_maps
from kaleido import extract, layers
from kaleido.config import ConfigError, Paths
from kaleido.games import Game

BASE = gba_gen3.ROM_BASE
TEXTS = {"a": 0x600, "b": 0x610, "c": 0x620, "d": 0x630, "e": 0x640, "f": 0x650, "g": 0x660}


def pointer(offset: int) -> bytes:
    return struct.pack("<I", BASE + offset)


def synthetic_rom(npc_script: bytes | None = None) -> bytes:
    """Two maps in two groups, the first with made-up events and scripts: NPC 1 (and NPC 2, which has no script), a
    trigger, a sign and a hidden item, and two map scripts, one through a table."""
    rom = bytearray(0x800)

    def put(offset: int, data: bytes) -> None:
        rom[offset : offset + len(data)] = data

    put(0x100, pointer(0x700) + pointer(0x200) + pointer(0x300) + bytes(4))  # map 0.0
    put(0x140, pointer(0x700) + pointer(0x2F0) + pointer(0x2F8) + bytes(4))  # map 1.0, no events
    put(0x400, pointer(0x100) + pointer(0x140))  # group 0's table, then group 1's
    put(0x480, pointer(0x400) + pointer(0x404))  # the table of groups
    put(0x4C0, pointer(0x404))  # a shorter run that also points to a group
    put(0x200, bytes([2, 0, 1, 2]) + pointer(0x220) + bytes(4) + pointer(0x260) + pointer(0x280))
    put(0x220, bytes([1]) + bytes(15) + pointer(0x500))
    put(0x238, bytes([2]) + bytes(23))
    put(0x260, bytes(12) + pointer(0x540))
    put(0x280, bytes(8) + pointer(0x560))
    put(0x28C, bytes([0, 0, 0, 0, 0, 7]) + bytes(2) + struct.pack("<I", 0x12345))
    put(0x300, bytes([3]) + pointer(0x580) + bytes([2]) + pointer(0x320) + bytes([0]))
    put(0x320, struct.pack("<HH", 0x4050, 0) + pointer(0x5A0) + bytes(2))

    def show(text: str) -> bytes:  # the standard message script's word 0, then the call
        return bytes([0x0F, 0]) + pointer(TEXTS[text]) + bytes([0x09, 2])

    default = bytes([0x6A, 0x5A, 0x2B, 1, 0, 0x06, 1]) + pointer(0x520) + show("a") + bytes([0x6C, 0x02])
    put(0x500, default if npc_script is None else npc_script)
    put(0x520, show("b") + bytes([0x02]))
    put(0x540, bytes([0x67]) + pointer(TEXTS["c"]) + bytes([0x04]) + pointer(0x500) + bytes([0x02]))
    put(0x560, show("d") + bytes([0x02]))
    put(0x580, bytes([0x16, 0x50, 0x40, 1, 0, 0x02]))
    put(0x5A0, bytes([0x5C, 1, 5, 0, 1, 0]) + pointer(TEXTS["e"]) + pointer(TEXTS["f"]) + pointer(0x5C0) + b"\x02")
    put(0x5C0, show("g") + bytes([0x02]))
    put(TEXTS["a"], gba_gen3.encode("Hi, ")[:-1] + bytes([0xFD, 0x01, 0xAB, 0xFF]))
    for name in "bcdefg":
        put(TEXTS[name], gba_gen3.encode(name.upper()))
    return bytes(rom)


class MessageTest(unittest.TestCase):
    def test_converts_breaks_names_and_fonts_to_gen_5_text(self) -> None:
        data = bytes([0xC2, 0xDD, 0xFE, 0xEC, 0xFA, 0xED, 0xFB, 0xFD, 0x01, 0xFD, 0x06, 0xFC, 0x06, 0x05, 0xEE, 0xFF])
        self.assertEqual(gba_gen3.message(data, 0), "Hi\\nx{be00}\\ny{be01}\\n{0100:0}{0100:1}z")

    def test_other_control_codes_are_refused(self) -> None:
        with self.assertRaisesRegex(gba_gen3.ExtractError, "0xfc 0x08 at 0x1"):
            gba_gen3.message(bytes([0xBB, 0xFC, 0x08, 0x10, 0xFF]), 0)
        with self.assertRaisesRegex(gba_gen3.ExtractError, "0xfd 0x07"):
            gba_gen3.message(bytes([0xFD, 0x07, 0xFF]), 0)
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no end of message"):
            gba_gen3.message(bytes([0xBB] * 8), 0, limit=4)


class MapsTest(unittest.TestCase):
    def test_finds_maps_by_group_and_number(self) -> None:
        rom = gba_gen3.Rom(synthetic_rom())
        self.assertEqual(gba_gen3.map_groups(rom), [0x400, 0x404])
        self.assertEqual(gba_gen3_maps.map_header(rom, 0, 0), 0x100)
        self.assertEqual(gba_gen3_maps.map_header(rom, 1, 0), 0x140)
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no map 0.1"):
            gba_gen3_maps.map_header(rom, 0, 1)
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no map group 2"):
            gba_gen3_maps.map_header(rom, 2, 0)

    def test_lists_where_scripts_start(self) -> None:
        rom = gba_gen3.Rom(synthetic_rom())
        self.assertEqual(
            gba_gen3_maps.entries(rom, 0x100),
            [
                gba_gen3_maps.Entry("Npc1", 0x500),
                gba_gen3_maps.Entry("Trigger0", 0x540),
                gba_gen3_maps.Entry("Sign0", 0x560),
                gba_gen3_maps.Entry("MapScript0", 0x580),
                gba_gen3_maps.Entry("MapScript1", 0x5A0),
            ],
        )

    def test_follows_jumps_calls_and_battles_to_each_message(self) -> None:
        rom = gba_gen3.Rom(synthetic_rom())
        self.assertEqual(gba_gen3_maps.messages(rom, 0x540), [TEXTS["a"], TEXTS["b"], TEXTS["c"]])
        self.assertEqual(
            gba_gen3_maps.map_messages(rom, 0, 0),
            [
                ("Npc1", [TEXTS["a"], TEXTS["b"]]),
                ("Trigger0", [TEXTS["c"]]),
                ("Sign0", [TEXTS["d"]]),
                ("MapScript0", []),
                ("MapScript1", [TEXTS["e"], TEXTS["f"], TEXTS["g"]]),
            ],
        )

    def test_an_unknown_opcode_is_an_error(self) -> None:
        rom = gba_gen3.Rom(synthetic_rom(npc_script=bytes([0x6A, 0xFF, 0x02])))
        with self.assertRaisesRegex(gba_gen3.ExtractError, "opcode 0xff at 0x501"):
            gba_gen3_maps.messages(rom, 0x500)


class MapTextTest(unittest.TestCase):
    def test_appends_each_maps_messages_to_its_zones_bank(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = Paths(Path(temp))
            header = paths.engine / "res/field/zones/aspertia_city.json"
            header.parent.mkdir(parents=True)
            header.write_text(json.dumps({"text": "SCRIPT_TEXT_ASPERTIA_CITY"}))
            region = paths.root / "content/regions/r"
            region.mkdir(parents=True)
            (region / "layer.json").write_text('{"kind": "region"}')
            (region / "zones.json").write_text(json.dumps({"locations": {"pallet_town": "ZONE_ASPERTIA_CITY"}}))
            stack = layers.load_stack(paths, ["regions/r"])
            game = Game("g", "G", {}, ("regions/r",), ("firered",))
            recipe = {"kind": "gba_gen3_map_text", "source": "firered", "maps": {"pallet_town": [0, 0]}}
            roms = {"firered": gba_gen3.Rom(synthetic_rom())}
            [(path, content)] = extract.KINDS["gba_gen3_map_text"](paths, game, stack, recipe, roms)
            self.assertEqual(path, "res/text/script/aspertia_city.txt.merge.json")
            self.assertEqual(
                json.loads(content),
                {
                    "$append": {
                        "PalletTown_Text_Npc1_0": "Hi, {0100:0}!",
                        "PalletTown_Text_Npc1_1": "B",
                        "PalletTown_Text_Trigger0_0": "C",
                        "PalletTown_Text_Sign0_0": "D",
                        "PalletTown_Text_MapScript1_0": "E",
                        "PalletTown_Text_MapScript1_1": "F",
                        "PalletTown_Text_MapScript1_2": "G",
                    }
                },
            )
            recipe["maps"] = {"pallet_town": "3.0"}
            with self.assertRaisesRegex(ConfigError, "its group and number"):
                extract.KINDS["gba_gen3_map_text"](paths, game, stack, recipe, roms)


if __name__ == "__main__":
    unittest.main()
