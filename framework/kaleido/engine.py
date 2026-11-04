"""The engine: pokebw2 at the pin, with Kaleido's patch series applied on a local branch (ADR 0002)."""
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from kaleido.config import Paths
from kaleido.process import CommandError, run, stream
from kaleido.roms import BASE, ENGINE_BASEROM

BRANCH = "kaleido"
# git am records this committer, with each patch's own date, so the series gives the same commits on every machine
COMMITTER = {"GIT_COMMITTER_NAME": "Kaleido", "GIT_COMMITTER_EMAIL": "kaleido@localhost"}


class EngineError(Exception):
    pass


@dataclass(frozen=True)
class EngineState:
    initialized: bool
    head: str | None = None
    dirty: bool = False
    # HEAD is the pin with the current series, as bootstrap applied it
    applied: bool = False


def pin(paths: Paths) -> str:
    """The commit that the submodule points to, from the superproject's index."""
    line = run(["git", "ls-files", "-s", "--", "engine/pokebw2"], cwd=paths.root).split()
    if len(line) < 2 or line[0] != "160000":
        raise EngineError("engine/pokebw2 isn't a submodule in this checkout")
    return line[1]


def committed_pin(paths: Paths) -> str:
    """The commit that HEAD's tree records for the submodule. It differs from pin() only while a new pointer is
    staged, which only an engine sync should do (docs/engine-sync.md)."""
    return run(["git", "rev-parse", "HEAD:engine/pokebw2"], cwd=paths.root).strip()


def series(paths: Paths) -> list[Path]:
    return sorted(paths.patches.glob("*.patch"))


def series_digest(patches: list[Path]) -> str:
    digest = hashlib.sha256()
    for patch in patches:
        digest.update(patch.name.encode() + b"\0" + patch.read_bytes())
    return digest.hexdigest()


def _stamp_path(paths: Paths) -> Path:
    return paths.cache / "engine-series.json"


def _read_stamp(paths: Paths) -> dict | None:
    try:
        return json.loads(_stamp_path(paths).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def state(paths: Paths) -> EngineState:
    engine = paths.engine
    if not (engine / ".git").exists():
        return EngineState(initialized=False)
    head = run(["git", "rev-parse", "HEAD"], cwd=engine).strip()
    dirty = bool(run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=engine).strip())
    expected = {"pin": pin(paths), "series": series_digest(series(paths)), "head": head}
    return EngineState(initialized=True, head=head, dirty=dirty, applied=_read_stamp(paths) == expected)


def fetch(paths: Paths) -> None:
    """Checks the submodule out at the pin, fetching only that commit."""
    if not (paths.engine / ".git").exists():
        stream(["git", "submodule", "update", "--init", "--depth", "1", "--", "engine/pokebw2"], cwd=paths.root)
        return
    commit = pin(paths)
    try:
        run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=paths.engine)
    except CommandError:
        stream(["git", "fetch", "--depth", "1", "origin", commit], cwd=paths.engine)


def apply_series(paths: Paths, force: bool = False) -> bool:
    """Puts branch `kaleido` at the pin with the series applied. Returns False if it already was.

    It refuses to discard work: uncommitted changes in the engine, or a HEAD that isn't what bootstrap last applied
    (engine commits not yet exported to engine/patches/), unless force is given."""
    current = state(paths)
    if not current.initialized:
        raise EngineError("engine/pokebw2 isn't checked out yet")
    if current.applied and not current.dirty:
        return False
    if current.dirty:
        raise EngineError("engine/pokebw2 has uncommitted changes: commit and export them to engine/patches/, "
                          "or discard them, first")
    commit = pin(paths)
    stamp = _read_stamp(paths)
    expected_head = stamp["head"] if stamp else commit
    if current.head != expected_head and not force:
        raise EngineError(f"engine/pokebw2 is at {current.head[:12]}, not where bootstrap left it: export any engine "
                          "commits to engine/patches/ (git format-patch), or pass --force to discard them")
    patches = series(paths)
    run(["git", "switch", "-q", "--force-create", BRANCH, commit], cwd=paths.engine)
    if patches:
        env = {**os.environ, **COMMITTER}
        try:
            run(["git", "am", "-q", "--committer-date-is-author-date", *map(str, patches)], cwd=paths.engine, env=env)
        except CommandError as error:
            run(["git", "am", "--abort"], cwd=paths.engine)
            raise EngineError(f"the series doesn't apply to {commit[:12]}: {error}") from error
    head = run(["git", "rev-parse", "HEAD"], cwd=paths.engine).strip()
    paths.cache.mkdir(exist_ok=True)
    _stamp_path(paths).write_text(json.dumps({"pin": commit, "series": series_digest(patches), "head": head},
                                             indent=2) + "\n", encoding="utf-8")
    return True


def _link(link: Path, target: Path) -> str:
    """Points link at target, relatively. Leaves a real file or directory there alone. Returns what it did."""
    relative = os.path.relpath(target, link.parent)
    if link.is_symlink() and os.readlink(link) == relative:
        return "already linked"
    if link.exists() and not link.is_symlink():
        return f"left {link.name} as it is: not a link"
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        link.unlink()
    link.symlink_to(relative)
    return f"linked to {relative}"


def link_base_rom(paths: Paths, engine_dir: Path | None = None) -> str:
    """Links an engine checkout's base ROM to the player's orig/black2.nds. Returns what it did."""
    target = paths.orig / BASE.file
    if not target.exists():
        return f"no {target.relative_to(paths.root)} yet"
    return f"{ENGINE_BASEROM}: {_link((engine_dir or paths.engine) / ENGINE_BASEROM, target)}"


def worktree(paths: Paths, directory: Path, tools: list[str]) -> str:
    """A git worktree of the engine at branch kaleido's commit, detached (the branch stays checked out in
    engine/pokebw2), with the base ROM and engine/pokebw2's downloaded tools linked in. Returns its commit.

    The worktree is Kaleido's: kaleido merge writes the layers into it. When the series moves, it is checked out again
    over any changes, and the next merge writes the layers again; nobody edits it by hand."""
    head = run(["git", "rev-parse", BRANCH], cwd=paths.engine).strip()
    if not (directory / ".git").exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "worktree", "add", "--quiet", "--detach", str(directory), head], cwd=paths.engine)
    elif run(["git", "rev-parse", "HEAD"], cwd=directory).strip() != head:
        run(["git", "checkout", "-q", "--force", "--detach", head], cwd=directory)
    link_base_rom(paths, directory)
    for name in tools:
        shared = paths.engine / "tools" / name
        if shared.exists():
            _link(directory / "tools" / name, shared)
    return head
