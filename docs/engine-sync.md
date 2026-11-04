# Syncing the engine with upstream

How the pin moves (ADR 0002, `docs/plan/03-architecture.md` §4). A sync is deliberate: chosen for a reason, never
automatic (R-02). `kaleido engine export` doesn't exist yet: until it does, export the series with
`git format-patch --zero-commit --no-signature --no-numbered` and fixed dates ([`engine/README.md`](../engine/README.md)).

The pin is `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (2026-10-31), recorded in `engine/pokebw2` (the submodule),
`docs/plan/02-foundation.md` and `docs/research/pokebw2.md`.

## Before

1. **Choose the commit** and read upstream's log since the pin for:
   - renamed symbols or constants (`rename_symbol.py`, `rename_constant.py`), which can break patches and content;
   - changed tool versions in `configure.py` (dsd, wibo, sjiswrap, objdiff, mwccarm);
   - changed packers or `res/` formats.
2. **Check Kaleido's upstream pull requests.** A merged one retires its patch or tool fork:
   - fuddlesworth/ds-rom#1 and fuddlesworth/ds-decomp#2: dsd's `--allow-stale-secure-area`;
   - fuddlesworth/pokebw2#807: depfile paths (R-28).

## The sync

All on a branch:

1. Move `engine/pokebw2` to the new commit and stage that pointer. `kaleido doctor` reports the staged pointer as a
   failure until the sync is committed; that is expected here and nowhere else.
2. `kaleido bootstrap` applies `engine/patches/` with `git am`. Fix conflicts on the engine branch, then
   `kaleido engine export` writes the series back.
3. `kaleido doctor`: new tool versions get their hashes recorded (R-12). If upstream's dsd changed, rebase Kaleido's dsd
   patch onto its new `ds-rom` and `ds-decomp` commits and rebuild it.
4. `kaleido baseline`: with every define off, the build must give Black 2's SHA1 `e51e6dfb…`. Run ninja until nothing
   is left to compile (R-28).
5. Build every game, and run `kaleido compile`, the tests and validation. The validator reports content that names a
   renamed constant. CI runs the checks that need no ROM, and its tool cache follows `engine/engine.toml`'s hashes.

## After

- One commit holds the new pointer, the updated series and any new tool hashes. It also updates the pin in
  `02-foundation.md` and `docs/research/pokebw2.md`, and a line in `docs/status.md`.
- Anything the sync couldn't verify goes into the pull request.
