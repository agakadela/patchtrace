# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and
  remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as
  separate files.

## Current Phase: Phase 4 - Evidence-Backed Explicit Claim Assessment

Phase 3 is closed. Durable proof for the real
`uv run patchtrace run -- codex` walking skeleton lives in
`docs/VERIFY_LOG.md`. Phase 4 makes that existing primary workflow produce a
readable, deterministic claim-vs-evidence assessment for a bounded set of
explicit final agent claims.

Product scope and acceptance criteria are canonical in `docs/SPEC.md`.
Architecture and module ownership are canonical in `docs/ARCHITECTURE.md`.

### Goal

After a wrapped Codex session, the reviewer can understand the recommended
next action within seconds and inspect each extracted claim with its category,
local evidence references, conservative relationship, evidence gap, and
concrete follow-up.

### Product And Architecture Boundary

- Analyze only explicit final claims about changed files, completed changes,
  tests, and verification commands.
- Stay local, deterministic, rules-first, and useful without an LLM.
- Normalize transcript noise before extracting claims.
- Produce one validated `AnalysisResult`; all reports render from that shared
  result instead of independently interpreting raw artifacts.
- Preserve the existing capability-package convention under
  `src/patchtrace/`.
- Do not implement `patchtrace analyze`, `patchtrace watch`, broad semantic
  interpretation, expanded adapters/risk classification, public JSON output,
  or external calls in this phase.

### Dependency Graph

```text
clean claim-bearing transcript
  -> first shared AnalysisResult and file/change claim detail
  -> test and verification-command assessments
  -> quick decision in SUMMARY.md
  -> aligned AGENT_FEEDBACK.md and VERIFICATION_BRIEF.md
  -> fixture matrix and real Codex dogfood close
```

The tasks are intentionally sequential because they evolve the same analysis
interface and report contract. Parallel implementation is N/A for this phase.

Suggested implementation branch: `agent/phase-4-claim-evidence`

Branch/PR rule: create the suggested branch after this plan is approved, commit
each verified task as a save point, push the branch, and keep one draft PR open
for the phase. Mark it ready only after the full Phase 4 checks, runtime dogfood,
review, simplification pass, and documentation close.

## Active Tasks

### Task 1: Clean Claim-Bearing Transcript

**Visible result:** Existing reports show clean command/test signals, while
ANSI sequences, terminal control noise, and unrelated environment warnings no
longer masquerade as agent evidence. Analysis receives a bounded final-response
region when one can be identified.

**Acceptance criteria:**

- Synthetic Codex-style fixtures normalize ANSI/control noise without
  committing a private real transcript.
- Final claim-bearing output and command/test signals are identified
  conservatively; ambiguous or missing final output remains explicit.
- Current fake-command and interactive-session behavior does not regress.

**Verification:**

- `uv run pytest tests/unit/test_transcript_normalization.py`
- `uv run pytest tests/integration/test_interactive_session_capture.py tests/integration/test_run_fake_command.py`
- `uv run mypy src tests`
- Manual fixture check: rendered command/test signals contain no synthetic ANSI
  or unrelated warning noise.

**Dependencies:** None.

**Files likely touched:**

- `src/patchtrace/session/transcript.py`
- `src/patchtrace/analysis/test_evidence.py`
- `tests/fixtures/`
- `tests/unit/test_transcript_normalization.py`
- `tests/integration/test_interactive_session_capture.py`

**Do not touch:** CLI command surfaces, `analyze`, `watch`, report layout beyond
cleaned signals, or any private `.patchtrace/runs/` material.

**Estimated scope:** Medium, about 4-5 files.

### Task 2: Show The First File/Change Claim Assessment

**Visible result:** `VERIFICATION_BRIEF.md` shows explicit file-change and
completed-change claims with their first evidence relationships, source
locators, gaps, and next actions.

**Acceptance criteria:**

- One `analyze_run(...) -> AnalysisResult` interface returns validated claim
  assessments without external calls.
- Only explicit final file/change claims are extracted; generic `done`,
  `fixed`, or `everything works` statements remain unassessed without specific
  evidence.
- The verification brief distinguishes supporting evidence, missing evidence,
  conflicting evidence, and cannot-assess outcomes in plain language.

**Verification:**

