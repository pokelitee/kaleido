# E4a — A new zone with existing art

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-03 on the owner's machine in the scratch checkout
`~/kaleido-work/pokebw2` at pokebw2 `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (branch `phase0-e4a`, on top of E3's
`--define`). Question: can a zone be added, with header, events, warps both ways and a script, using existing map
art?

## Summary

- **The data side works.** A new zone appended as ID 615, laid out like an Aspertia City house, with its own script,
  text and events, behind Aspertia's door warp 6 and leading back to it, packs into every archive. **Verified** by
  reading the built archives back.
- **Appending zones collides with hard-coded "no zone" values.** ID 615 is `ZONE_MAX`, the zone header cache's start
  value, and the place-name start value. A `KALEIDO_EXTRA_ZONES` switch moves all three to 0xffff (patch recorded).
  With the switch off, the build still matches Black 2.
- **With the switch on, the ROM can't be finished without the DS ARM7 BIOS.** The switch changes code in ARM9 main,
  which changes bytes in ARM9's first 16 KiB. dsd then needs the BIOS's Blowfish key to recompute the DSi secure-area
  values. **This applies to any engine change that moves code in ARM9 main**, not just this one (new risk R-27).
- Kanto doesn't need more than 615 zones for Tier 1 (FRLG has 425 maps), so appending isn't required yet.

## 1. How a zone is wired

All **Verified** in pokebw2's sources and packers:

- A zone is a line in `generated/zones.txt` and a header in `res/field/zones/<zone>.json`. The header names its map
  matrix, area, script file (`SCRIPTS_*`), text bank (`SCRIPT_TEXT_*`), music and the rest. Its map-script table
  defaults to the script file's ID plus one (`zone_data.py`), so the two constants are appended as a pair.
- Events (NPCs, warps, signs, triggers) are `res/field/events/<zone>.json`, packed in the order of
  `res/field/events/order.json`. The zone packer writes each header's events number from that order.
- Scripts are `res/field/scripts/<zone>.s` and `init_<zone>.s`; text is `res/text/script/<zone>.txt`, with a constant in
  `generated/script_text_banks.txt`.
- Warps pair up by index: Aspertia City's warp 6 leads to `ZONE_ASPERTIA_CITY_7` warp 0, and that house's warp 0 leads
  back to Aspertia's warp 6.
- Zone headers are one file, read at `zoneId × 0x30` with no bounds check (`zonedata.c`). No array in the code is sized
  by the zone count.

## 2. The "no zone" collisions

The first appended zone gets ID 615. Three places already use 615 to mean "no zone" (**Verified**, grep and reading):

| Where | Value | Effect on zone 615 |
| --- | --- | --- |
| `include/field/zone.h` | `#define ZONE_MAX 615`, the "none" value in gate and electronic-board gimmicks and the Pokédex area map | Those would treat zone 615 as none |
| `src/system/zonedata.c` | `ZONE_COUNT` (`ZONE_PLEDGE_GROVE + 1`) starts the header cache | If zone 615 is the first header asked for, the game returns the uninitialized cache without reading it |
| `src/system/player_savedata.c` | the initial place-name zone, 0x267 | A new game would believe it had already shown zone 615's place name |
| `src/system/game_beacon_accessor.c` | `BEACON_ZONE_COUNT` (`ZONE_PLEDGE_GROVE + 1`) | Beacons from zones ≥ 615 are rejected; only Wi-Fi/C-Gear features, switched off for Kanto (Q7) |

Gimmick data files store 615 as their "none" too. With `ZONE_MAX` at 0xffff, those Unova gimmicks would read past
their lists, but only in their own Unova zones, which Kanto games never visit.

The fix, recorded as [`e4a-extra-zones.patch`](e4a-extra-zones.patch) (applies cleanly to the pin): under
`KALEIDO_EXTRA_ZONES`, the first three move to 0xffff. **Verified**: with the switch off, `configure.py b2_us && ninja`
passes every matching check with Black 2's SHA1.

## 3. The test content

