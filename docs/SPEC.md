# Spec: PatchTrace

Product source of truth: problem, user, product boundaries, success criteria,
and capability roadmap.

`docs/PLAN.md` owns detailed tasks for the nearest proposed phase.
`docs/ARCHITECTURE.md` owns current and target system design.

## Status

- Product: PatchTrace
- Spec status: proposed re-baseline after Phase 4 dogfooding
- Baseline: commit `d8c98c4`, head of open PR #19
- Last updated: 2026-07-27
- Proposed next execution phase: Phase 5 in `docs/PLAN.md`
- Human acceptance of this re-baseline: pending

## Product Definition

PatchTrace is a local developer tool that helps a human verify one coding-agent
run after the agent says "done."

It binds:

```text
what the agent was asked to do
  + what the agent claims it did
  + what changed during the recorded session
  + which commands and tests actually produced results
  + how every evidence item was captured and attributed
```

and turns that material into:

```text
a decisive verification verdict
  + one recommended next action
  + an evidence-backed starting point for review
  + concrete feedback to send back to the agent
```

PatchTrace is an evidence and decision-support layer. It is not a general AI code
reviewer, a correctness oracle, or an autonomous agent that accepts code.

PatchTrace can recommend `ready_for_human_acceptance` when task coverage and
required evidence meet explicit rules. The human remains the final decision
maker, and the recommendation is not a proof that code is correct or safe.

## Problem

Coding agents make implementation faster but leave a verification bottleneck.
After an agent reports completion, the reviewer must reconstruct:

- the original task and omitted requirements;
- the agent's final claims;
- which files and commits came from this session versus earlier dirty work;
- which commands actually ran and what they returned;
- whether claims and requirements have evidence;
- where evidence conflicts or is too weak;
- what to inspect first;
- whether to accept, review, rerun, or send the agent back.

Today this reconstruction is manual, inconsistent, and vulnerable to persuasive
agent summaries that are not evidence.

## Target User

Primary near-term user:

- a developer using Codex CLI locally and reviewing agent-created changes in a
  Git repository.

Likely later users:

- developers using another local coding agent after a second real adapter use
  case exists;
- maintainers and freelancers reviewing agent-created branches;
- small teams that want a local, inspectable verification artifact.

PatchTrace optimizes for repeated dogfooding before broad OSS adoption.

## Product Promise

For one explicitly bounded run, PatchTrace should answer:

1. What was requested?
2. Which explicit requirements and required verification steps exist?
3. What did the agent claim in its final output?
4. Which Git changes are session-attributed, pre-existing, or unattributable?
5. Which commands/tests have structured results, PTY signals, or only text
   inference?
6. Which task requirements and claims are supported, contradicted, incomplete,
   unaddressed, or not assessable?
7. Which evidence limitations affect the whole analysis?
8. What is the verification verdict?
9. Where should the human review first?
10. What exact next instruction should be sent to the agent?

## Product Boundaries

### PatchTrace Does

- record or ingest one explicit agent run;
- bind a user-supplied task contract and target Git repository to that run;
- collect local final-message, Git, command, and test evidence;
- preserve provenance and integrity metadata;
- classify session attribution conservatively but usefully;
- compare task requirements, agent claims, and evidence;
- emit one decisive verification verdict and recommended action;
- render a quick summary, ready-to-paste agent feedback, and detailed evidence
  brief from one `AnalysisResult`;
- keep raw materials local by default;
- remain useful without an LLM.

### PatchTrace Does Not

- prove semantic code correctness;
- replace security, provider, production, or human review;
- autonomously merge, approve, or accept work;
- perform broad generic code review;
- repair code automatically;
- infer a task silently from arbitrary transcript text;
- call missing evidence false;
- claim agent authorship when it only has session attribution;
- send private code, diffs, prompts, transcripts, or command output externally
  by default.

### Explicitly Out Of Scope

- SaaS, auth, teams, workspaces, billing, and entitlements;
- databases, queues, workflow engines, event sourcing, and web dashboards;
- plugin marketplace or speculative adapter framework;
- multi-agent orchestration;
- RAG, embeddings, or required LLM analysis;
- automatic fixes or merges;
- a broad eval platform;
- external telemetry by default;
- hosted proof pages or social artifacts.

## Current Implementation Truth

The Phase 4 Python implementation currently provides:

- `patchtrace run -- <command>`;
- PTY-based session recording through Pexpect;
- a local run folder and nine artifacts;
- pre-run Git status and a post-run whole-worktree status/diff;
- rules-first extraction of bounded file/change/test/command claims;
- exact `Final answer:` / `• Final answer:` marker recognition with a small
  Codex TUI noise normalizer;
