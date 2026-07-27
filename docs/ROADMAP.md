# PatchTrace Roadmap

Canonical source of truth for the complete product sequence: completed
foundations, committed future capabilities, dependencies, phase exit criteria,
conditional capabilities, and plan-change triggers.

- `docs/SPEC.md` defines the product and success contract.
- `docs/PLAN.md` expands only the active/proposed phase into implementation
  tasks.
- `docs/ARCHITECTURE.md` defines current and target system design.
- `docs/VERIFY_LOG.md` records verified milestones after they close.

The roadmap is not a release-date promise. It is the dependency-ordered path to
the confirmed production product.

## Status Legend

| Status | Meaning |
|---|---|
| `N/A` | The repository has no accepted milestone with this phase number. |
| `complete` | Exit criteria were implemented and recorded in verification history. |
| `close pending` | Implementation exists on an open PR and has not landed on the default branch. |
| `proposed next` | Product intent is confirmed; architecture/plan approval is required before implementation. |
| `planned` | Committed product capability whose detailed plan is intentionally deferred. |
| `conditional` | Known capability that enters the committed sequence only after its trigger exists. |

## Product End State

PatchTrace is complete as a product when a local developer can:

1. give PatchTrace one explicit Markdown task;
2. let PatchTrace deliver that task to Codex under a versioned structured
   response contract;
3. capture one trusted run without mixing prior repository work into the
   session delta;
4. execute required final verification against the final repository state;
5. receive a decisive task-fulfillment verdict and paste-ready feedback;
6. re-analyze compatible saved runs;
7. keep PatchTrace watching selected repositories for later sessions;
8. install and operate the tool through a documented OSS distribution on
   supported platforms.

General code review, autonomous fixes/merges, SaaS, and required LLM analysis are
not part of this end state.

## Dependency Map

```text
Phase 1  Foundation
   -> Phase 2  CLI + local evidence scaffold
   -> Phase 3  Real interactive Codex dogfood + three-report package
   -> Phase 4  Explicit claim assessment
   -> Phase 5  End-to-End Trusted Run
   -> Phase 6  Evidence Quality + Review Prioritization
   -> Phase 7  Post-Hoc Analyze + Compatibility
   -> Phase 8  Local Continuous Watch
   -> Phase 9  OSS + macOS/Linux Distribution
   -> Phase 10 Windows Portability

Conditional capabilities attach only after their named trigger.
```

## Current Position

- Default branch: Phase 3 plus landed Phase 4 task work through PR #18.
- Open Phase 4 closeout: PR #19 at commit `d8c98c4`.
- Product re-baseline: proposed documentation stacked on PR #19.
- Next implementation: Phase 5 only after the re-baseline, roadmap,
  architecture, and proposed ADRs receive human approval.

Do not mark Phase 5 current or ADR-0002 through ADR-0005 accepted merely because
their documentation exists.

## Historical Phases

### Phase 0 — N/A

**Status:** `N/A`

The Python repository has no accepted Phase 0 milestone. Recorded project phase
history begins with Phase 1. This entry is explicit so the roadmap does not
invent missing history or leave numbering ambiguous.

`docs/patchtrace_phase0_design.md` is retained as superseded historical design
input; its title does not make it a verified product milestone.

### Phase 1 — Python V0 Spec And Foundation Decisions

**Status:** `complete`

**Problem:** The project needed a coherent local-CLI foundation before any
implementation.

**Value delivered:**

- confirmed Python >=3.11 local CLI direction;
- selected `uv`, Typer, Pydantic, Pexpect, pytest, Ruff, and mypy;
- selected `src/patchtrace/<capability>` module ownership;
- documented local-first privacy and no-required-LLM boundaries;
- accepted ADR-0001.

**Verification:** `docs/VERIFY_LOG.md`, entry
`2026-07-02 - Python V0 Foundation Spec`.

**Known limitation at close:** No scaffold or runtime flow existed.

### Phase 2 — Feedback Loops And CLI Scaffold

**Status:** `complete`

**Problem:** The documented foundation had no executable feedback loop.

**Value delivered:**

- installable CLI scaffold;
- fake-command PTY recording;
- local run manifest and transcript;
- first Git before/after evidence;
- minimal summary report;
- local and CI quality gates.

**Verification:** `docs/VERIFY_LOG.md`, entry
`2026-07-06 - Phase 2 Close`.

**Known limitation at close:** No real Codex run, complete report package, or
claim assessment.

### Phase 3 — Real Codex Dogfood Walking Skeleton

**Status:** `complete`

