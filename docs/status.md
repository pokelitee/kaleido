# Status

Last updated: 2026-11-08

## Current phase

**Phase 3 (Pallet Town to Viridian City), started 2026-11-04** by the accepted plan `docs/plan/08-phase3.md`. Exit
checks still open from earlier phases:
- Phase 1's: the same SHA1s from a clean clone on a second machine;
- Phase 2's: in game.

Phase 1 built:
- the repository layout, licenses and contributor docs;
- the engine submodule and its patch series;
- `./kaleido doctor`, `bootstrap`, `check`, `baseline`, `compile`, `extract`, `merge`, `validate`, `build` and `patch`;
- CI with Dependabot;
- the emulator harness spike with E6b.

Phase 2 added a second game, `red`, beside `firered`, each with its own DS-menu title and save magic, and the first
B2W2-system switch (Red has no C-Gear). Phase 3 has so far put FireRed's content and story, up to the Parcel, on
Unova stand-ins (steps 1 to 4), and is now generating Kanto's own maps from FireRed (step 5, D10). The owner's answers
are in `docs/plan/07-open-questions.md`, and what is decided so far is in `docs/architecture.md`.

Phase 0 (2026-11-03 to 2026-11-04) ran its experiments in a scratch pokebw2 checkout at the pin, in WSL's own
filesystem (on the owner's machine, `~/kaleido-work/pokebw2`). Its write-ups, patches and the extractor prototype are
in `docs/research/`. The playtest checks it deferred are listed at the end of this file.

## Done so far

- Researched the foundation and verified the brief's Section 3 baseline: `docs/research/` (pokebw2 pinned at
  `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c`, 2026-10-31).
- Wrote the plan: feasibility (`01`), foundation (`02`), architecture (`03`), roadmap (`05`), testing (`06`), open
  questions (`07`), and `docs/risks.md`.
- ADR 0001 (record decisions) accepted; ADR 0002 (engine integration) proposed, then accepted by the owner.
- Owner's answers to Q1–Q10 recorded. **Every game uses Gen 5 mechanics** and B2W2's move data; the ruleset mechanism
  is dropped until a game needs one (Q6, Q9). That replaces the brief's generation rulesets and two earlier answers
  the same day (per-game mechanic switches; a Gen 3 default for FRLG). B2W2-only systems are per-game compile-time
  switches (Q7). There is no hardware yet (Q4), so E7 moves out of the Phase 0 gate (`05-roadmap.md`).
