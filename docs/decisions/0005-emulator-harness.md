# 0005. Drive DS-mode emulator tests with py-desmume

- Status: Proposed (2026-11-04), for the owner to accept
- Date: 2026-11-04

## Context

R-16: Kaleido needs a way to run the game without a person, to measure memory (E6b), check boots and saves, and run
the playtest checks that are now deferred. melonDS, the primary emulator, has no headless or scripting mode. DeSmuME's
Lua runs on Windows only. BizHawk's licensing is unclear, and it needs Mono (`docs/research/hardware-and-rom.md`).

Phase 1's spike (`docs/research/harness-spike.md`, 2026-11-04) tried py-desmume, SkyTemple's GPL-3.0 Python binding of
DeSmuME's core. It drove Black 2 from power-on through the title screen, the field, the bag and the first battle
with scripted buttons, read the heap manager and the save table from RAM, and measured E6b. It runs headless at
about 30–100 frames per second on the owner's machine, from a pip install, with no BIOS or firmware files.

## Options

1. **py-desmume**: works now (**Verified**, spike). DS mode only; DeSmuME's accuracy, not melonDS's.
2. **A harness on melonDS's core library**: DS and DSi mode, melonDS's accuracy. A C++ program of our own to build
   and maintain; not started.
3. **BizHawk with Lua** (its melonDS core): DS and DSi mode, but unclear licensing, Mono, and no headless flag.
4. **Manual checks only**: no tooling, but every check costs the owner's time (`docs/status.md`, deferred checks).

## Decision

Option 1, proposed. Kaleido's automated emulator checks run on py-desmume, on the builder's machine, never in CI (no
ROM leaves the machine, `06-testing.md`). DSi-mode checks stay manual in melonDS. Option 2 is the fallback if DSi
automation, speed or accuracy ever needs it.

The spike's prototype stays in `docs/research/` (`e6b-harness.py`, `e6b-route.txt`). It becomes a `kaleido` command
(`06-testing.md`'s `kaleido test --local`) when the first automated test needs one, with the state readers it lacks.
For example, the player's position through the field system's pointers instead of an address found by RAM search.

## Consequences

- Local test tooling gains a GPL-3.0 Python dependency (py-desmume 0.0.9, bundling DeSmuME 0.9.12's core, GPL-2.0).
  The framework itself stays standard-library only; the harness installs py-desmume in its own virtual environment.
- Emulator results are DeSmuME's. A DS-mode pass in DeSmuME doesn't prove melonDS or hardware behave the same (E7).
- Screenshots, savestates and RAM dumps come from the ROM. They stay outside the repository, and the ROM-content guard
  rejects savestate files.
- Driving the game takes routes found by hand. They are tied to frame counts, so a route breaks when anything before
  it changes timing, including a Kaleido change. Tests should reach states through savestates made on the same
  build, or use state readers rather than fixed frame counts.