**Problem:** Fake capture did not prove that the CLI could preserve a real Codex
workflow or produce useful review artifacts.

**Value delivered:**

- interactive Codex PTY passthrough;
- full nine-artifact local run folder;
- `SUMMARY.md`, `AGENT_FEEDBACK.md`, and `VERIFICATION_BRIEF.md`;
- real local Codex dogfood proof.

**Verification:** `docs/VERIFY_LOG.md`, entry
`2026-07-08 - Phase 3 Close`.

**Known limitation at close:** Reports described evidence but did not
systematically assess explicit final claims.

### Phase 4 — Explicit Claim Assessment

**Status:** `close pending`

**Problem:** Evidence existed, but PatchTrace could not relate bounded explicit
agent claims to files, changes, commands, and results.

**Value delivered:**

- transcript cleanup and one identifiable final-output region;
- bounded file/change/test/command claim extraction;
- deterministic claim-versus-evidence relationships;
- one shared `AnalysisResult`;
- one quick decision, evidence gaps, and next action across all reports;
- sanitized fixture matrix and real Codex CLI 0.144.1 dogfood.

**Verification:** `docs/VERIFY_LOG.md`, entry
`2026-07-12 - Phase 4 Close`; open PR #19.

**Known limitations driving Phase 5:**

- task and prompt delivery are not bound;
- TUI marker parsing remains fragile;
- final worktree evidence is not a complete session delta;
- dirty/untracked/committed-during-run attribution is incomplete;
- command/test results are text-derived and can be stale;
- no requirement completeness or final-state verification exists;
- wrapped process, analysis, and package outcomes are not separate.

## Committed Product Phases

### Phase 5 — End-to-End Trusted Run

**Status:** `proposed next`

**Problem**

Phase 4 can assess selected self-reported claims but cannot decide whether Codex
fulfilled the complete task. It also cannot prove that the final output,
repository delta, and passing checks belong to the same final run state.

**User value**

The primary user supplies one task once and receives a production-quality,
evidence-backed `ready_to_accept`, `send_back`, `review_required`,
`rerun_required`, or `cannot_assess` decision.

**Dependencies**

- Phase 4 claim-assessment seam and three report renderers;
- accepted product spec and roadmap;
- approved ADR-0002 through ADR-0005;
- documented Codex `exec` JSONL, final-message, and output-schema behavior;
- existing Python stack, Git CLI, and fixture-first workflow.

**Capabilities**

- fixed-section Markdown task contract with closed `REQ-*`, `AC-*`, `VER-*`,
  and `OOS-*` semantics plus closed typed acceptance-evidence predicates;
- unchanged user task payload plus versioned PatchTrace execution/response
  protocol;
- canonical structured `codex exec` trusted mode under a recorded controlled
  security/effect-scope profile;
- supervised Codex and verification process trees with quiescent terminal
  checkpoints;
- interactive Codex as a secondary, explicitly weaker mode;
- private Git-metadata run storage and durable lifecycle manifest;
- separate wrapped-command, analysis, and package outcomes;
- bounded clean/dirty/staged/unstaged/untracked/commit baseline, agent-end, and
  verification-end capture;
- session-scoped Git attribution, including changes made after a private dirty
  baseline;
- non-refreshing Git collection that preserves index bytes and semantic state;
- final execution of user-authorized required verification commands;
- repository-state freshness and separate verification-phase deltas;
- deterministic requirement coverage and structured agent claims;
- one closed failure/outcome/verdict mapping, decisive next action, and three
  aligned reports.

**Exit criteria**

- all Phase 5 `docs/PLAN.md` task acceptance criteria pass;
- one task file is both bound evaluation input and unchanged Codex task payload;
- structured final response addresses every `REQ-*` and `AC-*`, and only a
  successful canonical Codex terminal outcome proceeds to fulfillment analysis;
- every acceptance criterion has a valid closed deterministic Git/artifact or
  `VER-*` predicate, or correctly selects `review_required` for declared human
  inspection;
- trusted Codex runs prove their effective writable scope and have no
  unaccounted command hook, notifier, MCP/plugin writer, network policy,
  inherited environment/credential exposure, temp path, or writable root;
- dirty baseline fixtures separate pre-existing and session-attributed content,
  including staged/unstaged material committed during the run;
- Git collection preserves index bytes and semantic repository state;
- required verification runs after agent capture against the final analyzed
  state under a recorded default-deny network/environment/credential/temp/
  writable-root effect profile;
- Codex and verification descendants are contained/reaped and terminal
  snapshots are quiescent; a delayed/background/detached writer cannot coexist
  with `ready_to_accept`;