- heuristic command/test result recognition from transcript text;
- one validated `AnalysisResult` used by all reports;
- shallow Markdown renderers;
- a sanitized Phase 4 claim matrix and real Codex CLI 0.144.1 dogfood proof.

Current limitations:

- no task contract or requirement coverage;
- no session-scoped Git attribution;
- untracked and committed-during-session changes are incomplete;
- no real `adapters/codex.py` boundary;
- no structured JSONL/final-message capture;
- wrapped-command and analysis outcomes are conflated;
- artifact provenance has no schema/parser/producer versions or digests;
- `Review First` is primarily changed-file order;
- `patchtrace analyze` and `patchtrace watch` are placeholders.

Current code and target architecture are intentionally separated in
`docs/ARCHITECTURE.md`.

## Trust Chain

```text
explicit task contract + target repository
  -> one resolved execution root + private run folder outside the worktree
  -> wrapped-command capture
  -> agent-specific final-output evidence
  -> before/after Git evidence
  -> command/test evidence
  -> provenance, integrity, and session attribution
  -> deterministic task/claim/evidence analysis
  -> one validated AnalysisResult
  -> verification verdict + recommended action + reports
  -> human review and final decision
```

### Trust Invariants

- No task contract is inferred silently. An explicit task input is bound to the
  run or the limitation is named.
- The selected repository root is the child's initial working directory, the
  Git evidence scope, and the identity used to resolve private run storage.
  PatchTrace records the caller, requested, and resolved paths rather than
  allowing those scopes to drift.
- The task contract is the user's evaluation contract. PatchTrace claims that
  the agent received identical task material only when prompt-delivery evidence
  separately establishes that fact.
- Every important evidence item records what it is, how it was captured, how it
  was interpreted, its locator, and its digest/version metadata.
- Structured evidence is preferred when the actual invocation provides it.
- Failed structured parsing cannot silently fall back to weaker transcript
  inference.
- `session-attributed` is a documented operational classification, not a claim
  of causal agent authorship.
- Pre-existing dirty material cannot support an agent file claim as if it were
  created during the run.
- A required command/test result supports readiness only when its captured
  repository state fingerprint matches the final state being analyzed.
- Wrapped-command outcome, analysis outcome, and package outcome remain
  independent.
- Missing evidence produces `degraded`, `blocked`, or an item-level
  `cannot_assess` result under explicit reason codes.
- Report renderers never reinterpret raw evidence independently.
- `ready_for_human_acceptance` is unavailable until task requirement coverage
  and required verification are implemented.
- The human can accept or override the verification verdict.

## Core Domain Relationships

```text
TaskContract
  contains -> TaskRequirement[]

AgentFinalOutput
  contains -> AgentClaim[]

EvidenceItem
  may support/conflict with -> TaskRequirement
  may support/conflict with -> AgentClaim

GitEvidenceItem
  has -> SessionAttribution

Run
  has -> WrappedCommandOutcome
  has -> AnalysisOutcome
  has -> PackageOutcome

AnalysisResult
  contains -> RequirementCoverage[]
  contains -> ClaimAssessment[]
  contains -> EvidenceGap[]
  contains -> VerificationVerdict
  contains -> RecommendedAction
```

These relationships do not imply code correctness.

## Verification Verdict

Target verdicts:

| Verdict | Meaning |
|---|---|
| `ready_for_human_acceptance` | Explicit task requirements, required verification, claims, and session-attributed evidence meet the accepted rules; the human can accept or inspect before accepting. |
| `review_required` | Evidence exists but a human must inspect identified risk, ambiguity, or scope before deciding. |
| `send_back` | A task requirement or agent claim is materially unsupported, contradicted, omitted, or outside the agreed scope and needs agent action. |
| `rerun_required` | The relevant command/test/capture must be rerun because result evidence is missing, stale, malformed, incomplete, or mismatched. |
| `cannot_assess` | PatchTrace lacks enough trusted run material to produce a stronger recommendation. |

The verdict should be decisive and appear early. Correctness limitations should
be stated once, not repeated as defensive boilerplate throughout every report.

Verdict selection is centralized in `AnalysisResult`; renderers cannot select or
upgrade it. Target precedence is:

1. `cannot_assess` when trusted analysis is blocked;
2. `rerun_required` when recapturing a missing, stale, malformed, incomplete, or
   mismatched required result is the next necessary action;
