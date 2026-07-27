# PatchTrace

Local evidence and a decisive verification verdict for the moment after a
coding agent says "done."

PatchTrace records one agent run, binds it to local task and repository
material, and produces a review package that helps a human answer:

- what was requested;
- what the agent claimed;
- which Git changes and command results belong to the recorded session;
- which requirements and claims have evidence;
- what is incomplete, conflicting, or not verifiable;
- where review should start and what feedback to send back.

PatchTrace is not a correctness oracle, a general AI code reviewer, or an
autonomous approval agent. It gives a decisive recommendation; the human keeps
the final decision.

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

- task-contract capture or requirement coverage;
- session-scoped Git attribution;
- a real Codex adapter boundary;
- structured Codex JSONL or final-message ingestion;
- repository-state freshness for command/test evidence;
- separate wrapped-command, analysis, and package outcomes;
- an implemented `patchtrace analyze` or `patchtrace watch` command.

Those limits matter. Today, the final Git diff can include pre-existing worktree
changes, final-output recognition depends on a Codex TUI marker, and
command/test results are inferred from transcript text.

See `docs/SPEC.md` for the target product, full capability roadmap, and scope.
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
task contract
  -> one resolved repository execution root
  -> private run storage outside the tracked worktree
  -> recorded agent session
  -> final claims + Git changes + command/test evidence
  -> provenance and session attribution
  -> deterministic analysis
  -> one shared result
  -> verification verdict, recommended action, and evidence detail
  -> human decision
```

The next phase strengthens evidence ownership before PatchTrace adds broader
analysis. In particular, it introduces explicit task binding, session-attributed
Git evidence, a concrete Codex boundary, structured evidence where Codex
provides it, command-result freshness, and separate process/analysis/package
outcomes.

## Source Of Truth

| Area | File |
|---|---|
| Product definition, scope, success criteria, roadmap | `docs/SPEC.md` |
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

- V0 targets macOS/Linux-style local CLI workflows.
- Windows PTY support is deferred.
- SaaS, auth, teams, billing, databases, queues, dashboards, automatic fixes,
  broad agent plugins, and required LLM analysis are out of scope.
- Optional integrations require a demonstrated use case and explicit approval.
