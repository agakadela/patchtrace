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

- `session-attributed`: the baseline-to-agent-end delta is assigned to the
  controlled PatchTrace agent session under the rules below, including later
  changes to a dirty path whose baseline was captured completely;
- `pre-existing`: material already present in the captured baseline;
- `unattributable`: baseline/agent-end evidence, repository history, or scope is
  too incomplete to compute the session delta reliably.

PatchTrace intentionally uses `session-attributed`, not a weaker generic
"observed" label. The session boundary is the product unit.

`session-attributed` is not synonymous with `agent-authored`. Without isolated
execution, PatchTrace does not claim which local actor authored every byte.

### Capture Baseline Layers And Agent-End State

Record:

- selected repository root and identity;
- baseline HEAD/index/worktree (`H0`, `I0`, `W0`) and agent-end
  HEAD/index/worktree (`Ha`, `Ia`, `Wa`) or explicit unborn state;
- ancestry relationship;
- staged and unstaged status before/after;
- tracked path state, content fingerprints, and private baseline bytes where
  needed, plus a bounded non-ignored untracked inventory before/after;
- baseline and final diff material where representable;
- descendant commit diff when HEAD advances;
- evidence locators and integrity metadata.

The target repository is explicit. Codex `-C/--cd` must match it. Trusted Phase
5 rejects `--add-dir`, config-derived extra writable roots, nested repositories,
or other writable repositories. Secondary modes may record incomplete scope,
but cannot claim complete attribution.

Untracked discovery uses Git's non-ignored inventory and `lstat`. PatchTrace
does not open FIFOs, sockets, devices, or other special files and does not follow
symlinks. Regular-file hashing is bounded by recorded per-file, total-byte,
path-count, and elapsed-time caps. Oversize/special paths keep metadata but are
`unattributable`; exceeding an inventory cap makes repository scope incomplete
and analysis degraded. "Complete" attribution always means complete within
these explicit recorded bounds.

### Attribution Rules

| Baseline/agent-end condition | Result |
|---|---|
| Path clean at start and changed, added, or deleted at end | `session-attributed` |
| Untracked path absent at start and present at end | `session-attributed` |
| Clean start and HEAD advances to a descendant commit | Committed delta is `session-attributed` |
| Dirty path present at start and identical at end | Baseline material is `pre-existing`; no session delta |
| Other paths dirty, but a specific path is clean at start and changed at end | That path is `session-attributed` |
| Dirty tracked/untracked path has a complete private baseline and changes again | Baseline material is `pre-existing`; baseline-to-agent-end delta is `session-attributed` |
| Pre-existing staged/unstaged bytes move into a descendant commit unchanged | Content remains `pre-existing`; committing it does not relabel the bytes |
| A dirty path is partially committed and changes again | Compare complete `W0` with `Wa`; only the separable content delta is `session-attributed` |
| Dirty path changes without a complete baseline | Affected scope is `unattributable` |
| HEAD becomes non-descendant, repo identity changes, or evidence scope is incomplete | Affected scope is `unattributable`; analysis is degraded |

Where Git evidence permits hunk-level separation, attribution may be more
precise. Otherwise the path-level label and basis are explicit.

Content attribution follows material across HEAD, index, and worktree layers.
The descendant `H0..Ha` commit diff is never assumed to be new session content
when `I0` or `W0` already contained those bytes. Fixtures cover fully staged,
mixed staged/unstaged, partial-commit, and same-path later-edit cases.

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
agent authorship. Their baseline-to-agent-end delta remains
`session-attributed` when capture is complete. PatchTrace does not lock the
repository or relabel the session delta as causal agent authorship.

## Alternatives Considered

### Require A Clean Repository And Refuse Dirty Runs

Rejected as the only mode. It provides a simple strong path but makes the tool
less useful in real workflows. A dirty run remains allowed with precise
pre-existing/unattributable classification.

A future repeated failure may still justify requiring a clean baseline for
`ready_to_accept`, but dirty state alone is not a blocker.

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
- Dirty same-path attribution requires private baseline bytes and bounded
  storage.
- Transient/reset activity can remain invisible.
- Multi-repo and submodule workflows are limited.

## Implementation Constraints

- Use the existing Git CLI and Python standard library.
- Do not mutate the user's index, commits, branches, or working tree.
- Run collector subprocesses with `git --no-optional-locks` or
  `GIT_OPTIONAL_LOCKS=0`, config-insensitive porcelain, disabled external diff
  drivers/fsmonitor hooks where applicable, and explicit bounded flags.
- Fixture-prove unchanged index bytes and semantic HEAD/index/worktree
  state across collection. This is required because
  [git status](https://git-scm.com/docs/git-status) may refresh and write index
  stat data by default.
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
