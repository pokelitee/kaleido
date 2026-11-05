import json
import sys
import tempfile
import unittest
from pathlib import Path

from kaleido import validate
from kaleido.config import Paths
from kaleido.games import Game


def put(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


class ValidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.tree = Path(self._temp.name) / "tree"
        put(self.tree / "generated/zones.txt", "# Zones\nZONE_A = 0\nZONE_B\nZONE_NO_EVENTS\n")
        put(self.tree / "generated/encounters.txt", "# Tables\nENCOUNTERS_A = 0\nENCOUNTERS_LOST\n")
        put(self.tree / "generated/species.txt", "# Species\nSPECIES_NONE = 0\nSPECIES_PIDGEY\n")
        put(self.tree / "res/field/events/events.schema.json", {})
        put(self.tree / "res/field/events/order.json", [])
        put(self.tree / "res/field/events/b.json", {"warps": [{"zone": "ZONE_A", "warp": 0}]})
        put(self.tree / "res/field/zones/a.json", {"encounters": "ENCOUNTERS_A"})
        put(self.tree / "res/field/zones/b.json", {"encounters": None})
        put(
            self.tree / "res/field/encounters/a.json",
            {
                "all_year": {
                    "rates": {"grass": 7},
                    "grass": [["SPECIES_PIDGEY", 2, 3]],
                    "surf": {"black2": [["SPECIES_PIDGEY", 5, 5]], "white2": []},
                }
            },
        )

    def tearDown(self) -> None:
        self._temp.cleanup()

    def warps(self, *warps: dict) -> None:
        put(self.tree / "res/field/events/a.json", {"warps": list(warps)})

    def test_upstream_shaped_data_has_no_problems(self) -> None:
        self.warps({"zone": "ZONE_B", "warp": 0}, {"zone": 0xFFFF, "warp": 0})
        self.assertEqual(
            validate.check_warps(self.tree)
            + validate.check_zone_encounters(self.tree)
            + validate.check_encounter_tables(self.tree),
            [],
        )

    def test_a_warp_needs_a_zone_with_that_warp(self) -> None:
        self.warps(
            {"zone": "ZONE_B", "warp": 1}, {"zone": "ZONE_GONE", "warp": 0}, {"zone": "ZONE_NO_EVENTS", "warp": 0}
        )
        problems = validate.check_warps(self.tree)
        self.assertEqual(
            [(p.field, p.message.split(":")[0]) for p in problems],
            [
                ("warps[0].warp", "ZONE_B has warps 0 to 0, not 1"),
                ("warps[1].zone", "'ZONE_GONE' isn't a zone of generated/zones.txt"),
                ("warps[2].zone", "ZONE_NO_EVENTS has no events file, so no warps"),
            ],
        )

    def test_events_name_scripts_their_zones_file_has(self) -> None:
        put(self.tree / "res/field/zones/a.json", {"scripts": "SCRIPTS_A"})
        put(self.tree / "res/field/scripts/a.s", '#include "x"\n    ScriptEntry Script_1\n    ScriptEntry Script_2\n')
        events = {
            "npcs": [{"script": 2}, {"script": 3}, {"script": 2100}],
            "bg_events": [{"script": 0}, {"script": 5}],
            "triggers": [{"script": 1}],
            "init_scripts": [{"type": 2, "script": 4}, {"type": 1, "conditions": [{"var": 1, "value": 0, "script": 6}]}],
        }
        put(self.tree / "res/field/events/a.json", events)
        self.assertEqual(
            [(p.field, p.message) for p in validate.check_event_scripts(self.tree)],
            [
                ("npcs[1].script", "res/field/scripts/a.s has scripts 1 to 2, not 3"),
                ("bg_events[1].script", "res/field/scripts/a.s has scripts 1 to 2, not 5"),
                ("init_scripts[0].script", "res/field/scripts/a.s has scripts 1 to 2, not 4"),
                ("init_scripts[1].conditions[0].script", "res/field/scripts/a.s has scripts 1 to 2, not 6"),
            ],
        )

    def test_a_zones_encounter_table_must_exist(self) -> None:
        put(self.tree / "res/field/zones/c.json", {"encounters": "ENCOUNTERS_LOST"})
        put(self.tree / "res/field/zones/d.json", {"encounters": "ENCOUNTERS_UNKNOWN"})
        messages = [p.message for p in validate.check_zone_encounters(self.tree)]
        self.assertEqual(
            messages,
            [
                "ENCOUNTERS_LOST has no file in res/field/encounters/",
                "ENCOUNTERS_UNKNOWN isn't in generated/encounters.txt",
            ],
        )

    def test_slots_name_species_and_sane_levels(self) -> None:
        put(
            self.tree / "res/field/encounters/a.json",
            {
                "all_year": {
                    "grass": [["SPECIES_MISSINGNO", 2, 3], ["SPECIES_PIDGEY", 5, 4]],
                    "surf": {"black2": [["SPECIES_PIDGEY", 0, 101]], "white2": []},
                }
            },
        )
        fields = [p.field for p in validate.check_encounter_tables(self.tree)]
        self.assertEqual(fields, ["all_year.grass[0]", "all_year.grass[1]", "all_year.surf[0]"])

    def test_region_zones_must_exist(self) -> None:
        root = Path(self._temp.name) / "kaleido"
        put(root / "content/regions/r/layer.json", {"kind": "region"})
        put(root / "content/regions/r/zones.json", {"locations": {"route_1": "ZONE_A", "route_2": "ZONE_Z"}})
        game = Game("g", "G", {}, ("regions/r",), ())
        problems = validate.check_region_zones(Paths(root), game, self.tree)
        self.assertEqual([p.field for p in problems], ["locations.route_2"])

    def test_merged_json_is_checked_against_the_schema_it_names(self) -> None:
        put(self.tree / "res/field/encounters/encounters.schema.json", {"required": ["all_year"]})
        put(self.tree / "res/field/encounters/good.json", {"$schema": "encounters.schema.json", "all_year": {}})
        put(self.tree / "res/field/encounters/bad.json", {"$schema": "encounters.schema.json"})
        put(self.tree / "res/field/encounters/lost.json", {"$schema": "../nowhere.schema.json"})
        put(self.tree / "res/field/encounters/bare.json", {"all_year": {}})
        put(self.tree / "res/text/system/t.txt", "T_Text = one\n")
        checked = []

        def schema_check(data, schema):
            checked.append(data)
            return None if all(key in data for key in schema["required"]) else "all_year is missing"

        files = [f"res/field/encounters/{name}.json" for name in ("good", "bad", "lost", "bare")]
        result = validate.check_schemas(self.tree, [*files, "res/text/system/t.txt"], schema_check)
        self.assertEqual(len(checked), 2)
        self.assertEqual(
            result.problems,
            [validate.Problem("res/field/encounters/bad.json", "encounters.schema.json", "all_year is missing")],
        )
        self.assertEqual(result.unchecked, ["res/field/encounters/bare.json", "res/field/encounters/lost.json"])

    def test_the_schema_check_is_pokebw2s_own_from_the_tree(self) -> None:
        # A stand-in for pokebw2's tools/data/datajson.py, with the two names Kaleido uses
        put(self.tree / "tools/__init__.py", "")
        put(self.tree / "tools/data/__init__.py", "")
        put(
            self.tree / "tools/data/datajson.py",
            "class DataError(Exception):\n    pass\n\n\n"
            "def validate(data, schema, where):\n"
            "    if data != schema['const']:\n        raise DataError(f'{data} is not {schema[\"const\"]}')\n",
        )
        try:
            check = validate.upstream_schema_check(self.tree)
            self.assertIsNone(check(1, {"const": 1}))
            self.assertEqual(check(2, {"const": 1}), "2 is not 1")
            self.assertNotIn(str(self.tree), sys.path)
        finally:
            for name in ("tools.data.datajson", "tools.data", "tools"):
                sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
