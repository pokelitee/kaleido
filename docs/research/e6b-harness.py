#!/usr/bin/env python3
"""E6b's emulator harness spike (R-16): runs Black 2 headless in py-desmume (DeSmuME's core), drives it with scripted
button presses, and reads free memory and the save's size from RAM.

    e6b_harness.py ROM --out DIR [--state FILE] --steps "wait 600, shot title, A*10/40, measure title, save title"
    e6b_harness.py ROM --out DIR --steps-file e6b-route.txt

Steps, separated by commas or lines (# starts a comment):
    wait N          run N frames
    KEY[*N][/F]     press KEY (A B X Y L R START SELECT UP DOWN LEFT RIGHT) N times, F frames after each (default 30)
    hold KEY N      hold KEY for N frames (walking)
    shot NAME       screenshot to DIR/NAME.png
    save NAME       savestate to DIR/NAME.dst
    load NAME       restore DIR/NAME.dst, to branch off a saved point
    measure NAME    measurements to DIR/NAME.json, and printed
    cgear-on        set the C-Gear's on byte in the save, as script command 0x197 does
    export-save N   the save chip to DIR/N.sav
    import-save N   DIR/N.sav into the save chip, then reset the console
    pos             the player's tile, from an address found in Aspertia City (see e6b's write-up)
    dump NAME A B   RAM from A to B to DIR/NAME.bin, for finding addresses

Screenshots and savestates come from the ROM: they stay in DIR, outside the repository, and are never committed."""

import argparse
import json
import time
from pathlib import Path

from desmume.controls import Keys, keymask
from desmume.emulator import DeSmuME

# Black 2 (USA) at pokebw2 41f42ca, from config/b2_us/arm9/symbols.txt and the source's structures
HEAP_MGR = 0x0214181C  # sHeapMgr (src/gfl/heapsys.c): heaps, indices, maxHeapIds, rootCount, heapCount
SAVE_CONTROL_WORK = 0x02140F60  # SaveControlWork (src/system/save_control.c)
ARENA_INFO = 0x02FFFDA0  # NitroSDK's OSArenaInfo: lo[OS_ARENA_MAX], then hi[OS_ARENA_MAX] (os_arena.c)
OS_ARENA_MAX = 9
HEAP_ENTRY_SIZE = 0x10  # HeapEntry: handle, parent, memory, allocations (u16), external (u8)
HEAP_INDEX_NONE = 0xFF
EXP_HEAP_SIGNATURE = 0x45585048  # 'EXPH'
FREE_BLOCK_SIGNATURE = 0x4652  # 'FR'
MAX_FREE_BLOCKS = 100_000
CGEAR_BLOCK = 0x20  # SAVE_BLOCK_CGEAR
CGEAR_SETTINGS = 5 * 8  # CGearSave.settings, after five 8-byte PMSData phrases

KEYS = {
    name: keymask(getattr(Keys, f"KEY_{name}"))
    for name in ("A", "B", "X", "Y", "L", "R", "START", "SELECT", "UP", "DOWN", "LEFT", "RIGHT")
}


