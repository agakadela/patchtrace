# Phase 5 Plan — Trusted Capture and Session Provenance

**Status:** ready for implementation

**Baseline:** Phase 4 complete

**Roadmap:** [ROADMAP.md](ROADMAP.md)

Work on one task at a time. Each task must end in a user-visible, fixture-backed
slice and a commit. Do not implement Phase 6 requirement satisfaction in this
phase.

## Phase goal

Make the local run package honest about task, Git, lifecycle, and capture
provenance before expanding what PatchTrace evaluates.

Phase 4 dogfooding confirmed the first priority: identical before/after Git
status material was interpreted as five run changes. T1–T3 repair that false
positive without waiting for App Server research.

## T1 — Capture the Git session envelope

### Outcome

The run package preserves enough non-mutating Git facts to distinguish a
session boundary from a final worktree snapshot.

### Scope

- capture `HEAD` before and after;
- record initial and final clean/dirty state;
- retain bounded initial facts needed to recognize pre-existing paths;
- capture previously clean tracked files changed during the run;
- capture new untracked files and their evidence;
- capture commits made in a straightforward before/after history range;
- record explicit limitations for non-linear or unsupported cases.

### Acceptance

- clean-to-modified, new-untracked, pre-existing-dirty, and in-run-commit
  fixtures preserve the expected raw facts;
- capture never mutates the worktree, index, branch, or history;
- `.patchtrace/` artifacts do not contaminate repository evidence;
- capture failure has an actionable, preserved failure path.

### Verification

- focused `vcs` unit tests;
- temporary-repository integration matrix;
- mypy and relevant existing run tests.

### Out of scope

Attribution labels, report rendering, dirty same-path byte separation, partial
commit reconstruction, sparse checkout, submodules, and nested repositories.

## T2 — Apply honest Git attribution

### Outcome

One analysis result classifies captured Git material as
`session-attributed`, `pre-existing`, or `indeterminate`.

### Scope

- derive attribution only from T1 facts;
- treat previously clean files changed during the run, new untracked files, and
  straightforward in-run commits as session-attributed;
- keep known initial material pre-existing;
- keep dirty same-path or inseparable history indeterminate;
- add evidence references and limitations to the validated result.

### Acceptance

- the Phase 4 false-positive regression reports identical before/after dirty
  material as pre-existing, not session-attributed;
- no class implies byte-level agent authorship;
- unsupported history shapes degrade to `indeterminate` rather than guessing;
- the existing single `AnalysisResult` seam remains intact.

### Verification

- fixture matrix for all three classes;
- clean, dirty-same-path, unchanged-dirty, untracked, and committed integration
  cases;
- focused analyzer tests.

### Out of scope

Hunk authorship, stashing, temporary commits, reflog forensics, and advanced
reconstruction.

## T3 — Propagate provenance across reports

### Outcome

Summary, agent feedback, and verification brief present the same Git attribution
and limitations from one analysis result.

### Scope

- add shallow report views for attribution and source references;
- remove independent changed-file interpretations from renderers;
- update review-first input to use shared provenance;
- make pre-existing and indeterminate material visible and actionable.

### Acceptance

- all three reports agree on attribution counts, paths, and limitations;
- no report calls pre-existing work a run change;
- renderers do not read raw Git artifacts or recompute attribution;
- the existing report purpose and concise next-action behavior remain.

### Verification

- golden or structured report assertions from the same fixtures;
- cross-report consistency test;
- real local dogfood with a dirty starting worktree.

### Out of scope

Requirement coverage, new risk scoring, and general review prioritization.

## T4 — Separate process, analysis, and package outcomes

### Outcome

A developer can tell independently what happened to the command, whether
analysis was usable, and whether the package was written.

### Scope

- replace the combined lifecycle meaning with process, analysis, and package
  outcomes;
- preserve evidence verdict as a separate concern;
- define the smallest explicit failure mapping for current capture, parsing,
  analysis, and write paths;
- keep CLI exit behavior documented and testable.

### Acceptance

- successful process plus degraded analysis is representable;
- task parsing or delivery failure can be represented without overloading
  process outcome;
- partial or failed package writes cannot be reported as a complete package;
- reports and manifest do not confuse lifecycle facts with verdict;
- no workflow state machine is introduced.

### Verification

- model validation tests;
- fake-command success and non-zero exit cases;
- injected analysis and package failure cases;
- backwards-compatibility decision for Phase 4 fixtures recorded in the task
  commit.

### Out of scope

Retries, queues, resumable workflows, or orchestration state machines.

## T5 — Capture Task Contract V1

### Outcome

PatchTrace preserves and binds the developer's task to the run without yet
claiming requirement satisfaction.

### Scope

- add the smallest discoverable CLI task-file input;
- preserve the raw Markdown artifact unchanged;
- compute and store its digest in the manifest;
- require `Outcome` and `Requirements`;
- allow omitted or explicit `N/A` for `Acceptance Criteria`,
  `Required Verification`, and `Out of Scope`;
