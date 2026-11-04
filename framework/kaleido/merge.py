"""kaleido merge <game>: lays a game's layers over the engine's res/ and generated/, lowest first, in the game's engine
worktree (03-architecture.md §5).

What a layer's file does to the merged tree:
- res/P: replaces P.
- res/P.merge.json: patches the lower P. For a JSON file, an RFC 7396 merge patch (arrays are replaced whole); for a
  text file (res/text/), an object of message labels and their new text, in the text file's own escaping.
- generated/<list>.txt: appends its constants to upstream's list; a name that's already there is an error.

The lower file is always the layers below over upstream's file at the worktree's commit, never the worktree's current
content, so a merge gives the same tree however often it runs. Only files whose bytes change are written, which keeps
ninja's build incremental, and files that an earlier merge wrote but this one doesn't are restored. The merge writes
build/<game>/merge-report.json: every file it wrote, and each layer's part in it with its provenance category."""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from kaleido import extract
from kaleido import layers as layer_module
from kaleido.config import ConfigError, Paths
from kaleido.games import Game
from kaleido.process import run

MERGE_SUFFIX = ".merge.json"
CONSTANT = re.compile(r"[A-Z][A-Z0-9_]*")


@dataclass(frozen=True)
class Part:
    layer: str
    category: str
    how: str


@dataclass
class Plan:
    files: dict[str, bytes]
    parts: dict[str, list[Part]]


def merge_patch(target, patch):
    """RFC 7396: an object merges key by key, null removes a key, anything else replaces."""
    if not isinstance(patch, dict):
        return patch
    result = dict(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge_patch(result.get(key), value)
    return result


def override_messages(text: str, overrides: dict, where: str) -> str:
    lines = text.split("\n")
    for label, message in overrides.items():
        if not isinstance(message, str):
            raise ConfigError(f"{where}: {label}'s text must be a string")
        found = [i for i, line in enumerate(lines) if line.startswith(f"{label} = ")]
        if len(found) != 1:
            raise ConfigError(f"{where}: the lower file has {len(found)} messages labelled {label}; expected one")
        lines[found[0]] = f"{label} = {message}"
    return "\n".join(lines)


def append_constants(text: str, addition: str, where: str) -> str:
    existing = {line.split()[0] for line in text.splitlines() if line and not line.startswith("#")}
    new = [line.strip() for line in addition.splitlines() if line.strip() and not line.startswith("#")]
    for name in new:
        if not CONSTANT.fullmatch(name):
            raise ConfigError(f"{where}: {name!r} isn't a constant name (appended constants take the next numbers)")
        if name in existing:
            raise ConfigError(f"{where}: {name} is already in the list")
        existing.add(name)
    return text.rstrip("\n") + "\n" + "".join(f"{name}\n" for name in new)


def _upstream(worktree: Path, path: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=worktree, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def plan(paths: Paths, game: Game, worktree: Path, extracted: list[extract.Extracted]) -> Plan:
    result = Plan({}, {})

    def lower(path: str, where: str) -> bytes:
        content = result.files[path] if path in result.files else _upstream(worktree, path)
        if content is None:
            raise ConfigError(f"{where}: there is no {path} below it to patch")
        return content

    for layer in layer_module.load_stack(paths, list(game.layers)):
        items = [(path, layer.path / path, layer.category_of(path)) for path in layer.content_files()]
        items += [
            (item.path, extract.directory(paths, game) / layer.id / item.path, "extracted")
            for item in extracted
            if item.layer == layer.id
        ]
        targets: dict[str, str] = {}
        for path, _, _ in items:
            target = path.removesuffix(MERGE_SUFFIX)
            if target in targets:
                raise ConfigError(f"{layer.id}: {targets[target]} and {path} both change {target}")
            targets[target] = path
        # Replacements first, so that a layer's patches never apply to its own files
        for path, file, category in sorted(items, key=lambda item: item[0].endswith(MERGE_SUFFIX)):
            where = f"{layer.id}/{path}"
            if path.endswith(MERGE_SUFFIX):
                target = path.removesuffix(MERGE_SUFFIX)
                patch = json.loads(file.read_text(encoding="utf-8"))
                if target.endswith(".json"):
                    merged = merge_patch(json.loads(lower(target, where)), patch)
                    content = (json.dumps(merged, indent=4, ensure_ascii=False) + "\n").encode()
                elif target.startswith("res/text/") and target.endswith(".txt"):
                    if not isinstance(patch, dict):
                        raise ConfigError(f"{where}: a text merge is an object of labels and their text")
                    content = override_messages(lower(target, where).decode("utf-8"), patch, where).encode()
                else:
                    raise ConfigError(f"{where}: only JSON files and res/text/ files take a merge")
                how = "merge"
            elif path.startswith("generated/") and path.endswith(".txt"):
                target = path
                content = append_constants(
                    lower(target, where).decode("utf-8"), file.read_text(encoding="utf-8"), where
                ).encode()
                how = "append"
            else:
                target, content, how = path, file.read_bytes(), "replace"
            result.files[target] = content
            result.parts.setdefault(target, []).append(Part(layer.id, category, how))
    return result


def report_path(paths: Paths, game: Game) -> Path:
    return paths.root / "build" / game.id / "merge-report.json"


def write(paths: Paths, game: Game, worktree: Path, merged: Plan) -> tuple[int, int]:
    """Writes the merged files that changed and restores those an earlier merge wrote but this one doesn't. Returns
    (written, restored)."""
    report = report_path(paths, game)
    previous = set(json.loads(report.read_text(encoding="utf-8"))["files"]) if report.exists() else set()
    written = 0
    for path, content in sorted(merged.files.items()):
        file = worktree / path
        if not file.exists() or file.read_bytes() != content:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
            written += 1
    restored = 0
    for path in sorted(previous - set(merged.files)):
        if _upstream(worktree, path) is not None:
            run(["git", "checkout", "HEAD", "--", path], cwd=worktree)
        else:
            (worktree / path).unlink(missing_ok=True)
        restored += 1
    commit = run(["git", "rev-parse", "HEAD"], cwd=worktree).strip()
    files = {path: [vars(part) for part in parts] for path, parts in sorted(merged.parts.items())}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"commit": commit, "files": files}, indent=2) + "\n", encoding="utf-8")
    return written, restored


def merge(paths: Paths, game: Game, worktree: Path, extract_sources: bool = True) -> tuple[int, int, int]:
    """Extracts, plans and writes. Returns (files merged, written, restored). Without extract_sources, only the
    committed layer files merge, as on a machine without the source ROMs (CI)."""
    extracted = extract.run(paths, game) if extract_sources else []
    merged = plan(paths, game, worktree, extracted)
    written, restored = write(paths, game, worktree, merged)
    return len(merged.files), written, restored
