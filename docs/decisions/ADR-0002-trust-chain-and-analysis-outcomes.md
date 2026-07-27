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
- one validated Markdown task payload preserved byte-for-byte;
- one separately versioned PatchTrace execution/response protocol;
- the requested and effective wrapped command;
- captured evidence artifacts;
- user-authorized final verification commands and repository fingerprints;
- one analysis result and report package.

Phase 5 parses Task Contract V1, delivers the unchanged task payload to the
canonical structured Codex path, records the separate PatchTrace protocol, and
assesses every requirement. PatchTrace does not infer the task silently from
terminal text.

### Use A Versioned Evidence Envelope

Every material evidence artifact records:

- evidence kind;
- capture method;
- directness/interpretation method;
- declared acceptance-evidence predicate when applicable;
- locator;
- session attribution when applicable;
- repository checkpoint (`baseline`, `agent_end`, `verification_end`, or N/A);
- repository state fingerprint and verification freshness when command evidence
  may satisfy a required check;
- SHA-256 digest and size;
- schema, producer, adapter, and parser versions where applicable.

These are separate axes, not one confidence or quality score.

A passing command supports final required verification only when PatchTrace
executed the user-authorized command after agent capture, its result remains
bound to verification-end state, and the verification phase contains no
relevant repository delta. Verification also requires a recorded default-deny
effect profile, a contained/reaped process tree, and a quiescent terminal
checkpoint. A valid state-bound failing check or relevant verification-phase
delta is evidence for `send_back`; missing, stale, malformed, incomplete,
mismatched, or non-quiescent capture in a valid supported run produces
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

- `ready_to_accept`;
- `send_back`;
- `review_required`;
- `rerun_required`;
- `cannot_assess`.

The verdict determines the next action within PatchTrace's task-fulfillment
contract. PatchTrace does not autonomously accept work and does not present the
verdict as proof of correctness.

Phase 5 implements the requirement-coverage and final-verification checks needed
for `ready_to_accept`.

The analyzer, not a renderer, applies one precedence order:

1. `cannot_assess` when the existing run has no usable trusted contract, uses an
   unknown-incompatible format, or has unrepairable integrity damage;
2. `rerun_required` when a valid supported run names a failed agent execution,
   capture, containment, quiescence, or verification step that can be repeated;
3. `send_back` for schema-valid `not_done`/`blocked` entries, independently
   shown unmet requirements, valid required-check failures, relevant
   verification-phase changes, scope violations, or material contradictions;
4. `review_required` for human-inspection criteria, bounded risk, ambiguity, or
   unattributable evidence;
5. `ready_to_accept` only after independently supported requirement/criterion
   predicates, successful quiescent canonical agent execution, controlled
   effects, state-bound passing verification, identical relevant agent-end and
   verification-end state, relevant attribution, and integrity under a
   supported current schema/protocol.

Failure classes are not selected ad hoc:

| Class | Analysis outcome | Verdict |
|---|---|---|
| Invalid preflight before safe manifest storage | N/A | No verdict; structured CLI failure |
| Repeatable supported agent-process/capture/containment/freshness/verification failure | `degraded` | `rerun_required` |
| Missing contract, unknown-incompatible format, or post-capture integrity damage | `blocked` | `cannot_assess` |
| Real fulfillment/check/scope/verification-phase stability failure | `completed` | `send_back` |
| Human-only evidence or bounded ambiguity/unattributable scope | `degraded` | `review_required` |
| Successful quiescent canonical agent execution and every declared predicate/effect/verification/attribution/integrity condition passes | `completed` | `ready_to_accept` |

The canonical Codex process mapping is exact:

| Wrapped Codex outcome | Analysis outcome | Verdict behavior |
|---|---|---|
| `not_started` after safe package creation or `spawn_failed` | `degraded` | `rerun_required` |
| `exited(0)` with compatible complete structured evidence | Continue through normal analysis | Determined by fulfillment/evidence rules |
| `exited(nonzero)` | `degraded` | `rerun_required`, even if a final schema object exists |
| `signaled` | `degraded` | `rerun_required` |
| `interrupted` | `degraded` | `rerun_required` |
| `unknown` | `degraded` | `rerun_required` |

Only successful canonical agent execution can reach the lower-precedence
fulfillment rows. Unknown-incompatible schema/protocol or post-capture integrity
damage still maps to `cannot_assess`.

Renderers cannot promote the result. Mutated artifacts, unknown-incompatible
schemas, and imported bundles without equivalent trusted provenance cannot emit
`ready_to_accept`. Compatible saved trusted runs may retain or recompute it
after digest and compatibility checks.

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
The tool must decide the next action within its contract; the human remains
responsible for the final choice.

### Treat Wrapped Exit Zero As Successful Analysis

Rejected. A command may exit zero while final output, Git attribution, or task
material is missing.

## Consequences

### Positive

- A saved run can identify the exact material and analyzer context used.
- Partial failures leave a diagnosable manifest.
- Process failure and evidence failure no longer overwrite each other.
- Reports remain consistent and decisive.
- Task coverage and final verification share the same trust chain.

### Negative / Trade-Offs

- Manifests and tests become more explicit.
- Artifact mutation becomes a named failure rather than silently re-analyzing.
- Users provide one task file once for the trusted run.
- Compatibility policy becomes necessary before post-hoc analysis is public.

## Implementation Constraints

- Prefer existing Python/Pydantic/stdlib and supported OS capabilities; any new
  containment runtime dependency requires explicit approval.
- Keep manifest lifecycle bounded to real run stages.
- Do not introduce database, queue, event bus, workflow engine, or external
  telemetry.
- Keep raw artifacts local and private by default.
- Resolve default run storage through Git metadata outside the tracked worktree;
  refuse an unsafe/colliding storage root before child launch.
- Execute only verification commands explicitly authorized by the validated
  task, under a recorded default-deny network/environment/credential/
  temp/writable-root effect profile with supervised subprocess containment,
  process/output/time bounds, and quiescent agent-end, per-command, and
  verification-end fingerprints.
- Evaluate acceptance only through the task's closed typed evidence predicates;
  never infer semantic fulfillment from generic artifact presence/change.
- Use exactly `claimed_done`, `not_done`, and `blocked` as structured
  fulfillment statuses. Missing/duplicate/invalid entries are capture defects;
  valid `not_done`/`blocked` entries are real fulfillment failures.
- Minimize sensitive excerpts in human-facing reports and render untrusted
  artifact content through one inert literal-text path covering raw HTML,
  entities, headings, fences, control characters, reference links, autolinks,
  extensions, and remote resources under injection fixtures.
- Keep paste-ready `AGENT_FEEDBACK.md` limited to PatchTrace-authored closed
  reason text, grammar-validated bounded ASCII task IDs, PatchTrace-generated
  evidence IDs, and PatchTrace-controlled local artifact locators. Prove that
  raw task, agent, command, diff, and user-controlled locator bytes cannot
  become a second-order prompt.

## Revisit Triggers

- The explicit task-file boundary fails repeated dogfooding.
- Public JSON/report schemas require a compatibility guarantee.
- A second independent report consumer needs a different interpretation seam.
- Partial-failure recovery requires more lifecycle detail than the bounded
  manifest can represent.
