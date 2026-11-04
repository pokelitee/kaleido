"""FireRed and LeafGreen (GBA, Gen 3): wild encounters, found by structure and named by the ROM's own text (E8,
docs/research/e8-extract-encounters.md).

The formats, from reading pret/pokefirered at ce6406d8 (nothing copied):
- wild encounter headers: 20 bytes each (map group, map number, two bytes of padding, then pointers to the land, water,
  rock smash and fishing groups, or 0), ended by map group and number 0xFF;
- a group: an encounter rate (u8, then padding) and a pointer to its slots; a slot: minimum and maximum level (u8) and
  species (u16); 12 land slots;
- a map header: 28 bytes, whose byte 0x14 is its map section; the map groups: a table of pointers to tables of pointers
  to map headers;
- the map section names: a table of pointers to strings, from the first Kanto section, KANTO_MAPSEC_START;
- text: capital letters from 0xBB, digits from 0xA1, space 0x00, ended by 0xFF;
- species 1 to 251 are in national Pokédex order."""
import struct
from dataclasses import dataclass

ROM_BASE = 0x08000000
KANTO_MAPSEC_START = 0x58
HEADER_SIZE, MAP_HEADER_SIZE, LAND_SLOTS = 20, 28, 12
MAP_SECTION_OFFSET = 0x14
LAST_NATIONAL_ORDER_SPECIES = 251


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


def encode(text: str) -> bytes:
    out = bytearray()
    for c in text:
        if "A" <= c <= "Z":
            out.append(0xBB + ord(c) - ord("A"))
        elif "0" <= c <= "9":
            out.append(0xA1 + ord(c) - ord("0"))
        elif c == " ":
            out.append(0x00)
        else:
            raise ExtractError(f"no encoding for {c!r}")
    return bytes(out) + b"\xff"


def _is_wild_header(rom: Rom, offset: int) -> bool:
    if rom.data[offset + 2:offset + 4] != b"\0\0":
        return False
    fields = [rom.u32(offset + 4 + 4 * i) for i in range(4)]
    return any(fields) and all(f == 0 or (rom.is_pointer(f) and f % 4 == 0) for f in fields)


def find_wild_headers(rom: Rom) -> int:
    """The offset of the wild encounter headers: the longest run of headers that a 0xFF 0xFF entry ends."""
    best, best_count, offset = None, 0, 0
    while offset + HEADER_SIZE <= len(rom.data):
        count = 0
        while offset + (count + 1) * HEADER_SIZE <= len(rom.data) and _is_wild_header(rom, offset + count * HEADER_SIZE):
            count += 1
        end = offset + count * HEADER_SIZE
        if count and rom.data[end:end + 2] == b"\xff\xff":
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
    target, candidates, start = encode(name), [], 0
    while (i := rom.data.find(target, start)) != -1:
        start = i + 1
        for slot in rom.pointers_to(i):
            first = slot
            while first >= 4 and rom.is_pointer(rom.u32(first - 4)):
                first -= 4
            last = slot
            while last + 4 < len(rom.data) and rom.is_pointer(rom.u32(last + 4)):
                last += 4
            candidates.append(((last - first) // 4 + 1, (slot - first) // 4))
    if not candidates:
        raise ExtractError(f"no table names {name!r}")
    return KANTO_MAPSEC_START + max(candidates)[1]


def _is_map_header(rom: Rom, offset: int) -> bool:
    if offset % 4 or offset < 0 or offset + MAP_HEADER_SIZE > len(rom.data):
        return False
    layout, events, scripts, connections = (rom.u32(offset + 4 * i) for i in range(4))
    return all(rom.is_pointer(p) for p in (layout, events, scripts)) and (connections == 0 or rom.is_pointer(connections))


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
    while rom.data[offset:offset + 2] != b"\xff\xff":
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
            raise ExtractError(f"{map_name}: species {species} isn't in national order; reading the ROM's own "
                               "national order table isn't written yet")
        slots.append(Slot(species, low, high))
    return LandEncounters(rate, tuple(slots))
