import json
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
        put(self.tree / "res/field/encounters/a.json", {"all_year": {
            "rates": {"grass": 7}, "grass": [["SPECIES_PIDGEY", 2, 3]],
            "surf": {"black2": [["SPECIES_PIDGEY", 5, 5]], "white2": []}}})

    def tearDown(self) -> None:
        self._temp.cleanup()

    def warps(self, *warps: dict) -> None:
        put(self.tree / "res/field/events/a.json", {"warps": list(warps)})

    def test_upstream_shaped_data_has_no_problems(self) -> None:
        self.warps({"zone": "ZONE_B", "warp": 0}, {"zone": 0xFFFF, "warp": 0})
        self.assertEqual(validate.check_warps(self.tree) + validate.check_zone_encounters(self.tree)
                         + validate.check_encounter_tables(self.tree), [])

    def test_a_warp_needs_a_zone_with_that_warp(self) -> None:
        self.warps({"zone": "ZONE_B", "warp": 1}, {"zone": "ZONE_GONE", "warp": 0},
                   {"zone": "ZONE_NO_EVENTS", "warp": 0})
        problems = validate.check_warps(self.tree)
        self.assertEqual([(p.field, p.message.split(":")[0]) for p in problems], [
            ("warps[0].warp", "ZONE_B has warps 0 to 0, not 1"),
            ("warps[1].zone", "'ZONE_GONE' isn't a zone of generated/zones.txt"),
            ("warps[2].zone", "ZONE_NO_EVENTS has no events file, so no warps"),
        ])

    def test_a_zones_encounter_table_must_exist(self) -> None:
        put(self.tree / "res/field/zones/c.json", {"encounters": "ENCOUNTERS_LOST"})
        put(self.tree / "res/field/zones/d.json", {"encounters": "ENCOUNTERS_UNKNOWN"})
        messages = [p.message for p in validate.check_zone_encounters(self.tree)]
        self.assertEqual(messages, ["ENCOUNTERS_LOST has no file in res/field/encounters/",
                                    "ENCOUNTERS_UNKNOWN isn't in generated/encounters.txt"])

    def test_slots_name_species_and_sane_levels(self) -> None:
        put(self.tree / "res/field/encounters/a.json", {"all_year": {
            "grass": [["SPECIES_MISSINGNO", 2, 3], ["SPECIES_PIDGEY", 5, 4]],
            "surf": {"black2": [["SPECIES_PIDGEY", 0, 101]], "white2": []}}})
        fields = [p.field for p in validate.check_encounter_tables(self.tree)]
        self.assertEqual(fields, ["all_year.grass[0]", "all_year.grass[1]", "all_year.surf[0]"])

    def test_region_zones_must_exist(self) -> None:
        root = Path(self._temp.name) / "kaleido"
        put(root / "content/regions/r/layer.json", {"kind": "region"})
        put(root / "content/regions/r/zones.json", {"locations": {"route_1": "ZONE_A", "route_2": "ZONE_Z"}})
        game = Game("g", "G", {}, ("regions/r",), ())
        problems = validate.check_region_zones(Paths(root), game, self.tree)
        self.assertEqual([p.field for p in problems], ["locations.route_2"])


if __name__ == "__main__":
    unittest.main()
