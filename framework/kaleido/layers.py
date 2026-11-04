"""Content layers: content/<kind>s/<name>/ (03-architecture.md §5, §6).

A layer holds layer.json (its kind), provenance.json (a category for every content file), content at upstream's paths
under res/ and generated/, extraction recipes under extract/, and, for a region, zones.json: which existing zone ID
holds each of its locations (ADR 0004)."""

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path

from kaleido.config import ConfigError, Paths

KINDS = ("region", "family", "game")
DIRECTORIES = {"region": "regions", "family": "families", "game": "games"}
CATEGORIES = ("original", "third-party", "extracted")
CONTENT_DIRS = ("res", "generated")


@dataclass(frozen=True)
class ProvenanceEntry:
    paths: tuple[str, ...]
    category: str
    recipe: str | None = None

    def matches(self, path: str) -> bool:
        return any(fnmatch.fnmatchcase(path, pattern) for pattern in self.paths)


@dataclass(frozen=True)
class Layer:
    # Its path under content/, as games name it: "regions/kanto"
    id: str
    path: Path
    kind: str
    provenance: tuple[ProvenanceEntry, ...]
    # Location name -> ZONE_* constant
    zones: dict[str, str]

    def content_files(self) -> list[str]:
        """The committed content files, as POSIX paths relative to the layer."""
        files = []
        for directory in CONTENT_DIRS:
            root = self.path / directory
            if root.is_dir():
                files += [path.relative_to(self.path).as_posix() for path in root.rglob("*") if path.is_file()]
        return sorted(files)

    def recipes(self) -> list[str]:
        return sorted(path.relative_to(self.path).as_posix() for path in (self.path / "extract").glob("*.json"))

    def category_of(self, path: str, recipe: str | None = None) -> str:
        """The one provenance category of a content path; extracted paths also name the recipe that makes them."""
        entries = [entry for entry in self.provenance if entry.matches(path)]
        if len(entries) != 1:
            found = "no provenance entry" if not entries else f"{len(entries)} provenance entries"
            raise ConfigError(f"{self.id}: {path} has {found}; it needs exactly one")
        entry = entries[0]
        if recipe is None and entry.category == "extracted":
            raise ConfigError(f"{self.id}: {path} is extracted content and must not be committed")
        if recipe is not None and (entry.category != "extracted" or entry.recipe != recipe):
            raise ConfigError(
                f"{self.id}: {path} comes from {recipe}; its provenance entry must be extracted, with that recipe"
            )
        return entry.category


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"{path}: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: must be a JSON object")
    return data


def _provenance(path: Path) -> tuple[ProvenanceEntry, ...]:
    entries = []
    for i, entry in enumerate(_read_json(path).get("entries", [])):
        where = f"{path} entry {i}"
        patterns, category = entry.get("paths"), entry.get("category")
        if not isinstance(patterns, list) or not patterns or not all(isinstance(p, str) for p in patterns):
            raise ConfigError(f"{where}: 'paths' must be a non-empty list of patterns")
        if category not in CATEGORIES:
            raise ConfigError(f"{where}: 'category' must be one of {', '.join(CATEGORIES)}")
        recipe = entry.get("recipe")
        if (category == "extracted") != (recipe is not None):
            raise ConfigError(f"{where}: an extracted entry, and only one, names its recipe")
        if category == "third-party" and not all(entry.get(key) for key in ("license", "author", "source")):
            raise ConfigError(f"{where}: a third-party entry records its license, author and source")
        entries.append(ProvenanceEntry(tuple(patterns), category, recipe))
    return tuple(entries)


def load(paths: Paths, layer_id: str) -> Layer:
    path = paths.root / "content" / layer_id
    manifest = _read_json(path / "layer.json")
    kind = manifest.get("kind")
    if kind not in KINDS or layer_id.split("/")[0] != DIRECTORIES[kind]:
        expected = ", ".join(f"{k} under content/{d}/" for k, d in DIRECTORIES.items())
        raise ConfigError(f"{path / 'layer.json'}: kind {kind!r} doesn't fit content/{layer_id}; kinds: {expected}")
    zones_file = path / "zones.json"
    zones = _read_json(zones_file).get("locations", {}) if zones_file.exists() else {}
    if zones and kind != "region":
        raise ConfigError(f"{zones_file}: only a region maps its locations to zones")
    provenance = _provenance(path / "provenance.json") if (path / "provenance.json").exists() else ()
    layer = Layer(layer_id, path, kind, provenance, dict(zones))
    for file in layer.content_files():
        layer.category_of(file)
    return layer


def load_stack(paths: Paths, layer_ids: list[str]) -> list[Layer]:
    """A game's layers, lowest first: regions, then families, then games, as 03-architecture.md §2 orders them."""
    layers = [load(paths, layer_id) for layer_id in layer_ids]
    order = [KINDS.index(layer.kind) for layer in layers]
    if order != sorted(order):
        raise ConfigError(f"layers {', '.join(layer_ids)}: regions come before families, families before games")
    return layers


def zone_of(layers: list[Layer], location: str) -> str:
    for layer in reversed(layers):
        if location in layer.zones:
            return layer.zones[location]
    raise ConfigError(f"no region layer maps location {location!r} to a zone (zones.json)")
