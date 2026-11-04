import unittest

from kaleido import enginecompile


class DefineSetsTest(unittest.TestCase):
    def test_the_baseline_first_and_each_distinct_set_once(self) -> None:
        game_defines = [
            ("red", {"KALEIDO_SAVE_MAGIC": "0x1"}),
            ("plain", {}),
            ("blue", {"KALEIDO_SAVE_MAGIC": "0x1"}),
            ("green", {"KALEIDO_SAVE_MAGIC": "0x2"}),
        ]
        self.assertEqual(
            enginecompile.define_sets(game_defines),
            [
                (["baseline", "plain"], {}),
                (["red", "blue"], {"KALEIDO_SAVE_MAGIC": "0x1"}),
                (["green"], {"KALEIDO_SAVE_MAGIC": "0x2"}),
            ],
        )


if __name__ == "__main__":
    unittest.main()