3. `send_back` when an explicit requirement is omitted, a valid required check
   fails, or evidence materially contradicts the agent;
4. `review_required` when evidence exists but risk, ambiguity, scope, or
   unattributable material requires inspection;
5. `ready_for_human_acceptance` only when the supported run schema is current,
   required task coverage and required verification are complete, evidence
   integrity passes, and no higher-precedence condition exists.

Mutated artifacts, unknown-incompatible schemas, and imported bundles without
equivalent trusted provenance cannot emit `ready_for_human_acceptance`. A
compatible saved trusted run may preserve or recompute the verdict after digest
and compatibility checks; post-hoc execution alone is not a disqualifier.

## Major Proposal Pressure Test

Every major capability must answer the anti-overengineering questions.

| Proposal | Confirmed problem | Needed now? | Current stack enough? | Simpler version | Cost of deferring |
|---|---|---|---|---|---|
| Raw task binding | PatchTrace cannot know what work was requested. | Yes, before broader trust claims. | Yes: Typer, files, Pydantic. | Copy one explicit task file; parse later. | Run evidence remains detached from the task. |
| Versioned provenance | Paths alone do not prove which mutable artifact was analyzed. | Yes. | Yes: Pydantic + SHA-256 stdlib. | One evidence envelope, no provenance graph. | Post-hoc analysis can reinterpret changed material silently. |
| Session-scoped Git attribution | Whole-worktree evidence can wrongly support agent claims. | Yes; highest-risk current flaw. | Yes: Git CLI + Python. | Before/after state, fingerprints, HEAD ancestry, limited dirty mode. | Reports can confidently cite another change as session evidence. |
| Concrete Codex adapter | Codex TUI markers currently leak into generic transcript code. | Yes, because one real agent format exists. | Yes. | One module, no registry/plugin system. | Format drift keeps breaking generic capture and docs remain false. |
| Structured `codex exec` capture | Codex exposes JSONL events and final-message output while text parsing is brittle. | Yes, as an additional real path. | Yes; subprocess/JSON stdlib. | Support only explicit `codex exec`; keep interactive PTY fallback. | Command/final evidence stays heuristic where stronger data exists. |
| Requirement coverage | Supported self-reported claims can omit requested work. | Immediately after trusted ingestion. | Yes for explicit small contracts. | User-authored requirement items; no LLM semantic parser. | PatchTrace can endorse a partial answer to the task. |
| Explainable review priority | Changed-file order ignores contradictions and task risk. | After provenance and coverage. | Yes. | Deterministic reasons and ordering, no score. | Review remains slower but evidence truth is not corrupted. |
| Post-hoc analyze | Users sometimes have saved material but no wrapped session. | After full run trust is stable. | Yes. | Analyze one saved run or explicit imported bundle. | Some adoption paths wait; primary workflow remains usable. |
| OSS distribution | Current source checkout is not easy for external users. | After repeated dogfood proves the contract. | Yes. | Package, compatibility matrix, docs, no hosted service. | External validation is delayed. |
| Optional integrations | Other agents/PR flows may become useful. | No confirmed second use case yet. | Probably, decision deferred. | Add only one triggered capability at a time. | Little; premature abstractions are the larger cost. |

## Success Criteria

### Product-Level

- A reviewer can identify the verification verdict and next action within
  seconds.
- Every decisive statement links to captured evidence or an explicit missing
  evidence reason.
- PatchTrace distinguishes task requirements, agent claims, evidence,
  attribution, and correctness.
- Pre-existing changes cannot be silently credited to the recorded session.
- Omitted task requirements remain visible even when every agent claim is
  supported.
- Structured command/final evidence is visibly stronger than text inference.
- Reports are useful without an LLM or external service.
- A human can send generated feedback directly back to the coding agent.

### Quality And Privacy

- Fixture-first tests cover fragile transcript, JSONL, Git, and report behavior.
- One `AnalysisResult` drives every report.
- Unknown/malformed inputs degrade explicitly.
- Run artifacts have version/integrity metadata and private local permissions
  where supported.
- Run artifacts default to Git metadata storage outside the selected worktree,
  so ordinary `git add` cannot commit task, transcript, prompt, or output data.
- Structured capture explicitly distinguishes complete, incomplete, malformed,
  and mismatched material.
- Reports minimize copied sensitive material and prefer locators into private
  raw artifacts.
- No private material is sent externally by default.
- No report presents a verdict as autonomous acceptance or correctness proof.

## Commands

Current:

```bash
uv sync
uv run patchtrace --help
uv run patchtrace run -- python tests/fixtures/fake_agent.py
uv run patchtrace run -- codex
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv build
```

