# Status

Last updated: 2026-11-04

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
B2W2-system switch (Red has no C-Gear). Phase 3 has so far laid a walkable Kanto skeleton on Unova stand-ins (step 1)
and is extracting FireRed's content onto it (step 2). The owner's answers are in `docs/plan/07-open-questions.md`, and
what is decided so far is in `docs/architecture.md`.

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

Not on screen yet: nothing names the messages until NPCs, signs and their scripts arrive. E8's `map_ids` also lists two
unrelated maps for Pallet Town's section (Route 1's is right); the note records it for a separate fix.

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

Next in step 2: the rival's parties.

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
| E9 | Game A saves and reloads (Continue shows). A's `.sav` copied to game B's name: B offers only New Game. A on a Black 2 save (save once in Black 2 first; none exists yet): only New Game. Black 2 on A's save: only New Game | `~/kaleido-work/e9/kaleido-e9-a.nds`, `kaleido-e9-b.nds` |

Risk of waiting: a runtime-only break, such as code that fails after overlays move, surfaces later. Phase 1's emulator
harness (R-16) could run these checks automatically.
