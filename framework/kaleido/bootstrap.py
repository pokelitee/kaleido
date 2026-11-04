"""kaleido bootstrap: checks the engine out at the pin, applies Kaleido's patch series, links the base ROM into the
engine and builds Kaleido's dsd. Each step is skipped when it is already done."""
from kaleido import dsd, engine
from kaleido.config import Paths, load_engine_config


def main(paths: Paths, force: bool = False, skip_dsd: bool = False) -> int:
    config = load_engine_config(paths)
    print("engine: checking out pokebw2 at the pin")
    engine.fetch(paths)
    applied = engine.apply_series(paths, force=force)
    count = len(engine.series(paths))
    print(f"engine: {'applied' if applied else 'already has'} the series ({count} patches) on branch {engine.BRANCH}")
    print(f"base ROM: {engine.link_base_rom(paths)}")
    if skip_dsd:
        print("dsd: skipped")
    else:
        if not dsd.is_current(paths, config):
            print("dsd: building Kaleido's dsd (about 35 minutes the first time)")
        print(f"dsd: {'built' if dsd.build(paths, config) else 'already built'}, {dsd.binary(paths)}")
    print("Next: ./kaleido doctor")
    return 0
