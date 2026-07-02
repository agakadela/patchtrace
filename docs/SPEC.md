# Spec: PatchTrace Python

Product source of truth: problem, user, scope, flows, and success criteria.

Template rules:
- This file is produced from `$aga-spec` interview, not from silent guessing.
- Do not duplicate architecture, auth, API contracts, UI system, AI boundaries,
  or integrations here. Link to their source docs once they exist.
- If unknown, write `UNKNOWN`. If not applicable, write `N/A` and why.
- Blocking unknowns must be resolved before planning implementation.

## Status

- Product name: PatchTrace
- Spec status: accepted for Python V0 planning
- Owner: project maintainer(s)
- Last updated: 2026-07-02
- Current implementation phase: see `docs/PLAN.md`

## Objective

PatchTrace Python is a local-first devtool for recording an AI coding agent
session and turning the resulting transcript, git patch, and test/command
evidence into a review package.

The Python V0 starts from the strongest dogfood workflow:

```bash
patchtrace run -- codex
```

PatchTrace should be present while Codex CLI works. It records the session,
captures git state before and after the agent run, extracts explicit agent
claims from the transcript, compares those claims against local evidence, and
writes practical next-step artifacts for the human reviewer.

PatchTrace does not replace human code review and does not claim to prove code
correctness, safety, or production readiness.

## Problem

AI coding agents can produce changes faster than a developer can comfortably
verify them. The hardest moment is immediately after the agent says "done":
the developer has a changed working tree, terminal output, maybe test output,
and an agent summary that may sound more certain than the evidence supports.

The pain PatchTrace solves is the decision bottleneck between:

```text
Codex CLI says "done"
```

and:

```text
Aga decides the next move: accept, review manually, run checks, or send the
agent back with precise feedback.
```

## Target User

The primary V0 user is Aga using Codex CLI in her own agent workflow.

Likely later users:
- developers who run local CLI coding agents;
- freelancers or maintainers who need a local record of agent work;
- small teams experimenting with agent-created branches.

V0 optimizes for dogfooding before broad OSS polish.

## Current Workaround / Status Quo

Today the reviewer manually reconstructs the session from terminal output,
agent final messages, git diff, changed files, and test output. This is slow,
easy to do inconsistently, and especially weak at turning unsupported agent
claims into a concrete follow-up prompt.

## Smallest Adoption Wedge

The smallest useful wedge is a local wrapper around Codex CLI that writes a
review package after the agent exits.

The review package must make the next action obvious without requiring the
reviewer to read the full diff cold.

## V0 Scope

V0 is the Codex session recorder and local verification package.

V0 will:
- run as a Python CLI;
- provide `patchtrace run -- codex` as the primary full workflow;
- launch Codex CLI through a pseudo-terminal so interactive terminal behavior
  still works;
- record a local session transcript from the wrapped Codex run;
- capture git status, changed files, and diff before and after the run;
- store run material under `.patchtrace/runs/<run-id>/`;
- extract explicit agent claims from transcript/session material with
  deterministic, rules-first logic;
- classify patch evidence, risk areas, test/command evidence, and missing
  evidence conservatively;
- generate `SUMMARY.md`, `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`;
- support `patchtrace analyze` as a manual fallback for an existing working
  tree, transcript, or saved run material;
- support a secondary `patchtrace watch` concept as a patch-only safety net,
  clearly labeled as limited when no session transcript is available;
- stay useful without any required LLM call or external service.

## Required V0 Artifacts

Each full `patchtrace run -- codex` session writes:

```text
.patchtrace/runs/<run-id>/
  run.json
  agent-session.txt
  git-before.txt
  git-after.txt
  patch.diff
  changed-files.txt
  SUMMARY.md
  AGENT_FEEDBACK.md
  VERIFICATION_BRIEF.md
```

Artifact roles:
- `SUMMARY.md`: short human-readable decision summary and next action.
- `AGENT_FEEDBACK.md`: ready-to-paste feedback for the agent.
- `VERIFICATION_BRIEF.md`: evidence-backed detail including claims, patch
  evidence, test evidence, gaps, review-first files, and conservative verdict.
