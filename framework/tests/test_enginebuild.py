import tempfile
import unittest
from pathlib import Path

from kaleido import enginebuild
from kaleido.enginebuild import Options


class OptionsTest(unittest.TestCase):
    def test_defines_are_sorted_and_valued(self) -> None:
        options = Options({"KALEIDO_B": "", "KALEIDO_A": "0x1"}, allow_stale_secure_area=True)
        self.assertEqual(
            options.arguments(), ["--define", "KALEIDO_A=0x1", "--define", "KALEIDO_B", "--allow-stale-secure-area"]
        )

    def test_the_baseline_passes_nothing(self) -> None:
        self.assertEqual(Options().arguments(), [])

    def test_a_title_passes_its_lines_joined_by_a_literal_backslash_n(self) -> None:
        options = Options(banner_title=("Kaleido", "FireRed"))
        self.assertEqual(options.arguments(), ["--banner-title", "Kaleido\\nFireRed"])


class FakeNinja:
    """Each real run compiles the next count in `runs`; a dry run shows the count after it as still to compile."""

    def __init__(self, runs: list[int], returncodes: list[int]) -> None:
        self.runs, self.returncodes, self.calls = runs, returncodes, []

    def __call__(self, args: list[str], cwd: Path, log: Path | None) -> tuple[int, str]:
        self.calls.append(args)
        real = sum(1 for call in self.calls if "-n" not in call)
        if "-n" in args:
            pending = self.runs[real] if real < len(self.runs) else 0
            return 0, "".join(f"[{i}/9] Compiling src/f{i}.c\n" for i in range(pending))
        output = "".join(f"[{i}/9] Compiling src/f{i}.c\n" for i in range(self.runs[real - 1]))
        if log is not None:
            log.write_text(output + ("FAILED: build/x.ok\n" if self.returncodes[real - 1] else ""))
        return self.returncodes[real - 1], output


class NinjaUntilCleanTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.logs = Path(self._temp.name) / "logs"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_one_run_when_nothing_is_left(self) -> None:
        result = enginebuild.ninja_until_clean(Path("."), [], self.logs, FakeNinja([5], [0]))
        self.assertEqual((result.returncode, result.compiled), (0, [5]))

    def test_runs_again_while_objects_are_stale(self) -> None:
        # R-28: the first run regenerates a header and fails a check on stale objects; the second compiles them
        result = enginebuild.ninja_until_clean(Path("."), [], self.logs, FakeNinja([1, 197], [1, 0]))
        self.assertEqual((result.returncode, result.compiled), (0, [1, 197]))
        self.assertEqual(result.log.name, "ninja-2.log")

    def test_gives_up_after_three_runs(self) -> None:
        result = enginebuild.ninja_until_clean(Path("."), [], self.logs, FakeNinja([1, 1, 1, 1], [1, 1, 1, 1]))
        self.assertEqual(len(result.compiled), enginebuild.MAX_NINJA_RUNS)
        self.assertEqual(enginebuild.failed_steps(result.log), ["build/x.ok"])

    def test_counts_only_compile_steps(self) -> None:
        output = "[1/3] Generating x.h\n[2/3] Compiling src/a.c\n[3/3] Linking main\n"
        self.assertEqual(enginebuild.compile_steps(output), 1)


if __name__ == "__main__":
    unittest.main()
