# ADR-0001: Project Foundation

- Date: 2026-06-15
- Status: accepted
- Owner: project maintainer(s)

## Context

PatchTrace is a local-first open-source devtool for verifying AI-agent code changes before a developer accepts a patch. The V0 product is a CLI that turns local patch material, agent claims, and test/command evidence into a conservative Markdown verification brief.

The foundation decisions optimize for:
- a small useful local workflow;
- evidence-backed reports;
- fixture-first development;
- conservative trust boundaries;
- public OSS maintainability.

## Decision Summary

| Area | Decision | Why | Revisit When |
|---|---|---|---|
| Stack | Node.js + TypeScript CLI | Fits local devtool workflow and typed report/domain model. | A non-Node ecosystem becomes the primary user base. |
| Package manager | `pnpm` | Accepted project default for small TypeScript tooling. | Dependency management becomes painful or contributors require another manager. |
| Test runner | Vitest | Fast TypeScript-friendly unit and fixture tests. | Test suite needs capabilities Vitest does not support. |
| Schema validation | Zod | Validate structured inputs and generated report objects. | Runtime validation becomes unnecessary or a better local standard emerges. |
| Database | N/A | V0 has no persisted app state. | A local history, cache, or hosted service is introduced. |
| Migrations | N/A | No database in V0. | A database is introduced. |
| Hosting/deploy | N/A for V0 | V0 is local CLI only. | Publishing/release/distribution is planned. |
| Auth/session | N/A | No users, teams, or accounts in V0. | Hosted service, team workspace, or protected surface is introduced. |
| Tenancy/workspace | N/A | No user accounts or multi-tenant data in V0. | Team/hosted features are introduced. |
| Data isolation | Local-first, no external calls by default | Diffs and code can be sensitive. | Any external provider or cloud feature is proposed. |
| Payments/entitlements | N/A | No billing in V0. | Paid distribution or hosted service is planned. |
| API style | CLI command interface | Primary interface is local `patchtrace analyze`. | Public library API or service API is introduced. |
| UI foundation | N/A | HTML/UI is out of scope for V0. | Local report UI becomes useful after CLI is dogfooded. |
| Module/domain convention | `src/modules/` | PatchTrace is a domain engine with stable product concepts. | Code naturally becomes UI-feature-first or package boundaries demand another shape. |
| AI boundary | No required AI/LLM in V0 | Rules-first engine keeps output inspectable, private, and cheap. | Opt-in extraction/summarization is explicitly approved. |
| Monitoring | N/A for V0 | Local CLI uses stdout/stderr and tests. | A hosted surface or package telemetry is proposed. |

## Decisions

### Stack

- Framework: N/A; local CLI.
- Language: TypeScript.
- Package manager: `pnpm`.
- Runtime: Node.js.
- Test runner: Vitest.
- Schema validation: Zod.
- Reasoning: TypeScript gives a strong, readable domain model for claims, evidence, risks, test-quality assessment, and verification briefs without requiring a web framework or hosted app.

### Database And Migrations

- Database: N/A for V0.
- Migration tool: N/A for V0.
- Rule: if a database is introduced later, schema changes must happen only through repo migrations.
- Local/preview/prod separation: N/A until a database or hosted service exists.
- Backup/PITR expectation before production migrations: N/A until production data exists.

### Auth And Sessions

- Identity provider: N/A for V0.
- Session model: N/A for V0.
- Server-side auth enforcement point: N/A for V0.
- UI role: N/A because V0 has no UI.

### Tenancy And Data Isolation

- Tenant/workspace model: N/A for V0.
- `workspace_id` from first table: N/A because V0 has no database tables.
- DB-level isolation/RLS or equivalent: N/A for V0.
- Two-user test expectation: N/A for V0; required if hosted/team/user data exists later.

### Entitlements And Payments

- Payment provider: N/A for V0.
- Paid access source of truth: N/A for V0.
- Event idempotency table: N/A for V0.
- Dashboard + DB verification required: N/A for V0.

### API/Interface Style

- Primary style: CLI commands.
- First public command target: `patchtrace analyze`.
- Validation boundary: CLI argument parsing and Zod validation for structured report/input objects.
- Error taxonomy:
  - validation: invalid flags, missing required local material, unreadable files;
  - unauthenticated: N/A;
  - unauthorized: N/A;
  - not found: missing path, missing base ref, missing diff file;
  - conflict: incompatible CLI options;
  - provider failure: N/A in V0 because no provider calls;
  - analyzer failure: unexpected parse or report generation error.
- Idempotency policy: running the same command with the same local inputs should produce stable report content except timestamps if included.

### Conventions

