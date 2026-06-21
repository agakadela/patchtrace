# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as separate files.

## Current Phase: Phase 3 - Agent Closeout Complete, Human Review Pending

Goal: make `patchtrace analyze` run one narrow end-to-end local verification path:
read saved patch material, produce a Markdown `VERIFICATION_BRIEF.md`, and prove
the output through fixture-driven tests.

Agent-owned Phase 3 work is complete as of 2026-06-20. The remaining closeout
checkpoint is human review of the generated payment fixture brief before the
phase is treated as fully closed.

Phase 3 is the PatchTrace equivalent of the generic walking skeleton. V0 has no
auth, database, provider dashboard, browser UI, deploy target, or hosted surface,
so runtime proof is local CLI proof plus fixture output proof.

Closed summary:
- Five V0 fixture families exist with local material and hand-written expected
  `VERIFICATION_BRIEF.md` files.
- `patchtrace analyze` reads saved `--diff`, `--changed-files`, `--summary`,
  optional `--test-output`, and writes a Markdown brief.
- The payment/webhook fixture generates risk areas, review-first guidance,
  claim-support assessment, test-quality assessment, cannot-verify gaps,
  suggested next checks, and a conservative `needs_human_review` verdict.
- Missing or partial patch material generates an explicit
  `insufficient_material` brief with only the missing local materials requested.
- V0 remains local-first and rules-first: no LLM, network, GitHub, package
  publishing, auth, database, payments, provider dashboard, HTML UI, deploy
  target, or external service calls were added.

Supporting design docs checked:
- `docs/patchtrace_phase0_design.md`
- `docs/patchtrace_project_starting_brief_rewritten.md`

Those docs reinforce fixture-first development, the payment/webhook demo moment,
Markdown as the core output, and the local CLI boundary. Their older suggested
`src/core`, `rules`, and `schemas` layout is superseded by the accepted
`src/modules/` convention in `docs/ARCHITECTURE.md` and `ADR-0001`.

## Phase close checkpoint

- [x] `pnpm lint`
- [x] `pnpm typecheck`
- [x] `pnpm test`
- [x] `pnpm build`
- [x] Built CLI smoke: `node dist/cli/index.js analyze --diff evals/fixtures/payment-webhook-idempotency/patch.diff --changed-files evals/fixtures/payment-webhook-idempotency/changed-files.txt --summary evals/fixtures/payment-webhook-idempotency/agent-summary.md --test-output evals/fixtures/payment-webhook-idempotency/test-output.txt --out <tmp>/VERIFICATION_BRIEF.md`
- [x] `docs/VERIFY_LOG.md` gets one compact Phase 3 closeout entry.
- [x] `README.md`, `docs/SPEC.md`, and `docs/ARCHITECTURE.md` are updated only if project truth changed.
- [ ] Human reviews the generated brief before Phase 3 is closed.

## Deferred until after Phase 3

- Generated-output parity for all non-payment fixture families.
- Live git `--base`/`--head` collection beyond saved diff and changed-file input.
- Optional JSON report output.
- Package publishing, GitHub integration, HTML report, SaaS, auth, database, and required LLM analysis.

## Rejected for this phase

- Broad analyzer behavior before one generated brief is useful.
- Generic AI code review framing or correctness scoring.
- External provider checks, dashboard checks, or network calls.
