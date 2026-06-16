# PLAN.md

Execution source of truth: current phase and active tasks only.

Hygiene rule:
- Keep only the current phase, active tasks, deferred items, and rejected items for this phase.
- When a phase closes, move the phase summary to `docs/VERIFY_LOG.md` and remove completed task details from this file.
- Do not store long-term roadmap, completed-task archive, or feature specs as separate files.

## Current Phase: Phase 2 - Target Repo Foundation

### Goal / Visible Result

PatchTrace becomes a real git-backed local CLI project in this `patchtrace/` directory, with working TypeScript feedback loops and the first hand-written fixture brief ready before analyzer implementation.

### Current State

- Project files have been moved into `patchtrace/`.
- `patchtrace/` is initialized as the target git repository.
- Node/TypeScript package scaffold exists with a minimal `patchtrace` CLI help path.
- A placeholder CI file exists at `workflows/ci.yml`; the accepted target is `.github/workflows/ci.yml` with `pnpm`.

### Acceptance Criteria

- [x] Current directory is initialized as the target `patchtrace` git repository.
- [x] Existing accepted docs remain in place and are included in the initial repo history.
- [x] Node/TypeScript package scaffold exists with `pnpm`, TypeScript, Vitest, Zod, and a `patchtrace` CLI binary target.
- [x] `pnpm typecheck`, `pnpm test`, and `pnpm build` pass locally.
- [x] CI workflow runs typecheck, tests, and build.
- [x] `patchtrace analyze --help` or equivalent local CLI help works.
- [ ] First payment/webhook/idempotency fixture has local input files and a hand-written expected `VERIFICATION_BRIEF.md`.

### Not Building In This Phase

- Full analyzer pipeline.
- Claim/evidence matching beyond skeleton types needed for tests.
- All five V0 fixtures.
- JSON public output.
- GitHub/PR integration.
- HTML report or UI.
- SaaS/auth/team functionality.
- Required LLM calls.

### Constraints And Assumptions

- PatchTrace is public OSS; docs and README should stay public-facing.
- V0 remains local-first, CLI-first, Markdown-first, and rules-first.
- Module convention remains `src/modules/` with a thin `src/cli/` entrypoint.
- New dependencies are limited to the accepted foundation unless approved.
- No external service calls should be added.
- This phase may require network access to install npm dependencies.

### Risk Classification

- Overall phase risk: standard
- High-risk areas touched: N/A
- Required high-risk override: N/A

### Dependency Graph

```text
Task 1: git repo + initial docs commit
  -> Task 2: TypeScript CLI scaffold + local feedback loops
      -> Task 3: CI mirrors local feedback loops
      -> Task 4: first payment/webhook fixture + fixture discovery
```

Task 3 and Task 4 can be done after Task 2. They do not depend on each other.

## Active Tasks

### Task 1 - Initialize Target Git Repository

- Status: complete
- User-visible result: the current workspace is the real `patchtrace` repo with accepted docs preserved.
- Acceptance criteria:
  - [x] `git status` works in the current directory.
  - [x] Existing docs, README, AGENTS, `.gitignore`, and `.env.example` are present.
  - [x] Initial commit captures the accepted spec/foundation docs.
- Verification:
  - Automated: `git status --short --branch`
  - Runtime/manual: inspect repository root file list.
  - Data/provider proof: N/A.
- Likely touched files:
  - `.git/`
  - existing docs and root files via initial commit only
- Do not touch:
  - Product scope docs except for mechanical repo-status updates if needed.
- Risk level: standard
- Skill routing:
  - `git-workflow-and-versioning`
- Dependencies:
  - None.
- Assumptions:
  - The target repo root is `patchtrace/`.
- Cannot verify yet:
  - Remote GitHub repo URL, unless created later.

### Task 2 - Scaffold TypeScript CLI Feedback Loops

- Status: complete
- User-visible result: a minimal local `patchtrace` CLI package with passing typecheck, tests, and build.
- Acceptance criteria:
  - [x] `package.json` exposes planned scripts and a `patchtrace` binary.
  - [x] TypeScript config builds `src/`.
  - [x] Vitest has at least one smoke test.
  - [x] Minimal CLI supports help for `analyze` without implementing analysis.
  - [x] `pnpm typecheck`, `pnpm test`, and `pnpm build` pass.
- Verification:
  - Automated: `pnpm typecheck`, `pnpm test`, `pnpm build`
  - Runtime/manual: `node dist/cli/index.js analyze --help`
  - Data/provider proof: N/A.
- Likely touched files:
  - `package.json`
  - `pnpm-lock.yaml`
  - `tsconfig.json`
  - `vitest.config.ts`
  - `src/cli/index.ts`
  - `tests/cli.test.ts`
- Do not touch:
  - Analyzer domain modules beyond a tiny placeholder if needed for CLI help.
- Risk level: standard
- Skill routing:
  - `incremental-implementation`
  - `test-driven-development`
