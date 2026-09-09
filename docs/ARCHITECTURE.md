# PatchTrace Architecture

**Last reviewed:** 2026-09-09

Related decisions:

- [ADR-0001: Project Foundation](decisions/ADR-0001-project-foundation.md)
- [ADR-0002: Trusted Run Evidence, Outcomes, and Human Decision](decisions/ADR-0002-trusted-run-evidence-and-outcomes.md)
- [ADR-0003: Codex Capture Modes and Trust Ceilings](decisions/ADR-0003-codex-capture-modes.md)

This document records current system truth and the accepted next architecture.
Product scope is owned by [SPEC.md](SPEC.md). [PLAN.md](PLAN.md) owns active
Phase 5 tasks; T1–T4 Git provenance and lifecycle outcomes are implemented.
Phase 4.1 closure evidence lives
in [VERIFY_LOG.md](VERIFY_LOG.md).

## 1. System constraints

PatchTrace is a local Python CLI. It has:

- no server, database, queue, accounts, or billing;
- no required LLM or external service;
- local run folders as its persistence boundary;
- deterministic analysis and Markdown reports;
- a POSIX PTY dependency for the current interactive workflow.

The established stack remains Python 3.11+, Typer, Pexpect, Pydantic v2,
pytest, Ruff, mypy, and `uv`.

## 2. CURRENT — Phase 4, Phase 4.1, and Phase 5 T1–T4

### 2.1 Implemented package ownership

```text
src/patchtrace/
├── cli/          command entry points and run orchestration
├── session/      PTY recording and transcript normalization
├── vcs/          Git command boundary, session envelope and final-state snapshots
├── analysis/     deterministic claim and command-signal analysis
├── models/       validated run and report models
├── reports/      shallow Markdown report builders and renderers
└── storage/      run paths and manifest persistence
```

There is no `adapters` package, command package hierarchy, risk module, verdict
module, database, or public JSON API in the current implementation.

### 2.2 Implemented run flow

```text
patchtrace run -- <command>
  -> validate that cwd is a Git worktree
  -> resolve the canonical Git worktree root and create an external run folder
  -> write an initial partial manifest and checkpoint lifecycle facts
  -> preserve pre-run HEAD, status, staged/unstaged patch and untracked evidence
  -> run the command through Pexpect and preserve the PTY transcript
  -> preserve post-run Git boundary and straightforward commit-range patches
  -> save git-session.json and the legacy final-state artifacts
  -> identify exactly one marker-bounded final answer, when available
  -> infer bounded claims and command/test signals from text
  -> build one validated AnalysisResult
  -> render SUMMARY, AGENT_FEEDBACK, and VERIFICATION_BRIEF
  -> check required artifacts and atomically replace run.json as complete
```

`analyze` and `watch` are explicit not-implemented placeholders.

### 2.3 Current artifacts

One run currently writes:

```text
run.json
agent-session.txt
git-before.txt
git-after.txt
changed-files.txt
patch.diff
git-session.json
SUMMARY.md
AGENT_FEEDBACK.md
VERIFICATION_BRIEF.md
```

The version-2 manifest records the wrapped command, timestamps, observed exit
status, separate process/analysis/package outcomes, failure stage/messages,
required artifact paths, Git evidence paths, and `repository_root`.
New runs record the canonical absolute Git worktree root; the model allows
`None` for fixture material without repository association. Legacy combined
outcomes are no longer accepted; see the compatibility decision in section 2.12.
`AnalysisResult` is validated in memory and shared by all report builders; it is
not persisted as a separate artifact.

### 2.4 Confirmed limitations

- `git-before.txt` is recorded but not used to attribute changes.
- Final status and diff can contain pre-existing work.
- Git attribution and report provenance consume the envelope, including bounded
  untracked bytes and linear commits. File claim assessment still describes
  observed snapshot material and does not establish session attribution.
- Dirty same-path work cannot be separated.
- The PTY final answer requires exactly one supported marker.
- Missing or ambiguous markers degrade claim evidence; there is no transcript
  tail fallback.
- Command and test evidence is text inference without structured lifecycle.
- No task artifact is captured or delivered by PatchTrace.

The final Phase 4 dogfood demonstrated the Git false positive: identical
before/after status material was reported as files changed by the run. Phase 5
T1–T3 address that confirmed defect; Phase 4.1 is closed.

### 2.5 Run storage decision — Phase 4.1 T1

