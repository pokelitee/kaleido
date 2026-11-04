"""kaleido extract <game>: runs the recipes of a game's layers on the player's source ROMs, into
build/<game>/extracted/<layer>/ at upstream's paths. Extracted content is never committed (03-architecture.md §6).

A recipe is extract/<name>.json in a layer. Locations are the region's names, which its zones.json maps to the zones
that hold them (ADR 0004). The kinds:

    { "kind": "gba_gen3_wild_land", "source": "firered", "map": "ROUTE 1", "location": "route_1" }

The map's land encounters, into the encounter table that the location's zone header names. `map` is the map's name as
the source ROM shows it.

    { "kind": "gba_gen3_place_names", "source": "firered", "places": { "pallet_town": 88 } }

Each location's name, from the source's map section of that number, as a merge patch on the place that its zone's
header names. Gen 3's capitals become Gen 5's title case ("PALLET TOWN" becomes "Pallet Town")."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from extractors import gba_gen3
from kaleido import layers as layer_module
from kaleido.config import ConfigError, Paths
from kaleido.games import Game
from kaleido.hashing import file_hash
from kaleido.roms import SOURCES

# Gen 5 has no per-step encounter rate: a walking group's rate selects one of 12 ramp settings (field_encount.c). A
# source game's land rate becomes setting 7, the most common in Black 2's grass tables, until Phase 3 decides the
# general rule (01-feasibility.md)
GEN5_GRASS_SETTING = 7
EMPTY_GROUPS = ("dark_grass", "shaking_grass", "surf", "rippling_surf", "fishing", "rippling_fishing")


@dataclass(frozen=True)
class Extracted:
    layer: str
    # At upstream's path, relative to the layer's extracted directory: res/field/encounters/route_19.json
    path: str
    recipe: str


def directory(paths: Paths, game: Game) -> Path:
    return paths.root / "build" / game.id / "extracted"


def _source_rom(paths: Paths, game: Game, source: str) -> bytes:
    if source not in game.sources:
        raise ConfigError(f"{game.id}: a recipe reads {source!r}, which game.json's 'sources' doesn't list")
    spec = next(spec for spec in SOURCES if Path(spec.file).stem == source)
    rom = paths.orig / spec.file
    if not rom.exists():
        raise ConfigError(f"put your own {spec.name} dump at orig/{spec.file}")
    if file_hash(rom, "sha1") != spec.sha1:
        raise ConfigError(f"orig/{spec.file} isn't {spec.name} (SHA1 {spec.sha1}): ./kaleido doctor says what it is")
    return rom.read_bytes()


def _species_names(paths: Paths) -> list[str]:
    text = (paths.engine / "generated" / "species.txt").read_text(encoding="utf-8")
    return [line.split()[0] for line in text.splitlines() if line.startswith("SPECIES_")]


def _zone_header(paths: Paths, zone: str) -> dict:
    header = paths.engine / "res" / "field" / "zones" / (zone.removeprefix("ZONE_").lower() + ".json")
    if not header.exists():
        raise ConfigError(f"no zone header for {zone} ({header.relative_to(paths.root)})")
    return json.loads(header.read_text(encoding="utf-8"))


def encounter_table_path(paths: Paths, zone: str) -> str:
    """The encounter table a zone's header names, as its file under res/."""
    table = _zone_header(paths, zone).get("encounters")
    if not table:
        raise ConfigError(f"{zone} has no encounter table to take the source's encounters")
    return f"res/field/encounters/{table.removeprefix('ENCOUNTERS_').lower()}.json"


def place_path(paths: Paths, zone: str) -> str:
    """The place a zone's header names, as its file under res/."""
    place = _zone_header(paths, zone).get("place")
    if not place:
        raise ConfigError(f"{zone} has no place to take the source's name")
    return f"res/field/places/{place.removeprefix('PLACE_').lower()}.json"


