"""FireRed and LeafGreen's maps: a map's header by its group and number, its events, and the messages that its events'
scripts show (Phase 3, docs/plan/08-phase3.md, W2).

The formats beyond gba_gen3's map headers and groups, from reading pret/pokefirered at ce6406d8 (nothing copied):
- a map header's word 1 points to its events: the counts of its NPCs, warps, triggers and signs (a byte each), then a
  pointer to each array. An NPC is 24 bytes, its local ID at 0 and its script at 16; a trigger 16, its script at 12; a
  sign 12, its kind at 5 and, for kinds 0 to 4, its script at 8 (the other kinds are hidden items);
- word 2 points to the map scripts: a kind (a byte) and a pointer each, ended by a 0 kind. Kinds 2 and 4 point to tables
  of a variable, a value and a script, 8 bytes each, ended by a 0 variable;
- a script is bytecode, an opcode and its arguments. ARGUMENTS gives their sizes for the opcodes Kaleido has met, from
  the event macros (asm/macros/event.inc); a walk that meets another opcode stops with an error, since its arguments'
  size can't be guessed. A trainer battle's arguments depend on its type."""

import struct
from dataclasses import dataclass

from extractors.gba_gen3 import ExtractError, Rom, _is_map_header, group_headers

NPC_SIZE, TRIGGER_SIZE, SIGN_SIZE, TABLE_ENTRY_SIZE = 24, 16, 12, 8
LAST_SCRIPT_SIGN = 4
MAP_SCRIPT_TABLES = (2, 4)

END, RETURN, CALL, GOTO, GOTO_IF, CALL_IF, STANDARD_GOTO = 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
RAM_RETURN, RAM_END = 0x0C, 0x0D
LOAD_WORD, MESSAGE, MESSAGE_AUTOSCROLL, TRAINER_BATTLE = 0x0F, 0x67, 0x9B, 0x5C
# Where a path through a script ends. The standard scripts that a script calls by number hold generic messages (an
# item received, a yes or no), so the walk doesn't enter them
STOPS = {END, RETURN, GOTO, STANDARD_GOTO, RAM_RETURN, RAM_END}
JUMPS = {CALL: 0, GOTO: 0, GOTO_IF: 1, CALL_IF: 1}
MESSAGES = {MESSAGE: 0, MESSAGE_AUTOSCROLL: 0}
# A trainer battle's type, a trainer and an NPC (u8, u16, u16), then pointers by type, as the event macros name them:
# the trainer's lines before the battle, on losing and on winning it, the line when the player can't take a double
# battle, and a script that runs after the battle
SCRIPT = "script"
TRAINER_BATTLE_POINTERS = {
    0: ("intro", "lose"), 1: ("intro", "lose", SCRIPT), 2: ("intro", "lose", SCRIPT), 3: ("lose",),
    4: ("intro", "lose", "not_enough"), 5: ("intro", "lose"), 6: ("intro", "lose", "not_enough", SCRIPT),
    7: ("intro", "lose", "not_enough"), 8: ("intro", "lose", "not_enough", SCRIPT), 9: ("lose", "win"),
}  # fmt: skip
ARGUMENTS = {
    0x00: (), 0x01: (), END: (), RETURN: (), CALL: (4,), GOTO: (4,), GOTO_IF: (1, 4), CALL_IF: (1, 4),
    STANDARD_GOTO: (1,), 0x09: (1,), 0x0A: (1, 1), 0x0B: (1, 1), RAM_RETURN: (), RAM_END: (), LOAD_WORD: (1, 4),
    0x16: (2, 2), 0x19: (2, 2), 0x1A: (2, 2), 0x21: (2, 2), 0x25: (2,), 0x26: (2, 2), 0x27: (), 0x28: (2,),
    0x29: (2,), 0x2A: (2,), 0x2B: (2,), 0x2F: (2,), 0x30: (), 0x31: (2,), 0x32: (), 0x33: (2, 1), 0x34: (2,), 0x35: (),
    0x39: (2, 1, 2, 2), 0x3E: (2, 1, 2, 2), 0x44: (2, 2), 0x45: (2, 2), 0x46: (2, 2), 0x47: (2, 2), 0x4F: (2, 4),
    0x51: (2,), 0x53: (2,), 0x55: (2,), 0x59: (2, 2), 0x5A: (), 0x5B: (2, 1), 0x61: (2,), 0x63: (2, 2, 2), 0x64: (2,),
    0x65: (2, 1), 0x66: (), MESSAGE: (4,), 0x68: (), 0x69: (), 0x6A: (), 0x6B: (), 0x6C: (), 0x6D: (),
    0x6F: (1, 1, 1, 1), 0x71: (1, 1, 1, 1, 1), 0x73: (1, 1, 1, 1), 0x75: (2, 1, 1), 0x76: (), 0x79: (2, 1, 2, 4, 4, 1),
    0x7C: (2,), 0x7D: (1, 2), 0x7F: (1, 2), 0x80: (1, 2), 0x82: (1, 2), 0x83: (1, 2), 0x86: (4,), 0x97: (1,),
    MESSAGE_AUTOSCROLL: (4,), 0x9C: (2,), 0x9D: (1, 2), 0x9E: (2,), 0x9F: (2,), 0xA0: (), 0xA1: (2, 2),
    0xA2: (2, 2, 2, 2), 0xAC: (2, 2), 0xAD: (2, 2), 0xAE: (), 0xC3: (1,), 0xC5: (), 0xC7: (1,), 0xCA: (), 0xCB: (),
    0xCF: (), 0xD0: (2,), 0xD1: (2, 1, 2, 2),
}  # fmt: skip


