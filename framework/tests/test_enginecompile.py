import unittest

from kaleido import enginecompile
from kaleido.games import Game


class DefineSetsTest(unittest.TestCase):
    def test_the_baseline_first_and_each_distinct_set_once(self) -> None:
        game_list = [
            Game("red", "Red", {"KALEIDO_SAVE_MAGIC": "0x1"}),
            Game("plain", "Plain", {}),
            Game("blue", "Blue", {"KALEIDO_SAVE_MAGIC": "0x1"}),
            Game("green", "Green", {"KALEIDO_SAVE_MAGIC": "0x2"}),
        ]
        self.assertEqual(
            enginecompile.define_sets(game_list),
            [
                (["baseline", "plain"], {}),
                (["red", "blue"], {"KALEIDO_SAVE_MAGIC": "0x1"}),
                (["green"], {"KALEIDO_SAVE_MAGIC": "0x2"}),
            ],
        )


if __name__ == "__main__":
    unittest.main()
