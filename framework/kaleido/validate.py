"""kaleido validate <game>: checks a game's merged tree before it builds (03-architecture.md §7), so a layer that breaks
something fails here, naming the file, the field, and the layers that wrote the file.

- Each JSON file the layers wrote is checked against the schema its "$schema" names, with pokebw2's own checker
  (tools/data/datajson.py), as the packers check it at build time. That also runs where nothing builds: CI, with
  --no-extract. A file whose "$schema" is missing or names no file is listed as unchecked.
- Cross-references, which span files: warps lead to a zone that has the target warp; events name scripts that their
  zone's script file has; zone headers name encounter tables that exist; encounter slots name species and sane levels;
  regions map their locations to zones that exist."""

import importlib
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
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
GLOBAL_SCRIPTS = 2000
SCRIPT_ENTRY = re.compile(r"^\s*ScriptEntry\s", re.MULTILINE)

say = partial(print, flush=True)


@dataclass(frozen=True)
class Problem:
    file: str
    field: str
    message: str


@dataclass(frozen=True)
class Result:
    problems: list[Problem]
    # JSON files the layers wrote that name no schema to check them against
    unchecked: list[str] = field(default_factory=list)


# Checks data against a schema: None when it fits, else what is wrong
SchemaCheck = Callable[[object, dict], str | None]


def upstream_schema_check(tree: Path) -> SchemaCheck:
    """pokebw2's tools/data/datajson.validate, imported from the tree: its constant lookups ("x-constant") then read
    the tree's merged generated/ lists, as the packers' do."""
    sys.path.insert(0, str(tree))
    try:
        datajson = importlib.import_module("tools.data.datajson")
    finally:
        sys.path.remove(str(tree))

    def check(data: object, schema: dict) -> str | None:
        try:
            datajson.validate(data, schema, "")
        except datajson.DataError as error:
            return str(error)
        return None

    return check


def check_schemas(tree: Path, files: list[str], schema_check: SchemaCheck) -> Result:
    """The JSON files among files (paths in the tree, as the merge report lists them) against the schema each one's
    "$schema" names, relative to the file."""
    problems, unchecked = [], []
    for file in sorted(files):
        if not file.startswith("res/") or not file.endswith(".json") or file.endswith(".schema.json"):
            continue
        path = tree / file
        data = json.loads(path.read_text(encoding="utf-8"))
        ref = data.get("$schema") if isinstance(data, dict) else None
        schema = path.parent / ref if isinstance(ref, str) else None
        if schema is None or not schema.is_file():
            unchecked.append(file)
            continue
        error = schema_check(data, json.loads(schema.read_text(encoding="utf-8")))
        if error:
            problems.append(Problem(file, schema.name, error))
    return Result(problems, unchecked)


def constants(tree: Path, list_name: str) -> set[str]:
    text = (tree / "generated" / f"{list_name}.txt").read_text(encoding="utf-8")
    return {line.split()[0] for line in text.splitlines() if line and not line.startswith("#")}


def _data_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.glob("*.json")
        if not path.name.endswith(".schema.json") and path.name != "order.json"
    )


def _file_name(constant: str, prefix: str) -> str:
    return constant.removeprefix(prefix).lower() + ".json"


def check_warps(tree: Path) -> list[Problem]:
    zones = constants(tree, "zones")
    events_dir = tree / "res" / "field" / "events"
    files = {path.name: path for path in _data_files(events_dir)}
    warp_counts = {
        name: len(json.loads(path.read_text(encoding="utf-8")).get("warps", [])) for name, path in files.items()
    }
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
                problems.append(
                    Problem(
                        file,
                        f"{field}.warp",
                        f"{zone} has warps 0 to {warp_counts[target] - 1}, not {warp.get('warp')}",
                    )
                )
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


def check_event_scripts(tree: Path) -> list[Problem]:
    """Each zone's NPCs, signs, triggers and init scripts name a script of the zone's own file, which lists them by
    ScriptEntry in order from 1, or a global one from GLOBAL_SCRIPTS up (pokebw2's docs/scripts.md); 0 is none."""
    problems = []
    for path in _data_files(tree / "res" / "field" / "zones"):
        scripts = json.loads(path.read_text(encoding="utf-8")).get("scripts")
        events = tree / "res" / "field" / "events" / path.name
        if not isinstance(scripts, str) or not events.exists():
            continue
        source = tree / "res" / "field" / "scripts" / (scripts.removeprefix("SCRIPTS_").lower() + ".s")
        count = len(SCRIPT_ENTRY.findall(source.read_text(encoding="utf-8"))) if source.exists() else 0
        data = json.loads(events.read_text(encoding="utf-8"))
        named = [
            (f"{kind}[{i}].script", event.get("script", 0))
            for kind in ("npcs", "bg_events", "triggers", "init_scripts")
            for i, event in enumerate(data.get(kind, []))
        ]
        named += [
            (f"init_scripts[{i}].conditions[{j}].script", condition.get("script", 0))
            for i, table in enumerate(data.get("init_scripts", []))
            for j, condition in enumerate(table.get("conditions", []))
        ]
        for field, script in named:
            if 0 < script < GLOBAL_SCRIPTS and script > count:
                problems.append(
                    Problem(
                        f"res/field/events/{path.name}",
                        field,
                        f"{source.relative_to(tree).as_posix()} has scripts 1 to {count}, not {script}",
                    )
                )
    return problems


def check_region_zones(paths: Paths, game: Game, tree: Path) -> list[Problem]:
    zones = constants(tree, "zones")
    return [
        Problem(f"content/{layer.id}/zones.json", f"locations.{location}", f"{zone} isn't a zone")
        for layer in layer_module.load_stack(paths, list(game.layers))
        for location, zone in sorted(layer.zones.items())
        if zone not in zones
    ]


def _merged_files(paths: Paths, game: Game) -> dict[str, list[dict]]:
    """The merge report's files: each path the layers wrote, with its layers."""
    report_file = merge.report_path(paths, game)
    return json.loads(report_file.read_text(encoding="utf-8"))["files"] if report_file.exists() else {}


def run(paths: Paths, game: Game, tree: Path, schema_check: SchemaCheck | None = None) -> Result:
    schemas = check_schemas(tree, list(_merged_files(paths, game)), schema_check or upstream_schema_check(tree))
    problems = [
        *schemas.problems,
        *check_region_zones(paths, game, tree),
        *check_warps(tree),
        *check_event_scripts(tree),
        *check_zone_encounters(tree),
        *check_encounter_tables(tree),
    ]
    return Result(problems, schemas.unchecked)


def report(paths: Paths, game: Game, result: Result) -> None:
    files = _merged_files(paths, game)
    for file in result.unchecked:
        say(f'{file}: not checked against a schema; its "$schema" is missing or names no file')
    for problem in result.problems:
        writers = ", ".join(part["layer"] for part in files.get(problem.file, [])) or "upstream"
        say(f"{problem.file} ({writers}) {problem.field}: {problem.message}")
    count = len(result.problems)
    say(f"{game.id}: {count} problems" if count else f"{game.id}: no problems")
