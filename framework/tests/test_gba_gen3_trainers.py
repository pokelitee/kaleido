import json
import struct
import tempfile
import unittest
from pathlib import Path

from extractors import gba_gen3, gba_gen3_trainers
from extractors.gba_gen3_trainers import Member, Trainer
from kaleido import extract, layers
from kaleido.config import ConfigError, Paths
from kaleido.games import Game
from tests.test_gba_gen3_maps import pointer, synthetic_rom

TABLE, MONEY = 0x900, 0xC00


def record(kind: int, trainer_class: int, party: int, size: int, items=(), double: bool = False) -> bytes:
    data = bytearray(gba_gen3_trainers.TRAINER_SIZE)
    data[0], data[1] = kind, trainer_class
    struct.pack_into("<4H", data, 0x10, *(list(items) + [0] * (4 - len(items))))
    data[0x18], data[0x20] = int(double), size
    data[0x24:0x28] = pointer(party)
    return bytes(data)


def trainer_rom() -> bytes:
    """The maps test's ROM, whose map 0.0 starts a battle with trainer 5, plus made-up trainers 1 to 5 after trainer
    0's empty record, and a prize money table with a shorter one before it."""
    rom = bytearray(synthetic_rom()) + bytearray(0x800)

    def put(offset: int, data: bytes) -> None:
        rom[offset : offset + len(data)] = data

    put(TABLE + 40, record(0, 3, 0xB00, 1))
    put(TABLE + 80, record(gba_gen3_trainers.HELD_ITEMS, 3, 0xB10, 1))
    put(TABLE + 120, record(0, 3, 0xB20, 1, items=(22,)))
    put(TABLE + 160, record(0, 3, 0xB30, 1))
    put(TABLE + 200, record(gba_gen3_trainers.CUSTOM_MOVES, 9, 0xB40, 2, double=True))
    put(0xB00, struct.pack("<HBxH2x", 0, 5, 7))
    put(0xB10, struct.pack("<HBxHH", 0, 5, 1, 13))
    put(0xB20, struct.pack("<HBxH2x", 0, 5, 4))
    put(0xB30, struct.pack("<HBxH2x", 0, 6, 16))
    put(0xB40, struct.pack("<HBxH4H2x", 255, 12, 74, 33, 111, 0, 0) + struct.pack("<HBxH4H2x", 0, 14, 95, 33, 0, 0, 0))
    put(0xBE0, bytes([3, 99, 0, 0, 0xFF, 9, 0, 0]))
    put(MONEY, bytes([3, 7, 0, 0, 9, 30, 0, 0, 0xFF, 5, 0, 0]))
    return bytes(rom)


class TrainersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rom = gba_gen3.Rom(trainer_rom())

    def test_finds_the_trainers_after_trainer_0(self) -> None:
        self.assertEqual(gba_gen3_trainers.trainer_table(self.rom), (TABLE, 6))

    def test_reads_a_trainer_and_its_party(self) -> None:
        self.assertEqual(
            gba_gen3_trainers.trainer(self.rom, 5),
            Trainer(9, (), True, (Member(74, 12, 255, 0, (33, 111)), Member(95, 14, 0, 0, (33,)))),
        )
        self.assertEqual(gba_gen3_trainers.trainer(self.rom, 2).party, (Member(1, 5, 0, 13, ()),))
        self.assertEqual(gba_gen3_trainers.trainer(self.rom, 3).items, (22,))
        with self.assertRaisesRegex(gba_gen3.ExtractError, "no trainer 6"):
            gba_gen3_trainers.trainer(self.rom, 6)

    def test_prize_money_is_the_class_multiplier_doubled_for_a_double_battle(self) -> None:
        self.assertEqual(gba_gen3_trainers.money_table(self.rom), ({3: 7, 9: 30}, 5))
        self.assertEqual(gba_gen3_trainers.prize_multiplier(self.rom, gba_gen3_trainers.trainer(self.rom, 5)), 60)
        self.assertEqual(gba_gen3_trainers.prize_multiplier(self.rom, Trainer(40, (), False, ())), 5)


class TrainerRecipeTest(unittest.TestCase):
    def test_patches_the_gen_5_trainer_with_the_source_party_lines_and_prize(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = Paths(Path(temp))
            generated = paths.engine / "generated"
            generated.mkdir(parents=True)
            (generated / "species.txt").write_text("".join(f"SPECIES_{i}\n" for i in range(252)))
            (generated / "moves.txt").write_text("".join(f"MOVE_{i}\n" for i in range(355)))
            (generated / "trainers.txt").write_text("TRAINER_NONE = 0\nTRAINER_RIVAL\n")
            region = paths.root / "content/regions/r"
            region.mkdir(parents=True)
            (region / "layer.json").write_text('{"kind": "region"}')
            (region / "zones.json").write_text('{"locations": {}}')
            stack = layers.load_stack(paths, ["regions/r"])
            game = Game("g", "G", {}, ("regions/r",), ("firered",))
            roms = {"firered": gba_gen3.Rom(trainer_rom())}

            def run(source: dict, constant: str = "TRAINER_RIVAL") -> list[tuple[str, str]]:
                recipe = {"kind": "gba_gen3_trainers", "source": "firered", "trainers": {constant: source}}
                return extract.KINDS["gba_gen3_trainers"](paths, game, stack, recipe, roms)

            [(path, content)] = run({"trainer": 5, "map": [0, 0]})
            self.assertEqual(path, "res/trainers/data/rival.json.merge.json")
            member = {"form": 0, "gender": 0, "ability": 0}
            self.assertEqual(
                json.loads(content),
                {
                    "battle_style": "BTL_STYLE_DOUBLE",
                    "money": 60,
                    "party": [
                        {"species": "SPECIES_74", "level": 12, "difficulty": 255, "moves": ["MOVE_33", "MOVE_111"]}
                        | member,
                        {"species": "SPECIES_95", "level": 14, "difficulty": 0, "moves": ["MOVE_33"]} | member,
                    ],
                    "messages": [{"type": "TRMSG_START", "text": "E"}, {"type": "TRMSG_LOSE", "text": "F"}],
                },
            )
            for source, error in (
                ({"trainer": 1, "map": [0, 0]}, "no script of map"),
                ({"trainer": 2, "map": [0, 0]}, "held item"),
                ({"trainer": 3, "map": [0, 0]}, "uses items"),
                ({"trainer": 5}, "a map is its group and number"),
            ):
                with self.subTest(source=source), self.assertRaisesRegex(ConfigError, error):
                    run(source)
            with self.assertRaisesRegex(ConfigError, "isn't a trainer"):
                run({"trainer": 5, "map": [0, 0]}, "TRAINER_NOBODY")


if __name__ == "__main__":
    unittest.main()
