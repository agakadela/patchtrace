# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and
  remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as
  separate files.

## Current Phase: None

Phase 4 closed on 2026-07-12. Durable fixture, quality-gate, and real Codex
dogfood proof lives in `docs/VERIFY_LOG.md` and git history.

No next phase has been selected. Use `$aga-spec` and `$aga-plan` before new
implementation work.
