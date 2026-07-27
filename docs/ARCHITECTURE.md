# PatchTrace Architecture

System source of truth: current implementation, target design, data flow,
trust boundaries, and deferred architecture.

Product scope lives in `docs/SPEC.md`.
The complete phase sequence lives in `docs/ROADMAP.md`.
Detailed tasks for the proposed next phase live in `docs/PLAN.md`.

## Status

- Last reviewed: 2026-07-27
- Baseline: `d8c98c4`, head of open PR #19
- Product intent: confirmed through `$aga-spec`
- Target architecture: proposed, pending human review before implementation
- Accepted foundation: `docs/decisions/ADR-0001-project-foundation.md`
- Proposed decisions:
  - `ADR-0002-trust-chain-and-analysis-outcomes.md`
  - `ADR-0003-codex-structured-evidence-boundary.md`
  - `ADR-0004-session-scoped-git-attribution.md`
  - `ADR-0005-task-payload-protocol-and-final-verification.md`

This document deliberately separates current code from target architecture.

## Stack

| Layer | Current decision | Status |
|---|---|---|
| Runtime | Python >=3.11 | Implemented |
| Project/dependency manager | `uv` | Implemented |
| CLI | Typer | Implemented |
| Interactive capture | Pexpect over POSIX PTY | Implemented |
| Structured models | Pydantic v2 | Implemented |
| Git collection | Local Git CLI subprocesses | Implemented, attribution incomplete |
| Analysis | Deterministic/rules-first Python | Implemented, bounded Phase 4 behavior |
| Reports | Markdown from one `AnalysisResult` | Implemented |
| Tests | pytest fixtures/unit/integration | Implemented |
| Lint/format/typecheck | Ruff + mypy | Implemented |
| Database/auth/hosting/payments | N/A; local CLI only | Intentionally absent |
| Required LLM/external service | N/A | Intentionally absent |

The existing application stack is sufficient for the target modules and data
contracts. Tasks 2–3 must source-check whether supported macOS primitives can
enforce the required effect/process containment; any new runtime dependency or
architecture change requires explicit approval before implementation.

## Current Implementation

### Current Package Tree

```text
src/patchtrace/
  __init__.py
  __main__.py
  cli/
    app.py
  session/
    recorder.py
    transcript.py
  vcs/
    git.py
    snapshot.py
  analysis/
    analyzer.py
    test_evidence.py
  models/
    run.py
    report.py
  reports/
    summary.py
    feedback.py
    verification_brief.py
  storage/
    runs.py
```

There is currently no `adapters/` package, no `models/evidence.py`, and no
implemented `cli/commands/` package. Older architecture text that showed those
paths as accepted implementation shape described a target, not current code.

### Current Run Flow

```text
`patchtrace run -- <command>`
  -> require current working directory to be a Git worktree
  -> capture pre-run porcelain status
  -> create `.patchtrace/runs/<run-id>/`
  -> launch the wrapped command through one PTY stream
  -> write `agent-session.txt`
  -> capture final whole-worktree status
  -> concatenate staged + unstaged final diffs
  -> derive changed-file paths from final status
  -> normalize Codex-like terminal text
  -> require exactly one `Final answer:` marker
  -> infer bounded claims and command/test signals from text
  -> build one `AnalysisResult`
  -> render three Markdown reports
  -> write `run.json`
```

### Current Trust Limitations

- `git-before.txt` is recorded, but it is not used to subtract or classify
  pre-existing changes.
- `patch.diff` represents the final worktree, not a session-attributed delta.
- A commit created during the run can leave a clean worktree and disappear from
  the captured patch.
- Untracked paths may be listed without content/diff evidence.
- Codex-specific final-marker logic lives in generic transcript and command
  analysis modules.
- Final-output extraction is ambiguous without exactly one recognized marker.
- Command/test results are inferred from text rather than bound structured
  events.
- `RunManifest.outcome` describes only zero/non-zero wrapped-command exit and
  cannot represent analysis usefulness.
- The manifest is written after reports; earlier failures may leave incomplete
  folders without a durable failure record.
- Artifact paths have no schema/producer/parser versions or integrity digests.
- `analyze` and `watch` are not implemented.

## Target Architecture

### Target Trust Chain

```text
explicit task file + explicit target repository
  -> one resolved execution root + private Git-metadata run folder
  -> versioned run manifest written before child start
  -> unchanged user task payload + versioned PatchTrace protocol
  -> canonical structured Codex exec capture
  -> raw evidence written privately
  -> evidence items bound by digest and provenance
  -> agent-end Git state captured and session delta classified
  -> structured final output interpreted for every REQ-* and AC-*
  -> PatchTrace executes required verification
  -> verification-end Git state captured and compared with agent-end
  -> deterministic task/claim/evidence analysis
  -> one validated AnalysisResult
  -> verification verdict + recommended action
  -> SUMMARY.md / AGENT_FEEDBACK.md / VERIFICATION_BRIEF.md
  -> human decision
```

