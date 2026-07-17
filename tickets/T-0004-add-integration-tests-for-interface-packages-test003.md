---
id: T-0004
title: Add integration tests for interface packages (TEST003)
state: queued
kind: feature
origin: human
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/lograder/common/**
- src/lograder/exception.py
- src/lograder/output/**
- src/lograder/pipeline/**
- src/lograder/process/**
- scripts/**
evidence: []
attachments: []
---

## Context

`frob check .` reports 6 TEST003 violations: `scripts`, `src/lograder/common`,
`src/lograder/exception.py`, `src/lograder/output`, `src/lograder/pipeline`,
and `src/lograder/process` are each derived as an "interface" (a package
whose public symbols are imported elsewhere) with 0 integration-kind
`frob:tests` edges, below `min_integration = 1`. `TEST003` is `warn` in the
adoption baseline.

Work: for each of the six, add or bind at least one integration test via
`# frob:tests <path> kind="integration"` above a test that exercises the
package's public surface end-to-end (not just unit-level). lograder's
`tests/integration/` tree already has real CMake-project-driven integration
tests for several of these (e.g. pipeline/process); those likely just need
the directive added, not new tests written, for `src/lograder/pipeline`
and `src/lograder/process`. `src/lograder/common`, `exception.py`, and
`scripts` may need new coverage. `frob check . --only test` isolates this
rule family; `TEST006` (1 violation: no coverage stamp) is also open --
run `make coverage` to close it once `frob.gates.stamp_coverage` wiring is
added to the Makefile.

## Done report

(pending)
