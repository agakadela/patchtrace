# Agent Workflow

Copy-ready operating workflow for implementation repos.

Assumption: Aga's Codex workflow commands are installed globally and available:
`$aga-spec`, `$aga-plan`, `$aga-build`, `$aga-verify-agent`, `$aga-test`,
`$aga-review`, `$aga-simplify`, `$aga-ship`.

This repo should store project truth in files, not in chat memory.

## 0. Always-On Rules

1. Feedback loops before features: typecheck, lint, tests, CI, and build must exist before real feature work. Add baseline error monitoring early. Use observability while building triggered production paths, not as a post-launch cleanup.
2. Specs are created through conversation. The agent interviews Aga, resolves blocking unknowns, and writes the spec.
3. Work in small vertical slices. One task at a time. `docs/PLAN.md` is the durable memory.
4. Git is a save-point system. Standard tasks end in commits. Larger or riskier changes go through short-lived branches and PRs. High-risk work pauses before commit.
5. `AGENTS.md` stays small and alive. Long-form workflow lives here.
6. Runtime proof beats agent claims. Passing tests, clicked flows, database records, provider dashboards, and triggered telemetry are evidence. `$aga-verify-agent` checks the task contract against agent claims and evidence after build; it does not replace `$aga-test` or `$aga-review`. Verification is proportional: routine browser proof is a targeted check, not full gstack `/qa`, and browser tooling defaults to an isolated or dedicated testing profile.
7. Non-trivial diffs get review before merge after the evidence gate is resolved.
8. High-risk decisions get `doubt-driven-development` before code.
9. Version-sensitive external behavior gets `source-driven-development`: before changing framework, library, provider, browser API, or tooling behavior, detect the installed version, check current official docs, follow the documented pattern, and cite the source in the work summary or PR.

## 1. Meta-Skill Routing

Use `using-agent-skills` at the start of a session or whenever the right workflow is unclear.

Addy Osmani `agent-skills` are the primary workflow system. Auxiliary installed
packs are constrained by this workflow: Matt Pocock is used only through
`grill-with-docs` for repeated terminology/plan confusion, and gstack is only a
focused browser/visual verification helper.

Rules:

- First classify the task: clarify, spec, plan, build, test, debug, review, simplify, ship.
- If the workflow is obvious, use the matching `$aga-*` command and state which underlying skills apply.
- If the workflow is not obvious, invoke `using-agent-skills`, choose the smallest useful skill set, and tell Aga the routing.
- Before non-trivial work, surface assumptions explicitly:

```text
ASSUMPTIONS I'M MAKING:
1. ...
2. ...
3. ...
Correct me now or I proceed.
```

- If requirements, docs, or code conflict, stop and name the conflict. Do not silently choose one interpretation.
- Push back when an approach has a concrete downside. Explain the tradeoff and propose a simpler or safer alternative.
- Keep scope tight. No opportunistic cleanup, unrelated refactors, or deleting code/tests without evidence.
- Verification is mandatory. "Looks right" is not done.

Common routing:

| Situation                                           | Command / Skill                                       | Underlying workflow                                      |
| --------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------- |
| Unclear request                                     | `using-agent-skills` -> `interview-me`                | clarify what Aga actually wants                          |
| New product, feature, or significant change         | `$aga-spec`                                           | `interview-me` + `spec-driven-development`               |
| Spec exists, tasks needed                           | `$aga-plan`                                           | `planning-and-task-breakdown`                            |
| Implement one task                                  | `$aga-build`                                          | `incremental-implementation` + `test-driven-development` |
| UI, forms, states, navigation                       | `$aga-build` + `frontend-ui-engineering`              | production UI, a11y, states                              |
| Endpoint, server action, webhook, shared interface  | `$aga-build` + `api-and-interface-design`             | contract, validation, error semantics                    |
| Version-sensitive framework/library/provider/browser/tooling behavior | `source-driven-development`                           | verify installed version + current official docs         |
| Production endpoint/integration/job/retry/I/O or hard-to-diagnose path | `observability-and-instrumentation`                   | on-call questions, structured telemetry, proof           |
| Auth, payments, tenant data, migrations, AI actions | `security-and-hardening` + `doubt-driven-development` | high-risk override                                       |
| Bug                                                 | `debugging-and-error-recovery`                        | reproduce -> localize -> regression test -> fix          |
| Completed agent work, commit, PR, or final answer   | `$aga-verify-agent`                                   | task contract vs claims/diff/proof + Aga Action          |
| Verification                                        | `$aga-test`                                           | tests + runtime proof + `docs/VERIFY_LOG.md`             |
| Pre-merge review                                    | `$aga-review`                                         | five-axis review + docs/security/perf gates              |
| Simplification                                      | `$aga-simplify`                                       | preserve behavior while reducing complexity              |
| Launch/deploy/handoff                               | `$aga-ship`                                           | release checklist, monitoring, rollback                  |

