# PLAN.md

Detailed execution source of truth for the proposed next phase only.

- Product contract: `docs/SPEC.md`
- Complete phase sequence: `docs/ROADMAP.md`
- System design: `docs/ARCHITECTURE.md`
- Decisions: `docs/decisions/`

Work on one task at a time. Each task is a production vertical slice with a
user-visible result, failure-path proof, focused tests, typecheck, and commit.

## Branch And Baseline

This plan is based on commit `d8c98c4`, the head of open PR #19, which contains
the Phase 4 implementation and closeout.

The product/architecture re-baseline remains stacked on PR #19 until that PR
merges. Retarget to `main` only after confirming:

- `main` contains `d8c98c4`;
- the retargeted diff contains only the re-baseline;
- no Phase 4 verification history is lost.

## Proposed Next Phase: Phase 5 — End-to-End Trusted Run

This phase becomes current only after the project owner approves this plan and
proposed ADR-0002 through ADR-0005.

### Phase Goal

Deliver the complete production trusted-run decision:

```text
one Markdown task
  -> structured Codex execution
  -> session-scoped Git delta
  -> final required verification
  -> requirement coverage
  -> decisive verdict and three aligned reports
```

The phase is not complete at "better provenance." It closes only when the user
can receive a real `ready_to_accept` or the correct actionable non-accept
verdict.

### User-Visible Result

Target command:

```bash
patchtrace run --task-file ./TASK.md
```

PatchTrace:

1. validates and privately binds the task;
2. passes the unchanged task payload to a PatchTrace-constructed `codex exec`
   command with a versioned structured response protocol;
3. records the session and a bounded private Git baseline;
4. attributes the session delta, including supported dirty-repo changes;
5. runs the task's authorized `Required Verification` commands against the
   final repository state;
6. evaluates every requirement and acceptance criterion;
7. writes one decisive verdict, one next action, and three reports from the same
   `AnalysisResult`.

Interactive Codex remains available as a secondary mode but cannot emit
`ready_to_accept` without the complete trusted contract.

### Confirmed Decisions

- Primary user: the project owner using local Codex.
- Primary trusted transport: structured `codex exec`.
- Task Contract V1: fixed-section Markdown.
- Task delivery: unchanged user task plus a separate versioned PatchTrace
  execution/response protocol.
- Storage: private Git metadata under `patchtrace/runs/`, outside the worktree.
- Dirty repositories: supported when the bounded baseline makes the delta
  complete.
- Final verification: PatchTrace executes only explicit user-authorized
  commands after agent capture.
- Highest verdict: `ready_to_accept`.
- Analysis: task fulfillment and evidence quality, not general code review.
- Stack/module convention: existing Python capability ownership; no new runtime
  dependency unless necessary.

### Dependencies

- Phase 4 commit `d8c98c4`, fixtures, `AnalysisResult`, and report renderers;
- approved `docs/SPEC.md` and `docs/ROADMAP.md`;
- approved ADR-0002 through ADR-0005;
- documented Codex CLI structured `exec` behavior;
- documented Git path/worktree behavior;
- existing local quality and package build loop.

### Phase Exit Criteria

#### Contract And Lifecycle

- Task Contract V1 validation, closed item taxonomy, requirement/criterion
  links, closed typed acceptance-predicate declarations, stable IDs,
  byte-preserving copy, digest, and execution-protocol separation are
  implemented.
- Caller cwd, requested/resolved repo, child cwd, Git metadata root, run path,
  requested/effective command, and protocol/schema versions are recorded.
- Run storage is private, atomic, bounded, collision-safe, outside the worktree,
  and cannot be staged by ordinary Git commands.
- Wrapped-command, analysis, and package outcomes are independent and
  failure-path tested.
- CLI exit semantics are documented, compatible, and fixture-proven.

#### Structured Codex

- PatchTrace constructs one canonical `codex exec` invocation and preserves
  stdout JSONL, stderr, final message, and schema-bound response separately.
- Only canonical Codex `exited(0)` with complete compatible evidence proceeds
  to fulfillment analysis; not-started, spawn, non-zero, signal, interruption,
  unknown, containment, and quiescence failures select the closed non-accept
  outcome.
- Every `REQ-*` and `AC-*` receives a structured agent status/claim entry or a
  named protocol failure; `VER-*` and `OOS-*` retain their distinct semantics.
- Security-relevant Codex configuration is recorded and constrained so hooks,
  notifications, MCP/plugins, sandbox/network settings, inherited
  environment/credentials, temp paths, and writable roots cannot create
  unaccounted trusted scope.
