# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items
  for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and
  remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as
  separate files.

## Current Phase: Phase 2 - Feedback Loops And CLI Scaffold

Goal: create the smallest installable Python CLI scaffold that can run a fake
agent command through PatchTrace, produce local run material under
`.patchtrace/runs/<run-id>/`, and prove the local quality loops before real
analyzer behavior starts.

Phase boundary:
- Build only the scaffold, CLI command surface, fake-command capture path, git
  evidence capture, and one minimal Markdown artifact.
- Keep real Codex dogfood, full claim extraction, full verdict/report behavior,
  watch idle detection, package publishing, and any external service out of
  this phase.
- Use the accepted package convention: `src/patchtrace/<capability>/...`.

Suggested implementation branch: `agent/phase-2-cli-scaffold`.

## Dependency Graph

```text
project metadata + local check config
  -> installable `patchtrace` CLI help path
    -> run storage + run manifest model
      -> fake-command PTY transcript capture
        -> git before/after evidence capture
          -> minimal Markdown summary artifact
            -> CI runs the same local checks
```

## Active Tasks

### Task 1: Installable CLI Help Path

**Status:** Complete.

**Description:** Scaffold the Python package and local quality-loop
configuration so `patchtrace` is installable from source and exposes the V0
command surface before any capture behavior exists.

**Acceptance criteria:**
- [x] `pyproject.toml` defines Python >=3.11, the `patchtrace` console script,
      accepted runtime dependencies, and dev dependencies for pytest, Ruff, and
      mypy.
- [x] `uv run patchtrace --help` exits 0 and lists `run`, `analyze`, and
      `watch` with conservative placeholder behavior for unimplemented paths.
- [x] The initial package follows `src/patchtrace/<capability>/...` and avoids
      global technical dumping grounds.

**Verification method:**
- [x] `uv sync`
- [x] `uv run patchtrace --help`
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `uv run pytest`
- [x] `uv build`

**Dependencies:** None.

**Likely touched files:**
- `pyproject.toml`
- `uv.lock`
- `src/patchtrace/__init__.py`
- `src/patchtrace/__main__.py`
- `src/patchtrace/cli/app.py`
- `tests/unit/test_cli_help.py`

**Do-not-touch list:**
- No real Codex adapter behavior.
- No claim extraction, verdict taxonomy changes, or analyzer behavior.
- No external services, LLM calls, telemetry, publishing, auth, database, or UI.

### Task 2: Fake Run Creates A Run Folder And Transcript

**Status:** Complete.

**Description:** Make `patchtrace run -- <fake command>` execute a local fake
agent command through the PTY session path, create a run folder, save a
manifest, and capture the terminal transcript.

**Acceptance criteria:**
- [x] `uv run patchtrace run -- <fake command>` creates
      `.patchtrace/runs/<run-id>/`.
- [x] The run folder contains `run.json` with command, timestamps, trigger
      source, artifact paths written so far, and wrapped command exit status.
- [x] The run folder contains `agent-session.txt` with the fake command output.
- [x] Non-zero fake command exits are recorded without claiming success.

**Verification method:**
- [x] `uv run pytest tests/integration/test_run_fake_command.py`
- [x] Manual smoke:
      `uv run patchtrace run -- python tests/fixtures/fake_agent.py`
- [x] Inspect the latest `.patchtrace/runs/<run-id>/run.json` and
      `agent-session.txt`.

**Dependencies:** Task 1.

**Likely touched files:**
- `src/patchtrace/cli/app.py`
- `src/patchtrace/session/recorder.py`
- `src/patchtrace/storage/runs.py`
- `src/patchtrace/models/run.py`
- `tests/integration/test_run_fake_command.py`
- `tests/fixtures/fake_agent.py`

**Do-not-touch list:**
- No real Codex CLI dogfood test yet.
- No broad transcript parser or claim extraction.
- No hidden background watcher or daemon behavior.

### Task 3: Run Captures Git Evidence

**Status:** Complete.

**Description:** Extend the fake-command run path to capture local git material
before and after the wrapped command when the run starts inside a git
repository.

**Acceptance criteria:**
- [x] A run inside a git repo writes `git-before.txt`, `git-after.txt`,
      `changed-files.txt`, and `patch.diff`.
- [x] The manifest records git artifact paths and whether patch material was
      present.
- [x] Running outside a git repo exits non-zero with an actionable message and
      does not write misleading report artifacts.

