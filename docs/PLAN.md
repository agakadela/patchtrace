# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rules:

- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- Move a closed phase summary to `docs/VERIFY_LOG.md`; completed task detail
  belongs in git and PR history.
- Keep the complete capability roadmap in `docs/SPEC.md`.
- Work on one task at a time.

## Branch And Baseline

This plan is based on commit `d8c98c4`, the head of open PR #19, which contains
the completed Phase 4 implementation and closeout.

The product/architecture re-baseline is stacked on PR #19. Its PR should target
`agent/phase-4-task-6-dogfood` until PR #19 merges, then be retargeted to
`main` only after confirming that `main` contains `d8c98c4` and the retargeted
diff contains only this re-baseline.

## Current Phase: Phase 5 — Trusted Run Evidence And Provenance

### Phase Goal

Make one PatchTrace run trustworthy enough to answer which task material, final
output, Git changes, and command results belong to the captured session before
adding broader analysis.

### User-Visible Result

A user can run PatchTrace with an explicit task file and target repository, then
receive a verification package that:

- binds the copied task material to the run;
- distinguishes `session-attributed`, `pre-existing`, and `unattributable` Git
  changes;
- states how final-message and command evidence were captured;
- separates wrapped-command outcome from analysis outcome;
- exposes integrity/version metadata;
- gives a decisive verification verdict and recommended action without claiming
  autonomous acceptance or correctness proof.

Target command shape:

```bash
patchtrace run --task-file ./TASK.md --repo . -- codex
```

For an explicitly non-interactive Codex invocation, the concrete Codex adapter
may use documented JSONL and final-message capture:

```bash
patchtrace run --task-file ./TASK.md --repo . -- codex exec "<prompt>"
```

PatchTrace must not silently convert interactive `codex` into `codex exec`.

### Phase Dependencies

- Phase 4 head `d8c98c4` and its fixture matrix.
- Existing PTY capture, local run storage, Git evidence, shared
  `AnalysisResult`, and three report renderers.
- Official Codex CLI 0.144.1 structured `exec` behavior documented in
  `docs/ARCHITECTURE.md` and ADR-0003.

### Phase Exit Criteria

- A raw task contract is explicitly supplied, copied into the run folder, and
  bound by digest; absence is represented as a named analysis limitation.
- The target repository identity and effective working directory are recorded.
  Codex `-C` mismatches and `--add-dir` multi-workspace scope cannot silently
  receive complete Git attribution.
- Clean, dirty, staged, unstaged, new-untracked, pre-existing-untracked,
  descendant-commit, and non-descendant-HEAD fixtures produce the documented
  attribution labels and limitations.
- The concrete Codex boundary owns Codex-specific TUI normalization and
  structured-event parsing; generic capture contains no Codex markers.
- Structured `codex exec` capture preserves JSONL event boundaries and
  stdout/stderr separation. Its integrity is explicitly `complete`,
  `incomplete`, `malformed`, or `mismatched`; failed structured capture cannot
  silently fall back to transcript inference.
- Evidence records separate kind, capture method, directness, attribution, and
  integrity metadata through closed enums and cross-field validation.
- Wrapped-command and analysis outcomes have tested operational semantics,
  including spawn failure, non-zero exit, signal/interruption, missing final
  output, Git collection failure, parser failure, and report-write failure.
- The run manifest has a schema version, PatchTrace producer version, adapter
  and parser versions where applicable, and SHA-256 digests for bound artifacts.
- Run folders and newly written sensitive artifacts use private local
  permissions where the platform supports them.
- Reports safely escape displayed material and minimize copied task, prompt,
  command-output, and final-message content.
- All reports consume one `AnalysisResult`, show a provenance-aware verification
  verdict chosen by one tested precedence rule, show one recommended action, and
  keep human authority explicit.
- Sanitized fixtures and at least one real interactive Codex dogfood run prove
  the fallback path; a structured `codex exec` dogfood run proves the JSONL
  path.
- `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src tests`, `uv run pytest`, and `uv build` pass.
- Human review confirms the attribution labels and report usefulness before
  Phase 5 closes.

### Out Of Scope

- Parsed requirement coverage and semantic completeness analysis;
- generic adapter/plugin architecture or non-Codex adapters;
- worktree virtualization or proof of causal agent authorship;
- exhaustive recovery of transient changes committed and later reset;
- attribution across multiple repositories, submodule contents, or ignored
  files;
- `patchtrace analyze` and `patchtrace watch`;
- review-priority scoring beyond making provenance gaps visible;
- public JSON API, package publishing, external services, or LLM use.

### Plan-Change Triggers

- If explicit task-file authoring is too disruptive in real dogfooding, pause
  before adding inference and test a simpler explicit input mechanism.
