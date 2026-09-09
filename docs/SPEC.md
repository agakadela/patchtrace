# PatchTrace Product Specification

**Status:** accepted product re-baseline after Phase 4

**Product stage:** local CLI, pre-OSS

**Current implementation:** Phase 4.1 complete

**Active phase:** Phase 5 — Trusted Capture and Session Provenance (T1–T3 implemented; T4 lifecycle outcomes next)

**Following phase:** Phase 6 — Task Coverage and Final Verification

## 1. Product definition

PatchTrace is a local evidence and verification layer for coding-agent runs.
Given captured evidence within an explicit task contract, it recommends the next
developer action.

The product helps a developer decide whether to:

- accept a run after review;
- begin manual review at the highest-risk evidence gap;
- run missing verification;
- rerun the task;
- send concrete feedback to the agent.

PatchTrace does not prove semantic correctness. It does not replace code review,
security review, or developer judgment, and it never makes the final acceptance
or merge decision.

## 2. Primary user and job

The primary user is a developer working locally with a coding agent in a Git
repository.

The user's job is:

> Determine, quickly and honestly, what happened during this agent run, how the
> result relates to the requested task, what evidence supports the result, and
> what to do next.

The primary experience remains an interactive terminal workflow. Higher-quality
structured capture may be offered where an official interface supports it, but
it must not silently replace interactive work with a different task experience.

## 3. Questions PatchTrace should answer

In its intended product state, PatchTrace should make the following questions
reviewable:

1. What was the agent asked to do?
2. What did the agent claim it did?
3. Which final output belongs to this run?
4. Which Git changes are attributable to the captured session boundary?
5. Which changes pre-existed the run or remain indeterminate?
6. Which commands and tests ran, and what results were captured?
7. Are those results fresh for the final analyzed repository state?
8. Which requirements and claims have supporting evidence?
9. What is contradicted, omitted, incomplete, or unverifiable?
10. Where should human review begin?
11. What concrete follow-up should be sent to the agent?

The roadmap orders these capabilities by evidence dependency. Their presence in
this list is not a claim that they are implemented today.

## 4. Product contract

### 4.1 Inputs

A run may include:

- an explicit Task Contract;
- a wrapped agent or local command;
- the repository state before and after the run;
- captured session, command, file-change, and lifecycle evidence;
- optional final verification authorized by the user in a later phase.

A run without a Task Contract remains valid. PatchTrace must state that it
cannot evaluate task coverage or issue its highest-trust recommendation.

### 4.2 Outputs

PatchTrace produces a local, inspectable package containing preserved evidence,
a validated analysis result, and shallow human-readable reports.

Every material assessment must distinguish:

- observed evidence;
- inference from evidence;
- missing or ambiguous evidence;
- a recommendation to the developer.

`cannot verify` is a complete and expected result, not an internal error.

### 4.3 Highest verdict boundary

The highest future verdict means:

> Declared evidence gates were satisfied, and captured evidence is sufficient
> to recommend acceptance within the preserved Task Contract.

It does not mean:

> PatchTrace proved the implementation semantically correct.

The developer owns final review, acceptance, and merge.

## 5. Task Contract V1

Task Contract V1 is plain Markdown, not a DSL.

Required sections:

- `Outcome`
- `Requirements`

Optional sections, which may be omitted or explicitly marked `N/A`:

- `Acceptance Criteria`
- `Required Verification`
- `Out of Scope`

PatchTrace must:

- preserve the raw task artifact without semantic rewriting;
- bind the artifact to the run with a digest;
- derive the Codex-specific initial prompt from that same artifact;
- retain both parsed structure and the raw source;
- assign simple deterministic run-local IDs by section and order.

Generated IDs are stable for the preserved task artifact. They are not promised
to remain stable after the task text is edited.

Phase 5 establishes capture, validation, preservation, and binding. It does not
evaluate full requirement satisfaction; that belongs to Phase 6.

Task Contract V1 must not introduce:

- typed predicate syntax;
- `all` or `any` expression trees;
- an acceptance policy engine;
- automatic claims that a changed file proves a natural-language requirement.

## 6. Evidence and trust

### 6.1 Evidence provenance

Evidence must retain enough provenance to answer where it came from, which run
it belongs to, how it was captured, and what limitation applies.

All report renderers consume one validated `AnalysisResult`; renderers do not
recompute evidence semantics independently.

### 6.2 Git attribution

Git evidence uses three honest attribution classes:

- `session-attributed` — the change is attributable to the captured session
  boundary;
- `pre-existing` — the material existed before the run;
- `indeterminate` — available evidence cannot separate the two reliably.

`session-attributed` does not prove that every byte was written exclusively by
the agent. A dirty same-path change remains `indeterminate` unless a simple,
reliable mechanism can separate it.