Verification routing:

- Routine browser proof means a targeted flow/state check. Do not invoke or
  suggest gstack `/qa` for small changes or ordinary task verification.
- Use gstack `/qa` or `/qa-only` only when Aga explicitly asks for QA, testing,
  or a bug report, or for larger release, client handoff, or regression passes.
- If the agent thinks gstack `/qa` is needed but Aga did not ask for it, ask
  first and explain why a targeted check is not enough.
- Browser tooling defaults to an isolated or dedicated Chrome profile. Attaching
  to Aga's everyday logged-in browser is a security exception requiring explicit
  need.
- gstack `/browse` is allowed for focused visual inspection when visual proof is
  needed; keep it scoped to the specific check.
- Do not route normal work through Matt `ask-matt`, `implement`, `to-prd`,
  `to-issues`, `tdd`, `codebase-design`, or `diagnosing-bugs`.

## 2. Files In Every Repo

Always present from day zero:

```text
repo/
  AGENTS.md
  CONTEXT.md
  README.md
  docs/
    AGENT_WORKFLOW.md
    SPEC.md
    PLAN.md
    ARCHITECTURE.md
    VERIFY_LOG.md
    decisions/
      ADR-0001-project-foundation.md
  migrations/
  .github/workflows/ci.yml
```

Canonical sources:

| File                     | Source of truth for                                   |
| ------------------------ | ----------------------------------------------------- |
| `docs/SPEC.md`           | product problem, user, scope, success criteria        |
| `docs/PLAN.md`           | current phase and active tasks                        |
| `docs/ARCHITECTURE.md`   | stack, module convention, data flow, trust boundaries |
| `CONTEXT.md`             | domain language and naming                            |
| `docs/VERIFY_LOG.md`     | verification evidence                                 |
| `docs/decisions/`        | why irreversible decisions were made                  |
| `docs/AGENT_WORKFLOW.md` | how Aga and the agent work together                   |

Do not duplicate truth. Link to the canonical file instead.

`docs/PLAN.md` hygiene:

- Keep only the current phase, active tasks, deferred items, and rejected items for this phase.
- At phase close, move the summary to `docs/VERIFY_LOG.md`.
- Completed task details live in git history and PRs, not forever in `PLAN.md`.

- Tracked, durable verification history.
- Add entries only for meaningful milestones:
  - feature/task verified,
  - phase close,
  - deploy/ship,
  - high-risk work,
  - browser/database/provider proof,
  - explicit cannot-verify decisions.
- Keep entries compact: date, commit, checks, runtime proof, cannot-verify,
  verdict.
- Do not log every exploratory command, file move, grep, local status check, or
  agent scratch note here.

`docs/VERIFY_LOG.local.md`:

- Ignored local scratchpad for noisy verification notes.
- Use for repeated command output, exploratory checks, temporary observations,
  and agent work-in-progress notes.
- Do not rely on it as project truth.

Pull requests as review artifacts:

- A standard small task can end as a commit on the current branch.
- A larger feature, riskier change, or several related commits go through a
  short-lived branch and PR.
- Branch names should use `agent/...`, and PR titles must use `[agent] ...`.
  If a GitHub plugin/skill such as `yeet` defaults to `codex/...` or
  `[codex] ...`, override that naming.
- The PR is not a place to add scope. It should show what changed, how it was
  checked, what could not be verified, which docs changed, and what needs a
  decision before merge.
- PR descriptions include: scope, linked PLAN task/phase, test commands,
  runtime proof, docs updated / not needed, cannot-verify items, and follow-ups.
- Merge is Aga's decision after `$aga-verify-agent`, needed review, runtime or
  provider verification, and understanding the diff. An opened PR is not "done"
  by itself.

## 3. Risk-Triggered Docs

Create these only when the trigger happens:

