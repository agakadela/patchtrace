# ADR-0002: Trusted Run Evidence, Outcomes, and Human Decision

- Date: 2026-07-27
- Status: accepted
- Owner: project maintainer

## Context

Phase 4 proved the value of one deterministic analysis result and local reports,
but dogfooding also exposed a trust failure: the final worktree diff could be
reported as run work even when the same dirty paths existed before the session.

PatchTrace also had no preserved task and used one wrapped-command result to
stand in for process, analysis, and package lifecycle. These gaps prevent later
requirement coverage and a trustworthy acceptance recommendation.

The product still needs to remain a proportionate local CLI. It must not solve
these problems with a correctness oracle, advanced Git forensics, or a workflow
engine.

## Decision

### Preserve the task as evidence

Task Contract V1 is plain Markdown. `Outcome` and `Requirements` are required;
`Acceptance Criteria`, `Required Verification`, and `Out of Scope` are optional
or may be `N/A`.

The raw task artifact is preserved unchanged and digest-bound to the run.
Parsing assigns deterministic run-local IDs by section and order. The IDs are
stable for the preserved artifact, not across edited task versions.

A missing task does not prevent a run, but it prevents the highest-trust
recommendation. Phase 5 captures the contract; Phase 6 evaluates satisfaction.

### Give evidence explicit provenance

Material assessments retain their run, source artifact or event, locator,
capture method, and limitations. One validated `AnalysisResult` combines these
facts. Every report remains a shallow view of that result.

Missing or ambiguous evidence lowers trust. `cannot verify` remains a valid
result.

### Attribute Git changes conservatively

Git material is classified as:

- `session-attributed`;
- `pre-existing`;
- `indeterminate`.

Session attribution refers to the captured boundary, not exclusive byte
authorship. Dirty same-path material stays indeterminate unless a simple and
reliable separator is demonstrated.

Capture records the before/after `HEAD`, initial state, clean-to-changed files,
new untracked files, straightforward in-run commits, and limitations. It never
mutates repository state to improve attribution.

### Separate lifecycle outcomes

Process, analysis, and package outcomes are independent. They are also separate
from the evidence verdict and developer decision.

The implementation will add only the states and failure mappings required by
tested paths. It will not create a workflow state machine.

### Keep the human decision boundary

The highest future verdict means that declared evidence gates support an
acceptance recommendation within the Task Contract. It does not mean semantic
correctness was proved.

The developer owns final review, acceptance, rejection, and merge.

## Alternatives considered

### Treat final worktree state as run work

Rejected. It caused a confirmed false positive and cannot distinguish
pre-existing changes.

### Require a Task Contract for every run

Rejected. Generic capture remains useful without a contract. The honest result
is a lower trust ceiling, not refusal to run.

### Use stable IDs across edited task versions

Rejected for V1. Cross-version identity needs explicit authoring or a matching
policy and is unnecessary for run-local evidence.

### Reconstruct all Git authorship

Rejected. Hunk-level reconstruction, stashing, reflog forensics, and temporary
commits add risk and complexity without a demonstrated product need.

### Let each report interpret raw evidence

Rejected. It permits contradictory reports and makes trust rules hard to test.

### Use an LLM to decide task satisfaction

Rejected as a foundation. PatchTrace remains deterministic, local, and useful
without a model. Natural-language criteria may be marked for human review.

## Consequences

Positive:

- later coverage analysis has a preserved task and attributable evidence;
- the confirmed Git false positive can be prevented;
- failures remain understandable across the run lifecycle;
- every report shares the same trust facts;
- verdict language remains useful without claiming correctness.

Costs and limits:

- run manifests and fixtures must evolve;
- some Git material will remain indeterminate;
- a run without a contract cannot reach the strongest future verdict;
- Task Contract edits may produce different generated IDs;
- Phase 5 still does not establish requirement satisfaction or verification
  freshness.

## References

- [PatchTrace product specification](../SPEC.md)
- [Deferred Phase 5 plan](../PHASE_5_PLAN.md)
- [Git status documentation](https://git-scm.com/docs/git-status)
- [Git diff documentation](https://git-scm.com/docs/git-diff)
- [Git revision syntax](https://git-scm.com/docs/revisions)
