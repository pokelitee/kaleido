"""File and directory hashes, for ROMs and downloaded tools."""

import hashlib
from pathlib import Path

CHUNK = 1 << 20


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as file:
        while chunk := file.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(directory: Path) -> str:
    """The SHA256 of a directory's files: of one line per file, `<sha256>  <path>\\n` with the path relative to the
    directory in POSIX form, sorted by path. Kaleido's own definition, independent of tools such as sha256sum."""
    lines = sorted(
        (path.relative_to(directory).as_posix(), file_hash(path)) for path in directory.rglob("*") if path.is_file()
    )
    digest = hashlib.sha256()
    for relative, sha256 in lines:
        digest.update(f"{sha256}  {relative}\n".encode())
    return digest.hexdigest()
