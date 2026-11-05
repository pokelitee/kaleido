"""FireRed and LeafGreen's trainers: a trainer's record and party by its number, and its prize money (Phase 3,
docs/plan/08-phase3.md, W2).

The formats, from reading pret/pokefirered at ce6406d8 (nothing copied):
- the trainers: a 40-byte record each from trainer 0, which is none: its party's kind (bit 0 custom moves, bit 1 held
  items), class, encounter music and sex, picture, name (12 bytes of text), four items (u16 from 0x10), a double
  battle flag (u8 at 0x18), AI flags (u32 at 0x1C), its party's size (u8 at 0x20) and a pointer to the party (0x24);
- a party member: its IV level (u16), level (u8 at 2) and species (u16 at 4), then its held item (u16 at 6) if the
  party has items, then four moves (u16 each, from 6 or 8) if it has moves: 8 bytes, or 16 with moves, as agbcc pads
  them. Every party of two or more without items or moves on the owner's ROM fits 8 bytes, and most don't fit 6;
- each IV is the IV level × 31 / 255 (CreateNPCTrainerParty), as a Gen 5 Pokémon's difficulty sets them (tr_tool.c);
- the prize money: a table of a class and its multiplier, 4 bytes each, ended by class 0xFF, whose multiplier is the
  default. The prize is 4 × the last party member's level × the multiplier, twice that in a double battle
  (GetTrainerMoneyToGive), where Gen 5's is 4 × that level × the trainer's money (btl_calc.c)."""

import functools
import re
import struct
from array import array
from dataclasses import dataclass

from extractors.gba_gen3 import ROM_BASE, ExtractError, Rom

TRAINER_SIZE = 40
CUSTOM_MOVES, HELD_ITEMS = 1, 2
MAX_PARTY, MOVES = 6, 4
MONEY_ENTRY, MONEY_END = 4, 0xFF
# The money table's last entry: class 0xFF, a multiplier, two bytes of padding
TABLE_END = re.compile(rb"\xff[\x01-\xff]\x00\x00")
# The parts of a record, in words from its start
PARTY_SIZE_WORD, PARTY_WORD = 0x20 // 4, 0x24 // 4


@dataclass(frozen=True)
class Member:
    species: int
    level: int
    iv: int
    item: int
    moves: tuple[int, ...]


@dataclass(frozen=True)
class Trainer:
    trainer_class: int
    items: tuple[int, ...]
    double: bool
    party: tuple[Member, ...]


def _member_size(kind: int) -> int:
    return 16 if kind & CUSTOM_MOVES else 8


@functools.cache
def trainer_table(rom: Rom) -> tuple[int, int]:
    """The offset of trainer 0's record and the number of trainers: the longest run of records with a party whose
    kind, size and pointer are possible, after trainer 0's empty one."""
    words = array("I", rom.data[: len(rom.data) // 4 * 4])
    low, high = ROM_BASE, ROM_BASE + len(rom.data)

    def possible(start: int) -> bool:
        size, party = words[start + PARTY_SIZE_WORD], words[start + PARTY_WORD]
        if rom.data[start * 4] > CUSTOM_MOVES | HELD_ITEMS or not 1 <= size <= MAX_PARTY:
            return False
        return low <= party < high and not party & 1

    step, best, best_count = TRAINER_SIZE // 4, 0, 0
    counted: set[int] = set()
    for start in range(step, len(words) - step):
        if start in counted or not possible(start):
            continue
        count = 0
        while start + (count + 1) * step <= len(words) and possible(start + count * step):
            counted.add(start + count * step)
            count += 1
        if count > best_count:
            best, best_count = start, count
    if not best_count:
        raise ExtractError("no table of trainers found")
    first = best - step
    if words[first + PARTY_SIZE_WORD] or words[first + PARTY_WORD]:
        raise ExtractError(f"the record before the trainers at {best * 4:#x} isn't trainer 0's empty one")
    return first * 4, best_count + 1


def trainer(rom: Rom, number: int) -> Trainer:
    table, count = trainer_table(rom)
    if not 0 < number < count:
        raise ExtractError(f"no trainer {number}; the ROM has trainers 1 to {count - 1}")
    record = table + TRAINER_SIZE * number
    kind, trainer_class = rom.data[record], rom.data[record + 1]
    items = tuple(i for i in struct.unpack_from("<4H", rom.data, record + 0x10) if i)
    size, party = rom.data[record + 0x20], rom.at(rom.u32(record + 0x24))
    members = []
    for i in range(size):
        at = party + _member_size(kind) * i
        iv, level, species = struct.unpack_from("<HBxH", rom.data, at)
        item = struct.unpack_from("<H", rom.data, at + 6)[0] if kind & HELD_ITEMS else 0
        first_move = at + (8 if kind & HELD_ITEMS else 6)
        moves = struct.unpack_from(f"<{MOVES}H", rom.data, first_move) if kind & CUSTOM_MOVES else ()
        members.append(Member(species, level, iv, item, tuple(m for m in moves if m)))
    return Trainer(trainer_class, items, bool(rom.data[record + 0x18]), tuple(members))


@functools.cache
def money_table(rom: Rom) -> tuple[dict[int, int], int]:
    """Each class's prize multiplier, and the default for classes the table doesn't list: the longest run of entries of
    distinct classes before an entry of class 0xFF."""
    best: tuple[dict[int, int], int] | None = None
    for match in TABLE_END.finditer(rom.data):
        end = match.start()
        if end % MONEY_ENTRY:
            continue
        table, at = {}, end - MONEY_ENTRY
        while (
            at >= 0
            and rom.data[at] != MONEY_END
            and rom.data[at] not in table
            and rom.data[at + 1]
            and rom.data[at + 2 : at + 4] == b"\0\0"
        ):
            table[rom.data[at]] = rom.data[at + 1]
            at -= MONEY_ENTRY
        if best is None or len(table) > len(best[0]):
            best = (table, rom.data[end + 1])
    if not best or not best[0]:
        raise ExtractError("no table of prize money found")
    return best


def prize_multiplier(rom: Rom, found: Trainer) -> int:
    """The trainer's prize as Gen 5's money: its class's multiplier, doubled for a double battle."""
    table, default = money_table(rom)
    return table.get(found.trainer_class, default) * (2 if found.double else 1)
