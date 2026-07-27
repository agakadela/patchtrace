# Spec: PatchTrace

Product source of truth: what PatchTrace is, who it serves, which outcomes it
owns, its boundaries, and how product success is measured.

- Full capability sequence and phase status: `docs/ROADMAP.md`
- Detailed tasks for the active/proposed phase: `docs/PLAN.md`
- Current and target system design: `docs/ARCHITECTURE.md`
- Canonical language: `CONTEXT.md`
- Irreversible decisions: `docs/decisions/`

## Status

- Product: PatchTrace
- Spec status: confirmed product intent; implementation re-baseline proposed
- Confirmed by: project owner during `$aga-spec` interview
- Baseline: commit `d8c98c4`, head of open Phase 4 PR #19
- Last updated: 2026-07-27
- Current implemented capability: Phase 4 explicit claim assessment
- Proposed next capability: Phase 5 end-to-end trusted run

The product direction in this spec is confirmed. Proposed architecture and ADR
details still require review before implementation starts.

## Objective

PatchTrace is a production-quality, local-first developer tool that verifies
whether one Codex run fulfilled an explicit task.

Its primary user is the project owner: a developer using Codex locally. After
Codex says "done", PatchTrace must make the next decision clear:

- `ready_to_accept`;
- `send_back`;
- `review_required`;
- `rerun_required`;
- `cannot_assess`.

PatchTrace must explain the decisive reason, show the relevant evidence, and
produce an exact next action. It verifies task fulfillment and evidence quality.
It does not perform general code review or prove semantic correctness.

The product is dogfooded for this real workflow first, then prepared for public
open-source use after its core contracts are stable.

## User Problem

Coding agents accelerate implementation but move effort into verification. A
developer currently has to reconstruct:

- the exact task the agent received;
- every explicit requirement and acceptance criterion;
- what the agent claims it completed;
- which Git changes belong to the captured session;
- whether prior dirty work was mixed into the evidence;
- which commands and tests ran, against which repository state, and with what
  result;
- which requirements are supported, omitted, contradicted, or not assessable;
- whether the work is ready to accept or must go back to the agent.

Agent prose is not sufficient evidence. A passing test from before the final edit
is not current evidence. A final worktree diff is not automatically a session
delta. PatchTrace exists to resolve those gaps with explicit, local,
inspectable contracts.

## Product Promise

For one trusted run, PatchTrace answers:

1. What exact task payload was given to Codex?
2. Which requirements, acceptance criteria, verification commands, and
   out-of-scope boundaries were declared?
3. What did Codex claim for every requirement?
4. Which changes are `session-attributed`, `pre-existing`, or
   `unattributable`?
5. Which command results are structured, state-bound, stale, inferred, missing,
   or failed?
6. Did the final required verification pass against the final analyzed
   repository state?
7. Which requirements are supported, contradicted, omitted, or not assessable?
8. What is the verification verdict and the one recommended next action?
9. Where should a human inspect first?
10. What exact feedback should be sent back to Codex?

## Canonical Trusted Flow

```text
validated Markdown task contract
  -> unchanged user task payload
  + versioned PatchTrace execution/response protocol
  -> explicit `codex exec` structured run
  -> structured final response for every requirement
  -> private baseline and agent-end Git snapshots
  -> session-scoped Git attribution
  -> final required verification executed by PatchTrace
  -> verification-end snapshot and side-effect check
  -> one validated AnalysisResult
  -> decisive verdict + recommended action
  -> SUMMARY.md + AGENT_FEEDBACK.md + VERIFICATION_BRIEF.md
  -> human accepts, reviews, reruns, or sends back
```

The task payload is preserved byte-for-byte and bound by digest. PatchTrace adds
a separate versioned execution/response protocol so Codex can return structured
requirement claims. The manifest records both inputs independently.

The primary trusted mode is non-interactive `codex exec`, using documented JSONL,
final-message, and output-schema capabilities. Interactive Codex remains a
supported workflow for conversations, but it is not treated as equivalent
evidence and cannot receive `ready_to_accept` without the complete trusted
evidence contract.

## Task Contract V1

The user supplies one human-readable Markdown file. V1 uses fixed sections:

```markdown
## Outcome

## Requirements

## Acceptance Criteria

## Required Verification

## Out of Scope
```

Rules:

- the file is validated before Codex starts;
- the original task bytes are copied into private run storage and digested;
- `Outcome` contains one non-empty goal and is not a completion checklist;
- `Requirements` contains one or more `REQ-*` obligations;
- `Acceptance Criteria` contains one or more `AC-*` observable conditions,
  links each condition to one or more requirements, and declares one closed
  independent evidence predicate;
- every `REQ-*` is linked from at least one `AC-*`;
- `Required Verification` contains zero or more `VER-*` commands authorized by
  the user, or an explicit `N/A` with a reason;
- `Out of Scope` contains zero or more `OOS-*` constraints, or an explicit
  `N/A` with a reason;
- Codex's structured response must address every `REQ-*` and `AC-*`; PatchTrace
  executes `VER-*` itself and evaluates `OOS-*` against captured evidence;
- the only structured fulfillment statuses for `REQ-*` and `AC-*` are
  `claimed_done`, `not_done`, and `blocked`; `claimed_done` remains a claim,
  while schema-valid `not_done` or `blocked` is explicit unfulfilled work and
  selects `send_back`;
- a missing, duplicate, unexpected, or invalid structured entry is a response
  protocol/capture failure and selects `rerun_required`, never an inferred
  fulfillment result;
- an agent response is always a claim, never the independent evidence basis for
  an acceptance criterion;
- PatchTrace does not invent requirements, commands, or scope;
- malformed or ambiguous contracts fail before launch rather than silently
  becoming a weaker trusted run.

An acceptance evidence predicate is a closed deterministic expression over
typed Git/artifact properties, named `VER-*` results with expected outcomes, or
explicit human inspection. It may combine supported atoms only with declared
`all`/`any` semantics. The task author defines which observable predicate
satisfies the natural-language criterion; PatchTrace evaluates that predicate
and never infers semantic sufficiency from file presence, a changed path, or an
agent claim. Unsupported or ambiguous machine predicates fail task validation;
an explicit human-inspection predicate produces `review_required` with the
exact inspection target when it remains necessary. An `OOS-*` constraint that
cannot be assessed deterministically also produces `review_required`; silence
is never treated as proof of compliance. The exact Markdown spelling for these
already-decided semantics remains a Phase 5 Task 1 design detail.

## Verification Verdict

### Verdict Contract

| Verdict | Meaning | Required next action |
|---|---|---|
| `ready_to_accept` | Canonical Codex completed successfully; every explicit requirement is fulfilled and every acceptance predicate is independently satisfied; all applicable required verification passed against unchanged relevant quiescent agent-end/verification-end state; relevant changes have complete session attribution; no higher-precedence conflict exists. | Accept. |
| `send_back` | A requirement is explicitly unfinished or independently shown unmet, a valid required check fails, a claim conflicts with evidence, or work exceeds the declared scope. | Send the generated corrective instruction to Codex. |
| `review_required` | Evidence is complete enough to identify a bounded ambiguity, human-inspection criterion, risk, or unattributable scope that requires human judgment. | Inspect the named evidence targets before deciding. |
| `rerun_required` | A valid supported run exists, but agent execution failed or a named capture, containment, quiescence, or verification step is missing, stale, malformed, incomplete, mismatched, or not bound to the final state and can be repaired by repeating that step/run. | Repeat the named supported execution, capture, or verification. |
| `cannot_assess` | The existing run has no usable trusted contract, uses an unsupported/incompatible trust format, or has integrity damage that a same-run recapture cannot repair. | Create or restore a compatible trusted run before evaluating the work. |

### Precedence

One analyzer-owned rule selects exactly one verdict:

1. `cannot_assess` for an unusable or unsupported trusted contract/package that
   cannot be repaired inside the existing run;
2. `rerun_required` when a valid supported run names a failed agent execution,
   capture, containment, quiescence, or verification step that must be repeated;
3. `send_back` for schema-valid `not_done`/`blocked` entries, independently
   shown unmet requirements, valid required-check failures, scope violations,
   relevant verification-phase changes, or material contradictions;