- parse simple ordered items with deterministic run-local IDs;
- link raw and parsed task material to the run;
- allow a run without a task with an explicit trust limitation.

### Acceptance

- the stored raw artifact matches the supplied artifact exactly;
- generated IDs are stable for that artifact and are not documented as stable
  across edits;
- invalid provided task material produces an explicit parsing and lifecycle
  result rather than silent rewriting;
- a missing task still permits the existing generic run;
- no requirement-satisfaction inference occurs.

### Verification

- valid, optional-section, explicit-`N/A`, invalid, duplicate-heading, and
  no-task fixtures;
- digest and exact-preservation tests;
- CLI integration test for generic task capture.

### Out of scope

Predicate syntax, `all`/`any` expressions, policy evaluation, semantic matching,
and coverage verdicts.

## T6 — Deliver the same task through Codex-specific modes

### Outcome

The user supplies the task once; supported Codex-specific modes use the
preserved raw artifact as the initial prompt source and record honest delivery
evidence.

### Scope

- add an explicit Codex interactive task path without changing the generic
  wrapped-command promise;
- add optional `codex exec --json` structured task mode;
- submit prompt material from the preserved artifact rather than a re-rendered
  parse;
- record delivery mode, artifact digest, attempted boundary, confirmation, and
  limitations in the manifest;
- interpret only documented structured event types needed by the run;
- map delivery failures into the T4 lifecycle model.

### Acceptance

- the prompt source and preserved task artifact have the same digest;
- tests assert the nearest reliable invocation, stdin, or event boundary the
  official transport exposes;
- no test or report claims byte-for-byte receipt when it is unobservable;
- no result claims that Codex or the model understood the task;
- generic commands retain task material for analysis and mark delivery
  unverified;
- structured task mode remains separate from interactive PTY.

### Verification

- fake Codex executable tests for argument/stdin boundaries and failures;
- official structured-event fixtures for final messages, commands, file
  changes, and lifecycle;
- one real structured task dogfood where locally supported.

### Out of scope

Automatic replacement of interactive UX, private Codex formats, generic agent
plugins, and full requirement evaluation.

## T7 — Time-box App Server structured-interactive feasibility

### Outcome

A small prototype records `GO`, `NO-GO`, or `CANNOT VERIFY` for using official
App Server evidence with the same interactive session.

### Time box

One focused engineering day. Stop sooner on a conclusive `NO-GO`.

### Questions

1. Do typed final-message, command-result, file-change, and lifecycle events
   exist?
2. Are they emitted for the same session the user operates interactively?
3. Can PatchTrace obtain them officially without building its own client?
4. Are the required transport and fields stable for production use?
5. What minimum integration code and maintenance burden would be required?

### Acceptance

- evidence uses current official documentation, CLI help/schema, or official
  source for the detected version;
- each question has an observed answer, limitation, and source;
- `GO` requires the same interactive session, required typed events, a stable
  official surface, and proportionate integration cost;
- needing a custom TUI, large protocol proxy, or private format is `NO-GO`;
- unknown access or stability after the time box is `CANNOT VERIFY`;
- prototype code is clearly throwaway and is not presented as a production
  adapter;
- ADR-0003 and the architecture are updated only with the confirmed result.

### Verification

- minimal end-to-end observation if the official surface permits it;
- captured schema/event examples with sensitive data excluded;
- written cost estimate and decision against the five questions.

### Out of scope

A production App Server integration, custom terminal UI, full Codex client,
protocol proxy, private-format parsing, or UX redesign.

## Phase 5 closure

Before closing the phase:

- run Ruff lint and format check, mypy, full pytest, and build;
- dogfood clean, dirty, committed, failed, no-task, and task-bound runs;
- record the milestone in `VERIFY_LOG.md`;
- confirm all reports obey the capture mode's trust ceiling.

App Server `NO-GO` or `CANNOT VERIFY` does not block closure. In that case:

- interactive PTY remains marker-based compatibility mode;
- missing or ambiguous marker degrades final-output evidence;
- transcript-tail guessing remains prohibited;
- there is no structured-interactive high-trust final output;
- reports and verdicts preserve that limitation.

Phase 5 must not be described as complete final-output provenance unless a
supported structured-interactive path was actually delivered.

## Deferred and rejected for this phase

- requirement satisfaction and final verification: Phase 6;
- evidence-quality scoring and expanded review-first logic: Phase 7;
- post-hoc analyze: Phase 8;
- watch, Windows, second agent integration, GitHub, HTML, LLM, hosted workflows:
  conditional;
- custom TUI, large protocol proxy, private Codex formats, advanced Git
  forensics, predicate DSL, policy engine, event bus, database, and queue:
  rejected for Phase 5.
