# PatchTrace Architecture

System source of truth: current implementation, target design, data flow,
trust boundaries, and deferred architecture.

Product scope and roadmap live in `docs/SPEC.md`.
Detailed tasks for the proposed next phase live in `docs/PLAN.md`.

## Status

- Last reviewed: 2026-07-27
- Baseline: `d8c98c4`, head of open PR #19
- Re-baseline status: proposed, pending human acceptance
- Accepted foundation: `docs/decisions/ADR-0001-project-foundation.md`
- Proposed decisions:
  - `ADR-0002-trust-chain-and-analysis-outcomes.md`
  - `ADR-0003-codex-structured-evidence-boundary.md`
  - `ADR-0004-session-scoped-git-attribution.md`

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

The existing stack is sufficient for the target design. Phase 5 requires no new
runtime dependency.

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
  -> capture plan selected for the actual command
  -> raw evidence written privately
  -> evidence items bound by digest and provenance
  -> Git changes classified by session attribution
  -> agent final output and command results interpreted
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
- raw task-contract artifact and digest;
- task-delivery evidence only when a separate capture mechanism proves which
  bytes reached the agent; the task contract alone is the evaluation contract;
- wrapped-command outcome;
- analysis outcome and reason codes;
- package outcome and artifact-write reason codes;
- adapter identity/version and detected Codex version where applicable;
- evidence artifact inventory with digests and sizes;
- generated report paths.

The manifest is created before the wrapped process starts and updated
atomically at meaningful boundaries. This is a small durable lifecycle record,
not a workflow engine.

### Evidence Item

Each evidence item keeps orthogonal fields separate:

| Axis | Examples | Purpose |
|---|---|---|
| Kind | task contract, final message, Git change, command result, transcript | What the evidence represents |
| Capture method | user file, Git snapshot, Codex JSONL, output-last-message file, PTY | How it was obtained |
| Directness | direct structured, deterministically derived, text inference | How much interpretation occurred |
| Session attribution | session-attributed, pre-existing, unattributable, N/A | Which session scope owns a Git change |
| Verification freshness | state-bound, stale, unknown, N/A | Whether a command result applies to the final analyzed repo state |
| Structured integrity | complete, incomplete, malformed, mismatched, N/A | Whether the expected structured sources are usable and agree |
| Locator | artifact path + line/event/path/hunk | Where the reviewer can inspect it |
| Integrity | digest, size, schema/producer/parser version | Which exact material was analyzed |

Do not collapse these axes into one quality enum. Phase 7 may prioritize review
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
- requirement coverage when Phase 6 implements it;
- claim assessments;
- evidence gaps and provenance;
- ordered review targets;
- `ready_for_human_acceptance`, `review_required`, `send_back`,
  `rerun_required`, or `cannot_assess`;
- one concrete recommended action.

Phase 5 cannot emit `ready_for_human_acceptance` because parsed requirement
coverage does not yet exist. The verdict remains decisive; a correctness limit
is stated once rather than diluting every line.

One analyzer-owned precedence rule selects the verdict:

1. `cannot_assess` when analysis is blocked;
2. `rerun_required` when missing, stale, malformed, incomplete, or mismatched
   evidence must be recaptured;
3. `send_back` for an omitted requirement, a valid required-check failure, or a
   material claim/evidence contradiction;
4. `review_required` for bounded risk, ambiguity, or unattributable material;
5. `ready_for_human_acceptance` only when the current supported schema has
   complete task coverage, required verification, capture integrity, and no
   higher-precedence condition.

Renderers cannot promote or recompute a verdict. Mutated artifacts,
unknown-incompatible schemas, and imported bundles without equivalent trusted
provenance cannot emit `ready_for_human_acceptance`. A compatible saved trusted
run may retain or recompute it after digest and compatibility checks.

## Capture Plans

### Generic Interactive Command

```text
transport: PTY combined stream
evidence: transcript + process outcome + Git snapshots
agent-specific interpretation: none unless a concrete adapter recognizes command
verification freshness: unknown unless a separate state-bound result exists
```

### Interactive Codex

```text
command: `codex ...` without `exec`
transport: PTY combined stream
adapter: concrete Codex TUI normalizer/final-region extractor
final source: explicit marker-based fallback
directness: text inference
verification freshness: unknown
failure: missing/ambiguous final output; never guess from the transcript tail
```

### Structured Codex Exec

```text
command: explicitly requested `codex exec ...`
transport: piped stdout/stderr, preserved separately
stdout: JSONL event stream
stderr: progress/diagnostic stream
final source: PatchTrace-controlled output-last-message path in this run's private folder
command source: JSONL command execution events
verification freshness: repository fingerprint captured at each structured command completion
failure: structured parse/file disagreement degrades or blocks; no silent TUI fallback
```

PatchTrace may add its owned `--json` and `--output-last-message` flags only to
an explicitly requested `codex exec` invocation. It records requested and
effective commands and rejects conflicting user output flags. It never silently
turns an interactive `codex` run into `codex exec`.

