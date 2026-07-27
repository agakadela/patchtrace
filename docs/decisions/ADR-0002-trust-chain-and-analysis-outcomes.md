# ADR-0002: Trust Chain, Provenance, Outcomes, And Verification Verdict

- Date: 2026-07-27
- Status: proposed
- Owner: project maintainer(s)
- Extends: ADR-0001
- Supersedes when accepted: ADR-0001's worktree `.patchtrace/runs/` storage
  location; the local-file storage decision remains

## Context

Phase 4 compares bounded explicit agent claims with local evidence, but the
product cannot yet establish:

- which task belongs to the run;
- which mutable artifact was actually analyzed;
- whether a zero-exit command produced a usable analysis;
- whether an analysis limitation affects one claim or the whole run;
- whether all reports reached the same conclusion.

The existing `RunManifest.outcome` collapses process exit into one
`completed`/`wrapped_command_failed` value. Artifact paths have no schema,
producer, parser, or digest metadata. The free-form verdict copy is decisive,
but its contract is not typed.

PatchTrace needs a trust chain without becoming a workflow engine, audit
platform, or correctness oracle.

## Decision

### Bind One Explicit Run

Each trusted run binds:

- one explicit target repository;
- one resolved child/Git execution root;
- one private PatchTrace-owned run folder in Git metadata outside the worktree;
- one explicit raw task contract copied from a user-supplied file;
- the requested and effective wrapped command;
- captured evidence artifacts;
- one analysis result and report package.

Phase 5 captures and binds the raw task. Phase 6 parses task requirements and
assesses requirement coverage. The task file is the user's evaluation contract;
it is not proof that the agent received the same bytes unless a separate
delivery mechanism records that fact. PatchTrace does not infer the task
silently from terminal text.

### Use A Versioned Evidence Envelope

Every material evidence artifact records:

- evidence kind;
- capture method;
- directness/interpretation method;
- locator;
- session attribution when applicable;
- repository state fingerprint and verification freshness when command evidence
  may satisfy a required check;
- SHA-256 digest and size;
- schema, producer, adapter, and parser versions where applicable.

These are separate axes, not one confidence or quality score.

A passing command supports final required verification only when its
command-completion repository fingerprint matches the final analyzed
fingerprint. A valid state-bound failing check is evidence for `send_back`;
missing, stale, malformed, incomplete, or mismatched capture produces
`rerun_required`.

### Separate Outcomes

Wrapped-command outcome distinguishes:

- `not_started`;
- `spawn_failed`;
- `exited` with exit code;
- `signaled` with signal;
- `interrupted`;
- `unknown`.

Analysis outcome distinguishes:

- `completed`: required bound inputs were interpreted into a valid
  `AnalysisResult`;
- `degraded`: analysis completed with a named material limitation;
- `blocked`: PatchTrace cannot safely perform the intended analysis.

Reason codes explain the outcome.

Package outcome independently distinguishes:

- `complete`: manifest and all requested reports were published;
- `partial`: a usable manifest/output exists but one or more writes failed;
- `failed`: no usable verification package was published.

The run manifest is created before child launch and updated atomically at
meaningful capture/analysis/report boundaries. This preserves a diagnosable
record without adding a general state machine.

Rendering happens only after `AnalysisResult` is finalized. A report failure
changes package outcome, not analysis outcome or verdict.

CLI exit preserves the wrapped command's normal exit when the manifest,
analysis, and package are usable. Usage/preflight errors return `2`;
spawn/unknown/blocked/package failures return `1`; signals use `128 + signal`
and interruption uses `130`. The verdict is read from the typed package and does
not overload process exit.

### Preserve One Interpretation

One validated `AnalysisResult` remains the only interpretation consumed by:

- `SUMMARY.md`;
- `AGENT_FEEDBACK.md`;
- `VERIFICATION_BRIEF.md`.

Renderers remain shallow and do not read raw evidence.

### Keep A Decisive Verdict

The product keeps a typed verification verdict:

- `ready_for_human_acceptance`;
- `review_required`;
- `send_back`;
- `rerun_required`;
- `cannot_assess`.

The verdict strongly recommends the next decision. PatchTrace does not
autonomously accept work and does not present the verdict as proof of
correctness.

`ready_for_human_acceptance` is unavailable until Phase 6 implements explicit
requirement coverage and required-verification checks.

The analyzer, not a renderer, applies one precedence order:

1. `cannot_assess` for blocked analysis;
2. `rerun_required` when missing, stale, malformed, incomplete, or mismatched
   evidence requires recapture;
3. `send_back` for omitted requirements, valid required-check failures, or
   material contradictions;
4. `review_required` for bounded risk, ambiguity, or unattributable evidence;
5. `ready_for_human_acceptance` only after complete required coverage,
   verification, and integrity under a supported current schema.

Renderers cannot promote the result. Mutated artifacts, unknown-incompatible
schemas, and imported bundles without equivalent trusted provenance cannot emit
`ready_for_human_acceptance`. Compatible saved trusted runs may retain or
recompute it after digest and compatibility checks.

## Alternatives Considered

### Keep Paths And Free-Form Strings

Rejected. Mutable local paths do not establish which bytes were analyzed, and
free-form outcome semantics drift across reports and versions.

### Store Every Event In An Event-Sourced Ledger

Rejected. A local versioned manifest plus evidence artifacts answers the
confirmed trust problem. Event sourcing would add infrastructure without a
recovery, replay, or multi-consumer requirement.

### Infer The Task From The Transcript

Rejected. Interactive sessions can contain multiple prompts and unrelated
discussion. Silent inference violates the product's conservative trust model.

### Remove The Verdict And Only Show Evidence

Rejected. That would make PatchTrace technically cautious but product-wise weak.
The tool must recommend a next decision; the human remains responsible for the
final choice.

### Treat Wrapped Exit Zero As Successful Analysis

Rejected. A command may exit zero while final output, Git attribution, or task
material is missing.

## Consequences

### Positive

- A saved run can identify the exact material and analyzer context used.
- Partial failures leave a diagnosable manifest.
- Process failure and evidence failure no longer overwrite each other.
- Reports remain consistent and decisive.
- Task coverage can be added without redesigning the trust chain.

### Negative / Trade-Offs

- Manifests and tests become more explicit.
- Artifact mutation becomes a named failure rather than silently re-analyzing.
- Users must provide a task file for the strongest run mode.
- Compatibility policy becomes necessary before post-hoc analysis is public.

## Implementation Constraints

- Use existing Python/Pydantic/stdlib capabilities; no new dependency.
- Keep manifest lifecycle bounded to real run stages.
- Do not introduce database, queue, event bus, workflow engine, or external
  telemetry.
- Keep raw artifacts local and private by default.
- Resolve default run storage through Git metadata outside the tracked worktree;
  refuse an unsafe/colliding storage root before child launch.
- Minimize sensitive excerpts in reports and render untrusted artifact content
  as inert text: neutralize headings, fence delimiters, control characters,
  links, and remote-image syntax under injection fixtures.

## Revisit Triggers

- The explicit task-file boundary fails repeated dogfooding.
- Public JSON/report schemas require a compatibility guarantee.
- A second independent report consumer needs a different interpretation seam.
- Partial-failure recovery requires more lifecycle detail than the bounded
  manifest can represent.
