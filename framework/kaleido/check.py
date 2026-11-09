"""kaleido check: the checks that need neither a ROM nor the engine, which CI runs on every push and pull request
(docs/plan/06-testing.md, layer 1):

- the ROM-content guard: no tracked file lies under orig/, extract/, build/ or dist/, has a ROM, save or patch
  extension, has the name of a file unpacked from a DS ROM or lies in its overlay directory, starts with a ROM's, a
  patch's or a Nitro file's header, or is larger than MAX_BYTES;
- every layer under content/ loads, with one provenance entry for each content file and recipes of a known kind with
  that kind's fields, and so does every game's config and layer stack;
- the links between the repository's Markdown files lead to files that exist."""

import re
from functools import partial
from pathlib import Path
from urllib.parse import unquote

from kaleido import extract, games, layers
from kaleido.config import ConfigError, Paths
from kaleido.process import run

FORBIDDEN_DIRECTORIES = ("orig/", "extract/", "build/", "dist/")
ROM_SUFFIXES = (".nds", ".srl", ".dsi", ".gba", ".gb", ".gbc")
# Saves, and emulator savestates, which hold the game's RAM: DeSmuME's .dst and slots .ds0-.ds9, melonDS's .mln
SAVE_SUFFIXES = (".sav", ".dsv", ".dst", ".mln", *(f".ds{slot}" for slot in range(10)))
PATCH_SUFFIXES = (".xdelta", ".bps", ".ips", ".ups")
FORBIDDEN_SUFFIXES = (*ROM_SUFFIXES, *SAVE_SUFFIXES, *PATCH_SUFFIXES)
# The files a DS ROM unpacks into, as ndstool and dsd name them; header_logo.png is the header's Nintendo logo
ROM_FILE_NAMES = frozenset(
    ("arm9.bin", "arm7.bin", "header.bin", "banner.bin", "y9.bin", "y7.bin", "dtcm.bin", "itcm.bin", "header_logo.png")
)
OVERLAY_DIRECTORIES = frozenset(("overlay", "arm9_overlays", "arm7_overlays"))
OVERLAY_FILE = re.compile(r"(ov\d{3}|overlay_\d{4})\.bin", re.IGNORECASE)
# Nitro files (an archive, a model, its textures and animations, 2D graphics, sound) start with their magic, then a
# byte-order mark, which keeps text that happens to start with the same letters from matching
NITRO_MAGICS = (
    b"NARC",
    b"BMD0",
    b"BTX0",
    b"BCA0",
    b"BTP0",
    b"BTA0",
    b"BMA0",
    b"BVA0",
    b"RGCN",
    b"RLCN",
    b"RCSN",
    b"RECN",
    b"RNAN",
    b"SDAT",
    b"SSEQ",
    b"SBNK",
    b"SWAR",
    b"SSAR",
    b"STRM",
)
NITRO_BYTE_ORDER_MARKS = (b"\xff\xfe", b"\xfe\xff")
PATCH_MAGICS = {b"PATCH": "an IPS patch", b"BPS1": "a BPS patch", b"UPS1": "a UPS patch"}
# A backstop for ROMs and dumps under other names; every file in the repository is far smaller. Raise it here, with
# the reason, if content ever needs larger files
MAX_BYTES = 1024 * 1024
HEADER_BYTES = 0x200
VCDIFF_MAGIC = bytes([0xD6, 0xC3, 0xC4, 0x00])
GITLINK = "160000"

LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:", re.IGNORECASE)

say = partial(print, flush=True)


def tracked_files(root: Path) -> list[str]:
    """The files in git's index, as POSIX paths; submodules (gitlinks) left out."""
    files = []
    for entry in run(["git", "ls-files", "--stage", "-z"], cwd=root).split("\0"):
        if entry:
            meta, path = entry.split("\t", 1)
            if meta.split()[0] != GITLINK:
                files.append(path)
    return files