- Unknown events are preserved; malformed, truncated, missing, or mismatched
  structured evidence never silently becomes trusted text inference.
- Interactive Codex remains usable and explicitly labels its weaker evidence.

#### Git And Verification

- Baseline/agent-end evidence covers clean, dirty, staged, unstaged, untracked,
  deleted, renamed, binary, committed-during-run, unborn, and non-descendant
  cases under documented limits.
- A pre-existing dirty/untracked path can still expose its later
  `session-attributed` delta when baseline bytes were captured completely.
- Symlinks are not followed; FIFOs, sockets, and devices are not opened;
  file/byte/path/time limits degrade only affected evidence where possible.
- PatchTrace never mutates the worktree, index, branch, history, or Git config.
- Git collection uses non-refresh/non-optional-lock behavior and proves that
  index bytes and semantic Git state remain unchanged.
- Required verification runs after agent capture under a recorded default-deny
  effect profile, records contained process-tree lifecycle and bounded output,
  and is bound across separate quiescent agent-end and verification-end
  repository fingerprints.
- Relevant verification-phase state is captured separately from the agent
  delta and produces `send_back`; it is never silently folded into accepted
  work.
- Timeout, signal, spawn, output-limit, repository-mutation, and command-failure
  behavior is explicit and tested.
- Delayed/background/detached descendant behavior is contained and
  fixture-proven; incomplete containment cannot produce `ready_to_accept`.

#### Analysis And Reports

- Every requirement and acceptance criterion has an explicit fulfillment and
  evidence-coverage result, or a named protocol failure.
- Every acceptance criterion has a supported closed independent evidence
  predicate; an
  agent claim alone cannot support acceptance.
- One analyzer-owned precedence rule emits exactly one of:
  `ready_to_accept`, `send_back`, `review_required`, `rerun_required`,
  `cannot_assess`.
- A valid failed required check yields `send_back`; stale/missing/broken capture
  yields `rerun_required`.
- A closed failure-class to analysis-outcome to verdict table distinguishes
  repeatable capture failures from incompatible/unrepairable runs.
- `SUMMARY.md` leads with verdict, decisive reason, coverage, final verification,
  attribution limits, and next action.
- `AGENT_FEEDBACK.md` is immediately pasteable into Codex without relaying raw
  untrusted task/evidence bytes into a new prompt.
- `VERIFICATION_BRIEF.md` preserves the complete task/claim/evidence path.
- All reports consume one `AnalysisResult` and render untrusted content as inert
  text.

#### Production Proof

- Unit/integration fixture matrices cover the supported happy paths and failure
  taxonomy.
- Three real sanitized dogfood runs pass:
  1. clean `ready_to_accept`;
  2. dirty baseline with correctly separated session delta;
  3. omitted, failed, or stale evidence producing the correct non-accept
     verdict.
- The project owner confirms that the verdict and generated feedback produce the
  right next decision.
- Ruff lint, Ruff format check, mypy, pytest, build, and PR CI pass.
- `docs/VERIFY_LOG.md` receives one Phase 5 close entry only after implementation
  and human verification.

### Out Of Scope

- generic code review, correctness scoring, vulnerability scanning;
- review-priority ranking beyond decisive Phase 5 reasons;
- post-hoc `analyze`;
- continuous `watch`;
- public package release;
- Linux/Windows release claims;
- non-Codex adapters or shared adapter framework;
- LLM or external services;
- public JSON contract;
- automatic fixes, acceptance, or merge.

### Phase Plan-Change Triggers

- Codex structured output cannot reliably carry requirement-level final claims.
- Task Contract V1 is unusable in three real dogfood runs.
- Dirty baseline storage or capture cost makes normal repositories impractical.
- Final verification authorization is unsafe or too surprising.
- Representative trusted tasks require network or external-writer effects that
  the Phase 5 controlled profile excludes.
- Supported macOS primitives cannot enforce the required Codex/verification
  process containment and quiescent checkpoint contract.
- Deterministic coverage produces misleading accept decisions.
- A task cannot be completed as a production vertical slice without changing the
  accepted trust contract.

## Active Tasks

### Task 1 — Trusted Task, Repository, Storage, And Lifecycle Contract

**User-visible result**

`patchtrace run --task-file TASK.md` validates the task and repository, creates a
private durable run manifest outside the worktree, shows the effective run
contract, and leaves a diagnosable package for every supported outcome after
safe storage is established. Earlier task/repository/storage preflight failures
produce structured stderr and exit diagnostics without promising a run folder.

