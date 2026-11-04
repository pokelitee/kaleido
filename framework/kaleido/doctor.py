"""kaleido doctor: checks the machine, the engine, Kaleido's dsd, the ROMs and the downloaded tools, and says how to
fix what's wrong. Exits 1 if anything fails; warnings don't."""

import platform
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from kaleido import dsd, engine, patch
from kaleido.config import ConfigError, EngineConfig, Paths, load_engine_config
from kaleido.hashing import file_hash, tree_digest
from kaleido.process import CommandError
from kaleido.roms import BASE, ENGINE_BASEROM, SOURCES, RomSpec, identify

OK, WARN, FAIL = "ok", "warn", "FAIL"
MIN_PYTHON = (3, 11)
MIN_FREE_BYTES = 5 * 1024**3
# What upstream's build calls (its docs/building.md and configure.py), and git for the engine
COMMANDS = ["git", "ninja", "clang", "llvm-objcopy", "sha1sum"]


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    fix: str = ""


def check_platform(system: str, root: Path) -> Check:
    if system != "Linux":
        return Check("platform", FAIL, f"{system}", "build in Linux or WSL2; upstream's build doesn't run elsewhere")
    if root.as_posix().startswith("/mnt/"):
        return Check(
            "platform",
            WARN,
            f"Linux, checkout on {root}",
            "clone into WSL's own filesystem (~/…): /mnt/ is far slower (R-23)",
        )
    return Check("platform", OK, f"Linux, {platform.release()}")


def check_python(version: tuple[int, int]) -> Check:
    found = f"{version[0]}.{version[1]}"
    if version < MIN_PYTHON:
        return Check("python", FAIL, found, "install Python 3.11 or later")
    return Check("python", OK, found)


def check_commands(which: Callable[[str], str | None] = shutil.which) -> list[Check]:
    checks = []
    for name in COMMANDS:
        found = which(name)
        checks.append(
            Check(
                f"command {name}",
                OK if found else FAIL,
                found or "not found",
                "" if found else "sudo apt install ninja-build clang llvm git coreutils",
            )
        )
    cargo = dsd.cargo()
    checks.append(
        Check(
            "command cargo",
            OK if cargo else WARN,
            cargo or "not found",
            "" if cargo else "install Rust with rustup (https://rustup.rs): bootstrap builds dsd with it",
        )
    )
    checks.append(check_xdelta(patch.version()))
    return checks


def check_xdelta(found: str | None) -> Check:
    if found is None:
        return Check("command xdelta3", WARN, "not found", "sudo apt install xdelta3: kaleido patch needs it")
    if found != patch.XDELTA_VERSION:
        return Check(
            "command xdelta3",
            WARN,
            f"version {found}",
            f"Kaleido has checked {patch.XDELTA_VERSION}'s patches only; another version may make others",
        )
    return Check("command xdelta3", OK, f"version {found}")


def check_disk(free_bytes: int) -> Check:
    detail = f"{free_bytes / 1024**3:.1f} GiB free"
    if free_bytes < MIN_FREE_BYTES:
        return Check("disk", WARN, detail, "one engine checkout with a build takes about 3 GB, dsd's build more")
    return Check("disk", OK, detail)


def check_engine(paths: Paths) -> Check:
    try:
        current = engine.state(paths)
    except (CommandError, engine.EngineError) as error:
        return Check("engine", FAIL, str(error), "run ./kaleido bootstrap")
    if not current.initialized:
        return Check("engine", WARN, "engine/pokebw2 isn't checked out", "run ./kaleido bootstrap")
    if current.dirty:
        return Check(
            "engine",
            WARN,
            "engine/pokebw2 has uncommitted changes",
            "export engine changes to engine/patches/; builds must use the series",
        )
    if not current.applied:
        return Check(
            "engine",
            WARN,
            f"engine/pokebw2 at {current.head[:12]} isn't the pin with the current series",
            "run ./kaleido bootstrap",
        )
    return Check("engine", OK, f"pin {engine.pin(paths)[:12]} + {len(engine.series(paths))} patches")


