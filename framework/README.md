# framework

Kaleido's tooling, in Python 3.11 or later with the standard library only, GPL-3.0 (`docs/plan/03-architecture.md` §3
and §7). Run it from the repository's root with `./kaleido <command>`; nothing needs installing.

| Path | What |
| --- | --- |
| `kaleido/` | the package and its commands. So far `doctor` and `bootstrap` (`docs/building.md`); `extract`, `merge`, `validate`, `build`, `patch` and `baseline` follow in Phase 1 |
| `tests/` | host-side unit tests with synthetic fixtures (synthetic git repositories and files, never ROM bytes) |
| `schemas/` | Kaleido's JSON schemas (game, layer, provenance): not yet |
| `extractors/` | readers for source-game formats: not yet. The first starts from E8's prototype, `docs/research/e8-frlg-wild.py` |

Tests:

```bash
python3 -m unittest discover -s framework -t framework
```

Ruff formats and lints this code (settings in `pyproject.toml`); CI runs both checks once it exists.