4. `review_required` for a human-inspection criterion, bounded ambiguity, risk,
   or unattributable evidence;
5. `ready_to_accept` only when every required condition passes.

A valid failing test is evidence for `send_back`, not a reason to repeat the same
capture. Missing structured final output in an otherwise supported run is
`rerun_required`; an unknown-incompatible schema or post-capture integrity
mismatch is `cannot_assess`. The closed class-to-outcome-to-verdict mapping
lives in `docs/ARCHITECTURE.md` and ADR-0002. Report renderers cannot select,
weaken, or promote the verdict.

`ready_to_accept` is a strong decision within PatchTrace's contract. It is not a
claim that PatchTrace performed general code review.

## Product Scope

### Committed Capabilities

- validated Markdown task contracts;
- PatchTrace-owned delivery of the task payload to Codex;
- versioned structured Codex execution and final response;
- private local run storage in Git metadata;
- clean and dirty repository baseline capture;
- session-scoped tracked, staged, unstaged, untracked, and committed change
  attribution;
- final-state execution of user-authorized verification commands;
- deterministic requirement, claim, and evidence relationships;
- one validated `AnalysisResult`;
- decisive verdict and recommended action;
- quick summary, paste-ready agent feedback, and detailed verification brief;
- explainable evidence quality and review prioritization;
- compatible post-hoc analysis;
- a local continuous watch workflow;
- public OSS packaging and documentation;
- macOS first, Linux before OSS release, and a later explicit Windows
  portability phase.

The complete sequence, dependencies, and phase exit criteria live in
`docs/ROADMAP.md`.

### Conditional Capabilities

These are recorded in the roadmap but are not committed phases until their
trigger exists:

- a second coding-agent adapter;
- a shared adapter protocol extracted from two real adapters;
- GitHub/PR integration;
- stable machine-readable public output;
- optional LLM extraction or summarization after a measured deterministic miss;
- local HTML presentation if Markdown becomes insufficient.

### Explicitly Out Of Product

- general code review or correctness scoring;
- autonomous code acceptance, merge, or repair;
- SaaS, hosted accounts, teams, billing, or entitlements;
- databases, queues, event sourcing, or a workflow platform without a future
  confirmed product requirement;
- plugin marketplace;
- required LLM, RAG, or embeddings;
- multi-agent orchestration;
- external telemetry or data transfer by default;
- speculative interfaces without a real second implementation.

## Trust And Privacy Boundaries

### Always

- keep task, prompt protocol, transcript, JSONL, diffs, baselines, command
  output, and reports local by default;
- store trusted-run artifacts under PatchTrace-owned Git metadata outside the
  tracked worktree;
- record schema, producer, adapter, parser, and protocol versions plus artifact
  digests;
- preserve the user task separately from PatchTrace's execution protocol;
- require a closed supported evidence predicate for every acceptance
  criterion before `ready_to_accept`;
- run every Git collector command with non-refresh/non-optional-lock behavior
  and prove that collection leaves index bytes and semantic Git state unchanged;
- construct trusted Codex execution from a recorded controlled profile with no
  unaccounted hooks, notification command, MCP/plugin writer, network policy,
  inherited environment/credential exposure, temp path, or writable root;
- execute required verification under a recorded controlled effect profile
  that default-denies network and external writes, allowlists environment and
  credential exposure, bounds temp/writable roots and subprocesses, and reaches
  quiescence before the terminal snapshot;
- bind required verification to the final analyzed repository state;
- capture agent-end state before verification and verification-end state after
  it, keeping any verification-phase delta separate;
- make every decisive report statement traceable to evidence or a named rule;
- use fixture-first tests for external formats and edge cases;
- leave partial failures diagnosable through a durable manifest.

### Ask First

- any new runtime dependency;
- any external service or network transfer;
- any expansion of the trusted Codex or verification effect scope beyond the
  Phase 5 local profile;
- any LLM/model call, with explicit privacy, cost, retry, logging, and failure
  boundaries;
- any public schema compatibility commitment;
- any new agent adapter or integration;
- any change that lets PatchTrace itself mutate the index, worktree, branches,
  commits, or Git configuration.

### Never

