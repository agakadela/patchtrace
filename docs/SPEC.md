# Spec: PatchTrace

Product source of truth: problem, user, scope, flows, and success criteria.

Template rules:
- This file is produced from `/spec` / `$aga-spec` interview, not from silent guessing.
- Do not duplicate architecture, auth, API contracts, UI system, AI boundaries, or integrations here. Link to their source docs once they exist.
- If unknown, write `UNKNOWN`. If not applicable, write `N/A` and why.
- Blocking unknowns must be resolved before planning implementation.

## Status

- Product name: PatchTrace
- Spec status: accepted
- Owner: project maintainer(s)
- Last updated: 2026-06-20
- Current implementation phase: see `docs/PLAN.md`

## Objective

PatchTrace is a local-first open-source devtool that helps developers verify AI-agent code changes before accepting a patch.

It compares the requested task, agent claims, actual patch material, and available test or command evidence. It then produces a conservative verification brief that helps a human reviewer start in the right place, notice unsupported claims, and avoid trusting the agent summary as truth.

PatchTrace is not a generic AI code reviewer and does not claim to prove code correctness.

## Problem

AI coding agents can produce patches faster than developers can comfortably verify them. After an agent session, the developer often has a changed working tree, a diff, an agent summary, terminal output, test output, and uncertainty about what was actually verified.

The pain PatchTrace solves is the review bottleneck between:

```text
AI agent says "done"
```

and:

```text
developer accepts the patch
```

## Target User

The primary user is a developer reviewing AI-agent code changes before accepting a patch.

Likely early adopters:
- solo developers using Codex, Cursor, Claude Code, GitHub Copilot coding agent, or similar tools;
- AI-assisted freelancers;
- small engineering teams experimenting with agent-created branches or pull requests;
- open-source maintainers who want a local evidence brief before reviewing generated changes.

## Current Workaround / Status Quo

Developers currently verify agent work by manually reading the diff, skimming the agent summary, re-running commands, inspecting test output, and writing their own review notes. This is slow, easy to do inconsistently, and vulnerable to trusting fluent agent summaries that are not backed by evidence.

## Smallest Adoption Wedge

The smallest serious adoption wedge is a local CLI that generates a useful `VERIFICATION_BRIEF.md` in under 5 minutes from local patch material and pasted agent/test notes.

The brief must be useful before the developer reads the full diff cold.

## V0 Scope

V0 is the Local Patch Verification Engine.

V0 will:
- run as a local Node/TypeScript CLI;
- accept local git diff or saved diff material;
- accept changed file lists, agent summary/session notes, test output, and optional manual notes;
- extract or accept explicit agent claims;
- identify changed areas from paths, filenames, and diff content;
- classify risk areas with deterministic rules;
- compare claims against patch evidence and test/command evidence;
- assess whether test evidence appears strong, weak, missing, contradictory, or not applicable;
- identify cannot-verify items when proof requires external dashboards, deployed environments, secrets, provider state, live logs, or manual runtime checks not provided;
- rank review-first files with file-specific reasons;
- generate a Markdown `VERIFICATION_BRIEF.md`;
- support fixture-first development with hand-written expected briefs before analyzer behavior is implemented.

JSON output may exist as an internal or optional fixture artifact, but Markdown is the V0 product output.

## Explicitly Out of Scope

V0 will not build:
- SaaS;
- login, auth, teams, workspaces, or cloud sync;
- billing or paid access;
- GitHub App, GitHub OAuth, PR comments, or hosted PR integration;
- local HTML report or dashboard;
- public proof pages, social posts, PNG cards, or video replay;
- full Codex/Cursor/Claude/GitHub Copilot session-log parsing;
- required LLM analysis;
- automatic correctness scoring;
- claims that code is safe, correct, guaranteed, or production verified;
- sending private code, diffs, summaries, or test output to external services by default.

## Tech Stack

See `docs/ARCHITECTURE.md` and `docs/decisions/ADR-0001-project-foundation.md` for foundation decisions.

Accepted product-level constraints:
- Runtime: local CLI.
- Language: TypeScript.
- Package manager: `pnpm`.
- Test runner: Vitest.
- Schema validation: Zod.
- Analyzer style: deterministic/rules-first.
- Module convention: `src/modules/` with a thin CLI entrypoint.
- Database, auth, hosting, and required AI provider: N/A for V0.

## Commands

These are the current local development commands plus the analyzer command shape.

```bash
# install dependencies
pnpm install

# run typecheck
pnpm typecheck

# run lint
pnpm lint

# run tests and fixture checks
pnpm test

# build the CLI
pnpm build

# analyze local patch material
patchtrace analyze --diff patch.diff --changed-files changed-files.txt --summary agent-summary.md --test-output test-output.txt --out VERIFICATION_BRIEF.md

# analyze a saved diff
patchtrace analyze --diff patch.diff --changed-files changed-files.txt --summary agent-summary.md --out VERIFICATION_BRIEF.md
```

