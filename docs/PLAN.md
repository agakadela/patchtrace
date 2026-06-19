# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as separate files.

## Current Phase: Phase 3 - Local CLI Walking Skeleton

Goal: make `patchtrace analyze` run one narrow end-to-end local verification path:
read saved patch material, produce a Markdown `VERIFICATION_BRIEF.md`, and prove
the output through fixture-driven tests.

Phase 3 is the PatchTrace equivalent of the generic walking skeleton. V0 has no
auth, database, provider dashboard, browser UI, deploy target, or hosted surface,
so runtime proof is local CLI proof plus fixture output proof.

Supporting design docs checked:
- `docs/patchtrace_phase0_design.md`
- `docs/patchtrace_project_starting_brief_rewritten.md`

Those docs reinforce fixture-first development, the payment/webhook demo moment,
Markdown as the core output, and the local CLI boundary. Their older suggested
`src/core`, `rules`, and `schemas` layout is superseded by the accepted
`src/modules/` convention in `docs/ARCHITECTURE.md` and `ADR-0001`.

### Five-line feature spec

- Problem: `patchtrace analyze` currently shows help, but cannot analyze local materials.
- Flow: developer runs `patchtrace analyze --diff ... --changed-files ... --summary ... --test-output ... --out ...`.
- Visible result: a Markdown `VERIFICATION_BRIEF.md` is written with evidence-linked sections.
- Success bar: the payment/webhook fixture produces a conservative, useful brief without LLM calls or external services.
- Out of scope: SaaS, auth, GitHub integration, HTML UI, package publishing, required LLM analysis, and broad correctness review.

### Dependency graph

```text
CLI option parsing and file IO
  -> local material readers (`patch`, `evidence`)
  -> normalized in-memory report inputs
  -> narrow analyzer rules (`risk`, `claims`, `test-quality`, `verdict`)
  -> Markdown renderer (`report`)
  -> CLI writes `VERIFICATION_BRIEF.md`
  -> fixture and CLI smoke tests prove the generated brief
```

Implementation order follows this graph while keeping each task user-visible.

## Ordered vertical-slice tasks

### Task 1: Freeze the five V0 fixture scenarios

**Description:** Create the missing fixture scenarios from the accepted spec before broadening analyzer behavior. The payment/webhook fixture already exists; this task adds the other four scenario folders with local inputs and hand-written expected `VERIFICATION_BRIEF.md` outputs at the same level of specificity.

**Acceptance criteria:**
- [x] `evals/fixtures/` contains five fixture folders for payment/webhook/idempotency, auth/session/ownership, weak-or-missing test-claim evidence, failed tests vs agent "done", and AI endpoint without usage/rate-limit evidence.
- [x] Each fixture contains local material files appropriate to the scenario, including `agent-summary.md`, `changed-files.txt`, `patch.diff`, `test-output.txt` when applicable, `notes.md` when useful, and expected `VERIFICATION_BRIEF.md`.
- [x] Fixture discovery tests assert that all five fixtures exist and that each expected brief contains scenario-specific conservative signals.

**Verification method:**
- [x] `pnpm test -- tests/fixtures.test.ts`
- [x] Manual read of the four new expected briefs confirms they are evidence-linked and not generic checklists.

**Dependencies:** None.

**Likely touched files:**
- `evals/fixtures/*`
- `tests/fixtures.test.ts`

**Do-not-touch list:**
- Do not implement analyzer behavior in this task.
- Do not add JSON output files unless separately approved.
- Do not add SaaS, auth, GitHub integration, HTML UI, required LLM analysis, network calls, package publishing, or new runtime dependencies.
- Do not use fixture scenarios to change accepted product scope, verdict taxonomy, or claim-support taxonomy.

### Task 2: Saved material generates a brief shell

**Description:** Replace the scaffold-only `analyze` path with the smallest real local CLI flow. The command should read saved fixture files, validate required input combinations, and write a structured Markdown brief shell with inputs reviewed and a conservative verdict placeholder.