@dataclass(frozen=True)
class Entry:
    """A place a map's scripts start: an NPC by its local ID, a sign or a trigger by its index, or a map script."""

    name: str
    script: int


@dataclass(frozen=True)
class Battle:
    """A trainer battle that a script starts: the trainer's number and the offset of each of its lines, by role."""

    trainer: int
    lines: dict[str, int]


def _offset(rom: Rom, pointer: int, what: str) -> int:
    if not rom.is_pointer(pointer):
        raise ExtractError(f"{what}: {pointer:#x} isn't a pointer into the ROM")
    return rom.at(pointer)


def map_header(rom: Rom, group: int, number: int) -> int:
    """The offset of a map's header."""
    headers = group_headers(rom, group)
    if not 0 <= number < len(headers):
        raise ExtractError(f"no map {group}.{number}")
    return headers[number]


def entries(rom: Rom, header: int) -> list[Entry]:
    """Where the map's scripts start, in the ROM's order: its NPCs, triggers and signs, then its map scripts."""
    if not _is_map_header(rom, header):
        raise ExtractError(f"{header:#x} isn't a map header")
    events = rom.at(rom.u32(header + 4))
    npcs, _, triggers, signs = rom.data[events : events + 4]
    npc_table, _, trigger_table, sign_table = (rom.u32(events + 4 + 4 * i) for i in range(4))
    found = []
    for i in range(npcs):
        npc = _offset(rom, npc_table, "NPCs") + NPC_SIZE * i
        if script := rom.u32(npc + 16):
            found.append(Entry(f"Npc{rom.data[npc]}", _offset(rom, script, f"NPC {rom.data[npc]}")))
    for i in range(triggers):
        if script := rom.u32(_offset(rom, trigger_table, "triggers") + TRIGGER_SIZE * i + 12):
            found.append(Entry(f"Trigger{i}", _offset(rom, script, f"trigger {i}")))
    for i in range(signs):
        sign = _offset(rom, sign_table, "signs") + SIGN_SIZE * i
        if rom.data[sign + 5] <= LAST_SCRIPT_SIGN:
            found.append(Entry(f"Sign{i}", _offset(rom, rom.u32(sign + 8), f"sign {i}")))
    scripts, number = rom.at(rom.u32(header + 8)), 0
    while kind := rom.data[scripts]:
        target = _offset(rom, rom.u32(scripts + 1), f"map script {number}")
        if kind in MAP_SCRIPT_TABLES:
            while struct.unpack_from("<H", rom.data, target)[0]:
                found.append(Entry(f"MapScript{number}", _offset(rom, rom.u32(target + 4), f"map script {number}")))
                number, target = number + 1, target + TABLE_ENTRY_SIZE
        else:
            found.append(Entry(f"MapScript{number}", target))
            number += 1
        scripts += 5
    return found


