"""kaleido build <game>: builds a game's ROM in its own engine worktree, build/<game>/engine/: its layers extracted
and merged in, its defines passed, its map chunks checked against their buffers (chunks.py), the ROM copied to
build/<game>/kaleido-<game>.nds (03-architecture.md §7)."""

import shutil
from functools import partial
from pathlib import Path

from kaleido import chunks, dsd, engine, enginebuild, games, merge, validate
from kaleido.config import Paths, load_engine_config
from kaleido.process import CommandError

say = partial(print, flush=True)


def prepare(paths: Paths, game: games.Game, extract_sources: bool = True) -> Path:
    """The game's worktree at the engine's series, with its layers merged in. Returns the worktree."""
    config = load_engine_config(paths)
    state = engine.state(paths)
    if not state.applied or state.dirty:
        raise CommandError("engine/pokebw2 isn't the pin with the current series: run ./kaleido bootstrap")
    worktree = paths.root / "build" / game.id / "engine"
    say(f"{game.id}: engine worktree {worktree.relative_to(paths.root)} (a first checkout takes a minute or two)")
    commit = engine.worktree(paths, worktree, sorted(config.tool_hashes))
    if not extract_sources:
        say(f"{game.id}: extraction skipped; only the committed layer files merge")
    files, written, restored = merge.merge(paths, game, worktree, extract_sources)
    say(
        f"{game.id}: at {commit[:12]}; {len(game.layers)} layers merged into {files} files "
        f"({written} written, {restored} restored); report {merge.report_path(paths, game).relative_to(paths.root)}"
    )
    return worktree


def main(paths: Paths, game_id: str) -> int:
    game = games.load(paths, game_id)
    if not dsd.is_current(paths, load_engine_config(paths)):
        raise CommandError("Kaleido's dsd isn't built: run ./kaleido bootstrap")
    worktree = prepare(paths, game)
    result = validate.run(paths, game, worktree)
    validate.report(paths, game, result)
    if result.problems:
        return 1
    defines = games.build_defines(paths, game)
    say(f"{game.id}: configure.py with {', '.join(sorted(defines)) or 'no defines'}")
    # A game's defines can change ARM9 main, so the stale secure-area values are allowed (R-27); DS mode ignores them
    options = enginebuild.Options(defines, allow_stale_secure_area=True, banner_title=game.title)
    enginebuild.configure(worktree, paths, options)
    say(f"{game.id}: ninja (about 10 minutes from clean)")
    out = paths.root / "build" / game.id
    result = enginebuild.ninja_until_clean(worktree, [enginebuild.ROM], out / "logs")
    enginebuild.report(result, say)
    if result.returncode != 0:
        say(f"{game.id}: FAILED")
        return 1
    over = chunks.check(worktree)
    for problem in over:
        say(f"{game.id}: {problem}")
    if over:
        say(f"{game.id}: FAILED, {len(over)} map chunks over their buffers, which the field would overrun")
        return 1
    say(f"{game.id}: every map chunk fits its map type's buffer")
    rom = out / f"kaleido-{game.id}.nds"
    shutil.copyfile(worktree / enginebuild.ROM, rom)
    say(f"{game.id}: {rom.relative_to(paths.root)}, SHA1 {enginebuild.rom_sha1(worktree)}")
    return 0