**Acceptance criteria:**
- [x] `patchtrace analyze --diff evals/fixtures/payment-webhook-idempotency/patch.diff --changed-files evals/fixtures/payment-webhook-idempotency/changed-files.txt --summary evals/fixtures/payment-webhook-idempotency/agent-summary.md --test-output evals/fixtures/payment-webhook-idempotency/test-output.txt --out <tmp>/VERIFICATION_BRIEF.md` exits 0 and writes a Markdown file.
- [x] The generated file contains `# VERIFICATION_BRIEF.md`, `## Conservative verdict`, and `## Inputs reviewed`.
- [x] Invalid or missing local input paths exit non-zero with an actionable stderr message; no misleading partial brief is silently written.

**Verification method:**
- [x] `pnpm test -- tests/cli.test.ts`
- [x] `pnpm typecheck`
- [x] Manual CLI smoke against the payment fixture writes the output file.

**Dependencies:** Task 1.

**Likely touched files:**
- `src/cli/commands/analyze.ts`
- `src/cli/io.ts`
- `src/modules/patch/*`
- `src/modules/evidence/*`
- `src/modules/report/*`
- `tests/cli.test.ts`

**Do-not-touch list:**
- Do not add new runtime dependencies.
- Do not add LLM, network, GitHub, package publishing, auth, database, or HTML UI behavior.
- Do not change verdict or claim-support taxonomy.

### Task 3: Payment/webhook risk and review-first files appear in the generated brief

**Description:** Add the first deterministic analyzer slice for changed-file and diff risk. The payment/webhook fixture should produce file-specific risk areas and ordered review-first guidance from the provided paths and patch text.

**Acceptance criteria:**
- [x] Generated output for the payment fixture includes `## Risk areas` with payment/webhook/access, entitlement, idempotency-storage, and test-quality risk language tied to fixture files.
- [x] Generated output includes `## Review first` with the webhook route, Stripe event storage, entitlement, and test files in a useful order.
- [x] Risk and review-first output is derived from provided paths/diff content, not from agent-summary claims alone.

**Verification method:**
- [x] `pnpm test -- tests/fixtures.test.ts`
- [x] `pnpm test -- tests/cli.test.ts`
- [x] Manual CLI smoke confirms the generated brief includes the expected risk and review-first sections.

**Dependencies:** Task 2.

**Likely touched files:**
- `src/modules/patch/*`
- `src/modules/risk/*`
- `src/modules/report/*`
- `src/cli/commands/analyze.ts`
- `tests/fixtures.test.ts`

**Do-not-touch list:**
- Do not build generic security review or correctness scoring.
- Do not introduce provider/dashboard checks; provider proof remains cannot-verify unless provided as local evidence.
- Do not move application logic into global `core/`, `rules/`, `schemas`, `services`, `types`, or `utils` dumping grounds.

### Task 4: Agent claims and test-quality evidence are assessed conservatively

**Description:** Extend the same CLI path to extract explicit claims from the agent summary and compare them to patch/test evidence for the payment fixture. Add a test-quality section that distinguishes passing test output from strong behavioral proof.

**Acceptance criteria:**
- [x] Generated output includes `## Agent claims and support` with the four payment fixture claims represented using the accepted claim-support taxonomy: supported, partially supported, unsupported, contradicted, or cannot-determine.
- [x] Generated output includes `## Test quality` with observed test command/result and weak or missing duplicate-event coverage notes.
- [x] The analyzer does not infer unstated claims; each claim is traceable to the provided summary or notes.

**Verification method:**
- [x] `pnpm test -- tests/fixtures.test.ts`
- [x] `pnpm test -- tests/cli.test.ts`
- [x] Manual CLI smoke confirms claim-support and test-quality sections are present and conservative.

**Dependencies:** Task 3.

**Likely touched files:**
- `src/modules/claims/*`
- `src/modules/evidence/*`
- `src/modules/test-quality/*`
- `src/modules/report/*`
- `tests/fixtures.test.ts`