The current walking skeleton supports install, typecheck, lint, tests, build, `analyze --help`, and `analyze` for saved local material. The payment/webhook fixture generates evidence-linked risk, review-first, claim-support, test-quality, cannot-verify, suggested-next-check, and conservative-verdict sections. Missing or partial saved patch material produces an explicit `insufficient_material` brief. Generated-output parity for the non-payment fixture families remains deferred until after Phase 3.

## Project Structure

The product structure belongs in `docs/ARCHITECTURE.md`. The accepted foundation direction is:

```text
src/
  cli/
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

The implementation should be organized by PatchTrace product/domain concepts, not by global technical dumping grounds such as `core/`, `rules/`, `schemas/`, or `utils/` for application logic.

## Code Style

The implementation should favor explicit, typed, evidence-preserving data transformations.

Example style target:

```ts
export type ClaimSupport =
  | "supported"
  | "partially_supported"
  | "unsupported"
  | "contradicted"
  | "cannot_determine";

export function assessClaimSupport(input: ClaimAssessmentInput): ClaimAssessment {
  const supportingEvidence = findSupportingEvidence(input.claim, input.evidence);
  const contradictions = findContradictions(input.claim, input.evidence);

  return {
    claimId: input.claim.id,
    support: chooseConservativeSupport({
      supportingEvidence,
      contradictions,
      missingEvidence: input.missingEvidence,
    }),
    supportingEvidence,
    contradictions,
    missingEvidence: input.missingEvidence,
    notes: [],
  };
}
```

Style rules:
- Prefer small pure functions for analysis rules.
- Preserve evidence source references wherever possible.
- Do not hide product judgment inside one prompt or one opaque function.
- Do not infer claims that are not stated.
- Use conservative language when evidence is incomplete.
- Validate structured inputs and generated report objects with schemas.

## Testing Strategy

V0 is fixture-first.

Before implementing broad analyzer behavior, create hand-written expected `VERIFICATION_BRIEF.md` outputs for five fixtures:
- payment/webhook/idempotency change;
- auth/session/ownership change;
- agent claims tests were added but evidence is weak or missing;
- test output fails while the agent says the work is done;
- AI endpoint added without usage or rate-limit evidence.

Test levels:
- unit tests for claim extraction, evidence matching, risk classification, test-quality assessment, cannot-verify generation, review-first ranking, and verdict selection;
- fixture tests comparing generated output against expected report sections;
- CLI smoke tests proving `patchtrace analyze` can read local inputs and write `VERIFICATION_BRIEF.md`;
- regression tests for weak-test patterns and contradicted claim handling.

The tests do not need to prove code correctness. They need to prove PatchTrace stays conservative, evidence-backed, and useful.

## Boundaries

Always:
- keep V0 local-first;
- tie warnings, verdicts, and next steps to provided evidence or missing evidence;
- use conservative verdict language;
- put fixture expectations before analyzer behavior;
- test rules and report output;
- include cannot-verify items when proof requires unavailable runtime, provider, dashboard, secret, deployed environment, or live data access;
- keep the CLI usable without an LLM.

Ask first:
- adding LLM calls;
- adding new runtime dependencies beyond the agreed foundation;
- adding GitHub/PR integration;
- adding an HTML UI or dashboard;
- publishing an npm package or release;
- changing the verdict taxonomy;
- changing the claim-support taxonomy;
- changing the module convention;
- adding any external service or network call.

Never in V0:
- SaaS;
- auth or team accounts;
- cloud sync;
- correctness scoring;
- claims that PatchTrace proves safety or correctness;
- sending private code or diffs to external services by default;
- generic checklist output that is not tied to changed files, evidence, or missing evidence.

## Core Flows

### Flow 1: Generate a verification brief from local patch material

- Actor: developer reviewing AI-agent code changes.
- Trigger: an AI coding agent says the work is done or a generated patch is ready for review.
- Steps:
  1. Developer runs `patchtrace analyze` with a base branch or saved diff.
  2. Developer provides an agent summary, test output, and optional manual notes.
  3. PatchTrace collects or reads changed files and diff hunks.
  4. PatchTrace extracts explicit agent claims.
  5. PatchTrace compares claims to patch, test, command, and note evidence.
  6. PatchTrace classifies changed areas and risk areas.
  7. PatchTrace assesses test evidence strength.
  8. PatchTrace generates `VERIFICATION_BRIEF.md`.
- Successful outcome: the developer has a source-backed brief with claim/evidence matrix, risk areas, test-quality review, checks run/missing, review-first files, cannot-verify items, suggested next steps, and a conservative verdict.
- Failure/empty states:
  - no diff or changed-file material: verdict should be `insufficient_material`;
  - no test output: report should mark test evidence as missing, not assume tests passed;
  - failing test output contradicts an agent "done" claim: report should surface the contradiction and recommend sending the agent back;
  - unsupported claims: report should label them as unsupported or cannot determine.
- Runtime proof required: fixture CLI run writes a Markdown brief with expected sections.

### Flow 2: Review the generated brief before accepting a patch

- Actor: developer reviewing the patch.
- Trigger: `VERIFICATION_BRIEF.md` exists for the agent session.
- Steps:
  1. Developer reads the verdict and claim/evidence matrix.
  2. Developer reviews the review-first file list.
  3. Developer checks weak or missing test evidence.
  4. Developer decides whether to review manually, run more checks, or send the agent back.
- Successful outcome: the developer starts review from the right files and questions instead of trusting the agent summary.
- Failure/empty states:
  - output is generic checklist noise: fails product bar;
  - report implies correctness without proof: fails product bar;
  - next steps are not actionable or evidence-linked: fails product bar.
- Runtime proof required: generated fixture reports include file-specific review-first guidance and evidence-linked next steps.

### Flow 3: Maintain fixture-first quality

- Actor: PatchTrace maintainer/contributor.
- Trigger: adding or changing analyzer behavior.
- Steps:
  1. Add or update fixture input files.
  2. Hand-write the expected `VERIFICATION_BRIEF.md` shape.
  3. Implement or adjust analyzer behavior.
  4. Run fixture tests.
- Successful outcome: analyzer changes improve or preserve expected brief quality.
- Failure/empty states:
  - analyzer output becomes vague;
  - warnings are not tied to evidence;
  - verdicts become overconfident;
  - fixture expectations are missing for new behavior.
- Runtime proof required: fixture tests pass.

## Success Criteria

| Criterion | How measured | Target | Owner |
|---|---|---|---|
| Useful local brief | Run CLI against fixture material | `VERIFICATION_BRIEF.md` generated from local inputs | Maintainer |
| Fast enough to adopt | Dogfood or fixture run timing including input prep | Useful brief in under 5 minutes | Maintainer |
| Claim skepticism | Fixture expectations and tests | Unsupported, partially supported, contradicted, and cannot-determine claims are labeled conservatively | Maintainer |
| Test-quality awareness | Fixture expectations and unit tests | Weak/missing/contradictory test evidence is visible and actionable | Maintainer |
| Risk awareness | Fixture expectations and unit tests | High-risk changed areas produce file-specific review-first guidance | Maintainer |
| Cannot-verify discipline | Fixture expectations and report review | External/runtime/provider proof gaps are explicit | Maintainer |
| No false confidence | Copy review and tests for verdict language | No "correct", "safe", "guaranteed", or "production verified" claims without evidence | Maintainer |
| Fixture-first foundation | Repository contents before broad analyzer behavior | Five initial fixtures have hand-written expected briefs | Maintainer |

## Product Constraints

- Legal/compliance constraints: N/A for V0; PatchTrace is a local OSS devtool and does not provide legal, security, or production-safety guarantees.
- Data/privacy constraints: local-first; no external service calls by default; do not ask for `.env`, secrets, customer data, provider tokens, or private dashboard exports.
- Performance expectations: the full workflow should be faster than writing equivalent manual review notes; target under 5 minutes for a useful brief.
- Accessibility expectations: CLI output and Markdown reports should be readable, structured, and usable without a graphical interface. HTML UI is out of scope for V0.
- Budget/cost constraints: no required paid API or LLM cost in V0.

## Source-of-Truth Links

| Area | Source |
|---|---|
| Architecture | `docs/ARCHITECTURE.md` |
| Foundation decisions | `docs/decisions/ADR-0001-project-foundation.md` |
| Access model | `docs/AUTH_ACCESS_MODEL.md` once triggered |
| API contracts | `docs/API_CONTRACTS.md` once triggered |
| UI conventions | `docs/UI_SYSTEM.md` once triggered |
| AI boundaries | `docs/AI_BOUNDARIES.md` once triggered |
| Integrations | `docs/INTEGRATIONS.md` once triggered |
| Operations | `docs/OPERATIONS.md` once launch prep begins |

## ADR Candidates

Decisions that may need ADRs because they are hard to reverse, affect public interfaces, or will surprise future maintainers.

- Project foundation: local Node/TypeScript CLI, `pnpm`, Vitest, Zod.
- Module convention: `src/modules/` with a thin CLI entrypoint.
- Markdown-first report with JSON as secondary/internal fixture artifact.
- Local-first/no-cloud/no-required-LLM boundary.
- Claim support taxonomy: `supported`, `partially_supported`, `unsupported`, `contradicted`, `cannot_determine`.
- Verdict taxonomy: `ready_for_focused_review`, `needs_human_review`, `send_agent_back`, `insufficient_material`.
- Fixture-first analyzer development.

## Open Questions

### Blocking

- N/A. Blocking product and foundation decisions for writing the V0 spec are resolved.

### Non-Blocking

- Whether optional JSON output is exposed in V0 or kept internal to fixture tests.
- Package publishing timing and npm package ownership.
- Whether and when live git `--base`/`--head` collection enters the CLI.
- Generated-output parity timing for non-payment fixture families.

## Review Notes

- Accepted by: project maintainer
- Date: 2026-06-15
- Links to discussion/PR: N/A; accepted in local spec interview.