**Scope**

- parse fixed Task Contract V1 headings, cardinalities, item taxonomy,
  requirement/criterion links, and closed typed evidence-predicate
  declarations;
- preserve/digest original task bytes and validate stable `REQ-*`, `AC-*`,
  `VER-*`, and `OOS-*` IDs under their distinct semantics;
- build and digest a separate versioned execution/response protocol;
- resolve caller cwd, repository root, child cwd, and Git metadata storage;
- introduce manifest/evidence schema versions and integrity fields;
- separate wrapped-command, analysis, and package outcomes;
- define atomic manifest lifecycle and CLI exit behavior.

**Acceptance criteria**

- [ ] Missing, malformed, unstable, oversize, unsupported-encoding, symlinked,
      or unreadable task input fails before Codex starts.
- [ ] `Outcome` is singular/non-empty; requirements and acceptance criteria are
      non-empty; verification/out-of-scope use their declared item or explicit
      `N/A` forms.
- [ ] Every acceptance criterion links to requirements and declares a supported
      closed predicate over exact Git/artifact properties, expected named
      `VER-*` outcomes, or explicit human inspection, with declared `all`/`any`
      composition.
- [ ] Generic file presence/change, agent claims, unsupported predicate atoms,
      and ambiguous compositions cannot satisfy a criterion; malformed machine
      predicates fail task validation.
- [ ] Every requirement is linked from at least one acceptance criterion;
      unmapped requirements fail contract validation.
- [ ] The task payload and PatchTrace protocol are stored/digested separately.
- [ ] Relative task/repo paths, symlinked repo paths, nested repos, and linked
      worktrees resolve under one tested rule.
- [ ] Child cwd and Git evidence scope are the same resolved worktree root.
- [ ] `git rev-parse --path-format=absolute --git-path patchtrace/runs` or its
      documented equivalent resolves storage, followed by explicit safety
      validation.
- [ ] Storage refuses worktree overlap, symlinks, regular-file collisions, and
      unowned pre-existing directories.
- [ ] Failures before safe storage exists return bounded structured diagnostics;
      durable manifest/package guarantees begin only after storage creation.
- [ ] Ordinary `git add -A` cannot stage any generated task, protocol, manifest,
      or run artifact.
- [ ] Manifest writes are private and atomic; partial preflight/spawn failure
      remains diagnosable.
- [ ] Outcome and CLI exit fixtures cover validation `2`, PatchTrace failure
      `1`, normal child exits, signals, and interruption.
- [ ] No new runtime dependency is added.

**Verification**

- [ ] Task parser/model unit tests.
- [ ] Storage permissions/collision/atomicity integration tests.
- [ ] Fake subprocess lifecycle and CLI exit tests.
- [ ] Manual fake run inspection of `run.json`.
- [ ] Ruff, format, mypy, focused pytest, full pytest, and build.

**Dependencies:** None after plan/ADR approval.

**Likely ownership:** `cli`, `models`, `storage`, new task-contract parsing under
a capability-owned module, and focused tests.

**Suggested branch:** `agent/phase-5-task-1-trusted-run-contract`

### Task 2 — Canonical Structured Codex Execution

**User-visible result**

PatchTrace launches the validated task through one structured trusted Codex path
and captures a schema-valid final response covering every `REQ-*` and `AC-*`.

**Scope**

- add one concrete Codex adapter;
- construct effective `codex exec` flags and stdin/prompt payload;
- resolve, constrain, and record the security-relevant effective Codex profile;
- use JSONL, final-message output, and output schema;
- preserve raw stdout JSONL and stderr separately;
- parse documented event shapes and structured final response;
- keep interactive PTY mode available but explicitly secondary.

**Acceptance criteria**

- [ ] The user task bytes remain unchanged inside the effective prompt; the
      versioned PatchTrace protocol is separately identifiable and digested.
- [ ] Requested/effective commands, Codex version, adapter/parser/protocol/schema
      versions, and output locators are recorded.
- [ ] Trusted mode explicitly fixes sandbox, approval, cwd, and writable-scope
      settings; explicitly configures network and temp behavior; allowlists and
      redacts inherited environment/credential inputs; records the effective
      config/profile and effect-scope digest; and rejects unaccounted hooks,
      notification commands, MCP/plugin writers, roots, environment channels,
      or unsafe bypass modes.
