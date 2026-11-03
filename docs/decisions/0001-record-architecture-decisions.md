# 0001. Record architecture decisions

- Status: Accepted
- Date: 2026-11-03

## Context

Kaleido is built by a solo owner with AI agents, on more than one machine, and is meant to let other people join.
Decisions made in a chat or held in an agent's memory are lost to the next session. The founding brief (Section 7)
requires that anyone can pick up the work from the repository alone.

## Options

1. No formal record; decisions live in commit messages and `docs/architecture.md`.
2. Architecture Decision Records (ADRs), one file per decision, in the format Michael Nygard described.
3. A single decisions log file.

## Decision

Use ADRs (option 2) in `docs/decisions/`.

- File name: `NNNN-title-in-kebab-case.md`, numbered in order, never reused.
- Sections: Status, Date, Context, Options, Decision, Consequences.
- Status is one of **Proposed**, **Accepted**, **Rejected**, **Superseded by NNNN**. Only the owner accepts or rejects.
- An accepted ADR is never edited, apart from changing its status line to "Superseded by NNNN". A new ADR replaces it and
  names what it supersedes. Typos may be fixed.
- `docs/architecture.md` describes the current state and links the ADRs that shaped it. When an ADR is accepted, the
  same commit updates `docs/architecture.md` and, if rules change, `AGENTS.md` and `CONTRIBUTING.md`.

## Consequences

- Every architectural choice (engine integration, layering, rulesets, distribution) gets a short, findable record of
  why it was made and what was rejected.
- Agents must check `docs/decisions/` before proposing a change that touches an accepted decision.
- Small overhead per decision; reversals are cheap to record and leave history intact.
