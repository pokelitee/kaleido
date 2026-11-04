"""kaleido baseline: the patched engine with every define off and no layers must rebuild Black 2 byte for byte
(03-architecture.md §1). It builds in engine/pokebw2 itself, with every one of upstream's matching checks."""

from functools import partial

from kaleido import dsd, engine, enginebuild
from kaleido.config import Paths, load_engine_config
from kaleido.process import CommandError

say = partial(print, flush=True)


def main(paths: Paths) -> int:
    config = load_engine_config(paths)
    state = engine.state(paths)
    if not state.applied or state.dirty:
        raise CommandError("engine/pokebw2 isn't the pin with the current series: run ./kaleido bootstrap")
    if not dsd.is_current(paths, config):
        raise CommandError("Kaleido's dsd isn't built: run ./kaleido bootstrap")
    say("baseline: configure.py b2_us, every define off")
    enginebuild.configure(paths.engine, paths, enginebuild.Options())
    say("baseline: ninja with every matching check (about 10 minutes from clean)")
    result = enginebuild.ninja_until_clean(paths.engine, [], paths.root / "build" / "baseline" / "logs")
    enginebuild.report(result, say)
    sha1 = enginebuild.rom_sha1(paths.engine)
    if result.returncode != 0 or sha1 != config.black2_sha1:
        say(f"baseline: FAILED, ROM SHA1 {sha1}, expected {config.black2_sha1}")
        return 1
    say(f"baseline: matches Black 2, SHA1 {sha1}")
    return 0
