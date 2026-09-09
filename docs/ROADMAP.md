# PatchTrace Roadmap

**Baseline:** Phase 4.1 complete

**Active phase:** Phase 5 — Trusted Capture and Session Provenance

This roadmap orders product capabilities by evidence dependency. [PLAN.md](PLAN.md)
owns the active phase and its tasks. Phase 4.1 closure evidence is recorded in
[VERIFY_LOG.md](VERIFY_LOG.md#2026-09-08---phase-41-close-trust-hardening).

## Phase 4.1 — Trust Hardening

### Problem

The Phase 4 baseline can overconfirm file/change claims, use an earlier command
result instead of the latest attempt, and expose run artifacts to accidental
staging in the reviewed repository.

### User value

Existing evidence labels stay within what captured material establishes, and
local session material stays outside the repository working tree.

### Main capabilities

- default artifact storage outside the working tree with repository association
  and a discoverable package location;
- separate observed file facts from semantic claims, including operation types
  and every target in multi-file claims;
- latest-command-attempt assessment with prior history, explicit unknown results,
  correct zero-failure parsing, and failed verification surfaced in next actions.

### Dependencies and exit criteria

Closed on 2026-09-08: T1 storage containment, T2 file/change assessment, and
T3 command-attempt semantics passed the merged-baseline closure checks.
Evidence and remaining trust limits are recorded in [VERIFY_LOG.md](VERIFY_LOG.md).

### Out of scope

Semantic correctness, requirement satisfaction, verification freshness,
structured command events, LLM analysis, and changes to Phase 5 Git-provenance
scope remain outside this phase.

## Phase 5 — Trusted Capture and Session Provenance

**Status:** active; T1–T4 implemented. Next task: T5 — Capture Task Contract V1.

**Active tasks:** [PLAN.md](PLAN.md).

### Problem

The phase began with packages mistaking pre-existing work for run changes and
conflating lifecycle outcomes. T1–T4 address those gaps. The remaining work has
no preserved task yet and obtains final-output and command evidence from a
marker-based PTY transcript.

### User value

The developer can see what evidence belongs to the captured session, what does
not, and what remains uncertain before relying on later analysis.

### Main capabilities

- a non-mutating Git capture envelope and honest attribution;
- provenance propagated consistently through analysis and reports;
- separate process, analysis, and package outcomes;
- Task Contract V1 capture and run binding;
- a concrete interactive Codex boundary for task delivery and TUI
  interpretation;
- the preserved raw task artifact as the sole interactive Codex prompt source;
- a time-boxed App Server feasibility prototype for structured-interactive
  capture;
- real dogfooding of clean, dirty, committed, failed, and degraded runs.

### Dependencies

Phase 4's validated `AnalysisResult`, deterministic report pipeline, local run
storage, and PTY recorder, with Phase 4.1 trust hardening completed.

Git provenance and lifecycle outcomes do not depend on Codex research. Task
capture does not depend on full requirement evaluation.

### Exit criteria

- confirmed pre-existing changes are never reported as session-attributed;
- clean-to-changed files, new untracked files, and in-run commits are captured;
- dirty same-path ambiguity is reported as `indeterminate`;
- every report uses the same attribution and lifecycle facts;
- raw Task Contract input is preserved, digest-bound, parsed, and linked to the
  run;
- Codex-specific delivery records the supported transport boundary it can
  actually confirm;
- generic session and analysis code contain no Codex TUI markers or
  interpretation rules;
- the App Server prototype records `GO`, `NO-GO`, or `CANNOT VERIFY` against
  explicit criteria;
- the PTY trust ceiling remains explicit if structured-interactive capture is
  not delivered.

Phase 5 may close with an App Server `NO-GO` or `CANNOT VERIFY`. In that case,
PTY remains marker-based compatibility mode, there is no structured-interactive
high-trust final output, and reports and verdicts must respect that ceiling.

### Out of scope

- full requirement satisfaction;
- advanced Git forensics or hunk authorship;
- a custom Codex TUI, large protocol proxy, or private-format integration;
- a production `codex exec --json` mode, JSONL parser, or structured-task
  dogfood in the current plan;
- final verification freshness;
- a generic adapter framework.

### Plan-change triggers

Change the plan only if dogfooding disproves the attribution model, an official
Codex surface changes materially, or the prototype shows that a small supported
integration can preserve the same interactive session.

`codex exec --json` remains an accepted candidate for a separate slice. It may
enter Phase 5 only after separate human approval or a concrete dogfood trigger;
it does not depend on the App Server result.

## Phase 6 — Task Coverage and Final Verification

### Problem

Claims selected by an agent are not a substitute for evaluating the requested
outcome, requirements, and required checks. A check can also become stale after
later changes.

### User value

The developer receives a task-anchored recommendation based on requirement
coverage and verification of the final analyzed state.

### Main capabilities

- requirement and acceptance-criterion coverage;
- explicit omitted-requirement detection;
- requirement, claim, and evidence relationships;
- user-authorized final verification with bounded execution evidence;
- freshness classification against final Git state;
- deterministic verdict and next action within the Task Contract.

### Dependencies

Trusted task, Git, lifecycle, and evidence provenance from Phase 5.

### Exit criteria

- every captured requirement has a visible coverage state and evidence links;
- natural-language criteria that need judgment are marked for human review;
- required verification is missing, failed, fresh, stale, or unknown;
- the highest verdict is unavailable without the required contract and gates;
- no verdict claims semantic correctness.

### Out of scope

- a predicate DSL or policy engine;
- a comprehensive host security sandbox;
- semantic code review by an LLM.

### Plan-change triggers

Add stronger execution isolation only when a real command-risk case or public
release requirement demonstrates the need.

## Phase 7 — Evidence Quality and Review Prioritization

### Problem

Evidence can be present but irrelevant, stale, scope-drifting, or too weak to
guide review efficiently.

### User value

The developer starts with the most consequential conflict or gap instead of
manually sorting a complete evidence package.

### Main capabilities

- deterministic evidence-quality checks;
- test relevance and unrelated-check signals;
- scope-drift detection;
- review prioritization across conflicts, omissions, verification gaps, and
  uncertain attribution;
- only dogfood-proven extensions to difficult Git cases.

### Dependencies

Task coverage and freshness from Phase 6.

### Exit criteria

- review order is explainable and traceable to captured facts;
- weak evidence is not promoted merely because it exists;
- prioritized reports remain shallow views of one analysis result;
- new Git complexity is backed by real examples.

### Out of scope

- general-purpose code quality scoring;
- automatic repair or acceptance;
- speculative Git forensics.

### Plan-change triggers

Expand prioritization only when observed review sessions show a repeatable
decision bottleneck.

## Phase 8 — Post-Hoc Analyze

### Problem

Developers need to revisit saved evidence and sometimes inspect a branch,
commit, or patch that lacks a captured live session.

### User value

They can re-run improved deterministic analysis without rerunning the agent and
can still obtain limited guidance for uncaptured work.

### Main capabilities

- re-analysis of a version-compatible saved run package;
- explicit compatibility and migration behavior;
- limited branch, commit, or patch analysis;
- a lower trust ceiling when task, session, command, or lifecycle evidence is
  absent.

### Dependencies

Stable run artifacts and analysis boundaries from Phases 5–7.

### Exit criteria

- saved runs can be analyzed reproducibly under a declared version contract;
- post-hoc inputs never masquerade as captured-session evidence;
- missing provenance produces explicit limitations and a lower verdict ceiling.

### Out of scope

- reconstructing an agent session from Git history;
- hosted package storage;
- continuous watch mode.

### Plan-change triggers

Introduce migrations only when an actual saved-package compatibility break must
be supported.

## Phase 9 — OSS Readiness

### Problem

A useful local prototype still needs a safe, understandable distribution and
support contract before external adoption.

### User value

An external developer can install PatchTrace, understand its privacy and trust
boundaries, run a documented workflow, and report a reproducible issue.

### Main capabilities

- installable package metadata and release automation;
- license, contribution, support, and compatibility policies;
- privacy and local-data documentation;
- concise examples and first-run guidance;
- release-level testing on the supported platform;
- validation with at least one real external user.

### Dependencies

A useful end-to-end local workflow from prior phases.

### Exit criteria

- a clean environment can install and run the supported workflow;
- public documentation matches actual behavior and limitations;
- package and Python compatibility are declared and tested;
- privacy implications are explicit;
- one external user completes the core flow.

### Out of scope

- SaaS, accounts, billing, teams, or hosted workflows;
- broad platform support without maintainable test coverage.

### Plan-change triggers

Add platform or integration commitments only in response to demonstrated user
demand and a maintainable verification path.

## Conditional capabilities

The following are not committed phases:

- continuous `watch`;
- Windows support;
- a second agent integration;
- GitHub or pull-request integration;
- an HTML viewer;
- optional LLM assistance;
- hosted or team workflows.

Each requires a concrete user problem, evidence that the existing CLI is
insufficient, and a proportionate implementation and verification plan.
