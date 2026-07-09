# PatchTrace

Record Codex CLI sessions and turn agent work into a local verification package.

PatchTrace is a local-first devtool for the moment after an AI coding agent says
"done." It captures the agent session, collects local git evidence, and writes
practical next-step artifacts. Deeper claim-vs-diff comparison is target V0
work beyond the current fake-command checkpoint.

PatchTrace does not replace human code review. It helps you decide what to do
next with better evidence.

## Status

- Stage: Python V0 Phase 3 real Codex dogfood proof captured locally
- Current phase: see `docs/PLAN.md`
- Product spec: see `docs/SPEC.md`
- Architecture: see `docs/ARCHITECTURE.md`
- Verification history: see `docs/VERIFY_LOG.md`
- Agent workflow: see `docs/AGENT_WORKFLOW.md`

## Source Of Truth

| Area | File |
|---|---|
| Product scope and success criteria | `docs/SPEC.md` |
| Current execution plan | `docs/PLAN.md` |
| Stack, package convention, data flow, trust boundaries | `docs/ARCHITECTURE.md` |
| Domain language | `CONTEXT.md` |
| Irreversible decisions | `docs/decisions/` |
| Verification proof | `docs/VERIFY_LOG.md` |
| Agent operating workflow | `docs/AGENT_WORKFLOW.md` |

Risk-triggered docs are created only when triggered:

| Trigger | File |
|---|---|
| First protected route/user | `docs/AUTH_ACCESS_MODEL.md` |
| Shared endpoint/action/webhook/public API | `docs/API_CONTRACTS.md` |
| Second view | `docs/UI_SYSTEM.md` |
| First AI call | `docs/AI_BOUNDARIES.md` |
| Provider with webhook/callback | `docs/INTEGRATIONS.md` |
| Existing/rescue repo | `docs/SYSTEM_MAP.md` |
| Launch prep | `docs/OPERATIONS.md` |
| Client delivery | `docs/HANDOFF.md` |

## Current Phase 3 Fake-Command Checkpoint

The implemented local checkpoint can run a fake command through PatchTrace:

```bash
uv run patchtrace run -- python tests/fixtures/fake_agent.py
```

That command creates a local run folder with the complete Phase 3 review
package shape:

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

The CLI help path is available with:

```bash
uv run patchtrace --help
```

`patchtrace analyze` and `patchtrace watch` are visible in help but still exit
with conservative placeholder behavior.

## Target V0

The primary V0 workflow is:

```bash
patchtrace run -- codex
```

PatchTrace will wrap Codex CLI through a pseudo-terminal, record the session
transcript, capture git state before and after the agent run, and write:

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

`patchtrace analyze` remains a manual fallback. `patchtrace watch` is planned as
a secondary patch-only safety net when no session transcript is available.
Real Codex dogfood is the next checkpoint; it has not been verified by the
current fake-command review-package proof.

## Available Local Loop

These commands are available in the current scaffold:

```bash
uv sync
uv run patchtrace --help
uv run patchtrace run -- python tests/fixtures/fake_agent.py
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv build
```

## Environment

- Local app URL: N/A; V0 is a CLI.
- Preview/staging URL: N/A.
- Production URL: N/A.
- Database projects are separated by environment: N/A; V0 has no database.
- Secrets live in: N/A; V0 should not require secrets.
- Local run artifacts live under `.patchtrace/runs/` once implemented.

Do not put real secrets, customer data, provider tokens, private transcripts, or
private diffs in README, docs, screenshots, commits, or chat.

## Development Workflow

- Read `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, and `docs/PLAN.md` before work.
- Work on one task at a time.
- Use `using-agent-skills` when the right skill path is unclear.
- Commit after each standard task once verified.
- Use `pause before commit` for high-risk work.
- Merge only after review and runtime verification.

## Deployment

- Provider: N/A for V0.
- Deploy command/process: N/A until package release or hosted surface exists.
- Rollback process: see `docs/OPERATIONS.md` once launch prep begins.
- Monitoring: N/A for V0 local CLI.

## Known Limitations

- PatchTrace does not prove code correctness.
- PatchTrace does not claim a patch is safe or production verified.
- V0 has no SaaS, auth, teams, GitHub integration, HTML report, or required LLM calls.
- Full claim-vs-evidence analysis requires session transcript material.
- V0 targets macOS/Linux-style PTY workflows first; Windows support is deferred.
