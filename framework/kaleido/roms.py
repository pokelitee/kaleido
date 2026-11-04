"""The player's ROMs: where Kaleido expects them, and the SHA1s it accepts.

The SHA1s are from docs/research/hardware-and-rom.md. Kaleido keeps the ROMs in the ignored orig/ at the repository's
root, under fixed names, and never in git."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RomSpec:
    file: str
    name: str
    sha1: str
    # The base ROM is needed for every build; the others only to extract their game's content
    required: bool


BASE = RomSpec("black2.nds", "Black 2 (USA, Europe)", "e51e6dfb8678a3d19dcd2a10691b96a569ca0abb", required=True)
SOURCES = [
    RomSpec("firered.gba", "FireRed (USA)", "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc", required=False),
]
# Other dumps that Kaleido recognizes, to name a ROM put under the wrong file name
KNOWN_SHA1S = {
    "e51e6dfb8678a3d19dcd2a10691b96a569ca0abb": "Black 2 (USA, Europe)",
    "b5d7490be7b415b8f1e672a53e978a9cc667e56a": "White 2 (USA, Europe)",
    "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc": "FireRed (USA)",
    "dd5945db9b930750cb39d00c84da8571feebf417": "FireRed (USA, Rev 1)",
    "574fa542ffebb14be69902d1d36f1ec0a4afd71e": "LeafGreen (USA)",
    "7862c67bdecbe21d1d69ce082ce34327e1c6ed5e": "LeafGreen (USA, Europe) (Rev 1)",
    "ea9bcae617fdf159b045185467ae58b2e4a48b9a": "Red (USA, Europe)",
    "d7037c83e1ae5b39bde3c30787637ba1d4c48ce2": "Blue (USA, Europe)",
    "cc7d03262ebfaf2f06772c1a480c7d9d5f4a38e1": "Yellow (USA, Europe)",
}
# Where pokebw2's configure.py looks for the base ROM, relative to the engine
ENGINE_BASEROM = "orig/baserom_b2_us.nds"


def identify(sha1: str) -> str | None:
    return KNOWN_SHA1S.get(sha1)
