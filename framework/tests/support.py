"""Synthetic repositories for the tests: a stand-in upstream engine and a Kaleido checkout around it."""
import os
import subprocess
import tempfile
from pathlib import Path

GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@localhost", "GIT_COMMITTER_NAME": "Test",
           "GIT_COMMITTER_EMAIL": "test@localhost", "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
           "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_CONFIG_NOSYSTEM": "1"}


def git(*args: str, cwd: Path) -> str:
    env = {**os.environ, **GIT_ENV, "GIT_ALLOW_PROTOCOL": "file"}
    return subprocess.run(["git", "-c", "protocol.file.allow=always", *args], cwd=cwd, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


class Fixture:
    """An upstream repository with one commit (the pin) and a Kaleido checkout whose engine/pokebw2 points at it,
    with engine/patches/ holding patches made from further upstream commits."""

    def __init__(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        base = Path(self._temp.name)
        self.upstream = base / "upstream"
        self.upstream.mkdir()
        git("init", "-q", "-b", "main", cwd=self.upstream)
        (self.upstream / "configure.py").write_text("print('engine')\n")
        git("add", "-A", cwd=self.upstream)
        git("commit", "-q", "-m", "pin", cwd=self.upstream)
        self.pin = git("rev-parse", "HEAD", cwd=self.upstream)
        self.root = base / "kaleido"
        self.root.mkdir()
        git("init", "-q", "-b", "main", cwd=self.root)
        (self.root / "engine" / "patches").mkdir(parents=True)
        git("submodule", "add", "-q", self.upstream.as_uri(), "engine/pokebw2", cwd=self.root)
        git("commit", "-q", "-m", "engine", cwd=self.root)

    def make_patch(self, name: str, content: str) -> Path:
        """Commits a change upstream (after the pin), exports it into engine/patches/, then removes the commit."""
        (self.upstream / f"{name}.txt").write_text(content)
        git("add", "-A", cwd=self.upstream)
        git("commit", "-q", "-m", f"add {name}", cwd=self.upstream)
        patches = self.root / "engine" / "patches"
        number = len(list(patches.glob("*.patch"))) + 1
        out = git("format-patch", "--zero-commit", "--no-signature", f"--start-number={number}", "-o", str(patches),
                  "HEAD~1..HEAD", cwd=self.upstream)
        git("reset", "-q", "--hard", "HEAD~1", cwd=self.upstream)
        return Path(out.splitlines()[-1])

    def cleanup(self) -> None:
        self._temp.cleanup()