- relevant verification-phase changes remain separate from the agent delta
  and select `send_back`;
- failure-class to analysis-outcome to verdict mapping is fixture-proven and
  report-independent;
- partial failures leave a truthful manifest and bounded artifacts;
- storage, command execution, untrusted Markdown, second-order prompt injection,
  symlink, special-file, timeout, output-limit, and mutation failure paths are
  tested;
- full lint, format, typecheck, test, and build gates pass;
- three real dogfood scenarios pass: clean accept, dirty attribution, and a
  non-accept failure path;
- the project owner confirms the reports make the right next decision.

**Out of scope**

- generic code review or semantic bug finding;
- review-priority scoring beyond the decisive verdict reasons;
- saved-run/import CLI;
- continuous watch;
- public package release;
- non-Codex adapters;
- LLM analysis or external services;
- Windows support.

**Plan-change triggers**

- official Codex structured output cannot reliably represent requirement-level
  final claims;
- dirty baseline cost or behavior makes normal repositories unusable;
- Markdown authoring is too expensive in three real dogfood runs;
- final verification commands cannot be executed safely under the approved
  authorization model;
- supported macOS primitives cannot enforce process containment and quiescent
  checkpoint semantics without a newly approved dependency or architecture
  change;
- representative trusted tasks require network or external-writer effects that
  the Phase 5 controlled profile intentionally excludes;
- deterministic requirement coverage produces a misleading
  `ready_to_accept`.

**Detailed plan:** `docs/PLAN.md`.

### Phase 6 — Evidence Quality And Review Prioritization

**Status:** `planned`

**Problem**

A correct verdict can still leave the user inspecting evidence in a poor order.
Phase 4 primarily orders changed files, while a production review should start
at the most consequential gap, conflict, scope violation, or uncertain change.

**User value**

When the verdict is not `ready_to_accept`, PatchTrace points directly to the
smallest set of evidence that can change the decision.

**Dependencies**

- Phase 5 trusted task, provenance, attribution, freshness, coverage, and verdict
  contracts;
- real dogfood examples of slow or misdirected review.

**Capabilities**

- deterministic priority reasons for explicitly unfinished or independently
  unmet requirements, failed final checks, claim/evidence conflicts, scope
  drift, unattributable material, and declared high-risk paths;
- grouped and ordered review targets with evidence locators;
- concise recommended actions and feedback shaped by the highest-priority
  decision blocker;
- evidence-quality dimensions kept separate from correctness scoring.

**Exit criteria**

- every priority reason is inspectable and deterministic;
- fixture ordering is stable under equivalent evidence;
- no opaque aggregate confidence/correctness score exists;
- summary, feedback, and brief agree on first review target;
- real dogfood shows that the first target usually resolves the decision faster;
- full quality gates and report safety tests pass.

**Out of scope**

- general code review;
- vulnerability scanning;
- LLM prioritization;
- automatic fixes;
- UI/dashboard.

**Plan-change triggers**

- users prefer grouped review queues over strict ordering;
- deterministic risk rules are noisy or encode project-specific policy;
- evidence gaps, not ordering, remain the dominant problem.

### Phase 7 — Post-Hoc Analyze And Compatibility

**Status:** `planned`

**Problem**

A user may need to re-render a saved trusted run or analyze an explicit local
evidence bundle without launching the original Codex process again.

**User value**

Existing compatible evidence remains useful and inspectable instead of being
discarded or silently reinterpreted.

**Dependencies**

- versioned Phase 5 task, protocol, manifest, evidence, outcome, verdict, and
  report contracts;
- stable Phase 6 review ordering;
- compatibility policy approved before a public read path exists.

**Capabilities**

- `patchtrace analyze --run <run-path>`;
- digest and schema verification before analysis;
- immutable raw evidence with analyzer/report version history;
- re-analysis of compatible trusted runs without weakening them;
- explicit imported-bundle mode with provenance-equivalent limits;
- clear rejection of unknown-incompatible or mutated material.

**Exit criteria**

- a compatible saved trusted run reproduces the expected decision under the
  declared analyzer version;
- original raw evidence is never mutated;
- imported evidence cannot gain attribution it did not capture;
- compatible saved trusted runs may retain `ready_to_accept`;
- unknown-incompatible schemas fail clearly;
- fixture matrix and at least one real saved-run replay pass.

**Out of scope**

- automatic discovery of arbitrary transcripts;
- current-worktree guessing;
- cloud imports;
- continuous monitoring;
- GitHub integration.