def _crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def rom_kind(header: bytes, size: int) -> str | None:
    """What a file's first bytes say it is, from the header checks each console's boot code makes (GBATEK; Pan Docs
    for the Game Boy); None for anything else."""
    if header.startswith(VCDIFF_MAGIC):
        return "a VCDIFF (xdelta) patch"
    for magic, kind in PATCH_MAGICS.items():
        if header.startswith(magic):
            return kind
    if header[:4] in NITRO_MAGICS and header[4:6] in NITRO_BYTE_ORDER_MARKS:
        return f"a Nitro {header[:4].decode()} file"
    if (
        len(header) >= 0x160
        and header[0x15C:0x15E] == b"\x56\xcf"
        and _crc16(header[:0x15E]) == int.from_bytes(header[0x15E:0x160], "little")
    ):
        return "a DS ROM"
    if (
        len(header) >= 0xC0
        and header[0x03] == 0xEA
        and header[0xB2] == 0x96
        and (-(sum(header[0xA0:0xBD]) + 0x19)) & 0xFF == header[0xBD]
    ):
        return "a GBA ROM"
    if len(header) >= 0x150 and header[0x148] <= 8 and size == 0x8000 << header[0x148]:
        checksum = 0
        for byte in header[0x134:0x14D]:
            checksum = (checksum - byte - 1) & 0xFF
        if checksum == header[0x14D]:
            return "a Game Boy ROM"
    return None


def guard(root: Path, files: list[str]) -> list[str]:
    problems = []
    for path in files:
        file = root / path
        if path.startswith(FORBIDDEN_DIRECTORIES):
            problems.append(f"{path}: nothing under {path.split('/')[0]}/ is ever committed")
        if path.lower().endswith(FORBIDDEN_SUFFIXES):
            problems.append(f"{path}: a ROM, save, patch or savestate file by its extension")
        *directories, name = path.lower().split("/")
        if name in ROM_FILE_NAMES or OVERLAY_FILE.fullmatch(name) or OVERLAY_DIRECTORIES.intersection(directories):
            problems.append(f"{path}: a file unpacked from a DS ROM by its name or directory")
        if not file.is_file():
            continue
        size = file.stat().st_size
        if size > MAX_BYTES:
            problems.append(f"{path}: {size} bytes, over the {MAX_BYTES}-byte limit")
        with file.open("rb") as stream:
            kind = rom_kind(stream.read(HEADER_BYTES), size)
        if kind:
            problems.append(f"{path}: starts like {kind}")
    return problems


def layer_problems(paths: Paths) -> list[str]:
    # Each error names its layer or file, and a layer two games use fails once
    problems: dict[str, None] = {}
    try:
        game_list = games.load_all(paths)
    except ConfigError as error:
        return [str(error)]
    for game in game_list:
        try:
            layers.load_stack(paths, list(game.layers))
            games.build_defines(paths, game)
        except ConfigError as error:
            problems[str(error)] = None
    for directory in layers.DIRECTORIES.values():
        for manifest in sorted((paths.root / "content" / directory).glob("*/layer.json")):
            try:
                layer = layers.load(paths, f"{directory}/{manifest.parent.name}")
                for recipe in layer.recipes():
                    extract.read_recipe(layer, recipe)
            except ConfigError as error:
                problems[str(error)] = None
    return list(problems)


def broken_links(root: Path, files: list[str]) -> list[str]:
    """Links in Markdown files to paths that don't exist. Links with a scheme (https:, mailto:) and links to a heading
    of the same file aren't checked, nor is anything in code."""
    problems = []
    for path in files:
        if not path.endswith(".md") or not (root / path).is_file():
            continue
        text = INLINE_CODE.sub("", FENCE.sub("", (root / path).read_text(encoding="utf-8")))
        for target in LINK.findall(text):
            if SCHEME.match(target) or target.startswith("#"):
                continue
            relative = unquote(target.split("#", 1)[0])
            resolved = root / relative.lstrip("/") if relative.startswith("/") else (root / path).parent / relative
            if not resolved.exists():
                problems.append(f"{path}: link to {target}, which doesn't exist")
    return problems


def main(paths: Paths) -> int:
    files = tracked_files(paths.root)
    sections = (
        ("ROM-content guard", guard(paths.root, files), f"{len(files)} tracked files"),
        ("layers and games", layer_problems(paths), "every layer and game loads"),
        ("links", broken_links(paths.root, files), "every link between Markdown files resolves"),
    )
    failed = 0
    for name, problems, success in sections:
        if problems:
            failed += len(problems)
            say(f"check: {name}: {len(problems)} problems")
            for problem in problems:
                say(f"  {problem}")
        else:
            say(f"check: {name}: ok, {success}")
    return 1 if failed else 0
