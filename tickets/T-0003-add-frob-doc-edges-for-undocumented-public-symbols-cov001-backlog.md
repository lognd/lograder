---
id: T-0003
title: Add frob:doc edges for undocumented public symbols (COV001 backlog)
state: queued
kind: docs
origin: human
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/lograder/**
- scripts/**
evidence: []
attachments: []
---

## Context

`frob check .` reports 751 COV001 violations (public symbol has no `doc`
edge) -- the largest single rule family in the legacy backlog. `COV001` is
`warn` in `frob.toml`'s adoption baseline. Many of these symbols already
have real docstrings; COV001 fires because frob requires an explicit `doc`
facet edge (per project policy, see `docs/gates.md`), not just docstring
presence, so this is largely an annotation/binding pass rather than a
prose-writing pass.

Work: sweep `src/lograder/**` and `scripts/**`, adding `frob:doc` /
docstring-facet bindings per `docs/graph.md`'s directive syntax. Prioritize
the packages with the widest fan-out first (`src/lograder/process/registry`
and `src/lograder/pipeline/test` have the largest counts per
`frob check`'s exports summary). `frob check . --only coverage` isolates
this rule family.

## Done report

(pending)
