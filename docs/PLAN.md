# Phase 6 — Task Coverage and Final Verification

**Status:** active; proposed incremental plan; T1 not started

**Baseline:** Phase 5 — Trusted Capture and Session Provenance closed on
2026-09-14. Closure evidence:
[VERIFY_LOG.md](VERIFY_LOG.md#2026-09-14---phase-5-close-app-server-decision-and-trust-ceiling-dogfood).

**Next task:** T1 — Render a complete conservative Task Contract coverage
inventory.

**Roadmap:** [ROADMAP.md](ROADMAP.md)

This file is the single owner of active tasks. Historical Phase 5 details live
in Git history, the architecture, its ADRs, and the verification log. No
parallel `tasks/` plan or duplicate checklist is created.

Work on one task at a time. Each standard task ends in a user-visible,
fixture-backed slice, targeted verification, an Aga verification result, code
review, and a commit. Use a short-lived `agent/...` branch and draft PR for
substantial slices. Do not weaken the Phase 5 provenance or capture-mode
ceilings to obtain a stronger Phase 6 verdict.

## Phase goal

Make every preserved Task Contract item visible in the shared analysis, connect
it conservatively to captured claims and evidence, distinguish missing or
human-judgment coverage from established facts, and optionally run explicitly
authorized final verification against an identified final Git state.

The developer remains the final decision-maker. A PatchTrace verdict describes
evidence coverage within the task and capture boundaries; it does not certify
semantic correctness, safety, or acceptance.

## Dependency order

```text
T1 complete task inventory and coverage model
  -> T2 conservative requirement/claim/evidence relationships
      -> checkpoint A
          -> T3 explicit final-verification authorization and capture
              -> T4 verification freshness against final Git identity
                  -> T5 deterministic task-bounded verdict and report parity
                      -> T6 Phase 6 dogfood and closure
```

T1–T2 do not execute user commands and can proceed independently of the T3
interface decision. T3 is high-risk because it executes user-authorized local
commands; implementation must pause at the ask-first checkpoint below.

## Phase constraints

- Task Contract V1 remains simple Markdown. Do not add a predicate DSL,
  expression trees, or a policy engine.
- Every requirement and acceptance criterion remains visible even when no
  claim or evidence refers to it.
- A claim-to-requirement link is not requirement satisfaction.
- Path presence or a changed file does not establish semantic behavior.
- Natural-language criteria requiring judgment are labeled for human review.
- A missing or invalid Task Contract prevents the strongest task-bounded
  verdict.
- PTY command results remain transcript-derived until an explicitly authorized
  final-verification command is captured by PatchTrace itself.
- Final verification never runs implicitly from prose in `task.md` or from
  agent output.
- No shell evaluation, network service, LLM, database, event bus, generic
  adapter framework, or new dependency is assumed.
- Existing process, analysis, and package outcomes remain independent of the
  evidence verdict.

## T1 — Render a complete conservative Task Contract coverage inventory

**Status:** not started

**Outcome**

A task-bound run lists every preserved requirement, acceptance criterion, and
required-verification item in one validated analysis result and all three
reports. Items begin from an honest unresolved state; merely capturing the task
does not satisfy it.

**Scope**

- add one validated coverage-assessment model keyed by existing deterministic
  run-local Task Contract IDs;
- build the inventory from the parsed task artifact already bound to the run;
- retain original section, order, text, task digest, and evidence references;
- represent absent task, invalid task, and optional empty sections without
  inventing items;
- render the same coverage inventory from the shared `AnalysisResult` in
  `SUMMARY.md`, `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`;
- update the architecture and domain glossary with the implemented states and
  their exact meanings.

**Acceptance**

- every captured `REQ-*`, `AC-*`, and `VER-*` ID appears exactly once and in
  source order in each report;
- initial coverage cannot be read as satisfaction and links back to `task.json`
  plus the task digest;
- no-task and invalid-task fixtures preserve their existing lifecycle behavior
  and cannot receive the strongest task-bounded verdict;
- all report renderers consume the same validated coverage list rather than
  reparsing the task.

**Verification**

- focused model/analyzer/report tests with minimal, full, `N/A`, invalid, and
  no-task fixtures;
- report-parity regression proving identical IDs, states, and evidence
  references;
- `uv run mypy src tests` and relevant integration tests before commit.

**Dependencies:** completed Phase 5 Task Contract capture and shared
`AnalysisResult` seam.

**Likely files:** `src/patchtrace/models/report.py`, one focused analysis module,
the three shallow report renderers/provenance helper, and focused tests. Keep
the slice medium by centralizing rendering in the existing shared helper.

**Out of scope:** relationship inference, command execution, freshness, and the
final Phase 6 verdict.

## T2 — Add conservative relationships and omitted-item detection

**Status:** not started

**Outcome**

Each coverage item shows any bounded relationship to agent claims, command
attempts, Git observations, and task evidence. Items with no relevant captured
relationship remain explicitly omitted or missing; criteria that need semantic
judgment remain assigned to the developer.

**Scope**

- define typed requirement-to-claim and requirement-to-evidence relationships
  separately from claim support;
- link only deterministic, inspectable matches with source locators;
- recognize exact required-verification command references only when the task
  item contains one unambiguous command and the captured attempt identifies the
  same command;
- allow an agent claim to be related to a task item without treating the claim
  as proof;
- keep file/path observations at the Phase 4.1 semantic ceiling;
- derive an explicit omitted/missing state when no relationship is available;
- mark natural-language behavior or acceptance judgment as human review even
  when a related claim or path exists;
- propagate the same relationships, gaps, and next action through all reports.

**Acceptance**

- fixtures cover exact command linkage, unrelated commands, one claim related
  to multiple items, multiple claims related to one item, missing items,
  conflicts, path-only material, and human-judgment criteria;
- every relationship includes a local artifact/locator and states what it does
  and does not establish;
- partial evidence never hides the unresolved part of an item;
- changing item wording cannot silently convert a semantic criterion into an
  established result.

**Verification**

- focused deterministic matching and negative-regression tests;
- integration fixture proving an omitted requirement is visible in all reports;
- `uv run mypy src tests` and the Task Contract/report suites before commit.

**Dependencies:** T1.

**Likely files:** one focused coverage analysis module, report models, shared
provenance rendering, analyzer orchestration, and focused tests.

**Out of scope:** LLM matching, embeddings, fuzzy semantic scoring, final
verification execution, and freshness.

## Checkpoint A — Coverage foundation

After T1–T2:

- run Ruff lint/format, mypy, full pytest, and build;
- dogfood one task-bound and one no-task package;
- confirm every report exposes the same complete inventory and omissions;
- independently review that no relationship is mislabeled as satisfaction;
- record the milestone in `VERIFY_LOG.md`.

## Ask-first checkpoint — Final verification interface

Before T3 implementation, pause and show the proposed CLI/task interface,
manifest shape, execution limits, failure mapping, and diff. Obtain Aga's
explicit approval because this slice executes local commands and establishes
cost/risk boundaries.

The exact command-input syntax is currently **UNKNOWN**. It must be designed
with `api-and-interface-design`, `security-and-hardening`, and
`doubt-driven-development` against these non-negotiable rules:

- prose in `task.md` and agent output is never executable authority;
- each command is explicitly supplied/confirmed by the user as argv and runs
  without a shell;
- cwd, timeout, output cap, retry cap, and network expectations are visible;
- no command runs after authorization becomes ambiguous or stale;
- interruption and partial capture are first-class outcomes;
- implementation permission does not authorize installation, spending,
  provider actions, merge, deploy, or destructive cleanup.

If no proportionate safe interface is approved, record `CANNOT VERIFY` for the
execution portion and continue only with the T1–T2 coverage capability; do not
silently downgrade this checkpoint.

## T3 — Capture one explicitly authorized final-verification command

**Status:** blocked on the ask-first checkpoint; not started

**Outcome**

After the wrapped agent process ends, the user can explicitly authorize one
bounded verification command. PatchTrace executes it without a shell and
preserves exact argv, cwd, start/end time, exit status, bounded output evidence,
termination reason, and limitations independently of the wrapped process.

**Scope**

- implement only the approved public interface and one-command vertical slice;
- record explicit authorization and the exact request in the run manifest;
- execute direct argv with an approved timeout and output cap;
- preserve truncation, signal, timeout, launch failure, and capture failure;
- keep the agent process outcome unchanged;
- make package/report failure behavior explicit and recoverable;
- never infer or execute a command from Task Contract prose or transcript text.

**Acceptance**

- success, non-zero, timeout, output-limit, signal, launch-failure, and
  no-authorization fixtures preserve distinct facts;
- shell metacharacters are passed as literal argv and never evaluated;
- a failed verification remains a complete evidence result when its artifacts
  are written successfully;
- interruption cannot produce a passing verification state;
- logs and reports exclude environment secrets and do not claim sandboxing that
  PatchTrace does not provide.

**Verification**

- focused runner tests using harmless temporary commands;
- temporary-repository integration tests for lifecycle independence and bounded
  artifacts;
- manual command-line proof of the approved UX;
- high-risk Aga verification before review/commit.

**Dependencies:** T2 and explicit approval at the ask-first checkpoint.

**Likely files:** a domain-owned verification runner/model module, CLI
orchestration, run/storage model, one report provenance helper, and focused
tests. Split the slice if it exceeds five primary files.

**Out of scope:** implicit execution, multiple commands, shell scripts,
installation, retries, remote providers, and freshness verdicts.

## T4 — Classify verification freshness against final Git identity

**Status:** not started

**Outcome**

Each required verification is classified as fresh, stale, failed, missing, or
unknown against an inspectable final Git identity. Later repository changes
cannot leave an earlier pass labeled fresh.

**Scope**

- define a deterministic final-state identity from supported captured Git facts
  without mutating the repository;
- bind the authorized verification attempt to before/after identities;
- mark a pass fresh only when it completed successfully and the analyzed final
  identity still matches its verified identity;
- mark post-check changes stale, failed exits failed, absent required attempts
  missing, and unsupported/partial identity unknown;
- treat verification commands that mutate the repository conservatively;
- expose the identity, source locators, and reason in every report.

**Acceptance**

- fixtures cover unchanged pass, later tracked edit, later untracked edit,
  commit after pass, failed command, timeout, missing command, unsupported Git
  history, and a verification command that changes the worktree;
- no timestamp alone establishes freshness;
- dirty same-path and unsupported boundaries degrade to unknown rather than
  fresh;
- all reports agree on the state and exact Git/evidence references.

**Verification**

- focused identity/freshness unit tests;
- temporary-repository integration matrix;
- `uv run mypy src tests` and relevant lifecycle/report tests before commit.

**Dependencies:** T3 and Phase 5 Git session envelope.

**Likely files:** one freshness module, validated evidence models, analyzer
orchestration, shared rendering, and focused tests.

**Out of scope:** cryptographic attestation, host sandbox guarantees, and
concurrent filesystem-event tracking.

## T5 — Produce the deterministic task-bounded verdict

**Status:** not started

**Outcome**

The shared `AnalysisResult` produces one deterministic verdict and next action
that account for task availability, complete coverage, human-review items,
required verification states, lifecycle outcomes, provenance, and the active
capture-mode ceiling.

**Scope**

- define documented precedence for lifecycle failure, invalid/missing task,
  conflicting evidence, failed/stale/unknown/missing verification, omissions,
  human review, and fully covered bounded facts;
- make the strongest verdict unavailable unless every required gate is met;
- retain explicit language that the verdict is review guidance rather than
  semantic correctness or automatic acceptance;
- render exactly one shared verdict, priority gap, and next action in all three
  reports;
- update specification, architecture, glossary, README, and ADR only with
  implemented truth.

**Acceptance**

- a table-driven fixture matrix covers every precedence branch and mixed-state
  case;
- a no-task run, degraded final output, indeterminate attribution, human-review
  criterion, or non-fresh required verification cannot receive the strongest
  verdict;
- lower-priority positive evidence cannot mask a process/package failure or
  failed required check;
- all reports are deterministic and byte-stable for the same validated result.

**Verification**

- table-driven decision tests and report-parity tests;
- integration packages for strongest-eligible and every blocking gate;
- Ruff, format, mypy, full pytest, and build before commit.

**Dependencies:** T1–T4.

**Likely files:** decision logic, report model, shared summary/provenance
rendering, integration fixtures, and matching truth documentation.

**Out of scope:** autonomous acceptance/merge, semantic code review, confidence
scores, policy configuration, and LLM judgments.

## Checkpoint B — Final verification and verdict

After T3–T5:

- rerun the complete quality gate and build from a clean candidate;
- independently verify the high-risk execution boundary and failure paths;
- code-review all public interfaces, security boundaries, compatibility, and
  report semantics;
- dogfood success, failure, timeout, mutation/staleness, missing task, and
  human-review cases;
- pause before any merge, release, or deployment.

## T6 — Close Phase 6 with a real task-bound run

**Status:** not started

**Outcome**

One real local task-bound workflow and the fixture matrix demonstrate that
coverage, omissions, authorized verification, freshness, verdict precedence,
and report parity hold together without exceeding the capture-mode ceiling.

**Scope**

- build and run the final wheel in an isolated temporary Git repository;
- use an explicit Task Contract with at least one covered item, one omitted or
  human-review item, and one required verification;
- exercise an authorized final check and a deliberate post-check freshness
  change in separate runs;
- inspect all manifests, raw artifacts, and all three reports;
- update `VERIFY_LOG.md`, close Phase 6 in `ROADMAP.md`, and activate only the
  next accepted phase in `PLAN.md`.

**Acceptance**

- every Task Contract item has a visible state and evidence links;
- missing, failed, stale, unknown, and human-review states cannot be mistaken
  for satisfaction;
- the final verdict follows the documented precedence and remains review
  guidance;
- no agent-started process remains and no test artifact contaminates the target
  repository;
- independent Aga verification and code review have no unresolved actionable
  finding.

**Verification**

- Ruff lint and format check, strict mypy, full pytest, and build;
- wheel/source identity and clean-install smoke test;
- runtime dogfood matrix with bounded artifacts and explicit cleanup proof;
- meaningful closure entry in `VERIFY_LOG.md`.

**Dependencies:** T1–T5 and both checkpoints.

**Out of scope:** merge, release, deployment, hosted execution, or publication
without separate authorization.

## Phase 6 closure criteria

- every captured requirement and acceptance criterion has a visible coverage
  state and evidence references;
- omitted items remain visible;
- natural-language criteria that need judgment are assigned to human review;
- required verification is visibly missing, failed, fresh, stale, or unknown;
- user-authorized execution is bounded, direct-argv, inspectable, and has an
  explicit failure path;
- the strongest verdict is unavailable without the required task, provenance,
  lifecycle, coverage, freshness, and capture-mode gates;
- all reports render one validated result and do not claim semantic correctness;
- full quality, runtime, independent verification, and review gates pass.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Natural-language matching overclaims satisfaction. | High | Separate relationships from satisfaction, use narrow deterministic matches, and route semantic criteria to human review. |
| Required-verification prose becomes executable input. | High | Never execute task/agent prose; require a separately approved direct-argv interface and explicit authorization. |
| A passing check becomes stale after later edits. | High | Bind it to supported Git identity and degrade unsupported or changed states. |
| Report renderers drift. | Medium | Keep one validated result and shared provenance rendering; add byte-level parity fixtures. |
| Phase 6 expands into a policy engine or sandbox. | Medium | Keep fixed V1 states/precedence and the local CLI boundary; defer configurable policy and host isolation. |
| Experimental App Server evidence leaks into production trust. | High | Preserve the Phase 5 `NO-GO`; Phase 6 consumes only implemented supported capture facts. |

## Deferred and rejected for this phase

- evidence-quality scoring and expanded review prioritization: Phase 7;
- post-hoc analyze and compatibility migration: Phase 8;
- OSS hardening and distribution: Phase 9;
- watch, Windows, second agent integration, GitHub/PR integration, HTML, LLM,
  hosted/team workflows: conditional;
- custom Codex TUI, production App Server client, private-format parsing,
  comprehensive host sandbox, predicate DSL, policy engine, event bus,
  database, and queue: rejected for Phase 6.
