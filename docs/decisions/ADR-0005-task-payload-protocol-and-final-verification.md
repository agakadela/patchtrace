# ADR-0005: Task Payload, Execution Protocol, And Final Verification

- Date: 2026-07-27
- Status: proposed
- Owner: project maintainer(s)
- Extends: ADR-0001, ADR-0002, ADR-0003

## Context

Phase 4 evaluates selected claims from Codex's final output. It does not know
whether:

- the final output addresses the complete task;
- the task used for evaluation is the task Codex received;
- a reported passing test ran after the final relevant edit;
- a command was required by the user or merely happened during the run.

Copying one task file for evaluation while separately asking the user to provide
a prompt creates two sources of truth. Treating free-form final prose as
requirement coverage creates another ambiguity. Trusting a test run inside the
agent session can make old results appear current.

PatchTrace needs one explicit task input, one structured response contract, and
one final verification boundary without becoming a workflow engine or code
reviewer.

## Decision

### Task Contract V1 Is Markdown

Trusted mode accepts one user-authored Markdown file with fixed sections:

```markdown
## Outcome

## Requirements

## Acceptance Criteria

## Required Verification

## Out of Scope
```

PatchTrace validates the file before launch, preserves its exact bytes, copies
it into private run storage, records a digest and grammar version, and applies
this closed taxonomy:

| Section | Cardinality / IDs | Analyzer semantics |
|---|---|---|
| `Outcome` | Exactly one non-empty goal; no completion-list IDs | Product goal summarized by the requirement/criterion result |
| `Requirements` | One or more `REQ-*` items | Codex must return one structured claim per item |
| `Acceptance Criteria` | One or more `AC-*` items linked to `REQ-*` | Codex must return one structured claim; PatchTrace separately evaluates its closed declared evidence predicate |
| `Required Verification` | Zero or more `VER-*` commands, or explicit `N/A` with reason | PatchTrace executes applicable commands after Codex; no Codex completion entry is required |
| `Out of Scope` | Zero or more `OOS-*` constraints, or explicit `N/A` with reason | PatchTrace checks captured evidence for conflicts; no completion entry is required |

Every acceptance criterion declares one closed independent evidence predicate.
Its typed atoms are supported exact Git/artifact properties, named `VER-*`
results with expected outcomes, or explicit human inspection; declared
`all`/`any` composition is the only combination mechanism. The task author
defines which observable predicate satisfies the natural-language criterion.
PatchTrace evaluates it and never infers that generic file presence/change is
semantically sufficient. Unsupported or ambiguous machine predicates fail task
validation. A structured Codex claim is never its own evidence. Every
requirement is linked from at least one acceptance criterion. A necessary
human-inspection atom selects `review_required`; it cannot silently support
`ready_to_accept`. An out-of-scope constraint that deterministic evidence
cannot assess also selects `review_required`; an absent agent scope claim is not
proof.

Malformed, ambiguous, unsupported-encoding, unstable, symlinked, or oversize
task input fails before Codex starts. PatchTrace does not infer or repair the
task silently.

### Preserve Task And Protocol Separately

The unchanged user task is both:

- the payload PatchTrace delivers to Codex; and
- the evaluation contract PatchTrace later uses for coverage.

PatchTrace adds a separately versioned execution/response protocol that:

- exposes stable `REQ-*` and `AC-*` IDs to Codex;
- requires one structured final entry per requirement and acceptance criterion;
- defines `claimed_done`, `not_done`, and `blocked` as the only fulfillment
  statuses plus typed evidence references;
- is enforced through the concrete Codex output schema;
- is stored and digested independently from the task.

`claimed_done` remains an agent claim that requires independent support.
Schema-valid `not_done` or `blocked` is an explicit fulfillment failure and
selects `send_back`. A missing, duplicate, unexpected, or invalid entry is a
protocol/capture defect and selects the applicable `rerun_required` or
`cannot_assess` integrity path; it is never converted into `not_done`.

The manifest records task, protocol, response-schema, adapter, parser, and Codex
versions plus the effective invocation. Reports can therefore state exactly
which user task and PatchTrace protocol governed the run.

### Execute Final Verification

Commands under `Required Verification` are explicit user authorization for the
command, not undeclared transitive effects. After Codex capture ends, PatchTrace
executes those commands from the selected repository root under a recorded
Phase 5 verification profile that:

- default-denies network and external writers;
- allowlists inherited environment and excludes/redacts credentials;
- restricts writable scope to the selected repository and bounded
  PatchTrace-controlled scratch/temp roots;
- supervises the process tree and subprocess lifecycle;
- bounds timeout and stdout/stderr capture/output size;
- records repository-state fingerprints and effect-scope integrity.

Unsupported effect expansion fails before execution. A future network,
credential, or external-root grant requires a separately recorded human
confirmation; listing a command does not grant it implicitly.

PatchTrace captures a quiescent agent-end repository state before the first
command, fingerprints before and after each ordered command, accounts for and
terminates/reaps descendants, and captures a quiescent verification-end state
after the command set. A result supports `ready_to_accept` only when it is
state-bound to verification-end state, the controlled effect profile remained
intact, no process escaped/survived containment, and no later relevant change
made it stale.

A valid failing command is evidence for `send_back`. Process outcomes are
closed rather than interpreted ad hoc:

| Observed outcome | Verdict behavior |
|---|---|
| Captured exit `0` with usable output/state | Normal pass evidence; remaining acceptance rules still apply |
| Captured non-zero exit | `send_back` |
| Declared timeout exceeded and PatchTrace terminates the process | `send_back` |
| Unrequested signal with a reliable signal outcome | `send_back` |
| Spawn fails before the command starts | `rerun_required` |
| User/PatchTrace interruption or loss of reliable exit/signal state | `rerun_required` |
| Saved output reaches its cap but PatchTrace drains/discards to a reliable outcome | The known exit/signal mapping remains authoritative; truncation is recorded |
| Output explicitly required as evidence is truncated, or the cap forces termination/loss of outcome | `rerun_required` |
| Accounted descendant survives, escapes containment, or cannot be reaped | `rerun_required` |

A stale, malformed, incomplete, or mismatched result similarly produces
`rerun_required` when recapture is the next action.

The baseline-to-agent-end delta is the Codex session delta. A relevant tracked,
staged, or non-ignored change between agent-end and verification-end is a
separate verification-phase delta. PatchTrace records it, does not credit it to
Codex, and selects `send_back`; the submitted state was not stable through final
verification. The snapshots prove when the change appeared, not whether the
verification command or a concurrent process wrote it. Ignored cache output and
task-declared ephemeral paths are outside the relevant fingerprint under
recorded rules.

PatchTrace may finish the already-authorized ordered command set for
diagnostics, but it does not auto-apply, stabilize, or accept the changed state.
Any earlier command made stale by a later relevant verification change remains
stale. Capture failure is `rerun_required`; a real relevant mutation is
`send_back`.

### Authorization Boundary

For the project owner's own task file, invoking trusted mode authorizes the
listed verification commands under the closed Phase 5 effect profile. It does
not authorize network, credentials, external roots, or unbounded subprocesses.

For public OSS workflows, a task file obtained from a repository, bundle, or
other untrusted source requires an explicit execution confirmation before
PatchTrace runs its commands. Post-hoc analysis never executes imported
commands silently.

PatchTrace executes only commands written in the validated task. It does not
invent a test command from framework detection, transcript text, or an LLM.

## Alternatives Considered

### Separate Task And Prompt Inputs

Rejected. Two independently editable inputs can diverge, defeating complete
task-fulfillment analysis.

### JSON-Only Task Contract

Rejected for V1. JSON is easy to parse but poor as the primary human-authored
Codex task. Fixed-section Markdown is both readable and deterministically
validated.

### Infer Requirements From Free-Form Markdown

Rejected. Broad semantic inference would require hidden judgment and can omit
or merge requirements unpredictably. V1 uses explicit sections and list items.

### Trust Agent-Run Tests

Rejected as the sole required-verification source. They may run before the final
edit. Agent command events remain evidence, but PatchTrace owns the final check.

### Let PatchTrace Discover And Run Tests

Rejected. Framework detection does not prove user authorization or task
requirements and can execute unexpected code.

### Append Protocol Without Recording It

Rejected. A hidden response instruction would make prompt delivery and future
compatibility unauditable.

## Consequences

### Positive

- The user provides one task once.
- Task delivery and evaluation cannot drift silently.
- Every requirement and acceptance criterion has a structured final-response
  position and an independent coverage path.
- Final verification is compared against separate agent-end and
  verification-end state.
- The verdict remains deterministic and does not require another LLM.
- Protocol evolution is explicit and compatibility-testable.

### Negative / Trade-Offs

- Task Contract V1 has an authoring format.
- PatchTrace owns protocol/schema compatibility with Codex.
- Running verification commands requires process, resource, and authorization
  controls.
- Verification tools that mutate relevant repository state force a send-back;
  ignored/declared ephemeral output needs explicit fingerprint rules.
- Interactive Codex cannot provide the same trusted contract automatically.

## Implementation Constraints

- Use the existing Python stack and one concrete Codex adapter.
- Keep original task bytes, parsed task model, protocol, and response schema as
  separate artifacts.
- Enforce the closed item taxonomy and typed acceptance-evidence predicates.
- Validate a closed typed acceptance-predicate grammar; generic artifact
  presence/change cannot imply semantic fulfillment.
- Do not execute verification before task and repository preflight succeeds.
- Do not execute imported/untrusted verification commands without confirmation.
- Do not use shell inference when an argv contract is available; document the
  chosen V1 command grammar.
- Bound execution time/output, supervise descendants, and require quiescent
  agent-end/per-command/verification-end checkpoints.
- Apply the recorded default-deny network/environment/credential/temp/
  writable-root verification profile to every command and subprocess.
- Prefer the installed version-checked `codex sandbox [COMMAND]...` host-OS
  sandbox entry point for verification when Phase 5 fixtures prove its
  effective policy, descendant inheritance, and denial behavior; do not infer
  enforcement from command availability alone.
- Record enough environment metadata to reproduce the command without storing
  secrets.
- Render task/output excerpts in human-facing reports through one proved-safe
  literal-text path, including raw HTML, entity, reference-link, autolink, and
  fence fixtures.
- Keep paste-ready `AGENT_FEEDBACK.md` limited to PatchTrace-authored closed
  reason text, grammar-validated bounded ASCII task IDs, PatchTrace-generated
  evidence IDs, and PatchTrace-controlled local artifact locators. It must
  contain no raw task, agent, command, diff, or user-controlled locator bytes.
- Keep all raw material local by default.

## Revisit Triggers

- Fixed-section Markdown is unusable in three real dogfood runs.
- Codex removes or changes the documented output-schema behavior.
- Requirement IDs cannot survive realistic task edits or saved-run re-analysis.
- Final verification routinely mutates relevant repository state.
- Supported macOS primitives cannot enforce the default-deny effect profile,
  process containment, or quiescent checkpoints without an approved
  architecture/dependency change.
- Public OSS users need a safer command-authorization model.
- A second trusted agent cannot consume the task/protocol split.
