# E9 — Save identity

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-03 on the owner's machine in the scratch checkout
`~/kaleido-work/pokebw2` at pokebw2 `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (branch `phase0-e9`, on top of E3's
`--define` and E4a's dsd flags). Question: can each Kaleido game refuse Black 2's saves and other Kaleido games' saves,
while flashcarts and emulators keep detecting the save type from B2's header (R-13)?

## Summary

- **Yes, with one switch.** `KALEIDO_SAVE_MAGIC` replaces the two magic numbers the game checks on the card: the save
  footers' (`SAVE_MAGIC`, main save and every extra save) and the outside data's (`SAVE_OUTSIDE_MAGIC`, Mystery Gift
  cards and keys). Each game gets its own value ([`e9-save-magic.patch`](e9-save-magic.patch)).
- **A save with another magic reads as no save at all**, not as a corrupt one: the title screen offers only New Game,
  and the outside data reads as never written. **Verified** in the code (§1); the in-game check is deferred.
- **Verified in the built ROMs**: two games with different magics differ only in those magic words. Every save magic
  (22 in ARM9 main, 2 in overlay 331) carries the game's value. With the switch off, the build still matches Black 2
  (§3).
- **A finding for R-27**: even this data-only change needs `--allow-stale-secure-area`. ARM9 main is stored
  compressed, and its compressed end is a word inside the secure area. Any change to ARM9 main can therefore change
  the secure area, not just code that moves (§3).
- **Nothing in the ROM header changes**, so the game code stays `IREO` and the save type stays what emulators and
  flashcarts pick for Black 2 (§4).
- Left alone: Pokémon Dream Radar's data at `0x7f000` has no identity, but Dream Radar is a B2W2 system that Kanto
  games switch off (Q7). Saving over another game's save gives no warning (§5).

## 1. How the game checks a save

All **Verified** in pokebw2's sources at the pin:

- The card is 512 KB of FLASH. The main save is two copies of 0x26000 bytes at `0` and `0x26000`. Extra saves (battle
  videos, C-Gear skin, musical, Pokédex skin, Hall of Fame, Pokéstar films, tournaments) follow up to `0x7e000`; the
  outside data (gifts in two copies, keys) is at `0x7e000`–`0x7eb00`; Dream Radar's data at `0x7f000`
  (`save_table.c`, `save_outside.c`, `cygnus_save_control.c`).
- Every save ends in a 16-byte footer: count, size, magic, an unused half-word, and a CRC of the blocks' CRCs
  (`backup_system.c`). `SaveData_CheckFooter` returns 2 ("not a save") when the size or the magic differs, 1 when only
  the CRC does.
- When neither copy's footer is right and neither is "only the CRC", the load returns `SAVE_LOAD_RESULT_NONE`, the
  result for an empty card. `SaveControl` then sets `newGame` and no error flags, so the game starts as on a blank card.
  A CRC-only failure would instead give `SAVE_LOAD_RESULT_BROKEN` and the "corrupted" path.
- The main save and all 21 extra saves take their magic from `SAVE_MAGIC` (0x31053527). Extra saves are only opened
  after a valid main save, by a count the main save keeps.
- The outside data's blocks each start with a header holding `SAVE_OUTSIDE_MAGIC` (0xa10f49ae), a count and a CRC. A
  block whose magic differs counts as never written: the gifts are cleared and the keys reset. A new game takes its
  gifts and keys from this data, so without its own magic a Kaleido game would take Black 2's.
- The footer's half-word at offset 0xC is never written or read (`SaveData_FillFooter` sets count, size, magic and
  CRC only). It could hold a Kaleido save-format version later; what it holds on a real card is **Unverified**.
- Nothing else reads these magics; no other code reads the card directly except Dream Radar's loader and a 4-byte
  probe before writes (`backup_card.c`).

## 2. The switch

[`e9-save-magic.patch`](e9-save-magic.patch), 2 files:

- `save_table.c`: `SAVE_MAGIC` is `KALEIDO_SAVE_MAGIC` when defined, else 0x31053527.
- `save_outside.c`: `SAVE_OUTSIDE_MAGIC` is `KALEIDO_SAVE_MAGIC` when defined, else 0xa10f49ae.

One value per game serves both: they're checked at different places on the card. A game passes it with E3's
`--define KALEIDO_SAVE_MAGIC=0x…`.

## 3. Builds

ninja ran until nothing was left to compile each time (R-28).

| Build | Result |
| --- | --- |
| Switch off, full `ninja` with every matching check | passed; SHA1 `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb` |
| Game A, `--define KALEIDO_SAVE_MAGIC=0x4b4c4431`, ROM target | dsd refused: "the ARM9 secure area … has changed". Built with `--allow-stale-secure-area`; SHA1 `90fc7c3571f35ebdcbe4045f6ddc88c9ce55e9a3` |
| Game B, `0x4b4c4432` | the same; SHA1 `5fca7f2d6979f2821b473592280fc82c72cb5ed3` |

**Verified** by comparing the built binaries with the extracted original and with each other:

- ARM9 main: all 22 copies of 0x31053527 became the game's magic, and none remain. `save_block_data.magic` reads the
  game's value. Besides those words, the linked binary differs from the original only in fields dsd fills in when it
  builds the ROM (the overlay digests and one module-parameter word).
- Overlay 331: both copies of 0xa10f49ae became the game's magic, and nothing else differs.
- Games A and B differ only in their magic words.
- ROM header: title, game code `IREO` and maker code equal Black 2's.
- `verify_dsi_rom.py` on both ROMs: every check it runs passes (it skips the secure area's values by design).

**Why the secure area changed** (**Verified**): the ROM stores ARM9 main compressed (472,740 B for Black 2). With the
new magics it compresses to 472,744 B. The compressed end, `0x02004000` + size, is the word at `0x02004fc4`, inside
the first 16 KiB. It went from `0x020776a4` to `0x020776a8`, the only byte that differs there. So any change to ARM9
main, code or data, can change the secure area. ADR 0004 described the trigger as code that moves; its decision
stands, and the flag covers this case. Kaleido games will build with the flag (or a BIOS) as a rule.

Test ROMs `~/kaleido-work/e9/kaleido-e9-a.nds` and `kaleido-e9-b.nds`, never committed.

## 4. Save type detection

The patch changes no header byte: title, game code `IREO` and maker code stay Black 2's (§3). Emulators and loaders
that pick the save type from the game code therefore keep picking Black 2's 512 KB FLASH. **Verified** for melonDS
(R-13, `hardware-and-rom.md`). Flashcart kernels and nds-bootstrap are **Unverified** until E7 has hardware.

## 5. What a player sees, and what's left

| Case | Result |
| --- | --- |
| A Kaleido game on a card or `.sav` with Black 2's save | No Continue; New Game only. The first save overwrites the old data without asking, because the game believes the card is empty |
| A Kaleido game on another Kaleido game's save | The same |
| A Kaleido game on its own save | Loads as before |
| Black 2 on a Kaleido game's save | The same refusal in reverse: Black 2 sees an empty card |
| A Kaleido game's outside data (gifts, keys) on a B2 card | Read as never written, so a new game takes none of B2's |

- **No warning before overwriting a foreign save.** On flashcarts and emulators each ROM file has its own `.sav`, so
  this only bites a player who copies one game's save to another's name. A "this card has another game's save" screen
  would need new UI. Not planned for Phase 1.
- **Dream Radar data** (`0x7f000`) has no game identity. Kanto games switch Dream Radar off (Q7). If a game keeps it,
  it needs its own check.
- **Save layout across releases of one game**: the magic stays fixed per game, so a later release still loads earlier
  saves. If the layout ever changes incompatibly, the footer's unused half-word could carry a format version.
  Decided when it's needed.
- Save editors that look for Black 2's magic won't recognize Kaleido saves (**Assumption**).
- Choosing values: each game's magic must differ from Black 2's two magics, from every other Kaleido game's, and from
  0 and 0xffffffff, the values of a zeroed or erased card. Phase 1's game config holds it, and the validator checks
  those rules.

## Not done

- In-game checks, deferred to the playtest pass (`docs/status.md`): game A saves and reloads its own save; game B and
  Black 2 see A's save as an empty card; A sees a Black 2 save as an empty card. No Black 2 save exists yet on the
  owner's machine; one save in melonDS makes one.
- Flashcarts and nds-bootstrap keeping the save type: E7.
