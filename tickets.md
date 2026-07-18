# Tickets

Central ledger managed by `frob ticket` -- one section per ticket.

<!-- ticket:T-0001 -->
```yaml
id: T-0001
title: Fix frob graph build crash on property getter/setter pairs (upstream frob bug)
state: queued
kind: bug
origin: human
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/lograder/output/handlers.py
- src/lograder/process/executable.py
evidence: []
attachments: []
acceptance: []
threat: null
```
## Context

`frob graph build` crashed with `sqlite3.IntegrityError: UNIQUE constraint
failed: symbols.symref` while parsing `src/lograder/output/handlers.py`.
Root cause: `HTMLHandler.output_file` is a `@property`/`@output_file.setter`
pair -- two methods sharing one name in one class -- and frob 0.1.0a0's
graph builder assigns both the same symref, so the second insert violates
the cache's UNIQUE constraint and the whole build aborts.
`src/lograder/process/executable.py` has the same pattern.

This is an upstream frob bug, not a lograder bug -- lograder's source is
correct, idiomatic Python. Filed here (not in the frob repo) as an
adoption note: both files are excluded from `[graph] exclude` in
`frob.toml` as a workaround so `frob graph build`/`frob check` can run at
all. This ticket tracks removing that workaround once frob disambiguates
getter/setter symrefs (e.g. `Class.prop#getter` / `Class.prop#setter`)
upstream, so these two files' obligations get graph coverage again.

## Done report

(pending upstream fix)

<!-- ticket:T-0002 -->
```yaml
id: T-0002
title: Bind frob:tests unit edges across public API (TEST001 backlog)
state: queued
kind: feature
origin: human
created: '2026-07-17'
blocked_by: []
parent: null
scope:
- src/lograder/**
evidence: []
attachments: []
acceptance: []
threat: null
```
## Context

`frob check .` reports 410 TEST001 violations (public function/method has
no `frob:tests` unit edge) across `src/lograder/**`. `TEST001` is set to
`warn` in `frob.toml`'s legacy-adoption baseline, so it does not fail CI
yet, but it is real backlog: most of lograder's existing pytest suite
predates frob and was never bound to the symbols it covers via
`# frob:tests <path>::<symbol>` directives.

Work: for each public symbol flagged, either add a `frob:tests` directive
above its covering test function(s), or -- where no test exists -- write
one. Track progress incrementally; this ticket does not need to close all
410 in one pass. `frob check . --only test` isolates this rule family.

## Done report

(pending)

<!-- ticket:T-0003 -->
```yaml
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
acceptance: []
threat: null
```
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

<!-- ticket:T-0004 -->
```yaml
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
acceptance: []
threat: null
```
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

<!-- ticket:T-0005 -->
```yaml
id: T-0005
title: Adopt strata self-model (design/lograder.strata) and drive frob sys audit clean
state: done
kind: docs
origin: agent
created: '2026-07-18'
blocked_by: []
parent: null
scope:
- design/lograder.strata
evidence:
- tests/test_design_model.py::test_frob_sys_audit_proves_clean
- tests/test_design_model.py::test_strata_model_exists
attachments: []
acceptance: []
threat: null
```
Pilot: model the real package graph (api/exception/common/output/pipeline/process), measured capability surface, and true isolation claims in strata; wire frob sys audit into the check loop.

## Done report

design/lograder.strata landed: 8 nodes (submission/api/exception/common/
output/pipeline/process/data), 15 flows (all measured import edges,
including the real output/pipeline/process package cycle), 5 assert
claims (reach/noflow, all PROVED) plus 1 assume discharging the
THREAT003 CWE-78 obligation that `may "exec"` on `process` drags in.
Capability surface measured with frob.vet._capability scanner per node;
`frob sys audit` exits 0: PROVED across 9 views, self-conformance
PROVED (SYS101 verified falsifiable: a probe `may "net"` on `common`
was correctly flagged, then removed). Regression guard:
tests/test_design_model.py runs `frob sys audit` in CI-with-frob
environments and skips cleanly elsewhere. Flow-level TEST001 coverage
debt (15 warn-severity findings) deferred to T-0006.

<!-- ticket:T-0006 -->
```yaml
id: T-0006
title: Bind unit/integration tests to lograder.strata flows (TEST001 debt from strata
  pilot)
state: queued
kind: feature
origin: agent
created: '2026-07-18'
blocked_by: []
parent: null
scope:
- design/lograder.strata
evidence: []
attachments: []
acceptance: []
threat: null
```
The strata self-model (T-0005) declares 15 flows; each currently has no frob:tests unit edge, adding 15 warn-severity TEST001 findings to the adoption baseline. Bind existing integration tests (tests/integration/ CMake pipelines already exercise pipeline->process->submission paths) via frob:tests directives, or add targeted tests, once the model has stabilized. Mirrors typani's T-0005 debt-ticket pattern.