**Plan-change triggers**

- compatibility maintenance exceeds the user value of re-analysis;
- users primarily need repository-current analysis rather than saved runs;
- imported bundles cannot preserve useful trust boundaries.

### Phase 8 — Local Continuous Watch

**Status:** `planned`

**Problem**

The user wants to use Codex normally without remembering to start every session
through the PatchTrace wrapper.

**User value**

A local repo-scoped watcher stays running, pre-binds an explicit task, and uses
a documented Codex integration to prove delivery and capture without requiring
the user to remember the Phase 5 wrapper command. Unbound or post-hoc candidate
sessions remain inspectable but cannot become fully trusted.

**Dependencies**

- Phase 7 saved-run ingestion and compatibility;
- stable pre-run task/run association and payload-delivery proof;
- a documented Codex event/launch interface that can preserve the trusted
  contract without unsupported private-session parsing;
- bounded retention and cleanup policy;
- a proven local process lifecycle on macOS.

**Capabilities**

- `patchtrace watch --repo <repo-path>`;
- explicit install/start/stop/status behavior;
- durable local watcher identity and crash recovery;
- candidate session detection without external telemetry;
- pre-bound task-contract association and recorded payload delivery before a
  full verdict;
- an explicit non-trusted ceiling for sessions discovered only after launch;
- duplicate/incomplete session handling;
- bounded storage, retention, and deletion;
- reuse of the same evidence and `AnalysisResult` path as wrapped runs.

**Exit criteria**

- start/stop/status/restart behavior is deterministic;
- watcher crashes do not corrupt completed runs or duplicate decisions;
- no session receives `ready_to_accept` without pre-bound task delivery and the
  complete trusted contract;
- resource use and storage growth remain within documented bounds;
- three real multi-session macOS dogfood workflows pass;
- privacy and process lifecycle documentation is complete.

**Out of scope**

- cloud daemon;
- multi-user service;
- invisible execution of untrusted commands;
- arbitrary process surveillance;
- second-agent support.

**Plan-change triggers**

- Codex adds or changes a documented local event/session/launch interface;
- reliable session detection requires unsupported private storage;
- no supported integration can prove pre-bound task delivery without a manual
  wrapper, requiring the watcher UX or trust ceiling to be re-specified;
- watcher overhead or false associations exceed its workflow value;
- OS service installation changes distribution requirements.

### Phase 9 — OSS And macOS/Linux Distribution Readiness

**Status:** `planned`

**Problem**

The trusted local product is still optimized for the maintainer's source
checkout and environment.

**User value**

Other developers can install, understand, trust, operate, upgrade, and remove
PatchTrace on supported macOS and Linux systems.

**Dependencies**

- stable wrapped, analyze, and watch workflows;
- repeated dogfood through Phases 5–8;
- approved public compatibility and privacy contracts;
- operations documentation for any watcher installation.

**Capabilities**

- package metadata, versioning, release artifacts, checksums, changelog, and
  rollback guidance;
- documented install, upgrade, uninstall, run, analyze, and watch paths;
- supported Python, Git, Codex, macOS, and Linux matrix;
- public CLI/schema compatibility policy;
- sanitized examples and fixture contribution process;
- release CI and external clean-machine smoke tests;
- contributor docs, license, security/privacy disclosure, and issue templates.

**Exit criteria**

- clean macOS and Linux installs pass the supported workflow;
- upgrade and uninstall leave documented state;
- public command and schema compatibility rules are explicit;
- watcher lifecycle is safe on supported systems;
- no private dogfood artifact appears in release material;
- release CI, package build, checksums, smoke tests, and rollback proof pass;
- at least one external user completes the trusted-run quickstart.

**Out of scope**

- Windows support;
- hosted service;
- teams/auth/billing;
- marketplace integrations;
- paid distribution.

**Plan-change triggers**

- package installation exposes platform-specific PTY/process constraints;
- external users require a different task-authoring or storage workflow;
- public schema stability is premature;
- watcher installation requires separate platform packaging.

### Phase 10 — Windows Portability

**Status:** `planned`

**Problem**

The production product should eventually support Windows, but the accepted
foundation and current process capture are POSIX-oriented.

**User value**

Windows developers can use the same trusted-run, analyze, and watch contracts
without receiving a weaker product under the same command names.

**Dependencies**

- stable public macOS/Linux product;
- selected Windows terminal/process strategy;
- Windows Git, path, permissions, process, and service fixtures;
- a real Windows user or test environment.

**Capabilities**

