"""kaleido build <game>: builds a game's ROM in its own engine worktree, build/<game>/engine/, with the game's
defines, and copies it to build/<game>/kaleido-<game>.nds (03-architecture.md §7)."""
import shutil
from functools import partial

from kaleido import dsd, engine, enginebuild, games
from kaleido.config import Paths, load_engine_config
from kaleido.process import CommandError

say = partial(print, flush=True)


def main(paths: Paths, game_id: str) -> int:
    config = load_engine_config(paths)
    game = games.load(paths, game_id)
    state = engine.state(paths)
    if not state.applied or state.dirty:
        raise CommandError("engine/pokebw2 isn't the pin with the current series: run ./kaleido bootstrap")
    if not dsd.is_current(paths, config):
        raise CommandError("Kaleido's dsd isn't built: run ./kaleido bootstrap")
    out = paths.root / "build" / game.id
    worktree = out / "engine"
    say(f"{game.id}: engine worktree {worktree.relative_to(paths.root)}")
    commit = engine.worktree(paths, worktree, sorted(config.tool_hashes))
    say(f"{game.id}: at {commit[:12]}; configure.py with {', '.join(sorted(game.defines)) or 'no defines'}")
    # A game's defines can change ARM9 main, so the stale secure-area values are allowed (R-27); DS mode ignores them
    enginebuild.configure(worktree, paths, enginebuild.Options(game.defines, allow_stale_secure_area=True))
    say(f"{game.id}: ninja (about 10 minutes from clean)")
    result = enginebuild.ninja_until_clean(worktree, [enginebuild.ROM], out / "logs")
    enginebuild.report(result, say)
    if result.returncode != 0:
        say(f"{game.id}: FAILED")
        return 1
    rom = out / f"kaleido-{game.id}.nds"
    shutil.copyfile(worktree / enginebuild.ROM, rom)
    say(f"{game.id}: {rom.relative_to(paths.root)}, SHA1 {enginebuild.rom_sha1(worktree)}")
    return 0