| File                        | Trigger                                                |
| --------------------------- | ------------------------------------------------------ |
| `docs/AUTH_ACCESS_MODEL.md` | first protected route or first user                    |
| `docs/API_CONTRACTS.md`     | first shared endpoint/server action/webhook/public API |
| `docs/UI_SYSTEM.md`         | second view or reusable UI pattern                     |
| `docs/AI_BOUNDARIES.md`     | first AI call                                          |
| `docs/INTEGRATIONS.md`      | first external provider with callback/webhook          |
| `docs/SYSTEM_MAP.md`        | entering an existing/rescue/client repo                |
| `docs/OPERATIONS.md`        | launch preparation                                     |
| `docs/HANDOFF.md`           | client delivery/handoff                                |

If a feature changes project truth, update the matching doc in the same PR.

## 4. Process A: New Product From Zero

### Phase 0: Framing

Before opening the repo, Aga and the agent clarify:

- What exact pain are we solving?
- For which specific person?
- How is the pain solved today?
- What is the narrowest wedge someone might pay for?
- What are we consciously not building in V1?

If these cannot be answered, do not start implementation.

### Phase 1: Spec And Foundation Decisions

Use `$aga-spec`.

Exit criterion: blocking unknowns are resolved. Remaining unknowns are explicitly marked blocking or non-blocking.

Output:

- `docs/SPEC.md`
- initial `CONTEXT.md`
- ADR candidates
- foundation decisions for `docs/decisions/ADR-0001-project-foundation.md`

Foundation decisions:

- stack, framework, runtime, package manager
- database and migration tool
- hosting/deploy
- auth/session model
- tenancy/workspace model
- data isolation
- payments/entitlements, if relevant
- API/interface style
- conventions: IDs, money, time, soft delete, errors
- AI boundary, if relevant
- module/domain convention
- feedback loops

Use `doubt-driven-development` for decisions that are expensive to reverse.

Module convention rule:

- Default principle: organize code by product/domain ownership, not by technical layer.
- Preferred default for typical web/product apps: `src/features/`.
- Use `src/modules/` or `src/domains/` when the project has stable backend/domain boundaries, models business capabilities more than UI flows, or an existing repo already uses that convention.
- Record the exact convention and reason in `docs/decisions/ADR-0001-project-foundation.md` and `docs/ARCHITECTURE.md`.
- Do not use global `components/`, `hooks/`, `services/`, `types/`, or `utils/` as dumping grounds for application logic. Global shared folders are only for genuinely shared primitives with clear ownership.

### Phase 2: Feedback Loops Before Features

Before real features:

- scaffold app and the chosen feature/domain-first module convention
- migrations configured and first migration committed
- typecheck, lint, test runner work locally
- CI runs typecheck, lint, tests, build
- deploy a hello-world/skeleton through CI
- local/preview/prod environments are separated
- `.env.example` exists; real secrets never enter repo or chat
- error monitoring exists if production-like deploy exists
- observability trigger rule exists for production-facing endpoints,
  integrations, jobs, queues/retries, external I/O, high-risk flows, and
  behavior hard to diagnose from current data
- seed data includes at least two test accounts
- baseline UI approach is chosen
- `AGENTS.md` and this workflow exist in repo

### Phase 3: Walking Skeleton

Build a narrow end-to-end skeleton before features:

```text
auth -> one trivial core action -> database write with isolation
-> protected route shows result -> deploy through CI
```

If paid access is part of the first real promise, include payment skeleton early:

```text
checkout -> webhook -> entitlement -> access
```

Gate: skeleton works in production or production-like environment, with browser proof, database proof, and provider proof where relevant.

## 5. Process B: Phase / Milestone

A phase is a coherent group of work with one visible goal.

Start:

1. Add current phase to `docs/PLAN.md`.
2. Use `$aga-spec` if the phase introduces a new domain.
3. Use `$aga-plan` to create ordered vertical-slice tasks.

Middle:

- Work one task at a time.
- Use Process C for standard features.

Close:

- acceptance criteria verified in runtime
- `$aga-simplify` run on touched areas, or explicitly not useful
- `$aga-review` completed
- relevant docs updated
- `docs/VERIFY_LOG.md` entry added
- `$aga-ship` completed if deploying or launching

## 6. Process C: Standard Feature

Use this for new user-visible behavior, backend flow, or non-trivial change.