Target after Phase 5:

```bash
uv run patchtrace run --task-file ./TASK.md --repo . -- codex
uv run patchtrace run --task-file ./TASK.md --repo . -- codex exec "<prompt>"
```

`patchtrace analyze` and `patchtrace watch` remain not implemented until their
roadmap gates are reached.

## Capability Roadmap

This roadmap belongs here because it expresses product capability order and
value. `docs/PLAN.md` contains implementation detail only for the nearest phase.

### Phase 5 — Trusted Run Evidence And Provenance

**Problem:** The current run cannot reliably bind the task, final output, Git
delta, or command results to one session.

**User value:** The verification package becomes trustworthy enough to use as
the factual basis for review.

**Dependencies:** Phase 4 capture/analysis/report baseline; current Codex
0.144.1 structured `exec` capabilities; existing Git/PTY fixtures.

**Exit criteria:**

- explicit raw task and target-repository binding;
- one execution/storage anchor: child cwd and Git scope use the resolved
  repository root, while private artifacts live in Git metadata outside the
  tracked worktree;
- versioned/digested evidence envelope;
- session-attributed/pre-existing/unattributable Git material;
- concrete Codex adapter with structured exec path and explicit TUI fallback;
- repository-state freshness for command/test results;
- separate wrapped-command, analysis, and package outcomes plus documented CLI
  exit semantics;
- provenance-aware reports with decisive verdicts;
- full fixture matrix, real dogfood, automated gates, and human review.

**Out of scope:** Parsed requirement coverage, broad prioritization,
post-hoc analyze, watch, package release, non-Codex adapters, LLM.

**Plan-change triggers:** Structured events omit required facts; dirty attribution
misleads; explicit task input is unusable; transport abstraction becomes
speculative.

Detailed tasks: `docs/PLAN.md`.

### Phase 6 — Task Contract And Requirement Coverage

**Problem:** Claim support alone cannot detect work the agent omitted from its
final answer.

**User value:** PatchTrace can say whether the complete explicit task was
addressed, not only whether selected agent claims have evidence.

**Dependencies:** Phase 5 raw task binding, provenance, attribution, outcome
semantics, and trusted final/command evidence.

**Exit criteria:**

- a small validated task-contract format covers requested outcome, explicit
  requirements, acceptance criteria, required verification, and out of scope;
- each explicit requirement has an addressed/unaddressed/cannot-assess coverage
  result with linked claims/evidence;
- omitted requirements appear in summary, brief, and agent feedback;
- `ready_for_human_acceptance` requires complete required coverage plus required
  verification that is bound to the final analyzed repository state under
  tested rules;
- fixtures cover complete, partial, omitted, conflicting, and malformed
  contracts without LLM use;
- human dogfood confirms authoring cost is acceptable.

**Out of scope:** Large-spec semantic interpretation, generated requirements,
LLM extraction, correctness analysis, scope negotiation.

**Plan-change triggers:** Manual contract authoring is too expensive; users
repeatedly need Markdown and JSON variants; deterministic coverage cannot handle
the smallest real contracts.

### Phase 7 — Evidence Quality And Review Prioritization

**Problem:** Correct evidence ownership still leaves the reviewer with an
unhelpful file-order list and no explanation of what deserves attention first.

**User value:** Review starts at the most consequential conflict, missing proof,
scope drift, or risky area.

**Dependencies:** Trusted provenance and requirement coverage from Phases 5–6.

**Exit criteria:**

- review ordering considers requirement gaps, claim/evidence conflicts,
  missing required verification, unattributable changes, scope drift, and
  deterministic high-risk path/content rules;
- every priority has a plain-language reason and evidence locator;
- no opaque score or correctness ranking is introduced;
- fixtures prove stable ordering and decisive next actions;
- dogfooding shows the first suggested target is usually the right place to
  begin.

**Out of scope:** Generic bug finding, LLM code review, broad security scanning,
autonomous acceptance.

**Plan-change triggers:** Rules produce noisy priorities; risk categories lack
real misses; users prefer grouped review paths over strict ordering.

### Phase 8 — Post-Hoc Analyze Workflow

**Problem:** A user may have a saved PatchTrace run or explicit evidence bundle
without having started the original agent through the current CLI path.

**User value:** Existing local material can be analyzed with transparent limits
instead of being discarded.

**Dependencies:** Versioned provenance, compatibility rules, task contracts,
analysis outcomes, and stable `AnalysisResult`.

**Exit criteria:**

