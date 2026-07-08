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

Branch/PR rule: implement Phase 3 on `agent/phase-3-codex-dogfood`. Because
this phase has a suggested branch, implementation is not done until the branch
is pushed and a draft PR with a `[agent]` title exists, unless Aga explicitly
asks not to open one.

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

## Dependency Graph

```text
interactive PTY passthrough with a fake interactive command
  -> bounded evidence-aware SUMMARY.md from local run material
    -> AGENT_FEEDBACK.md generated from the same bounded evidence
      -> VERIFICATION_BRIEF.md generated from the same bounded evidence
        -> full fake-command review package checkpoint
          -> real `patchtrace run -- codex` dogfood proof and phase close
```

Notes:
- Tasks are intentionally ordered by dependency, not by report importance.
- `AGENT_FEEDBACK.md` and `VERIFICATION_BRIEF.md` both depend on the bounded
  evidence summary rules. They can be reviewed independently after Task 2, but
  should be implemented sequentially in one branch because both update the run
  artifact manifest.

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

- Aga may override the default real Codex dogfood prompt before Task 6 if a
  safer tiny docs-only task appears.
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

### Task 1: Real Interactive PTY Passthrough With Fake Fixture

**Status:** Complete.

**Description:** Upgrade the existing run recorder from fake non-interactive
command capture to a narrow interactive PTY path that can preserve a user's
terminal interaction while still saving the transcript, exit status, and git
evidence. Prove it with a local fake interactive command before using real
Codex.

**Acceptance criteria:**
- [x] `uv run patchtrace run -- python tests/fixtures/fake_interactive_agent.py`
      can complete a one-prompt interactive exchange in local runtime.
- [x] `agent-session.txt` captures the fake prompt, supplied response, command
      output, and exit status evidence without dropping the transcript.
- [x] Existing fake non-interactive runs still create the Phase 2 artifacts.
- [x] Non-zero wrapped command exits still record run material without claiming
      success.

**Verification method:**
- [x] `uv run pytest tests/integration/test_interactive_session_capture.py`
- [x] `uv run pytest tests/integration/test_run_fake_command.py`
- [x] Manual smoke:
      `uv run patchtrace run -- python tests/fixtures/fake_interactive_agent.py`

**Dependencies:** None.

**Likely touched files:**
- `src/patchtrace/session/recorder.py`
- `tests/fixtures/fake_interactive_agent.py`
- `tests/integration/test_interactive_session_capture.py`
- `tests/integration/test_run_fake_command.py`

**Do-not-touch list:**
- No real Codex invocation yet.
- No report package expansion beyond preserving existing `SUMMARY.md`.
- No claim extraction, LLM calls, external services, telemetry, `analyze`, or
  `watch`.

### Task 2: Bounded Evidence-Aware Summary

**Status:** Complete.

**Description:** Make `SUMMARY.md` use the exact Phase 3 evidence boundary:
transcript presence, wrapped command exit status, changed files, diff
presence, generated artifacts, obvious command/test lines, and conservative
gaps. This keeps the quick summary useful before deeper claim analysis exists.

**Acceptance criteria:**
- [x] A fake run with a changed tracked file lists changed files and whether
      diff material is present.
- [x] A transcript containing obvious command/test lines surfaces those lines
      as command/test signals.
- [x] Missing test signals, empty diffs, missing git evidence, and non-zero
      exits are named as evidence gaps.
- [x] The summary still avoids correctness, safety, guarantee, or production
      verification claims.

**Verification method:**
- [x] `uv run pytest tests/unit/test_summary_report.py`
- [x] `uv run pytest tests/integration/test_git_evidence.py`
- [x] `uv run pytest tests/integration/test_run_fake_command.py`

**Dependencies:** Task 1.

**Likely touched files:**
- `src/patchtrace/reports/summary.py`
- `src/patchtrace/models/report.py`
- `src/patchtrace/analysis/test_evidence.py`
- `tests/unit/test_summary_report.py`
- `tests/integration/test_git_evidence.py`

