# Emulator harness spike (R-16)

Phase 1 spike (`docs/plan/05-roadmap.md`), run 2026-11-04 on the owner's machine: WSL2 Ubuntu, system Python 3.14.4,
12 cores. It used the owner's Black 2 (USA) dump, SHA1 `e51e6dfb…`. Question: can a harness drive the game and read
its state without a person, well enough to run E6b now and the deferred playtest checks later?

Prototype: [`e6b-harness.py`](e6b-harness.py) (GPL-3.0) and the route it replays, [`e6b-route.txt`](e6b-route.txt).
E6b's results are in [`e6-headroom.md`](e6-headroom.md) §5. Decision proposed: ADR 0005.

## Summary

- **py-desmume works headless on Linux** (**Verified**). `pip install py-desmume==0.0.9` in a virtual environment is
  all it takes: the wheel bundles DeSmuME 0.9.12's core (`libdesmume.so`, built with SDL2), and it needs no BIOS or
  firmware files. Black 2 booted in DS mode and was on the title screen 1,272 frames (21 seconds of game time) after
  power-on.
- **It drives the game.** Scripted buttons took a new game from power-on through Juniper's intro, Aspertia City, the
  bag, the starter at the lookout and the first rival battle, Tackle included.
- **It reads the game's state.** RAM reads through pokebw2's symbols gave every heap's free space, the arena and the
  save table, which is E6b. A RAM search found the player's tile coordinates, which made navigation tractable.
- **Savestates** make each reached state reusable. The route was found one savestate at a time.
- **Speed**: 30–105 emulated frames per second, about 0.5–1.75 times real time. Text and menus ran fastest, and the
  lookout scenes and battles slowest. DeSmuME reported its interpreter CPU mode; whether py-desmume can turn on the
  bundled JIT is **Unverified**.
- **Limits**: DS mode only (DeSmuME has no real DSi mode). Results are DeSmuME's, not melonDS's or hardware's. Routes
  are tied to frame counts.

Only py-desmume was tried. A melonDS-core harness wasn't built, because py-desmume answered the question. BizHawk
stays excluded: unclear licensing, Mono, no headless flag (`hardware-and-rom.md`).

## How the prototype works

`e6b-harness.py ROM --out DIR --steps-file e6b-route.txt` opens the ROM in py-desmume and runs steps:
- waits, button presses, holds (walking);
- screenshots, savestates (`save` and `load`, to branch);
- measurements, the player's tile, RAM dumps.

Everything it writes comes from the ROM, so `--out` is a directory outside the repository (`~/kaleido-work/e6b`).
The ROM-content guard rejects savestate files.

A measurement reads, all at pokebw2 `41f42ca`'s addresses for Black 2:

| What | Where | Source |
| --- | --- | --- |
| Main arena's low and high ends | `0x02fffda0`: `lo[9]` then `hi[9]` | NitroSDK's `OSArenaInfo`, `lib/nitro/src/os/os_arena.c` |
| Each heap: start, size, free bytes, largest free block, allocation count | `sHeapMgr` at `0x0214181c`: entries of 16 bytes, an index per heap ID; each heap's free list after its 0x24-byte head | `src/gfl/heapsys.c`, `lib/nnsys/src/fnd/expheap.c` |
| The save's used size | `SaveControlWork` at `0x02140f60` → `sv` (+0x10) → `table` (+0x2c) → `total_size` (+0x0c) | `src/system/save_control.c`, `src/gfl/backup_system.c`, `src/gfl/savedata.c` |

The free-byte sum is `NNS_FndGetTotalFreeSizeForExpHeap`'s, done from outside. The harness checks each free block's
`FR` signature and each heap's `EXPH`, and stops on a mismatch, so a wrong address fails loudly.

## Findings on the way

- **Name entry takes the presses.** Pressing A through the intro typed the player's name ("A"), then the rival's
  ("HughAAA"), and nicknamed the starter ("AAAAAAAAAA"). The game asks for both names, which the route has to expect.
  Harmless for E6b; a test that checks names needs explicit input.
- **One scene's text crawled.** On the lookout's stairs, the rival's line printed a few characters per thousand frames,
  with presses every 30 frames and with none. Presses every 240 frames got through it, and every 120 frames worked
  for the scenes after. The emulator also slowed to 35–45 frames per second there. The cause is **Unverified**.
- **The player's tile** was at `0x0223e43a` (x) and `0x0223e43c` (z) in Aspertia City. Three RAM dumps, around one
  step left and one up, found it. The address belonged to that field heap's layout and read 0 after the map reloaded.
  A real harness should read the player object through the field system's pointers.
- **Maps from pokebw2's data.** Navigation used the zone's own records: trigger, sign and NPC coordinates in
  `res/field/events/aspertia_city.json`. The lookout's stairs sat behind a hidden-item tile at (36, 725, height 80).
- **A loop that was the route's fault.** After Bianca's scene, more A presses talked to her again, and she repeated
  her line. The battle started from talking to the rival. A harness needs to know when a script has ended, for
  example by reading the script system's state.

## Determinism

Pending: the whole route replayed from power-on in one run.

## Not verified

- Touch input; the bundled JIT; other machines and Python versions.
- DSi mode, which DeSmuME doesn't have.
- Whether routes survive the in-game clock. DeSmuME's real-time clock follows the host by default, and Black 2's
  seasons and some events follow the clock.
- Whether DeSmuME and melonDS agree on anything measured here. They should for RAM layout (the same code runs), not
  necessarily for timing.