- `uv run pytest tests/unit/test_verification_brief_report.py`
- `uv run pytest tests/unit/test_claim_analysis.py`
- `uv run mypy src tests`
- Manual fixture check: one supported file claim and one ambiguous completion
  claim render with different, appropriate next actions.

**Dependencies:** Task 1.

**Files likely touched:**

- `src/patchtrace/models/report.py`
- `src/patchtrace/analysis/analyzer.py`
- `src/patchtrace/cli/app.py`
- `src/patchtrace/reports/verification_brief.py`
- `tests/unit/test_claim_analysis.py`

**Do not touch:** summary/feedback redesign, risk expansion, persistence of
analysis JSON, or non-Codex adapters.

**Estimated scope:** Medium, about 5 files.

### Checkpoint A: Transcript And First Claim Slice

- Targeted tests and `uv run mypy src tests` pass.
- A fake run still writes every required artifact.
- The verification brief displays at least one evidence-referenced claim while
  preserving cannot-assess behavior for ambiguous language.
- Review the `AnalysisResult` interface before adding more claim categories.

### Task 3: Assess Test And Verification-Command Claims

**Visible result:** The verification brief distinguishes an agent mentioning a
test command from evidence that the command passed, failed, or had no captured
result.

**Acceptance criteria:**

- Explicit test and verification-command claims retain command and output
  evidence locators when available.
- Passing, failing, missing, and contradictory evidence map conservatively to
  the agreed internal support taxonomy and plain-language labels.
- A passing unrelated command never proves a claimed behavior change.

**Verification:**

- `uv run pytest tests/unit/test_claim_analysis.py tests/unit/test_verification_brief_report.py`
- `uv run pytest tests/integration/test_run_fake_command.py`
- `uv run mypy src tests`
- Manual fixture check: claimed-pass, captured-failure, and command-only cases
  produce distinct assessments and next actions.

**Dependencies:** Task 2 and Checkpoint A approval.

**Files likely touched:**

- `src/patchtrace/analysis/analyzer.py`
- `src/patchtrace/analysis/test_evidence.py`
- `src/patchtrace/models/report.py`
- `src/patchtrace/reports/verification_brief.py`
- `tests/unit/test_claim_analysis.py`

**Do not touch:** generic test-coverage scoring, execution of new commands on
the user's behalf, or claims about code correctness.

**Estimated scope:** Medium, about 5 files.

### Task 4: Put The Quick Decision In The Summary

**Visible result:** `SUMMARY.md` leads with one conservative verdict, the most
important evidence gap, and one recommended next action before metadata and
detail.

**Acceptance criteria:**

- The summary consumes the shared `AnalysisResult`; it does not parse raw run
  artifacts or independently calculate claim support.
- Verdict and next-action wording remain useful for no-change, missing-
  transcript, failed-command, and mixed-claim runs.
- User-facing copy never equates evidence support with correctness, safety, or
  acceptance.

**Verification:**

- `uv run pytest tests/unit/test_summary_report.py`
- `uv run pytest tests/integration/test_run_fake_command.py`
- `uv run mypy src tests`
- Manual Markdown check: the first screenful answers `what happened?`, `what is
  uncertain?`, and `what should I do next?`.

**Dependencies:** Task 3.

**Files likely touched:**

- `src/patchtrace/cli/app.py`
- `src/patchtrace/analysis/analyzer.py`
- `src/patchtrace/models/report.py`
- `src/patchtrace/reports/summary.py`
- `tests/unit/test_summary_report.py`

**Do not touch:** new output formats, interactive prompts, automatic acceptance,
or report styling unrelated to decision clarity.

**Estimated scope:** Medium, about 5 files.

### Task 5: Align Agent Feedback And Verification Detail

**Visible result:** `AGENT_FEEDBACK.md` gives the agent precise evidence gaps to
close, while `VERIFICATION_BRIEF.md` gives the human the matching detailed
claim/evidence record. Both agree with `SUMMARY.md` because they consume the
same analysis result.

**Acceptance criteria:**

- All three reports render from the same `AnalysisResult` produced once per
  run.
- Agent feedback requests only concrete missing work or evidence and cites the
  relevant claim.
- Verification detail preserves claim category, relationship, locator, gap,
  and next action without duplicating the quick summary.

**Verification:**