- [ ] Canonical Codex and accounted descendants run under a source-checked
      supervised containment boundary; agent-end capture waits for quiescence,
      and surviving/escaped/unreaped descendants select `rerun_required`.
- [ ] The response schema requires one result for every stable requirement and
      acceptance-criterion ID.
- [ ] The only response statuses are `claimed_done`, `not_done`, and `blocked`;
      schema-valid `not_done`/`blocked` is explicit unfulfilled work and later
      selects `send_back`.
- [ ] Missing IDs, duplicates, invalid statuses, unexpected IDs, malformed or
      truncated JSONL, missing final files, and event/file disagreement are
      protocol/capture failures with explicit `rerun_required` or
      `cannot_assess` integrity outcomes; they never become `not_done`.
- [ ] Raw structured evidence remains authoritative; parse failure does not
      silently fall back to TUI inference.
- [ ] Canonical terminal mapping covers `not_started`, spawn failure, exit `0`,
      non-zero exit even with valid final schema, signal, interruption, and
      unknown outcome; only exit `0` can continue toward `ready_to_accept`.
- [ ] User-supplied conflicting structured-output flags fail before launch.
- [ ] Codex `-C/--cd` must match the selected repo; trusted mode rejects
      additional writable roots, while secondary modes label the scope
      incomplete and retain their verdict ceiling.
- [ ] Generic process/session code contains no Codex markers or event rules.
- [ ] Interactive mode preserves verified Phase 4 behavior and cannot emit
      `ready_to_accept` under incomplete evidence.

**Verification**

- [ ] Synthetic JSONL/final-response fixture corpus covering success and every
      supported integrity failure.
- [ ] Fake piped process proves stdout/stderr separation, timeout, signal, and
      output limits.
- [ ] Delayed/background/detached child fixtures prove Codex process-tree
      containment and quiescent agent-end capture on supported macOS.
- [ ] Existing interactive transcript fixtures pass through the adapter.
- [ ] One sanitized real structured Codex run proves the installed documented
      path.
- [ ] Ruff, format, mypy, focused pytest, full pytest, and build.

**Dependencies:** Task 1.

**Likely ownership:** `adapters/codex.py`, generic piped `session` capture,
evidence models, CLI orchestration, sanitized fixtures, and focused tests.

**Suggested branch:** `agent/phase-5-task-2-structured-codex`

### Task 3 — Session Delta And Final Verification

**User-visible result**

The run package distinguishes pre-existing work from the session delta,
including supported dirty files, then executes every authorized required check
and captures a distinct verification-end state.

**Scope**

- capture bounded baseline/agent-end repository state and private dirty/untracked
  content needed for later comparison;
- capture distinct agent-end and verification-end repository states;
- capture HEAD/index/worktree and descendant commit evidence;
- compute session attribution without mutating Git;
- execute final verification commands from the validated task;
- enforce a recorded verification effect profile independently from command
  authorization;
- source-check and fixture-prove the installed `codex sandbox [COMMAND]...` as
  the preferred host-OS verification launcher before considering any new
  dependency;
- bind command results across agent-end, per-command, and verification-end
  repository fingerprints;
- define resource, filesystem, process, and repository-mutation behavior.

**Acceptance criteria**

- [ ] Clean tracked changes, additions, deletions, renames, binary paths, new
      untracked files, and descendant commits are `session-attributed`.
- [ ] Unchanged baseline changes remain `pre-existing`.
- [ ] Changes after a completely captured dirty/untracked baseline are
      `session-attributed`, including the same path.
- [ ] Baseline HEAD/index/worktree layers remain decomposed when pre-existing
      staged/unstaged content is partially or fully committed; moving identical
      baseline bytes into a descendant commit does not relabel them as session
      content.
- [ ] Only genuinely inseparable, incomplete, rewritten, or out-of-scope
      material is `unattributable`.
- [ ] Unborn/non-descendant HEAD, submodules, sparse checkouts, linked
      worktrees, ignored files, and extra repositories have explicit behavior.
- [ ] Symlinks use `lstat` and are never followed; special files are never
      opened.
- [ ] Per-file, total-byte, path-count, elapsed-time, command-timeout, and
      output limits are recorded and tested.
- [ ] PatchTrace performs no index, worktree, branch, commit, or Git-config
      mutation.
- [ ] Every Git collector invocation uses `git --no-optional-locks` or the
      tested equivalent; collection preserves index bytes and semantic
      Git state in isolated fixtures.
- [ ] Required verification runs only from the user-authorized task section and
      only after agent capture.