**Do-not-touch list:**
- No `AGENT_FEEDBACK.md` or `VERIFICATION_BRIEF.md` yet.
- No semantic claim-vs-diff matching.
- No verdict or claim-support taxonomy changes.
- No LLM calls, external services, GitHub integration, `analyze`, or `watch`.

### Task 3: Agent Feedback Artifact

**Status:** Complete.

**Description:** Generate `AGENT_FEEDBACK.md` from the bounded evidence so a
human can paste concrete next steps back to the agent when evidence is missing,
weak, contradictory, or the wrapped command failed.

**Acceptance criteria:**
- [x] Every `patchtrace run -- <command>` that reaches report generation writes
      `AGENT_FEEDBACK.md` and lists it in `run.json`.
- [x] Feedback references concrete local evidence: exit status, changed files,
      diff presence, command/test signals, and evidence gaps.
- [x] Feedback is ready to paste to an agent and asks for specific missing
      evidence or follow-up work when needed.
- [x] Feedback does not say the patch succeeded, is correct, is safe, or is
      production verified.

**Verification method:**
- [x] `uv run pytest tests/unit/test_agent_feedback_report.py`
- [x] `uv run pytest tests/integration/test_run_fake_command.py`
- [x] Manual smoke:
      `uv run patchtrace run -- python tests/fixtures/fake_agent.py`
      then inspect `.patchtrace/runs/<run-id>/AGENT_FEEDBACK.md`.

**Dependencies:** Task 2.

**Likely touched files:**
- `src/patchtrace/storage/runs.py`
- `src/patchtrace/reports/feedback.py`
- `src/patchtrace/cli/app.py`
- `tests/unit/test_agent_feedback_report.py`
- `tests/integration/test_run_fake_command.py`

**Do-not-touch list:**
- No `VERIFICATION_BRIEF.md` yet.
- No broad analyzer, claim extraction, or semantic diff reasoning.
- No LLM calls, external services, GitHub integration, `analyze`, or `watch`.

### Task 4: Verification Brief Artifact

**Status:** Complete.

**Description:** Generate `VERIFICATION_BRIEF.md` as the detailed human-facing
artifact for the same bounded evidence. It should explain what PatchTrace saw,
what it did not see, and where the human should review first, without claiming
semantic correctness.

**Acceptance criteria:**
- [x] Every `patchtrace run -- <command>` that reaches report generation writes
      `VERIFICATION_BRIEF.md` and lists it in `run.json`.
- [x] The brief includes run metadata, artifact paths, changed files, diff
      status, command/test signals, evidence gaps, and a simple review-first
      list based on changed files.
- [x] Missing transcript, missing tests, empty diff, and non-zero exit states
      are labeled conservatively.
- [x] The brief explicitly states that Phase 3 does not perform full
      claim-vs-diff matching or prove correctness.

**Verification method:**
- [x] `uv run pytest tests/unit/test_verification_brief_report.py`
- [x] `uv run pytest tests/integration/test_run_fake_command.py`
- [x] Manual smoke:
      `uv run patchtrace run -- python tests/fixtures/fake_agent.py`
      then inspect `.patchtrace/runs/<run-id>/VERIFICATION_BRIEF.md`.

**Dependencies:** Task 3.

**Likely touched files:**
- `src/patchtrace/storage/runs.py`
- `src/patchtrace/reports/verification_brief.py`
- `src/patchtrace/cli/app.py`
- `tests/unit/test_verification_brief_report.py`
- `tests/integration/test_run_fake_command.py`

**Do-not-touch list:**
- No expanded risk taxonomy beyond simple changed-file review ordering.
- No semantic claim-vs-diff matching.
- No verdict or claim-support taxonomy changes.
- No LLM calls, external services, GitHub integration, `analyze`, or `watch`.

### Task 5: Full Fake-Command Review Package Checkpoint

**Status:** Pending.

**Description:** Prove the complete Phase 3 review package shape on local fake
commands before the real Codex dogfood run. This is the last fake-command gate:
the run folder, manifest, CLI output, and reports should all match the target
artifact contract.

