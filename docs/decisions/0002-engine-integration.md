# 0002. Integrate pokebw2 as an upstream submodule with a patch series

- Status: Proposed
- Date: 2026-11-03

## Context

Kaleido builds on [fuddlesworth/pokebw2](https://github.com/fuddlesworth/pokebw2), a GPL-3.0 matching decompilation of
Black 2 and White 2. Facts from `docs/research/pokebw2.md` (commit `41f42ca`, 2026-10-31):

- Upstream commits ~140k extracted Nintendo assets in `res/` (139,732 files).
- Upstream moves fast: 13–236 commits a day in late October 2026, with frequent renames of symbols and constants.
- The build needs the user's base ROM; matching is checked by SHA1.
- GitHub forks of public repositories are always public ("Public repository forks are public", GitHub Docs, fetched
  2026-11-03). Kaleido's own repository is public as well (owner's decision, 2026-11-03).

The brief (Section 4) asks for the option that best handles upstream sync cost, keeps Nintendo assets out of our repo,
and is reproducible.

## Options

### (a) Submodule of our own fork, engine changes on a branch

- A GitHub fork is public, so it would republish upstream's ~140k extracted Nintendo assets under the owner's account.
  A private mirror (push of a clone to a new private repo) keeps them out of public view, but the owner still hosts
  them in a repo they control.
- Sync: merge or rebase upstream into the branch. Ergonomic for development.
- Reproducible: yes (submodule commit).

### (b) Vendored copy with a patch series

- Copies `res/` into our repo: fails the asset criterion outright.
- Sync: re-vendor (thousands of changed files per sync) and re-apply patches.

### (c) Submodule pointing at upstream itself, engine changes as a patch series in our repo (proposed)

- Our repo stores only the submodule's commit ID and our patches. No Nintendo assets in anything we host.
- Sync: re-apply the series on a new upstream commit with `git am -3`, resolve, re-export. With a small series, cost
  grows with how much of the engine we touch, not with upstream's volume.
- Reproducible: upstream commit ID + patch files are content-addressed. `kaleido bootstrap` applies them the same way
  everywhere.
- Risk: depends on upstream staying reachable (a takedown, or a history rewrite, though upstream's rules forbid
  force-pushes). Mitigated by an optional owner-controlled mirror outside GitHub that `engine/engine.toml` can point
  at, and by testing whether `res/` can be regenerated from a user's ROM with upstream's own extraction scripts
  (experiment E10).

## Decision (proposed)

Option (c).

- `engine/pokebw2` is a submodule of `https://github.com/fuddlesworth/pokebw2`, pinned to one commit.
- `engine/patches/NNNN-topic.patch` is the ordered series. It is the source of truth. Developers work on a local branch
  created by `kaleido bootstrap` and export with `kaleido engine export` (deterministic `git format-patch`).
- Every behavior change is behind a `KALEIDO_*` define. With all defines off and no content layers, the patched engine
  must rebuild Black 2's SHA1 (`kaleido baseline`). This runs before any series change merges and on every sync.
- Generic improvements (a `--define` option for `configure.py`, packers that can add new map models and texture sets)
  are offered upstream first.
- Upstream is synced deliberately, not continuously: when we need an upstream change, or on a schedule the owner picks
  (proposed: monthly). Procedure in Phase 1's `docs/engine-sync.md`.

## Consequences

- Our repo stays small and free of Nintendo assets; the owner's account hosts no extracted data.
- A fresh clone needs network access to upstream (or the mirror) for bootstrap.
- Developers have one extra step (export the series) compared with a fork branch. The CLI hides it.
- Large engine features become long patches that conflict more on sync. That is a reason to upstream generic work and
  keep Kaleido-specific changes narrow and flag-guarded.
- Upstream renames can break both patches and content references to constants. Sync must run full validation and
  every game build (R-02).