- `uv run pytest tests/unit/test_agent_feedback_report.py tests/unit/test_verification_brief_report.py`
- `uv run pytest tests/integration/test_run_fake_command.py`
- `uv run mypy src tests`
- Manual cross-report check: verdict, highest-priority gap, and requested action
  do not conflict across the three Markdown artifacts.

**Dependencies:** Task 4.

**Files likely touched:**

- `src/patchtrace/reports/feedback.py`
- `src/patchtrace/reports/verification_brief.py`
- `tests/unit/test_agent_feedback_report.py`
- `tests/unit/test_verification_brief_report.py`
- `tests/integration/test_run_fake_command.py`

**Do not touch:** report filenames, external messaging, GitHub integration, or
additional agent adapters.

**Estimated scope:** Medium, about 5 files.

### Checkpoint B: Shared Analysis And Layered Report UX

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `uv run pytest`
- `uv build`
- Fake zero-exit and non-zero-exit runs produce internally consistent reports.
- Product-architecture review confirms report renderers remain shallow and the
  analysis module owns interpretation.

### Task 6: Prove The Phase 4 Fixture Matrix And Real Codex Flow

**Visible result:** A real `uv run patchtrace run -- codex` session produces a
readable quick decision plus evidence-referenced claim detail, and the phase has
durable verification evidence.

**Acceptance criteria:**

- Sanitized fixtures cover supported, partially supported, unsupported,
  contradicted, cannot-assess, missing-material, and non-zero-exit scenarios.
- Real Codex dogfood confirms the report is understandable within seconds and
  retains actionable claim detail without exposing private transcript content
  in tracked files.
- Phase close updates current project truth and explicitly names anything that
  still cannot be verified.

**Verification:**

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `uv run pytest`
- `uv build`
- Runtime dogfood: `uv run patchtrace run -- codex`
- Inspect `SUMMARY.md`, `AGENT_FEEDBACK.md`, `VERIFICATION_BRIEF.md`, and
  `run.json` in the untracked local run folder.
- Run `$aga-simplify`, `$aga-review`, and `$aga-test` before marking the draft
  PR ready.

**Dependencies:** Task 5 and Checkpoint B.

**Files likely touched:**

- `tests/fixtures/`
- `tests/integration/test_run_fake_command.py`
- `README.md`
- `docs/VERIFY_LOG.md`
- `docs/PLAN.md`

**Do not touch:** private run artifacts, package publishing, hosted services,
`analyze`, or `watch`.

**Estimated scope:** Medium, about 5 tracked areas/files.

### Phase 4 Completion Checkpoint

- Every acceptance criterion in the Phase 4 slice of `docs/SPEC.md` is mapped
  to passing automated or runtime evidence.
- Full lint, format, typecheck, test, and build checks pass.
- Real Codex dogfood proves the primary flow and report readability.
- No required LLM, external call, new dependency, or private tracked transcript
  was introduced.
- `$aga-simplify`, `$aga-review`, and `$aga-test` are complete.
- `docs/VERIFY_LOG.md` contains the compact Phase 4 close entry.
- The draft PR accurately lists scope, checks, runtime proof, docs, and
  cannot-verify items and is ready for Aga's merge decision.

## Deferred From Phase 3

- Full `patchtrace analyze` behavior.
- Expanded risk classification beyond simple local evidence signals.
- `patchtrace watch` idle detection and deduplication.
- Optional JSON report output beyond internal run metadata.
- Non-Codex adapters.
- Package publishing, GitHub integration, HTML report, SaaS, auth, database,
  and required LLM analysis.
- Transcript sanitization / command-test signal cleanup for interactive Codex
  ANSI/control noise beyond the bounded Phase 4 normalization rules.

## Deferred From Phase 4

- Broad semantic extraction of arbitrary or implied agent claims.
- Persisted/public `AnalysisResult` JSON.
- Dedicated parsers for additional agent transcript formats.
- Automatic execution of missing verification commands.
- General correctness, safety, or production-readiness judgments.

## Rejected For Phase 4

- Placeholder-only reports that ignore available local evidence.
- LLM-based extraction or summarization.
- External service calls.
- Watcher-first design.
- Treating agent summaries as proof.
- Independent analysis logic inside each report renderer.
- Treating missing evidence as evidence that a claim is false.
