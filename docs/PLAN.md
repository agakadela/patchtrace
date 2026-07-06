# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and
  remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as
  separate files.

## Current Phase: Phase 3 - Real Codex Dogfood Walking Skeleton

Goal: prove the first real local dogfood path for PatchTrace by wrapping a
real Codex CLI session and producing the first full review-package shape from
strictly bounded local evidence.

Phase 2 is closed. Durable verification evidence lives in `docs/VERIFY_LOG.md`;
completed Phase 2 task detail lives in git history and merged PRs.

Suggested implementation branch: `agent/phase-3-codex-dogfood`.

## 5-Line Phase Spec

**Problem:** Phase 2 can run fake commands and write minimal run material, but
PatchTrace has not yet proved the product-defining Codex dogfood flow.

**User:** Aga, using Codex CLI locally in this repo.

**Flow:** `uv run patchtrace run -- codex` launches a real interactive Codex
session, captures transcript and git evidence, and writes the review package
after Codex exits.

**Visible result:** the run folder contains `run.json`, `agent-session.txt`,
git evidence, `SUMMARY.md`, `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`.

**Out of scope:** full claim-vs-diff matching, semantic patch correctness,
expanded risk taxonomy, LLM calls, external services, GitHub integration, and
`watch` behavior.

## Phase Boundary

Phase 3 is evidence-aware, but intentionally narrow.

Phase 3 reports may use only:
- transcript present or missing;
- wrapped command and exit code;
- changed files;
- diff present, empty, or missing;
- generated artifact paths;
- obvious command/test lines detected in transcript text;
- conservative local evidence gaps.

Phase 3 reports must not:
- claim the patch is correct, safe, guaranteed, or production verified;
- infer unstated agent claims;
- do semantic claim-vs-diff matching;
- use an LLM, network call, telemetry, or external service;
- add GitHub integration, package publishing, or hosted behavior;
- implement `patchtrace watch`.

## Done Means

- `uv run patchtrace run -- codex` can be used in a real local dogfood session.
- The run folder contains the required raw artifacts and Markdown reports.
- `SUMMARY.md` gives a conservative next-action summary.
- `AGENT_FEEDBACK.md` is ready to paste back to an agent when evidence is
  missing, weak, or contradictory.
- `VERIFICATION_BRIEF.md` names the local evidence, command/test signals,
  changed files, and explicit gaps without overstating confidence.
- Fake-command integration tests still pass.
- New fixture/unit tests prove the bounded evidence-aware report behavior.
- Local checks pass: `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src tests`, `uv run pytest`, and `uv build`.
- Runtime proof records a real Codex dogfood run, or names exactly why it could
  not be completed locally.

## Open Questions

### Blocking

- N/A. The Phase 3 product boundary is accepted.

### Non-Blocking

- The exact real Codex dogfood prompt/task should be chosen during Phase 3
  planning so it is small, reversible, and safe for this repo.
- The exact obvious command/test-line detection rules can be refined from
  fixtures before implementation.
- Whether report rendering should introduce new Pydantic report models in
  Phase 3 or keep using existing run/report structures until the analyzer
  deepens.

## ADR Candidates

- N/A for Phase 3 foundation. Existing ADRs already cover the CLI, local-first
  boundary, package convention, run folder format, and report package shape.
- Future ADR candidate if changed later: public report/verdict taxonomy beyond
  the bounded Phase 3 evidence-aware skeleton.

## Active Tasks

No active implementation tasks yet. Next step: use `$aga-plan` to break this
phase into ordered vertical slices with acceptance criteria, verification
methods, likely touched files, and do-not-touch lists.

## Deferred

- Full `patchtrace analyze` behavior.
- Full claim extraction from real Codex transcript formats.
- Full claim-vs-evidence matching.
- Expanded risk classification beyond simple local evidence signals.
- `patchtrace watch` idle detection and deduplication.
- Optional JSON report output beyond internal run metadata.
- Non-Codex adapters.
- Package publishing, GitHub integration, HTML report, SaaS, auth, database,
  and required LLM analysis.

## Rejected For This Phase

- Placeholder-only reports that ignore available local evidence.
- LLM-based extraction or summarization.
- External service calls.
- Watcher-first design.
- Treating agent summaries as proof.
