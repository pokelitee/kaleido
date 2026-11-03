# 01 — Feasibility

Status: **proposal** for owner review (planning pass, 2026-11-03). Classifications are provisional until the named
experiment or phase confirms them. Evidence tags: **Verified** (source named, with commit), **Unverified**,
**Assumption**. Upstream facts are from pokebw2 `41f42ca` (`docs/research/pokebw2.md`); FireRed facts from pokefirered
`ce6406d8` and Red facts from pokered `0dbf95cd`, read for behavior only (`docs/research/peripheral-tools.md`).

## Verdict

Tier 1 is feasible on pokebw2, on two conditions:

1. **A route for new map art** (R-01). Upstream's packers can edit the original 1,065 map models and 409 texture sets
   but can't add any. Direction chosen in Q3: repurpose Unova chunks for the Phase 3 prototype, then build a glTF →
   Nitro encoder that can add models and texture sets (offered upstream) before Phase 4. E4b confirms.
2. **A distribution decision** (Q1, decided 2026-11-03): a single-source xdelta carries the FireRed content it adds,
   and that is accepted.

**Mechanics are Gen 5 for every game** (owner's decision, Q6 and Q9, 2026-11-03), so no generation-specific battle or
field variants are needed. Original-game mechanics that Gen 5 lacks are Approximate by decision, and the content is
adapted to fit. Everything else in Tier 1 is either possible with upstream's formats today or a bounded engine change.

## Possible now (upstream formats, no engine change)

All **Verified** from upstream's docs and packers unless marked.

- Text: edit or add messages in `res/text/` banks; IDs are stable names.
- Species, moves, items, trainers (record and party), wild encounter tables, zone headers, zone events (NPCs, warps,
  signs, triggers), trades, marts: per-entity JSON with schemas; add an entry by adding its constant and file.
- Field scripts and trainer AI: assembly sources, assembled by the build.
- Trainer battle sprites and overworld actors: new entries by constant + directory.
- Edits to existing map geometry, UVs, materials and textures, and to terrain (collision) within a chunk's grid.
- Battle code changes in C under preprocessor guards (`#ifdef BUGFIX` is the upstream pattern); size changes are
  shift-safe per upstream's audit (**Assumption** until E3 shows it on a real change).
- Places where Gen 5 already matches Gen 3, so FRLG keeps the original behavior under Gen 5 mechanics: grass, surf and
  Super Rod slot odds; crit stage table; type chart (all 289 cells identical). See the tables below.

## Needs engine or tool changes

| Change | Why | Size | Evidence / experiment |
| --- | --- | --- | --- |
| Add new map models and texture sets | Packers patch originals only. Template-append (~25 lines) adds entries that keep a template's materials and texture layout; a full encoder is needed beyond that | Small (template-append, prototyped) / Large (encoder) | **Verified**, E4b (`docs/research/e4b-map-art.md`); ADR 0003 |
| Kaleido defines through `configure.py` | Upstream knows only `--bugfix` and `--shift` | Small | **Verified** (`docs/building.md`); E3 |
| Guard out DS Protect (anti-piracy) | Loaders fix it by game code + header CRC, which a modified ROM won't match | Small | **Verified** (TWiLight Menu++ source, `hardware-and-rom.md`); E7 |
| Content overlay into the engine tree | Our layers must land in `res/` and `generated/` | Small (framework, maybe no engine change) | Phase 1 |
| New-game start in Pallet Town; title, intro, Professor | B2W2's opening is code and scripts | Medium | Phase 3 |
| Per-game switches for B2W2-only systems | C-Gear, Pass Powers, seasons, Join Avenue, PWT, …; each game's config turns each on or off (Q7) | Medium, spread over overlays | Phase 1 inventory, Q7 |
| Kanto regional Pokédex (151) | Regional dex length looks like a code constant (White2Upgrade had to patch it) | Small | **Assumption**; E5 |
| FRLG-only key items' behavior (where kept) | New item entries are data; their screens and logic are code | Small each | Phase 3–4 |
| Music from FRLG | GBA sequence → Nitro SSEQ/SBNK/SWAR converter | Medium–Large | Q6, R-24 |

## Uncertain until measured

| Question | Experiment |
| --- | --- |
| Free RAM and heap in DS mode and DSi mode at field, battle, menus (static bound known: ≈ 213 KiB of DS-mode arena for added code and static data; 288,256 B of heap 1 left in the field) | E6b |
| Per-overlay slack on the overlay tree | E6b / Phase 2 |
| Save area headroom (ROM headroom is ≈ 231 MiB, E6) | E6b |
| Whether a modified DSi-hybrid ROM boots in DSi mode on each loader and device | E7 |
| Zone, flag and variable capacity beyond B2W2's counts | E4a, E6 |
| Cost of species past 649 | E5 |
| Determinism of upstream's packers across machines and Python versions | E0, Phase 1 exit |
| How FRLG text fits Gen 5 boxes (width, control codes) | E1, E8 |

## Hardware bounds

From `docs/research/hardware-and-rom.md` (GBATEK and melonDS, **Verified** unless marked):

| Bound | Value | Consequence |
| --- | --- | --- |
| Main RAM | 4 MB in DS mode, 16 MB in DSi mode | DS Lite support means fitting 4 MB (Q4) |
| ARM9 binary on a DSi | 2.5 MB, "even in NDS-mode" | Main-module growth is capped if DSi/3DS are targets; E6 measures today's size |
| ROM size | 512 MB cart, the largest that exists; melonDS refuses bigger ROMs | Kaleido ROMs stay ≤ 512 MB; E6 measures how much B2 uses |
| Save | 512 KB FLASH behind an infrared-capable SPI bus | Keep size and type; never change the game code (`IREO`), which emulators and loaders use to pick the save type |
| Hybrid signature | RSA can't be redone | No DSi-mode boot from the system menu on unmodified consoles; loaders (nds-bootstrap, Unlaunch) are the DSi-mode path; DS mode should be unaffected (**Assumption**, E7) |
| Anti-piracy | DS Protect is in the game; loader fixes won't match a modified ROM | Guard it out in source (above) |

## Fidelity: FireRed and LeafGreen

Mechanics are Gen 5 (owner's decision, Q6, 2026-11-03): where they differ from Gen 3, the row is Approximate "by
decision". Content (story, dialogue, maps, trainers, encounters, items, learnsets) is FireRed's or LeafGreen's.

Presentation is always Gen 5. **Exact** = behaves as the original; **Approximate** = differs, with the reason;
**Infeasible** = can't be done here, with the reason.

| Feature | Class | What differs and why | Evidence / confirmed by |
| --- | --- | --- | --- |
| Story, progression, event order | Exact | Scripts are rewritten by hand (category 3) in upstream's assembly, using B2W2's flag and variable ranges | Phase 3–4 |
| Dialogue wording | Exact | Extracted from the builder's ROM | E8 |
| Dialogue layout | Approximate | Reflowed to Gen 5 text boxes; Gen 3 control codes mapped to Gen 5's | E1, E8 |
| Characters (battle sprites) | Approximate | Gen 5-style art; 11 Kanto characters already exist in B2W2 | **Verified** sprite list |
| Map layouts and interiors | Approximate | Same layouts on Gen 5's tile grid and 3D models; generic interiors (Pokémon Center, Mart) use B2W2's | R-01, E4b |
| Grass encounters: slots and odds | Exact | Both 12 slots, `20,20,10,10,10,10,5,5,4,4,1,1` | **Verified** both sources |
| Surf encounters | Exact | Both 5 slots, `60,30,5,4,1` | **Verified** |
| Super Rod | Exact | FRLG Super Rod `40,40,15,4,1` = Gen 5 fishing | **Verified** |
| Old Rod, Good Rod | Approximate (by decision) | Gen 5 has one fishing table; FRLG has three (2, 3 and 5 slots). The Old and Good Rod tables are folded into the one table or dropped (content choice in Phase 3) | **Verified** slot counts |
| Rock Smash encounters | Approximate (by decision) | No Gen 5 encounter kind; dropped or moved to another table | **Verified** |
| Encounter rate per map | Approximate (by decision) | Gen 5's per-step climbing rate model | **Verified** Gen 5 side |
| Trainers' parties, items, money | Exact | Data, extracted | E2, E8 |
| Trainer AI | Approximate | Gen 5 AI scripts (grown from Gen 4's) replace FRLG's; can be tuned in assembly | **Verified** upstream `docs/scripts.md` |
| Gyms, Elite Four, Champion | Exact | Data + scripts | Phase 3.5–4 |
| VS Seeker rematches | Approximate initially | Needs an item and its logic | Phase 4 |
| Items shared with Gen 5 | Exact | Existing entries | — |
| FRLG-only key items (e.g. Tea, Teachy TV, Fame Checker) | Approximate | New entries are easy; their screens and logic are new work, simplified where needed | **Assumption**; inventory in Phase 3 |
| TM contents | Exact | Which move each TM teaches is content | Phase 3 |
| TM reuse | Approximate (by decision) | TMs are reusable, as in Gen 5 | — |
| HMs and field moves (Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall) | Approximate (by decision) | Gen 5's HM set and field moves; Flash's field effect exists (`res/field/flash/`). Where FRLG gates progress on a field move B2W2 lacks, the map or script is adapted | **Verified** Flash; others Phase 3 |
| Moves available | Exact | All 354 FRLG moves exist in B2W2 with the same IDs (names differ only in spelling, e.g. Smokescreen) | **Verified** (pokefirered `moves.h` vs pokebw2 `generated/moves.txt`) |
| Move data (power, accuracy, PP, type) and effects | Approximate (by decision) | B2W2's values and behavior, where they differ from Gen 3's | — |
| Physical/special split | Approximate (by decision) | Gen 5 decides per move; Gen 3 decided by type | **Verified** per-move category in data |
| Type chart | Exact | All 289 cells equal | **Verified** (comparison script, 2026-11-03) |
| Critical hit chance stages | Exact | Both `{16, 8, 4, 3, 2}` | **Verified** both sources |
| Damage formula details, EXP formula | Approximate (by decision) | Gen 5's modifier order and EXP scaling | — |
| Abilities | Approximate (by decision) | Gen 5 behavior. Hidden abilities exist but appear only if content hands them out | — |
| Base stats and species types | Exact | Gen 5 data; **Assumption**: no Gen 1–3 species' stats or types changed between Gen 3 and Gen 5 | Phase 3 data check |
| Learnsets and evolutions | Exact | Learnsets extracted from the game; evolutions limited to species in the game's Pokédex | E8 |
| Pokédex: Kanto (151) and National (386) | Exact with engine change | Regional length; Gen 5 UI | E5 |
| Version exclusives | Exact | Game layers | Phase 4 |
| Sevii Islands postgame | Exact | Content volume, not feasibility | Phase 4 |
| Mystery Gift events (Navel Rock, Birth Island) | Infeasible as distributions; Approximate as in-game unlocks | The services are gone and Gen 5 gift formats differ | Phase 4 |
| Link trading and battles with real GBA games | Infeasible | Different hardware link | — |
| Trading between two Kaleido carts | Approximate | Gen 5 wireless stack may work between two Kaleido ROMs | **Unverified** |
| Help system, Union Room, Teachy TV screen | Approximate | Simplified or omitted Gen 3-specific UI | Phase 4 |

## Fidelity: Red, Blue and Yellow

Mechanics are Gen 5 here too (owner's decision, Q6 and Q9, 2026-11-03), so most battle rows are Approximate by
decision. The game plays like a Gen 5 game set in Gen 1's story.

| Feature | Class | What differs and why | Evidence / confirmed by |
| --- | --- | --- | --- |
| Story, dialogue, progression | Exact (wording) / Approximate (layout) | As FRLG | Phase 5 |
| Stats: one Special, DVs, Stat Exp | Approximate (by decision) | Gen 5's split Special Attack/Defense, IVs and EVs, with Gen 5 base stats; Gen 1 had one Special (**Verified** pokered base stats) | — |
| Type chart and species typing | Approximate (by decision) | Gen 5's 17-type chart and typing; Gen 1 had 15 types (**Verified** pokered type list), and e.g. Magnemite was pure Electric (Electric/Steel in B2W2) | **Verified** both sources |
| Crits | Approximate (by decision) | Gen 5 stage table; Gen 1 used base Speed / 2 | **Verified** pokered `CriticalHitTest` |
| Gen 1 battle quirks (1/256 miss, partial trapping, Hyper Beam, freeze, Focus Energy) | Approximate (by decision) | Absent: Gen 5 behavior | — |
| Move data | Approximate (by decision) | B2W2's values; e.g. Bite is Dark-type (Normal in Gen 1) | **Verified** pokered `moves.asm`, pokebw2 `res/moves/bite/` |
| Abilities, held items, natures, genders, shinies | Approximate (by decision) | Present, as in Gen 5; Gen 1 had none | — |
| Encounter slots and odds | Approximate | Gen 1 tables mapped onto Gen 5's 12 grass slots and odds | **Assumption** on Gen 1 table shape; Phase 5 |
| Yellow: Pikachu following | Approximate | B2W2 has walking-Pokémon actors but no following partner | Phase 5 |
| Glitches (MissingNo., item duplication, the Mew glitch) | Infeasible / out of scope | Depend on Gen 1 memory layout | — |
| Time Capsule and Game Boy link | Infeasible | Different hardware | — |

## Tier 2 and 3 requirements (recorded only)

- **Species past 649**: save bitfields hold 672 species; archives indexed by species × constant; egg sentinels at
  650/651; encounter species is 11 bits (max 2047); evolution slots 7 (**Verified** via White2Upgrade and pokebw2
  headers). E5 measures the cost.
- **Fairy type**: 17 → 18 types; the "no type" sentinel 17 must move; every hard-coded 17 found and changed; UI loops
  over types (**Verified** via White2Upgrade).
- **Abilities past 255**: ability IDs are u8 in personal data (**Verified** via White2Upgrade).
- Mega Evolution, Z-Moves, Dynamax, Terastallization: new battle state, UI and data. Gen 5-style reinterpretations
  only (brief). No design work until Tier 3.
- Tier 2 games use Gen 5 mechanics too unless the owner decides otherwise (Q6), so what remains is features: GSC's
  day/night and phone, HGSS's following Pokémon, RSE's contests and secret bases (large), DPPt's Underground. BW is
  native.
