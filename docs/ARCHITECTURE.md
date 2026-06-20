# ARCHITECTURE.md

System source of truth: stack, module convention, data flow, and trust boundaries.

Template rules:
- Keep this short and current.
- Do not duplicate product scope from `docs/SPEC.md`.
- Do not duplicate detailed auth/API/UI/AI/integration contracts; link to risk-triggered docs when they exist.
- If unknown, write `UNKNOWN`. If not applicable, write `N/A` and why.

## Status

- Last reviewed: 2026-06-15
- Reviewed by: project maintainer
- Related ADRs: `docs/decisions/ADR-0001-project-foundation.md`

## Stack

| Layer | Decision | Source / ADR | Notes |
|---|---|---|---|
| App framework | N/A | `ADR-0001` | V0 is a local CLI, not a web app. |
| Language | TypeScript | `ADR-0001` | Strong typed domain model for claims, evidence, risks, and reports. |
| Runtime | Node.js | `ADR-0001` | Local developer-machine CLI. |
| Package manager | `pnpm` | `ADR-0001` | Accepted foundation choice. |
| Test runner | Vitest | `ADR-0001` | Unit and fixture tests. |
| Schema validation | Zod | `ADR-0001` | Validate structured inputs and report objects. |
| Database | N/A | `ADR-0001` | V0 has no persisted app database. |
| Migrations | N/A | `ADR-0001` | No schema migrations in V0. |
| Auth | N/A | `ADR-0001` | V0 has no users, sessions, teams, or accounts. |
| Payments | N/A | `ADR-0001` | V0 has no billing or entitlements. |
| AI provider | N/A for V0 | `ADR-0001` | CLI must be useful without LLM calls. Future LLM use must be opt-in and evidence-constrained. |
| Hosting/deploy | N/A for V0 | `ADR-0001` | Local CLI only; package publishing is a later decision. |
| Monitoring | N/A for V0 | `ADR-0001` | Use test logs and CLI errors locally. |

## Module Convention

Default principle: organize code by product/domain ownership, not by technical layer.

- Chosen convention: `modules`
- Exact root path: `src/modules`
- Reason: PatchTrace is a domain engine/devtool with stable product concepts: claims, evidence, patch material, risk, test quality, reports, and verdicts.
- Existing repo convention, if any: Phase 3 now has a thin `src/cli/` entrypoint plus first analyzer modules under `src/modules/patch`, `src/modules/evidence`, and `src/modules/report`.

Global technical folders policy:

- `src/cli/` is allowed as a thin command entrypoint.
- `tests/` and `evals/fixtures/` are allowed as verification roots.
- Application logic belongs in product/domain modules under `src/modules/`.
- Avoid global `core/`, `rules/`, `schemas/`, `services/`, `types/`, or `utils/` dumping grounds for PatchTrace logic.

Current implementation structure:

```text
src/
  cli/
    index.ts
    io.ts
    commands/
      analyze.ts
  modules/
    claims/
      claim-analysis.ts
    evidence/
      local-materials.ts
    patch/
      changed-files.ts
    report/
      brief-shell.ts
    risk/
      risk-analysis.ts
    test-quality/
      test-quality-analysis.ts
    verdict/
      verdict-selection.ts
evals/
  fixtures/
tests/
docs/
```

Target analyzer module structure as later Phase 3 behavior lands:

```text
src/
  cli/
    index.ts
    io.ts
    commands/
      analyze.ts
  modules/
    claims/
    evidence/
    patch/
    risk/
    test-quality/
    report/
    verdict/
evals/
  fixtures/
tests/
docs/
```

## Data Flow

```text
developer runs CLI
  -> CLI reads local inputs and flags
  -> patch module collects or parses changed files and diff hunks
  -> claims module extracts explicit agent claims
  -> evidence module normalizes patch, test, command, note, and summary evidence
  -> risk module classifies changed areas and risk areas
  -> test-quality module assesses provided test evidence
  -> verdict module chooses a conservative verdict
  -> report module writes VERIFICATION_BRIEF.md
```

Notes:

- The agent summary is never treated as truth.
- The analyzer should preserve evidence source references wherever practical.
- Missing local/provided material should produce explicit gaps, not confident guesses.

## Trust Boundaries