def _walk(rom: Rom, start: int) -> tuple[dict[int, int], dict[int, Battle]]:
    """What the script at start can do, following its jumps and calls: the messages it shows, each with the first
    instruction that shows it, and the trainer battles it starts, by instruction."""
    shown: dict[int, int] = {}
    battles: dict[int, Battle] = {}
    pending, seen = [start], set()
    while pending:
        pc = pending.pop()
        while pc not in seen:
            seen.add(pc)
            if pc >= len(rom.data):
                raise ExtractError(f"a script runs past the ROM's end from {start:#x}")
            op, at = rom.data[pc], pc + 1
            if op == TRAINER_BATTLE:
                roles = TRAINER_BATTLE_POINTERS.get(rom.data[at])
                if roles is None:
                    raise ExtractError(f"trainer battle type {rom.data[at]} at {pc:#x} isn't one Kaleido reads")
                trainer = struct.unpack_from("<H", rom.data, at + 1)[0]
                at += 5
                lines = {}
                for role in roles:
                    target = _offset(rom, rom.u32(at), f"the trainer battle at {pc:#x}")
                    if role == SCRIPT:
                        pending.append(target)
                    else:
                        shown.setdefault(target, pc)
                        lines[role] = target
                    at += 4
                battles[pc] = Battle(trainer, lines)
            elif op in ARGUMENTS:
                arguments = []
                for size in ARGUMENTS[op]:
                    arguments.append(int.from_bytes(rom.data[at : at + size], "little"))
                    at += size
                if op in JUMPS:
                    pending.append(_offset(rom, arguments[JUMPS[op]], f"the jump at {pc:#x}"))
                elif op in MESSAGES:
                    shown.setdefault(_offset(rom, arguments[MESSAGES[op]], f"the message at {pc:#x}"), pc)
                elif op == LOAD_WORD and arguments[0] == 0:
                    # Word 0 holds the message that a standard message script shows next
                    shown.setdefault(_offset(rom, arguments[1], f"the message at {pc:#x}"), pc)
                if op in STOPS:
                    break
            else:
                raise ExtractError(f"script opcode {op:#04x} at {pc:#x} isn't one Kaleido reads yet")
            pc = at
    return shown, battles


def messages(rom: Rom, start: int) -> list[int]:
    """The offsets of the messages that the script at start can show, following its jumps and calls, in the order of
    the instructions that show them."""
    shown, _ = _walk(rom, start)
    return sorted(shown, key=lambda message: shown[message])


def map_messages(rom: Rom, group: int, number: int) -> list[tuple[str, list[int]]]:
    """Each of a map's entries and the messages its scripts show. A message that an earlier entry shows too is that
    entry's alone, so each is listed once."""
    listed, result = set(), []
    for entry in entries(rom, map_header(rom, group, number)):
        own = [offset for offset in messages(rom, entry.script) if offset not in listed]
        listed.update(own)
        result.append((entry.name, own))
    return result


def map_battles(rom: Rom, group: int, number: int) -> list[Battle]:
    """The trainer battles that a map's scripts start, each once, in the order of their instructions."""
    found: dict[int, Battle] = {}
    for entry in entries(rom, map_header(rom, group, number)):
        found.update(_walk(rom, entry.script)[1])
    return [found[pc] for pc in sorted(found)]