- `run.json`: structured manifest for the run and generated artifacts.
- Raw material files: local evidence sources used by the reports.

## Explicitly Out Of Scope

V0 will not build:
- SaaS;
- login, auth, teams, workspaces, or cloud sync;
- billing or paid access;
- GitHub App, GitHub OAuth, PR comments, or hosted PR integration;
- local HTML report or dashboard;
- public proof pages, social posts, PNG cards, or video replay;
- broad adapters for every coding agent;
- required LLM analysis;
- automatic correctness scoring;
- claims that code is safe, correct, guaranteed, or production verified;
- sending private code, diffs, transcripts, summaries, or test output to
  external services by default.

## Tech Stack

See `docs/ARCHITECTURE.md` and
`docs/decisions/ADR-0001-project-foundation.md` for foundation decisions.

Accepted product-level constraints:
- Runtime: local CLI.
- Language: Python >=3.11.
- Project manager: `uv`.
- CLI framework: Typer.
- Session/PTY capture: Pexpect, with Python stdlib `pty` as the underlying
  platform concept.
- Data validation: Pydantic v2.
- Test runner: pytest.
- Lint/format: Ruff.
- Typecheck: mypy.
- Analyzer style: deterministic/rules-first.
- Package layout: `src/patchtrace/<capability>/...`.
- Database, auth, hosting, and required AI provider: N/A for V0.

## Commands

These are target commands for the Python foundation. They become executable
after the scaffold task.

```bash
# install/sync dependencies
uv sync

# run the CLI from source
uv run patchtrace --help

# full Codex session workflow
uv run patchtrace run -- codex

# manual fallback analysis
uv run patchtrace analyze

# secondary watch mode, limited without transcript material
uv run patchtrace watch

# lint and format check
uv run ruff check .
uv run ruff format --check .

# typecheck
uv run mypy src tests

# tests
uv run pytest

# build package
uv build
```

## Project Structure

The product structure belongs in `docs/ARCHITECTURE.md`. The accepted
foundation direction is:

```text
src/
  patchtrace/
    __init__.py
    __main__.py
    cli/
    session/
    adapters/
    vcs/
    analysis/
    reports/
    models/
    storage/
tests/
  unit/
  integration/
  fixtures/
docs/
```

The implementation should be organized by PatchTrace capabilities and domain
concepts, not by global technical dumping grounds such as `utils`.

## Code Style

The implementation should favor explicit, typed, evidence-preserving data
transformations.

Example style target:

```python
from enum import StrEnum
from pydantic import BaseModel


class ClaimSupport(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    CANNOT_DETERMINE = "cannot_determine"


class AgentClaimAssessment(BaseModel):
    claim: str
    support: ClaimSupport
    assessment: str
    evidence_sources: list[str]
    missing_evidence: list[str]
```

Style rules:
- Prefer small pure functions for analysis rules.
- Preserve evidence source references wherever possible.
- Keep session capture, git collection, analysis, and report rendering separate.
- Do not hide product judgment inside one prompt or opaque function.
- Do not infer claims that are not stated.
- Use conservative language when evidence is incomplete.
- Validate structured run and report objects with Pydantic models.
- Keep CLI commands thin; product behavior belongs in package modules.

## Testing Strategy

V0 is fixture-first and session-aware.

Before broad analyzer behavior, create fixtures for:
- a recorded Codex-like transcript that claims work is done and tests passed;
- a transcript where tests fail while the agent claims completion;
- a patch-only run with no transcript, producing limited analysis;
- high-risk changed paths such as auth, payment/webhook, AI endpoint, or
  migration-like changes;
- a minimal successful `patchtrace run -- <fake interactive command>` capture.

Test levels:
- unit tests for transcript normalization, claim extraction, evidence matching,
  risk classification, test-evidence assessment, verdict selection, and report
  rendering;
- integration tests for run-folder creation and git snapshot/diff collection;
- PTY capture tests using a local fake command, not real Codex CLI;
- fixture tests comparing generated Markdown sections against expected output;
- CLI smoke tests proving `patchtrace run -- <fake command>` and
  `patchtrace analyze` write expected artifacts.

