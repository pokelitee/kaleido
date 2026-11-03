# 07 — Open questions

Status: **answered by the owner on 2026-11-03.** The questions below are kept as asked, ranked by how much each one
blocked the architecture; this table records the answers. Q6 (mechanics), Q7 and Q9 differ from the
recommendations. The final mechanics decision (Gen 5 for every game) also replaces the brief's ruleset requirement
(Sections 4 and 5).

## Answers

| Q | Decision | As recommended? |
| --- | --- | --- |
| Q1 | Patches carry the extracted content they add: one xdelta per game against the B2 ROM. The publishing channel is decided before the first release; until then the brief's "no ROM-derived data on GitHub" rule stands, so no GitHub Releases. | Yes |
| Q2 | ADR 0002 accepted: pokebw2 as an upstream submodule plus a patch series. | Yes |
| Q3 | Repurpose Unova chunks for the Phase 3 prototype; build a glTF → Nitro encoder that can add models and texture sets before Phase 4, offered upstream. Provisional until E4b. | Yes |
| Q4 | No hardware yet: E7 waits for devices. DS mode is the hard limit: every build must fit 4 MB and run on a DS Lite; DSi mode is tested but never required. | Yes |
| Q5 | Target whichever revision the owner dumps; one revision per game to start; each game builds from its own ROM. | Yes |
| Q6 (mechanics) | **Every game uses Gen 5 mechanics**, with B2W2's move data as is. The ruleset mechanism is dropped until some game needs a variant. Gen 5 decides how things work (battle and field rules, move data, species stats, types and abilities); the original game decides what is in it (story, dialogue, maps, trainers, encounters, items, learnsets and TM contents). Replaces two earlier answers the same day: per-game mechanic switches, then a Gen 3 default for FRLG. | **No** (recommended original mechanics) |
| Q6 (music) | Prototype converting one FRLG song from the builder's ROM in Phase 3, then decide. | Yes |
| Q7 | Each B2W2-only system is a **per-game compile-time switch**; each game's config picks. | **No** (recommended disabling all) |
| Q8 | Original art and data: **CC BY-SA 4.0**. | Yes |
| Q9 | Superseded by Q6: Red, Blue and Yellow use Gen 5 mechanics too (Gen 5 type chart, stats, crits and species typing). First answered "Gen 1 rules on Gen 5 data". | **No** |
| Q10 | Offer generic engine and tool work upstream; tag each release's source commit. | Yes |

## Top 10

### Q1. May a patch carry extracted FireRed content, and where may patches be published?

A single-source xdelta from Black 2 to Kaleido FireRed necessarily contains every byte the build added, including
FireRed dialogue, parties and encounter tables extracted from the builder's ROM. The brief allows that only "where
unavoidable". The alternative is a player-side builder that takes both the B2 and the FireRed ROM and does the
extraction on the player's machine. That tool would be a second distributable (Python or a small native app) and
changes Phase 1's design. Separately, patches are ROM-derived, and the brief forbids ROM-derived data on GitHub. That
rules out GitHub Releases as written.

- Blocks: Phase 1 pipeline and distribution design (R-06).
- Recommendation: accept that patches carry extracted content (the common practice for ROM hacks, and xdelta is what
  the brief asks for), and choose a non-GitHub channel when the first release nears. If not, the two-ROM builder is
  added to Phase 1.

### Q2. Accept ADR 0002 (engine as an upstream submodule plus a patch series)?

- Blocks: Phase 1 repo layout and bootstrap.
- Recommendation: accept. A GitHub fork would be public and would publish ~140k Nintendo assets under your account. A
  private mirror would host them privately. The patch series keeps both out of anything you own.

### Q3. How should new map art get into the ROM?

Upstream's packers can edit the 1,065 original map models and 409 texture sets but can't add new ones, new materials or
new draw calls (R-01). Kanto needs hundreds of new chunks.

- Options: (a) write a glTF → Nitro encoder that can add models and texture sets, and offer it upstream (largest engine
  task in Tier 1; upstream may build it first); (b) repurpose Unova chunks and texture sets within their limits (no
  tooling, heavy art constraints); (c) both: (b) for the Phase 3 prototype, (a) before Phase 4.
- Blocks: Phase 3 art production and the art estimate.
- Recommendation: (c), decided for real after E4b.

### Q4. Which hardware and modes must be supported?

The brief leaves hardware as "owner to state". DS Lite runs Black 2 in DS mode with 4 MB of main RAM; DSi and 3DS can
also run it in DSi mode with 16 MB. On a DSi or 3DS, the ARM9 binary is limited to 2.5 MB even in DS mode (GBATEK). A
modified hybrid can't boot in DSi mode from the system menu (the RSA signature can't be redone), only through loaders
such as nds-bootstrap or Unlaunch. If DS Lite is a target, every build must fit DS-mode memory.

- Needed: devices (DS Lite / DSi / 3DS), flashcarts and loaders you own.
- Blocks: E7, the memory budget (R-05), the DSi-hybrid handling (R-04).
- Recommendation: DS mode on DS Lite is the hard limit; DSi mode is tested but never required.