**Verification method:**
- [x] `uv run pytest tests/integration/test_git_evidence.py`
- [x] Integration fixture creates a temporary git repo, runs the fake command,
      and asserts the before/after/diff artifacts exist.
- [x] `uv run ruff check .`
- [x] `uv run mypy src tests`

**Dependencies:** Task 2.

**Likely touched files:**
- `src/patchtrace/vcs/git.py`
- `src/patchtrace/vcs/snapshot.py`
- `src/patchtrace/models/run.py`
- `src/patchtrace/storage/runs.py`
- `tests/integration/test_git_evidence.py`

**Do-not-touch list:**
- No GitHub integration or network calls.
- No risk classifier or review-first ordering yet.
- No changes to `.gitignore` unless the run artifact boundary is wrong.

### Task 4: Fake Run Writes A Minimal Summary

**Status:** Complete.

**Description:** Generate the first Markdown artifact from run metadata and raw
material so Phase 2 ends with a visible local review package, while keeping full
reporting behavior for a later phase.

**Acceptance criteria:**
- [x] A successful fake run writes `SUMMARY.md` in the run folder.
- [x] The summary includes run ID, wrapped command, exit status, artifacts
      written, and conservative evidence gaps.
- [x] The summary does not claim the patch is correct, safe, or production
      verified.
- [x] `run.json` lists `SUMMARY.md` as a generated artifact.

**Verification method:**
- [x] `uv run pytest tests/unit/test_summary_report.py`
- [x] `uv run pytest tests/integration/test_run_fake_command.py`
- [x] Manual smoke:
      `uv run patchtrace run -- python tests/fixtures/fake_agent.py`
- [x] Inspect the latest `.patchtrace/runs/<run-id>/SUMMARY.md`.

**Dependencies:** Tasks 2 and 3.

**Likely touched files:**
- `src/patchtrace/reports/summary.py`
- `src/patchtrace/models/report.py`
- `src/patchtrace/models/run.py`
- `tests/unit/test_summary_report.py`
- `tests/integration/test_run_fake_command.py`

**Do-not-touch list:**
- No full `AGENT_FEEDBACK.md` or `VERIFICATION_BRIEF.md` behavior yet.
- No final verdict taxonomy changes.
- No LLM summarization.

### Task 5: CI Proves The Scaffold

**Status:** Complete.

**Description:** Replace the current docs-only CI check with the real Phase 2
feedback loop so every push or PR proves the package scaffold, CLI help path,
fake-run tests, typecheck, lint, format check, and build.

**Acceptance criteria:**
- [x] CI installs Python/uv and runs `uv sync`, Ruff lint, Ruff format check,
      mypy, pytest, and `uv build`.
- [x] README command status changes from planned to available only for commands
      implemented in this phase.
- [x] Architecture/docs stay aligned with any implementation-level deviation
      from the accepted package convention.

**Verification method:**
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `uv run pytest`
- [x] `uv build`
- [x] PR check shows the updated CI workflow passing.

**Dependencies:** Tasks 1-4.

**Likely touched files:**
- `.github/workflows/ci.yml`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/VERIFY_LOG.md`

**Do-not-touch list:**
- No package publishing/release automation.
- No deployment, hosted preview, provider dashboard, database, browser, or UI
  proof.
- No broad roadmap rewrites.

## Checkpoint: Phase 2 Close

- [x] `uv sync` succeeds.
- [x] `uv run patchtrace --help` exits 0.
- [x] `uv run patchtrace run -- python tests/fixtures/fake_agent.py` creates a
      run folder with `run.json`, `agent-session.txt`, git artifacts when in a
      git repo, and `SUMMARY.md`.
- [x] `uv run ruff check .` passes.
- [x] `uv run ruff format --check .` passes.
- [x] `uv run mypy src tests` passes.
- [x] `uv run pytest` passes.
- [x] `uv build` passes.
- [x] Updated CI workflow passes in the PR.
- [x] `docs/VERIFY_LOG.md` records the phase close evidence.

## Deferred

- Real Codex CLI dogfood test after fake-command PTY capture works.
- Full `AGENT_FEEDBACK.md` and `VERIFICATION_BRIEF.md` generation.
- Full claim extraction from real Codex transcript formats.
- `patchtrace watch` idle detection details.
- Optional JSON report output beyond internal run metadata.
- Non-Codex adapters.
- Package publishing, GitHub integration, HTML report, SaaS, auth, database, and
  required LLM analysis.

## Rejected For This Phase

- Saved-diff analyzer as the primary V0 workflow.
- Watcher-first design as full session truth.
- Required LLM extraction.
- External service calls.
