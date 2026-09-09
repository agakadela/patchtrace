# PatchTrace Architecture

**Last reviewed:** 2026-09-08

Related decisions:

- [ADR-0001: Project Foundation](decisions/ADR-0001-project-foundation.md)
- [ADR-0002: Trusted Run Evidence, Outcomes, and Human Decision](decisions/ADR-0002-trusted-run-evidence-and-outcomes.md)
- [ADR-0003: Codex Capture Modes and Trust Ceilings](decisions/ADR-0003-codex-capture-modes.md)

This document records current system truth and the accepted next architecture.
Product scope is owned by [SPEC.md](SPEC.md). [PLAN.md](PLAN.md) owns active
Phase 5 tasks; implementation has not started. Phase 4.1 closure evidence lives
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

## 2. CURRENT — Phase 4 plus Phase 4.1 T1–T3

### 2.1 Implemented package ownership

```text
src/patchtrace/
├── cli/          command entry points and run orchestration
├── session/      PTY recording and transcript normalization
├── vcs/          Git command boundary and final-state snapshots
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
  -> capture pre-run porcelain status
  -> resolve the canonical Git worktree root and create an external run folder
  -> run the command through Pexpect and preserve the PTY transcript
  -> capture post-run status plus final staged and unstaged diff
  -> identify exactly one marker-bounded final answer, when available
  -> infer bounded claims and command/test signals from text
  -> build one validated AnalysisResult
  -> render SUMMARY, AGENT_FEEDBACK, and VERIFICATION_BRIEF
  -> write run.json
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
SUMMARY.md
AGENT_FEEDBACK.md
VERIFICATION_BRIEF.md
```

The manifest records the wrapped command, timestamps, exit status, a combined
process outcome, artifact paths, Git evidence paths, and `repository_root`.
New runs always record the canonical absolute Git worktree root; older manifests
without this field load with `None` (unknown repository association).
`AnalysisResult` is validated in memory and shared by all report builders; it is
not persisted as a separate artifact.

### 2.4 Confirmed limitations

- `git-before.txt` is recorded but not used to attribute changes.
- Final status and diff can contain pre-existing work.
- Untracked content and commits during the run are incomplete.
- Dirty same-path work cannot be separated.
- The PTY final answer requires exactly one supported marker.
- Missing or ambiguous markers degrade claim evidence; there is no transcript
  tail fallback.
- Command and test evidence is text inference without structured lifecycle.
- No task artifact is captured or delivered by PatchTrace.
- Wrapped-command outcome stands in for multiple lifecycle concerns.

The final Phase 4 dogfood demonstrated the Git false positive: identical
before/after status material was reported as files changed by the run. Phase 5
starts with that confirmed defect; Phase 4.1 is now closed.

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

## 3. ACCEPTED TARGET — Phase 5 architecture (not implemented)

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

The run model separates:

- process outcome;
- analysis outcome;
- package outcome.

The three facts must survive independent failure paths. For example, a wrapped
command may succeed while current transcript analysis is degraded, or a report
write may fail after analysis completes.

Verdict remains a recommendation about evidence. It is not any lifecycle
outcome and does not define the CLI exit code by itself.

Task 4 implements only the smallest model and reason mapping needed by current,
tested capture, analysis, and package-write failures. Tasks 5 and 6 add their
own parsing and delivery reasons only after those failure paths exist. Phase 5
does not introduce a workflow state machine or design a speculative error
catalog.

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
