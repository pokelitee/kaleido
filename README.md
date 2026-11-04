# Kaleido

Recreations of earlier games of the series in Black 2/White 2 presentation, built on the
[pokebw2](https://github.com/fuddlesworth/pokebw2) decompilation. Each game builds to its own Nintendo DS ROM and ships
as an xdelta patch against the player's own Black 2 dump. No ROMs or game data are included.

## Getting started

Nothing is playable yet. Phase 0's experiments are done, and Phase 1 is building the framework skeleton; see
[`docs/status.md`](docs/status.md). Until the `kaleido` commands exist, [`docs/building.md`](docs/building.md)
describes how to build the engine by hand.

## Architecture

Engine (pinned pokebw2 + a patch series) → framework (layering, provenance, extraction) → region → game family →
game. The repository has `engine/`, `framework/`, `content/` and `docs/`. Details in
[`docs/plan/03-architecture.md`](docs/plan/03-architecture.md); what is built so far in
[`docs/architecture.md`](docs/architecture.md).

## Documentation

Start with [`AGENTS.md`](AGENTS.md), which maps the docs. Plans are in [`docs/plan/`](docs/plan/), decisions in
[`docs/decisions/`](docs/decisions/), research in [`docs/research/`](docs/research/).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Above all: never commit ROMs or anything extracted from them, and never copy
code from unlicensed projects.

## License

Code (the framework, engine patches and tools): GNU GPL v3.0, [`LICENSE`](LICENSE), as pokebw2 is. Original art and
data: CC BY-SA 4.0, [`LICENSE-CONTENT`](LICENSE-CONTENT).
