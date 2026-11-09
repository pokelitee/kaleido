import tempfile
import unittest
from pathlib import Path

from kaleido import play

WORKS = 431


class FakeMemory:
    """Little-endian memory with the harness's accessors' code at made-up addresses, and the game's structures."""

    def __init__(self) -> None:
        self.bytes: dict[int, int] = {}
        self.symbols = {"g_GameSystem": 0x02100000}
        address = 0x02000100
        for name, (code, _, _) in {**play.ACCESSORS, **play.FIELD_ACCESSORS}.items():
            self.symbols[name] = address | 1
            for i, half in enumerate(code):
                self.put(address + 2 * i, half, 2)
            address += 0x20

    def put(self, address: int, value: int, size: int) -> None:
        for i in range(size):
            self.bytes[address + i] = (value >> (8 * i)) & 0xFF

    def get(self, address: int, size: int) -> int:
        return sum(self.bytes.get(address + i, 0) << (8 * i) for i in range(size))

    def memory(self) -> play.Memory:
        def s16(address: int) -> int:
            value = self.get(address, 2)
            return value - 0x10000 if value & 0x8000 else value

        return play.Memory(lambda a: self.get(a, 1), lambda a: self.get(a, 2), lambda a: self.get(a, 4), s16)

    def start_field(self, hidden: bool = False, event: bool = False) -> None:
        gsys, game_data, field, player, core, actor, work = (0x02200000 + 0x1000 * i for i in range(7))
        self.put(self.symbols["g_GameSystem"], gsys, 4)
        self.put(gsys + 0x18, 0x02300000 if event else 0, 4)
        self.put(gsys + 0x1C, game_data, 4)
        self.put(gsys + 0x20, field, 4)
        self.put(game_data + 0x114, 427, 2)
        self.put(game_data + 0x1AC, work, 4)
        self.put(field + 0x94, player, 4)
        self.put(player + 0x4, core, 4)
        self.put(core + 0x1C, actor, 4)
        self.put(actor, 0x27 if hidden else 0x23, 4)
        self.put(actor + 0x3C, 42, 2)
        self.put(actor + 0x40, 750, 2)
        self.work = work


NAMES = {
    "zones": {"ZONE_ASPERTIA_CITY": 427, "KANTO_VAR_STORY": 0x404E},
    "flags": {"EVENT_FLAG_0x01f2": 0x1F2, "KANTO_FLAG_GOT_POTION": 0x1F5},
    "vars": {"EVENT_WORK_0x404e": 0x404E, "KANTO_VAR_STORY": 0x404E, "KANTO_STORY_HAS_STARTER": 2},
}


class StateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = FakeMemory()
        self.state = play.GameState(self.fake.memory(), self.fake.symbols, WORKS)

    def test_reads_nothing_before_the_game_system_exists(self) -> None:
        self.assertFalse(self.state.field())
        self.assertIsNone(self.state.zone())
        self.assertIsNone(self.state.tile())
        self.assertIsNone(self.state.flag(0x1F2))

    def test_reads_the_field_the_player_and_the_event_work(self) -> None:
        self.fake.start_field()
        self.fake.put(self.fake.work + 2 * 0x4E, 3, 2)
        self.fake.put(self.fake.work + WORKS * 2 + 0x1F2 // 8, 1 << (0x1F2 % 8), 1)
        self.assertTrue(self.state.field())
        self.assertEqual(self.state.zone(), 427)
        self.assertEqual(self.state.tile(), (42, 750))
        self.assertTrue(self.state.player_visible())
        self.assertEqual(self.state.var(0x404E), 3)
        self.assertTrue(self.state.flag(0x1F2))
        self.assertFalse(self.state.flag(0x1F3))

    def test_an_event_or_a_hidden_player(self) -> None:
        self.fake.start_field(hidden=True, event=True)
        self.assertFalse(self.state.field())
        self.assertTrue(self.state.event_running())
        self.assertFalse(self.state.player_visible())

    def test_code_that_reads_elsewhere_stops_the_run(self) -> None:
        self.fake.start_field()
        self.fake.put(self.fake.symbols["GetGPosX"] & ~1, 0x2140, 2)
        with self.assertRaisesRegex(play.PlayError, "GetGPosX .* isn't the code that reads FieldActor.gx at 0x3c"):
            self.state.tile()

    def test_conditions(self) -> None:
        self.fake.start_field()
        self.fake.put(self.fake.work + 2 * 0x4E, 2, 2)
        holds = {
            "field": True,
            "not field": False,
            "event": False,
            "zone ZONE_ASPERTIA_CITY": True,
            "zone 428": False,
            "at 42 750": True,
            "player-visible": True,
            "flag KANTO_FLAG_GOT_POTION": False,
            "not flag 0x1f5": True,
            "var KANTO_VAR_STORY >= 2": True,
            "var KANTO_VAR_STORY == KANTO_STORY_HAS_STARTER": True,
            "var EVENT_WORK_0x404e == 3": False,
        }
        for text, expected in holds.items():
            with self.subTest(text):
                self.assertEqual(play.parse_condition(text.split(), "t", NAMES).holds(self.state), expected)


class FakeEmulator:
    """Moves the fake player a tile per `frames_per_tile` frames that a direction is held, unless the tile ahead is a
    wall."""

    def __init__(self, fake: FakeMemory, frames_per_tile: int, walls: set) -> None:
        self.fake, self.frames_per_tile, self.walls = fake, frames_per_tile, walls
        self.held: set[int] = set()
        self.input = self
        self.counter = 0
        self.actor = 0x02200000 + 0x1000 * 5

    def keypad_add_key(self, key: int) -> None:
        self.held.add(key)
        self.counter = 0

    def keypad_rm_key(self, key: int) -> None:
        self.held.discard(key)

    def cycle(self, with_joystick: bool) -> None:
        if not self.held:
            return
        self.counter += 1
        if self.counter < self.frames_per_tile:
            return
        self.counter = 0
        dx, dz = play.DIRECTIONS[play.KEYS[next(iter(self.held))]]
        x, z = self.fake.get(self.actor + 0x3C, 2), self.fake.get(self.actor + 0x40, 2)
        if (x + dx, z + dz) not in self.walls:
            self.fake.put(self.actor + 0x3C, x + dx, 2)
            self.fake.put(self.actor + 0x40, z + dz, 2)

    def screenshot(self):
        return self

    def save(self, path) -> None:
        pass


class WalkTest(unittest.TestCase):
    def player(self, frames_per_tile: int, walls: set = frozenset()) -> play.Player:
        fake = FakeMemory()
        fake.start_field()
        emulator = FakeEmulator(fake, frames_per_tile, walls)
        keys = {key: i for i, key in enumerate(play.KEYS)}
        return play.Player(emulator, keys, play.GameState(fake.memory(), fake.symbols, WORKS), Path("."))

    def test_walks_until_the_tile_has_moved_that_far(self) -> None:
        player = self.player(frames_per_tile=16)
        [step] = play.parse_route("walk LEFT 3")
        player.step(step)
        self.assertEqual(player.state.tile(), (39, 750))

    def test_a_wall_stops_the_walk(self) -> None:
        player = self.player(frames_per_tile=16, walls={(42, 752)})
        [step] = play.parse_route("walk DOWN 3")
        with self.assertRaisesRegex(play.PlayError, r"stopped at \(42, 751\) after 1 of 3 tiles"):
            player.step(step)

    def test_refuses_a_direction_it_doesnt_know(self) -> None:
        with self.assertRaisesRegex(play.PlayError, "walk goes UP DOWN LEFT RIGHT"):
            play.parse_route("walk NORTH 2")


class RouteTest(unittest.TestCase):
    def test_parses_each_step(self) -> None:
        route = (
            "# a comment\n"
            "wait 900, START/120, A*3/60\n"
            "hold LEFT 48\n"
            "repeat A/60 START/60 until field for 120 timeout 600  # the intro\n"
            "until not event\n"
            "check var KANTO_VAR_STORY == 5\n"
            "shot town, save town, load town\n"
        )
        steps = play.parse_route(route, NAMES)
        self.assertEqual(
            [(s.kind, s.line) for s in steps],
            [("wait", 2), ("press", 2), ("press", 2), ("hold", 3), ("repeat", 4), ("until", 5), ("check", 6)]
            + [("shot", 7), ("save", 7), ("load", 7)],
        )
        self.assertEqual(steps[1].args, ("START", 1, 120))
        self.assertEqual(steps[2].args, ("A", 3, 60))
        presses, condition, hold, timeout = steps[4].args
        self.assertEqual(
            (presses, condition.kind, hold, timeout), ((("A", 1, 60), ("START", 1, 60)), "field", 120, 600)
        )
        self.assertEqual(steps[5].args[1:], (1, play.DEFAULT_TIMEOUT))
        self.assertEqual(steps[6].args[0].args, (0x404E, "==", 5))

    def test_refuses_what_it_cant_run(self) -> None:
        for route, message in (
            ("jump", "isn't a step"),
            ("Z*2", "isn't a step"),
            ("repeat until field", "needs presses"),
            ("until sky", "isn't a condition"),
            ("check at 1", "takes 2 arguments"),
            ("check zone ZONE_NOWHERE", "ZONE_NOWHERE isn't a constant"),
            ("check var KANTO_VAR_STORY ~ 1", "isn't a comparison"),
            ("check flag 0x4001", "isn't a saved flag"),
            ("shot ../out", "isn't a step"),
        ):
            with self.subTest(route), self.assertRaisesRegex(play.PlayError, message):
                play.parse_route(route, NAMES)

    def test_without_names_constants_are_left_for_the_run(self) -> None:
        [step] = play.parse_route("check zone ZONE_ANYWHERE")
        self.assertEqual(step.args[0].text, "zone ZONE_ANYWHERE")


class TreeTest(unittest.TestCase):
    def test_reads_symbols_names_and_the_event_work_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tree = Path(temp)
            xmap = tree / "arm9.o.xMAP"
            xmap.write_text(
                "  021410F4 00000004 .bss    g_GameSystem\t(game_system.o)\n"
                "  02016AE8 00000004 .text   GSYS_GetNowEvent\t(game_system.o)\n"
                "  02200000 00000004 .text   GSYS_GetNowEvent\t(other.o)\n",
                encoding="utf-8",
            )
            self.assertEqual(play.read_symbols(xmap), {"g_GameSystem": 0x021410F4, "GSYS_GetNowEvent": 0x02016AE8})
            for list_name, text in (
                ("zones", "ZONE_A = 0\nZONE_B\n"),
                ("flags", "EVENT_FLAG_0x0001 = 0x1\n"),
                ("vars", "EVENT_WORK_0x4000 = 0x4000\n"),
            ):
                (tree / "generated").mkdir(exist_ok=True)
                (tree / "generated" / f"{list_name}.txt").write_text(f"# {list_name}\n{text}", encoding="utf-8")
            scripts = tree / "res" / "field" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "story.inc").write_text(
                "#define KANTO_VAR_STORY 0x404E\n#define KANTO_STORY_IN_LAB 1\n#define B2_FLAG EVENT_FLAG_0x0961\n",
                encoding="utf-8",
            )
            names = play.read_names(tree)
            self.assertEqual(names["zones"]["ZONE_B"], 1)
            self.assertEqual(names["vars"]["KANTO_VAR_STORY"], 0x404E)
            self.assertNotIn("B2_FLAG", names["flags"])
            (tree / "include" / "save").mkdir(parents=True)
            (tree / "include" / "save" / "event_work.h").write_text("#define EVENT_WORK_COUNT 431\n", encoding="utf-8")
            self.assertEqual(play.event_work_count(tree), WORKS)


if __name__ == "__main__":
    unittest.main()
