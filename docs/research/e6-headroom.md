# E6 — Headroom

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-03 on the owner's machine from the extracted Black 2 ROM
and pokebw2's source at `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c`. Question: how much RAM, overlay space, ROM space
and save space does Kanto have to work with?

E6 has two parts:

- **E6a (static), done here.** Everything readable from the ROM's header and configs and from the source's constants.
- **E6b (runtime), not done.** Free memory while the game runs, and the save's actual use. It needs an emulator
  harness or a debugger session (see the end).

## Summary

| Resource | Limit | Black 2 uses | Headroom | Evidence |
| --- | --- | --- | --- | --- |
| ROM | 512 MiB (header capacity byte `0x0C`; the largest cart) | 294,568,960 B with the DSi area (header `0x210`) | **≈ 231 MiB** | **Verified**, original ROM header |
| ARM9 binary | 2.5 MB on a DSi, even in DS mode (GBATEK) | 472,740 B in ROM (compressed, header `0x2C`); 628,544 B code and data in RAM | **≈ 1.9 MB** | **Verified**, header and `arm9.yaml` |
| **Main RAM, DS mode** | arena `0x021fd080`–`0x023e0000` | fixed root heaps 1,744,384 B + extra heap 16,128 B | **≈ 213 KiB** for added code and static data, before heap-manager and OS overhead | **Verified** constants; overhead **Unverified** |
| Main RAM, DSi mode | arena `0x0276dde0`–`0x02f80000` | root heaps 4,787,712 B | ≈ 3.5 MiB | **Verified** constants |
| Field memory, DS mode | heap 1 = 1,719,808 B | field heap 1,271,808 B + child heap 7 159,744 B | 288,256 B for everything else in heap 1 while in the field | **Verified** constants; actual use **Unverified** (E6b) |
| Save | 0x26000 B per copy (main at 0, backup at 0x26000) of a 512 KiB chip | **Unverified** (E6b) | **Unverified** | **Verified** layout constants |

What it means:

- **ROM space and the ARM9 binary limit are not constraints.** Kanto's data and code fit many times over.
- **DS-mode RAM is the constraint.** The heaps are fixed sizes, and the arena starts where the last overlay ends. All
  of Kaleido's added code and static data (main module and overlays together) must fit in about 213 KiB, or the heaps
  must shrink, or B2W2 systems must be switched off (Q7). This is now R-05's concrete budget.
- DSi mode has far more room, but DS mode is the hard limit (Q4), so it doesn't help the budget.

## 1. ROM

From the original dump's header (`orig/baserom_b2_us.nds`, SHA1 `e51e6dfb…`):

| Field | Value |
| --- | --- |
| Capacity byte `0x14` | `0x0C` → 128 KiB << 12 = 536,870,912 B |
| Used size, NTR region (`0x80`) | `0x11831a00` (293,804,544 B) |
| Used size with the DSi area (`0x210`) | `0x118ec400` (294,568,960 B) |
| ARM9 (`0x20`–`0x2C`) | ROM offset `0x4000`, RAM `0x02004000`, entry `0x02004800`, size `0x736a4` |
| ARM7 (`0x30`–`0x3C`) | ROM offset `0x33a400`, RAM `0x02380000`, size `0x28f84` |
| ARM9i, ARM7i (`0x1CC`, `0x1DC`) | `0x21c40`, `0x470f8` |

The E4b test ROM, with one more map chunk and texture set, used `0x11851400` NTR bytes. It grew by 129,536 bytes and
still fit before the same DSi area boundary.

## 2. ARM9 in RAM, DS mode

All from `extract/b2_us/arm9/arm9.yaml`, `extract/b2_us/arm9_overlays/overlays.yaml` and the source, **Verified**:

| Region | Range | Size |
| --- | --- | --- |
| Main module: code and data | `0x02004000`–`0x0209d740` | 628,544 B |
| Main module: BSS | `0x0209d740`–`0x0214f500` | 728,512 B |
| Overlay area (main RAM) | `0x0214f500`–`0x021fd080` | 711,552 B |
| Main arena (`OS_GetInitArenaLo`/`Hi`) | `0x021fd080`–`0x023e0000` | 1,978,240 B |

- 344 overlays at 72 load addresses. Overlays at one address replace each other; the layout is a tree, where an
  overlay can load after another's end. The largest overlay is 418,272 B (in the group at `0x0217f600` with overlays
  36, 170 and 337).
