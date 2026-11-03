# 01 — Feasibility

Status: **proposal** for owner review (planning pass, 2026-11-03). Classifications are provisional until the named
experiment or phase confirms them. Evidence tags: **Verified** (source named, with commit), **Unverified**,
**Assumption**. Upstream facts are from pokebw2 `41f42ca` (`docs/research/pokebw2.md`); FireRed facts from pokefirered
`ce6406d8` and Red facts from pokered `0dbf95cd`, read for behavior only (`docs/research/peripheral-tools.md`).

## Verdict

Tier 1 is feasible on pokebw2, on three conditions:

1. **A route for new map art** (R-01). Upstream's packers can edit the original 1,065 map models and 409 texture sets
   but can't add any. Direction chosen in Q3: repurpose Unova chunks for the Phase 3 prototype, then build a glTF →
   Nitro encoder that can add models and texture sets (offered upstream) before Phase 4. E4b confirms.
2. **A distribution decision** (Q1, decided 2026-11-03): a single-source xdelta carries the FireRed content it adds,
   and that is accepted.
3. **A bounded Gen 1 scope** (Q9, decided: Gen 1 rules on Gen 5 data). Several Gen 1 behaviors need engine variants;
   some data-model differences stay Approximate.

Everything else in Tier 1 is either possible with upstream's formats today or a bounded engine change.

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
- Gen 3 data that already matches Gen 5: grass, surf and Super Rod slot odds; crit stage table; type chart (all 289
  cells identical). See the tables below.

## Needs engine or tool changes

| Change | Why | Size | Evidence / experiment |
| --- | --- | --- | --- |
| Add new map models and texture sets | Packers patch originals only | Large (encoder) | **Verified** in `map_model_data.py`, `map_texture_data.py`; E4b |
| Kaleido defines through `configure.py` | Upstream knows only `--bugfix` and `--shift` | Small | **Verified** (`docs/building.md`); E3 |
| Guard out DS Protect (anti-piracy) | Loaders fix it by game code + header CRC, which a modified ROM won't match | Small | **Verified** (TWiLight Menu++ source, `hardware-and-rom.md`); E7 |
| Content overlay into the engine tree | Our layers must land in `res/` and `generated/` | Small (framework, maybe no engine change) | Phase 1 |
| New-game start in Pallet Town; title, intro, Professor | B2W2's opening is code and scripts | Medium | Phase 3 |
| Per-game switches for B2W2-only systems | C-Gear, Pass Powers, seasons, Join Avenue, PWT, …; each game's config turns each on or off (Q7) | Medium, spread over overlays | Phase 1 inventory, Q7 |
| Old/Good Rod and Rock Smash encounters | Gen 5 has one fishing kind and no Rock Smash kind (**Verified**, `enc_pokeset.h`) | Medium | Phase 3 |
| Single-use TMs, FRLG's HM set | Gen 5 TMs are reusable; HM count differs (**Assumption**) | Small–Medium | Phase 3 |
| Kanto regional Pokédex (151) | Regional dex length looks like a code constant (White2Upgrade had to patch it) | Small | **Assumption**; E5 |
| Gen 3 experience and encounter-rate rules | Gen 5's step-based rate climbs per step (**Verified**, `EncountRateConfig`); Gen 5 EXP formula differs (**Assumption**) | Small each | Phase 3 |
| Gen 1 battle variants | Speed-based crit, Special stat, 15-type chart, quirks | Medium–Large | Phase 5 |
| Music from FRLG | GBA sequence → Nitro SSEQ/SBNK/SWAR converter | Medium–Large | Q6, R-24 |

## Uncertain until measured

