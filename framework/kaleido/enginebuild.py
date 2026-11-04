"""Building with the engine: upstream's configure.py with Kaleido's dsd and options, then ninja, run again until
nothing is left to compile."""
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kaleido import dsd
from kaleido.config import Paths
from kaleido.hashing import file_hash
from kaleido.process import CommandError, run

ROM = "build/pokeblack2_us.nds"
# ninja runs at most this many times. Upstream's depfiles name generated headers by absolute path, so a run that
# regenerates a header leaves the objects that include it stale until the next run (R-28)
MAX_NINJA_RUNS = 3
COMPILE_STEP = re.compile(r"^\[\d+/\d+\] Compiling ", re.MULTILINE)

# Runs a command in a directory, writing its output to the log if one is given: (exit code, output)
Runner = Callable[[list[str], Path, Path | None], tuple[int, str]]


@dataclass(frozen=True)
class Options:
    """What a build passes to configure.py beyond the version and dsd."""

    defines: dict[str, str] = field(default_factory=dict)
    # Needed whenever ARM9 main changes, code or data (R-27); never for the baseline
    allow_stale_secure_area: bool = False

    def arguments(self) -> list[str]:
        args = []
        for name, value in sorted(self.defines.items()):
            args += ["--define", f"{name}={value}" if value else name]
        if self.allow_stale_secure_area:
            args.append("--allow-stale-secure-area")
        return args


@dataclass(frozen=True)
class NinjaResult:
    returncode: int
    # How many files each run compiled
    compiled: list[int]
    log: Path


def configure(engine_dir: Path, paths: Paths, options: Options) -> None:
    executable = dsd.binary(paths)
    if not dsd.has_flag(executable):
        raise CommandError("Kaleido's dsd isn't built: run ./kaleido bootstrap")
    run([sys.executable, "configure.py", "b2_us", "--dsd", str(executable), *options.arguments()], cwd=engine_dir)


def compile_steps(ninja_output: str) -> int:
    return len(COMPILE_STEP.findall(ninja_output))


def _run(args: list[str], cwd: Path, log: Path | None) -> tuple[int, str]:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if log is not None:
        log.write_text(output, encoding="utf-8")
    return result.returncode, output


def ninja_until_clean(engine_dir: Path, targets: list[str], logs: Path, runner: Runner = _run) -> NinjaResult:
    """Runs ninja, and again while a dry run still has something to compile. A failed run is retried only then, since
    stale objects can be what failed it."""
    logs.mkdir(parents=True, exist_ok=True)
    compiled: list[int] = []
    returncode, log = 1, logs / "ninja-1.log"
    for attempt in range(1, MAX_NINJA_RUNS + 1):
        log = logs / f"ninja-{attempt}.log"
        returncode, output = runner(["ninja", *targets], engine_dir, log)
        compiled.append(compile_steps(output))
        _, dry_run = runner(["ninja", "-n", *targets], engine_dir, None)
        if not compile_steps(dry_run):
            break
    return NinjaResult(returncode, compiled, log)


def failed_steps(log: Path) -> list[str]:
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    return [line.removeprefix("FAILED: ") for line in lines if line.startswith("FAILED: ")]


def rom_sha1(engine_dir: Path) -> str | None:
    rom = engine_dir / ROM
    return file_hash(rom, "sha1") if rom.exists() else None


def report(result: NinjaResult, say: Callable[[str], None]) -> None:
    runs = ", ".join(f"run {i} compiled {count}" for i, count in enumerate(result.compiled, 1))
    say(f"ninja: exit {result.returncode} ({runs}); log {result.log}")
    for step in failed_steps(result.log)[:10]:
        say(f"  failed: {step}")
