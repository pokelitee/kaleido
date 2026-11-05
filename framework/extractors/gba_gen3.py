"""FireRed and LeafGreen (GBA, Gen 3): wild encounters, found by structure and named by the ROM's own text (E8,
docs/research/e8-extract-encounters.md).

The formats, from reading pret/pokefirered at ce6406d8 (nothing copied):
- wild encounter headers: 20 bytes each (map group, map number, two bytes of padding, then pointers to the land, water,
  rock smash and fishing groups, or 0), ended by map group and number 0xFF;
- a group: an encounter rate (u8, then padding) and a pointer to its slots; a slot: minimum and maximum level (u8) and
  species (u16); 12 land slots;
- a map header: 28 bytes, whose byte 0x14 is its map section; the map groups: a table of pointers to tables of pointers
  to map headers;
- the map section names: a table of pointers to strings, one per section from the first Kanto section,
  KANTO_MAPSEC_START, up to MAPSEC_NONE (0xC5), so KANTO_MAPSEC_COUNT of them. The owner's FireRed holds exactly one
  such run; a longer run of names that also starts with Pallet Town (the region map's) is another table;
- text: capital letters from 0xBB, digits from 0xA1, space 0x00, ended by 0xFF; the rest of CHARACTERS from pret's
  charmap.txt, read on 2026-11-04. In messages, 0xFA scrolls a line and 0xFB starts a new box; 0xFD and a byte is a
  name (the player's, the rival's or a string the script buffered); 0xFC and a code is a command whose arguments'
  length the code gives (GetExtCtrlCodeLength), the font command 0x06 taking one byte;
- species 1 to 251 are in national Pokédex order."""

import struct
from array import array
from dataclasses import dataclass

ROM_BASE = 0x08000000
KANTO_MAPSEC_START = 0x58
KANTO_MAPSEC_COUNT = 109
HEADER_SIZE, MAP_HEADER_SIZE, LAND_SLOTS = 20, 28, 12
MAP_SECTION_OFFSET = 0x14
LAST_NATIONAL_ORDER_SPECIES = 251
STRING_END = 0xFF
NEWLINE, SCROLL, NEW_BOX = 0xFE, 0xFA, 0xFB
NAME, COMMAND, FONT = 0xFD, 0xFC, 0x06
# Gen 5 shows a name through a word set buffer that the script fills before the message. Black 2's scripts put the
# player's name in buffer 0 and the rival's in buffer 1; the script's own strings (Gen 3's STR_VAR_1 to 3) take 2 to 4.
# The engine expands a placeholder by its buffer alone (wordset.c), so every name is a word placeholder, {0100:n}
NAME_BUFFERS = {0x01: 0, 0x06: 1, 0x02: 2, 0x03: 3, 0x04: 4}
# The characters of the English text encoding. Names and plain lines (decode) hold only these; messages (message) may
# also hold the control codes above
CHARACTERS = {
    0x00: " ", 0x1B: "é", 0x2D: "&", 0x2E: "+", 0x5C: "(", 0x5D: ")", 0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-",
    0xB0: "…", 0xB1: "“", 0xB2: "”", 0xB3: "‘", 0xB4: "’", 0xB5: "♂", 0xB6: "♀", 0xB8: ",", 0xBA: "/", 0xF0: ":",
    NEWLINE: "\n",
    **{0xA1 + i: str(i) for i in range(10)},
    **{0xBB + i: chr(ord("A") + i) for i in range(26)},
    **{0xD5 + i: chr(ord("a") + i) for i in range(26)},
}  # fmt: skip
# A map section's name fits on the region map: a few words, one line
MAX_NAME = 24


class ExtractError(Exception):
    pass


@dataclass(frozen=True)
class Slot:
    species: int
    min_level: int
    max_level: int


@dataclass(frozen=True)
class LandEncounters:
    rate: int
    slots: tuple[Slot, ...]


class Rom:
    def __init__(self, data: bytes):
        self.data = data

    def is_pointer(self, value: int) -> bool:
        return ROM_BASE <= value < ROM_BASE + len(self.data)

    def u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self.data, offset)[0]

    def at(self, pointer: int) -> int:
        return pointer - ROM_BASE

    def pointers_to(self, offset: int) -> list[int]:
        """Every 4-aligned offset that holds a pointer to offset."""
        needle = struct.pack("<I", ROM_BASE + offset)
        found, start = [], 0
        while (i := self.data.find(needle, start)) != -1:
            if i % 4 == 0:
                found.append(i)
            start = i + 1
        return found