`--output-schema` is documented but not required by the Phase 5 design; forcing
a PatchTrace response schema would change the user's agent contract and needs a
separate demonstrated benefit.

Structured capture reports `complete`, `incomplete`, `malformed`, or
`mismatched` integrity. Truncated JSONL is incomplete or malformed; disagreement
between the final-message file and final agent-message event is mismatched.
Neither condition silently falls back to TUI inference.

### Command-Result Freshness

A passing command is not proof about later edits. Each structured command
completion that may serve as verification is paired, while capture is live, with
a repository state fingerprint containing HEAD, index state, and the bounded
supported worktree inventory. The final analyzed repository receives the same
fingerprint.

Command-result freshness is:

| State | Meaning |
|---|---|
| `state_bound` | Command-completion fingerprint equals the final analyzed fingerprint |
| `stale` | A later captured repository change makes the fingerprints differ |
| `unknown` | The capture path cannot bind the result to a repository state |
| `N/A` | The result is not repository verification |

PTY/text-inferred commands normally remain `unknown`; a timestamp or output line
alone does not upgrade them. In Phase 6, a required verification item can support
`ready_for_human_acceptance` only when it is `state_bound`. A valid failing
state-bound result is decisive evidence for `send_back`; `rerun_required` is
reserved for missing, stale, malformed, incomplete, mismatched, or otherwise
untrustworthy capture.

Official Codex evidence:

- the locally installed CLI is `codex-cli 0.144.1`;
- `codex exec --help` exposes `--json`, `--output-last-message`, and
  `--output-schema`;
- official non-interactive documentation states that `--json` emits JSONL
  events including thread, turn, agent message, command execution, file change,
  and error events, and that `--output-last-message` writes the final agent
  message.

