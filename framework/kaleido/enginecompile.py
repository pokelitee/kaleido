"""kaleido compile: compiles every C file of the patched engine for Black 2 with upstream's
tools/decomp/compile_all.py, once with every define off and once for each game's defines. It needs no ROM, so CI runs
it; only a build with the ROMs shows that the result matches or runs (docs/plan/06-testing.md)."""

import sys
from functools import partial

from kaleido import engine, enginebuild, games
from kaleido.config import Paths
from kaleido.process import CommandError, stream

VERSION = "b2_us"

say = partial(print, flush=True)


def define_sets(game_list: list[games.Game]) -> list[tuple[list[str], dict[str, str]]]:
    """Each distinct set of defines with the names that build with it: the baseline's (none) first, then each game's
    in turn, so games that share a set compile once."""
    sets: list[tuple[list[str], dict[str, str]]] = [(["baseline"], {})]
    for game in game_list:
        for names, defines in sets:
            if defines == game.defines:
                names.append(game.id)
                break
        else:
            sets.append(([game.id], dict(game.defines)))
    return sets


def main(paths: Paths) -> int:
    state = engine.state(paths)
    if not state.applied or state.dirty:
        raise CommandError("engine/pokebw2 isn't the pin with the current series: run ./kaleido bootstrap")
    failed = []
    for names, defines in define_sets(games.load_all(paths)):
        label = ", ".join(names)
        arguments = enginebuild.Options(defines).arguments()
        say(f"compile: {label}: compile_all.py --version {VERSION} {' '.join(arguments) or '(every define off)'}")
        try:
            stream([sys.executable, "tools/decomp/compile_all.py", "--version", VERSION, *arguments], cwd=paths.engine)
        except CommandError:
            failed.append(label)
    if failed:
        say(f"compile: FAILED for {'; '.join(failed)}")
        return 1
    say("compile: every define set compiles")
    return 0
