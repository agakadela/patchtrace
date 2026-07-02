# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and
  remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as
  separate files.

## Current Phase: Phase 1 - Python V0 Spec And Foundation Decisions

Goal: define PatchTrace Python as a Codex CLI session recorder and local
verification package before implementation starts.

Current accepted direction:
- Primary full workflow: `patchtrace run -- codex`.
- Manual fallback: `patchtrace analyze`.
- Secondary safety net: `patchtrace watch`, limited when no transcript exists.
- Required artifacts: `SUMMARY.md`, `AGENT_FEEDBACK.md`,
  `VERIFICATION_BRIEF.md`, plus raw run material under `.patchtrace/runs/`.
- Stack: Python >=3.11, `uv`, Typer, Pydantic v2, Pexpect, pytest, Ruff, mypy.
- Package convention: `src/patchtrace/<capability>/...`.
- Boundary: local-first, no required LLM, no external calls by default.

## Active Tasks

- [x] Capture Python V0 product spec in `docs/SPEC.md`.
- [x] Capture foundation architecture in `docs/ARCHITECTURE.md`.
- [x] Capture foundation decision in `docs/decisions/ADR-0001-project-foundation.md`.
- [x] Update domain language in `CONTEXT.md`.
- [x] Update README and agent command references away from TypeScript prototype assumptions.

## Next Phase Candidate: Phase 2 - Feedback Loops And CLI Scaffold

Use `$aga-plan` before implementation.

Candidate goal: scaffold the Python package, local CLI, test/lint/typecheck/build
loops, and a fake-command PTY capture path before real analyzer behavior.

Candidate first vertical slice:
- `uv` project with `pyproject.toml` and console script.
- `patchtrace --help` and `patchtrace run -- <fake command>` smoke path.
- run folder created under `.patchtrace/runs/<run-id>/`.
- transcript captured for a fake interactive command.
- minimal `SUMMARY.md` generated from the run metadata.
- `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src tests`, `uv run pytest`, and `uv build` pass.

## Deferred

- Real Codex CLI dogfood test after fake-command PTY capture works.
- Full claim extraction from real Codex transcript formats.
- `patchtrace watch` idle detection details.
- Optional JSON report output beyond internal run metadata.
- Non-Codex adapters.
- Package publishing, GitHub integration, HTML report, SaaS, auth, database, and
  required LLM analysis.

## Rejected For This Phase

- Direct TypeScript port.
- Saved-diff analyzer as the primary V0 workflow.
- Watcher-first design as full session truth.
- Required LLM extraction.
- External service calls.