ENCODING = {character: byte for byte, character in CHARACTERS.items()}


def encode(text: str) -> bytes:
    """text in the source's encoding, ended by 0xFF: the inverse of decode."""
    out = bytearray()
    for c in text:
        if c not in ENCODING:
            raise ExtractError(f"no encoding for {c!r}")
        out.append(ENCODING[c])
    return bytes(out) + bytes([STRING_END])


def decode(data: bytes, offset: int, limit: int = 1024) -> str:
    """The string at offset, up to its 0xFF; an unknown byte, a control code or a missing end is an error."""
    out = []
    for i in range(offset, min(offset + limit, len(data))):
        byte = data[i]
        if byte == STRING_END:
            return "".join(out)
        if byte not in CHARACTERS:
            raise ExtractError(f"byte {byte:#04x} at {i:#x} isn't a character Kaleido decodes")
        out.append(CHARACTERS[byte])
    raise ExtractError(f"no end of string within {limit} bytes of {offset:#x}")


def message(data: bytes, offset: int, limit: int = 1024) -> str:
    """The message at offset as a line of Gen 5 text, escaped as pokebw2's res/text/ files are: a line break, a scroll
    and a new box become `\\n`, `{be00}\\n` and `{be01}\\n` (the stream's scroll and clear, printsys.c), a name becomes
    its buffer's placeholder, and a font change is dropped, Gen 5 having no voice fonts. Any other control code is an
    error."""
    out, i = [], offset
    end = min(offset + limit, len(data))
    while i < end:
        byte = data[i]
        argument = data[i + 1] if i + 1 < end else None
        if byte == STRING_END:
            return "".join(out)
        if byte == NEWLINE:
            out.append("\\n")
        elif byte == SCROLL:
            out.append("{be00}\\n")
        elif byte == NEW_BOX:
            out.append("{be01}\\n")
        elif byte == NAME and argument in NAME_BUFFERS:
            out.append(f"{{0100:{NAME_BUFFERS[argument]}}}")
            i += 1
        elif byte == COMMAND and argument == FONT:
            i += 2
        elif byte in CHARACTERS:
            out.append(CHARACTERS[byte])
        else:
            code = f"{byte:#04x}" + (f" {argument:#04x}" if byte in (NAME, COMMAND) and argument is not None else "")
            raise ExtractError(f"{code} at {i:#x} isn't a character or control code Kaleido converts")
        i += 1
    raise ExtractError(f"no end of message within {limit} bytes of {offset:#x}")


def _is_name(data: bytes, offset: int) -> bool:
    try:
        name = decode(data, offset, MAX_NAME + 1)
    except ExtractError:
        return False
    return bool(name.strip()) and "\n" not in name


