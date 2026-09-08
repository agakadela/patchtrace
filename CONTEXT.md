# PatchTrace Domain Context

This file is the canonical short glossary for product and system terms. Product
rules belong in `docs/SPEC.md`; implementation details belong in
`docs/ARCHITECTURE.md`.

## Core terms

### Run

One PatchTrace capture boundary around a local command, its evidence, analysis,
and review package.

### Repository association

A run's original canonical Git worktree path, preserved in its manifest. It
groups runs from the same local checkout; it does not establish change ownership
or session attribution. The storage key and move behavior belong in
[ARCHITECTURE.md](docs/ARCHITECTURE.md#25-run-storage-decision--phase-41-t1).

### Task Contract

The explicit task material against which a future high-trust recommendation is
bounded. V1 is simple Markdown with required `Outcome` and `Requirements`
sections and optional `Acceptance Criteria`, `Required Verification`, and
`Out of Scope` sections.

### Raw task artifact

The preserved task source before parsing or semantic normalization. It is bound
to the run by a digest and is the source of a Codex-specific initial prompt.

### Deterministic run-local ID

An ID assigned by section and order while parsing one preserved task artifact.
It is stable for that artifact, not across edited versions of the task.

### Evidence

Captured local material used to support or limit an assessment, such as a task,
session event, command result, Git observation, transcript location, or patch.

### Evidence provenance

The origin, run association, capture method, locator, and known limitations of
an evidence item.

### Claim

An explicit statement attributed to the agent. Claim support is not proof of
code correctness.

### Observed file fact

A bounded observation about captured file material, such as a path appearing in
a diff with a modification or deletion. It does not establish semantic behavior
or that the change occurred during the captured session.

A path-only claim names file operations and targets without a semantic result
(e.g. `Modified auth.py`). Support describes those operations in captured
material; it never attributes the work to this session. A multi-target partial
assessment names both the established operation/targets and unresolved targets.

### Claim support

Accepted Phase 4.1 meanings; implementation status belongs in `docs/PLAN.md`:

- `supported`: evidence establishes the complete factual content of a bounded
  claim within the capture mode's trust ceiling;
- `partially_supported`: evidence establishes a specific identifiable part of
  the claim, and the unresolved part remains explicit;
- `cannot_determine`: available evidence cannot establish the claim, including
  semantic behavior when only path/change facts are observed.

### Verification state

What captured verification shows, independently of whether an agent describes
it truthfully. A supported claim that tests failed still describes failed
verification and must not imply a healthy work result.

### Latest command attempt

The most recent captured invocation of the exact command before identified
final output, including an attempt with an unknown or incomplete result. Earlier
attempts remain history, not a fallback result. In PTY mode these are
transcript-derived observations, not independent execution or freshness proof.

### Requirement coverage

The relationship between one Task Contract item and available evidence.
Coverage may still require human judgment and is not implemented in Phase 5.

### AnalysisResult

The one validated domain result from which all reports are rendered. Report
renderers do not independently reinterpret evidence.

### Verdict

A deterministic evidence assessment within the available task and capture
boundaries. It is distinct from process exit status and from the developer's
final decision.

### Next action

The concrete recommendation produced from the most important captured gap or
supported state.

### Human decision

The developer's final review, acceptance, rejection, or merge decision.
PatchTrace never owns it.

## Lifecycle terms

### Process outcome

What happened to the wrapped command.

### Analysis outcome

Whether PatchTrace analysis completed, was degraded by limited evidence, or
could not proceed.

### Package outcome

Whether the required run artifacts and reports were written successfully.

These outcomes are independent. None is a synonym for verdict.

## Git attribution terms

### Session-attributed

A change attributable to the captured session boundary. This does not prove
that every byte was written exclusively by the agent.

### Pre-existing

Material known to have existed before the run began.

### Indeterminate

Material that available evidence cannot reliably divide between pre-existing
and in-session work. Dirty same-path changes are indeterminate in V1 unless a
simple, reliable separator is found.

## Capture terms

### Interactive PTY mode

The primary compatibility workflow: PatchTrace wraps an interactive command in
a pseudo-terminal and records text. Its final-output evidence is marker-based
and has a lower trust ceiling.

### Structured task mode

An optional Codex-specific task workflow using an official structured transport,
such as `codex exec --json`. It is separate from interactive PTY mode.

### Structured-interactive capture

Typed evidence for the same interactive session. It is a desired property, not
a current capability. Codex App Server remains a candidate pending feasibility.

### Trust ceiling

The strongest assessment a capture mode can support given what its transport
actually observes.

### Task delivery evidence

Evidence of how the preserved raw task artifact was submitted at the nearest
reliable transport boundary. It does not imply model receipt when unobservable
and never implies model understanding.

### Marker-based final output

A final response identified by exactly one supported transcript marker. Missing
or ambiguous markers degrade evidence; PatchTrace does not guess from the
transcript tail.

## Status words

### CURRENT

Implemented and verified behavior in the repository.

### TARGET

Accepted direction that is not yet implemented.

### DEFERRED

Explicitly postponed work.

### CONDITIONAL

Work that requires a future product or evidence trigger before commitment.
