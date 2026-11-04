import json
import tempfile
import unittest
from pathlib import Path

from kaleido import games
from kaleido.config import ConfigError, Paths


class GamesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name))

    def tearDown(self) -> None:
        self._temp.cleanup()

    def add(self, game_id: str, config: dict, paths: Paths | None = None) -> None:
        path = games.directory(paths or self.paths) / game_id / "game.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(config), encoding="utf-8")

    def test_loads_a_game(self) -> None:
        self.add("test_game", {"name": "Test", "defines": {"KALEIDO_SAVE_MAGIC": "0x54455354", "KALEIDO_X": ""}})
        game = games.load(self.paths, "test_game")
        self.assertEqual((game.name, game.defines["KALEIDO_X"]), ("Test", ""))

    def test_a_title_is_up_to_three_plain_lines(self) -> None:
        magic = {"KALEIDO_SAVE_MAGIC": "0x54455354"}
        self.add("titled", {"name": "Titled", "defines": magic, "title": ["Kaleido", "Test"]})
        self.assertEqual(games.load(self.paths, "titled").title, ("Kaleido", "Test"))
        for i, title in enumerate((["a", "b", "c", "d"], ["a\\nb"], [""], "Kaleido", ["x" * 129])):
            paths = Paths(Path(self._temp.name) / f"bad{i}")
            self.add("bad", {"name": "Bad", "defines": magic, "title": title}, paths)
            with self.assertRaisesRegex(ConfigError, "DS menu's title"):
                games.load_all(paths)

    def test_a_start_location_becomes_the_new_game_zone(self) -> None:
        content = self.paths.root / "content"
        (content / "regions/r").mkdir(parents=True)
        (content / "regions/r/layer.json").write_text('{"kind": "region"}', encoding="utf-8")
        (content / "regions/r/zones.json").write_text('{"locations": {"home": "ZONE_A_2"}}', encoding="utf-8")
        magic = {"KALEIDO_SAVE_MAGIC": "0x54455354"}
        self.add("started", {"name": "S", "defines": magic, "layers": ["regions/r"], "start": "home"})
        game = games.load(self.paths, "started")
        self.assertEqual(games.build_defines(self.paths, game), {**magic, "KALEIDO_NEW_GAME_ZONE": "ZONE_A_2"})
        unmapped = games.Game("g", "G", magic, ("regions/r",), start="nowhere")
        with self.assertRaisesRegex(ConfigError, "'nowhere'"):
            games.build_defines(self.paths, unmapped)
        both = Paths(Path(self._temp.name) / "both")
        self.add("both", {"name": "B", "defines": {**magic, "KALEIDO_NEW_GAME_ZONE": "ZONE_A"}, "start": "home"}, both)
        with self.assertRaisesRegex(ConfigError, "don't define it as well"):
            games.load_all(both)

    def test_names_unknown_games(self) -> None:
        self.add("one", {"name": "One", "defines": {"KALEIDO_SAVE_MAGIC": "0x1"}})
        with self.assertRaisesRegex(ConfigError, r"no game 'two'.*games: one"):
            games.load(self.paths, "two")

    def test_defines_are_kaleido_names_with_string_values(self) -> None:
        self.add("bad_name", {"name": "Bad", "defines": {"BUGFIX": ""}})
        with self.assertRaisesRegex(ConfigError, "isn't a KALEIDO_"):
            games.load_all(self.paths)

    def test_a_define_value_is_a_string(self) -> None:
        self.add("bad_value", {"name": "Bad", "defines": {"KALEIDO_SAVE_MAGIC": 1}})
        with self.assertRaisesRegex(ConfigError, "must be a string"):
            games.load_all(self.paths)

    def test_every_game_needs_a_save_magic(self) -> None:
        self.add("none", {"name": "None", "defines": {}})
        with self.assertRaisesRegex(ConfigError, "needs its own KALEIDO_SAVE_MAGIC"):
            games.load_all(self.paths)

    def test_black2s_magics_and_blank_cards_are_reserved(self) -> None:
        for magic in ("0x31053527", "0xa10f49ae", "0", "0xffffffff"):
            with self.subTest(magic=magic), tempfile.TemporaryDirectory() as temp:
                paths = Paths(Path(temp))
                self.add("game", {"name": "Game", "defines": {"KALEIDO_SAVE_MAGIC": magic}}, paths)
                with self.assertRaisesRegex(ConfigError, "magic"):
                    games.load_all(paths)

    def test_two_games_never_share_a_magic(self) -> None:
        self.add("one", {"name": "One", "defines": {"KALEIDO_SAVE_MAGIC": "0x10"}})
        self.add("two", {"name": "Two", "defines": {"KALEIDO_SAVE_MAGIC": "16"}})
        with self.assertRaisesRegex(ConfigError, "also one's"):
            games.load_all(self.paths)

    def test_the_repository_games_load(self) -> None:
        loaded = games.load_all(Paths(Path(__file__).resolve().parents[2]))
        self.assertIn("firered", [game.id for game in loaded])


if __name__ == "__main__":
    unittest.main()