| Piece | What |
| --- | --- |
| `ZONE_KALEIDO_E4A` | Header copied from `aspertia_city_7` (map type 16, `MAP_MATRIX_ASPERTIA_CITY_3`, `AREA_ASPERTIA_CITY_3`), with its own scripts and text |
| Events | One NPC running script 1; one warp back to Aspertia City's warp 6 |
| Aspertia City warp 6 | Now leads to `ZONE_KALEIDO_E4A` warp 0 (the house it used to lead to becomes unreachable) |
| Script and text | `kaleido_e4a.s` (one script: show a message), `init_kaleido_e4a.s` (empty map-script table), `kaleido_e4a.txt` |

**Verified** by dumping the built archives (`build/b2_us/files`) back to JSON:

| Archive | Built | Original |
| --- | --- | --- |
| Zone headers (`a/0/1/2`) | 616 | 615 |
| Field scripts (`a/0/5/6`) | 1,291 | 1,289 |
| Script text banks (`a/0/0/3`) | 677 | 676 |
| Zone entities (`a/1/2/6`) | 617 | 616 |

The new header resolves to `SCRIPTS_KALEIDO_E4A` (map scripts implicit), `SCRIPT_TEXT_KALEIDO_E4A`, the Aspertia house
matrix and area. Its events hold one NPC with script 1 and the warp back to Aspertia warp 6. Aspertia's warp 6 leads
to the new zone's warp 0.

## 4. The secure-area wall

With `KALEIDO_EXTRA_ZONES` on, the last step, `dsd rom build`, stopped:

```
Error: the ARM9 secure area (its first 0x4000 bytes) has changed since extracting, so the secure area values stored in
the DSi config are stale. Provide the ARM7 BIOS so the Blowfish key can encrypt the secure area and compute them again
```

**Verified** cause:

- The built ARM9 main is exactly the original's size (628,544 B), but 395 bytes differ in its first 0x4000, from
  `0x02004980` on.
- The switch changes code inside `zonedata.c`, so some of its functions move by a few bytes within the file. Its
  `ZoneData_*` functions are called from all over ARM9 main, including the first 16 KiB, and every such call encodes
  the target's address.
- pokebw2's docs predicted this: the DSi secure-area digests "are computed over its encrypted form. Without an ARM7 BIOS
  the build reuses the original values, which stay valid as long as the secure area is unchanged"
  (`docs/configs.md`).
- `dsd rom build` takes `-7, --arm7-bios <FILE>` (Nintendo DS ARM7 BIOS). pokebw2's `configure.py` never passes it.

So **any engine change that moves code in ARM9 main needs the BIOS at build time.** In practice, that's any change to
main that isn't byte-for-byte size-neutral at function level. Changes confined to overlays (E3) or to data (E1, E2,
E4b) don't.

## 5. Options

| Option | What it takes | Effect |
| --- | --- | --- |
| A. Supply the DS ARM7 BIOS | The owner dumps it from their own DS (16 KiB); a one-line engine patch passes `--arm7-bios` to dsd | Every ARM9 main change works, appended zones included. Needs hardware the owner doesn't have yet |
| B. Repurpose zone IDs for Tier 1 | No engine change: Kanto's zones take over Unova zone IDs and their files. 615 is enough for FRLG's 425 maps | Unblocks Kanto content now; zone constants keep Unova names; doesn't solve other main-module changes |
| C. Let dsd build with stale DSi secure-area values | A change to dsd (`fuddlesworth/ds-decomp` fork, MIT), offered upstream | DS mode, the hard limit, is unaffected. DSi mode through loaders that check those values would fail; whether nds-bootstrap or Unlaunch check them is **Unverified** |

The DS Protect guard (R-25) and the B2W2-system switches (Q7) may also touch ARM9 main, so A or C will be needed
eventually even if B handles zones.

## Not done

- No E4a ROM was produced with the switch on. A build with the switch off but the content in would boot, but zone 615
  would hit the collisions above. It wasn't built.
- In-game check (walk through Aspertia's door into the new zone and back, talk to the NPC): deferred to the playtest
  pass, once a ROM exists.