- If Codex JSONL does not preserve the events needed for final/command evidence,
  keep structured mode degraded and revise ADR-0003; do not parse more TUI text
  by default.
- If path-level dirty-repo attribution produces misleading results, require a
  clean baseline for complete analysis and keep dirty runs explicitly limited.
- If supporting structured and PTY transports forces broad framework
  abstraction, keep two concrete capture paths until a second real adapter
  proves a shared protocol.

## Active Tasks

### Task 1: Bind The Raw Task And Target Repository To The Run

**Description:** Add explicit `--task-file` and `--repo` inputs, safely copy the
task material into the private run folder, record the resolved repository
identity, and bind the task artifact with a digest. The task is the evaluation
contract; do not claim that the same bytes reached the agent without separate
delivery evidence, and do not parse requirements yet.

**Acceptance criteria:**

- [ ] A run manifest records the requested and resolved repository plus the
      copied `task.md` artifact and SHA-256 digest.
- [ ] Task input is a bounded regular non-symlink file with supported encoding;
      unstable bytes during copy, oversize input, and symlink input fail before
      child launch.
- [ ] Missing/unreadable task input and non-Git target paths fail or degrade
      according to documented reason codes without launching the wrapped command
      under a false complete state.
- [ ] Codex `-C` mismatch or `--add-dir` is detected by the Codex boundary and
      reported as incomplete repository scope.
- [ ] Relative paths, symlinked repository paths, nested repositories, and
      multiple workspace declarations resolve under one explicit, tested scope
      rule.

**Verification:**

- [ ] Focused CLI/model/storage tests pass.
- [ ] A fake run proves the copied task and repository binding in `run.json`.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** None.

**Likely files:** `src/patchtrace/cli/app.py`,
`src/patchtrace/models/run.py`, `src/patchtrace/storage/runs.py`,
`tests/integration/test_run_fake_command.py`.

**Suggested branch:** `agent/phase-5-task-1-run-binding`

### Task 2: Separate Wrapped-Command And Analysis Outcomes

**Description:** Replace the current single `outcome` field with explicit
wrapped-command and analysis outcomes, reason codes, and early manifest writes
that survive partial failure.

**Acceptance criteria:**

- [ ] Wrapped process states distinguish not started, spawn failure, exited,
      signaled, interrupted, and unknown without converting every signal into an
      ordinary exit.
- [ ] Analysis is `completed`, `degraded`, or `blocked` under explicit tested
      invariants and reason codes.
- [ ] The manifest exists before the child starts and is updated after capture,
      analysis, and report boundaries so failures leave a diagnosable record.

**Verification:**

- [ ] Fake-command tests cover zero/non-zero exit, spawn failure, signal, and
      interrupted/unknown behavior.
- [ ] Unit tests cover analysis outcome invariants.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Task 1.

**Likely files:** `src/patchtrace/models/run.py`,
`src/patchtrace/session/recorder.py`, `src/patchtrace/cli/app.py`,
`tests/integration/test_run_fake_command.py`.

**Suggested branch:** `agent/phase-5-task-2-outcomes`

### Task 3: Create Versioned Evidence And Integrity Models

**Description:** Introduce the smallest validated evidence envelope needed by
the trust chain. Keep evidence kind, capture method, directness, attribution,
locator, and integrity as separate fields.

**Acceptance criteria:**

- [ ] Manifest/evidence schemas include schema, producer, adapter, and parser
      versions where applicable.
- [ ] Bound artifacts carry path, SHA-256 digest, size, capture method, and
      directness without treating those fields as correctness scores.
- [ ] Evidence taxonomies are closed enums with cross-field validators, and
      structured evidence records `complete`, `incomplete`, `malformed`,
      `mismatched`, or `N/A` integrity.
- [ ] Mutated or missing artifacts are detected before post-capture analysis and
      produce named analysis limitations.

**Verification:**

- [ ] Pydantic validation and mutation-detection tests pass.
- [ ] A saved-run fixture proves stable serialization.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Tasks 1–2.

**Likely files:** `src/patchtrace/models/run.py`,
`src/patchtrace/models/evidence.py`, `src/patchtrace/storage/runs.py`,
`tests/unit/test_evidence_models.py`.

**Suggested branch:** `agent/phase-5-task-3-evidence-envelope`

### Task 4: Attribute Clean-Baseline And Committed Git Changes

**Description:** Capture HEAD/repository identity plus before/after path state
and content fingerprints. Classify clean-baseline worktree changes, new
untracked files, and descendant commits as session-attributed.

**Acceptance criteria:**

- [ ] Clean tracked modifications, additions, deletions, renames, binary-path
      changes, and new untracked files receive tested session attribution.