The tests do not need to prove code correctness. They need to prove PatchTrace
stays conservative, evidence-backed, local-first, and useful.

## Boundaries

Always:
- keep V0 local-first;
- treat the transcript as sensitive local evidence;
- tie warnings, verdicts, and next steps to provided evidence or missing
  evidence;
- use conservative verdict language;
- include cannot-verify items when proof requires unavailable runtime,
  provider, dashboard, secret, deployed environment, live data, or logs;
- keep full claim-vs-evidence analysis dependent on available session material;
- label patch-only analysis as limited when transcript/session evidence is
  missing;
- keep the CLI usable without an LLM.

Ask first:
- adding any LLM call or model SDK;
- adding new runtime dependencies beyond the agreed foundation;
- adding non-Codex agent adapters;
- adding GitHub/PR integration;
- adding an HTML UI or dashboard;
- publishing a package or release;
- changing the verdict taxonomy;
- changing the claim-support taxonomy;
- changing the package/module convention;
- adding any external service, network call, telemetry, or daemon install.

Never in V0:
- SaaS;
- auth or team accounts;
- cloud sync;
- correctness scoring;
- claims that PatchTrace proves safety or correctness;
- sending private code, diffs, transcripts, summaries, or test output to
  external services by default;
- generic checklist output that is not tied to changed files, evidence, or
  missing evidence.

## Core Flows

### Flow 1: Record and analyze a Codex CLI session

- Actor: Aga using Codex CLI.
- Trigger: Aga starts an agent session through PatchTrace.
- Command:

```bash
patchtrace run -- codex
```

- Steps:
  1. PatchTrace creates a new run ID and run folder.
  2. PatchTrace records pre-run git status and diff state.
  3. PatchTrace launches Codex CLI through a pseudo-terminal.
  4. Aga uses Codex normally.
  5. PatchTrace records the terminal transcript locally.
  6. When Codex exits, PatchTrace records post-run git status, changed files,
     and diff.
  7. PatchTrace extracts explicit claims and command/test evidence from the
     transcript.
  8. PatchTrace analyzes claims against patch evidence and missing evidence.
  9. PatchTrace writes `SUMMARY.md`, `AGENT_FEEDBACK.md`, and
     `VERIFICATION_BRIEF.md`.
- Successful outcome: Aga knows the next action and has a ready feedback
  message if the agent should continue.
- Failure/empty states:
  - no git repo: exit with actionable error;
  - no patch after session: write a no-change run summary;
  - transcript capture fails: keep git evidence and mark session evidence
    unavailable;
  - command exits non-zero: record exit code and include it in the verdict;
  - claims cannot be extracted: mark claim material missing or limited.
- Runtime proof required: fake interactive command fixture produces a run
  folder with transcript, diff evidence, and all required Markdown artifacts.

### Flow 2: Analyze existing local material manually

- Actor: developer reviewing an existing changed working tree or saved run.
- Trigger: developer did not start the agent through PatchTrace or wants to
  re-run analysis.
- Command:

```bash
patchtrace analyze
```

- Successful outcome: PatchTrace produces an evidence brief from available git
  material and any supplied transcript/test evidence.
- Failure/empty states:
  - transcript missing: claim analysis is limited;
  - no diff: report says no patch material found;
  - test output missing: test evidence is marked missing, not passed.

### Flow 3: Watch as a secondary safety net

- Actor: Aga running PatchTrace in the background.
- Trigger: working tree changes become idle after agent-like activity.
- Command:

```bash
patchtrace watch
```

- Successful outcome: PatchTrace writes a limited patch-only package when no
  transcript is available, or links to session material when available.
- Failure/empty states:
  - watch triggers early or more than once: deduplicate by run fingerprint
    where practical and label trigger source;
  - no transcript: do not assess agent claims.
- Runtime proof required: local fixture simulates file changes and idle
  detection without requiring real Codex CLI.

## Success Criteria

