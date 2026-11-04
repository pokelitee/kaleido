import hashlib
import tempfile
import unittest
from pathlib import Path

from kaleido.hashing import file_hash, tree_digest


class TreeDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.base = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def make(self, name: str, files: dict[str, bytes]) -> Path:
        directory = self.base / name
        for relative, content in files.items():
            (directory / relative).parent.mkdir(parents=True, exist_ok=True)
            (directory / relative).write_bytes(content)
        return directory

    def test_is_the_sha256_of_sorted_hash_and_path_lines(self) -> None:
        directory = self.make("tree", {"b.txt": b"B", "a/c.bin": b"C"})
        lines = "".join(
            f"{hashlib.sha256(content).hexdigest()}  {path}\n"
            for path, content in sorted({"b.txt": b"B", "a/c.bin": b"C"}.items())
        )
        self.assertEqual(tree_digest(directory), hashlib.sha256(lines.encode()).hexdigest())

    def test_does_not_depend_on_creation_order(self) -> None:
        first = self.make("first", {"x": b"1", "y/z": b"2"})
        second = self.make("second", {"y/z": b"2", "x": b"1"})
        self.assertEqual(tree_digest(first), tree_digest(second))

    def test_changes_with_a_name_or_a_byte(self) -> None:
        reference = tree_digest(self.make("ref", {"x": b"1"}))
        self.assertNotEqual(tree_digest(self.make("renamed", {"w": b"1"})), reference)
        self.assertNotEqual(tree_digest(self.make("edited", {"x": b"2"})), reference)

    def test_file_hash_takes_an_algorithm(self) -> None:
        path = self.make("file", {"rom": b"synthetic"}) / "rom"
        self.assertEqual(file_hash(path, "sha1"), hashlib.sha1(b"synthetic").hexdigest())
        self.assertEqual(file_hash(path), hashlib.sha256(b"synthetic").hexdigest())


if __name__ == "__main__":
    unittest.main()