- Dependencies:
  - Task 1.
- Assumptions:
  - Dependency install is allowed for accepted foundation packages.
- Cannot verify yet:
  - Actual analyzer output; intentionally out of scope.

### Task 3 - Add CI For Foundation Checks

- Status: complete
- User-visible result: repo has CI that runs the same foundation checks expected locally.
- Acceptance criteria:
  - [x] CI workflow lives under `.github/workflows/ci.yml`.
  - [x] CI installs with `pnpm`.
  - [x] CI runs typecheck, tests, and build.
  - [x] Existing nonstandard `workflows/ci.yml`, if present, is migrated or removed only with clear explanation.
- Verification:
  - Automated: inspect workflow syntax and run local commands matching CI.
  - Runtime/manual: N/A until a remote exists.
  - Data/provider proof: N/A.
- Likely touched files:
  - `.github/workflows/ci.yml`
  - `workflows/ci.yml`
- Do not touch:
  - Release/publish workflows.
- Risk level: standard
- Skill routing:
  - `ci-cd-and-automation`
- Dependencies:
  - Task 2.
- Assumptions:
  - GitHub Actions is the intended CI target for public OSS.
- Cannot verify yet:
  - Remote CI run before GitHub remote exists.

### Task 4 - Create First Payment/Webhook Fixture

- Status: not started
- User-visible result: the first demo-quality fixture defines the expected Markdown brief before analyzer behavior exists.
- Acceptance criteria:
  - [ ] Fixture folder contains agent summary, changed files, patch diff, test output, optional notes, and expected `VERIFICATION_BRIEF.md`.
  - [ ] Expected brief shows partially supported duplicate-webhook claim, weak/missing duplicate-event test evidence, payment/webhook/access risk, cannot-verify Stripe production settings, review-first files, and conservative verdict.
  - [ ] Fixture is referenced by tests or documented as the first analyzer target.
- Verification:
  - Automated: fixture files are included in test fixture discovery or a placeholder fixture test.
  - Runtime/manual: read expected brief for usefulness and specificity.
  - Data/provider proof: N/A.
- Likely touched files:
  - `evals/fixtures/payment-webhook-idempotency/agent-summary.md`
  - `evals/fixtures/payment-webhook-idempotency/changed-files.txt`
  - `evals/fixtures/payment-webhook-idempotency/patch.diff`
  - `evals/fixtures/payment-webhook-idempotency/test-output.txt`
  - `evals/fixtures/payment-webhook-idempotency/VERIFICATION_BRIEF.md`
  - `tests/fixtures.test.ts`
- Do not touch:
  - Full analyzer pipeline.
  - Other V0 fixtures in this phase unless explicitly approved.
- Risk level: standard
- Skill routing:
  - `incremental-implementation`
  - `test-driven-development`
- Dependencies:
  - Task 2.
- Assumptions:
  - Payment/webhook remains the strongest first demo scenario.
- Cannot verify yet:
  - Generated report matching the expected brief, because analyzer implementation is deferred.

## Deferred For This Phase

Items intentionally delayed but still plausible later.

- Implement claim extraction.
- Implement diff parsing beyond CLI/file reading skeleton.
- Implement changed-area and risk classification rules.
- Implement claim/evidence matching.
- Implement test-quality assessment.
- Generate `VERIFICATION_BRIEF.md` from the first fixture.
- Add the remaining four V0 fixtures.
- Expose optional JSON output.
- Create/push a GitHub remote and open a PR.

## Checkpoints

### Checkpoint: After Task 1

- [x] `git status --short --branch` works from `patchtrace/`.
- [x] Initial commit contains accepted docs and root project files.
- [x] No package/scaffold work has been mixed into the docs initial commit.

### Checkpoint: After Tasks 2-3

- [x] `pnpm typecheck` passes.
- [x] `pnpm test` passes.
- [x] `pnpm build` passes.
- [x] CI workflow matches the local commands.

### Checkpoint: After Task 4

- [ ] First fixture can be discovered by tests or explicit fixture check.
- [ ] Expected `VERIFICATION_BRIEF.md` is specific, evidence-backed, and conservative.
- [ ] Full analyzer implementation is still deferred.

## Rejected For This Phase

Items explicitly not being built in this phase.

- SaaS/auth/teams/cloud sync.
- GitHub App, OAuth, PR comments, or hosted integration.
- HTML report or dashboard.
- Required LLM calls.
- Correctness scoring.
- Full analyzer implementation.

## Phase Closing Gate

- [ ] Acceptance criteria met and verified locally.
- [ ] `$aga-simplify` run on touched areas, or explicitly not useful.
- [ ] `$aga-review` completed on the phase diff.
- [ ] Relevant docs updated in the same commit/PR.
- [ ] `docs/VERIFY_LOG.md` entry added with commit, checks, runtime proof, cannot-verify, and verdict.
- [ ] `$aga-ship` completed if this phase deploys or launches; N/A for local foundation.