**Acceptance criteria:**
- [ ] `uv run patchtrace run -- python tests/fixtures/fake_agent.py` writes
      `run.json`, `agent-session.txt`, git artifacts, `SUMMARY.md`,
      `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`.
- [ ] `run.json` lists all required artifact paths in the run folder.
- [ ] The CLI points the user to the run folder and does not imply the patch is
      accepted, correct, safe, or production verified.
- [ ] Non-zero wrapped-command exits still write the full review package before
      exiting with the wrapped command status.
- [ ] README status reflects the Phase 3 fake-command review-package checkpoint
      only if the behavior is implemented.

**Verification method:**
- [ ] `uv run pytest tests/integration/test_run_fake_command.py`
- [ ] `uv run pytest tests/integration/test_git_evidence.py`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy src tests`
- [ ] `uv run pytest`
- [ ] `uv build`

**Dependencies:** Task 4.

**Likely touched files:**
- `src/patchtrace/cli/app.py`
- `src/patchtrace/storage/runs.py`
- `tests/integration/test_run_fake_command.py`
- `README.md`
- `docs/VERIFY_LOG.md`

**Do-not-touch list:**
- No real Codex dogfood run yet.
- No `patchtrace analyze` or `patchtrace watch` behavior.
- No package publishing, GitHub integration, external services, or LLM calls.

### Task 6: Real Codex Dogfood Proof And Phase Close

**Status:** Pending.

**Description:** Run the first real dogfood session:
`uv run patchtrace run -- codex`. Use a tiny docs-only prompt so the session is
safe and reversible, then record the generated PatchTrace run folder as Phase 3
runtime proof.

**Default dogfood prompt:** Ask Codex to make one small docs-only README status
update reflecting that Phase 3 real Codex dogfood is being verified. Tell Codex
not to touch application code, secrets, external services, publishing, GitHub
integration, `analyze`, or `watch`.

**Acceptance criteria:**
- [ ] `uv run patchtrace run -- codex` launches a usable real Codex CLI session
      through PatchTrace.
- [ ] The resulting run folder contains the full required review package:
      `run.json`, `agent-session.txt`, git artifacts, `SUMMARY.md`,
      `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`.
- [ ] The transcript captures the Codex session locally, and reports reflect
      the actual changed files, diff presence, command/test signals, and gaps.
- [ ] If Codex CLI cannot be run locally, the cannot-verify reason is explicit
      and no report claims real dogfood success.
- [ ] `docs/VERIFY_LOG.md` records the real dogfood proof or the exact
      cannot-verify reason.
- [ ] The implementation branch is pushed and a draft PR with a `[agent]` title
      exists, unless Aga explicitly asks not to open one.

**Verification method:**
- [ ] `uv run patchtrace run -- codex`
- [ ] Inspect the latest `.patchtrace/runs/<run-id>/run.json`,
      `agent-session.txt`, `SUMMARY.md`, `AGENT_FEEDBACK.md`, and
      `VERIFICATION_BRIEF.md`.
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy src tests`
- [ ] `uv run pytest`
- [ ] `uv build`

**Dependencies:** Task 5.

**Likely touched files:**
- `README.md`
- `docs/VERIFY_LOG.md`
- `docs/PLAN.md`

**Do-not-touch list:**
- No application-code dogfood prompt unless Aga approves it.
- No secrets, customer data, private dashboard output, or provider tokens in
  transcript excerpts, docs, commits, screenshots, or chat.
- No LLM integration inside PatchTrace; Codex CLI is only the wrapped user
  command.
- No package publishing, GitHub integration, external services, `analyze`, or
  `watch`.

## Checkpoint: After Tasks 1-2

- [x] Fake interactive command capture works locally.
- [x] `SUMMARY.md` is bounded evidence-aware and still conservative.
- [ ] Aga reviews whether the bounded evidence language is useful enough before
      adding the remaining report artifacts.

## Checkpoint: After Tasks 3-5

- [ ] Fake-command runs write the complete Phase 3 review package.
- [ ] Local lint, format check, typecheck, tests, and build pass.
- [ ] Aga reviews the report package before real Codex dogfood.

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