def section_names(rom: Rom) -> list[str]:
    """The map section names, the first being KANTO_MAPSEC_START's: the one run of exactly KANTO_MAPSEC_COUNT pointers
    to one-line names, so no name has to be known to find them."""
    words = array("I", rom.data[: len(rom.data) // 4 * 4])
    low, high = ROM_BASE, ROM_BASE + len(rom.data)
    tables, start, count = [], 0, 0
    for index, value in enumerate(words):
        if low <= value < high and _is_name(rom.data, value - ROM_BASE):
            if count == 0:
                start = index
            count += 1
            continue
        if count == KANTO_MAPSEC_COUNT:
            tables.append(start)
        count = 0
    if count == KANTO_MAPSEC_COUNT:
        tables.append(start)
    if len(tables) != 1:
        raise ExtractError(f"{len(tables)} tables of {KANTO_MAPSEC_COUNT} map section names, not one")
    return [decode(rom.data, rom.at(words[tables[0] + i])) for i in range(KANTO_MAPSEC_COUNT)]


def _is_wild_header(rom: Rom, offset: int) -> bool:
    if rom.data[offset + 2 : offset + 4] != b"\0\0":
        return False
    fields = [rom.u32(offset + 4 + 4 * i) for i in range(4)]
    return any(fields) and all(f == 0 or (rom.is_pointer(f) and f % 4 == 0) for f in fields)


def find_wild_headers(rom: Rom) -> int:
    """The offset of the wild encounter headers: the longest run of headers that a 0xFF 0xFF entry ends."""
    best, best_count, offset = None, 0, 0
    while offset + HEADER_SIZE <= len(rom.data):
        count = 0
        while offset + (count + 1) * HEADER_SIZE <= len(rom.data) and _is_wild_header(
            rom, offset + count * HEADER_SIZE
        ):
            count += 1
        end = offset + count * HEADER_SIZE
        if count and rom.data[end : end + 2] == b"\xff\xff":
            if count > best_count:
                best, best_count = offset, count
            offset = end + 4
        else:
            # A run without the terminator can begin a few bytes before a real table and overlap its start, so the
            # scan goes on from the next word, not from the run's end
            offset += 4
    if best is None:
        raise ExtractError("no wild encounter headers found")
    return best


def map_section(rom: Rom, name: str) -> int:
    """The map section that the ROM names `name`: its place in the table of names, from KANTO_MAPSEC_START."""
    names = section_names(rom)
    if name not in names:
        raise ExtractError(f"no map section named {name!r}")
    return KANTO_MAPSEC_START + names.index(name)


def _is_map_header(rom: Rom, offset: int) -> bool:
    if offset % 4 or offset < 0 or offset + MAP_HEADER_SIZE > len(rom.data):
        return False
    layout, events, scripts, connections = (rom.u32(offset + 4 * i) for i in range(4))
    return all(rom.is_pointer(p) for p in (layout, events, scripts)) and (
        connections == 0 or rom.is_pointer(connections)
    )


def _points_to_map_header(rom: Rom, slot: int) -> bool:
    value = rom.u32(slot)
    return rom.is_pointer(value) and _is_map_header(rom, rom.at(value))


def _points_to_map_group(rom: Rom, slot: int) -> bool:
    value = rom.u32(slot)
    return rom.is_pointer(value) and _points_to_map_header(rom, rom.at(value))


def map_ids(rom: Rom, section: int) -> list[tuple[int, int]]:
    """The (group, number) of every map in a section: a map's number is its place in its group's table of headers, and
    its group is that table's place in the table of groups."""
    ids = set()
    for offset in range(0, len(rom.data) - MAP_HEADER_SIZE, 4):
        if rom.data[offset + MAP_SECTION_OFFSET] != section or not _is_map_header(rom, offset):
            continue
        for slot in rom.pointers_to(offset):
            # The groups' tables lie back to back, so a group starts where the table of groups points
            group_start, group_slots = slot, []
            while True:
                group_slots = [s for s in rom.pointers_to(group_start) if _points_to_map_group(rom, s)]
                if group_slots or group_start < 4 or not _points_to_map_header(rom, group_start - 4):
                    break
                group_start -= 4
            for group_slot in group_slots:
                groups_start = group_slot
                while groups_start >= 4 and _points_to_map_group(rom, groups_start - 4):
                    groups_start -= 4
                ids.add(((group_slot - groups_start) // 4, (slot - group_start) // 4))
    return sorted(ids)


def land_encounters(rom: Rom, map_name: str) -> LandEncounters:
    """The land encounters of the map that the ROM names `map_name`."""
    maps = map_ids(rom, map_section(rom, map_name))
    headers = find_wild_headers(rom)
    entries, offset = [], headers
    while rom.data[offset : offset + 2] != b"\xff\xff":
        if (rom.data[offset], rom.data[offset + 1]) in maps:
            entries.append(offset)
        offset += HEADER_SIZE
    if len(entries) != 1:
        raise ExtractError(f"{map_name}: maps {maps}, {len(entries)} wild encounter headers; expected one")
    land = rom.u32(entries[0] + 4)
    if not land:
        raise ExtractError(f"{map_name} has no land encounters")
    info = rom.at(land)
    rate, slots_pointer = rom.data[info], rom.u32(info + 4)
    slots = []
    for i in range(LAND_SLOTS):
        low, high, species = struct.unpack_from("<BBH", rom.data, rom.at(slots_pointer) + 4 * i)
        if not 1 <= species <= LAST_NATIONAL_ORDER_SPECIES:
            raise ExtractError(
                f"{map_name}: species {species} isn't in national order; reading the ROM's own "
                "national order table isn't written yet"
            )
        slots.append(Slot(species, low, high))
    return LandEncounters(rate, tuple(slots))
