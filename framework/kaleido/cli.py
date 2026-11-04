"""The kaleido command."""

import argparse
import sys

from extractors.gba_gen3 import ExtractError
from kaleido import baseline, bootstrap, build, check, doctor, enginecompile, extract, games, patch, validate
from kaleido.config import ROOT, ConfigError, Paths
from kaleido.engine import EngineError
from kaleido.process import CommandError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kaleido", description="Kaleido's commands (docs/building.md)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="check the machine, engine, dsd, ROMs and tools")
    boot = commands.add_parser("bootstrap", help="set up the engine at the pin with Kaleido's patches, and dsd")
    boot.add_argument(
        "--force",
        action="store_true",
        help="re-apply the series even if engine/pokebw2 has commits bootstrap didn't make",
    )
    boot.add_argument("--skip-dsd", action="store_true", help="don't build Kaleido's dsd")
    commands.add_parser("check", help="the checks that need no ROM: ROM-content guard, layers and games, doc links")
    commands.add_parser("baseline", help="check that the patched engine, every define off, still builds Black 2")
    commands.add_parser("compile", help="compile the patched engine's C files for every define set; needs no ROM")
    for name, help_text in (
        ("extract", "run a game's extraction recipes on your source ROMs into build/<game>/"),
        ("merge", "merge a game's layers into its engine worktree, build/<game>/engine/"),
        ("validate", "merge a game's layers, then check the merged tree's cross-references"),
        ("build", "build a game's ROM into build/<game>/"),
        ("patch", "make dist/kaleido-<game>.xdelta from the built ROM, and check it"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("game", help="a directory of content/games/, such as firered")
        if name == "validate":
            command.add_argument(
                "--no-extract",
                action="store_true",
                help="skip extraction and check only the committed layer files, as CI does without source ROMs",
            )
    args = parser.parse_args(argv)
    paths = Paths(ROOT)
    try:
        if args.command == "doctor":
            return doctor.main(paths)
        if args.command == "bootstrap":
            return bootstrap.main(paths, force=args.force, skip_dsd=args.skip_dsd)
        if args.command == "check":
            return check.main(paths)
        if args.command == "baseline":
            return baseline.main(paths)
        if args.command == "compile":
            return enginecompile.main(paths)
        if args.command == "extract":
            return extract.main(paths, games.load(paths, args.game))
        if args.command == "merge":
            build.prepare(paths, games.load(paths, args.game))
            return 0
        if args.command == "validate":
            game = games.load(paths, args.game)
            problems = validate.run(paths, game, build.prepare(paths, game, extract_sources=not args.no_extract))
            validate.report(paths, game, problems)
            return 1 if problems else 0
        if args.command == "patch":
            return patch.main(paths, games.load(paths, args.game))
        return build.main(paths, args.game)
    except (ConfigError, EngineError, CommandError, ExtractError) as error:
        print(f"kaleido {args.command}: {error}", file=sys.stderr)
        return 1
