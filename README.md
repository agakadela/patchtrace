# PatchTrace

Local evidence and a decisive task-fulfillment verdict for the moment after
Codex says "done."

PatchTrace binds one explicit task to a local Codex run, repository delta, final
verification, and review package so a developer can answer:

- what was requested;
- what the agent claimed;
- which Git changes and command results belong to the recorded session;
- which requirements and claims have evidence;
- what is incomplete, conflicting, or not verifiable;
- where review should start and what feedback to send back.

PatchTrace is not a correctness oracle or general AI code reviewer. It makes a
strong decision about task fulfillment — `ready_to_accept`, `send_back`,
`review_required`, `rerun_required`, or `cannot_assess` — while the developer
performs the final action.

## Current Status

The current Python V0 implements:

- `patchtrace run -- <command>` with PTY-based local session capture;
- before/after Git status plus a final working-tree diff;
- deterministic extraction of bounded explicit claims from one identified
  `Final answer:` region;
- heuristic command/test signal extraction;
- one shared `AnalysisResult`;
- three Markdown renderers:
  `SUMMARY.md`, `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`;
- fixture-first tests and a real Codex CLI 0.144.1 dogfood path.

The current implementation does **not** yet provide:

- task-contract capture;
- session-scoped Git attribution;
- a real Codex adapter boundary;
- structured Codex JSONL or final-message ingestion;
- repository-state freshness for command/test evidence;
- separate wrapped-command, analysis, and package outcomes;
- final-state required verification or complete requirement coverage;
- an implemented `patchtrace analyze` or `patchtrace watch` command.

Those limits matter. Today, the final Git diff can include pre-existing worktree
changes, final-output recognition depends on a Codex TUI marker, and
command/test results are inferred from transcript text.

See `docs/SPEC.md` for the target product and scope.
See `docs/ROADMAP.md` for the complete project roadmap.
See `docs/PLAN.md` for the detailed next phase.

## Current Workflow

Run a command through PatchTrace:

```bash
uv run patchtrace run -- python tests/fixtures/fake_agent.py
```

The dogfood workflow is:

```bash
uv run patchtrace run -- codex
```

Each recorded run writes:

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

The review package is useful evidence, but its current Git and transcript
limitations must be considered before relying on a claim assessment.

`patchtrace analyze` and `patchtrace watch` are visible in CLI help but currently
exit with explicit not-implemented behavior.

## Target Trust Chain

```text
validated Markdown task
  -> one resolved repository execution root
  -> private run storage outside the tracked worktree
  -> unchanged user payload + versioned PatchTrace execution/response protocol
  -> structured `codex exec`
  -> structured final claims + session-attributed Git delta
  -> final required verification
  -> deterministic requirement coverage
  -> one shared AnalysisResult
  -> decisive verdict + action + three reports
```

The next phase delivers this complete trusted flow end to end. Later committed
phases add review prioritization, compatible post-hoc analysis, continuous local
watch, OSS distribution, and Windows portability. Conditional integrations are
recorded separately and require real demand.

## Source Of Truth

| Area | File |
|---|---|
| Product definition, scope, success criteria | `docs/SPEC.md` |
| Complete phase sequence and status | `docs/ROADMAP.md` |
| Proposed next phase and detailed active tasks | `docs/PLAN.md` |
| Current and target architecture, trust boundaries | `docs/ARCHITECTURE.md` |
| Domain language | `CONTEXT.md` |
| Irreversible decisions | `docs/decisions/` |
| Verified milestones | `docs/VERIFY_LOG.md` |
| Agent operating workflow | `docs/AGENT_WORKFLOW.md` |

## Development Commands

```bash
uv sync
uv run patchtrace --help
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv build
```

## Privacy

Run artifacts may contain source paths, diffs, prompts, terminal output, command
results, and agent messages. The current implementation stores them locally
under `.patchtrace/`. The Phase 5 target moves them to PatchTrace-owned Git
metadata outside the tracked worktree, so ordinary `git add` cannot stage them.
Do not commit or share private run folders, transcripts, diffs, secrets, tokens,
customer data, or provider output.

PatchTrace requires no LLM, account, database, hosted service, or external
telemetry.

Target reports minimize copied task, command, and output content and prefer
locators into private raw artifacts. Local integrity detects mutation after
capture; it is not a tamper-proof audit boundary against a malicious local
process running as the same user.

## Platform And Product Boundaries

- Current V0 targets macOS/POSIX-style local CLI workflows.
- The roadmap adds Linux before public OSS release and a later explicit Windows
  portability phase.
- SaaS, auth, teams, billing, databases, queues, dashboards, automatic fixes,
  broad agent plugins, and required LLM analysis are out of scope.
- Optional integrations require a demonstrated use case and explicit approval.
