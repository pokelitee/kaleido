"""Kaleido's dsd: the dsd that pokebw2 pins, plus `rom build --allow-stale-secure-area` (ADR 0004), built with Rust
from ds-rom and ds-decomp at the commits engine/engine.toml names. Until upstream takes the change."""

import json
import os
import shutil
from pathlib import Path

from kaleido.config import EngineConfig, Paths, Repo
from kaleido.hashing import file_hash
from kaleido.process import CommandError, run, stream

FLAG = "--allow-stale-secure-area"


def directory(paths: Paths) -> Path:
    return paths.cache / "dsd"


def binary(paths: Paths) -> Path:
    return directory(paths) / "ds-decomp" / "target" / "release" / "dsd"


def expected_stamp(config: EngineConfig) -> dict:
    return {"ds_rom": config.ds_rom.commit, "ds_decomp": config.ds_decomp.commit, "patch": file_hash(config.dsd_patch)}


def _stamp_path(paths: Paths) -> Path:
    return directory(paths) / "stamp.json"


def has_flag(executable: Path) -> bool:
    """Whether a dsd takes Kaleido's flag, as its help for `rom build` says."""
    try:
        return FLAG in run([str(executable), "rom", "build", "--help"])
    except (CommandError, OSError):
        return False


def is_current(paths: Paths, config: EngineConfig) -> bool:
    try:
        stamp = json.loads(_stamp_path(paths).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return binary(paths).exists() and stamp == expected_stamp(config) and has_flag(binary(paths))


def cargo() -> str | None:
    found = shutil.which("cargo")
    if found:
        return found
    rustup_cargo = Path.home() / ".cargo" / "bin" / "cargo"
    return str(rustup_cargo) if rustup_cargo.exists() else None


def _checkout(checkout: Path, repo: Repo) -> None:
    """Puts a checkout at the commit, without local changes, fetching only that commit."""
    if not (checkout / ".git").exists():
        checkout.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q"], cwd=checkout)
        run(["git", "remote", "add", "origin", repo.url], cwd=checkout)
    try:
        run(["git", "cat-file", "-e", f"{repo.commit}^{{commit}}"], cwd=checkout)
    except CommandError:
        stream(["git", "fetch", "-q", "--depth", "1", "origin", repo.commit], cwd=checkout)
    run(["git", "checkout", "-q", "--force", "--detach", repo.commit], cwd=checkout)


def apply_patch(root: Path, patch: Path, checkouts: list[str]) -> None:
    """Applies a patch whose paths start with the checkouts' directory names, from root, and checks that it changed
    each checkout. root may lie inside another repository (.cache/ is inside Kaleido's): git apply run there would take
    the paths as that repository's and skip them, so the ceiling stops its search at root."""
    run(["git", "apply", str(patch)], cwd=root, env={**os.environ, "GIT_CEILING_DIRECTORIES": str(root.parent)})
    for checkout in checkouts:
        if not run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root / checkout).strip():
            raise CommandError(f"{patch.name} changed nothing in {checkout}")


def build(paths: Paths, config: EngineConfig) -> bool:
    """Builds Kaleido's dsd unless it is current. Returns False if it was."""
    if is_current(paths, config):
        return False
    tool = cargo()
    if not tool:
        raise CommandError("cargo not found: install Rust with rustup (https://rustup.rs) to build Kaleido's dsd")
    root = directory(paths)
    _checkout(root / "ds-rom", config.ds_rom)
    _checkout(root / "ds-decomp", config.ds_decomp)
    apply_patch(root, config.dsd_patch, ["ds-rom", "ds-decomp"])
    env = dict(os.environ)
    if not shutil.which("cc") and shutil.which("clang"):
        # Rust links with cc by default; upstream's build already needs clang
        env.update(CC="clang", RUSTFLAGS="-C linker=clang")
    stream([tool, "build", "--release", "--bin", "dsd"], cwd=root / "ds-decomp", env=env)
    if not has_flag(binary(paths)):
        raise CommandError(f"the built dsd doesn't take {FLAG}")
    _stamp_path(paths).write_text(json.dumps(expected_stamp(config), indent=2) + "\n", encoding="utf-8")
    return True
