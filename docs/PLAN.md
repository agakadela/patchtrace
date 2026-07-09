# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and
  remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as
  separate files.

## Current Phase: Between Phases - Phase 4 Planning Pending

Phase 3 is closed. Durable verification evidence lives in
`docs/VERIFY_LOG.md`, including the 2026-07-08 Phase 3 close entry for the real
`uv run patchtrace run -- codex` dogfood proof.

No active implementation task is selected. Before the next implementation
slice, define Phase 4 here with its goal, boundary, branch/PR rule, active
tasks, and verification method.

Suggested implementation branch: N/A until Phase 4 is defined.

Branch/PR rule: N/A until Phase 4 is defined.

## Active Tasks

- N/A. Choose and write the next phase before implementation work resumes.

## Deferred From Phase 3

- Full `patchtrace analyze` behavior.
- Full claim extraction from real Codex transcript formats.
- Full claim-vs-evidence matching.
- Expanded risk classification beyond simple local evidence signals.
- `patchtrace watch` idle detection and deduplication.
- Optional JSON report output beyond internal run metadata.
- Non-Codex adapters.
- Package publishing, GitHub integration, HTML report, SaaS, auth, database,
  and required LLM analysis.
- Transcript sanitization / command-test signal cleanup for interactive Codex
  ANSI/control noise.

## Rejected For Phase 3

- Placeholder-only reports that ignore available local evidence.
- LLM-based extraction or summarization.
- External service calls.
- Watcher-first design.
- Treating agent summaries as proof.