def check_pointer(paths: Paths) -> Check:
    """The engine's branch carries the series, so git status shows engine/pokebw2 as changed. Staging that would point
    the superproject at a commit only this machine has."""
    try:
        staged, committed = engine.pin(paths), engine.committed_pin(paths)
    except (CommandError, engine.EngineError) as error:
        return Check("engine pointer", FAIL, str(error), "check engine/pokebw2 in .gitmodules and the index")
    if staged != committed:
        return Check(
            "engine pointer",
            FAIL,
            f"staged {staged[:12]}, committed {committed[:12]}",
            "git restore --staged engine/pokebw2, unless you are syncing the engine (docs/engine-sync.md)",
        )
    return Check("engine pointer", OK, f"{committed[:12]}")


def check_dsd(paths: Paths, config: EngineConfig) -> Check:
    if dsd.is_current(paths, config):
        return Check("dsd", OK, str(dsd.binary(paths).relative_to(paths.root)))
    if not dsd.binary(paths).exists():
        return Check(
            "dsd", WARN, "Kaleido's dsd isn't built", "run ./kaleido bootstrap (about 35 minutes the first time)"
        )
    if not dsd.has_flag(dsd.binary(paths)):
        return Check("dsd", WARN, f"the built dsd doesn't take {dsd.FLAG}", "run ./kaleido bootstrap")
    return Check("dsd", WARN, "built from other commits or another patch", "run ./kaleido bootstrap")


def check_rom(paths: Paths, spec: RomSpec) -> Check:
    name = f"rom {spec.file}"
    path = paths.orig / spec.file
    if not path.exists():
        status = FAIL if spec.required else WARN
        need = "for every build" if spec.required else "to extract its game's content"
        return Check(name, status, "missing", f"put your own {spec.name} dump at orig/{spec.file} ({need})")
    sha1 = file_hash(path, "sha1")
    if sha1 != spec.sha1:
        actual = identify(sha1)
        return Check(
            name,
            FAIL,
            f"SHA1 {sha1}" + (f", which is {actual}" if actual else ", unknown"),
            f"Kaleido needs {spec.name}, SHA1 {spec.sha1}",
        )
    return Check(name, OK, spec.name)


def check_engine_rom(paths: Paths) -> Check:
    link = paths.engine / ENGINE_BASEROM
    if not paths.engine.joinpath(".git").exists():
        return Check("engine base ROM", WARN, "engine not checked out", "run ./kaleido bootstrap")
    if not link.exists():
        return Check("engine base ROM", WARN, f"no {ENGINE_BASEROM}", "run ./kaleido bootstrap after adding the ROM")
    return Check("engine base ROM", OK, f"{ENGINE_BASEROM} -> {link.resolve()}")


def check_tools(paths: Paths, config: EngineConfig) -> list[Check]:
    checks = []
    for name, expected in sorted(config.tool_hashes.items()):
        path = paths.engine / "tools" / name
        if not path.exists():
            checks.append(Check(f"tool {name}", OK, "not downloaded yet: the first build does it"))
            continue
        actual = tree_digest(path) if path.is_dir() else file_hash(path)
        if actual != expected:
            checks.append(
                Check(
                    f"tool {name}",
                    FAIL,
                    f"SHA256 {actual}, recorded {expected}",
                    "delete it so the next build downloads it again, and compare (R-12)",
                )
            )
        else:
            checks.append(Check(f"tool {name}", OK, "hash matches"))
    return checks


def run_checks(paths: Paths) -> list[Check]:
    checks = [
        check_platform(platform.system(), paths.root),
        check_python(sys.version_info[:2]),
        *check_commands(),
        check_disk(shutil.disk_usage(paths.root).free),
    ]
    try:
        config = load_engine_config(paths)
    except ConfigError as error:
        return [*checks, Check("engine.toml", FAIL, str(error), "fix engine/engine.toml")]
    checks += [
        check_pointer(paths),
        check_engine(paths),
        check_dsd(paths, config),
        check_rom(paths, BASE),
        *(check_rom(paths, spec) for spec in SOURCES),
        check_engine_rom(paths),
        *check_tools(paths, config),
    ]
    return checks


def main(paths: Paths) -> int:
    checks = run_checks(paths)
    width = max(len(check.name) for check in checks)
    for check in checks:
        print(f"{check.status:4}  {check.name:{width}}  {check.detail}")
        if check.fix and check.status != OK:
            print(f"{'':4}  {'':{width}}  -> {check.fix}")
    failures = sum(check.status == FAIL for check in checks)
    warnings = sum(check.status == WARN for check in checks)
    print(f"\n{failures} failed, {warnings} warnings")
    return 1 if failures else 0