### Q5. Which FireRed and LeafGreen revisions, and does each game need its own ROM?

FRLG have rev 0 and rev 1 dumps with different SHA1s (`docs/research/peripheral-tools.md`). Each supported revision
needs its own offset tables.

- Blocks: extraction recipes (Phase 1), E8.
- Recommendation: one revision per game to start (whichever you own), and each game builds from its own ROM
  (LeafGreen from LeafGreen).

### Q6. Where Gen 5 and the original game differ, which wins?

Examples: reusable TMs (Gen 5) vs single-use (Gen 3); Gen 5 move data vs Gen 3 values; B2W2's experience formula; the
Gen 5 encounter-rate model; six HMs vs FRLG's eight; Gen 5 hidden abilities; and audio: FRLG's songs converted from the
GBA (a converter we would write), new arrangements, or B2W2 tracks.

- Blocks: ruleset scope (how many engine variants), the music pipeline (R-24).
- Recommendation: original mechanics wherever the brief's fidelity list covers them (data and rulesets), Gen 5
  presentation for everything else. Music: prototype converting one FRLG song in Phase 3 before committing.

### Q7. Which B2W2 systems stay in a Kanto game?

C-Gear, Pass Powers, Entralink, Join Avenue, seasons, Hidden Grottoes, PWT, Medal Rally, Pokéstar Studios, Memory Link,
Unova Pokédex, Wi-Fi and IR features.

- Blocks: engine scope, RAM and overlay budget (R-15).
- Recommendation: disable all of them for FRLG and RBY; reconsider seasons for later games.

### Q8. Which license for original art and data?

- Recommendation: **CC BY-SA 4.0**. It is one-way compatible with GPL-3.0 (Creative Commons, 2015), so the art can
  ship in GPL builds and be reused by GPL projects. The alternative, CC BY-NC-SA 4.0, states non-commercial intent but
  isn't GPL-compatible.

### Q9. How faithful must Red, Blue and Yellow be?

Exact Gen 1 needs a single Special stat, DVs, Stat Exp, a 15-type chart, Speed-based crits, the 1/256 miss, Gen 1 move
and status quirks, and no abilities, held items, genders, natures or shinies. Most of these fight Gen 5's Pokémon
structure, save and UI.

- Blocks: Phase 5 engine scope; whether `gen1` touches the Pokémon data structure.
- Recommendation: "Gen 1 rules on Gen 5 data": exact battle formulas and type chart through rulesets, Gen 1 base data
  mapped onto Gen 5 fields (Special → SpA = SpD), and documented Approximations for the data model. Glitches such as
  MissingNo. are out of scope. `01-feasibility.md` lists each item.

### Q10. What is Kaleido's public footprint?

Two linked choices. (a) Offer generic engine and tool work upstream (public pull requests to pokebw2 from your
account)? That shrinks our patch series (R-02). (b) When patches ship, the GPL requires the corresponding source to be
available to recipients (R-07). The repository has been public since 2026-11-03, so (b) reduces to naming each
release's source commit.

- Recommendation: yes to (a) for generic tooling; for (b), tag the exact source commit of each release and link it in
  the release notes.

## Brief defaults marked [CONFIRM]

| Default | Recommendation |
| --- | --- |
| Base ROM: Black 2 (USA/Europe) | Keep. It is upstream's primary version, and W2's differences don't matter to Kaleido. |
| English only | Keep. Upstream's text pipeline is English-first; other languages only change text banks later. |
| melonDS primary, DeSmuME secondary | Keep. melonDS has real DSi mode (with DSi BIOS, firmware and NAND dumps); DeSmuME doesn't, but is easier to automate headless (py-desmume). Neither has a headless Lua mode on Linux (`docs/research/hardware-and-rom.md`). |
| Hardware | Needs an answer (Q4). |
| Solo owner + agents, open to others | Keep. The repo records and `AGENTS.md` are written for that. |
| Private repo | **Decided 2026-11-03: public.** The owner made the repository public to unblock GitHub features. It holds no ROM or Nintendo content; the rules in `AGENTS.md` keep it that way. |

## Requirements challenged

- **"Never include other-game content in patches beyond what is unavoidable"** and **xdelta distribution** pull against
  each other (Q1).
- **"Never put ROM-derived data in GitHub"** also covers patches, so it rules out GitHub Releases (Q1).
- **Generation rulesets and exact Gen 1 quirks**: most clash with Gen 5 data structures. The owner dropped them: every
  game uses Gen 5 mechanics (Q6, 2026-11-03).
- **Phase 2 with two builds differing by ruleset**: with no rulesets, Phase 2's two builds (FireRed and a Red stub)
  differ by a compile-time B2W2-system switch and data instead (`05-roadmap.md`).
- **"Gen 5-style Kanto tilesets"**: blocked by R-01 until a new-map-art route exists (Q3).
