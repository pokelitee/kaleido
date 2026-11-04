"""kaleido patch <game>: the xdelta patch players apply to their own Black 2, dist/kaleido-<game>.xdelta, and its
checksums (03-architecture.md §7). It contains the game's extracted content (Q1), so it never goes in git.

The patch is the same however the files are named and wherever they are: xdelta3 3.0.11 otherwise writes the files'
names into the patch's application header, and -A leaves the header out (verified 2026-11-04). The source window
covers the whole base ROM. Before writing the checksums, the patch is applied to the base ROM, and the result must be
the built ROM."""
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path

from kaleido.config import ConfigError, Paths
from kaleido.games import Game
from kaleido.hashing import file_hash
from kaleido.process import CommandError, run
from kaleido.roms import BASE

XDELTA = "xdelta3"
# The version whose output Kaleido has checked; doctor warns about others
XDELTA_VERSION = "3.0.11"
# xdelta3 refuses a smaller source window (-B)
MIN_SOURCE_WINDOW = 512 * 1024

say = partial(print, flush=True)


def encode_arguments(base: Path, target: Path, out: Path) -> list[str]:
    window = max(base.stat().st_size, MIN_SOURCE_WINDOW)
    return [XDELTA, "-e", "-9", "-S", "none", "-A", "-B", str(window), "-f", "-s", str(base), str(target), str(out)]


def decode_arguments(base: Path, patch: Path, out: Path) -> list[str]:
    return [XDELTA, "-d", "-f", "-s", str(base), str(patch), str(out)]


def version() -> str | None:
    """xdelta3's version, from `xdelta3 -V` (which it prints to standard error)."""
    if not shutil.which(XDELTA):
        return None
    result = subprocess.run([XDELTA, "-V"], capture_output=True, text=True)
    text = (result.stdout + result.stderr).split()
    return text[text.index("version") + 1].rstrip(",") if "version" in text else "unknown"


def checksums(game: Game, base_sha1: str, patch_sha1: str, rom_sha1: str) -> str:
    return (f"# Kaleido {game.name}: apply kaleido-{game.id}.xdelta to your own {BASE.name} ROM with xdelta3\n"
            f"{base_sha1}  base ROM, {BASE.name}\n"
            f"{patch_sha1}  kaleido-{game.id}.xdelta\n"
            f"{rom_sha1}  kaleido-{game.id}.nds, the result\n")


def make(paths: Paths, game: Game) -> tuple[Path, str]:
    """Writes dist/kaleido-<game>.xdelta and .sha1 after checking the patch. Returns the patch and the ROM's SHA1."""
    if not shutil.which(XDELTA):
        raise CommandError("xdelta3 not found: sudo apt install xdelta3")
    base = paths.orig / BASE.file
    if not base.exists() or file_hash(base, "sha1") != BASE.sha1:
        raise ConfigError(f"orig/{BASE.file} must be your own {BASE.name} dump ({BASE.sha1}): ./kaleido doctor")
    rom = paths.root / "build" / game.id / f"kaleido-{game.id}.nds"
    if not rom.exists():
        raise ConfigError(f"no {rom.relative_to(paths.root)}: run ./kaleido build {game.id} first")
    dist = paths.root / "dist"
    dist.mkdir(exist_ok=True)
    patch = dist / f"kaleido-{game.id}.xdelta"
    run(encode_arguments(base, rom, patch))
    rom_sha1 = file_hash(rom, "sha1")
    with tempfile.TemporaryDirectory(dir=paths.root / "build") as temp:
        applied = Path(temp) / "applied.nds"
        run(decode_arguments(base, patch, applied))
        if file_hash(applied, "sha1") != rom_sha1:
            patch.unlink()
            raise CommandError(f"the patch applied to {BASE.file} doesn't give {rom.name}; nothing written")
    patch_sha1 = file_hash(patch, "sha1")
    (dist / f"kaleido-{game.id}.sha1").write_text(checksums(game, BASE.sha1, patch_sha1, rom_sha1), encoding="utf-8")
    return patch, rom_sha1


def main(paths: Paths, game: Game) -> int:
    found = version()
    if found and found != XDELTA_VERSION:
        say(f"xdelta3 {found}: Kaleido has checked {XDELTA_VERSION}'s output only; the patch may differ elsewhere")
    patch, rom_sha1 = make(paths, game)
    say(f"{game.id}: {patch.relative_to(paths.root)} ({patch.stat().st_size} bytes), SHA1 {file_hash(patch, 'sha1')}")
    say(f"{game.id}: applying it to {BASE.file} gives the built ROM, SHA1 {rom_sha1}; checksums in "
        f"dist/kaleido-{game.id}.sha1")
    return 0
