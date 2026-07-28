# PatchTrace

PatchTrace is a local evidence and verification layer for coding-agent runs. It
helps a developer decide whether the captured evidence is sufficient to review
or accept a run, whether more verification is needed, or whether work should be
sent back to the agent.

PatchTrace does not prove semantic correctness and does not make the final
decision for the developer.

## Current status

Version `0.1.0` is the completed Phase 4 baseline. The implemented command is:

```bash
patchtrace run -- <command>
```

It:

- runs the command in an interactive PTY;
- preserves the terminal transcript;
- records Git status before and after the command;
- records the final staged and unstaged diff visible after the command;
- applies deterministic rules to bounded claims in one identified final answer;
- writes one local review package under `.patchtrace/runs/<run-id>/`.

`patchtrace analyze` and `patchtrace watch` are placeholders and exit with an
explicit not-implemented error.

## Try it

PatchTrace requires Python 3.11 or newer and uses
[uv](https://docs.astral.sh/uv/) for project development.

```bash
uv sync
uv run patchtrace run -- python tests/fixtures/fake_agent.py
```

To wrap an installed interactive Codex CLI:

```bash
uv run patchtrace run -- codex
```

The wrapped command retains its normal terminal interaction. When it exits,
PatchTrace prints the path to the generated package.

## Run package

The Phase 4 package contains:

```text
.patchtrace/runs/<run-id>/
├── run.json
├── agent-session.txt
├── git-before.txt
├── git-after.txt
├── changed-files.txt
├── patch.diff
├── SUMMARY.md
├── AGENT_FEEDBACK.md
└── VERIFICATION_BRIEF.md
```

The reports are deterministic views of one validated analysis result:

- `SUMMARY.md` gives the verdict, most important gap, and next action.
- `AGENT_FEEDBACK.md` turns evidence gaps into follow-up requests.
- `VERIFICATION_BRIEF.md` links assessed claims to local evidence for review.

## Current evidence limits

The Phase 4 package is useful, but it is not yet trusted session provenance:

- the final Git diff can include work that existed before the run;
- untracked content and commits made during the run are not captured completely;
- a file dirty before and after the run cannot be attributed honestly;
- the PTY parser requires exactly one supported final-answer marker;
- a missing or ambiguous marker degrades claim evidence; PatchTrace does not
  guess from the transcript tail;
- command and test signals are inferred from terminal text, not structured
  command events;
- there is no preserved task contract or requirement-coverage analysis;
- a passing check is not proven fresh relative to the final repository state.

Treat current verdicts as review guidance within those limits, not as proof of
correctness or acceptance.

## Product direction

The next phase strengthens capture before broadening analysis:

1. distinguish session-attributed, pre-existing, and indeterminate Git changes;
2. separate process, analysis, and package outcomes;
3. preserve a simple Task Contract and bind it to the run;
4. pass that same preserved task through supported Codex-specific modes;
5. test whether the official Codex App Server can provide structured evidence
   for the same interactive session without replacing the current UX.

Interactive PTY remains the primary compatibility workflow. Structured Codex
execution may be offered as a separate higher-evidence task mode. App Server is
a candidate subject to a small feasibility prototype, not an accepted target
architecture.

See:

- [Product specification](docs/SPEC.md)
- [Roadmap](docs/ROADMAP.md)
- [Current Phase 5 plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Domain language](CONTEXT.md)

## Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv build
```

Verification milestones are recorded in
[docs/VERIFY_LOG.md](docs/VERIFY_LOG.md).
