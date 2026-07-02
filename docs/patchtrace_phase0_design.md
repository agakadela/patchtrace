# PatchTrace Phase 0 Design - Historical Note

Status: historical input, superseded by the current Python V0 spec.

Canonical sources:

- `docs/SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/decisions/ADR-0001-project-foundation.md`
- `docs/PLAN.md`

## Original Problem Statement

AI coding agents can produce patches faster than developers can comfortably
verify them. After a session, the developer has a requested task, agent claims,
a changed working tree, a diff, command output, test output, and uncertainty
about what was actually verified.

PatchTrace exists to compare agent work against local evidence before the human
accepts the patch.

## Preserved Product Insight

The valuable question is not only:

```text
are there bugs in this patch?
```

The sharper PatchTrace question is:

```text
did the agent actually do what it claimed, and what evidence is missing?
```

That remains the center of the Python V0.

## Superseded Implementation Direction

The old Phase 0 direction emphasized manually collecting patch material and
running an analyzer after the agent finished.

The current direction is stronger for dogfooding:

```bash
patchtrace run -- codex
```

This records the session while it happens, so PatchTrace can preserve the
transcript, command output, git before/after state, and patch in one run folder.

Manual analysis remains a fallback. Watching the repo remains a secondary safety
net, not the primary truth source.

## Current V0 Constraints

- Local-first.
- CLI-first.
- Python package managed with `uv`.
- Typer CLI.
- Pydantic v2 models.
- Pexpect-backed PTY capture.
- pytest, Ruff, and mypy feedback loops.
- No required database.
- No required external service calls.
- No required LLM.

## Current Success Criteria

Phase 2 should start by proving the smallest full loop:

1. `patchtrace --help` works.
2. `patchtrace run -- <fake command>` runs a child command.
3. A run folder is created under `.patchtrace/runs/<run-id>/`.
4. The transcript is captured.
5. Git before/after material is captured when available.
6. A minimal `SUMMARY.md` is generated.
7. Lint, format check, typecheck, tests, and build pass.

## Historical Value

Keep these Phase 0 instincts:

- source-backed reasoning beats generic advice,
- conservative cannot-verify sections are a feature,
- test evidence quality matters,
- risk areas should change review priority,
- reports should help the human decide what to inspect first.

Use the canonical docs for all current implementation choices.
