import json
import tempfile
import unittest
from pathlib import Path

from kaleido import extract, merge
from kaleido.config import ConfigError, Paths
from kaleido.games import Game
from tests.support import git

UPSTREAM = {
    "res/data/a.json": {"name": "a", "stats": {"hp": 1, "attack": 2}, "list": [1, 2]},
    "res/text/system/t.txt": "T_Text_One = one\nT_Text_Two = two\n",
    "generated/things.txt": "# Things\nTHING_A = 0\nTHING_B\n",
}


class MergeRulesTest(unittest.TestCase):
    def test_merge_patch_follows_rfc_7396(self) -> None:
        target = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2]}
        patch = {"a": None, "b": {"c": 9}, "e": [3], "f": {"g": 1}}
        self.assertEqual(merge.merge_patch(target, patch), {"b": {"c": 9, "d": 3}, "e": [3], "f": {"g": 1}})
        self.assertEqual(target["a"], 1)

    def test_messages_are_overridden_by_label(self) -> None:
        text = merge.override_messages(UPSTREAM["res/text/system/t.txt"], {"T_Text_Two": "zwei"}, "here")
        self.assertEqual(text, "T_Text_One = one\nT_Text_Two = zwei\n")
        with self.assertRaisesRegex(ConfigError, "0 messages labelled T_Text_Three"):
            merge.override_messages(text, {"T_Text_Three": "x"}, "here")

    def test_constants_are_appended_once(self) -> None:
        self.assertEqual(
            merge.append_constants(UPSTREAM["generated/things.txt"], "# mine\nTHING_C\n", "here"),
            "# Things\nTHING_A = 0\nTHING_B\nTHING_C\n",
        )
        with self.assertRaisesRegex(ConfigError, "already in the list"):
            merge.append_constants(UPSTREAM["generated/things.txt"], "THING_B\n", "here")
        with self.assertRaisesRegex(ConfigError, "isn't a constant name"):
            merge.append_constants(UPSTREAM["generated/things.txt"], "THING_D = 5\n", "here")


class MergeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.paths = Paths(Path(self._temp.name) / "kaleido")
        self.worktree = self.paths.root / "build" / "g" / "engine"
        self.worktree.mkdir(parents=True)
        git("init", "-q", cwd=self.worktree)
        for path, data in UPSTREAM.items():
            self.put(self.worktree / path, data)
        git("add", "-A", cwd=self.worktree)
        git("commit", "-q", "-m", "upstream", cwd=self.worktree)
        self.layer("regions/r", "region", {})
        self.layer(
            "games/g",
            "game",
            {
                "res/data/a.json.merge.json": {"stats": {"hp": 5}},
                "res/text/system/t.txt.merge.json": {"T_Text_One": "uno"},
                "generated/things.txt": "THING_C\n",
                "res/data/new.json": {"new": True},
            },
        )
        self.game = Game("g", "G", {}, ("regions/r", "games/g"), ())

    def tearDown(self) -> None:
        self._temp.cleanup()

    @staticmethod
    def put(path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")

    def layer(self, layer_id: str, kind: str, files: dict) -> None:
        root = self.paths.root / "content" / layer_id
        self.put(root / "layer.json", {"kind": kind})
        self.put(root / "provenance.json", {"entries": [{"paths": ["res/*", "generated/*"], "category": "original"}]})
        for path, data in files.items():
            self.put(root / path, data)

    def run_merge(self) -> tuple[int, int]:
        planned = merge.plan(self.paths, self.game, self.worktree, [])
        return merge.write(self.paths, self.game, self.worktree, planned)

    def read(self, path: str) -> str:
        return (self.worktree / path).read_text(encoding="utf-8")

    def test_lays_every_kind_of_file_into_the_worktree(self) -> None:
        self.assertEqual(self.run_merge(), (4, 0))
        self.assertEqual(json.loads(self.read("res/data/a.json"))["stats"], {"hp": 5, "attack": 2})
        self.assertIn("T_Text_One = uno\n", self.read("res/text/system/t.txt"))
        self.assertTrue(self.read("generated/things.txt").endswith("THING_B\nTHING_C\n"))
        self.assertEqual(json.loads(self.read("res/data/new.json")), {"new": True})
        report = json.loads(merge.report_path(self.paths, self.game).read_text())
        self.assertEqual(
            report["files"]["res/data/a.json"], [{"layer": "games/g", "category": "original", "how": "merge"}]
        )

    def test_a_second_merge_writes_nothing(self) -> None:
        self.run_merge()
        self.assertEqual(self.run_merge(), (0, 0))

    def test_patches_apply_to_upstream_not_to_earlier_output(self) -> None:
        self.run_merge()
        self.put(self.paths.root / "content/games/g/res/text/system/t.txt.merge.json", {"T_Text_Two": "dos"})
        self.run_merge()
        self.assertEqual(self.read("res/text/system/t.txt"), "T_Text_One = one\nT_Text_Two = dos\n")

    def test_files_a_layer_no_longer_has_go_back_to_upstream(self) -> None:
        self.run_merge()
        (self.paths.root / "content/games/g/res/data/a.json.merge.json").unlink()
        (self.paths.root / "content/games/g/res/data/new.json").unlink()
        self.assertEqual(self.run_merge(), (0, 2))
        self.assertEqual(json.loads(self.read("res/data/a.json")), UPSTREAM["res/data/a.json"])
        self.assertFalse((self.worktree / "res/data/new.json").exists())

    def test_higher_layers_patch_what_lower_ones_made(self) -> None:
        self.put(self.paths.root / "content/regions/r/res/data/a.json.merge.json", {"name": "region"})
        self.run_merge()
        merged = json.loads(self.read("res/data/a.json"))
        self.assertEqual((merged["name"], merged["stats"]["hp"]), ("region", 5))

    def test_one_layer_changes_a_file_once(self) -> None:
        self.put(self.paths.root / "content/games/g/res/data/a.json", {"name": "whole"})
        with self.assertRaisesRegex(ConfigError, "both change res/data/a.json"):
            merge.plan(self.paths, self.game, self.worktree, [])

    def test_a_patch_needs_a_file_below_it(self) -> None:
        self.put(self.paths.root / "content/games/g/res/data/missing.json.merge.json", {"x": 1})
        with self.assertRaisesRegex(ConfigError, "no res/data/missing.json below it"):
            merge.plan(self.paths, self.game, self.worktree, [])

    def test_extracted_files_join_their_layer(self) -> None:
        output = extract.directory(self.paths, self.game) / "regions/r/res/data/extracted.json"
        self.put(output, {"from": "rom"})
        items = [extract.Extracted("regions/r", "res/data/extracted.json", "extract/x.json")]
        planned = merge.plan(self.paths, self.game, self.worktree, items)
        self.assertEqual(planned.parts["res/data/extracted.json"][0].category, "extracted")


if __name__ == "__main__":
    unittest.main()
