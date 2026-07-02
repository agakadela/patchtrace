# PatchTrace - Historical Starting Brief

Status: historical input, superseded by the current Python V0 spec.

Canonical sources:

- `docs/SPEC.md` for current product scope.
- `docs/ARCHITECTURE.md` for current stack and module boundaries.
- `docs/decisions/ADR-0001-project-foundation.md` for foundation decisions.
- `CONTEXT.md` for current domain language.

This document preserves the original product framing that led to PatchTrace.
It is not the implementation plan.

## Preserved Framing

PatchTrace helps developers verify what an AI coding agent changed before they
accept the work.

The core product insight remains:

```text
requested task
-> agent claims
-> actual patch
-> command/test evidence
-> conservative verification brief
```

PatchTrace is not a generic AI code reviewer, correctness oracle, model
benchmark, SaaS dashboard, or replacement for human review. It is a local-first
verification layer for AI-assisted coding work.

## Current Interpretation

The current Python V0 turns the original patch-analysis idea into a stronger
dogfood workflow:

```bash
patchtrace run -- codex
```

That command is intended to wrap a Codex CLI session, preserve the terminal
transcript, capture git state before and after the run, collect the patch, and
produce:

- `SUMMARY.md`
- `AGENT_FEEDBACK.md`
- `VERIFICATION_BRIEF.md`

Manual analysis remains useful, but it is a fallback:

```bash
patchtrace analyze
```

The watcher remains a secondary safety net:

```bash
patchtrace watch
```

## Product Boundaries

V0 is:

- local-first,
- CLI-first,
- Python-first,
- rules-first,
- Markdown-first,
- conservative about what can and cannot be verified.

V0 is not:

- a hosted service,
- a PR bot,
- a required LLM workflow,
- a correctness score,
- a public proof system,
- a replay/video tool,
- a multi-agent observability platform.

## Claim And Evidence Model

PatchTrace treats the agent summary as a claim source, not as truth.

Useful support levels:

- `supported`
- `partially_supported`
- `unsupported`
- `contradicted`
- `cannot_determine`

Evidence can come from:

- session transcript,
- changed files,
- diff hunks,
- command output,
- test output,
- developer notes,
- generated run metadata.

The report should tie every material conclusion back to available evidence and
name what cannot be verified locally.

## Example Scenario

```text
Agent claim:
Added duplicate Stripe webhook protection and tests.

Observed evidence:
- billing webhook code changed
- entitlement logic changed
- a webhook test changed
- provided output shows a passing webhook test

PatchTrace result:
Partially supported. The changed files are related to the claim, but the
available evidence does not prove duplicate-event behavior or production
provider settings.

Review first:
1. billing webhook handler
2. entitlement state update path
3. webhook test coverage

Verdict:
Needs focused human review before accepting.
```

## Current Build Direction

The current implementation should follow `docs/PLAN.md`:

1. Scaffold a Python package with `uv`.
2. Expose a Typer CLI.
3. Implement a fake-command `patchtrace run -- <command>` path first.
4. Capture a PTY transcript and git before/after state.
5. Write run artifacts under `.patchtrace/runs/<run-id>/`.
6. Generate a minimal `SUMMARY.md`.
7. Add Ruff, mypy, pytest, and build checks before real analyzer behavior.

## Historical Value

This brief is useful only as product memory:

- keep the tool skeptical of agent claims,
- avoid false confidence,
- make missing evidence visible,
- keep outputs review-oriented,
- prefer local source-backed evidence over generic warnings.

For active work, use the canonical docs listed at the top of this file.