- modify Git state merely to improve attribution;
- infer a missing task silently;
- treat agent claims as evidence by themselves;
- infer that a changed/present artifact semantically satisfies an acceptance
  criterion without its declared supported predicate;
- treat old passing tests as verification of later edits;
- execute verification commands that were not explicitly authorized;
- send private run material externally by default;
- downgrade structured-capture failure into unlabeled text inference;
- place raw task text, agent claims/output, command output, diffs, or
  user-controlled paths/file names in paste-ready agent feedback;
- represent a PatchTrace verdict as general code correctness.

For public OSS use, verification commands from an untrusted or repository-owned
task file require an explicit execution confirmation. The project owner's own
task input is authorized by invoking the trusted run.

## Engineering Constraints

- Keep the accepted Python >=3.11 stack and
  `src/patchtrace/<capability>/...` module convention from ADR-0001.
- Prefer the existing standard-library, Git CLI, Typer, Pydantic, Pexpect,
  pytest, Ruff, mypy, and `uv` toolchain; a new runtime dependency requires
  explicit approval.
- Keep one concrete Codex adapter and a deterministic rules-first analyzer; do
  not create a plugin framework or make an LLM part of the trusted path.
- Preserve local-first operation, strict typing, validated boundary models,
  fixture-first external-format support, and no silent failure handling.
- Require automated quality gates plus real workflow proof before a production
  phase closes.

System ownership, data contracts, capture rules, and dependency boundaries live
in `docs/ARCHITECTURE.md`. Exact Phase 5 tasks and verification matrices live in
`docs/PLAN.md`. Workflow commands and commit/PR gates live in `AGENTS.md` and
`docs/AGENT_WORKFLOW.md`.

## Success Criteria

### Product

- the primary user can provide one task file once and receive a complete trusted
  package without duplicating the prompt;
- the first report screen makes the verdict, decisive reason, coverage summary,
  final verification results, attribution limitations, and next action clear;
- omitted task requirements remain visible even if Codex omits them from its
  own summary;
- an agent claim without independent supported evidence never produces
  `ready_to_accept`;
- dirty repositories remain usable when the private baseline makes the session
  delta complete;
- a passing required command can support `ready_to_accept` only when it ran
  against the final analyzed repository state;
- a required command that changes relevant tracked or non-ignored repository
  state during the verification phase produces `send_back` with its
  verification-phase delta;
- generated feedback is directly usable as the next Codex instruction using
  only PatchTrace-authored reason text, grammar-validated task IDs,
  PatchTrace-generated evidence IDs, and PatchTrace-controlled local artifact
  locators;
- all three reports agree because they consume one `AnalysisResult`;
- the trusted workflow requires no LLM or external service.

### Production Engineering

- supported failures leave a durable, truthful manifest and actionable CLI
  output;
- storage is private, bounded, atomic, and collision-safe;
- file/snapshot traversal has explicit file, byte, path-count, and time limits;
- special files and symlinks cannot block or escape the selected repository;
- structured artifacts are versioned, digested, and compatibility-checked;
- trusted Codex runs record and constrain security-relevant effective
  configuration, network, environment, credential, temp, and writable scope;
- Codex spawn, non-zero exit, signal, interruption, and unknown terminal
  outcomes have one closed mapping and cannot produce `ready_to_accept`;
- verification execution has explicit authorization, controlled effect scope,
  timeout, process-tree containment, output-limit behavior, and separate
  quiescent agent-end and verification-end snapshots;
- verification spawn failure, intentional interruption, lost exit status, and
  required-output truncation select `rerun_required`; a captured non-zero exit,
  declared-timeout termination, or unrequested signal selects `send_back`;
- external format drift is covered by sanitized fixtures before support claims
  expand;
- macOS real workflows pass before Phase 5 close, Linux passes before public OSS
  release, and Windows passes before Windows support is claimed.

## Major Decision Pressure Test