**Do-not-touch list:**
- Do not add broad session-log parsing for Codex, Cursor, Claude Code, or Copilot.
- Do not treat the agent summary as truth.
- Do not change claim-support taxonomy without explicit approval.

### Task 5: Cannot-verify items and verdict selection close the payment fixture loop

**Description:** Add cannot-verify generation and conservative verdict selection for the payment fixture so the generated brief matches the expected report's product intent, not just its section headings.

**Acceptance criteria:**
- [x] Generated output includes `## Cannot verify from provided material` or the accepted equivalent title with Stripe dashboard, deployed env, database constraint, provider replay, and prior-duplicate-access gaps.
- [x] Generated output includes `## Suggested next checks` with evidence-linked next actions.
- [x] Conservative verdict is `needs_human_review` for the payment fixture and avoids words like "safe", "correct", "guaranteed", or "production verified".
- [x] Fixture tests compare the generated payment brief against expected key sections or a stable normalized expected output.

**Verification method:**
- [x] `pnpm test -- tests/fixtures.test.ts`
- [x] `pnpm lint`
- [x] `pnpm typecheck`
- [x] Manual CLI smoke confirms the generated payment fixture brief is useful before reading the full diff.

**Dependencies:** Task 4.

**Likely touched files:**
- `src/modules/risk/*`
- `src/modules/verdict/*`
- `src/modules/report/*`
- `evals/fixtures/payment-webhook-idempotency/VERIFICATION_BRIEF.md`
- `tests/fixtures.test.ts`

**Do-not-touch list:**
- Do not claim production/provider verification from static fixture files.
- Do not add optional JSON output unless separately approved.
- Do not change public verdict taxonomy without explicit approval.

### Task 6: Insufficient-material failure state is explicit and useful

**Description:** Add the first failure/empty-state slice so `patchtrace analyze` handles missing patch material conservatively instead of pretending analysis happened.

**Acceptance criteria:**
- [x] Running `patchtrace analyze --summary <path> --out <tmp>/VERIFICATION_BRIEF.md` without `--diff`/`--changed-files` and without a usable git comparison writes an `insufficient_material` brief.
- [x] Missing test output is represented as missing test evidence, not as passing tests.
- [x] Unreadable local input paths still exit non-zero with an actionable stderr message.
- [x] Error or report language tells the developer exactly which local materials are needed next.

**Verification method:**
- [x] `pnpm test -- tests/cli.test.ts`
- [x] `pnpm test -- tests/fixtures.test.ts`
- [x] Manual CLI smoke for missing material shows the expected stderr or generated `insufficient_material` brief.

**Dependencies:** Task 5.

**Likely touched files:**
- `src/cli/commands/analyze.ts`
- `src/modules/evidence/*`
- `src/modules/verdict/*`
- `src/modules/report/*`
- `tests/cli.test.ts`

**Do-not-touch list:**
- Do not implement live git diff collection unless explicitly chosen for this task; saved-diff support is enough for Phase 3.
- Do not hide missing material behind generic checklist output.
- Do not add network or external service calls.

## Phase close checkpoint

- [ ] `pnpm lint`
- [ ] `pnpm typecheck`
- [ ] `pnpm test`
- [ ] `pnpm build`
- [ ] Built CLI smoke: `node dist/cli/index.js analyze --diff evals/fixtures/payment-webhook-idempotency/patch.diff --changed-files evals/fixtures/payment-webhook-idempotency/changed-files.txt --summary evals/fixtures/payment-webhook-idempotency/agent-summary.md --test-output evals/fixtures/payment-webhook-idempotency/test-output.txt --out <tmp>/VERIFICATION_BRIEF.md`
- [ ] `docs/VERIFY_LOG.md` gets one compact Phase 3 closeout entry.
- [ ] `README.md`, `docs/SPEC.md`, and `docs/ARCHITECTURE.md` are updated only if project truth changed.
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
