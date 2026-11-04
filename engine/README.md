# engine

Kaleido's engine: [pokebw2](https://github.com/fuddlesworth/pokebw2) pinned to one commit, plus Kaleido's patch series
(ADR 0002, `docs/decisions/0002-engine-integration.md`). GPL-3.0, as pokebw2 is.

| Path | What |
| --- | --- |
| `pokebw2/` | git submodule pointing at upstream at the pin (`41f42ca`, 2026-10-31). It records only a commit ID; no Nintendo data is in this repository. `git submodule update --init --depth 1` fetches it |
| `patches/` | Kaleido's engine changes, `NNNN-topic.patch`, applied in order with `git am` |
| `engine.toml` | upstream URL, optional mirror URL, the Black 2 baseline SHA1, and how Kaleido's dsd is built |
| `dsd/` | Kaleido's change to dsd (MIT, as dsd is), until upstream takes it |

## The series

| Patch | What | Prototype |
| --- | --- | --- |
| `0001` | `configure.py --define NAME[=VALUE]`: a macro for the code and scripts | E3 |
| `0002` | `configure.py --arm7-bios PATH` and `--allow-stale-secure-area`, passed to `dsd rom build` | E4a, ADR 0004 |
| `0003` | `KALEIDO_SAVE_MAGIC`: each game's own save magic | E9 |
| `0004` | `compile_all.py --define NAME[=VALUE]`, so CI compiles each game's defines without a ROM | Phase 1 CI |
| `0005` | `configure.py --banner-title TEXT`: the DS menu's title, in every language | Phase 2 |
| `0006` | `KALEIDO_NO_CGEAR`: a game without the C-Gear, the first B2W2-system switch (`docs/research/b2w2-systems.md`) | Phase 2 |
| `0007` | `KALEIDO_NEW_GAME_ZONE`: where a new game starts (a zone's Fly position), without Black 2's flight over Unova and opening scene | Phase 3 |

- Every behavior change sits behind a `KALEIDO_*` define. With all defines off, the patched engine must still rebuild
  Black 2 byte for byte (`e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`).
- Patches come from `git format-patch --zero-commit --no-signature --no-numbered` with fixed dates, so exporting an
  unchanged series gives the same files, and adding a patch leaves the others' files as they were.
- Changes that upstream would want are offered upstream first, which shrinks the series. `0001`, `0002`, `0004` and
  `0005` are candidates.
- Moving the pin: [`docs/engine-sync.md`](../docs/engine-sync.md).