| Decision | Confirmed problem | Needed | Existing stack sufficient | Simpler version | Cost of deferring |
|---|---|---|---|---|---|
| One Markdown task payload | Claims alone cannot reveal omitted work. | Now | Yes | Fixed headings and lists; no semantic LLM parser | PatchTrace cannot make a complete accept decision. |
| Closed acceptance predicates | A changed artifact does not prove a natural-language criterion. | Now | Yes | User-declared typed Git/artifact, `VER-*`, or human-inspection expression | `ready_to_accept` can be promoted by irrelevant file presence. |
| Structured `codex exec` as trusted mode | TUI markers and text command parsing are presentation-dependent. | Now | Yes | One concrete Codex adapter; interactive mode remains secondary | Final/command evidence remains too weak for a production verdict. |
| Private dirty baseline | Final worktree evidence can mix prior and session changes. | Now | Yes | Bounded `H0/I0/W0` and agent-end content snapshots; no worktree virtualization | Dirty repos remain unsafe or unnecessarily rejected. |
| PatchTrace final verification | Agent-run tests may predate the final change. | Now | Yes | Execute only explicit contract commands after capture | `ready_to_accept` can rely on stale tests. |
| Controlled quiescent execution | Background descendants and external effects can outlive the parent command. | Now | Needs a source-checked supported-platform implementation | Contained process tree, closed effect profile, quiescent snapshots | A matching endpoint snapshot can become stale immediately. |
| One deterministic verdict | Evidence without a decision leaves verification work to the user. | Now | Yes | Five typed outcomes and one precedence rule | Product remains a report generator instead of solving the decision. |
| Separate canonical roadmap | Product phases and current implementation tasks were mixed in SPEC/PLAN. | Now | Yes | One Markdown source of truth | Future capabilities keep disappearing or being mistaken for current scope. |
| Watch | The user wants normal Codex use without remembering a wrapper. | Later, committed | Probably | Local repo-scoped watcher after saved-run ingestion is stable | Manual wrapper remains required. |
| OSS | The owner wants eventual public use. | Later, committed | Yes | Package and support matrix; no hosted platform | External validation and adoption wait. |

## ADR Register

| Decision | Status | ADR action |
|---|---|---|
| Python stack and `src/patchtrace/<capability>` module convention | Accepted | Keep ADR-0001; no new module-convention ADR required. |
| Versioned trust chain, evidence envelope, outcomes, and decisive verdict | Proposed | Revise ADR-0002 to use `ready_to_accept` and package/final-verification semantics. |
| Structured `codex exec` as canonical trusted mode; interactive as secondary | Proposed | Revise ADR-0003. |
| Private dirty baseline and session-scoped Git attribution | Proposed | Revise ADR-0004. |
| Markdown task payload, versioned response protocol, and authorized final verification | Proposed | Review ADR-0005 before implementation. |
| Watch lifecycle and session association | Candidate | Add an ADR only when Phase 8 specifies its real process model. |
| Public schema compatibility | Candidate | Add an ADR when Phase 9 creates a public contract. |

## Open Questions

### Blocking

- N/A. The confirmed product intent is sufficient to prepare the full roadmap
  and Phase 5 implementation plan.

### Non-Blocking

- Exact Markdown syntax and validation messages for the decided Task Contract V1
  taxonomy, links, and typed evidence-predicate declarations.
- Source-checked supported-macOS primitives for Codex/verification effect
  enforcement, descendant containment, and quiescent checkpoints.
- Default per-file, total-byte, path-count, output, and elapsed-time limits.
- Exact analysis/package reason-code spellings.
- Run retention and deletion policy before continuous watch ships.
- Watch process installation, lifecycle, and Codex-session association.
- Minimum Linux distribution matrix for OSS.
- Windows process/terminal strategy and release phase detail.
- Exact demand thresholds for conditional integrations.

## Source-Of-Truth Links

| Area | Source |
|---|---|
| Product objective, scope, success, boundaries | This file |
| Complete phase sequence and status | `docs/ROADMAP.md` |
| Detailed tasks for the active/proposed phase | `docs/PLAN.md` |
| Current/target design and trust boundaries | `docs/ARCHITECTURE.md` |
| Canonical domain language | `CONTEXT.md` |
| Decisions | `docs/decisions/` |
| Verified milestones | `docs/VERIFY_LOG.md` |
| Agent workflow | `AGENTS.md`, `docs/AGENT_WORKFLOW.md` |
