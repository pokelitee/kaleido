# framework

Kaleido's tooling, in Python 3.11 or later with the standard library only, GPL-3.0 (`docs/plan/03-architecture.md` §3
and §7). Run it from the repository's root with `./kaleido <command>`; nothing needs installing.

| Path | What |
| --- | --- |
| `kaleido/` | the package and its commands: `doctor`, `bootstrap`, `baseline`, `extract`, `merge` and `build` (`docs/building.md`); `validate` and `patch` follow in Phase 1 |
| `extractors/` | readers for source-game formats, code only: `gba_gen3.py` reads FireRed's wild encounters by structure (from E8's prototype) |
| `tests/` | host-side unit tests with synthetic fixtures (synthetic git repositories, files and ROM-shaped bytes, never ROM data) |
| `schemas/` | Kaleido's JSON schemas (game, layer, provenance): not yet; the code checks the files for now |

Tests:

```bash
python3 -m unittest discover -s framework -t framework
```

Ruff formats and lints this code (settings in `pyproject.toml`); CI runs both checks once it exists.