def _rom(paths: Paths, game: Game, recipe: dict, roms: dict[str, gba_gen3.Rom]) -> gba_gen3.Rom:
    source = recipe["source"]
    if source not in roms:
        roms[source] = gba_gen3.Rom(_source_rom(paths, game, source))
    return roms[source]


def _wild_land(
    paths: Paths, game: Game, stack: list, recipe: dict, roms: dict[str, gba_gen3.Rom]
) -> list[tuple[str, str]]:
    land = gba_gen3.land_encounters(_rom(paths, game, recipe, roms), recipe["map"])
    names = _species_names(paths)
    table = {
        "$schema": "encounters.schema.json",
        "all_year": {
            "rates": {"grass": GEN5_GRASS_SETTING, **{group: 0 for group in EMPTY_GROUPS}, "flags": 0},
            "grass": [[names[slot.species], slot.min_level, slot.max_level] for slot in land.slots],
            **{group: [] for group in EMPTY_GROUPS},
        },
    }
    path = encounter_table_path(paths, layer_module.zone_of(stack, recipe["location"]))
    return [(path, json.dumps(table, indent=4) + "\n")]


def _place_names(
    paths: Paths, game: Game, stack: list, recipe: dict, roms: dict[str, gba_gen3.Rom]
) -> list[tuple[str, str]]:
    names = gba_gen3.section_names(_rom(paths, game, recipe, roms))
    outputs = []
    for location, section in sorted(recipe["places"].items()):
        index = section - gba_gen3.KANTO_MAPSEC_START if isinstance(section, int) else -1
        if not 0 <= index < len(names):
            raise ConfigError(f"{location}: map section {section!r} isn't one of the source's {len(names)} names")
        path = place_path(paths, layer_module.zone_of(stack, location)) + ".merge.json"
        outputs.append((path, json.dumps({"name": names[index].title()}, ensure_ascii=False, indent=4) + "\n"))
    return outputs


KINDS = {"gba_gen3_wild_land": _wild_land, "gba_gen3_place_names": _place_names}
# Each kind's fields and their types
FIELDS = {
    "gba_gen3_wild_land": {"source": str, "map": str, "location": str},
    "gba_gen3_place_names": {"source": str, "places": dict},
}


def read_recipe(layer: layer_module.Layer, recipe_path: str) -> dict:
    """A layer's recipe, checked for a known kind and that kind's fields; reading it needs no ROM."""
    where = f"{layer.id}/{recipe_path}"
    try:
        recipe = json.loads((layer.path / recipe_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"{where}: {error}") from error
    kind = recipe.get("kind") if isinstance(recipe, dict) else None
    if kind not in KINDS:
        raise ConfigError(f"{where}: kind {kind!r} isn't one of {', '.join(KINDS)}")
    missing = [key for key, kind_of in FIELDS[kind].items() if not isinstance(recipe.get(key), kind_of)]
    if missing:
        raise ConfigError(f"{where}: missing {', '.join(missing)}, or not of the right type")
    return recipe


def run(paths: Paths, game: Game) -> list[Extracted]:
    stack = layer_module.load_stack(paths, list(game.layers))
    out = directory(paths, game)
    if out.exists():
        shutil.rmtree(out)
    results, roms = [], {}
    for layer in stack:
        for recipe_path in layer.recipes():
            where = f"{layer.id}/{recipe_path}"
            recipe = read_recipe(layer, recipe_path)
            for path, content in KINDS[recipe["kind"]](paths, game, stack, recipe, roms):
                layer.category_of(path, recipe_path)
                target = out / layer.id / path
                if target.exists():
                    raise ConfigError(f"{where}: {path} is also another recipe's output in {layer.id}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                results.append(Extracted(layer.id, path, recipe_path))
    return results


def main(paths: Paths, game: Game) -> int:
    results = run(paths, game)
    for result in results:
        print(f"{result.layer}: {result.path} from {result.recipe}")
    print(f"{len(results)} files in {directory(paths, game).relative_to(paths.root)}")
    return 0