- [ ] A descendant `HEAD` change captures committed changes even when the final
      worktree is clean.
- [ ] Non-descendant/unborn HEAD, submodules, ignored files, and multi-repo scope
      produce explicit bounded behavior instead of guessed attribution.

**Verification:**

- [ ] Git integration fixtures cover the supported clean-baseline matrix.
- [ ] Report input includes attribution basis and evidence locators.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Task 3.

**Likely files:** `src/patchtrace/vcs/snapshot.py`,
`src/patchtrace/models/evidence.py`, `src/patchtrace/cli/app.py`,
`tests/integration/test_git_evidence.py`.

**Suggested branch:** `agent/phase-5-task-4-clean-git-attribution`

### Task 5: Add Dirty-Repository Limited Attribution

**Description:** Preserve the pre-run dirty baseline and distinguish unchanged
pre-existing paths from new session-attributed paths and overlapping
unattributable paths.

**Acceptance criteria:**

- [ ] Unchanged baseline dirt is labeled pre-existing.
- [ ] A path clean at start and changed at end is session-attributed even when
      other paths were already dirty.
- [ ] A pre-existing tracked or untracked path that also changes during the
      session is labeled unattributable at the inseparable scope, with the
      baseline and final fingerprints retained.

**Verification:**

- [ ] Dirty/staged/unstaged/untracked overlap fixtures pass.
- [ ] Reports do not present whole-worktree material as session-attributed.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Task 4.

**Likely files:** `src/patchtrace/vcs/snapshot.py`,
`src/patchtrace/models/evidence.py`,
`src/patchtrace/analysis/analyzer.py`,
`tests/integration/test_git_evidence.py`.

**Suggested branch:** `agent/phase-5-task-5-dirty-git-attribution`

### Task 6: Establish The Concrete Codex Adapter Boundary

**Description:** Move Codex-specific TUI marker/noise behavior out of generic
session/analysis modules into one concrete adapter. Preserve the verified Phase
4 fallback behavior and sanitized transcript corpus.

**Acceptance criteria:**

- [ ] Generic PTY recording contains no Codex-specific marker or shutdown rules.
- [ ] `adapters/codex.py` owns current final-region normalization and returns
      typed final-message evidence or an explicit missing/ambiguous result.
- [ ] No generic plugin registry, discovery mechanism, or hypothetical adapter
      interface is introduced.

**Verification:**

- [ ] Existing Codex transcript fixtures pass through the new boundary.
- [ ] Markerless and multi-marker transcripts remain unassessed.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Task 3.

**Likely files:** `src/patchtrace/adapters/codex.py`,
`src/patchtrace/session/transcript.py`,
`src/patchtrace/analysis/analyzer.py`,
`tests/unit/test_transcript_normalization.py`,
`tests/fixtures/codex_transcript_noise.json`.

**Suggested branch:** `agent/phase-5-task-6-codex-boundary`

### Task 7: Capture Structured Codex Exec Evidence

**Description:** Add a concrete piped transport for explicitly requested
`codex exec`, preserve stdout JSONL and stderr separately, and let the Codex
adapter own PatchTrace-controlled JSONL/final-message capture.

**Acceptance criteria:**

- [ ] Interactive `codex` continues to use PTY capture; PatchTrace never silently
      converts it to `codex exec`.
- [ ] `codex exec` structured mode stores JSONL events and a fresh final message
      inside the current run folder, records requested/effective commands, and
      rejects conflicting user-owned output flags.
- [ ] Final-message selection, unknown events, malformed/truncated JSONL,
      missing output files, and event/file disagreement have explicit behavior;
      failed structured parsing never silently becomes text inference.
- [ ] Structured integrity is `complete`, `incomplete`, `malformed`, or
      `mismatched` under fixture-proven rules; raw JSONL remains authoritative
      evidence even when derived selection fails.
- [ ] Command events preserve invocation, lifecycle, exit/status information,
      and source locators when Codex emits them.

**Verification:**

- [ ] Sanitized JSONL fixtures cover successful, failed, unknown-event,
      truncated, and mismatched-final-message cases.
- [ ] A fake structured subprocess proves stdout/stderr separation.
- [ ] A real local `codex exec` dogfood run proves the documented 0.144.1 path
      without tracking private output.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Tasks 2, 3, and 6.

**Likely files:** `src/patchtrace/adapters/codex.py`,
`src/patchtrace/session/recorder.py`, `src/patchtrace/cli/app.py`,
`tests/integration/test_structured_codex_capture.py`,
`tests/fixtures/codex_exec_events.jsonl`.

**Suggested branch:** `agent/phase-5-task-7-codex-structured-evidence`