```text
1. SPEC
   If clear: write a five-line feature spec in PLAN.md.
   If unclear: use $aga-spec.

2. PLAN
   Use $aga-plan. Tasks must be vertical slices with acceptance criteria.

3. BUILD
   Use $aga-build for one task.
   If the task touches framework, library, provider, browser API, or tooling
   behavior where correctness may depend on installed version or current docs,
   use source-driven-development before coding.
   If the task touches a production endpoint, integration, job, queue/retry,
   external I/O, high-risk flow, or behavior hard to diagnose from current data,
   use observability-and-instrumentation while building: write 2-4 on-call
   questions first, then add only telemetry that answers them.
   Run the smallest relevant test loop while editing.
   Typecheck + relevant tests before commit.
   Full suite + build before PR/merge.
   Use a short-lived branch and PR for larger or riskier changes.
   PR descriptions must include scope, tests, runtime proof, docs, and
   cannot-verify items.
   High-risk work pauses before commit.

4. VERIFY AGENT WORK
   Use $aga-verify-agent after completed agent work, commit, PR, or final answer.
   Compare the task contract, agent claims, diff/PR, tests, runtime evidence,
   docs truth, unsupported claims, scope drift, and cannot-verify items.
   The output must end with Aga Action: merge decision, next action, next exact
   agent instruction if any, proof needed before merge, first human inspection
   area, VERIFY_LOG action, and what not to do next.
   If evidence is missing, run $aga-test or a verification-only task.
   If work is misaligned or drifted, use a targeted fix, split, or revert task.
   This is not code review.

5. REVIEW
   Use $aga-review before merge when the task is aligned and evidence is adequate.
   Check API contracts, access model, UI system, and docs consistency.
   Keep Aga-facing groups as BLOCKER / FIX NOW / FOLLOW-UP. Internally map
   Addy severities as: Critical -> BLOCKER; required no-prefix findings -> FIX
   NOW; Optional/Consider/FYI/Nit -> FOLLOW-UP or omit if noisy. Include Addy's
   structural checks for bolted-on conditionals, repeated condition chains,
   complexity relocation, feature logic leaking into shared modules, weak type
   boundaries, and unhealthy large-file growth.

6. TEST / RUNTIME VERIFY
   Use $aga-test.
   Click the flow if UI exists.
   Treat browser proof as a targeted flow/state check, not full gstack `/qa`.
   Do not invoke or suggest gstack `/qa` unless Aga explicitly asked for QA/testing/bug reporting,
   or this is a larger release/client handoff/regression pass.
   Use an isolated or dedicated browser profile by default.
   Check database/provider proof where relevant.
   If observability was triggered, verify a test event/error/request through
   logs, metrics, traces, or alert path when environment access allows it.
   Add one line to VERIFY_LOG.

7. DOCS
   If project truth changed, update the matching doc in the same PR.
```

## 7. Process D: Small Change

Small changes include copy tweaks, tiny UI fixes, or one loading/error state.

Flow:

```text
task directly -> $aga-build -> Light Mode $aga-verify-agent when Aga needs to
trust or continue from the agent output -> small verification
```

No full spec, no phase plan, no VERIFY_LOG entry unless the change affects runtime truth.
No gstack `/qa`; use the smallest relevant verification and a targeted browser
check if UI is involved.

Small change does not mean no verification. It means small verification.

## 8. Process E: Bug

Use `debugging-and-error-recovery`.

Flow:

```text
reproduce -> localize -> regression test -> minimal fix -> verify -> commit
```

No fix before reproduction.

Production bug:

```text
mitigate or rollback first -> diagnose -> fix -> verify
```

## 9. Process F: Existing / Rescue Repo

First hours are mapping, not refactor.

Flow:

```text
1. SETUP
   Clone, install, try to run locally. Record missing env/access/docs.

2. MAP
   Build docs/SYSTEM_MAP.md:
   flows, routes, APIs, tables, auth, payments, AI calls, jobs,
   providers, tests, deploy, unknowns, do-not-touch areas.

3. BASELINE
   Before changes, record test/build status, runtime behavior,
   console/server errors, and core flow behavior.

4. GUARDRAILS
   Adapt AGENTS.md for this repo.

5. WORK
   Bug -> Process E.
   Feature -> Process C.
   Larger scope -> Process B.

6. BOUNDARIES
   Name what cannot be verified without access.
```

Special rescue rules:

- Missing tests do not mean no safety net. Add characterization tests around touched areas.
- Dead code requires evidence.
- Refactor needs its own task and scope.
- Never put client secrets in chat, commits, docs, or screenshots.

## 10. High-Risk Override

High-risk areas:

- Auth/AuthZ/RLS
- payments/entitlements
- tenant/workspace data
- migrations/backfills
- secrets/env
- production config
- AI actions/costs
- provider callbacks/webhooks

Additional requirements:

- Run `doubt-driven-development` before code.
- Pause before commit and show the diff.
- Source diff alone is not enough for `VERIFIED` in `$aga-verify-agent`.
  Missing high-risk proof means HOLD or DO NOT MERGE until the exact proof is
  collected.
- Migrations require rollback/backfill plan before execution.
- Production migrations require fresh backup/PITR confirmation.
- Auth/data isolation requires manual two-user test.
- Payments require provider dashboard proof and database proof.
- AI endpoints require cost cap, retry cap, logging, and failure path proof.
- High-risk production paths automatically trigger observability: the PR names
  on-call questions and proves or names cannot-verify for telemetry.
- Cannot-verify items must be named in `docs/VERIFY_LOG.md`.

## 11. Required Command Outputs

```text
$aga-spec
  -> docs/SPEC.md updated OR five-line feature spec in PLAN.md
  -> open questions listed
  -> ADR candidates listed

$aga-plan
  -> vertical-slice tasks in PLAN.md
  -> each task has acceptance criteria, verification method,
     likely touched files, and do-not-touch list

$aga-build
  -> small diff for one task
  -> checks run
  -> changed files summarized
  -> commit for standard task; branch + PR for larger/riskier work
  -> PR description includes scope, tests, runtime proof, docs, cannot-verify
  -> on-call questions and telemetry proof/not-needed note when observability
     is triggered
  -> pause before commit for high-risk

$aga-verify-agent
  -> factual verification verdict
  -> claim-vs-evidence matrix
  -> scope drift
  -> cannot-verify
  -> human inspection first
  -> Aga Action with merge decision, next action, agent instruction,
     proof needed, VERIFY_LOG action, and what not to do next

$aga-test
  -> command results
  -> proportional runtime/manual proof
  -> cannot-verify items named
  -> VERIFY_LOG entry

$aga-review
  -> findings grouped BLOCKER / FIX NOW / FOLLOW-UP
  -> Critical maps to BLOCKER; required no-prefix findings map to FIX NOW;
     Optional/Consider/FYI/Nit map to FOLLOW-UP or are omitted if noisy
  -> file:line references when possible
  -> no unrelated refactor

$aga-simplify
  -> simpler code with identical behavior
  -> or explicit note that no worthwhile simplification exists

$aga-ship
  -> env/webhook/monitoring/observability/rollback checklist
  -> GO/NO-GO decision
  -> VERIFY_LOG entry
  -> handoff notes for client work
```

## 12. Aga vs Agent

| Stage             | Aga                             | Agent                                           |
| ----------------- | ------------------------------- | ----------------------------------------------- |
| Framing           | thinks and decides              | asks questions, captures                        |
| Spec              | answers, resolves decisions     | interviews, writes spec, challenges assumptions |
| Plan              | accepts or cuts scope           | creates vertical slices                         |
| Build             | reads diffs                     | implements and tests                            |
| Verify agent work | chooses Aga Action              | checks task contract vs claims/diff/proof       |
| Review            | decides fix-now/later           | finds issues                                    |
| Runtime verify    | clicks flows, checks dashboards | runs tests and records evidence                 |
| Merge/ship        | final decision                  | checklist, rollback, notes                      |

One main agent by default. Session per feature or per task. Use `docs/PLAN.md` and git history as memory, not conversation history.

## 13. Anti-Rationalizations

- "Small change, no verification needed" -> small change means small verification.
- "The app runs, so the flow works" -> the flow works after it is clicked.
- "The UI hides it, so auth is done" -> UI hiding is not authorization.
- "Checkout redirected successfully" -> payment state lives in webhook/provider/database proof.
- "The model said it is fixed" -> agent claims are not evidence.
- "I will clean this up while I am here" -> cleanup needs its own task.
- "Current docs probably did not change" -> source-check version-sensitive framework, library, provider, browser API, and tooling behavior.
- "This test is annoying" -> tests protect behavior until proven obsolete.

## 14. When To Extend This Workflow

Extend only after two real misses.

| Signal appears twice                        | Patch                                                |
| ------------------------------------------- | ---------------------------------------------------- |
| Agent mixes domain terms despite CONTEXT.md | add stronger terminology checks or `grill-with-docs` |
| Product direction feels wrong               | use Addy `idea-refine` / `doubt-driven-development` before spec |
| UI looks generic or sloppy                  | use Addy `frontend-ui-engineering` plus focused browser/visual proof |
| Payment/auth diff feels risky               | second-model cross-review before merge               |
| Build loop is boring and reliable           | consider broader automation or second worktree       |