- IDs: stable string IDs for claims, evidence, risks, and review targets where needed.
- Money: N/A for PatchTrace product state; payment-risk fixtures may mention money only as analyzed code context.
- Time/timezones: use ISO 8601 when report timestamps are needed.
- Soft delete: N/A for V0.
- Logging: CLI stdout/stderr; no telemetry by default.
- Error handling: no silent catch blocks; errors should be explicit and actionable.
- Privacy: no external network calls or LLM submission by default.

### AI Boundary

- AI role: N/A in V0.
- Human checkpoint required before: adding any LLM call, model dependency, external provider, or network submission of code/diffs/summaries.
- Cost/retry caps: N/A in V0; required if AI calls are added later.
- Logging/failure path: N/A in V0; required if AI calls are added later.
- Future rule: if an LLM is introduced, it may extract or summarize explicit material only; it must not be treated as truth or as a correctness oracle.

### Module/Domain Convention

- Default principle: organize code by product/domain ownership, not by technical layer.
- Chosen convention: `modules`.
- Exact root path: `src/modules`.
- Reason: PatchTrace is a domain engine/devtool, not a screen-based application. Its stable boundaries are concepts like claims, evidence, patch material, risk, test quality, reports, and verdicts.
- Why not `features`: V0 has no UI flows or user-facing feature screens, so `features` would imply a UI/product-app shape.
- Why not global `core/rules/schemas`: those become technical-layer dumping grounds and hide ownership of product judgment.
- Shared code policy: only genuinely generic primitives may live outside modules, and they should remain small.
- Dependency boundaries: `src/cli` calls modules; modules should expose small typed APIs and avoid reaching into CLI concerns.

### Feedback Loops

- Typecheck: `pnpm typecheck` after scaffold.
- Lint: `pnpm lint` after scaffold.
- Test runner: `pnpm test` after scaffold.
- Build: `pnpm build` after scaffold.
- CI: typecheck, lint, tests, build, and fixture checks before release/PR merge after scaffold.
- Error monitoring: N/A for V0.
- Seed data / two test accounts: N/A for V0.

## Alternatives Considered

| Alternative | Why Not Chosen | Cost Of Switching Later |
|---|---|---|
| Web app first | Adds auth/hosting/UI before local workflow proves value. | Medium; web app can wrap the CLI engine later. |
| SaaS or GitHub App first | Creates privacy, auth, integration, and trust complexity too early. | High; platform assumptions would shape the product prematurely. |
| LLM-first analyzer | Risks generic output, privacy concerns, cost, and hidden judgment. | Medium; optional LLM extraction can be added later behind validated schemas. |
| `src/features/` convention | Better for UI/product apps than a local domain engine. | Low to medium if a future UI becomes primary. |
| Global `core/rules/schemas` layout | Encourages technical-layer ownership instead of product/domain ownership. | Medium; refactor cost grows as rules and schemas multiply. |
| JSON-first output | Pulls V0 toward API/platform design before report quality is proven. | Low; JSON can still support fixtures or future integrations. |

## Consequences

### Positive

- Keeps V0 small, local, and dogfoodable.
- Makes report quality testable through fixtures.
- Protects sensitive code and diffs by default.
- Avoids false confidence from LLM or correctness-score framing.
- Keeps future GitHub, HTML, package, or AI integrations possible without committing to them early.

### Negative / Trade-Offs

- The first version may feel less magical than an AI reviewer.
- Early analysis will be intentionally shallow and rules-based.
- Markdown-first output may delay API/integration use cases.
- Contributors may expect GitHub integration or LLM analysis because of the AI-agent context; docs must keep scope clear.

### Operational Requirements Created By This ADR

- Create fixtures before broad analyzer behavior.
- Keep all report claims evidence-backed.
- Require explicit approval before adding external services or LLM calls.
- Run typecheck, lint, tests, build, and fixture checks once the scaffold exists.

## Follow-Up Docs Triggered

- [ ] `docs/AUTH_ACCESS_MODEL.md` after first protected route/user.
- [ ] `docs/API_CONTRACTS.md` after first shared endpoint/action/webhook/public API.
- [ ] `docs/UI_SYSTEM.md` after second view.
- [ ] `docs/AI_BOUNDARIES.md` after first AI call.
- [ ] `docs/INTEGRATIONS.md` after first provider webhook/callback.

Current V0 triggers none of the above risk docs.

## Revisit Triggers

- The CLI is dogfooded on 3-5 real agent sessions and report quality demands a different architecture.
- Optional JSON becomes a public interface.
- GitHub/PR integration becomes part of the next accepted phase.
- LLM extraction is proposed.
- A local HTML report becomes necessary for comprehension.
- Package publishing or release automation begins.