### Task 8: Make Analysis And Reports Provenance-Aware

**Description:** Feed the bound task, attributed Git changes, final-message
source, command evidence, and separate outcomes into the existing single
analysis seam. Replace free-form verdict copy with a typed, decisive
verification verdict and recommended action.

**Acceptance criteria:**

- [ ] One `AnalysisResult` exposes analysis outcome/reasons, evidence provenance,
      attribution, gaps, verification verdict, and recommended action to all
      renderers.
- [ ] Reports distinguish direct structured evidence from deterministic text
      inference and identify pre-existing/unattributable Git material.
- [ ] Reports use `ready_for_human_acceptance`, `review_required`, `send_back`,
      `rerun_required`, or `cannot_assess` under tested rules; Phase 5 cannot
      emit `ready_for_human_acceptance` before requirement coverage exists.
- [ ] One analyzer-owned precedence rule selects the verdict; renderers cannot
      promote it, and incompatible, mutated, post-hoc, or renderer-failed runs
      cannot emit `ready_for_human_acceptance`.
- [ ] Reports may strongly recommend the next decision but do not perform
      acceptance or represent the verdict as proof of correctness.
- [ ] Reports safely escape excerpts and minimize sensitive raw task, prompt,
      command-output, and final-message content.

**Verification:**

- [ ] The Phase 4 claim matrix still produces conservative claim relationships.
- [ ] Report tests prove the three renderers agree on outcomes and provenance.
- [ ] `uv run mypy src tests` passes before commit.

**Dependencies:** Tasks 4–7.

**Likely files:** `src/patchtrace/models/report.py`,
`src/patchtrace/analysis/analyzer.py`,
`src/patchtrace/reports/summary.py`,
`src/patchtrace/reports/feedback.py`,
`src/patchtrace/reports/verification_brief.py`.

**Suggested branch:** `agent/phase-5-task-8-provenance-reports`

### Task 9: Prove And Close The Trusted-Run Phase

**Description:** Run the complete supported fixture matrix and real interactive
plus structured Codex dogfood flows, then reconcile documentation with
implemented truth.

**Acceptance criteria:**

- [ ] The Phase 5 exit-criteria matrix is recorded without private transcripts
      or diffs.
- [ ] Full quality gates and package build pass.
- [ ] `README.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `CONTEXT.md`, and ADR
      statuses match implemented and human-accepted truth.
- [ ] `docs/VERIFY_LOG.md` receives one compact Phase 5 close entry only after
      human review.

**Verification:**

- [ ] Full automated gates and runtime artifact checks pass.
- [ ] `$aga-simplify`, `$aga-review`, `$aga-test`, and `$aga-verify-agent` are
      completed or exact cannot-verify items are recorded.
- [ ] Human confirms whether Phase 6 should preserve the planned contract
      authoring format.

**Dependencies:** Tasks 1–8.

**Likely files:** fixture/tests as required, then `README.md`,
`docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/PLAN.md`,
`docs/VERIFY_LOG.md`.

**Suggested branch:** `agent/phase-5-task-9-closeout`

## Phase Checkpoints

### Checkpoint A — After Tasks 1–3

- [ ] Run/task/repository binding is explicit and versioned.
- [ ] Partial failures leave a diagnosable manifest.
- [ ] Human reviews outcome semantics before Git and adapter code depends on
      them.

### Checkpoint B — After Tasks 4–5

- [ ] Attribution matrix is understandable and does not mix pre-existing
      worktree changes into session-attributed evidence.
- [ ] Dirty-repository limitations are acceptable in real dogfooding.

### Checkpoint C — After Tasks 6–7

- [ ] Interactive Codex behavior remains usable.
- [ ] Structured Codex evidence is stronger than the TUI fallback and has no
      silent fallback on parse failure.

### Checkpoint D — After Tasks 8–9

- [ ] Reports remain decisive, with human authority and correctness limits
      stated once rather than repeated as defensive boilerplate.
- [ ] Full phase exit criteria and runtime proof pass.

## Deferred After Phase 5

- Parsed task requirements and requirement coverage (Phase 6).
- Evidence-quality review prioritization (Phase 7).
- Post-hoc `patchtrace analyze` (Phase 8).
- Package publishing and OSS readiness (Phase 9).
- `watch`, non-Codex adapters, public JSON, GitHub integration, optional LLM,
  and hosted surfaces remain trigger-dependent.

## Rejected For Phase 5

- Worktree virtualization or causal `agent-authored` claims.
- Generic plugin/adapter framework.
- Broad natural-language task interpretation.
- LLM parsing of transcript, command output, or task material.
- Review scoring or generic code review.
- Implementing `analyze` or `watch` before the run evidence is trustworthy.
