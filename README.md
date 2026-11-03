# Kaleido

Recreations of earlier games of the series in Black 2/White 2 presentation, built on the
[pokebw2](https://github.com/fuddlesworth/pokebw2) decompilation. Each game builds to its own Nintendo DS ROM and ships
as an xdelta patch against the player's own Black 2 dump. No ROMs or game data are included.

## Getting started

Nothing is buildable yet. The project has finished planning and is waiting for approval before Phase 0
experiments. See [`docs/status.md`](docs/status.md).

## Architecture

Engine (pinned pokebw2 + a patch series) → framework (layering, provenance, extraction) → region → game
family → game. Details in [`docs/plan/03-architecture.md`](docs/plan/03-architecture.md).

## Documentation

Start with [`AGENTS.md`](AGENTS.md), which maps the docs. Plans are in [`docs/plan/`](docs/plan/), decisions in
[`docs/decisions/`](docs/decisions/), research in [`docs/research/`](docs/research/).

## Contributing

Read [`AGENTS.md`](AGENTS.md) for the rules (never commit ROMs or ROM-derived data; never copy unlicensed code).
`CONTRIBUTING.md` arrives in Phase 1.

## License

Engine changes and tooling: GPL-3.0, as required by pokebw2. Original art and data: CC BY-SA 4.0. License files are
added in Phase 1.
