---
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
---

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
