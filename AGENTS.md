# AGENTS.md

## Process

- Read `docs/AGENT_WORKFLOW.md` for the long-form workflow before non-trivial work.
- Read `docs/PLAN.md` before any work. Work on ONE task at a time.
- Use `using-agent-skills` at session start or when the right skill is unclear.
- Build vertical slices: every task ends in a user-visible, verifiable result.
- Run the smallest relevant test loop while editing.
  Run typecheck + relevant tests before EVERY commit.
  Run full tests + build before PR/merge. Commit after every standard task.
- Routine browser proof is a targeted flow/state check, not gstack `/qa`.
  Do not invoke or suggest gstack `/qa` for small changes or ordinary task
  verification. Use `/qa` or `/qa-only` only when Aga explicitly asks for QA,
  testing, or a bug report, or for larger release/client handoff/regression
  passes. If unsure, ask first.
- Larger or riskier changes are PR-first: create a short-lived branch, commit the verified slice there, push it, and open a PR. Do not land substantial work
  directly on `main` unless Aga explicitly asks for that.
- If work happens on a non-default branch, or a `docs/PLAN.md` task has a
  suggested branch, the turn is not done until the branch is pushed and a draft
  PR exists, unless Aga explicitly asks not to open one. Report the PR URL and
  draft/ready status in the final response.
- PR titles must use the `[agent]` prefix, not tool-specific prefixes such as
  `[codex]`. Branch names should use `agent/...`; if a GitHub plugin/skill such
  as `yeet` defaults to `codex/...` or `[codex]`, override it.
- Before any non-trivial work, surface assumptions explicitly:
  `ASSUMPTIONS I'M MAKING: 1... 2... -> Correct me now or I proceed.`
- STOP RULE: after 3 failed fix attempts, stop. Report what you tried and what you observed.
- When a domain term is decided or disambiguated, update `CONTEXT.md`.
- Organize code by product/domain ownership, not global technical-layer dumps.
  Use the module convention recorded in `docs/ARCHITECTURE.md` / `ADR-0001`.
- When work changes project truth, update the matching doc in `docs/` in the same PR.
- Do not create risk-triggered docs before their trigger exists.
- Do not invent. If unknown, write `UNKNOWN`. If not applicable, write `N/A` and why.

## Verification logs

- `docs/VERIFY_LOG.md` is tracked and reserved for meaningful verification
  milestones: phase close, feature verification, deploy/ship checks, high-risk
  work, provider/database/browser proof, or explicit cannot-verify decisions.
- Do not add noisy command-by-command scratch notes to `docs/VERIFY_LOG.md`.
- Use `docs/VERIFY_LOG.local.md` for temporary local notes, repeated command
  output, exploration logs, and pre-commit scratch verification. This file is
  ignored by git.

## Commands

- dev: N/A; V0 is a local CLI.
- install/sync: `uv sync`
- test: `uv run pytest`
- typecheck: `uv run mypy src tests`
- lint: `uv run ruff check .`
- format check: `uv run ruff format --check .`
- build: `uv build`
- db:migrate: N/A; V0 has no database.
- db:seed: N/A; V0 has no database.

## Skill routing

- If routing is unclear, use `using-agent-skills` first and state the chosen skill path.
- Endpoint/server action/webhook/shared interface -> `api-and-interface-design`.
- Screens/components/forms/states/navigation -> `frontend-ui-engineering`.
- Auth/access/tenant data/secrets/payments/provider callbacks/AI actions -> `security-and-hardening` + `doubt-driven-development`.
- Provider/library behavior -> `source-driven-development`; check current docs, not model memory.
- Routine UI/browser verification -> targeted flow/state check, not gstack `/qa`.
- gstack `/qa` or `/qa-only` -> only on Aga's explicit QA/testing/bug-report request,
  or for larger release/client handoff/regression passes; ask first if unsure.

## High-risk override

- High-risk areas: Auth/AuthZ/RLS, payments/entitlements, tenant data, migrations, secrets/env, production config, AI actions/costs.
- For high-risk work: pause before commit and show the diff.
- Migration work must include rollback/backfill plan before execution.
- Auth/data isolation work must include a manual two-user test.
- Payment work must be checked in provider dashboard and database.
- AI endpoint work must prove cost cap, retry cap, logging, and failure path.

## Never

- Auth checks only in UI; always enforce server-side and, where applicable, DB-level isolation.
- Payment or AI endpoint without an explicit failure path.
- Silent catch blocks or accumulated type errors.
- Schema changes outside the migrations directory once a database exists.
- Refactor unrelated code or delete tests to make build pass.
- Assume provider behavior from memory.
- Commit secrets, tokens, customer data, or screenshots containing secrets.

## Ask first

- Anything touching auth, access/isolation policies, payments, migrations, production config, new dependencies, AI actions, or cost boundaries.

## Done means

- Typecheck + tests + build pass.
- Core flow verified in runtime with proportional command/artifact proof; browser, database, and provider proof only when applicable.
- Diff explained and committed; branch pushed and draft PR opened when the work
  is branch-based; cannot-verify items named.