### Target Capability Ownership

```text
src/patchtrace/
  cli/          command parsing and user-facing orchestration
  session/      generic PTY or piped subprocess capture
  adapters/     one concrete Codex boundary
  vcs/          repository identity, snapshots, and attribution inputs
  analysis/     one interpretation of task, claims, and evidence
  models/       validated run, evidence, analysis, and report contracts
  reports/      shallow Markdown rendering only
  storage/      private run paths, atomic writes, digests, manifest lifecycle
```

This is a target ownership map, not a requirement to create empty packages or
one file per box. New boundaries appear only when Phase 5 tasks implement them.

No generic adapter registry or plugin framework is planned. A shared adapter
protocol becomes justified only after a second real agent adapter exists.

### Execution And Storage Anchoring

Phase 5 resolves `--repo` to one Git worktree root before launching the child.
That root is:

- the child's initial working directory;
- the selected Git collection scope;
- the repository identity against which Codex `-C/--cd` is checked;
- the anchor used to resolve PatchTrace's private storage root.

The task-file path is resolved against the caller's original working directory
before the child cwd changes. The manifest records caller cwd, requested repo,
resolved worktree root, child cwd, Git metadata directory, and run directory.

The target run root is resolved through Git metadata, equivalent to
`git rev-parse --git-path patchtrace/runs`, not inside the tracked worktree.
PatchTrace creates a private, PatchTrace-owned directory only when the resolved
path is absent or carries its expected ownership marker. A symlink, regular
file, path inside the worktree, or pre-existing unowned directory is a preflight
failure. This avoids `.patchtrace` namespace collisions and makes ordinary
`git add` unable to commit transcripts, prompts, diffs, or task material.

The current implementation still writes `.patchtrace/runs/` under the current
working directory. Moving it is Phase 5 work, not current truth.