- [ ] Every command and descendant runs with network/external writers denied,
      inherited environment allowlisted, credentials excluded/redacted, and
      writable/temp roots bounded to the recorded Phase 5 profile; unsupported
      expansion fails before execution.
- [ ] The selected version-checked verification launcher proves effective
      filesystem/network denial, descendant policy inheritance, and denial
      diagnostics on supported macOS; command/flag presence alone is not proof.
- [ ] Command authorization alone never grants network, credentials, external
      roots, or unbounded subprocess effects.
- [ ] A verification result is `state_bound` only when it applies to
      verification-end state and no later relevant change made it stale.
- [ ] A relevant repository delta observed from agent-end to verification-end
      invalidates acceptance: it is reported as verification-phase and the
      verdict is `send_back`. The snapshots
      establish that the change happened during the phase, not which concurrent
      process wrote it. Ignored/declared ephemeral outputs remain outside the
      relevant fingerprint.
- [ ] Verification process outcomes use one closed mapping: captured exit `0`
      follows normal evidence rules; captured non-zero exit, declared-timeout
      termination, or unrequested signal selects `send_back`; spawn failure,
      PatchTrace/user interruption, or lost exit status selects
      `rerun_required`.
- [ ] Bounded saved output continues draining to a reliable process outcome;
      truncation alone does not change a known exit-based verdict, but
      truncating output explicitly required as evidence or terminating/loss of
      outcome at the cap selects `rerun_required`.
- [ ] Verification-end capture waits until every accounted descendant is
      terminated/reaped and the effect boundary is quiescent; surviving,
      escaped, or unaccounted descendants select `rerun_required`.
- [ ] Valid pass, valid fail, spawn failure, timeout, signal, output limit, and
      stale-state fixtures prove the mapping.

**Verification**

- [ ] Temporary-repository integration matrix for all accepted Git cases.
- [ ] Dirty-baseline-to-descendant-commit fixtures cover staged, unstaged,
      partial-commit, and same-path later-edit cases.
- [ ] Special-file, symlink, huge-file/tree, and cap fixtures.
- [ ] Fake verification command process matrix.
- [ ] Credential/network/external-root denial plus delayed/background/detached
      writer fixtures.
- [ ] Manual dirty-repo artifact inspection without private material committed.
- [ ] Ruff, format, mypy, focused pytest, full pytest, and build.

**Dependencies:** Tasks 1–2.

**Likely ownership:** `vcs`, verification process capture, evidence/run models,
CLI orchestration, and integration fixtures.

**Suggested branch:** `agent/phase-5-task-3-session-delta-verification`

### Task 4 — Requirement Coverage, Decisive Reports, And Phase Proof

**User-visible result**

The complete trusted flow emits one production decision, one exact next action,
and three aligned reports, then proves the result in clean, dirty, and failure
dogfood scenarios.

**Scope**

- map task requirements/acceptance criteria to structured Codex claims, Git
  evidence, and final verification;
- enforce independent acceptance evidence and define coverage, evidence gaps,
  the closed failure/outcome/verdict mapping, and next actions;
- preserve one `AnalysisResult`;
- update all three renderers and CLI completion output;
- neutralize untrusted Markdown/control content;
- run the complete fixture and real dogfood matrix;
- reconcile docs/ADR status with implemented truth at close.

**Acceptance criteria**

- [ ] Every `REQ-*` and `AC-*` has a deterministic coverage result and evidence
      locators; every `VER-*` and `OOS-*` has its distinct assessment.
- [ ] Only `REQ-*` and `AC-*` require structured agent entries; `VER-*` results
      come from PatchTrace and `OOS-*` constraints are checked against evidence.
- [ ] An `OOS-*` constraint that cannot be assessed deterministically selects
      `review_required`; absence of an agent scope claim is not proof.
- [ ] No acceptance criterion reaches supported coverage from an agent claim
      alone; a declared human-inspection basis selects `review_required`.
- [ ] Only the task's closed typed predicate determines machine support;
      misleading generic changed-file bases and unsupported natural-language
      inference cannot promote `ready_to_accept`.
- [ ] Missing agent entries and unsupported/contradicted claims cannot disappear
      from the verdict.
- [ ] A missing/duplicate/invalid structured entry remains a protocol capture
      failure and selects `rerun_required`; a schema-valid `not_done` or
      `blocked` entry is an explicit fulfillment failure and selects
      `send_back`.
