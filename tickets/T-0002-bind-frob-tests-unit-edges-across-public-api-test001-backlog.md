---
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
---

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
