import os
import shutil
import tempfile
import unittest
from pathlib import Path

from kaleido import doctor, patch
from kaleido.games import Game
from kaleido.process import run


class PatchArgumentsTest(unittest.TestCase):
    def test_encode_leaves_out_the_header_and_covers_the_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "base.nds"
            base.write_bytes(bytes(4096))
            small = patch.encode_arguments(base, Path("t.nds"), Path("p.xdelta"))
            base.write_bytes(bytes(patch.MIN_SOURCE_WINDOW + 4))
            large = patch.encode_arguments(base, Path("t.nds"), Path("p.xdelta"))
        self.assertIn("-A", small)
        self.assertEqual(small[small.index("-S") + 1], "none")
        self.assertEqual(small[small.index("-B") + 1], str(patch.MIN_SOURCE_WINDOW))
        self.assertEqual(large[large.index("-B") + 1], str(patch.MIN_SOURCE_WINDOW + 4))

    def test_checksums_name_each_file(self) -> None:
        text = patch.checksums(Game("firered", "FireRed", {}), "a" * 40, "b" * 40, "c" * 40)
        self.assertIn(f"{'b' * 40}  kaleido-firered.xdelta", text)
        self.assertIn("base ROM, Black 2 (USA, Europe)", text)

    def test_doctor_wants_the_checked_xdelta(self) -> None:
        self.assertEqual(doctor.check_xdelta(None).status, doctor.WARN)
        self.assertEqual(doctor.check_xdelta("3.1.0").status, doctor.WARN)
        self.assertEqual(doctor.check_xdelta(patch.XDELTA_VERSION).status, doctor.OK)


@unittest.skipUnless(shutil.which(patch.XDELTA), "xdelta3 isn't installed")
class XdeltaTest(unittest.TestCase):
    def test_the_patch_restores_the_target_and_ignores_file_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = bytes(range(256)) * 512
            target = base[:1000] + b"Kaleido" + base[1007:]
            patches = []
            for name in ("one", "two"):
                (root / name).mkdir()
                (root / name / f"{name}-base.nds").write_bytes(base)
                (root / name / f"{name}-game.nds").write_bytes(target)
                out = root / name / "p.xdelta"
                run(patch.encode_arguments(root / name / f"{name}-base.nds", root / name / f"{name}-game.nds", out))
                patches.append(out.read_bytes())
            self.assertEqual(patches[0], patches[1])
            run(patch.decode_arguments(root / "one" / "one-base.nds", root / "one" / "p.xdelta", root / "out.nds"))
            self.assertEqual((root / "out.nds").read_bytes(), target)


if __name__ == "__main__":
    unittest.main()