- [ ] `ready_to_accept` requires complete supported task coverage, passing
      declared acceptance predicates, successful quiescent canonical Codex
      execution, controlled Codex/verification effects, state-bound required
      verification, identical relevant agent-end/verification-end state,
      complete relevant session attribution, compatible integrity, and no
      higher-precedence condition.
- [ ] Valid required-check failure selects `send_back`.
- [ ] Missing/stale/malformed/incomplete/mismatched required evidence selects
      `rerun_required`.
- [ ] Bounded ambiguity/unattributable risk selects `review_required`; blocked
      trusted analysis selects `cannot_assess`.
- [ ] Reports never perform general code review or claim semantic correctness.
- [ ] `SUMMARY.md` shows verdict, decisive reason, coverage counts, final checks,
      attribution limitations, and one action before secondary metadata.
- [ ] `AGENT_FEEDBACK.md` is pasteable and contains only PatchTrace-authored
      closed reason text, task IDs validated under a bounded ASCII grammar,
      PatchTrace-generated evidence IDs, PatchTrace-controlled local artifact
      locators, and the requested correction.
- [ ] Raw task text, agent claims/output, command output, diff excerpts, and
      user-controlled paths/file names never enter the paste-ready feedback
      section; prompt-injection fixture bytes prove this boundary.
- [ ] `VERIFICATION_BRIEF.md` preserves full provenance and review locators.
- [ ] Untrusted headings, fences, links, images, control characters, and
      terminal escape content remain inert through one renderer-independent
      literal-text path.
- [ ] Raw HTML, HTML entities, reference definitions, autolinks, remote
      resources, and renderer-specific Markdown extensions remain inert.
- [ ] Clean, dirty, and non-accept real dogfood scenarios pass.
- [ ] The project owner explicitly approves report usefulness and Phase 5 close.

**Verification**

- [ ] Requirement/claim/predicate/evidence/verdict unit matrix, including
      misleading-basis fixtures.
- [ ] Cross-report agreement and Markdown-injection fixtures.
- [ ] Full supported integration and partial-failure matrix.
- [ ] Three real sanitized dogfood run inspections.
- [ ] Ruff, format, mypy, full pytest, build, and PR CI.
- [ ] `$aga-simplify`, `$aga-review`, `$aga-test`, and `$aga-verify-agent`, or
      exact cannot-verify records.
- [ ] One compact `docs/VERIFY_LOG.md` Phase 5 close entry after human approval.

**Dependencies:** Tasks 1–3.

**Likely ownership:** `analysis`, `models`, `reports`, CLI presentation, docs,
fixtures, and phase-close verification.

**Suggested branch:** `agent/phase-5-task-4-trusted-verdict`

## Checkpoints

### Checkpoint A — After Task 1

- [ ] Human confirms Task Contract V1 authoring and CLI preflight ergonomics.
- [ ] Manifest/outcome/storage contracts are stable enough for adapter and Git
      work.
- [ ] No worktree artifact can be staged accidentally.

### Checkpoint B — After Task 2

- [ ] A real structured Codex task produces a schema-valid response for every
      task item.
- [ ] Interactive mode remains usable and honestly differentiated.
- [ ] Protocol and external-format fixtures cover observed drift.

### Checkpoint C — After Task 3

- [ ] Dirty baseline attribution is understandable and useful in a real repo.
- [ ] Final verification is demonstrably tied to final analyzed state.
- [ ] Resource limits and special-file behavior do not hide whole-run failures.

### Checkpoint D — After Task 4

- [ ] The user receives the correct decision in all three real dogfood cases.
- [ ] Reports agree and generated feedback is immediately actionable.
- [ ] Full phase exit criteria and production proof pass.

## Open Questions Owned By Phase 5

### Approval Gate Before Task 1

- The project owner must approve `docs/SPEC.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE.md`, ADR-0002 through ADR-0005, and this plan.
- This is a human approval gate, not an unresolved design question.

### Blocking Design Questions After Approval

- N/A.

### Non-Blocking Until Their Owning Task

- Task 1: exact Markdown syntax for the decided taxonomy/links/typed evidence
  predicates, default task size limit, and lifecycle reason-code names.
- Task 2: exact protocol version field, response schema shape, supported Codex
  version matrix, version-checked config override keys, and source-checked macOS
  containment primitive.
- Task 3: exact snapshot/command/output/time defaults, verification-profile
  enforcement primitive, and ignored/ephemeral fingerprint rules.
- Task 4: final report wording and coverage state spellings.

These questions must be decided and tested inside the named task before that
task can close. They do not authorize silent implementation assumptions.