| Question | Experiment |
| --- | --- |
| Free RAM and heap in DS mode and DSi mode at field, battle, menus | E6 |
| Free space in overlay regions; how much code a ruleset may add | E6 |
| ROM size headroom and save area headroom | E6 |
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
| Old Rod, Good Rod | Approximate → Exact with engine change | Gen 5 has one rod's table; FRLG has three (2, 3 and 5 slots) | **Verified**; Phase 3 |
| Rock Smash encounters | Approximate → Exact with engine change | No Gen 5 encounter kind | **Verified**; Phase 3 |
| Encounter rate per map | Approximate | Gen 5's per-step climbing rate model differs from Gen 3's | **Verified** Gen 5 side; Phase 3 |
| Trainers' parties, items, money | Exact | Data, extracted | E2, E8 |
| Trainer AI | Approximate | Gen 5 AI scripts (grown from Gen 4's) replace FRLG's; can be tuned in assembly | **Verified** upstream `docs/scripts.md` |
| Gyms, Elite Four, Champion | Exact | Data + scripts | Phase 3.5–4 |
| VS Seeker rematches | Approximate initially | Needs an item and its logic | Phase 4 |
| Items shared with Gen 5 | Exact | Existing entries | — |
| FRLG-only key items (e.g. Tea, Teachy TV, Fame Checker) | Approximate | New entries are easy; their screens and logic are new work, simplified where needed | **Assumption**; inventory in Phase 3 |
| TM contents | Exact | TM → move table is data | Phase 3 |
| Single-use TMs | Approximate → Exact with engine variant | Gen 5 TMs are reusable | Phase 3 |
| HMs (Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall) | Approximate | Gen 5's HM set and field moves differ; Flash's field effect exists (`res/field/flash/`) | **Verified** Flash; others Phase 3 |
| Moves available | Exact | All 354 FRLG moves exist in B2W2 with the same IDs (names differ only in spelling, e.g. Smokescreen) | **Verified** (pokefirered `moves.h` vs pokebw2 `generated/moves.txt`) |
| Move data (power, accuracy, PP, type) | Exact | Gen 3 values via data overrides | Phase 3 |
| Move effects whose rules changed by Gen 5 | Approximate → Exact per engine variant | Case by case | Phase 3–4 |
| Physical/special by type | Exact | Ruleset data transform sets each move's `category` from its type | **Verified** per-move category in data |
| Hidden Power and other moves typed in battle | Approximate → Exact with engine variant | Category must follow the computed type | Phase 4 |
| Type chart | Exact | All 289 cells equal | **Verified** (comparison script, 2026-11-03) |
| Critical hit chance stages | Exact | Both `{16, 8, 4, 3, 2}` | **Verified** both sources |
| Damage formula details, EXP formula | Approximate → Exact with variants | Modifier order and EXP scaling differ | **Assumption**; Phase 3 |
| Abilities (Gen 3 set) | Approximate | Exist in Gen 5; some changed behavior; hidden abilities disabled | Phase 4 |
| Base stats, learnsets, evolutions | Exact | Extracted data; post-Gen 3 evolutions removed by data | E8 |
| Pokédex: Kanto (151) and National (386) | Exact with engine change | Regional length; Gen 5 UI | E5 |
| Version exclusives | Exact | Game layers | Phase 4 |
| Sevii Islands postgame | Exact | Content volume, not feasibility | Phase 4 |
| Mystery Gift events (Navel Rock, Birth Island) | Infeasible as distributions; Approximate as in-game unlocks | The services are gone and Gen 5 gift formats differ | Phase 4 |
| Link trading and battles with real GBA games | Infeasible | Different hardware link | — |
| Trading between two Kaleido carts | Approximate | Gen 5 wireless stack may work between two Kaleido ROMs | **Unverified** |
| Help system, Union Room, Teachy TV screen | Approximate | Simplified or omitted Gen 3-specific UI | Phase 4 |

## Fidelity: Red, Blue and Yellow (scope accepted in Q9: Gen 1 rules on Gen 5 data)

| Feature | Class | What differs and why | Evidence / confirmed by |
| --- | --- | --- | --- |
| Story, dialogue, progression | Exact (wording) / Approximate (layout) | As FRLG | Phase 5 |
| Single Special stat | Exact for battle with engine variant; Approximate in UI | Gen 1 base data has one Special (**Verified** pokered base stats); mapped to SpA = SpD, with stage changes applied to both | Phase 5 |
| DVs (0–15) and Stat Exp | Approximate | Gen 5 stores IVs and EVs; a Gen 1 stat formula variant can approximate | Phase 5 |
| 15-type chart | Exact with chart variant | Compile-time table; Dark and Steel unused | **Verified** pokered type list |
| Speed-based crits | Exact with engine variant | Gen 1 uses base Speed / 2 | **Verified** pokered `CriticalHitTest` |
| 1/256 miss and other battle quirks (partial trapping, Hyper Beam, freeze, Focus Energy) | Approximate → Exact per variant | One variant per quirk; scoped by Q9 | **Assumption**; Phase 5 |
| No abilities, held items, natures, genders, shinies | Exact in rules; Approximate in UI | Disabled by data and rules; Gen 5 screens still have the fields unless hidden | Phase 5 |
| Gen 1 move data and effects | Exact (data) / Approximate (effects) | As FRLG | Phase 5 |
| Gen 1 encounter slots and odds | Approximate → Exact with slot-odds variant | Gen 1 tables differ from Gen 5's 12 slots | **Assumption**; Phase 5 |
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
- Gen 2 (GSC): split Special, held items, no abilities, day/night, phone. Gen 4 (DPPt, HGSS): Gen 4 rules, following
  Pokémon (HGSS). Gen 3 (RSE): shares the `gen3` ruleset with FRLG; contests and secret bases are large. BW: native.