| Boundary | Validation | Auth/AuthZ Enforcement | Logging | Failure Behavior |
|---|---|---|---|---|
| CLI flags -> analyzer | Validate required combinations, file existence, and supported options. | N/A | CLI error output. | Exit non-zero with actionable message. |
| Local filesystem -> patch material | Read only user-provided paths or git material from the target repo. | N/A | Record material source in report where useful. | Mark material missing or insufficient instead of inventing evidence. |
| Agent summary -> claims | Extract explicit claims only; do not infer unstated claims. | N/A | Include claim source. | If no claims are found, report insufficient or limited claim material. |
| Test output -> test evidence | Parse conservatively; distinguish pass/fail from behavior proof. | N/A | Include command/test evidence when provided. | Mark test evidence missing, weak, or contradictory. |
| Analyzer -> report | Validate report object before export. | N/A | Surface generation errors. | Do not write misleading partial reports silently. |
| CLI -> external services | N/A in V0. | N/A | N/A | No external calls by default. |

## Server-Side Enforcement Points

- Auth/session checked at: N/A because V0 has no auth.
- Authorization checked at: N/A because V0 has no users or accounts.
- Tenant/workspace isolation checked at: N/A because V0 has no tenant model.
- DB-level isolation/RLS: N/A because V0 has no database.
- Entitlements checked at: N/A because V0 has no payments.

## Data Model Overview

Do not maintain full schemas here. Keep canonical schema definitions in code once implementation exists.

| Concept | Storage | Owner Module | Notes |
|---|---|---|---|
| PatchTrace input | In-memory object built from CLI/local files | `src/modules/patch` and `src/modules/evidence` | Includes session goal, agent summary, changed files, diff hunks, test output, command output, manual notes. |
| Agent claim | In-memory/report object | `src/modules/claims` | Explicit claim extracted from agent summary or manual note. |
| Evidence | In-memory/report object | `src/modules/evidence` | Source-backed material: changed file, diff hunk, test file, output, note, or command output. |
| Risk area | In-memory/report object | `src/modules/risk` | Conservative risk classification tied to evidence. |
| Test-quality assessment | In-memory/report object | `src/modules/test-quality` | Describes what tests appear to prove and not prove. |
| Verification brief | Markdown file | `src/modules/report` | Main V0 product artifact: `VERIFICATION_BRIEF.md`. |

## External Systems

| System | Purpose | Source Doc | Failure Path |
|---|---|---|---|
| N/A | V0 has no required external services. | N/A | N/A |

Future optional integrations such as LLM extraction, GitHub PR integration, package publishing, or hosted services require explicit approval and matching risk-triggered docs.

## Environments

| Environment | URL | Database/Provider Project | Notes |
|---|---|---|---|
| local | N/A | N/A | V0 runs as a local CLI. |
| preview/staging | N/A | N/A | N/A until a hosted surface exists. |
| production | N/A | N/A | N/A until package release or hosted service is planned. |

## Observability

- Error monitoring: N/A for V0 local CLI.
- Logs: CLI stdout/stderr and test output.
- Alerts: N/A.
- Dashboards: N/A.

## Known Constraints

- V0 must be useful without an LLM.
- Markdown report quality is the product bar.
- JSON is secondary/internal unless separately approved.
- The report must not claim correctness, safety, guarantees, or production verification without evidence.
- Fixture expectations should precede analyzer behavior.

## Change Log

| Date | Change | Reason | Commit/PR |
|---|---|---|---|
| 2026-06-15 | Initial accepted architecture | Project foundation | N/A |
| 2026-06-16 | Recorded Phase 2 CLI scaffold, fixture, lint gate, and pinned CI actions | Keep project truth aligned after review fixes | `agent/fix-phase-2-review-gates` |
| 2026-06-18 | Recorded Phase 3 saved-material brief shell under `src/modules/patch`, `src/modules/evidence`, and `src/modules/report` | Analyzer module work has begun with local CLI proof | `agent/task-2-brief-shell` |
| 2026-06-18 | Recorded Phase 3 payment fixture risk and review-first analyzer under `src/modules/risk` | First deterministic risk slice now derives report guidance from changed paths and diff text | `agent/task-3-payment-risk-review-first` |
| 2026-06-18 | Recorded Phase 3 payment fixture claim-support and test-quality analyzers under `src/modules/claims` and `src/modules/test-quality` | Generated briefs now assess explicit agent summary claims and passing-test limits conservatively | `agent/task-4-claims-test-quality` |
| 2026-06-19 | Recorded Phase 3 payment fixture verdict selection under `src/modules/verdict` | Generated briefs now include cannot-verify gaps, suggested next checks, and conservative verdict rationale | `agent/task-5-payment-verdict-gaps` |
| 2026-06-19 | Recorded Phase 3 insufficient-material verdict path under `src/modules/evidence` and `src/modules/verdict` | Summary-only or incomplete saved material now produces an explicit `insufficient_material` brief instead of pretending analysis happened | `agent/task-6-insufficient-material` |
