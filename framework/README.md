# framework

Kaleido's tooling, in Python, GPL-3.0 (`docs/plan/03-architecture.md` §3 and §7).

| Path | What |
| --- | --- |
| `kaleido/` | the package and its commands: `doctor`, `bootstrap`, `extract`, `merge`, `validate`, `build`, `patch`, `baseline` |
| `schemas/` | Kaleido's JSON schemas (game, layer, provenance) and extensions of upstream's |
| `extractors/` | readers for source-game formats (GBA Gen 3, GB Gen 1): code only, never game data |
| `tests/` | host-side unit tests with synthetic fixtures |

None of these exist yet; Phase 1 adds them (`docs/plan/05-roadmap.md`). The first extractor starts from E8's
prototype, `docs/research/e8-frlg-wild.py`.