class Harness:
    def __init__(self, rom: Path, state: Path | None = None) -> None:
        self.emu = DeSmuME()
        self.emu.open(str(rom))
        if state is not None:
            self.emu.savestate.load_file(str(state))
        self.mem = self.emu.memory.unsigned
        self.frames = 0

    def run(self, frames: int) -> None:
        for _ in range(frames):
            self.emu.cycle(with_joystick=False)
        self.frames += frames

    def press(self, key: str, hold: int = 6, after: int = 30) -> None:
        self.emu.input.keypad_add_key(KEYS[key])
        self.run(hold)
        self.emu.input.keypad_rm_key(KEYS[key])
        self.run(after)

    def u8(self, address: int) -> int:
        return self.mem.read_byte(address)

    def u16(self, address: int) -> int:
        return self.mem.read_short(address)

    def u32(self, address: int) -> int:
        return self.mem.read_long(address)

    def heaps(self) -> list[dict]:
        """Every heap ID with a heap: its size, free bytes (NNS_FndGetTotalFreeSizeForExpHeap's sum over the free
        list), largest free block and allocation count."""
        entries, indices = self.u32(HEAP_MGR), self.u32(HEAP_MGR + 4)
        max_ids = self.u16(HEAP_MGR + 8)
        result = []
        for heap_id in range(max_ids):
            index = self.u8(indices + heap_id)
            if index == HEAP_INDEX_NONE:
                continue
            entry = entries + index * HEAP_ENTRY_SIZE
            handle, parent = self.u32(entry), self.u32(entry + 4)
            if self.u32(handle) != EXP_HEAP_SIGNATURE:
                result.append({"id": heap_id, "error": f"no expanded heap at {handle:#x}"})
                continue
            free = largest = blocks = 0
            block = self.u32(handle + 0x24)  # NNSiFndExpHeapHead.mbFreeList.head, after the 0x24-byte common head
            while block and blocks < MAX_FREE_BLOCKS:
                if self.u16(block) != FREE_BLOCK_SIGNATURE:
                    raise RuntimeError(f"heap {heap_id}: free block {block:#x} has no 'FR' signature")
                size = self.u32(block + 4)
                free, largest, blocks = free + size, max(largest, size), blocks + 1
                block = self.u32(block + 0xC)
            result.append(
                {
                    "id": heap_id,
                    "start": handle,
                    "size": self.u32(handle + 0x1C) - handle,
                    "free": free,
                    "largest_free_block": largest,
                    "free_blocks": blocks,
                    "allocations": self.u16(entry + 0xC),
                    "child_of_root": parent != 0,
                }
            )
        return result

    def _save(self) -> tuple[int, int]:
        """SaveData and its SaveDataTable, or zeros before the save is loaded."""
        control = self.u32(SAVE_CONTROL_WORK)
        save = self.u32(control + 0x10) if control else 0  # SaveControl.sv
        table = self.u32(save + 0x2C) if save else 0  # SaveData.table
        return save, table

    def save_block(self, block: int) -> int:
        """Where a save block lives in RAM: SaveData.data plus the block's offset (SaveDataTable.blocks, 12 bytes
        each: id, size, offset; src/gfl/savedata.c)."""
        save, table = self._save()
        if not table:
            return 0
        return self.u32(save + 0x34) + self.u32(self.u32(table + 0x14) + block * 12 + 8)

    def save_control(self) -> dict | None:
        """SaveControl's first bytes: newGame (no save was loaded) and dataExists (the card holds this game's save)."""
        control = self.u32(SAVE_CONTROL_WORK)
        if not control:
            return None
        return {"new_game": self.u8(control), "data_exists": self.u8(control + 1)}

    def set_cgear_on(self) -> None:
        """What script command 0x197 does to the save before the C-Gear shows: CGearSettings.on = 1."""
        self.emu.memory.write_byte(self.save_block(CGEAR_BLOCK) + CGEAR_SETTINGS + 7, 1)

    def save_table(self) -> dict | None:
        save, table = self._save()
        if not table:
            return None
        cgear = self.save_block(CGEAR_BLOCK) + CGEAR_SETTINGS
        return {
            "total_size": self.u32(table + 0x0C),  # SaveDataTable.total_size
            "savearea_size": self.u32(table + 0x10),
            "blocks": self.u32(table + 0x04),
            "save_size": self.u32(save + 0x30),  # SaveData.saveSize
            # CGearSettings.wasOn and .on (include/save/c_gear_savedata.h)
            "cgear": {"was_on": self.u8(cgear + 6), "on": self.u8(cgear + 7)},
        }

    def measure(self) -> dict:
        lo, hi = self.u32(ARENA_INFO), self.u32(ARENA_INFO + 4 * OS_ARENA_MAX)
        return {
            "frame": self.frames,
            "main_arena": {"lo": lo, "hi": hi, "free": hi - lo},
            "heaps": self.heaps(),
            "save": self.save_table(),
            "save_control": self.save_control(),
        }