PatchTrace must not mutate the worktree, index, branch, or history to improve
attribution.

### 6.3 Capture-mode ceilings

Each capture mode has a trust ceiling determined by what its supported
transport can actually observe.

- Interactive PTY is a marker-based compatibility mode.
- Codex structured execution may be a separate, higher-evidence task mode.
- Codex App Server is a candidate for structured-interactive capture, pending a
  feasibility result.

A missing or ambiguous PTY final-answer marker degrades final-output evidence.
PatchTrace must not infer the final answer from an arbitrary transcript tail.

Transport evidence may establish how a task was submitted at the nearest
reliable boundary. It does not establish byte-for-byte receipt when that is not
observable, and never establishes that a model understood the task.

## 7. Run lifecycle

PatchTrace treats these as separate concerns:

- process outcome — what happened to the wrapped command;
- analysis outcome — whether evidence analysis completed, degraded, or could
  not proceed;
- package outcome — whether required run artifacts and reports were written.

These outcomes exist independently of Task Contract parsing or Codex delivery.
An evidence verdict is not the CLI exit status and must not obscure failures in
another lifecycle concern.

The exact V1 model and failure mapping are owned by the architecture and the
[active Phase 5 plan](PLAN.md) rather than duplicated here.

## 8. Current implementation

The CLI currently:

- wraps one command in a PTY;
- preserves a transcript;
- captures Git status before and after;
- captures the final staged and unstaged diff visible after the run;
- preserves the Git session envelope described in
  [ARCHITECTURE.md](ARCHITECTURE.md#29-git-session-envelope--phase-5-t1);
- extracts bounded claims from exactly one marker-identified final answer;
- infers command and test signals from text;
- builds one deterministic `AnalysisResult`;
- renders a summary, agent feedback, and verification brief with shared Git
  attribution, source references, limitations, and provenance-aware review targets;
- stores one ten-artifact local package.

Known current gaps:

- final Git state is not session-scoped provenance;
- dirty same-path work and unsupported history remain indeterminate;
- attribution describes session boundaries, not agent or byte-level authorship;
- command results and final messages are not structured in PTY mode;
- no Task Contract is captured;
- lifecycle outcomes are conflated;
- verification freshness and requirement coverage are absent.

These are product gaps, not permission to overstate current evidence.

### Completed Phase 4.1 hardening

Phase 4.1 addressed artifact containment and known overconfirmation paths.
Storage containment (T1), file/change assessment (T2), and command-attempt
semantics (T3) are implemented and verified; closure evidence is recorded in
[VERIFY_LOG.md](VERIFY_LOG.md):

- default run storage moves outside the target working tree without modifying
  user Git configuration or `.gitignore`;
- observed path/change facts remain separate from semantic claim support;
- a whole multi-file claim cannot be supported by evidence for only one target;
- command claims use the latest captured attempt, including unknown or incomplete
  results, while retaining prior attempts;
- claim truth and verification state remain distinct: confirmed failed
  verification drives the next action even when the agent describes it truthfully.

A fact about captured diff material does not establish session attribution. A
transcript-derived command result does not establish final-state freshness.
Phase 5 provenance and Phase 6 coverage/freshness retain their accepted scope.

## 9. Product requirements

### Required direction

PatchTrace must remain:

- local-first and inspectable;
- deterministic and rules-first by default;
- usable without an LLM or hosted service;
- human-in-the-loop;
- explicit about evidence gaps and trust ceilings;
- organized around small, testable capability slices;
- proportional to a local CLI.

### Deferred or conditional

The following require a concrete trigger before entering a committed phase:

- continuous watch mode;
- Windows support;
- a second agent integration;
- GitHub or pull-request integration;
- an HTML viewer;
- optional LLM assistance;
- hosted or team workflows.

### Non-goals

PatchTrace is not:

- a correctness oracle;
- a general AI code reviewer;
- a security scanner;
- an autonomous repair, acceptance, or merge agent;
- a guarantee against regressions;
- a generic multi-agent platform;
- a SaaS product in the current roadmap.

It also does not need a plugin registry, workflow engine, event bus, database,
queue, dependency-injection framework, or large public API for the accepted
local CLI scope.

## 10. Success measures

The product is moving in the right direction when:

- a developer can trace each material recommendation to preserved local
  evidence;
- pre-existing work is not falsely presented as session-attributed;
- missing evidence lowers trust instead of being guessed;
- a preserved task anchors coverage analysis;
- reports agree because they consume the same analysis result;
- dogfooding exposes limitations as explicit outcomes;
- the developer remains the final decision-maker.

Phase-specific exit criteria live in [ROADMAP.md](ROADMAP.md), and detailed work
for only the active phase lives in [PLAN.md](PLAN.md). Phase 5 is active with
its previously accepted task scope unchanged.
