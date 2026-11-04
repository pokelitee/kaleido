"""The repository's paths and engine/engine.toml."""
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Repo:
    """A source repository at a commit."""

    url: str
    commit: str


@dataclass(frozen=True)
class EngineConfig:
    upstream_url: str
    mirror_url: str
    black2_sha1: str
    dsd_patch: Path
    ds_rom: Repo
    ds_decomp: Repo
    # SHA256 of each tool that pokebw2 downloads into engine/pokebw2/tools/ (a directory's is a tree digest)
    tool_hashes: dict[str, str]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def engine(self) -> Path:
        return self.root / "engine" / "pokebw2"

    @property
    def patches(self) -> Path:
        return self.root / "engine" / "patches"

    @property
    def engine_toml(self) -> Path:
        return self.root / "engine" / "engine.toml"

    @property
    def orig(self) -> Path:
        return self.root / "orig"

    @property
    def cache(self) -> Path:
        return self.root / ".cache"


def _get(table: dict, key: str, where: str):
    if key not in table:
        raise ConfigError(f"{where}: missing {key!r}")
    return table[key]


def _repo(table: dict, where: str) -> Repo:
    return Repo(url=_get(table, "url", where), commit=_get(table, "commit", where))


def load_engine_config(paths: Paths) -> EngineConfig:
    where = str(paths.engine_toml)
    try:
        data = tomllib.loads(paths.engine_toml.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(f"{where}: {error}") from error
    upstream = _get(data, "upstream", where)
    dsd = _get(data, "dsd", where)
    return EngineConfig(
        upstream_url=_get(upstream, "url", f"{where} [upstream]"),
        mirror_url=upstream.get("mirror", ""),
        black2_sha1=_get(_get(data, "baseline", where), "black2_sha1", f"{where} [baseline]"),
        dsd_patch=paths.root / "engine" / _get(dsd, "patch", f"{where} [dsd]"),
        ds_rom=_repo(_get(dsd, "ds_rom", f"{where} [dsd]"), f"{where} [dsd.ds_rom]"),
        ds_decomp=_repo(_get(dsd, "ds_decomp", f"{where} [dsd]"), f"{where} [dsd.ds_decomp]"),
        tool_hashes=dict(data.get("tools", {})),
    )