Run packages live at
`$XDG_STATE_HOME/patchtrace/repos/<repository-id>/runs/<run-id>/`, falling back to
`~/.local/state` when `XDG_STATE_HOME` is unset, empty, or relative. This POSIX
convention is used on both macOS and Linux; no dependency is added.

`repository-id` is the full SHA-256 of the filesystem-encoded, resolved absolute
Git worktree root (`git rev-parse --show-toplevel`). Runs from subdirectories or
symlink aliases group together; different checkouts/worktrees remain separate.
Moving a checkout gives it a new storage key. The old package still identifies
its original path through `run.json.repository_root` and its run through `run_id`;
this association is not Git provenance or proof of authorship.

Storage resolves symlinks before checking containment. A destination inside the
target worktree is rejected before creating artifacts or starting the command,
with an instruction to set an external absolute `XDG_STATE_HOME`. Storage
creation errors also stop the run. New runs and their containing `runs` directory
use mode `0700`. CLI output exposes the absolute package path; artifact references
inside the package remain relative and portable. No user `.gitignore` or Git
configuration is changed. Existing `.patchtrace` packages are not moved or
cleaned up; automatic migration and retention are outside T1.

Sources checked with Python 3.11.15 and Git 2.54.0:
[XDG state directories](https://specifications.freedesktop.org/basedir/latest/#variables),
[Python path resolution](https://docs.python.org/3.11/library/pathlib.html#pathlib.Path.resolve),
[Git worktree root](https://git-scm.com/docs/git-rev-parse#Documentation/git-rev-parse.txt---show-toplevel).

### 2.6 File/change evidence ceiling — Phase 4.1 T2

The analyzer separates captured file observations from the whole claim. Semantic
claims such as “Fixed authentication in `auth.py`” remain `cannot_determine`,
even when a matching diff exists. Reference descriptions identify the observed
path/type; the assessment gap identifies what those facts cannot establish.

Only complete path-only statements can receive factual support: `Changed`,
`Updated`/`Modified`, `Added`/`Created`, or `Removed`/`Deleted`, followed by
backticked paths joined by commas and/or `and`. Extra prose stays unresolved.
Path matching preserves whitespace and real `a/`/`b/` directory names; only
a leading `./` is normalized.
`Changed` can match an inventory or diff entry; the other verbs require the
matching diff operation. All targets are considered. `partially_supported`
names a specific established operation and its targets, plus unresolved targets.

Diff operation detection uses unquoted, whitespace-free Git paths: new/deleted file mode or
matching modification file headers. A bare diff header or inventory entry does
not establish the operation type. Repeated entries retain all observed types;
conflicting or unknown types cannot establish a specific operation. Unsupported
forms, including quoted/whitespace-containing Git paths, rename/copy types,
and binary modifications,
remain conservative. Nonempty unparsed diff material cannot establish a
no-changes claim. No natural-language semantic judge or LLM is involved.

All reports consume the existing shared `AnalysisResult`. Captured material can
include pre-existing work; even a supported path-only claim does not establish
who made a change or when. Phase 5 still owns session attribution.

Source checked with installed Git 2.54.0:
[Git patch format](https://git-scm.com/docs/diff-format#_generating_patch_text_with_p).

### 2.7 Command-attempt semantics — Phase 4.1 T3

Command evidence retains all recognized attempts in transcript order before the
identified final output. Claims use the latest invocation of the exact normalized
command, including arguments. A later invocation with different arguments cannot
supply its result. Each attempt ends at the next captured command prompt or final
output; results from unrelated commands cannot fill a missing result.

Positive failure/error counts indicate failure; zero counts do not. A positive
pass count or existing recognized success message can establish a passing result.
Within an attempt, a failure takes precedence over a passing line; a captured
interruption leaves the outcome unknown. Result-less or interrupted latest
attempts support only the invocation, never inherit an earlier pass, and say so
in the claim gap. Earlier attempts remain in the raw transcript for inspection;
the brief's assessment references identify the latest invocation/result. The
bounded command/test signal list is a preview, not a complete execution history.

Quick decisions consider the latest attempt of each exact verification command.
A failed latest attempt requires action even if its associated claim is truthful
or absent. Wrapped-process failure retains first priority. All three reports
consume the shared analysis and explicitly name the transcript/freshness limit.

Phase 4.1 T1–T3 are implemented and the phase is closed. Closure evidence is
recorded in [VERIFY_LOG.md](VERIFY_LOG.md); active Phase 5 tasks belong in
[PLAN.md](PLAN.md).

Phase 4.1 does not establish session attribution,
requirement satisfaction, structured execution proof, or final-state freshness.

### 2.9 Git session envelope — Phase 5 T1

`vcs/envelope.py` owns raw capture facts. `git-session.json` schema version 1
records the canonical repository root, before/after boundaries, history, capture
status, and limitations. Each boundary preserves HEAD (null on an unborn branch),
clean/dirty state within the supported path scope, porcelain XY/path entries,
separate staged/unstaged binary patches, and untracked evidence. Rename detection
is disabled, so a rename appears as deletion/addition rather than guessed identity.
NUL-delimited status parsing preserves UTF-8 paths including whitespace and newlines.

Initial facts cover paths visible to Git status and current differences, not a
copy of all tracked file contents. Regular untracked files retain exact bytes as
base64 plus SHA-256, up to 1 MiB per file and 8 MiB per boundary. Over-limit files
and symlinks keep their paths and explicit content omissions. Tracked patches use
Git's normal content representation; they are not a raw worktree byte archive.

History is `unchanged`, `linear`, or `unsupported`. A supported range is at most
100 direct single-parent commits linking before HEAD to after HEAD. Each commit
retains its ID, parent and binary patch, including changes later reverted in the
same range. Merges, rewrites, backwards movement, truncated ranges and unborn HEAD
ranges retain an explicit limitation. These are history shapes, not attribution
labels. Branch switches or concurrent work are not proof of agent authorship.

Capture never stages, refreshes the index, checks out, commits, stashes or updates
refs. Git uses `--no-optional-locks`, `--no-lazy-fetch`, `--no-replace-objects` and
an invocation-only `core.fsmonitor=false`; diff disables external drivers and
textconv, and forces uncolored patches. Active configured clean/process filters on tracked paths are rejected
before status/diff because Git may execute them while inspecting content. Git
commands have a 30-second timeout. No user configuration is edited.

The root `.patchtrace/` path is excluded from status, patches, untracked bytes and
commit patches, including tracked legacy artifacts. Boundaries are sequential,
not atomic; intermediate/reverted edits are not observable. Dirty same-path byte
separation, partial-commit reconstruction, sparse checkouts, submodules, nested
repositories, ignored files, and non-UTF-8 Git output are unsupported. The envelope
preserves these limits; it does not infer attribution.

CLI persistence records the initial boundary before starting the command and the
final boundary before history capture. A capture failure after repository
validation preserves completed boundaries plus `failed_stage`, `error`, and
`recovery`, prints the partial package path and exits 1. The transcript remains
when the command ran. No complete `run.json` or reports are claimed on that path.
An unwritable storage directory can prevent persistence; stderr reports that
secondary failure. T4 also preserves independent lifecycle facts and records
package-write failures, as described in section 2.12.

New manifests link `session_envelope_path`; this field remains optional for
version-2 fixture material without an envelope. T4's legacy-manifest policy is
recorded in section 2.12. T3 reports consume shared attribution; material without
an envelope cannot establish session attribution from final-state artifacts.

Sources checked with Git 2.54.0: [status](https://git-scm.com/docs/git-status),
[diff](https://git-scm.com/docs/git-diff),
[revision traversal](https://git-scm.com/docs/git-rev-list),
[global options](https://git-scm.com/docs/git),
[content filters](https://git-scm.com/docs/gitattributes), and
[fsmonitor configuration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corefsmonitor).

### 2.10 Git attribution — Phase 5 T2

`analysis/git_attribution.py` derives `AnalysisResult.git_attribution` solely from
the linked T1 envelope, validated through the existing capture dataclasses.
It never consults live Git, the transcript, or legacy final-status artifacts
for attribution. The existing `analyze_run()` entry point still returns one
validated result, including when final-output evidence is missing.

The additive result contains `items` and global `limitations`. Each item has
`material` (`initial`, `final`, `commit`, or `history`), a repository-relative
`path` (null for a range or a commit without captured path changes), optional
`commit_head`, one attribution label, item limitations, and nonempty evidence
references. Locators are JSON Pointers into `git-session.json`.

- Initial path material is `pre-existing`, including content-omission limits.
- Final paths absent from the initial dirty inventory are `session-attributed`
  when capture/history are supported. New untracked paths retain any content
  omission; path appearance does not establish the omitted bytes.
- An initial dirty path remains `pre-existing` only when its status and both
  per-path staged/unstaged patches match, or its complete untracked evidence
  matches, and no captured commit touches it. Status equality alone is insufficient.
- Changed/staged/committed initial dirty paths are `indeterminate`; no hunks or
  partial commits are reconstructed. Initial evidence remains separately visible.
- Each linear commit's path material is `session-attributed` unless the path
  was initially dirty. Reverted commits remain visible. Empty or excluded-only
  commits get a pathless item that explicitly establishes no file changes.
- Unsupported or inconsistent history and incomplete capture yield an
  `indeterminate` history item, indeterminate final material, and limitations.
  Missing, malformed, or unknown-version envelopes yield no invented path items
  and an actionable limitation. Legacy results default to explicitly unassessed
  attribution; legacy manifests never gain attribution from final snapshots.

T2 tightens one capture guarantee without changing the version-1 envelope's
existing fields: new CLI captures use `git diff --default-prefix` and record
`patch_prefixes: "a/b"`. This overrides mnemonic, omitted and custom prefixes
for that invocation, without changing Git configuration. Missing metadata in
older T1 captures loads as null: those patches cannot establish session paths.
Exact unchanged boundary material can still be classified pre-existing without
interpreting a prefix; other later material is indeterminate with a recapture
limitation. Header equality alone cannot distinguish an omitted prefix from
identical custom prefixes, which could otherwise invent a new path.

The patch reader preserves ordered blocks for tracked type changes, quoted
UTF-8 names and binary patches. Unknown patch formats degrade attribution with
a limitation. T1's capture scope
and sequential-boundary limitations still apply. No class proves byte-level
or agent authorship, correctness, or acceptance.

T2 exposes attribution through the analysis API; it does not persist a second
analysis artifact. T3 propagates this result into reports as described below.
Consumers must distinguish material entries from unique-path counts.

Sources checked with Git 2.54.0 and Pydantic 2.13.4:
[patch format](https://git-scm.com/docs/diff-format#_generating_patch_text_with_p),
[default-prefix override](https://git-scm.com/docs/git-diff#Documentation/git-diff.txt---default-prefix),
[dataclass validation via TypeAdapter](https://pydantic.dev/docs/validation/latest/concepts/type_adapter/).

### 2.11 Report provenance — Phase 5 T3

All three report models carry the same `GitAttribution` from `AnalysisResult`.
`reports/provenance.py` renders one shared view: counts by attribution class,
ordered observations with material/path/commit identity, every source reference,
and both item and global limitations. Counts describe observations, not unique
files; initial and final material on the same path remain distinct. Pathless
history and empty-commit observations never become file counts.

Report builders require the shared analysis result. The summary's optional
raw-artifact fallback and all report-model `changed_files` fields are removed;
renderers neither open Git artifacts nor derive attribution. Results for
material without an envelope retain the unavailable/unassessed attribution
limitation, without inventing paths from the final snapshot. T3 changed only
in-memory report models; T4 changes the stored run format as described below.

The common view gives an action for each present class. Verification brief
review targets use the same observations in their existing order: review
session-attributed material, keep pre-existing work separate, and resolve
indeterminate material against its sources. This adds no risk ranking.

The analysis's no-file-changes decision also checks shared attribution, so a
clean final snapshot cannot hide captured commit paths or unresolved history.
Empty final-snapshot notices are explicitly scoped to that snapshot. Legacy
`AnalysisResult.changed_files` remains an observed snapshot inventory for
existing claim assessment, not report provenance. Claim support, verdict
priority, and the semantic/PTY trust ceilings remain unchanged; report Git
attribution does not promote a claim to session authorship or correctness.

### 2.12 Lifecycle outcomes — Phase 5 T4

`models/run.py` owns `RunManifest` schema version 2. It replaces the combined
`outcome` with three independent facts. `AnalysisResult.analysis_outcome` owns
the usable analysis status; CLI copies that result to the manifest and all
report builders consume the same result. Evidence verdict and claim support
remain separate and keep their existing semantics.

| Field | Values and meaning |
| --- | --- |
| `process_outcome` | `not_started`; `completed` with observed exit 0; `failed` with observed exit 1–255; `unknown` with no reliable exit result |
| `analysis_outcome` | `not_run`; `completed` with identified final output and readable changed-file/patch inputs; `degraded` when those inputs are missing or final output is ambiguous; `failed` when analysis raises |
| `package_outcome` | `partial` before completion or when capture/analysis/material validation fails; `failed` for package writes or report generation errors; `complete` after all required artifacts and final manifest are written |

`completed` analysis does not guarantee supported claims, determinate Git
attribution, structured evidence, semantic correctness, or a favorable verdict.
A limited but readable Git envelope keeps its existing provenance limitations.
No verdict controls the package status or CLI exit code.

The model rejects a process status inconsistent with its nullable observed exit
code, and rejects a complete package without finished capture, usable analysis,
`ended_at`, or with recorded failures. `ended_at` records command completion when
observed; otherwise it records when PatchTrace stopped on a handled failure.
It remains null in an unfinished checkpoint. Signals normalize to 128 + signal.
Absent Pexpect exit/signal status stays unknown, never a guessed exit 1.

Persistence is a sequence of ordinary checkpoints, not a workflow state machine.
CLI writes `partial` before capture, `unknown` before attempting launch, observed
process facts after recording, and the usable analysis result before reports.
`artifact_paths` is the required inventory. Before declaring completion, CLI
checks that each required artifact can be opened as a file and read. Storage
revalidates the manifest, writes a sibling temporary file, and replaces
`run.json`. Reports refer to `run.json` for package outcome, so a surviving report
cannot falsely announce completion if a later report or manifest write fails.

Current failure mapping (`failures` contains a stage and error message):

| Failure stage | Process / analysis | Package / CLI |
| --- | --- | --- |
| Git validation or storage creation before a run folder | No manifest guaranteed; process not started | Exit 1 with diagnostic |
| `capture_before` | Not started / not run | Partial, exit 1; preserve envelope failure |
| `process_start` | Not started / not run | Partial, exit 1 |
| `session_capture` | Unknown unless an exit was observed / not run | Partial, exit 1; close the child PTY |
| `capture_after`, `capture_history`, `capture_final_snapshot` | Preserve observed process / not run | Partial, exit 1; preserve envelope failure |
| `analysis` | Preserve observed process / failed | Partial, exit 1 |
| `package_validation` (required file missing or unreadable) | Preserve process and usable analysis | Partial, exit 1 |
| `transcript_write`, `git_artifact_write`, `report_write`, `manifest_write` | Preserve all facts observed before failure | Failed, exit 1; attempt to preserve failure manifest |

A write failure may leave some files present; `failed` does not mean an empty
directory. If the failure manifest also cannot be saved, CLI prints that secondary
failure and the partial path. The last checkpoint survives an unsuccessful
manifest replacement; an initial write failure may leave no manifest. Forced
termination, machine loss, and subsequent external deletion are not crash-durability
or tamper-detection guarantees. No retry, queue, resume API, task-parsing reason
catalog, or task-delivery catalog is introduced.

When package completion succeeds, CLI returns the wrapped command's status,
including non-zero exits and degraded analysis. A PatchTrace failure takes
precedence with exit 1 while any observed child status remains in the manifest.
Missing command arguments return 2. `analyze` and `watch` still return 1 as
not-implemented placeholders.

**Phase 4 compatibility decision:** old unversioned manifests with `outcome`
are rejected by the new strict model, not silently promoted to complete packages.
They do not contain independent analysis/write facts. Existing packages stay
untouched; post-hoc loading/migration is outside this task (`analyze` remains a
placeholder). Phase 4 raw fixtures and their evidence assertions remain intact;
test builders explicitly construct version-2 partial/not-run manifests. The
Git envelope stays at schema version 1. No dependency or package version changes.

Implementation references: [Pydantic model validators](https://docs.pydantic.dev/latest/concepts/validators/#model-validators),
[Pexpect close and exit status](https://pexpect.readthedocs.io/en/stable/api/pexpect.html#pexpect.spawn.close),
and [Path.replace](https://docs.python.org/3.11/library/pathlib.html#pathlib.Path.replace).
Locked versions: Pydantic 2.13.4, Pexpect 4.9.0, Typer 0.26.8; Python 3.11+.

## 3. ACCEPTED TARGET — Remaining Phase 5 architecture

Phase 5 strengthens capture and provenance. It does not implement requirement
satisfaction or final-verification freshness.

### 3.1 Target data flow

```text
optional explicit task input
  -> preserve raw task artifact and digest
  -> capture initial Git and lifecycle envelope
  -> deliver task only through an explicit supported agent mode
  -> capture session evidence at that mode's observable boundary
  -> capture final Git and lifecycle envelope
  -> classify evidence provenance and limitations
  -> build one validated AnalysisResult
  -> render verdict, next action, and reports
  -> human review and decision
```

Task parsing or delivery may fail after the run boundary exists. Process,
analysis, and package outcomes therefore precede and remain independent of
Codex-specific task delivery.

### 3.2 Capability ownership

Existing packages keep their current responsibilities:

| Package | Phase 5 responsibility |
|---|---|
| `cli` | Choose an explicit capture mode, accept task input, orchestrate the run, and map terminal exit behavior without deciding evidence semantics. |
| `session` | Own generic process/PTY transport, raw transcript capture, and agent-agnostic terminal cleanup. |
| `vcs` | Capture non-mutating before/after Git facts and produce attribution inputs. |
| `analysis` | Combine validated task, Git, agent-specific, command, and lifecycle evidence into one result and enforce trust ceilings without interpreting Codex TUI text. |
| `models` | Validate task, provenance, outcome, delivery, and analysis data. |
| `reports` | Render only the shared result and evidence references. |
| `storage` | Preserve raw artifacts, digests, manifests, and package completion facts. |

Task 6 adds one concrete Codex-specific boundary. It owns interactive task
delivery, Codex TUI rules, marker-based final-output extraction, Codex-specific
evidence locators, and any later approved structured events or final-message
selection. It appears with the concrete T6 implementation, not as an empty
abstraction. It is not a plugin registry or a generic multi-agent framework.

### 3.3 Git capture envelope

The V1 Git boundary records, without repository mutation:

- `HEAD` before and after;
- initial and final clean/dirty state;
- sufficient initial material to recognize pre-existing paths;
- previously clean tracked files changed during the run;
- new untracked files;
- commits created within a straightforward captured history range;
- explicit limitations for non-linear or inseparable cases.

Analysis assigns:

- `session-attributed`;
- `pre-existing`;
- `indeterminate`.

The classification applies to the captured session boundary, not authorship of
each byte. Dirty same-path changes remain `indeterminate` in V1. No stashing,
temporary commits, index rewriting, branch changes, or worktree cleanup is
permitted.

### 3.4 Lifecycle outcomes

Implemented in T4; section 2.12 owns the current contract. Task capture and
interactive delivery extend those facts only when their concrete failure paths
exist. They must preserve process, analysis, package, and verdict independence.

### 3.5 Task Contract capture

The raw Markdown task is preserved unchanged and digest-bound to the run.
Parsing validates required and optional sections and produces deterministic
run-local IDs stable for that preserved artifact only.

The parsed representation is an analysis input. It is not a predicate program.
Phase 5 records task material and limitations; Phase 6 evaluates requirement
satisfaction.

A missing task is allowed but caps trust. An invalid provided task produces an
explicit parsing failure and lifecycle outcomes rather than silently running
with rewritten content.

### 3.6 Task delivery boundary

For a Codex-specific mode, the preserved raw task artifact is the source of the
initial prompt. The manifest records:

- delivery mode and supported transport;
- the artifact digest used as the source;
- the nearest boundary PatchTrace actually submitted or observed;
- whether delivery was attempted and what that boundary confirmed;
- any unobservable receipt limitation.

PatchTrace does not claim byte-for-byte receipt if the official transport does
not expose it, and never claims model understanding.

For a generic wrapped command, PatchTrace preserves the task for analysis but
marks delivery as unverified. It does not infer how arbitrary commands consume
arguments or stdin.

### 3.7 Capture modes and trust ceilings

| Mode | User experience | Evidence boundary | Phase 5 ceiling |
|---|---|---|---|
| Generic PTY transport | Existing wrapped-command terminal session | Raw transcript, agent-agnostic cleanup, exit status, and Git envelope | No agent-specific final-output claim without a concrete boundary. |
| Interactive Codex compatibility | Existing interactive Codex session over generic PTY transport plus the concrete Codex boundary | Codex TUI interpretation, exact marker when present, transport-bounded task delivery, and Git envelope | Final output remains marker-based; missing or ambiguous marker degrades analysis. |
| Structured-interactive candidate | Same interactive session, only if officially observable without a replacement client | App Server typed events to be tested | Not accepted; the prototype must return `GO`, `NO-GO`, or `CANNOT VERIFY`. |

No mode may claim evidence above what its transport observes. A production
`codex exec --json` task mode, JSONL parser, and real structured-task dogfood are
not part of T6 or the Phase 5 exit criteria. They remain a separate candidate
slice requiring human approval or a concrete dogfood trigger, independently of
the App Server result.

### 3.8 App Server feasibility gate

The time-boxed prototype asks only:

1. Do the required typed final-message, command-result, file-change, and
   lifecycle events exist?
2. Do they belong to the same interactive session the user is operating?
3. Can PatchTrace obtain them through an official route without building its
   own client?
4. Is the required surface stable rather than private or experimental for the
   needed fields and transport?
5. What is the minimum production integration cost?

Needing a custom TUI, a large protocol proxy, or private formats is `NO-GO` for
Phase 5. The prototype is not a production integration.

If the result is `NO-GO` or `CANNOT VERIFY`, Phase 5 can still close. PTY then
remains marker-based compatibility mode, with no structured-interactive
high-trust final output, and all verdicts and reports retain that ceiling.

## 4. Trust boundaries

| Boundary | Required behavior | Failure behavior |
|---|---|---|
| CLI task input -> raw artifact | Preserve source, compute digest, validate separately. | Keep exact failure evidence; do not rewrite into a valid task. |
| Raw task -> Codex transport | Submit only in an explicit Codex mode and record the observable boundary. | Mark delivery failed or unverified; do not claim receipt. |
| Wrapped process -> capture | Record process lifecycle and mode-specific evidence. | Preserve process outcome independently of analysis/package outcomes. |
| Generic PTY text -> Codex boundary | Keep transport and cleanup agent-agnostic; pass preserved text to the concrete boundary. | Generic session code does not select a Codex final answer. |
| Codex boundary -> final output | Apply supported Codex TUI markers and evidence locators. | Degrade on missing or ambiguous marker; never guess the tail. |
| Approved structured Codex events -> typed evidence | If a later slice is approved, consume documented event fields inside the Codex boundary. | Degrade or reject unsupported/experimental evidence instead of parsing private formats. |
| Git repository -> attribution | Observe before/after facts without mutation. | Classify inseparable material as `indeterminate`. |
| Evidence -> AnalysisResult | Validate provenance and apply the mode ceiling once. | Return degraded/blocked analysis with actionable gaps. |
| AnalysisResult -> reports | Render the same facts and references everywhere. | Package outcome exposes incomplete writes; renderers do not invent fallback analysis. |
| CLI -> external services | N/A for accepted scope. | No network or hosted service is required for normal operation. |

## 5. Storage and compatibility

Phase 5 extends the local run package only with artifacts required by accepted
tasks. Exact filenames and schema fields are chosen in their implementation
slice and validated with fixtures.

Raw evidence and derived data must remain distinguishable. Digests identify
preserved artifacts; they do not certify truth. Any future post-hoc compatibility
contract belongs to Phase 8.

## 6. Verification strategy

Every capability is defined first by fixtures and focused integration tests.
Phase 5 requires:

- temporary Git repositories covering clean, dirty, untracked, and committed
  runs;
- fake interactive commands for process and package failures;
- Task Contract fixtures preserving exact source and deterministic parsing;
- interactive Codex boundary fixtures for task delivery, TUI markers, and
  evidence locators;
- official App Server schema or event examples only for the Task 7 feasibility
  result;
- real dogfood before phase closure.

The full quality gate remains Ruff lint and format check, mypy, pytest, and
build. App Server feasibility evidence is recorded as research/prototype proof,
not as passing production capability.

## 7. DEFERRED OR CONDITIONAL

- requirement satisfaction and final verification: Phase 6;
- evidence quality and review prioritization: Phase 7;
- post-hoc analyze: Phase 8;
- OSS hardening and distribution: Phase 9;
- watch, Windows, second agent integration, GitHub, HTML, LLM, and hosted
  workflows: conditional.

No event bus, workflow engine, database, queue, dependency-injection framework,
generic plugin system, or full Git forensics is justified by the local CLI.

## 8. Official interface references

- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/)
- [Codex App Server](https://developers.openai.com/codex/app-server/)
- [Git status](https://git-scm.com/docs/git-status)
- [Git diff](https://git-scm.com/docs/git-diff)
- [Git revisions](https://git-scm.com/docs/revisions)