Source:
[OpenAI Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

These are `codex exec` capabilities. They do not prove that the interactive TUI
exposes the same structured stream.

## Session-Scoped Git Attribution

Canonical public labels:

- `session-attributed`;
- `pre-existing`;
- `unattributable`.

`session-attributed` is intentionally useful and strong: the change is assigned
to the controlled PatchTrace session under the documented baseline/end rules.
It is not weakened to a generic "observed" label.

It is also not synonymous with `agent-authored`. Without isolation, PatchTrace
does not prove whether the coding agent, user, hook, or another local process
authored every byte.

### Evidence Captured

- repository root and identity;
- HEAD OID before/after, including unborn state;
- ancestry relationship when both OIDs exist;
- staged/unstaged status before/after;
- path state and content fingerprint before/after for tracked paths and a
  bounded non-ignored untracked inventory visible to the selected repository;
- baseline and final diffs where Git can represent them;
- descendant commit diff when HEAD advances;
- explicit limitations for ignored files, submodule contents, multi-repository
  scope, history rewrite, and transient changes absent from both snapshots.

### Attribution Rules

| Case | Attribution |
|---|---|
| Clean path at start, changed/added/deleted at end | `session-attributed` |
| New untracked path absent at start, present at end | `session-attributed` |
| Clean start and descendant HEAD advances, even with clean final worktree | `session-attributed` |
| Dirty path present at start and unchanged at end | `pre-existing` |
| Other paths dirty, but this path clean at start and changed at end | `session-attributed` |
| Dirty tracked/untracked path changes again and portions cannot be separated | `unattributable` at the inseparable scope |
| HEAD becomes non-descendant, repository identity changes, or scope is incomplete | `unattributable` plus degraded analysis |

The model is path/hunk-aware where evidence supports it and explicit when only
path-level attribution is possible. It does not attempt worktree
virtualization, recover every reflog/transient action, or inspect arbitrary
repositories outside the selected target.

Symlinks are fingerprinted as links rather than followed outside the selected
repository. Nested repositories, linked worktrees, sparse checkouts, submodule
contents, ignored paths, and concurrent local writers are explicit scope
limits. When such a condition makes the before/end delta inseparable, the
affected evidence is `unattributable`; PatchTrace does not add repository
locking merely to simulate causal authorship.

Untracked discovery uses Git's non-ignored path inventory followed by `lstat`;
PatchTrace never opens FIFOs, sockets, devices, or other special files and never
follows symlinks. Regular-file fingerprints have configurable per-file,
total-byte, path-count, and elapsed-time caps with conservative defaults recorded
in the manifest. Oversize or special entries retain path/type/size metadata but
are `unattributable`; exceeding an inventory cap marks repository scope
incomplete and degrades analysis. The product promises complete attribution only
within these recorded bounds, never unbounded filesystem traversal.

For Codex, `-C/--cd` must resolve to the selected repository. `--add-dir`
declares additional writable scope that PatchTrace cannot fully attribute in
Phase 5; the analysis cannot claim complete repository coverage.

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
- report renderers do not read raw transcripts/diffs or rerun rules;
- missing evidence is not false evidence;
- current bounded explicit claim extraction remains rules-first;
- Phase 6 adds requirement coverage without forking the analysis path;
- Phase 7 adds explainable prioritization without correctness scoring.

Private pure functions are encouraged. A large abstract analysis framework is
not.

## Report Boundary

`SUMMARY.md`:

- verification verdict;
- most important reason/gap;
- one recommended action;
- key run/analysis outcome.

`AGENT_FEEDBACK.md`:

- ready-to-paste instruction;
- exact omitted/unsupported/conflicting item;
- requested evidence or correction;
- relevant artifact references.

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

## Trust Boundaries

| Boundary | Validation | Failure behavior |
|---|---|---|
| User task file -> run | Explicit bounded regular non-symlink file, stable bytes during copy, supported encoding, private copy and digest | Fail before launch or name missing task limitation; never infer silently; do not claim prompt delivery |
| CLI target repo -> wrapped command | Resolve one repo root; force child initial cwd; check Codex `-C` and `--add-dir` scope | Reject mismatch or degrade incomplete scope |
| Git metadata -> run storage | Resolve outside worktree; require absent or PatchTrace-owned non-symlink root; private creation | Fail before launch on collision, unsafe type, or worktree overlap |
| PatchTrace -> child process | Record requested/effective command and real process state | Persist spawn/exit/signal/interruption outcome |
| PTY stream -> Codex final output | Concrete Codex adapter; exact bounded marker fallback | Missing/ambiguous, never transcript-tail guessing |
| JSONL/final file -> Codex structured evidence | Strict line parsing, current-run controlled path, freshness/digest, event/file reconciliation | Degraded/blocked; no silent text fallback |
| Git repo -> attributed change | Identity, before/after state, fingerprints, HEAD ancestry, explicit scope | Pre-existing/unattributable labels; never whole-worktree credit |
| Command material -> command result | Structured event preferred; PTY and text inference labeled separately; bind completion/final repository fingerprints | Missing/stale/unknown result remains explicit |
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
- reports minimize raw task/output content, use safe escaped display, and prefer
  locators plus concise excerpts over duplicating sensitive artifacts;
- untrusted task/output text never becomes active Markdown: renderers neutralize
  headings, links, images, fence delimiters, and control characters so opening a
  report cannot fetch an attacker-supplied remote image;
- retention/deletion remains a user-controlled local filesystem concern until
  repeated dogfooding justifies a command;
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

Phase 8 post-hoc analysis must:

- verify digests before analysis;
- preserve original raw evidence;
- reject unknown incompatible schemas clearly;
- record which analyzer version produced a new report;
- never make a weak imported run look stronger than a wrapped trusted run.

## Testing Strategy

- unit tests for models, normalization, parsing, attribution, outcomes, claims,
  requirement coverage, verdicts, and renderers;
- integration tests for Git repositories, task/run storage, PTY and piped
  capture, partial failures, and manifest lifecycle;
- sanitized fixture corpus for Codex TUI and JSONL shapes;
- fake subprocess fixtures for deterministic command behavior;
- report-injection fixtures for headings, dynamic fences, control characters,
  links, and remote-image syntax;
- real Codex dogfood used as milestone proof, with private artifacts ignored;
- full lint, format, mypy, pytest, and build gates before PR/merge.

Fragile external formats get fixtures before broader rules.

## Current Versus Target Versus Deferred

| Capability | Current | Target | Deferred |
|---|---|---|---|
| Task input | None | Explicit raw task bound in Phase 5; parsed coverage Phase 6 | LLM/large-spec inference |
| Run storage | Worktree `.patchtrace/runs/` | Private Git-metadata `patchtrace/runs/` outside worktree | Hosted storage |
| Git | Whole final worktree | Session attribution with limited dirty mode | Worktree virtualization, causal authorship |
| Codex interactive | PTY + marker | Concrete adapter keeps explicit fallback | Replacing interactive workflow |
| Codex exec | Generic PTY only | JSONL + final-message structured path | Forced output schema |
| Command freshness | Text inference only | Structured completion bound to final repo fingerprint | General execution provenance |
| Outcomes | Zero/non-zero `outcome` | Wrapped + analysis + package outcomes | Workflow engine |
| Reports | Shared result, free-form verdict copy | Typed decisive verdict + provenance | UI/dashboard |
| Analyze | Placeholder | Saved-run/import flow in Phase 8 | Cloud imports |
| Watch | Placeholder | No active target | Reconsider only after repeated missed-run need |
| Other agents | None | None | Second concrete adapter after real demand |
| LLM | None | None required | Optional only after measured rules-first ceiling |
| Distribution | Source checkout | OSS readiness in Phase 9 | Hosted/SaaS |

## Architecture Revisit Triggers

- A second real agent requires a concrete adapter.
- Codex removes or materially changes the documented JSONL/final-message
  interface.
- Dirty-repo attribution remains misleading after Phase 5 dogfooding.
- The single `AnalysisResult` becomes impossible to evolve compatibly.
- Public JSON output or package publishing creates a stability contract.
- An optional external/LLM capability is explicitly approved.
- Windows becomes a selected platform target.
