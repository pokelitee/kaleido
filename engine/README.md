# engine

Kaleido's engine: [pokebw2](https://github.com/fuddlesworth/pokebw2) pinned to one commit, plus Kaleido's patch series
(ADR 0002, `docs/decisions/0002-engine-integration.md`). GPL-3.0, as pokebw2 is.

| Path | What |
| --- | --- |
| `pokebw2/` | git submodule pointing at upstream at the pin. It records only a commit ID; no Nintendo data is in this repository |
| `patches/` | Kaleido's engine changes, `NNNN-topic.patch`, applied in order on top of the pin |
| `engine.toml` | upstream URL, optional mirror URL, notes on the pin |

- Every behavior change in a patch sits behind a `KALEIDO_*` define. With all defines off, the patched engine must
  still rebuild Black 2 byte for byte (`e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`).
- Changes that upstream would want are offered upstream first, which shrinks the series.
- Moving the pin: [`docs/engine-sync.md`](../docs/engine-sync.md).

The submodule and the first patches, from Phase 0's prototypes in `docs/research/`, come next in Phase 1.
