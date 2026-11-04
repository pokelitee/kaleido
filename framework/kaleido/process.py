"""Running other programs."""
import subprocess
from pathlib import Path


class CommandError(Exception):
    pass


def run(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    """Runs a command and returns its standard output; a failure raises CommandError with its standard error."""
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-5:]
        raise CommandError(f"{' '.join(args)} failed ({result.returncode}): " + " / ".join(detail))
    return result.stdout


def stream(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    """Runs a long command with its output shown as it goes; a failure raises CommandError."""
    returncode = subprocess.run(args, cwd=cwd, env=env).returncode
    if returncode != 0:
        raise CommandError(f"{' '.join(args)} failed ({returncode})")
