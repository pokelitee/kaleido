"""The kaleido command."""
import argparse
import sys

from kaleido import bootstrap, doctor
from kaleido.config import ROOT, ConfigError, Paths
from kaleido.engine import EngineError
from kaleido.process import CommandError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kaleido", description="Kaleido's commands (docs/building.md)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="check the machine, engine, dsd, ROMs and tools")
    boot = commands.add_parser("bootstrap", help="set up the engine at the pin with Kaleido's patches, and dsd")
    boot.add_argument("--force", action="store_true",
                      help="re-apply the series even if engine/pokebw2 has commits bootstrap didn't make")
    boot.add_argument("--skip-dsd", action="store_true", help="don't build Kaleido's dsd")
    args = parser.parse_args(argv)
    paths = Paths(ROOT)
    try:
        if args.command == "doctor":
            return doctor.main(paths)
        return bootstrap.main(paths, force=args.force, skip_dsd=args.skip_dsd)
    except (ConfigError, EngineError, CommandError) as error:
        print(f"kaleido {args.command}: {error}", file=sys.stderr)
        return 1