- `patchtrace analyze --run <path>` re-renders or re-analyzes a compatible saved
  run without mutating original evidence;
- an explicit imported-bundle path validates task, repository, final, Git, and
  command material and labels anything that cannot be session-attributed;
- schema/parser compatibility is checked and unknown versions fail clearly;
- post-hoc reports cannot look stronger than wrapped-run reports when provenance
  is weaker;
- fixture and real saved-run tests pass.

**Out of scope:** Watch daemon, automatic repository discovery, cloud imports,
GitHub integration, transcript guessing.

**Plan-change triggers:** Users primarily need current-worktree analysis rather
than saved runs; compatibility maintenance becomes too costly; imported
evidence cannot retain useful provenance.

### Phase 9 — OSS And Distribution Readiness

**Problem:** The validated local tool is still optimized for a maintainer source
checkout rather than external installation and contribution.

**User value:** Developers can install, understand, trust, and report issues
against a stable local CLI.

**Dependencies:** Stable run/task/evidence/report contracts and repeated
dogfooding through Phases 5–8.

**Exit criteria:**

- package metadata, CLI versioning, installation, upgrade, and uninstall paths
  are documented and tested;
- supported Python, OS, Git, and Codex version matrix is explicit;
- privacy/retention/security guidance and sanitized examples are complete;
- public command behavior and schema compatibility policy are documented;
- release CI, changelog, contributor workflow, license, and rollback guidance
  exist;
- at least one clean external install smoke test passes.

**Out of scope:** Hosted service, telemetry by default, billing, Windows support
unless explicitly selected, marketplace integrations.

**Plan-change triggers:** External users require Windows; packaging exposes
dependency/permission problems; public schema stability is premature.

### Phase 10 — Triggered Integrations, Not A Pre-Committed Platform

**Problem:** Proven adoption may create a concrete need for another agent,
machine-readable output, background capture, or PR workflow.

**User value:** PatchTrace fits one demonstrated adjacent workflow without
weakening local evidence semantics.

**Dependencies:** OSS-ready core plus a real repeated use case and explicit
human approval for the selected integration.

**Exit criteria:**

- exactly one triggered capability is selected and specified;
- its trust boundary, privacy impact, failure behavior, and compatibility are
  explicit;
- a second real adapter is required before extracting a generic adapter
  protocol;
- any external transfer is opt-in and separately approved;
- the integration reuses the same `AnalysisResult` and does not fork analysis.

**Out of scope:** Building all candidates, plugin marketplace, SaaS platform,
required LLM, broad orchestration.

**Plan-change triggers:** No repeated demand means no phase. Candidate triggers
include:

- a second real coding agent -> second concrete adapter, then consider a shared
  protocol;
- repeated need for automation -> optional stable JSON output;
- repeated missed sessions -> reconsider `watch`;
- repeated PR workflow demand -> scoped GitHub integration;
- rules-first extraction ceiling demonstrated by fixtures -> consider opt-in LLM
  extraction with privacy, cost, retry, logging, and failure boundaries.

## Deferred Capabilities

- `patchtrace watch` remains a candidate, not an assumed product requirement.
- Public JSON output waits for a real downstream consumer.
- Non-Codex adapters wait for a second real agent workflow.
- Optional LLM use waits for a measured rules-first miss and explicit approval.
- GitHub integration waits for local workflow maturity and user demand.
- Windows waits for prioritization and a tested PTY strategy.

## Architecture Decision Records

- `ADR-0001`: accepted Python local-CLI foundation.
- `ADR-0002`: proposed trust chain, provenance, outcomes, and decisive
  verification verdict.
- `ADR-0003`: proposed concrete Codex structured-first boundary.
- `ADR-0004`: proposed session-scoped Git attribution model.

Proposed ADRs become accepted only after human review.

## Open Questions

### Blocking Before Phase 5 Task 1

- N/A. The first task tests the explicit raw task-file boundary without deciding
  the Phase 6 parsed contract format.

### Non-Blocking

- Should the Phase 6 contract be structured Markdown, JSON, or both?
- Which exact reason-code names produce the clearest reports?

## Source-Of-Truth Links

| Area | Source |
|---|---|
| Current/target system design and trust boundaries | `docs/ARCHITECTURE.md` |
| Current detailed implementation phase | `docs/PLAN.md` |
| Canonical domain language | `CONTEXT.md` |
| Foundation and proposed irreversible decisions | `docs/decisions/` |
| Verified milestones | `docs/VERIFY_LOG.md` |
| Team/agent workflow | `docs/AGENT_WORKFLOW.md` |
