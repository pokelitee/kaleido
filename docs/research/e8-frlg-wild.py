#!/usr/bin/env python3
"""E8 prototype: read one map's wild encounters from a FireRed (USA) ROM and write them as a pokebw2 encounter table.
Kaleido's own code, GPL-3.0. A Phase 0 record (docs/research/e8-extract-encounters.md): no build runs it.

    e8-frlg-wild.py ROM "ROUTE 1" ENGINE OUTPUT.json

ROM must be FireRed (USA), SHA1 41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc. ENGINE is a pokebw2 checkout, for its species
constants. Nothing in this file comes from the ROM: it finds the tables by their structure, and names the map by the
name the ROM itself shows.

The ROM's formats (from reading pret/pokefirered at ce6406d8; nothing copied):
- the wild encounter headers: 20 bytes each (map group, map number, two bytes of padding, then pointers to the land,
  water, rock smash and fishing groups, or 0), ended by map group and number 0xFF;
- a group: an encounter rate (u8, then padding) and a pointer to its slots; a slot: minimum and maximum level (u8)
  and species (u16); 12 land slots;
- a map header: 28 bytes, whose byte 0x14 is its map section; the map groups: a table of pointers to tables of
  pointers to map headers;
- the map section names: a table of pointers to strings, from the first Kanto section, KANTO_MAPSEC_START;
- text: capital letters from 0xBB, digits from 0xA1, space 0x00, ended by 0xFF;
- species 1 to 251 are in national Pokédex order.

How the table maps onto Gen 5 (docs/research/e8-extract-encounters.md):
- the land slots become the 12 grass slots in order: FireRed's and Black 2's slot odds are the same;
- Gen 5 has no per-step rate: a walking group's rate selects one of 12 ramp settings (field_encount.c). Any land rate
  becomes setting 7, the one most Black 2 routes use. The original rate is reported, not carried over.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

FIRERED_USA_SHA1 = "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"
KANTO_MAPSEC_START = 0x58
HEADER_SIZE, MAP_HEADER_SIZE, LAND_SLOTS = 20, 28, 12
ROM_BASE = 0x08000000
GEN5_STANDARD_GRASS_SETTING = 7
LAST_NATIONAL_ORDER_SPECIES = 251


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
            raise ValueError(f"no encoding for {c!r}")
    return bytes(out) + b"\xff"


def is_wild_header(rom: Rom, offset: int) -> bool:
    if rom.data[offset + 2:offset + 4] != b"\0\0":
        return False
    fields = [rom.u32(offset + 4 + 4 * i) for i in range(4)]
    return any(fields) and all(f == 0 or (rom.is_pointer(f) and f % 4 == 0) for f in fields)


def find_wild_headers(rom: Rom) -> int:
    """The offset of the wild encounter headers: the longest run of headers that a 0xFF 0xFF entry ends."""
    best, best_count = None, 0
    offset = 0
    while offset + HEADER_SIZE <= len(rom.data):
        count = 0
        while offset + (count + 1) * HEADER_SIZE <= len(rom.data) and is_wild_header(rom, offset + count * HEADER_SIZE):
            count += 1
        end = offset + count * HEADER_SIZE
        if count and rom.data[end:end + 2] == b"\xff\xff" and count > best_count:
            best, best_count = offset, count
        offset = end + 4 if count else offset + 4
    if best is None:
        raise SystemExit("no wild encounter headers found")
    return best


def string_table_index(rom: Rom, name: str) -> int:
    """The index of a map section name in the table of pointers to the names."""
    target = encode(name)
    candidates = []
    start = 0
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
        raise SystemExit(f"no table names {name!r}")
    return max(candidates)[1]


def is_map_header(rom: Rom, offset: int) -> bool:
    if offset % 4 or offset + MAP_HEADER_SIZE > len(rom.data):
        return False
    layout, events, scripts, connections = (rom.u32(offset + 4 * i) for i in range(4))
    return all(rom.is_pointer(p) for p in (layout, events, scripts)) and (connections == 0 or rom.is_pointer(connections))


def points_to_map_header(rom: Rom, slot: int) -> bool:
    value = rom.u32(slot)
    return rom.is_pointer(value) and is_map_header(rom, rom.at(value))


def points_to_map_group(rom: Rom, slot: int) -> bool:
    value = rom.u32(slot)
    return rom.is_pointer(value) and points_to_map_header(rom, rom.at(value))


def map_ids_of_section(rom: Rom, section: int) -> list[tuple[int, int]]:
    """The (group, number) of every map whose header is in that map section, through the map groups' tables: a map's
    number is its place in its group's table of headers, and its group is that table's place in the table of groups."""
    ids = set()
    for offset in range(0, len(rom.data) - MAP_HEADER_SIZE, 4):
        if rom.data[offset + 0x14] != section or not is_map_header(rom, offset):
            continue
        for slot in rom.pointers_to(offset):
            # The groups' tables lie back to back, so a group starts where the table of groups points, not where the
            # run of header pointers starts
            group_start, group_slots = slot, []
            while True:
                group_slots = [s for s in rom.pointers_to(group_start) if points_to_map_group(rom, s)]
                if group_slots or group_start < 4 or not points_to_map_header(rom, group_start - 4):
                    break
                group_start -= 4
            for group_slot in group_slots:
                groups_start = group_slot
                while groups_start >= 4 and points_to_map_group(rom, groups_start - 4):
                    groups_start -= 4
                ids.add(((group_slot - groups_start) // 4, (slot - group_start) // 4))
    return sorted(ids)


def land_slots(rom: Rom, info_pointer: int) -> tuple[int, list[tuple[int, int, int]]]:
    info = rom.at(info_pointer)
    rate, slots_pointer = rom.data[info], rom.u32(info + 4)
    slots = []
    for i in range(LAND_SLOTS):
        low, high, species = struct.unpack_from("<BBH", rom.data, rom.at(slots_pointer) + 4 * i)
        slots.append((species, low, high))
    return rate, slots


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    rom_path, map_name, engine, output = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    data = rom_path.read_bytes()
    if hashlib.sha1(data).hexdigest() != FIRERED_USA_SHA1:
        raise SystemExit(f"{rom_path} isn't FireRed (USA), SHA1 {FIRERED_USA_SHA1}")
    rom = Rom(data)

    section = KANTO_MAPSEC_START + string_table_index(rom, map_name)
    maps = map_ids_of_section(rom, section)
    headers = find_wild_headers(rom)
    entries = []
    offset = headers
    while rom.data[offset:offset + 2] != b"\xff\xff":
        if (rom.data[offset], rom.data[offset + 1]) in maps:
            entries.append(offset)
        offset += HEADER_SIZE
    if len(entries) != 1:
        raise SystemExit(f"{map_name}: section {section:#x}, maps {maps}, {len(entries)} wild encounter headers")
    land_pointer = rom.u32(entries[0] + 4)
    if not land_pointer:
        raise SystemExit(f"{map_name} has no land encounters")
    rate, slots = land_slots(rom, land_pointer)

    species_names = [line.split()[0] for line in (engine / "generated/species.txt").read_text().splitlines()
                     if line.startswith("SPECIES_")]
    grass = []
    for species, low, high in slots:
        if not 1 <= species <= LAST_NATIONAL_ORDER_SPECIES:
            raise SystemExit(f"species {species} isn't in national order; reading the ROM's national table is Phase 1")
        grass.append([species_names[species], low, high])
    table = {"$schema": "encounters.schema.json", "all_year": {
        "rates": {"grass": GEN5_STANDARD_GRASS_SETTING, "dark_grass": 0, "shaking_grass": 0, "surf": 0,
                  "rippling_surf": 0, "fishing": 0, "rippling_fishing": 0, "flags": 0},
        "grass": grass, "dark_grass": [], "shaking_grass": [], "surf": [], "rippling_surf": [], "fishing": [],
        "rippling_fishing": []}}
    output.write_text(json.dumps(table, indent=4) + "\n")
    print(f"{map_name}: section {section:#x}, map {maps}, wild header at {headers:#x} + "
          f"{(entries[0] - headers) // HEADER_SIZE} * {HEADER_SIZE}, land rate {rate} -> Gen 5 setting "
          f"{GEN5_STANDARD_GRASS_SETTING}, {len(grass)} slots")


if __name__ == "__main__":
    main()