- documented Windows install and filesystem storage behavior;
- process capture that preserves structured `codex exec` evidence;
- Windows-safe task, path, permission, signal/termination, and command
  execution semantics;
- watcher lifecycle appropriate to Windows;
- parity matrix for every trusted-run contract.

**Exit criteria**

- supported Windows versions and Codex versions are explicit;
- clean and dirty Git attribution fixtures pass on Windows;
- trusted run, final verification, analyze, and watch real workflows pass;
- no verdict is promoted when platform evidence is weaker;
- installation, upgrade, uninstall, and rollback are verified.

**Out of scope**

- feature divergence by platform;
- Windows-only product capabilities;
- hosted execution.

**Plan-change triggers**

- Codex or Python support changes the viable process strategy;
- no real Windows user/use case exists by the time Phase 9 stabilizes;
- parity requires a platform abstraction too costly for demonstrated demand.

## Conditional / Triggered Capabilities

These items are known and intentionally visible. They are not numbered committed
phases until the trigger is observed and the project owner approves a spec.

### Second Coding-Agent Adapter

- **Trigger:** The primary user repeatedly uses a second coding agent.
- **Then:** Implement one concrete second adapter. Extract a shared protocol only
  after both implementations reveal a stable common contract.
- **Do not:** Build discovery, registry, marketplace, or hypothetical adapters
  first.

### GitHub / Pull-Request Integration

- **Trigger:** Repeated need to attach PatchTrace decisions to PR review without
  manual copying.
- **Then:** Specify exactly which local evidence or sanitized summary leaves the
  machine, with explicit opt-in and failure behavior.
- **Do not:** Upload raw tasks, transcripts, diffs, or command output by default.

### Stable Machine-Readable Output

- **Trigger:** A real script, CI consumer, or integration needs a supported data
  contract.
- **Then:** Version a minimal JSON output derived from `AnalysisResult`.
- **Do not:** Confuse this optional stdout/export contract with Phase 9's
  required compatibility policy for persisted run formats and public commands,
  or expose internal models as a public API accidentally.

### Optional LLM Assistance

- **Trigger:** A sanitized fixture corpus demonstrates a repeated deterministic
  extraction or summarization miss that materially harms decisions.
- **Then:** Specify opt-in data scope, provider, cost cap, retry cap, logging,
  evaluation, and failure path.
- **Do not:** Make an LLM required for trusted verdicts or treat its judgment as
  evidence.

### Local HTML Presentation

- **Trigger:** Markdown reports repeatedly fail usability dogfood and a richer
  local view solves a measured comprehension problem.
- **Then:** Render the same `AnalysisResult` locally with no separate analysis.
- **Do not:** turn presentation into a web platform.

### Multi-Repository / Submodule Attribution

- **Trigger:** Real trusted tasks routinely modify declared multiple
  repositories or submodule contents.
- **Then:** Specify an explicit multi-root task and evidence contract.
- **Do not:** silently treat `--add-dir` as complete single-repository
  attribution.

## Permanently Rejected Without A New Product Decision

- correctness oracle or general AI code reviewer;
- autonomous code repair, approval, or merge;
- SaaS, accounts, teams, billing, or entitlements;
- required LLM, RAG, or embeddings;
- event-sourced workflow platform;
- plugin marketplace;
- multi-agent orchestration;
- external telemetry or private-data upload by default.

Moving one of these into the roadmap requires a new confirmed product decision,
not merely an implementation convenience.

## Roadmap Maintenance Rules

- Update this file when a phase is added, removed, reordered, or changes status.
- Keep only the active/proposed phase's detailed task breakdown in
  `docs/PLAN.md`.
- Record phase close proof in `docs/VERIFY_LOG.md`; do not copy command logs here.
- Update `docs/SPEC.md` when the product promise or boundary changes.
- Update `docs/ARCHITECTURE.md` and an ADR when a system or irreversible decision
  changes.
- Do not mark a phase complete until its exit criteria and real workflow proof
  pass.
- Do not convert conditional capabilities into committed phases without their
  trigger and explicit project-owner approval.

## Known Non-Blocking Decisions

- Exact Task Contract V1 Markdown grammar and stable requirement ID syntax.
- Default snapshot, command-output, timeout, and retention limits.
- Exact analyzer/package reason-code names.
- Phase 8 watcher process and Codex-session detection mechanism.
- Phase 9 Linux distribution matrix.
- Phase 10 Windows process/service strategy.
- Numeric thresholds for conditional capability triggers.

These are visible so they are not forgotten. They become blocking only when the
phase that owns them enters detailed planning.
