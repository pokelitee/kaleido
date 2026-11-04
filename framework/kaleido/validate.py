"""kaleido validate <game>: checks the cross-references of a game's merged tree before it builds (03-architecture.md §7).
Upstream's packers check each file against its schema; these checks span files, so a layer that breaks a reference
fails here, naming the file, the field, and the layers that wrote the file.

So far: warps lead to a zone that has the target warp; zone headers name encounter tables that exist; encounter slots
name species and sane levels; regions map their locations to zones that exist."""
import json
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from kaleido import layers as layer_module
from kaleido import merge
from kaleido.config import Paths
from kaleido.games import Game

# A warp whose zone is 0xffff leads nowhere; Black 2's events have five
NO_ZONE = 0xFFFF
SEASONS = ("all_year", "spring", "summer", "autumn", "winter")
MAX_LEVEL = 100

say = partial(print, flush=True)


@dataclass(frozen=True)
class Problem:
    file: str
    field: str
    message: str


def constants(tree: Path, list_name: str) -> set[str]:
    text = (tree / "generated" / f"{list_name}.txt").read_text(encoding="utf-8")
    return {line.split()[0] for line in text.splitlines() if line and not line.startswith("#")}


def _data_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.json")
                  if not path.name.endswith(".schema.json") and path.name != "order.json")


def _file_name(constant: str, prefix: str) -> str:
    return constant.removeprefix(prefix).lower() + ".json"


def check_warps(tree: Path) -> list[Problem]:
    zones = constants(tree, "zones")
    events_dir = tree / "res" / "field" / "events"
    files = {path.name: path for path in _data_files(events_dir)}
    warp_counts = {name: len(json.loads(path.read_text(encoding="utf-8")).get("warps", []))
                   for name, path in files.items()}
    problems = []
    for name, path in files.items():
        for i, warp in enumerate(json.loads(path.read_text(encoding="utf-8")).get("warps", [])):
            file, field, zone = f"res/field/events/{name}", f"warps[{i}]", warp.get("zone")
            if zone == NO_ZONE:
                continue
            if not isinstance(zone, str) or zone not in zones:
                problems.append(Problem(file, f"{field}.zone", f"{zone!r} isn't a zone of generated/zones.txt"))
                continue
            target = _file_name(zone, "ZONE_")
            if target not in warp_counts:
                problems.append(Problem(file, f"{field}.zone", f"{zone} has no events file, so no warps"))
            elif not 0 <= warp.get("warp", -1) < warp_counts[target]:
                problems.append(Problem(file, f"{field}.warp", f"{zone} has warps 0 to {warp_counts[target] - 1}, "
                                                               f"not {warp.get('warp')}"))
    return problems


def check_zone_encounters(tree: Path) -> list[Problem]:
    tables = constants(tree, "encounters")
    problems = []
    for path in _data_files(tree / "res" / "field" / "zones"):
        table = json.loads(path.read_text(encoding="utf-8")).get("encounters")
        if table is None:
            continue
        file = f"res/field/zones/{path.name}"
        if table not in tables:
            problems.append(Problem(file, "encounters", f"{table} isn't in generated/encounters.txt"))
        elif not (tree / "res" / "field" / "encounters" / _file_name(table, "ENCOUNTERS_")).exists():
            problems.append(Problem(file, "encounters", f"{table} has no file in res/field/encounters/"))
    return problems


def _slots(group) -> list:
    """A group's slots; a group that differs between the versions is { "black2": [...], "white2": [...] }."""
    if isinstance(group, dict):
        return [slot for variant in group.values() for slot in variant]
    return group


def check_encounter_tables(tree: Path) -> list[Problem]:
    species = constants(tree, "species")
    problems = []
    for path in _data_files(tree / "res" / "field" / "encounters"):
        data, file = json.loads(path.read_text(encoding="utf-8")), f"res/field/encounters/{path.name}"
        for season in SEASONS:
            for group, slots in data.get(season, {}).items():
                if group == "rates":
                    continue
                for i, slot in enumerate(_slots(slots)):
                    field = f"{season}.{group}[{i}]"
                    name, low, high = slot[0], slot[1], slot[2]
                    if name not in species:
                        problems.append(Problem(file, field, f"{name!r} isn't a species of generated/species.txt"))
                    if not 1 <= low <= high <= MAX_LEVEL:
                        problems.append(Problem(file, field, f"levels {low} to {high}: need 1 <= min <= max <= 100"))
    return problems


def check_region_zones(paths: Paths, game: Game, tree: Path) -> list[Problem]:
    zones = constants(tree, "zones")
    return [Problem(f"content/{layer.id}/zones.json", f"locations.{location}", f"{zone} isn't a zone")
            for layer in layer_module.load_stack(paths, list(game.layers))
            for location, zone in sorted(layer.zones.items()) if zone not in zones]


def run(paths: Paths, game: Game, tree: Path) -> list[Problem]:
    return [*check_region_zones(paths, game, tree), *check_warps(tree), *check_zone_encounters(tree),
            *check_encounter_tables(tree)]


def report(paths: Paths, game: Game, problems: list[Problem]) -> None:
    merged = merge.report_path(paths, game)
    files = json.loads(merged.read_text(encoding="utf-8"))["files"] if merged.exists() else {}
    for problem in problems:
        writers = ", ".join(part["layer"] for part in files.get(problem.file, [])) or "upstream"
        say(f"{problem.file} ({writers}) {problem.field}: {problem.message}")
    say(f"{game.id}: {len(problems)} problems" if problems else f"{game.id}: no problems")