Official Git source:
[git rev-parse](https://git-scm.com/docs/git-rev-parse) documents
`--show-toplevel`, absolute path formatting, Git-directory resolution, and
`--git-path` relocation behavior. PatchTrace still validates the resolved path
instead of assuming every Git configuration places it safely. The target
command shape was also checked locally with Git 2.54.0.

## Target Data Contracts

### Run Manifest

The manifest should contain:

- schema version and PatchTrace producer version;
- run ID and lifecycle timestamps;
- requested command and effective command;
- caller cwd, requested repository, resolved repository identity, child cwd,
  Git metadata path, and private run path;
- original Markdown task payload, digest, parsed item IDs, and grammar version;
- requirement/criterion links and declared closed acceptance-evidence
  predicates;
- separately stored/digested PatchTrace execution protocol and response schema;
- proof that trusted mode delivered the unchanged task payload plus the recorded
  protocol to the effective Codex invocation;
- wrapped-command outcome;
- analysis outcome and reason codes;
- package outcome and artifact-write reason codes;
- adapter identity/version and detected Codex version where applicable;
- effective Codex profile/config digest, sandbox, approval policy, hooks/notifier
  state, enabled external writers, network policy, environment allowlist/redaction
  policy, credential sources, temp/scratch paths, and every writable root;
- required-verification authorization, commands, outcomes, bounded output, and
  baseline, agent-end, per-command, and verification-end repository
  fingerprints;
- evidence artifact inventory with digests and sizes;
- generated report paths.

The manifest is created before the wrapped process starts and updated
atomically at meaningful boundaries. This is a small durable lifecycle record,
not a workflow engine.

### Evidence Item

Each evidence item keeps orthogonal fields separate:

| Axis | Examples | Purpose |
|---|---|---|
| Kind | task payload, execution protocol, final message, Git change, command result, transcript | What the evidence represents |
| Capture method | user file, PatchTrace protocol, Git snapshot, Codex JSONL, final-message file, PTY | How it was obtained |
| Directness | direct structured, deterministically derived, text inference | How much interpretation occurred |
| Predicate-atom link | Exact Git/artifact property, named final verification, human inspection, N/A | Which declared deterministic acceptance atom this evidence can satisfy |
| Repository checkpoint | baseline, agent-end, verification-end, N/A | Which lifecycle state the item describes |
| Session attribution | session-attributed, pre-existing, unattributable, N/A | Which session scope owns a Git change |
| Verification freshness | state-bound, stale, unknown, N/A | Whether a command result applies to the final analyzed repo state |
| Structured integrity | complete, incomplete, malformed, mismatched, N/A | Whether the expected structured sources are usable and agree |
| Locator | artifact path + line/event/path/hunk | Where the reviewer can inspect it |
| Integrity | digest, size, schema/producer/parser version | Which exact material was analyzed |

Do not collapse these axes into one quality enum. Phase 6 may prioritize review
using them, but it must remain explainable.

Public enum values are closed and cross-field validated. For example,
`session-attributed` is valid only for Git-change evidence with an attribution
basis, and `complete` structured integrity requires all capture-plan artifacts
that the selected mode declares mandatory.

### Outcomes

Wrapped-command outcome:

| State | Meaning |
|---|---|
| `not_started` | Manifest exists, but child launch has not been attempted |
| `spawn_failed` | Child process never started |
| `exited` | Child exited normally; exit code is recorded |
| `signaled` | Child ended because of a signal; signal is recorded |
| `interrupted` | User/PatchTrace interrupted the run |
| `unknown` | Capture ended without a reliable process outcome |

Analysis outcome:

| State | Meaning |
|---|---|
| `completed` | Required bound inputs were interpreted into one valid `AnalysisResult` |
| `degraded` | Analysis completed with a material but bounded evidence limitation |
| `blocked` | PatchTrace cannot safely perform the intended analysis |

Reason codes explain missing task material, incomplete repository scope,
missing/ambiguous final output, Git failure, malformed structured events,
artifact mutation, or parser failure.

Package outcome:

| State | Meaning |
|---|---|
| `complete` | Manifest and every requested report were published |
| `partial` | The manifest and at least one requested output are usable, but one or more writes failed |
| `failed` | No usable verification package was published |

Artifact-level reason codes name report and manifest publication failures.
Rendering starts only after `AnalysisResult` is finalized. Package failure
cannot retroactively change analysis outcome or verdict, and reports never claim
that sibling artifacts were written; the manifest is authoritative for package
completeness.

A wrapped command may exit zero while analysis is degraded or blocked. A
non-zero command may still produce a completed analysis of the captured failure.

### CLI Exit Semantics

CLI exit is an execution compatibility signal, not a second verification
verdict:

- invalid invocation or preflight input uses Typer's usage exit `2`;
- after a usable manifest, analysis result, and complete package exist, a normal
  wrapped exit is propagated unchanged;
- a wrapped signal returns shell-compatible `128 + signal`; an interrupt
  returns `130`;
- spawn failure, unknown process outcome, blocked analysis, or partial/failed
  package returns PatchTrace failure exit `1` and takes precedence over the
  wrapped status;
- a decisive verdict such as `send_back` or `review_required` does not rewrite
  an otherwise successful wrapper exit. Automation reads the typed verdict from
  the manifest/report rather than guessing it from process status.

The manifest always disambiguates a wrapped exit `1` from PatchTrace's own
failure exit `1`.

### Verification Verdict

`AnalysisResult` carries:

- analysis outcome and reason codes;
- requirement and acceptance-criterion coverage;
- claim assessments;
- evidence gaps and provenance;
- ordered review targets;
- `ready_to_accept`, `send_back`, `review_required`, `rerun_required`, or
  `cannot_assess`;
- one concrete recommended action.

Phase 5 implements the complete coverage and final-verification path required
for `ready_to_accept`. The verdict is decisive within task fulfillment and
evidence quality; it does not perform general code review.

One analyzer-owned precedence rule selects the verdict:

1. `cannot_assess` when the existing run has no usable trusted contract, uses
   an unsupported/incompatible format, or has integrity damage that cannot be
   repaired inside that run;
2. `rerun_required` when a valid supported run names a failed agent execution
   or a missing, stale, malformed, incomplete, or mismatched
   capture/verification step that can be repeated;
3. `send_back` for an explicit unfulfilled requirement, a valid required-check
   failure, a relevant verification-phase delta, scope violation, or material
   claim/evidence contradiction;
4. `review_required` for a human-inspection criterion, bounded risk, ambiguity,
   or unattributable material;
5. `ready_to_accept` only when the supported protocol/schema has complete task
   coverage backed by satisfied declared predicates, successful canonical agent
   execution, controlled effect scopes, state-bound required verification,
   identical relevant quiescent agent-end/verification-end state, complete
   relevant attribution, capture integrity, and no higher-precedence condition.

Renderers cannot promote or recompute a verdict. Mutated artifacts,
unknown-incompatible schemas, and imported bundles without equivalent trusted
provenance cannot emit `ready_to_accept`. A compatible saved trusted run may
retain or recompute it after digest and compatibility checks.

### Failure-Class Mapping

Reason codes are closed within these mutually exclusive classes:

| Failure class | Analysis outcome | Verdict / external behavior |
|---|---|---|
| Invalid task/repo/storage input before safe manifest storage exists | N/A; no `AnalysisResult` | Structured CLI diagnostic and usage/preflight exit; no run package promised |
| Supported run with repeatable agent-process, structured-output, capture, freshness, or verification-integrity failure | `degraded` with the named repeat target | `rerun_required` |
| Missing trusted contract, unknown-incompatible schema/protocol, or post-capture digest/integrity damage | `blocked` | `cannot_assess` |
| Schema-valid `not_done`/`blocked` fulfillment entry, independently contradicted claim, scope violation, valid failed required check, or relevant verification-phase delta | `completed` | `send_back` |
| Human-inspection evidence basis, bounded ambiguity/risk, or bounded unattributable material | `degraded` | `review_required` |
| Successful quiescent canonical agent execution, satisfied declared predicates, controlled effects, state-bound passing checks, complete attribution/integrity, and no relevant verification delta | `completed` | `ready_to_accept` |
| Report/package publication failure after analysis | Analysis outcome/verdict unchanged | Package outcome/CLI failure reports publication state |

A missing structured final response in a supported attempted run maps to the
repeatable-capture row. An unknown schema or an artifact whose recorded digest
no longer matches maps to the blocked row. The analyzer does not choose between
`rerun_required` and `cannot_assess` ad hoc.

The output schema uses exactly `claimed_done`, `not_done`, or `blocked` for each
`REQ-*` and `AC-*`. A missing, duplicate, unexpected, or invalid entry is a
protocol/capture defect and follows the repeatable or incompatible-integrity
row; it is never treated as an omitted task item. A schema-valid `not_done` or
`blocked` is a direct fulfillment failure and follows the `send_back` row.

Canonical Codex terminal outcomes are also closed:

| Wrapped Codex outcome | Analysis/verdict behavior |
|---|---|
| `not_started` after safe package creation or `spawn_failed` | `degraded` / `rerun_required` |
| `exited(0)` with complete compatible structured evidence | Continue through fulfillment/evidence rules |
| `exited(nonzero)` even with a schema-valid final response | Failed agent execution: `degraded` / `rerun_required`; never `ready_to_accept` |
| `signaled`, whether external or PatchTrace-initiated for a declared bound | Failed agent execution: `degraded` / `rerun_required` |
| `interrupted` | Incomplete agent execution: `degraded` / `rerun_required` |
| `unknown` | Incomplete process capture: `degraded` / `rerun_required` |

An unknown-incompatible response protocol or post-capture integrity damage still
takes the higher-precedence `cannot_assess` path. A schema-valid
`not_done`/`blocked` entry selects `send_back` only after the canonical Codex
process itself completed successfully.

## Capture Plans

### Canonical Trusted Codex Exec

```text
user command: `patchtrace run --task-file <path>`
task: unchanged validated Markdown payload
protocol: separately versioned PatchTrace requirement-ID/response instructions
effective agent command: PatchTrace-constructed `codex exec`
transport: piped stdout/stderr, preserved separately
stdout: JSONL event stream
stderr: progress/diagnostic stream
final sources: output-last-message file + schema-valid final agent event
response contract: PatchTrace-owned output schema
command source: JSONL command execution events
failure: map repeatable capture vs incompatible/integrity failure; never fall back
```

PatchTrace owns `--json`, `--output-last-message`, and `--output-schema` for this
mode, records the requested user action and effective command, and rejects
conflicting output flags. The task payload and PatchTrace protocol/schema remain
separate digested artifacts.

Trusted mode also constructs a version-checked effective Codex profile. It fixes
the repository cwd, sandbox, approval policy, network policy, temp behavior, and
every writable root; applies tested CLI config overrides; allowlists inherited
environment variables while recording names/policy but redacting credential
values; and records the effective security-relevant configuration. It rejects
danger-full-access, unaccounted roots/effect channels, command hooks,
notification commands, or MCP/plugin tools that can write outside the selected
evidence scope.

The effect-scope inventory distinguishes the selected repository, a
PatchTrace-owned bounded scratch/temp root when the supported Codex version
requires one, and declared Codex authentication/runtime state. Scratch and auth
state are never task evidence; unknown writable roots or unbounded inherited
environment produce a trusted-mode failure or explicit verdict ceiling. Shell
network access is disabled by default in Phase 5. A task that genuinely requires
network or an external writer needs a later explicit policy/integration;
PatchTrace does not pretend repository evidence covers external side effects.

PatchTrace launches canonical Codex under a supervised process-containment
boundary. Agent-end is a quiescent checkpoint only after the root process has a
reliable successful outcome, all accounted descendants are terminated/reaped,
no descendant can remain with repository write access, and the controlled
effect profile remains intact. A detached/escaped or otherwise unaccounted
descendant makes trusted capture incomplete and selects `rerun_required`; it
cannot coexist with `ready_to_accept`. Phase 5 must source-check and fixture-
prove the macOS containment primitive before implementation closes.

User and project configuration may still supply non-security preferences, but
it cannot silently widen trusted write scope. If a supported Codex version
cannot expose or reliably override the security-relevant configuration,
trusted preflight fails for that version instead of assuming the effective
profile.

Structured capture reports `complete`, `incomplete`, `malformed`, or
`mismatched` integrity. Unknown events remain in raw JSONL. Truncated JSONL,
missing `REQ-*`/`AC-*` IDs, invalid schema output, or disagreement between final
sources never silently falls back to text inference.

### Secondary Interactive Codex

```text
command: explicit interactive `codex ...`
transport: PTY combined stream
adapter: concrete Codex TUI normalizer/final-region extractor
final source: explicit marker-based fallback
directness: text inference
trusted-verdict ceiling: no `ready_to_accept` without complete structured contract
failure: missing/ambiguous final output; never guess from transcript tail
```

Interactive mode remains useful when the user needs a live conversation. It is
not presented as evidence-equivalent to the canonical trusted path.

### Generic Interactive Command

```text
transport: PTY combined stream
evidence: transcript + process outcome + Git snapshots
agent-specific interpretation: none unless a concrete adapter recognizes command
trusted-verdict ceiling: no `ready_to_accept`
```

### Final Required Verification

Agent command events remain useful historical evidence, but trusted required
verification is executed by PatchTrace after agent capture from the explicit
Task Contract section.

Command authorization and effect authorization are separate. Phase 5 executes
`VER-*` under a recorded verification profile that:

- default-denies network and external writers;
- allowlists inherited environment variables and excludes/redacts credentials;
- limits writable scope to the selected repository plus bounded
  PatchTrace-controlled scratch/temp paths;
- starts a supervised process-containment boundary and accounts for
  subprocesses;
- rejects unsupported effect expansion before execution.

A repository/bundle-provided task still requires explicit command confirmation
for public OSS use. Any future network, credential, or external-root grant also
requires a separately recorded human confirmation; the command text alone does
not grant transitive effects.

For each authorized command PatchTrace records:

- exact argv/shell contract and cwd;
- start/end/process outcome, bounded stdout/stderr, timeout, and signal;
- the agent-end fingerprint before any required command;
- repository fingerprint immediately before execution;
- repository fingerprint after execution;
- process-tree containment/quiescence outcome;
- the verification-end fingerprint after the ordered command set reaches a
  quiescent checkpoint.

Verification freshness is:

| State | Meaning |
|---|---|
| `state_bound` | The result applies to verification-end state and no later relevant change made it stale |
| `stale` | Relevant repository state changed after the result |
| `unknown` | The capture cannot bind the result to repository state |
| `N/A` | The command is not a required repository verification |

The baseline-to-agent-end delta is the agent session delta. Any relevant
tracked, staged, or non-ignored change between agent-end and verification-end is
recorded separately as a verification-phase delta. It is not credited to Codex
and selects `send_back`: the submitted state was not stable through final
verification. The snapshots establish that the change appeared during this
phase, not whether the verification command or a concurrent local process wrote
it. Ignored cache output or a task-declared ephemeral path is outside the
relevant fingerprint under the recorded rules.

A later verification-phase change makes earlier command results stale for
acceptance even if their exit code was zero. PatchTrace may finish the
authorized ordered command set to preserve useful diagnostics, but it cannot
stabilize or promote the changed state automatically.

Verification process outcomes use this closed mapping:

| Observed outcome | Evidence/verdict behavior |
|---|---|
| Process starts, exits `0`, output and state capture remain usable | Normal pass evidence; other acceptance rules still apply |
| Process starts and exits non-zero | Valid required-check failure -> `send_back` |
| Process exceeds its declared timeout and PatchTrace terminates it | Valid failure to complete the authorized check within its bound -> `send_back` |
| Process ends by an unrequested signal with a reliable signal outcome | Valid required-check failure -> `send_back` |
| Process cannot be spawned | Missing execution evidence -> `rerun_required` |
| User/PatchTrace interrupts the run, or reliable exit/signal state is lost | Incomplete capture -> `rerun_required` |
| Saved output reaches its cap but PatchTrace keeps draining/discarding until a reliable outcome | Exit/signal mapping remains authoritative; truncation is recorded |
| Truncated bytes were explicitly declared as required evidence, or the cap forces termination/loss of outcome | Incomplete evidence -> `rerun_required` |
| An accounted descendant survives, escapes containment, or cannot be reaped | Incomplete effect/process capture -> `rerun_required` |

This mapping distinguishes a real check result from missing capture. A valid
state-bound failure produces `send_back`; `rerun_required` is reserved for a
supported capture that must actually be repeated.

Official Codex evidence:

- the locally installed CLI is `codex-cli 0.144.1`;
- `codex exec --help` exposes `--json`, `--output-last-message`, and
  `--output-schema`;
- official non-interactive documentation states that `--json` emits JSONL
  events including thread, turn, agent message, command execution, file change,
  and error events, and that `--output-last-message` writes the final agent
  message; `--output-schema` constrains the final response shape.

Source:
[OpenAI Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

The official
[Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents user/project config layers, command hooks, notification commands, MCP
servers, sandbox writable roots, and repeatable CLI overrides. The official
[Codex CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
documents `--add-dir`, cwd, approval, sandbox, and config flags. Phase 5 fixtures
must use the installed version's observed effective behavior, not only the
existence of these keys.

The installed Codex CLI 0.144.1 also exposes `codex sandbox [COMMAND]...`,
permission-profile/config selection, sandbox-state input, explicit network
disablement, cwd, and denial logging. The upstream
[OpenAI Codex CLI README](https://github.com/openai/codex/blob/main/codex-rs/README.md)
documents `codex sandbox` as the host-OS sandbox entry point (Seatbelt on macOS)
and the upstream
[Codex core README](https://github.com/openai/codex/blob/main/codex-rs/core/README.md)
documents policy-controlled network and filesystem roots. It is therefore the
preferred Phase 5 verification-profile mechanism to fixture-prove before
considering a new dependency. Command presence alone is not proof: Task 3 must
verify the effective profile, denial behavior, descendant inheritance, and
quiescence on the supported installed version. This current nested agent
environment cannot itself apply a second Seatbelt profile, so real enforcement
proof remains a Phase 5 macOS dogfood gate.

These are `codex exec` capabilities. They do not prove that the interactive TUI
exposes the same structured stream.

## Session-Scoped Git Attribution

Canonical public labels:

- `session-attributed`;
- `pre-existing`;
- `unattributable`.

`session-attributed` is intentionally useful and strong: the change is assigned
to the controlled PatchTrace agent session under the documented
baseline/agent-end rules.
It is not weakened to a generic "observed" label.

It is also not synonymous with `agent-authored`. Without isolation, PatchTrace
does not prove whether the coding agent, user, hook, or another local process
authored every byte.

### Evidence Captured

- repository root and identity;
- baseline HEAD/index/worktree (`H0`, `I0`, `W0`) and agent-end
  HEAD/index/worktree (`Ha`, `Ia`, `Wa`), including unborn state;
- ancestry relationship when both OIDs exist;
- staged/unstaged status before/after;
- path state, content fingerprint, and private baseline bytes where needed for
  tracked dirty paths and a bounded non-ignored untracked inventory;
- baseline and final diffs where Git can represent them;
- descendant commit diff when HEAD advances;
- explicit limitations for ignored files, submodule contents, multi-repository
  scope, history rewrite, and transient changes absent from both snapshots.

### Attribution Rules

| Case | Attribution |
|---|---|
| Clean path at start, changed/added/deleted at end | `session-attributed` |
| New untracked path absent at start, present at end | `session-attributed` |
| Clean start and descendant HEAD advances, even with clean agent-end worktree | `session-attributed` |
| Dirty path present at start and unchanged at end | `pre-existing` |
| Other paths dirty, but this path clean at start and changed at end | `session-attributed` |
| Dirty tracked/untracked path has a complete private baseline and changes again | Baseline material remains `pre-existing`; baseline-to-agent-end delta is `session-attributed` |
| Pre-existing staged/unstaged material moves into a descendant commit unchanged | Content remains `pre-existing`; the commit event is session activity but does not relabel its bytes |
| A dirty baseline path is partially committed and changes again | Compare complete `W0` material with `Wa`; only the separable baseline-to-agent-end content delta is `session-attributed` |
| Dirty path changes but baseline bytes/state were not captured completely | Affected scope is `unattributable` |
| HEAD becomes non-descendant, repository identity changes, or scope is incomplete | `unattributable` plus degraded analysis |

Content attribution follows material across HEAD, index, and worktree layers;
staging or committing identical baseline bytes does not turn them into new
session content. The session unit is the baseline-to-agent-end delta. The model
is path/hunk-aware where evidence supports it and explicit when only path-level
attribution is possible. It does not attempt worktree virtualization, recover every
reflog/transient action, or inspect arbitrary repositories outside the selected
target.

Symlinks are fingerprinted as links rather than followed outside the selected
repository. Nested repositories, linked worktrees, sparse checkouts, submodule
contents, ignored paths, and incomplete baseline capture are explicit scope
limits. Concurrent local writers are included in the PatchTrace session delta;
PatchTrace does not use `agent-authored` or add repository locking merely to
make a causal claim.

Untracked discovery uses Git's non-ignored path inventory followed by `lstat`;
PatchTrace never opens FIFOs, sockets, devices, or other special files and never
follows symlinks. Regular-file fingerprints have configurable per-file,
total-byte, path-count, and elapsed-time caps with conservative defaults recorded
in the manifest. Oversize or special entries retain path/type/size metadata but
are `unattributable`; exceeding an inventory cap marks repository scope
incomplete and degrades analysis. The product promises complete attribution only
within these recorded bounds, never unbounded filesystem traversal.

For Codex, `-C/--cd` must resolve to the selected repository. `--add-dir`
or config-derived additional writable scope is rejected in trusted Phase 5.
Secondary modes may record incomplete scope, but cannot claim complete
repository coverage.

Every collector subprocess uses `git --no-optional-locks` or
`GIT_OPTIONAL_LOCKS=0`, config-insensitive porcelain, disabled external diff
drivers/fsmonitor hooks where applicable, and explicit bounded flags.
Collection fixtures compare index bytes and semantic HEAD/index/worktree
state before and after. This is required because official
[git status documentation](https://git-scm.com/docs/git-status) states that
default background status may refresh and write index stat information.

See proposed ADR-0004.

## Analysis Boundary

The conceptual public seam remains:

```python
analyze_run(run_evidence) -> AnalysisResult
```

Rules:

- analysis consumes validated, integrity-checked evidence objects;
- agent-specific parsing happens before the generic analyzer;
- task requirements, agent claims, and evidence remain distinct;
- every acceptance criterion links to requirements and an independent supported
  evidence predicate over closed typed atoms; a structured agent entry alone
  is never support;
- analysis evaluates only the user-declared predicate and never infers that a
  changed or present file semantically satisfies natural-language prose;
- report renderers do not read raw transcripts/diffs or rerun rules;
- missing evidence is not false evidence;
- current bounded explicit claim extraction remains rules-first;
- Phase 5 adds requirement coverage without forking the analysis path;
- Phase 6 adds explainable prioritization without correctness scoring.

Private pure functions are encouraged. A large abstract analysis framework is
not.

## Report Boundary

`SUMMARY.md`:

- verification verdict;
- decisive reason;
- requirement and acceptance-criterion coverage counts;
- final required-verification result;
- material attribution limitations;
- one required next action;
- key run/analysis outcome.

`AGENT_FEEDBACK.md`:

- ready-to-paste PatchTrace-authored instruction;
- closed reason text naming task IDs validated under the closed ASCII ID grammar
  and PatchTrace-generated evidence IDs;
- requested correction;
- PatchTrace-controlled local artifact locators.

`VERIFICATION_BRIEF.md`:

- task/run metadata;
- evidence provenance and integrity;
- attribution;
- requirement and claim relationships;
- review-first ordering and reasons;
- cannot-verify items;
- verdict and action.

All three reports receive the same `AnalysisResult`. They differ in audience and
depth, not in interpretation.

`AGENT_FEEDBACK.md` is a machine-generated correction template, not a general
evidence excerpt. Its paste-ready section never contains raw task text, agent
claims/output, command output, diff excerpts, or user-controlled paths/file
names; bounded grammar-validated task IDs and PatchTrace-generated evidence IDs
point back to the original task/protocol and evidence package.
This prevents untrusted evidence from becoming a second-order prompt when the
file is pasted into Codex.

Human-facing excerpts in `SUMMARY.md` and `VERIFICATION_BRIEF.md` pass through
one renderer-independent literal-text function. It strips/escapes terminal
control characters and emits dynamically sized fenced literal blocks (or an
equivalent proved-safe representation) so raw HTML, entities, headings, fence
sequences, reference definitions, autolinks, images, and renderer extensions
cannot become active Markdown or fetch remote content. Renderers do not
implement their own partial escaping.

## Trust Boundaries

| Boundary | Validation | Failure behavior |
|---|---|---|
| User task file -> run | Fixed-section bounded regular non-symlink Markdown, closed ID taxonomy, requirement/criterion links, deterministic evidence predicates, stable bytes, private copy/digest | Fail before launch on unsupported/ambiguous predicates; never infer or repair silently |
| Task + PatchTrace protocol -> Codex | Preserve/digest task bytes and protocol/schema separately; record effective delivery | Block trusted mode on mismatch; never claim an unrecorded prompt |
| CLI target repo/config -> wrapped command | Resolve one repo root; force cwd; constrain/digest sandbox, approval, network, env/credentials, temp, hooks/notifier, external writers, and every writable root | Reject unaccounted effect scope; weaker modes retain explicit verdict ceiling |
| Git metadata -> run storage | Resolve outside worktree; require absent or PatchTrace-owned non-symlink root; private creation | Fail before launch on collision, unsafe type, or worktree overlap |
| PatchTrace -> child process | Record requested/effective command, controlled effect profile, supervised process tree, real terminal state, and quiescence | Surviving/escaped/unaccounted descendant or incomplete containment -> `rerun_required`; never accept |
| PTY stream -> Codex final output | Concrete Codex adapter; exact bounded marker fallback | Missing/ambiguous, never transcript-tail guessing |
| JSONL/final file -> Codex structured evidence | Strict line parsing, current-run controlled path, freshness/digest, event/file reconciliation | Supported repeatable failure -> `rerun_required`; incompatible/digest damage -> `cannot_assess`; no text fallback |
| Git repo -> attributed change | Identity, private dirty baseline bytes, `H0/I0/W0` and `Ha/Ia/Wa`, ancestry, non-refreshing collector, explicit limits | Compute material baseline/session delta without relabeling committed pre-existing bytes |
| Task verification command -> final result | Explicit command authorization, default-deny effect profile, bounded process tree/output, quiescent agent-end/per-command/verification-end fingerprints | Valid fail or relevant verification-phase delta is send-back evidence; effect expansion, surviving descendant, or stale/broken capture prevents acceptance |
| Artifact -> analyzer | Schema/version compatibility and digest check | Refuse mutation/unknown incompatible schema |
| Analyzer -> reports | Pydantic-validated `AnalysisResult` only | No renderer-specific reinterpretation |
| CLI -> external service | N/A | No external transfer by default |

## Privacy And Local Storage

Run material can include task text, prompts, intermediate JSONL events, paths,
diffs, terminal output, command output, and final agent messages.

Target rules:

- run directory permissions are private to the current user where supported;
- files created by PatchTrace use private permissions;
- the default run root is PatchTrace-owned Git metadata outside the worktree,
  never a tracked `.patchtrace/` directory;
- adapter-owned final-message output stays inside this run's private folder;
- raw JSONL is treated as sensitive evidence, not harmless telemetry;
- fixtures contain only sanitized synthetic or reviewed shapes;
- manifests record local paths but do not upload them;
- human-facing reports minimize raw task/output content, use one literal-text
  renderer, and prefer locators plus concise excerpts over duplicating
  sensitive artifacts;
- paste-ready agent feedback contains only PatchTrace-authored closed reason
  text, stable IDs, and PatchTrace-controlled local artifact locators; it never
  embeds raw untrusted evidence;
- untrusted task/output text never becomes active Markdown: raw HTML, entities,
  headings, links, images, reference definitions, autolinks, fence delimiters,
  extensions, and control characters remain literal;
- retention/deletion remains user-controlled until Phase 8 specifies bounded
  continuous-watch lifecycle;
- docs, tests, commits, and PRs never include private runs.

The local trust model detects accidental mutation and inconsistent artifacts.
It is not a tamper-proof boundary against a malicious process running as the
same user; stronger adversarial isolation is deferred until a real requirement
justifies it.

## Versioning And Re-Analysis

The target manifest/evidence format includes:

- schema version;
- PatchTrace version;
- adapter/parser version;
- detected Codex version when available;
- artifact digests.

Phase 7 post-hoc analysis must:

- verify digests before analysis;
- preserve original raw evidence;
- reject unknown incompatible schemas clearly;
- record which analyzer version produced a new report;
- never make a weak imported run look stronger than a wrapped trusted run.

## Testing Strategy

- unit tests for models, normalization, parsing, attribution, outcomes, claims,
  requirement/criterion evidence coverage, verdict mapping, and renderers;
- integration tests for Git repositories, task/run storage, PTY and piped
  capture, controlled Codex config, non-mutating collection, final verification
  effect scope, partial failures, and manifest lifecycle;
- sanitized fixture corpus for Codex TUI and JSONL shapes;
- fake subprocess fixtures for deterministic command behavior;
- misleading acceptance-basis fixtures proving that generic file
  presence/change cannot satisfy a criterion without a supported declared
  predicate;
- delayed, background, and detached-writer fixtures proving process-tree
  containment and quiescent checkpoints for Codex and final verification;
- report-injection fixtures for raw HTML, entities, headings, dynamic fences,
  control characters, reference links, autolinks, renderer extensions, and
  remote-resource syntax;
- second-order prompt-injection fixtures proving that raw task, agent, command,
  diff, and user-controlled locator bytes never enter paste-ready
  `AGENT_FEEDBACK.md`;
- real Codex dogfood used as milestone proof, with private artifacts ignored;
- full lint, format, mypy, pytest, and build gates before PR/merge.

Fragile external formats get fixtures before broader rules.

## Current Versus Target Versus Deferred

| Capability | Current | Target | Deferred |
|---|---|---|---|
| Task input | None | Markdown task is unchanged payload + evaluation contract in Phase 5 | LLM/large-spec inference |
| Run storage | Worktree `.patchtrace/runs/` | Private Git-metadata `patchtrace/runs/` outside worktree | Hosted storage |
| Git | Whole final worktree | Private `H0/I0/W0` to agent-end attribution plus separate verification-end state | Worktree virtualization, causal authorship |
| Codex interactive | PTY + marker | Concrete secondary adapter path with verdict ceiling | Structured interactive interface if documented |
| Codex exec | Generic PTY only | Canonical JSONL + final-message + output-schema under a controlled recorded profile | Second agent |
| Command freshness | Text inference only | Agent-end/per-command/verification-end binding with side-effect detection | General execution provenance |
| Outcomes | Zero/non-zero `outcome` | Wrapped + analysis + package outcomes | Workflow engine |
| Reports | Shared result, free-form verdict copy | Typed task-coverage verdict + provenance | Local HTML if triggered |
| Analyze | Placeholder | Committed compatible saved-run/import phase | Cloud imports |
| Watch | Placeholder | Committed local continuous-watch phase | Hosted daemon |
| Other agents | None | None | Second concrete adapter after real demand |
| LLM | None | None required | Optional only after measured rules-first ceiling |
| Distribution | Source checkout | macOS/Linux OSS, then Windows portability | Hosted/SaaS |

## Architecture Revisit Triggers

- A second real agent requires a concrete adapter.
- Codex removes or materially changes the documented JSONL/final-message
  interface.
- Dirty-repo attribution remains misleading after Phase 5 dogfooding.
- The single `AnalysisResult` becomes impossible to evolve compatibly.
- Public JSON output or package publishing creates a stability contract.
- An optional external/LLM capability is explicitly approved.
- Windows becomes a selected platform target.
