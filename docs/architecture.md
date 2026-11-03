# Architecture

The architecture as it exists now. The full design is in `docs/plan/03-architecture.md`; this file tracks what is
decided and what is built.

## Built

Nothing yet: the repository holds documentation only. Phase 1 (`docs/plan/05-roadmap.md`) builds the skeleton.

## Decided

| Decision | Record |
| --- | --- |
| Architecture decisions are ADRs in `docs/decisions/` | ADR 0001 |
| pokebw2 is a git submodule pointing at upstream, pinned to one commit; Kaleido's engine changes are a patch series in `engine/patches/`, each behind a `KALEIDO_*` define; with every define off the engine rebuilds Black 2 byte for byte | ADR 0002 |
| Patches carry the extracted content they add (one xdelta per game against the B2 ROM) | `07-open-questions.md`, Q1 |
| Every build fits DS mode (4 MB, DS Lite); DSi mode is never required | Q4 |
| Mechanics that differ between Gen 5 and an original game, and B2W2-only systems, are per-game compile-time switches chosen in each game's config | Q6, Q7 |
| Original art and data are CC BY-SA 4.0; engine changes and tooling are GPL-3.0 | Q8; brief |
| Gen 1 games use Gen 1 rules on Gen 5 data structures | Q9 |
| Generic engine and tool work is offered upstream | Q10 |