def parse_steps(text: str) -> list[str]:
    """Steps separated by commas or lines; # starts a comment."""
    steps = []
    for line in text.splitlines():
        steps += [s.strip() for s in line.split("#", 1)[0].split(",") if s.strip()]
    return steps


def run_steps(harness: Harness, steps: list[str], out: Path) -> None:
    for step in steps:
        words = step.split()
        if words[0] == "load":
            harness.emu.savestate.load_file(str(out / f"{words[1]}.dst"))
        elif words[0] == "wait":
            harness.run(int(words[1]))
        elif words[0] == "hold":
            harness.press(words[1], hold=int(words[2]), after=0)
        elif words[0] == "shot":
            harness.emu.screenshot().save(out / f"{words[1]}.png")
        elif words[0] == "save":
            harness.emu.savestate.save_file(str(out / f"{words[1]}.dst"))
        elif words[0] == "cgear-on":
            harness.set_cgear_on()
        elif words[0] == "export-save":
            if not harness.emu.backup.export_file(str(out / f"{words[1]}.sav")):
                raise RuntimeError(f"couldn't export the save to {words[1]}.sav")
        elif words[0] == "import-save":
            if not harness.emu.backup.import_file(str(out / f"{words[1]}.sav")):
                raise RuntimeError(f"couldn't import {words[1]}.sav")
            harness.emu.reset()
        elif words[0] == "pos":
            # Found by RAM search in Aspertia City after one step left and one up; valid while that field heap lives
            print(f"pos: x {harness.u16(0x0223E43A)} z {harness.u16(0x0223E43C)}", flush=True)
        elif words[0] == "dump":
            start, end = int(words[2], 0), int(words[3], 0)
            (out / f"{words[1]}.bin").write_bytes(harness.emu.memory.read(start, end, 1, False))
        elif words[0] == "measure":
            data = harness.measure()
            (out / f"{words[1]}.json").write_text(json.dumps(data, indent=2) + "\n")
            print(f"{words[1]}: {summary(data)}", flush=True)
        else:
            key, _, rest = step.partition("*")
            count, _, after = rest.partition("/") if rest else ("1", "", step.partition("/")[2])
            key = key.partition("/")[0]
            for _ in range(int(count or 1)):
                harness.press(key, after=int(after or 30))


def summary(data: dict) -> str:
    arena = data["main_arena"]
    parts = [f"frame {data['frame']}", f"arena {arena['lo']:#x}-{arena['hi']:#x} free {arena['free']}"]
    for heap in data["heaps"]:
        if "error" in heap:
            parts.append(f"heap {heap['id']}: {heap['error']}")
        elif heap["id"] in (0, 1, 7, 9) or heap["size"] >= 0x10000:
            parts.append(f"heap {heap['id']} {heap['free']}/{heap['size']} free (largest {heap['largest_free_block']})")
    if data["save"]:
        parts.append(f"save total {data['save']['total_size']} of {data['save']['savearea_size']}")
        parts.append(f"C-Gear on {data['save']['cgear']['on']}")
    if data["save_control"]:
        control = data["save_control"]
        parts.append(f"new game {control['new_game']}, data exists {control['data_exists']}")
    return "; ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--state", type=Path, help="a savestate to start from")
    parser.add_argument("--steps", default="", help="the steps to run, separated by commas")
    parser.add_argument("--steps-file", type=Path, help="a file of steps, run before --steps")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    steps = parse_steps(args.steps_file.read_text(encoding="utf-8")) if args.steps_file else []
    steps += parse_steps(args.steps)
    start = time.monotonic()
    harness = Harness(args.rom, args.state)
    run_steps(harness, steps, args.out)
    elapsed = time.monotonic() - start
    print(f"{harness.frames} frames in {elapsed:.1f} s ({harness.frames / max(elapsed, 1e-9):.0f} frames/s)")


if __name__ == "__main__":
    main()