- Overlays outside main RAM: 218–225 at `0x02400020` are 32-byte stubs; overlay 169 runs from VRAM at `0x06898020`
  (`docs/configs.md`).
- In DS mode the main arena starts at `OV290_BSS_END` (`lib/nitro/src/os/os_arena.c`). Overlay 290's end is the
  highest end of any main-RAM overlay (`0x021fd080`), so **any growth that raises the overlay area's end shrinks the
  arena by the same amount**. Growth on a branch of the overlay tree that doesn't reach the end is free up to that
  branch's slack (not measured per overlay here).
- The arena ends at `0x023e0000` in DS mode. The ARM7 binary is loaded at `0x02380000`; whether that range stays in
  use after boot is **Unverified**.

### Heaps (`src/system/gfl_use.c`)

| Heap | DS mode | DSi mode |
| --- | --- | --- |
| Root heap 0 | 0x6000 (24,576 B) | same |
| Root heap 1 | 0x1a3e00 (1,719,808 B) | 0x48ae00 (4,763,136 B) |
| Extra heap 9 (`EXTRA_HEAP_SIZE` 0x3f00) | from the OS heap in the arena | child of heap 1 |
| Child heap 7 of heap 1 | 0x27000 (159,744 B) | same |
| DTCM heap | 0x2000 | same |
| Heap IDs | 193 (`GFL_MemInit`) | same |

`GFL_MemInit` stops the console (`OS_Terminate`) if the heap manager can't create the root heaps. So if the arena
shrinks below the fixed root heaps, the game fails at boot, not later.

Map types give the field its own heap from heap 1: 0x136800 (1,271,808 B) for most types, 0x12a000 and 0xaa000 for
two (`MAP_CONFIGS`, `src/ov036/fieldmap.c`, see E4b).

## 3. DSi mode

The arena starts at the LTD module's end (`0x0276dde0`; the module is at `0x02700000`) and ends at `0x02f80000`:
8,462,880 B, of which the root heaps take 4,787,712 B. About 3.5 MiB is left before overhead. Heap 1 is 2.77 times
its DS size. None of this helps Kaleido, because every build must fit DS mode (Q4).

## 4. Save

`src/system/save_table.c`: `SAVE_MAIN_ADDR` 0, `SAVE_BACKUP_ADDR` 0x26000, `SAVE_SIZE` 0x26000 (155,648 B per copy),
`SAVE_MAGIC` 0x31053527. 73 blocks (`SAVEDATA_INIT`, up to `SAVE_BLOCK_MAX`), each padded to a 0x100 boundary
(`SaveData_BuildTable`). The build asserts that the total fits the save area. Other data sits outside the two copies,
for example a gifts backup at `0x7e400` (`src/system/save_control.c`). The chip is 512 KiB
(`hardware-and-rom.md`).

The blocks' sizes come from functions (`*_GetSize`), so the used total isn't a single constant. Measuring it is part
of E6b. For Tier 1, Kanto reuses B2W2's blocks (event flags and variables, Pokédex, party, boxes), so no save growth is
planned (R-13).

## 5. E6b — runtime measurements (to do)

| Measurement | Why | How |
| --- | --- | --- |
| Main arena lo and hi after boot, and free bytes in heaps 0 and 1, in DS mode: at the title screen, in the field (Aspertia), in a wild battle and in the bag menu | Turns the ≈ 213 KiB upper bound and the 288,256 B field figure into measured values | Read the heap manager's state from RAM: melonDS's GDB stub (on by default) with `gdb-multiarch` in WSL, or the Phase 1 emulator harness (R-16) |
| The save's used total (`SaveDataTable.total_size`) | Exact save headroom per copy | Same RAM read after boot; or block footers in a real save file |
| Per-overlay slack on the overlay tree | Which overlays can grow without moving the arena | Static, from the linker script (LCF) of a build; Phase 2, when the first engine patch adds code |

Owner action for the GDB route: enable melonDS's GDB stub in its settings and run a session in which an agent reads
memory. This is optional: the Phase 1 harness spike covers the same measurements.

## Consequences for the plan

- Validation (`03-architecture.md` §9) adds an **arena check** on every build: `0x023e0000` minus the new
  `OV290_BSS_END` must cover the fixed root heaps and the extra heap, plus a safety margin set from E6b's overhead
  measurement. This is cheap and catches overgrowth before anything boots.
- Kaleido's engine changes should favor code in overlays that replace B2W2 ones (switched off per game, Q7), over
  growing ARM9 main or adding resident overlays.
- ROM space and the ARM9 binary size need only a sanity check.
