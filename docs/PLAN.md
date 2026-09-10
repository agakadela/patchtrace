# Phase 5 — Trusted Capture and Session Provenance

**Status:** active; T1–T6 implemented and locally verified; T6a and T7 not started

**Baseline:** Phase 4.1 — Trust Hardening closed on 2026-09-08.
Closure evidence: [VERIFY_LOG.md](VERIFY_LOG.md#2026-09-08---phase-41-close-trust-hardening).

**Next task:** T6a — Update the local Codex CLI and close the real-response verification gap.

**Roadmap:** [ROADMAP.md](ROADMAP.md)

The previously accepted Phase 5 task scope is unchanged. This file is the
single owner of active tasks; Phase 4.1 completion is recorded in the verification log.

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

**Status:** implemented and locally verified. Capture format and limits:
[ARCHITECTURE.md](ARCHITECTURE.md#29-git-session-envelope--phase-5-t1).
Evidence: [VERIFY_LOG.md](VERIFY_LOG.md).

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

**Status:** implemented and locally verified. Result contract and limits:
[ARCHITECTURE.md](ARCHITECTURE.md#210-git-attribution--phase-5-t2).
Evidence: [VERIFY_LOG.md](VERIFY_LOG.md).

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

**Status:** implemented and locally verified. Report contract and limits:
[ARCHITECTURE.md](ARCHITECTURE.md#211-report-provenance--phase-5-t3).
Evidence: [VERIFY_LOG.md](VERIFY_LOG.md).

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

**Status:** implemented and locally verified. Lifecycle mapping, CLI exits, and
Phase 4 compatibility decision:
[ARCHITECTURE.md](ARCHITECTURE.md#212-lifecycle-outcomes--phase-5-t4).
Evidence: [VERIFY_LOG.md](VERIFY_LOG.md).

### Outcome

A developer can tell independently what happened to the command, whether
analysis was usable, and whether the package was written.

### Scope

- replace the combined lifecycle meaning with process, analysis, and package
  outcomes;
- preserve evidence verdict as a separate concern;
- define the smallest explicit failure mapping for current capture, analysis,
  and write paths;
- keep CLI exit behavior documented and testable.

### Acceptance

- successful process plus degraded analysis is representable;
- partial or failed package writes cannot be reported as a complete package;
- reports and manifest do not confuse lifecycle facts with verdict;
- the model can be extended by later tasks without T4 inventing task-parsing or
  task-delivery reason catalogs;
- no workflow state machine is introduced.

### Verification

- model validation tests;
- fake-command success and non-zero exit cases;
- current missing/ambiguous transcript-analysis and injected package failure
  cases;
- backwards-compatibility decision for Phase 4 fixtures recorded in the task
  commit.

### Out of scope

Retries, queues, resumable workflows, or orchestration state machines.

## T5 — Capture Task Contract V1

**Status:** implemented and locally verified. Syntax, artifacts, and failure mapping:
[ARCHITECTURE.md](ARCHITECTURE.md#213-task-contract-v1-capture--phase-5-t5).
Evidence: [VERIFY_LOG.md](VERIFY_LOG.md).

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
- add only the task-parsing reason mappings required by these new paths;
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

## T6 — Establish the interactive Codex boundary and deliver the same task

**Status:** implemented and locally verified. Boundary and limits:
[ARCHITECTURE.md](ARCHITECTURE.md#214-interactive-codex-boundary--phase-5-t6).
Evidence, including the local CLI/model compatibility limit:
[VERIFY_LOG.md](VERIFY_LOG.md#2026-09-09---phase-5-t6-interactive-codex-task-delivery).

### Outcome

The user supplies the task once; the existing interactive Codex workflow uses
the preserved raw artifact as its initial prompt source and records honest
delivery evidence without changing the PTY experience.

### Scope

- add the concrete Codex-specific boundary with the interactive implementation;
- preserve the current PTY interaction and generic wrapped-command promise;
- submit prompt material from the preserved artifact rather than a re-rendered
  parse;
- record delivery mode, artifact digest, attempted boundary, confirmation, and
  limitations in the manifest;
- move Codex TUI rules, marker-based final-output extraction, and
  Codex-specific evidence locators out of generic session and analysis code;
- add only the task-delivery reason mappings required by the new interactive
  path.

### Acceptance

- the prompt source and preserved task artifact have the same digest;
- tests assert the nearest reliable invocation or stdin boundary the official
  interactive transport exposes;
- no test or report claims byte-for-byte receipt when it is unobservable;
- no result claims that Codex or the model understood the task;
- generic session and analysis code contain no Codex-specific final markers or
  Codex TUI interpretation rules;
- the concrete boundary owns final-output selection and Codex evidence
  locators without creating a plugin registry or empty adapter abstraction;
- generic commands retain task material for analysis and mark delivery
  unverified;
- the normal interactive Codex PTY experience remains intact.

### Verification

- fake interactive Codex executable tests for argument/stdin boundaries, TUI
  markers, and delivery failures;
- ownership tests for Codex final-output extraction and evidence locators;
- one real interactive Codex task-delivery dogfood where locally supported.

### Out of scope

Production `codex exec --json`, a JSONL parser, structured-task dogfood, App
Server integration, automatic replacement of interactive UX, private Codex
formats, generic agent plugins, and full requirement evaluation.

`codex exec --json` remains an accepted candidate for a separate slice. It can
enter Phase 5 only after separate human approval or a concrete dogfood trigger
and does not depend on the Task 7 App Server result.

## T6a — Update the local Codex CLI and close the real-response verification gap

**Status:** not started; planning only. No CLI update has been executed.

**Type:** local environment maintenance and T6 runtime follow-up, before T7.
This task does not redefine T6 acceptance or expand the Phase 5 product scope.

### Outcome

The terminal's active Codex CLI can use the configured `gpt-6-astra` model, and
one task-bound PatchTrace interactive session produces a real model response
while retaining honest delivery and final-output limitations.

### Starting evidence

- T6 wheel run `20260910T012924798118Z-bf273c37` displayed the task in the TUI,
  then received a model/CLI compatibility error requiring a newer Codex version.
- Observed on 2026-09-09: `codex-cli 0.144.1`; shell entry
  `/Users/coderwoman/.local/bin/codex` resolves through
  `/Users/coderwoman/.codex/packages/standalone/current/bin/codex`.
- Installed `codex update --help` exposes standalone self-update. The
  [official update reference](https://learn.chatgpt.com/docs/developer-commands#codex-update)
  documents self-update for supported releases.
- Target version: **UNKNOWN** until checked against the official stable release
  available at execution time; do not infer it from an old update notification.

### Scope and execution order

1. Recheck the active binary, resolved installation path, installed version,
   available stable release, and official update instructions. Record the exact
   original release path and supported way to restore the previous CLI binary
   if the update breaks startup; do not treat a downgrade as proof that the
   current model will work.
2. Update this standalone installation through its supported `codex update`
   path. Verify the version and resolved path again in a fresh shell so a stale
   binary elsewhere in PATH cannot impersonate a successful update.
3. Use an identified PatchTrace commit/wheel in a temporary Git repository.
   Supply a small Task Contract once through
   `patchtrace run --codex --task-file task.md -- codex`. Use the configured
   `gpt-6-astra`, a read-only session, and a text-only task requiring no tools,
   file changes, browsing, or delegation. Obtain the response and send one short
   interactive follow-up; then exit and inspect the package.
4. Record exact CLI version/path, PatchTrace commit and wheel digest, task digest,
   run ID, observed response/follow-up, lifecycle fields, and remaining limits
   in `docs/VERIFY_LOG.md`. Update this task's status from the observed result.
   Close all processes started for the test.

### Acceptance

- The active CLI uses the recorded updated release and `gpt-6-astra` produces a
  response without the previously observed version-compatibility error. A
  changed version string alone does not satisfy this criterion.
- The task-bound interactive session accepts a follow-up, exits, and produces
  its review package. Raw task and prompt digests agree; delivery confirmation,
  process outcome, analysis outcome, and package outcome reflect the observations.
  A missing final marker may still degrade analysis and must remain visible.
- Evidence is tied to the tested binary and PatchTrace snapshot. No model
  substitution, weakened check, authentication reset, or change to user
  configuration/skills/plugins is used to manufacture success. On a new blocker,
  record its exact boundary and leave this task incomplete.

### Verification and separate gates

- Inspect pre/post `command -v codex`, resolved path, `codex --version`, and
  relevant `--help`; use current official release/update documentation.
- Run one bounded real interactive task and follow-up from the identified
  PatchTrace build. Retain sanitized runtime evidence and inspect all three
  reports; do not infer authenticated message provenance or understanding from
  a sensible model response.
- `aga-verify-agent`: assess these acceptance criteria against the versioned
  runtime evidence, distinguishing actual observations from agent claims.
- Code review: **N/A if no executable project code changes**. Review any
  separately authorized compatibility fix through its own implementation task;
  a CLI update does not justify a ceremonial second code review of unchanged code.
- Documentation-only results require readback and evidence/link checks. If a
  code fix becomes necessary, stop this maintenance scope and specify the fix
  with a failing reproduction and normal project test/review gates.

### Out of scope

Updating the desktop app or IDE extension, changing model/provider selection,
editing auth/config/skills/plugins, upgrading project dependencies, changing
PatchTrace source, introducing `codex exec --json` or App Server, and merge/deploy.
The current request authorizes writing this task; execution follows a separate
instruction to perform it.

### Expected change size

One local CLI installation; repository evidence/status updates in
`docs/VERIFY_LOG.md` and `docs/PLAN.md`. Runtime duration depends on installation
and provider availability; no estimate is treated as a completion guarantee.

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
