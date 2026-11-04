"""Games: content/games/<game>/game.json, each one ROM (03-architecture.md §2).

A game's config has its name, its layers (lowest first), the source ROMs its layers extract from, and the KALEIDO_*
defines it builds with."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

from kaleido.config import ConfigError, Paths
from kaleido.roms import SOURCES

SAVE_MAGIC = "KALEIDO_SAVE_MAGIC"
# A game's save magic must not be Black 2's footer or outside-data magic, nor what a zeroed or erased card holds (E9)
RESERVED_MAGICS = {0x31053527: "Black 2's save footers'", 0xA10F49AE: "Black 2's outside data's",
                   0: "a zeroed card's", 0xFFFFFFFF: "an erased card's"}
DEFINE_NAME = re.compile(r"KALEIDO_[A-Z0-9_]+")
GAME_ID = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class Game:
    id: str
    name: str
    defines: dict[str, str]
    # Layer IDs under content/, lowest first
    layers: tuple[str, ...] = ()
    # The source ROMs its recipes read, by the name of their file in orig/ without its extension
    sources: tuple[str, ...] = ()


def directory(paths: Paths) -> Path:
    return paths.root / "content" / "games"


def _load(path: Path) -> Game:
    where = str(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"{where}: {error}") from error
    game_id = path.parent.name
    if not GAME_ID.fullmatch(game_id):
        raise ConfigError(f"{where}: a game's directory is lower case letters, digits and _")
    name, defines = data.get("name"), data.get("defines", {})
    if not isinstance(name, str) or not name:
        raise ConfigError(f"{where}: 'name' must be a non-empty string")
    if not isinstance(defines, dict):
        raise ConfigError(f"{where}: 'defines' must be an object")
    for define, value in defines.items():
        if not DEFINE_NAME.fullmatch(define):
            raise ConfigError(f"{where}: define {define!r} isn't a KALEIDO_* name")
        if not isinstance(value, str):
            raise ConfigError(f"{where}: define {define} must be a string, \"\" for one without a value")
    layers, sources = data.get("layers", []), data.get("sources", [])
    for key, value in (("layers", layers), ("sources", sources)):
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ConfigError(f"{where}: '{key}' must be a list of strings")
    known = {Path(spec.file).stem for spec in SOURCES}
    for source in sources:
        if source not in known:
            raise ConfigError(f"{where}: source {source!r} isn't a ROM Kaleido knows ({', '.join(sorted(known))})")
    return Game(game_id, name, dict(defines), tuple(layers), tuple(sources))


def load_all(paths: Paths) -> list[Game]:
    games = [_load(path) for path in sorted(directory(paths).glob("*/game.json"))]
    check_save_magics(games)
    return games


def load(paths: Paths, game_id: str) -> Game:
    for game in load_all(paths):
        if game.id == game_id:
            return game
    known = ", ".join(game.id for game in load_all(paths)) or "none"
    raise ConfigError(f"no game {game_id!r} in content/games/ (games: {known})")


def check_save_magics(games: list[Game]) -> None:
    """Each game has its own save magic, so that it reads every other game's card as empty (E9)."""
    seen: dict[int, str] = {}
    for game in games:
        if SAVE_MAGIC not in game.defines:
            raise ConfigError(f"{game.id}: every game needs its own {SAVE_MAGIC}")
        try:
            magic = int(game.defines[SAVE_MAGIC], 0)
        except ValueError as error:
            raise ConfigError(f"{game.id}: {SAVE_MAGIC} must be a number, such as 0x4b465231") from error
        if not 0 <= magic <= 0xFFFFFFFF:
            raise ConfigError(f"{game.id}: {SAVE_MAGIC} must fit in 32 bits")
        if magic in RESERVED_MAGICS:
            raise ConfigError(f"{game.id}: {SAVE_MAGIC} {magic:#x} is {RESERVED_MAGICS[magic]} magic")
        if magic in seen:
            raise ConfigError(f"{game.id}: {SAVE_MAGIC} {magic:#x} is also {seen[magic]}'s")
        seen[magic] = game.id
