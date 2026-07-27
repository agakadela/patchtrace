# ADR-0004: Session-Scoped Git Attribution

- Date: 2026-07-27
- Status: proposed
- Owner: project maintainer(s)
- Extends: ADR-0001

## Context

The current CLI records pre-run status, but its final `changed-files.txt` and
`patch.diff` describe the whole ending worktree. This can:

- credit pre-existing dirty or staged changes to the recorded session;
- omit committed changes when the final worktree is clean;
- represent untracked paths incompletely;
- support an agent file claim with evidence that predates the run.

This is a trust-chain flaw, not only a report-quality issue.

PatchTrace needs useful session attribution without worktree virtualization or
an unbounded Git forensics system.

## Decision

### Canonical Attribution Labels

- `session-attributed`: the change was absent from the relevant baseline and is
  assigned to the controlled PatchTrace session under the rules below;
- `pre-existing`: the change was already present at session start and did not
  change during the captured delta;
- `unattributable`: pre-existing and in-session portions cannot be separated
  reliably or repository history/scope prevents attribution.

PatchTrace intentionally uses `session-attributed`, not a weaker generic
"observed" label. The session boundary is the product unit.

`session-attributed` is not synonymous with `agent-authored`. Without isolated
execution, PatchTrace does not claim which local actor authored every byte.

### Capture The Baseline And End State

Record:

- selected repository root and identity;
- HEAD OID before/after or explicit unborn state;
- ancestry relationship;
- staged and unstaged status before/after;
- tracked path state and content fingerprints plus a bounded non-ignored
  untracked inventory visible to the selected repository before/after;
- baseline and final diff material where representable;
- descendant commit diff when HEAD advances;
- evidence locators and integrity metadata.

The target repository is explicit. Codex `-C/--cd` must match it.
`--add-dir`, nested repositories, or other writable repositories create
incomplete scope and prevent a claim of complete attribution.

Untracked discovery uses Git's non-ignored inventory and `lstat`. PatchTrace
does not open FIFOs, sockets, devices, or other special files and does not follow
symlinks. Regular-file hashing is bounded by recorded per-file, total-byte,
path-count, and elapsed-time caps. Oversize/special paths keep metadata but are
`unattributable`; exceeding an inventory cap makes repository scope incomplete
and analysis degraded. "Complete" attribution always means complete within
these explicit recorded bounds.

### Attribution Rules

| Baseline/end condition | Result |
|---|---|
| Path clean at start and changed, added, or deleted at end | `session-attributed` |
| Untracked path absent at start and present at end | `session-attributed` |
| Clean start and HEAD advances to a descendant commit | Committed delta is `session-attributed` |
| Dirty path present at start and identical at end | `pre-existing` |
| Other paths dirty, but a specific path is clean at start and changed at end | That path is `session-attributed` |
| Dirty tracked/untracked path changes again and delta portions cannot be separated | Inseparable scope is `unattributable` |
| HEAD becomes non-descendant, repo identity changes, or evidence scope is incomplete | Affected scope is `unattributable`; analysis is degraded |

Where Git evidence permits hunk-level separation, attribution may be more
precise. Otherwise the path-level label and basis are explicit.

### Explicit Limits

Phase 5 does not promise:

- causal proof of agent authorship;
- recovery of every change created and later reset before the end snapshot;
- ignored-file contents;
- attribution inside submodules;
- complete multi-repository attribution;
- attribution through nested repositories, linked worktrees, or sparse checkout
  boundaries when the selected repository does not expose complete state;
- following symlinks outside the selected repository;
- worktree/container virtualization;
- perfect rename or binary-hunk semantics beyond captured path/digest evidence.

These limits are named when they affect the run. They do not weaken supported
clean-path session attribution.

Concurrent local writers are part of the controlled session scope, not proof of
agent authorship. When their contribution is detectable but inseparable, the
affected material is `unattributable`. PatchTrace does not lock the repository
to create a stronger causal claim than its capture model supports.

## Alternatives Considered

### Require A Clean Repository And Refuse Dirty Runs

Rejected as the only mode. It provides a simple strong path but makes the tool
less useful in real workflows. A dirty run remains allowed with precise
pre-existing/unattributable classification.

A future repeated failure may still justify requiring a clean baseline for
`ready_for_human_acceptance`.

### Treat The Final Worktree As Session Evidence

Rejected. It is the current flaw and can misattribute another change.

### Call Everything "Run-Window Observed"

Rejected. It is technically cautious but too weak for the product. PatchTrace
defines and tests a meaningful session-attribution contract.

### Use A Temporary Worktree Or Container

Rejected for now. Isolation would strengthen authorship/causality but changes
the developer workflow and adds Git/environment complexity before baseline
attribution is tested.

### Reconstruct Everything From Reflog

Rejected. Reflog does not reliably capture worktree edits or every relevant
actor and would create false confidence.

## Consequences

### Positive

- Pre-existing work no longer silently supports session claims.
- Clean-path changes receive a clear useful session label.
- Commits made during the run remain visible with a clean ending worktree.
- Dirty repositories remain usable with bounded limitations.
- Reports can prioritize unattributable changes.

### Negative / Trade-Offs

- Git fixtures and models become more detailed.
- Dirty same-path changes may remain unattributable.
- Transient/reset activity can remain invisible.
- Multi-repo and submodule workflows are limited.

## Implementation Constraints

- Use the existing Git CLI and Python standard library.
- Do not mutate the user's index, commits, branches, or working tree.
- Do not create a hidden temporary commit.
- Keep PatchTrace run storage in Git metadata outside the tracked worktree, so
  no blanket `.patchtrace/` exclusion hides a legitimate user path.
- Keep attribution basis inspectable in the run folder/report.

## Revisit Triggers

- Dirty-mode results are repeatedly misleading in dogfooding.
- Users require causal agent authorship.
- Multi-repository or submodule work becomes a primary workflow.
- A temporary worktree can be introduced without breaking the interactive user
  experience.