| Criterion | How measured | Target | Owner |
|---|---|---|---|
| Codex session captured | PTY fake-command integration test | Transcript saved under `.patchtrace/runs/<run-id>/agent-session.txt` | Maintainer |
| Patch evidence captured | Git fixture/integration test | Before/after status, changed files, and diff saved | Maintainer |
| Useful next action | Fixture review | `SUMMARY.md` states accept/review/run-checks/send-back style decision | Maintainer |
| Agent feedback useful | Fixture review | `AGENT_FEEDBACK.md` is ready to paste back to an agent | Maintainer |
| Claim skepticism | Unit and fixture tests | Unsupported, contradicted, missing, and cannot-determine claims are labeled conservatively | Maintainer |
| Test-evidence awareness | Unit and fixture tests | Missing/failing/weak test evidence is visible and actionable | Maintainer |
| Privacy boundary | Code review and tests | No external calls by default; transcript stays local | Maintainer |
| No false confidence | Copy review and tests | No "correct", "safe", "guaranteed", or "production verified" claims without evidence | Maintainer |

## Product Constraints

- Legal/compliance constraints: N/A for V0; PatchTrace is a local devtool and
  does not provide legal, security, or production-safety guarantees.
- Data/privacy constraints: local-first; no external service calls by default;
  do not ask for `.env`, secrets, customer data, provider tokens, or private
  dashboard exports.
- Platform expectations: V0 targets macOS/Linux-style PTY workflows first.
  Windows support is not a V0 acceptance criterion.
- Performance expectations: the report package should be generated quickly
  enough to use after every agent session.
- Accessibility expectations: CLI output and Markdown reports should be
  readable, structured, and usable without a graphical interface.
- Budget/cost constraints: no required paid API or LLM cost in V0.

## Source-Of-Truth Links

| Area | Source |
|---|---|
| Architecture | `docs/ARCHITECTURE.md` |
| Foundation decisions | `docs/decisions/ADR-0001-project-foundation.md` |
| Access model | `docs/AUTH_ACCESS_MODEL.md` once triggered |
| API contracts | `docs/API_CONTRACTS.md` once triggered |
| UI conventions | `docs/UI_SYSTEM.md` once triggered |
| AI boundaries | `docs/AI_BOUNDARIES.md` once triggered |
| Integrations | `docs/INTEGRATIONS.md` once triggered |
| Operations | `docs/OPERATIONS.md` once launch prep begins |

## ADR Candidates

Decisions that may need ADRs because they are hard to reverse, affect public
interfaces, or will surprise future maintainers.

- Project foundation: Python >=3.11 CLI, `uv`, Typer, Pydantic v2, Pexpect,
  pytest, Ruff, mypy.
- Primary interface: `patchtrace run -- codex` instead of saved-material-only
  analysis.
- Package layout: `src/patchtrace/<capability>/...`.
- Local run-folder format under `.patchtrace/runs/<run-id>/`.
- Report package: `SUMMARY.md`, `AGENT_FEEDBACK.md`, and
  `VERIFICATION_BRIEF.md`.
- Local-first/no-cloud/no-required-LLM boundary.
- Claim support taxonomy: `supported`, `partially_supported`, `unsupported`,
  `contradicted`, `cannot_determine`.
- Verdict taxonomy: `ready_for_review`, `needs_manual_review`,
  `run_more_checks`, `send_agent_back`, `insufficient_material`.
- Fixture-first session-capture and analyzer development.

## Open Questions

### Blocking

- N/A. Blocking product and foundation decisions for writing the Python V0 spec
  are resolved.

### Non-Blocking

- Exact idle threshold and deduplication strategy for `patchtrace watch`.
- Whether optional JSON output is exposed publicly or kept as internal run
  metadata.
- Whether real Codex CLI transcript formats need a dedicated parser beyond
  generic transcript rules.
- Package publishing timing and package ownership.
- Whether later non-Codex adapters belong in this package or separate plugins.

## Review Notes

- Accepted by: project maintainer
- Date: 2026-07-02
- Links to discussion/PR: N/A; accepted in local `$aga-spec` interview.