- Planning pass merged to `main` (pokelitee/kaleido#1). The owner made the repository **public** on 2026-11-03 to
  unblock GitHub features. That settles the brief's [CONFIRM] default; see the table in `07-open-questions.md`.
- Repository settings: squash merges only; branches deleted after merge; secret scanning with push protection; a
  "Protect main" ruleset (pull request required, no force-push, no deletion, squash only, no bypass). Since
  2026-11-04 it also requires the `CI` check, from GitHub Actions only, and auto-merge is allowed, so a pull request
  with it on merges once `CI` passes (owner's go-ahead).
- Repo records: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/glossary.md`, `.gitignore` (ROMs, saves, build output,
  agent-local settings), `.gitattributes` (LF everywhere).
- **E0a passed** (Phase 0, 2026-11-03): upstream's `compile_all.py` at the pin compiled 3,584 of 3,584 (every C file,
  both versions) with no warnings, in WSL's filesystem with system Python 3.14.4. Three planning-pass attempts had
  stopped on setup (path rewriting, no venv package, a checkout without `res/`). Details:
  `docs/research/e0-baseline.md`.
- **E0 passed** (2026-11-03): with the owner's Black 2 dump, `configure.py b2_us && ninja` reproduced Black 2's SHA1
  (`e51e6dfb…`) twice from clean, in about 10–12 minutes each. Upstream doesn't hash-check dsd, objdiff or the
  Metrowerks compilers; all five downloaded tools' hashes are recorded for Kaleido's `doctor`.
- **E4b done** (2026-11-03): upstream's packers refuse new map models and texture sets. A ~25-line template-append
  prototype (`docs/research/e4b-template-append.patch`) built a ROM with a new chunk (#1065) and texture set (#409),
  with every original unchanged and valid DSi digests. It plays normally in melonDS in DS mode (owner's check). Found: `AREA_COUNT` caps areas at
  409; each chunk must fit its map type's buffer (86,020 B for most); recoloring shared texture data can be refused.
  ADR 0003 accepted. Details: `docs/research/e4b-map-art.md`.
- **E6a done** (2026-11-03, static): ROM ≈ 231 MiB free of 512 MiB; ARM9 binary far under the DSi's 2.5 MB. **DS-mode
  RAM is the constraint**: the heaps are fixed and the arena starts where the last overlay ends, so all added code and
  static data must fit in ≈ 213 KiB. Heap 1 has 288,256 B left in the field. E6b (runtime free memory, save use) moved
  to Phase 1's harness spike (owner, 2026-11-04). Details: `docs/research/e6-headroom.md`.
- **Phase 0 closed** (2026-11-04): every exit criterion met (`05-roadmap.md`), with E6b in Phase 1 and E7 waiting for
  hardware.
- **E1–E3 built, in-game checks partly pending** (2026-11-03). E3: `configure.py --define` plus a
  `KALEIDO_E3_ALWAYS_CRIT` switch. With the switch off, the build still matches Black 2 with every check; with it on,
  the compiled crit roll is always TRUE and 15 overlays move. E2: the rival's first party unpacks from the built ROM as
  Pikachu Lv 5. E1: the new intro text shows in game (owner). Pending: E1 glyph and line-width details; the rival
  battle in game (E2, E3). Details: `docs/research/e1-e3.md`.
- **E4a done** (2026-11-03): a new zone (header, events, warps both ways, script, text) packs and reads back from
  the built ROM. Appending zones collides with three hard-coded "no zone" values of 615; `KALEIDO_EXTRA_ZONES`
  fixes them, but it changes ARM9 main, which needs the DS ARM7 BIOS to finish the ROM (R-27). Resolved by ADR 0004
  (owner): Tier 1 reuses zone IDs, and Kaleido's dsd change `--allow-stale-secure-area` builds without the BIOS.
  With it, the untouched pin still matches Black 2, and E4a's ROM builds. Details: `docs/research/e4a-new-zone.md`.
- **E5 done** (2026-11-03): a test species inserted after Genesect, as #650, builds into every archive a species
  needs (data, text, sprites, icon, musical, footprint, cry, Pokédex, a Route 19 slot) and reads back from the ROM.
  The engine cost is a matching-neutral patch (`docs/research/e5-species-expansion.patch`): about 40 numbers derived
  from the species list, and a template splice in the two packers that can't add files. The Pokédex save fits 672
  species. Known gaps: Box Search and GTS letter tables, easy-chat word numbering, forms. The Kanto regional Pokédex's
  length is data. Found on the way: one ninja run can link stale objects after a generated header changes (R-28).
  Details: `docs/research/e5-species.md`.
- **E9 done** (2026-11-03): `KALEIDO_SAVE_MAGIC` replaces the save footers' magic and the outside data's (Mystery Gift
  cards, keys). The game reads another game's card, Black 2's included, as empty: New Game only, and no gifts or keys
  taken. The ROM header, and so the save type, stay Black 2's. Verified in the code and in two built games, which
  differ only in their magic words; switch off still matches. Found: even this data-only change to ARM9 main needs
  `--allow-stale-secure-area`, because the ROM records ARM9's compressed size in the secure area (R-27 widened).
  Details: `docs/research/e9-save-identity.md`.
- **E8 done** (2026-11-04): the owner's FireRed dump is FireRed (USA), SHA1 `41cb23d8…`, the first extraction target
  (Q5); it lives in `~/kaleido-work/roms/` and is never committed. Our extractor (`docs/research/e8-frlg-wild.py`):
  - reads Route 1's wild encounters by structure, naming the map by the ROM's own text;
  - gives the same output on every run, which matches pret's table;
  - writes a table that packs into Black 2 (on Route 19, since E4a's zone has no grass).
  The encounter rate is Approximate in Gen 5. Details: `docs/research/e8-extract-encounters.md`.
- **E10 done, partly** (2026-11-03): upstream's dumpers rebuilt 74.7% of `res/` (104,424 of 139,732 files) from the
  Black 2 ROM. With those files in place, the full matching build still gives Black 2's SHA1. Not rebuilt:
  - 13% needs a White 2 ROM;
  - 12% needs Apicula;
  - 88 text and AI files carry upstream's curation.
  So the mirror stays R-03's mitigation, and regeneration is a fallback. Details: `docs/research/e10-regenerate-res.md`.
- Offered upstream (2026-11-03), all open:
  - the dsd change: [fuddlesworth/ds-rom#1](https://github.com/fuddlesworth/ds-rom/pull/1) and
    [fuddlesworth/ds-decomp#2](https://github.com/fuddlesworth/ds-decomp/pull/2); CI hasn't run on either;
  - the depfile fix for R-28: [fuddlesworth/pokebw2#807](https://github.com/fuddlesworth/pokebw2/pull/807), CI waiting
    for a maintainer to approve a first-time contributor.

## Most important findings

1. Upstream's packers can **edit** the original map models and texture sets but can't **add** new ones (R-01).
   Template-append adds them while keeping a template's materials and textures (E4b); a full encoder is needed
   before Phase 4 (ADR 0003).
2. A single-source xdelta from B2 necessarily carries the extracted FRLG content; the owner accepted that (Q1).
   Patches still can't go on GitHub under the brief's rules; the channel is chosen before the first release.
3. B2W2 carts have infrared, a 512 KB FLASH save behind it, and 512 MB of ROM space at most. The game code must stay
   `IREO`. DS Protect must be guarded out in source (R-25).
4. FRLG's grass, surf and Super Rod odds, crit stages and type chart are identical to B2W2's (verified), so much of
   Gen 3 is data-exact.
5. Upstream's incremental build can finish a ROM from objects compiled against old constants after a constant list
   changes (R-28, E5). Until it's fixed, run ninja again until nothing is left to compile.

## Next steps

Phase 1's deliverables (`05-roadmap.md`), in a proposed order:

1. ~~Repo layout, `LICENSE`, `LICENSE-CONTENT`, `CONTRIBUTING.md`, `docs/building.md`, `docs/engine-sync.md`~~: done
   2026-11-04.
2. ~~The engine submodule and the first patches~~: done 2026-11-04. `engine/patches/` holds `--define` (E3), the dsd
   flags (E4a) and `KALEIDO_SAVE_MAGIC` (E9). Verified:
   - with every define off, the patched engine passes every matching check (`e51e6dfb…`);
   - with `KALEIDO_SAVE_MAGIC`, the ROM equals E9's prototype byte for byte;
   - two exports of the series are identical.
   Left out on purpose: E5's species-count patch (no species-expansion scaffolding, `03-architecture.md` §12) and E4b's
   template-append, which joins when Phase 3 adds map art (ADR 0003).
3. ~~`kaleido doctor` and `bootstrap`~~: done 2026-11-04. They are `./kaleido` from the checkout: Python 3.11+, standard
   library only, 31 unit tests on synthetic repositories. A fresh WSL clone bootstrapped to the tested engine tree
   (`60702d25…`) with a working dsd, and `doctor` passed with no warnings. The tool hashes are in `engine/engine.toml`.
   Running ninja until nothing compiles (R-28) belongs to `kaleido build` and `baseline`, next.
4. Partly done 2026-11-04: `./kaleido baseline` and `./kaleido build <game>`, and `content/games/firered/game.json`
   (its own save magic). Verified on the WSL clone:
   - `baseline` matches Black 2 in 8 minutes;
   - the freshly downloaded tools match `engine.toml`'s hashes;
   - `build firered` gives a ROM whose ARM9 carries FireRed's save magic in all 22 places;
   - a rebuild compiles nothing and gives the same SHA1.
   Then `./kaleido extract` and `merge`, with FireRed's first layers: Kanto maps `route_1` to `ZONE_ROUTE_19`, the
   FRLG family extracts Route 1's land encounters there, and the game layer overrides Juniper's first line with
   original text. Verified on the WSL clone with the owner's FireRed:
   - the extracted table is byte-identical to E8's;
   - the merge report records each file's layer and category;
   - the built ROM's Route 19 table and intro line are FireRed's;
   - a rebuild writes and compiles nothing.
   Then `./kaleido validate` (warps, encounter tables, species and levels, region zones; no problems on the full
   merged tree) and `./kaleido patch`:
   - `dist/kaleido-firered.xdelta` (420 KB) rebuilds the built ROM from Black 2, including from a renamed copy;
   - a second patch is byte-identical (xdelta3 3.0.11 with `-A`).
   83 unit tests. This step is done.
5. The emulator harness spike (R-16) and E6b (2026-11-04): py-desmume drove Black 2 headless from power-on to the
   first battle and read RAM through pokebw2's symbols (`docs/research/harness-spike.md`). E6b, DS mode, all
   **Verified** (`docs/research/e6-headroom.md` §5):
   - the arena keeps **226,620 B** unused in every state, the budget for added code and static data; E6a's ≈ 213 KiB
     wrongly counted heap 9, which lives below ARM9;
   - heap 1 has **110,696 B** free in the field, the tightest state (title 317,592; battle 512,856; bag 1,169,528);
   - the save has **92 B** free per copy.
   R-05, R-13 and R-16 are updated. ADR 0005 accepted by the owner (2026-11-04): py-desmume for DS-mode checks, DSi
   mode manual in melonDS. This step is done.
6. CI on GitHub Actions and Dependabot (2026-11-04): `.github/workflows/ci.yml` and `.github/dependabot.yml`
   (`docs/building.md` §6). Built for it:
   - `./kaleido check` (ROM-content guard, layers and games, links);
   - `./kaleido compile`, with engine patch `0004` (`compile_all.py --define`);
   - `validate --no-extract`.
   The framework is now formatted with Ruff. CI's first run found a real bug: a failed series' `git am --abort` needed
   the builder's git identity (fixed, with a test). Verified on the WSL clone:
   - `compile`: 1792 of 1792 files for each define set;
   - `validate firered --no-extract`: no problems;
   - `baseline` still matches Black 2;
   - `build firered` gives the same SHA1 as before (`f64d9a56…`).
   On GitHub, the Engine job takes about 4 minutes. The "Protect main" ruleset requires the `CI` check (2026-11-04).
   This step is done.
   Schema validation followed (2026-11-04): `validate` checks each JSON file the layers wrote against pokebw2's
   schema, with pokebw2's own checker, so CI checks it through `validate --no-extract`. **Verified** on the WSL
   clone:
   - FireRed's merged Route 19 table passes;
   - a layer file with a string for a rate fails, naming the field, the schema and both layers that wrote it.

   Kaleido's own files stay checked by the code that reads them; JSON schemas for them would repeat those checks. Not
   added: a pre-commit hook (only after doing it by hand three times).
7. Reproducibility. A clean clone of `main` (`6c98934`) in a new WSL directory on the owner's machine, built from
   nothing (2026-11-04), matched the first clone. **Verified**:
   - bootstrap gave the same engine commit (`e66725f1c361…`);
   - doctor passed with no warnings, and the freshly downloaded tools match `engine.toml`'s hashes;
   - `baseline` matches Black 2 (`e51e6dfb…`);
   - `build firered` gives `f64d9a56…`;
   - `patch firered` gives the same 420,320-byte patch (`7c4e38f87441bd45fa220041529639bbf1faf94e`).

   Kaleido's dsd binary differs between the two directories, but its ROMs don't. **Assumption**: Rust embeds the build
   path. Left for Phase 1's exit: the same SHA1s from a clean clone on a **second machine** (`docs/building.md`).

Phase 2's deliverables (`05-roadmap.md`, two builds), started 2026-11-04:

1. ~~A Red stub~~: done. `games/red` and the RBY family layer share the Kanto region with FireRed. Red has no source
   ROM, its own save magic (`0x4b524431`), and original intro lines from both its family and its game layer. The
   emulator harness showed Red's line and FireRed's in game.
2. ~~A title per game~~: done. The owner chose the DS menu's title, while the title screen keeps Black 2's art until
   original art exists. Engine patch `0005` adds `configure.py --banner-title`, and each `game.json` names its title.
   The built banners read back "Kaleido / FireRed" and "Kaleido / Red" in every language, and the DSi checks pass.
3. ~~The first B2W2-system switch~~: done. Engine patch `0006`, `KALEIDO_NO_CGEAR`, keeps the C-Gear out of Red.
   `docs/research/b2w2-systems.md` is a first inventory of the systems, with the C-Gear's entry points traced.
   **Verified** on the WSL clone:
   - `baseline` still matches Black 2, and `compile` is clean both with and without the switch;
   - FireRed is unchanged (`688d008d…`);
   - Red builds (`4566ffc8…`), its DSi checks pass, and its patch applies back to it.

   Red's patch grew from about 420 KB to 5.9 MB. The switch shortens a function in ARM9 main, so the code after it
   moves, and so does every reference to it. Any switch that changes code size in ARM9 main will do the same.
4. Left for the exit:
   - both ROMs in melonDS, DS mode;
   - the C-Gear in one game and not the other;
   - each game refusing the other's save.

   The harness can check the last two. It already showed the C-Gear byte, saving and exporting a save on Black 2, but
   the owner set harness testing aside on 2026-11-04, so these are listed under "Deferred to playtesting" for now.

Phase 3 (Pallet Town to Viridian City) has an accepted plan, `docs/plan/08-phase3.md`: eight workstreams in six
steps. The owner took every recommendation on 2026-11-04:
- D1: the story runs on existing Unova maps first, then Pallet Town (and Route 1 if possible) is rebuilt as new maps
  for the art-cost measurement;
- D2: the measured maps are made by the owner or an artist in Blender;
- D3: Oak appears with Juniper's sprite as a placeholder;
- D4: the player stays Nate or Rosa;
- D5: FireRed switches off seasons, Pass Powers, the Unova Pokédex (for a Kanto one) and, after Phase 2's exit check,
  the C-Gear;
- D6: FireRed's encounter rates map to Gen 5's nearest setting by one recorded rule.

Step 1, a walkable Kanto skeleton (2026-11-04):
- The Kanto region maps the nine locations to Unova stand-ins: Pallet Town on Aspertia City, Route 1 on Route 19 and
  Viridian City on Floccesy Town, which Unova's maps already join, plus six interiors.
- Every stand-in, and Aspertia's gate to Route 19, loses Black 2's NPCs, triggers, signs and map scripts and keeps its
  warps.
- Engine patch `0007` (`KALEIDO_NEW_GAME_ZONE`) starts a new game upstairs in the player's house, without Black 2's
  flight over Unova or its opening scene. `game.json`'s `start` names the location.
- Doors that lead to Unova zones outside the nine stay as they are, with Black 2's own contents; new maps replace the
  stand-ins later.

**Verified** on the WSL clone:
- `baseline` still matches Black 2;
- `validate firered` is clean, the ten merged events files included;
- every stand-in reads back with no NPCs, triggers, signs or map scripts, and its warps intact;
- both games build with `KALEIDO_NEW_GAME_ZONE=ZONE_ASPERTIA_CITY_4` (FireRed `a072ae76…`, Red `1f5346d2…`), and
  their patches apply back to them. The patches are now about 5.7 MB each, since `0007` changes ARM9 main too.

Not seen in game yet: the playtest list has it, since harness testing is set aside.

Step 2, FireRed's content on the skeleton, started 2026-11-04 with place names:
- The extractor now decodes Gen 3 text and finds FireRed's table of map section names by its shape.
- The FRLG family's `place_names` recipe names Pallet Town, Viridian City and Route 1 from FireRed's map sections
  88, 89 and 101, onto their stand-ins' places, title-cased as Gen 5 writes them. Red keeps Unova's names until it
  has a source ROM.
- On the way it fixed E8's name lookup, which gave the wrong section for 35 of FireRed's 109 names (Route 1's was
  right).

**Verified** on the WSL clone:
- the merged places read "Pallet Town", "Viridian City" and "Route 1";
- Route 1's encounter table is unchanged (`488c6a6c…`);
- `validate` is clean for both games;
- FireRed builds (`a52ef1cc…`) and its patch applies back to it.

Then the dialogue (`docs/research/frlg-dialogue.md`):
- The `map_text` recipe reads every message that the nine maps' scripts show, 174 in all. It finds each map by its
  group and number and walks its scripts' bytecode.
- It converts them to Gen 5 text: breaks, scrolls and new boxes, and names as word placeholders. Voice fonts are
  dropped.
- It appends them to the stand-ins' text banks, with IDs that say where each comes from (`OaksLab_Text_Npc4_0`).
- A text merge's new `"$append"` object adds messages.
- No reflow was needed: the path's widest line is narrower than 1% of Black 2's own.

**Verified** on the WSL clone:
- `validate firered` is clean, and the merged banks end with FireRed's messages;
- FireRed builds (`3dc66e8e…`) and its patch applies back to it;
- `validate red --no-extract` is clean.

Not on screen yet: nothing names the messages until NPCs, signs and their scripts arrive.

E8's `map_ids` listed two unrelated maps for Pallet Town's section (Route 1's was right). Fixed: it now reads the maps
of the table of map groups (`docs/research/frlg-dialogue.md` §1). **Verified** on the WSL clone: section 0x58 gives
only 3.0 and 4.0 to 4.3, and `extract firered` writes the same files as before, Route 1's encounters (`488c6a6c…`)
included.

Then the people and signs (`frlg-dialogue.md` §5):
- The FRLG family puts FireRed's 22 always-present people and 12 of its signs on Black 2's own NPC and sign spots of
  the stand-ins, with placeholder models.
- It replaces the stand-ins' script files with talk and sign scripts that show the extracted messages.
- People that a story flag hides (Oak, the rival, the starter balls) and signs with no spot wait for step 3.
- `validate` now checks that every event's script is one its zone's script file has.

**Verified** on the WSL clone:
- `validate` is clean for both games;
- FireRed builds (`e5f593ec…`), its nine new script files assembling without a warning, and its patch applies back to
  it.

Then the rival's parties (`docs/research/frlg-trainers.md`), which finish step 2:
- The `trainers` recipe finds FireRed's trainers and prize money table by structure.
- It puts the rival's three Oak's Lab parties (trainers 326 to 328) on Black 2's three first rival battles, each on
  the one whose starter shares its type.
- Each gets its party, the prize and its losing and winning lines. IVs and prize money carry over exactly.
- Black 2's name, class, sprite and AI stay. Items aren't mapped yet, and the rival's parties have none.

**Verified** on the WSL clone:
- `validate` is clean for both games;
- FireRed builds (`bda143d9…`) and its patch applies back to it;
- pokebw2's own `trainer_data.py dump` of the built archives reads the three FireRed parties, prizes and lines back.

Nothing starts the battles until step 3's lab script, which is next: Oak's escort, the starter, the rival battle, the
Parcel errand and the Pokédex (W3, W4).

Step 3, the story, started 2026-11-05:
- **The owner's choices** (`08-phase3.md`):
  - D7: on the stand-ins, Oak talks at the edge of town, then a fade takes both to the lab;
  - D8: the starter is chosen on Black 2's starter screen, offering Kanto's three;
  - D9: the rival is named with Black 2's naming screen when he first appears.
- **Two pull requests.** 3a is the lab: the escort, the starter, the rival battle, Mom's healing and Route 1's Potion.
  3b is the Parcel errand: the Mart, Viridian's old man, the Pokédex and Poké Balls, the Town Map, and the Pokémon
  Center and Mart.
- **Story progress** takes event flags from 0x1F2 and variables from 0x404E. Those are runs of 106 and 34 that no
  Black 2 script, event or C source names (**Assumption**: a flag reached only by arithmetic would escape the scan;
  none of the C literals in those ranges are flags).
- **Engine patch `0008`** (`KALEIDO_KANTO_STARTERS`, D8) makes Black 2's starter screen offer Bulbasaur, Charmander and
  Squirtle.
  - Its sub screen draws the starters' own sprites instead of the archive's drawings of Black 2's starters, scaled as
    those are.
  - Each dark palette is an eighth of each channel: Black 2's dark palettes are roughly that, hand-tuned.
  - Whether a starter's sprite scales cleanly on the sub screen is **Unverified** until the playtest.

**Verified** on the WSL clone, for patch `0008`:
- `baseline` still matches Black 2 (`e51e6dfb…`);
- `compile` compiles all 1,792 C files for every game's defines;
- FireRed builds with `KALEIDO_KANTO_STARTERS` (`c4bd580d…`) and its patch applies back to it;
- clang-format 23.1.1 leaves the patched `psel.c` as it is.

Nothing opens the starter screen until 3a's lab script.

3a, the lab (the FRLG family's scripts on the stand-ins):
- **The escort.** In Pallet Town, Oak (hidden by his flag except for this) calls out from a trigger before Route 1's
  gate, walks up and warns the player. A fade then takes both to the lab (D7).
- **The starter scene.** It runs when the player arrives with the story at 1:
  - the rival is named on Black 2's screen (D9);
  - Oak and the rival speak FireRed's lines;
  - the player chooses on Black 2's starter screen (D8);
  - FireRed's "received" line plays, then a nickname offer;
  - the rival takes the starter strong against the player's.
- **The rival battle.** Heading for the door starts the rival's challenge. The battle is on the trainer that
  matches, the player may lose and go on, as in Black 2's first rival battle, and the party is healed.
- **Mom** heals once the player has a Pokémon. Route 1's clerk gives one Potion, if the bag has room.
- **Shared constants.** `frlg_story.inc` names the story's flags and variable values, and the comparisons the
  scripts make. `VMJumpIf CMP_STACK` jumps when its comparison is false, and `YesNoWin` gives 0 for yes; both are
  **Verified** in `scrcmd_vm.c` and `scrcmd_menu.c`, against the docs' wording.
- **Validation** now also checks the script numbers in the zones' init script tables.

**Verified** on the WSL clone: `validate` is clean for both games, and FireRed builds with the scripts (`e3999055…`),
its patch applying back to it. Nothing of 3a has been seen in game: the playtest row below lists each beat.

3b, the Parcel errand:
- **The Mart's parcel.** On first entering the Viridian Mart after the rival's battle, the clerk calls out and gives
  Oak's Parcel, which is Black 2's Parcel (`ITEM_PARCEL`). It keeps Black 2's name, "Parcel", until item names are
  extracted. After that the clerk asks the player to deliver it, and once it's delivered he runs Black 2's own Mart
  (global script 10110) with its standard, badge-based list. FireRed's own list waits for item extraction.
- **The delivery.** With the parcel, talking to Oak runs the delivery:
  - he takes it and the rival comes back;
  - both get a Pokédex, as Black 2's starter scene gives it: its flag 0x962 and the player-by-gender animation;
  - the player gets five Poké Balls;
  - the rival leaves for his sister's Town Map, with FireRed's lines throughout.
- **Viridian's old man.** Until the delivery he forbids the way north, at the row where Black 2's own story blocks
  Floccesy's upper town, and the player steps back. His granddaughter's lines follow.
- **Daisy** gives the Town Map once the player has the Pokédex, through Black 2's item-receiving script (global 2805),
  if the bag has room.
- **The Pokémon Center's nurse** runs Black 2's healing script (global 2100), so her lines are Black 2's, and the
  Center's PC (global 2108) is back. Its other map scripts stay out: they set up Black 2's Memory Link visitors, and
  one deletes NPCs by number.
- **Not in Phase 3's beats:** FireRed's catching tutorial with the old man, and the Mom-and-Oak lines after the
  delivery.

**Verified** on the WSL clone: `validate` is clean for both games, and FireRed builds with 3b (`96eb2d90…`), its patch
applying back to it. Not seen in game: the playtest row below lists each beat.

Step 4, FireRed's B2W2-system switches (D5), traced in `docs/research/b2w2-systems.md`:
- **Seasons**, patch `0009` (`KALEIDO_NO_SEASONS`): the season follows the DS clock's month and some 30 files read
  it. With the switch it stays spring, so no season banner shows, a new game included.
- **Pass Powers** need no switch. They start only from two of the C-Gear's screens, so a game without the C-Gear has
  none. FireRed's scripts never power the C-Gear on, so it has neither already.
- **The Pokédex**, patch `0010` (`KALEIDO_KANTO_POKEDEX`): the regional Pokédex is Kanto's 151 at their national
  numbers, complete without Mew, and FireRed calls it "KANTO POKÉDEX". Its area, habitat and rating pages stay
  Unova's for now.
- **The C-Gear's switch** (`KALEIDO_NO_CGEAR`, patch `0006`) goes into FireRed after the owner's Phase 2 exit check,
  as D5 says.

**Verified** on the WSL clone, with `0009` and `0010`:
- `baseline` still matches Black 2 (`e51e6dfb…`);
- `compile` compiles every game's defines;
- FireRed builds (`d3e00b92…`) and its patch applies back to it;
- clang-format leaves both patches' files unchanged.

Step 5 changed on 2026-11-06 (D10, ADR 0006): Kanto's maps are to be generated from the player's FireRed with
Black 2's textures and props, on FireRed's own grid and replaceable per map, instead of rebuilt by hand. The plan,
`docs/plan/09-generated-maps.md`, was accepted by the owner the same day. It starts with template-append as an engine
patch and a spike on Pallet Town alone, which the owner plays to judge the look.

The plan's step 1, template-append (2026-11-06):
- **Patch `0011`**, E4b's prototype as an engine patch: a map model or texture set listed after Black 2's starts from
  an original, its template, and is appended. It is tooling only, so it has no define.
- **The chunk check** (`framework/kaleido/chunks.py`): after ninja, `kaleido build` checks every chunk a zone's matrix
  can show against its map type's buffer, which the field never bounds-checks. The buffers run from 40,964 to 344,080
  bytes, not just the 86,020 E4b recorded (`docs/research/e4b-map-art.md` §2).

**Verified**, 2026-11-06:
- `baseline` still matches Black 2 (`e51e6dfb…`), and `compile` compiles every game's defines.
- FireRed builds unchanged (`d3e00b92…`), every chunk within its budget, and its patch applies back to it.
- In the series worktree, on a scratch copy since restored, new entries packed as copies of their templates, every
  original byte-identical. The check named the one copy placed in a zone whose buffer it overflows.

The plan's step 2, the Pallet Town spike (2026-11-06), is built and waits for the owner's playtest:
- **The converter** (`framework/kaleido/mapgen.py`, recipe kind `gba_gen3_map_model`) generates a FireRed map as a
  map model from a template chunk. Kaleido labels each FireRed metatile by kind, and a kit names the template's
  material, height, tree, prop and tile type for each kind (`content/families/frlg/maps/`).
- **The spike game, `firered_spike`:** FireRed's story stays on its stand-ins, so the spike is a game of its own.
  - Pallet Town is generated into Aspertia City's southern overworld cell.
  - A new game starts in front of the player's house.
  - The house, the rival's house and the lab lead into the stand-in interiors.
- **Patch `0012`:** the packer writes a vertex's color and normal only when they change. That brought Pallet Town's
  chunk from 2,656 bytes over its budget to 80,568 of 110,600.
- **Findings:** `docs/research/generated-maps-spike.md`, including the converter's cost and the touch-ups found.

**Verified**, 2026-11-06:
- `baseline` still matches Black 2, and `compile` compiles every define set, the spike's included.
- FireRed builds unchanged (`d3e00b92…`).
- The spike builds, its validation clean and every chunk within budget, and its patch applies back to it.

The owner's first playtest (`ce083c99…`): "some resemblance to Pallet Town but seems a bit off (texturing and some
layout)". The causes and the texture pass that followed are in `docs/research/generated-maps-spike.md` §7:
- the paths were tiled with a border texture;
- the pond had no bed under its see-through water;
- the fence was flat;
- the town stood in an open field.

The model now shows Aspertia City's texture set, so its materials can show more of it:
- sand paths with soft edges;
- the sea;
- red flowers;
- a standing picket fence;
- red mailboxes;
- a forest with trees in front.

The owner chose Black 2's textures over generated art. The textured spike is `022bd2c9…`, its chunk 100,308 bytes of
110,600.

Next: the owner plays the textured spike (the playtest row below) and judges the look. That decides whether the plan's
step 3 goes ahead as written.

`docs/plan/10-next-steps.md` (proposed, 2026-11-08) orders the rest of Phase 3 and outlines Phase 3.5. Its decisions
D11 to D14 wait for the owner. Its step A1 is done (2026-11-08): a `gba_gen3_map_model` recipe now lists every
generated map of one matrix, so two maps no longer write the same `generated/map_models.txt` and matrix patch. A lower
layer that also changes the matrix is refused, since the recipe's merge patch would replace its change.

**Verified**, 2026-11-08: unit tests, including two maps in one matrix; the spike's extract, byte-identical to the
texture pass's.

Step A2 is done too (2026-11-08). The ROM-content guard (`./kaleido check`) also refuses:
- the files a DS ROM unpacks into, by ndstool's and dsd's names (`arm9.bin`, `header_logo.png`, `ov012.bin`, …), and
  anything in an `overlay/` or `arm9_overlays/` directory;
- Nitro files by their magic and byte-order mark (`NARC`, `BMD0`, `BTX0`, sound and 2D graphics);
- BPS, IPS and UPS patches, by extension and magic.

**Verified**, 2026-11-08: unit tests. On the 318 files under `files/` that dsd unpacks from Black 2, the magic check
finds every NARC (308), the sound archive and the two embedded DS ROMs.

Step A3 is done (2026-11-08). The FRLG family's `layer.json` reserves the story's runs, flags 0x01F2 to 0x025B and
variables 0x404E to 0x406F, and `kaleido validate` checks that none of Black 2's scripts or events uses them:
- by a constant from `generated/flags.txt` or `vars.txt`, or a hexadecimal number in a script;
- by an event's `flag` or `var`, as a number, a hexadecimal string or a constant.

Of a file a layer patched, upstream's version is read; a file a layer replaced is the layer's own. Two layers of a game
that reserve the same flags or variables are refused too.

**Verified**, 2026-11-08:
- unit tests;
- on FireRed's merged tree (the texture pass), no problems in Black 2's 1,290 scripts and their events;
- read the same way, Kaleido's own story files show all 11 of their uses.

The story's runs were an **Assumption** from a one-time scan. For scripts and events this check now settles it. A flag
reached by arithmetic, written in decimal in a script, or named in C still escapes it.

Step B has started (2026-11-08) with `./kaleido play <game> <route>`. It runs the built ROM in py-desmume, from its
own environment in `build/harness-venv/`, and drives it with a route under `content/games/<game>/play/`. The route
presses buttons, waits on the game's state, and makes playtest checks. The state is read through the build's link map
(`arm9.o.xMAP`), not dsd's `symbols.txt`: Kaleido's patches move ARM9's data. `g_GameSystem` is at `0x02141114` in
FireRed's build and `0x021410f4` in Black 2's and the spike's. The harness reads:
- through `g_GameSystem`: the running event, the zone, and the saved flags and variables;
- through the field: the player's actor, its tile and its hidden flag.

Each offset is proved by the accessor function that reads it: the harness compares that function's Thumb code with
the code at pokebw2's pin, and stops on a difference.

**Verified**, 2026-11-08:
- **The spike's missing player is the ROM's.** The player's actor has its hidden flag set (`flags 0x27`) in the
  spike's Pallet Town, from a savestate and from a new game.
- **Black 2's control.** Four of E6b's field savestates read `0x23`, not hidden, in Aspertia City (zone 427) and
  zone 428.
- **The spike's first route,** `firered_spike/new_game`, reaches Pallet Town from power-on in about 8,700 frames,
  through both name screens, at tile (42, 750). Its `player-visible` check fails, as it should until step C.
- **Presses before the game boots** leave the screen white for good in py-desmume, so routes wait 900 frames first.
  The cause is **Unverified**.

Not yet: the battle state, temporary flags, saves and the routes for the deferred playtest checks.

Step C's first touch-up is done (2026-11-09): **the player is shown.** Black 2's first field event hides the player
before Aspertia City's opening scripts `0x1d` and `0x1e`, which patch `0007` skips for a game with
`KALEIDO_NEW_GAME_ZONE`. The hiding now sits behind the same `#ifndef`. FireRed and Red also start elsewhere (the
player's room), so the change reaches them too; neither was run in the harness yet (**Unverified**).

**Verified**, 2026-11-09:
- `baseline` still matches Black 2 (`e51e6dfb…`);
- the spike builds (`e64b7438…`), and `firered_spike/new_game` passes every check, `player-visible` included. Its
  screenshots show the player in front of the house;
- FireRed builds (`bc6ccb44…`). Its new game wasn't run in the harness.

`./kaleido play` also switches into `build/harness-venv/` by itself now. It compared resolved interpreters, which are
the same file for a virtual environment and the system.

FireRed's first route, `firered/new_game` (2026-11-09), runs most of the "Phase 3, step 1" playtest row:
- a new game reaches the player's room upstairs (`ZONE_ASPERTIA_CITY_4`), with the player shown and
  `KANTO_VAR_STORY` at `KANTO_STORY_NEW_GAME`;
- the player walks around the room to the stairs, and down them to `ZONE_ASPERTIA_CITY_3`, arriving at (6, 1);
- the player walks out of the front door into "Pallet Town" (`ZONE_ASPERTIA_CITY`).

It passes in 9,778 frames, about 107 s, on FireRed `bc6ccb44…`. A new step, `walk DIRECTION N`, holds a direction
until the player's tile has moved N tiles, and fails where something stops them.

A new game put the player at the room's Fly position, Black 2's (5, 4). That is a blocked tile, the bed, so the player
was drawn over the pillow, though they could walk off it. Black 2 never starts there, since its opening scene places
the player. The Kanto region now moves the room's Fly position to (4, 4), the open floor beside the bed, for FireRed
and Red alike.

**Verified**, 2026-11-09:
- FireRed (`fe7ad58e…`) and Red (`f1f4de14…`) build;
- `firered/new_game` passes from the new start, and its screenshot shows the player standing beside the bed.

Red's new game wasn't run. The rest of the step 1 row (the other doors, the gate, Route 1 and Viridian City) has no
route yet.

The harness got faster (2026-11-09):
- **Checkpoints.** A route can begin with `start ROUTE SAVE`, from another route's savestate instead of from power-on.
  Each savestate records the SHA1 of the ROM it was made on. When the savestate is missing or comes from another
  build, `play` runs that route first.
- **Frame skipping, tried and left out.** py-desmume's `skip_next_frame` before every frame ran FireRed's field at
  87–89 frames per second, against 70–72 drawn. But the screenshots then showed frames from long before (the title
  screen for the player's room). A savestate made so crashed DeSmuME's software 3D renderer when loaded in the lab
  (`_UpdateEdgeMarkColorTable`). Every frame is drawn. Most of the time goes to emulating the CPU, and py-desmume
  offers no switch for DeSmuME's JIT.

**Verified**, 2026-11-09:
- **FireRed's second route,** `firered/lab` (step 3a's first half), starts from `new_game`'s Pallet Town checkpoint:
  - Oak calls out at Route 1's gate and brings the player to the lab;
  - A presses name the rival, pick Charmander on Black 2's starter screen (drawing Kanto's starters on its sub
    screen), and answer the nickname offer;
  - it ends in the lab with `KANTO_VAR_STORY` at `KANTO_STORY_HAS_STARTER`.
- From a stale checkpoint, `lab` ran `new_game` first, 165 s in all. From the checkpoint it took 80 s, both times
  6,038 frames.
- **FireRed's third route,** `firered/rival`, starts from `lab`'s checkpoint. A step toward the door starts the rival's
  challenge, and A presses fight with the first move until the story reaches `KANTO_STORY_RIVAL_BATTLED` and the field
  is back. The battle's length varies from run to run (5,897 and 6,685 frames), since its random numbers follow the
  clock.
- From nothing, `rival` ran `lab`, which ran `new_game`, all passing, in 410 s; each screenshot shows its own scene.
- **FireRed's fourth route,** `firered/route_1` (2026-11-09), starts from `rival`'s checkpoint and passes in 3,559
  frames, 101 s:
  - out of the lab to Pallet Town (39, 739);
  - north through the gate to Route 1 (52, 702);
  - up Route 1 and east into Viridian City;
  - the old man's warning at (112, 670) steps the player back to (112, 671), with the story still at
    `KANTO_STORY_RIVAL_BATTLED`.

  Its path came from the merged tree's collision tiles, the overworld matrix's chunks' `terrain_0.csv`. Route 1's
  walks fight through wild battles with A; none started in that run.
- **FireRed's fifth route,** `firered/parcel` (2026-11-09, step 3b), starts from `route_1`'s Viridian checkpoint and
  passes in 9,536 frames, 132 s:
  - entering Viridian's Mart (a house) has the clerk give the Parcel, and the story reaches `KANTO_STORY_HAS_PARCEL`;
  - back down Route 1, through the gate, and into the lab;
  - talking to Oak (Juniper's look) runs the delivery, and the story reaches `KANTO_STORY_HAS_POKEDEX`, with Black 2's
    Pokédex flag (`EVENT_FLAG_0x0962`) set.

  The routes now chain from a new game to the Pokédex. Not checked by them: the Bag's contents (the Potion, the
  Parcel, the Poké Balls), text, the old man letting the player by afterwards, Daisy's Town Map, the Center and the
  Mart's shop, and everything visual.

Saves and the C-Gear in the harness (2026-11-09):
- **New conditions:** `new-game` and `save-exists` (the save control's bytes), and `cgear` (the field's lower screen
  is the C-Gear's).
- **New steps:** `export-save`, `import-save GAME ROUTE NAME` (another route's save, of this game or another, made
  first if it's missing), `reset`, and `cgear-on` (the save's C-Gear byte, as script command `0x197` sets it).
- **Proved offsets:** each new offset is proved by its accessor's code, like the others. Two layout facts come from
  pokebw2's source rather than checked code: the save table's `blocks` pointer and its 12-byte entries.

**Verified**, 2026-11-09, FireRed `fe7ad58e…` and Red `f1f4de14…`:
- **E9, saving:** `firered/save` and `red/save` save from the field menu (X, then Save). After a reset the save
  loads (`not new-game`), so the title offers Continue.
- **Phase 2 and E9, each game refuses the other's save:**
  - `firered/foreign_save` imports FireRed's own save, which loads, then Red's, which leaves `new-game` set;
  - `red/foreign_save` does the same the other way.

  Black 2's side of E9 (A on a Black 2 save, Black 2 on A's) still waits, since Black 2 isn't a game the harness
  plays.
- **Phase 2, the C-Gear:** with the save's C-Gear turned on, FireRed's lower screen becomes the C-Gear after the field
  restarts (`firered/cgear`, its screenshot showing it). Red's never does (`red/cgear`): patch `0006`'s
  `CGearSettings_IsOn` answers no, so the field puts its blank lower screen there. A first try read the C-Gear's
  `wasOn` byte instead, which follows the player's C-Gear power option, not whether the game has a C-Gear.
- **Isolated saves:** DeSmuME keeps a battery save per ROM file name in `~/.config/desmume/` and loads it with the ROM.
  `play` now opens each run's ROM through a link named for the game and route, and clears that battery before and
  after. Older harness runs used `kaleido-firered.dsv` and `kaleido-red.dsv`, which these routes' first runs left
  holding saves. `play` no longer reads them. They were deleted afterwards, with the owner's go-ahead.

Step C, the spike's grass and path (2026-11-09):
- **The split is FireRed's.** A rendering of FireRed's own Pallet Town from the ROM, beside Kaleido's labels (on the
  builder's machine, never committed), shows the town really is mostly path. The pale, speckled ground between the
  houses is path; grass is only the darker patches around the lots and along the south. The labels match FireRed
  tile for tile. **Verified**, 2026-11-09; this settles the earlier **Unverified** note.
- **The color was the difference.** The kit drew FireRed's pale path with the template's sand (`michi01b`). It now
  draws Aspertia's pale green ground (`michi03b`, its edge `michi03a`), so the town reads as FireRed's light ground.
  That green is brighter than FireRed's near-white path, and closer to the grass, so the lots stand out less. The
  owner kept it over the sand (2026-11-09).
- **The spike rebuilt** (`a3aca316…`). Its `new_game` passes. A new route, `firered_spike/tour`, screenshots the
  house, the pond, the lab and the north edge (closed by forest, as the spike has no Route 1). The pond now shows.

- **The town's name** (2026-11-09). The spike leaves out the FRLG family, whose recipe names the stand-ins, so its
  town kept Aspertia City's place name. The spike's own `place_names` recipe now names Pallet Town from FireRed's map
  section 88. **Verified** on the spike `d4a16e17…`: the merged tree's place reads "Pallet Town", and so does the save
  dialog, which the tour opens and leaves without saving. The banner that names a place on arrival doesn't show on
  leaving a house of the same town, and the spike has no route to arrive from, so the banner is unseen.

Still in step C: the buildings' fit.

For the owner: entering Route 1 shows Black 2's place-name banner with "SPRING" at its right. FireRed builds with
`KALEIDO_NO_SEASONS`, and step 4's playtest row expects no season banner. Whether this is the banner that row means is
**Unverified**.

For routes: the rival's name screen starts empty, so START there (which moves the cursor to OK) leaves nothing to
confirm. A presses type until the name is full, which moves the cursor to OK by itself. At the starter's yes/no
question UP wraps to NO.

Outside Phases 1 and 2:

- E7 waits for hardware.
- Manual in-game checks are batched into a playtest pass (owner's decision, 2026-11-03); the list is under
  "Deferred to playtesting" below. The harness may run some of them.
- Optional, E10's rest: a White 2 dump and Apicula (a third-party download, owner's go-ahead).

The prototypes are on branches of `~/kaleido-work/pokebw2`: `e4b-template-append`, `phase0-e1-e3`, `phase0-e4a`,
`phase0-e5`, `phase0-e8` and `phase0-e9`. E10's regenerated tree is the worktree `~/kaleido-work/e10-res`. The
FireRed dump is `~/kaleido-work/roms/firered.gba`. The harness's virtual environment is `~/kaleido-work/harness-venv`
(py-desmume 0.0.9), and E6b's savestates, screenshots and measurements are in `~/kaleido-work/e6b`.

## Blockers

- No hardware yet (E7; required by Phase 3.5's exit).

## Not verified yet

- Hardware facts come from GBATEK, emulator and loader sources, not from devices.
- Determinism on a second machine: same ROM and patch SHA1s from a clean clone (Phase 1's exit). On the owner's
  machine, rebuilds, patches and a second clean clone are byte-identical (2026-11-04).

## Deferred to playtesting

Manual in-game checks are batched into one playtest pass at the end, not done after each experiment (owner's
decision, 2026-11-03). Experiments proceed on build-level verification. Until then:

| From | Check | Test ROM (never committed) |
| --- | --- | --- |
| E1 | Whether é ♂ ♀ ★ ♪ … all draw as glyphs, and how the over-long second line behaves (the new text itself shows) | `~/kaleido-work/e1-e3/kaleido-e1-e3-test.nds` |
| E2 | The rival at the Aspertia lookout sends out a level 5 Pikachu | same |
| E3 | Every damaging hit in that battle is "A critical hit!", with no crash, although 15 overlays moved | same |
| E4a | Aspertia City's door (warp 6) leads into the new zone: one NPC whose line is "Kaleido E4a: you're in a new zone."; the exit leads back; DS mode with stale secure-area values boots | `~/kaleido-work/e4a/kaleido-e4a-test.nds` |
| E5 | Kaleidomon (#650, Audino's art and cry, Steel/Psychic) appears in Route 19's grass at level 3; its battle sprite, cry, summary and icon show; it can be caught; the Pokédex lists it at #650 with its entry and finds it by search; it goes to the box and the party; it survives save and reload. Also check the egg, a Pokéstar Studios film and the musical still work, and whether Box Search by name misgroups species from K on (`e5-species.md` §8) | `~/kaleido-work/e5/kaleido-e5-test.nds` |
| E8 | Route 19's grass gives FireRed Route 1's wild Pokémon at their levels, with no shaking grass, surfing or fishing encounters | `~/kaleido-work/e8/kaleido-e8-test.nds` |
| Phase 1 | `./kaleido build firered`: the intro's first line is "Kaleido FireRed / This is Phase 1's test layer." (seen in DeSmuME by the harness, 2026-11-04); Route 19's grass gives FireRed Route 1's wild Pokémon (from Phase 3's step 3 on, once the story gives a Pokémon; before then, at `6342c0e`) | `build/firered/kaleido-firered.nds` (rebuild it) |
| Phase 2 | Both ROMs boot in melonDS in DS mode, and the DS menu lists them as "Kaleido / FireRed" and "Kaleido / Red". Red's intro shows its line, then the RBY family's ("This line comes from the RBY family's layer…"). After the first rival battle in Aspertia, FireRed's bottom screen becomes the C-Gear and Red's never does. Each game, given the other's save, offers only New Game | Both games built at `6342c0e`, Phase 2's last commit: Phase 3's skeleton takes Aspertia's story (the rival battle, the C-Gear) out of later builds |
| Phase 3, step 1 | A new game goes from the intro straight to the player's room upstairs, with no flight over Unova and no opening scene, standing on open floor. The stairs lead down. The front door leads out into "Pallet Town" (Aspertia City, still with Unova's names), with no NPCs or scenes. The other doors reach the rival's house and the lab (the Trainers' School). The gate leads through to Route 1 (Route 19), and Route 1 to Viridian City (Floccesy Town), with its Pokémon Center and Mart (a house). Nothing stops the player on the way | `build/firered/kaleido-firered.nds` or `build/red/kaleido-red.nds` (rebuild them) |
| Phase 3, step 2 | The stand-ins show FireRed's names: "Pallet Town", "Route 1" and "Viridian City" as each is entered. Its people stand on the stand-ins, each with a placeholder model, and talking to one shows its FireRed line in a speech box, the player's name filled in. Mom's line differs for a boy and a girl. Pallet Town's five signs read FireRed's text: the town sign as a town board, the houses' and the lab's as building signs, and Trainer Tips. Route 1's sign is a route board, and the upstairs room's, the lab's and Viridian's read too. FireRed's capitals ("POKéMON") show as written. Check line breaks, scrolls and new boxes, and whether the rival's name (`{0100:1}`, Daisy's line and the rival's house sign) shows, since the new game skips the intro that may set it | `build/firered/kaleido-firered.nds` (rebuild it) |
| Phase 3, step 3a | From a new game, walk to Route 1's gate in "Pallet Town": Oak calls out, appears with Juniper's look, walks up, warns, and a fade brings both into the lab facing up. The rival-naming screen opens, then Oak and the rival (Hugh's look) speak. Black 2's starter screen offers Bulbasaur, Charmander and Squirtle; check that its lower screen draws them, scaling cleanly and dimming the two not picked. The chosen one joins at level 5 with FireRed's "received" line and a nickname offer, the party menu works, and the rival takes the starter strong against it. Walking toward the door starts his challenge and battle; check his losing and winning lines (and his name in the winning one). Win or lose, the party is healed and he's gone. Mom heals afterwards. Route 1's clerk gives one Potion, which the Bag shows, and only once | `build/firered/kaleido-firered.nds` (rebuild it) |
| Phase 3, step 3b | After 3a's battle, walking north in "Viridian City" (Floccesy Town's way up) stops at the old man's warning and steps the player back; his granddaughter apologizes. Entering the Mart (a house) has the clerk call out and give the Parcel, which the Bag's Key Items show as "Parcel"; talking to him again asks the player to deliver it. Talking to Oak with it runs the delivery: the rival comes back, the Pokédex animation and FireRed's line play, five Poké Balls arrive, and the rival leaves; the Pokédex then works from the menu. Afterwards the old man lets the player by, the Mart sells (Black 2's list), Daisy gives the Town Map once, the Center's nurse heals with Black 2's sequence, and its PC opens. Note where losing all Pokémon wakes the player, which nothing here sets | `build/firered/kaleido-firered.nds` (rebuild it) |
| Phase 3, step 4 | With the DS clock's month set to any of the year's, FireRed shows no season banner (at a new game or on going outside) and the maps look as in spring. After the delivery, the Pokédex is "KANTO POKÉDEX": its list runs from Bulbasaur to Mew numbered 001 to 151, and the seen and caught counts count only those | `build/firered/kaleido-firered.nds` (rebuild it) |
| Generated maps, step 2 | **The spike, the owner's to judge.** A new game of `firered_spike` starts outdoors in front of the player's house in Pallet Town generated from FireRed. Check that the ground, paths, flower bed, fences, pond, trees and signs stand where FireRed has them, with Black 2's textures, and that Black 2's two houses and larger building stand on FireRed's houses and lab. Walk the edges: trees, buildings, fences and the pond block, and the north exit is closed. The doors lead into the stand-in houses and lab and back out to the same door. Watch the camera, the lights over a day, and anything missing, untextured or floating. Then judge the look | `build/firered_spike/kaleido-firered_spike.nds` (rebuild it), or `~/kaleido-work/spike/kaleido-firered_spike.nds` |
| E9 | Game A saves and reloads (Continue shows). A's `.sav` copied to game B's name: B offers only New Game. A on a Black 2 save (save once in Black 2 first; none exists yet): only New Game. Black 2 on A's save: only New Game | `~/kaleido-work/e9/kaleido-e9-a.nds`, `kaleido-e9-b.nds` |

Risk of waiting: a runtime-only break, such as code that fails after overlays move, surfaces later. Phase 1's emulator
harness (R-16) could run these checks automatically.
