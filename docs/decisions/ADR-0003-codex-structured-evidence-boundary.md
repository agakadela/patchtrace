# ADR-0003: Concrete Codex Structured-Evidence Boundary

- Date: 2026-07-27
- Status: proposed
- Owner: project maintainer(s)
- Extends: ADR-0001

## Context

Phase 4 identifies final output through exact Codex TUI markers:

```text
Final answer:
• Final answer:
```

This works for the verified Codex CLI 0.144.1 transcript shape and selected TUI
noise, but Codex-specific behavior currently lives in generic transcript and
command-analysis modules. Markerless output remains ambiguous.

The installed Codex CLI 0.144.1 exposes structured non-interactive features:

- `codex exec --json` emits JSONL events;
- `--output-last-message <file>` writes the final agent message;
- `--output-schema <file>` constrains final response shape.

Official OpenAI documentation describes JSONL thread, turn, agent-message,
command-execution, file-change, and error events.

Source:
[OpenAI Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

These are `codex exec` capabilities. They are not proof that the interactive TUI
offers the same structured stream.

## Decision

### Add One Concrete Adapter

Create one concrete Codex boundary that owns:

- Codex command recognition and effective workspace checks;
- current TUI noise normalization and final-marker fallback;
- structured JSONL parsing;
- final-message selection;
- Codex version capture where available;
- Codex-specific evidence locators and parser version.

Generic session capture owns process transport and raw streams. Generic analysis
receives typed evidence and contains no Codex presentation markers.

Do not create a plugin registry, discovery layer, marketplace, or speculative
generic adapter protocol. Consider a shared protocol only after a second real
agent adapter exists.

### Make Structured Exec The Canonical Trusted Mode

Trusted `codex exec`:

- is constructed by PatchTrace from one validated task file;
- receives the unchanged task payload plus a separately versioned PatchTrace
  requirement-ID/response protocol;
- uses separate piped stdout/stderr;
- stores JSONL event boundaries;
- uses a PatchTrace-owned final-message path inside this run's private folder;
- uses a PatchTrace-owned output schema requiring one result per `REQ-*` and
  `AC-*`;
- records requested and effective commands;
- captures a repository state fingerprint when each structured command event
  completes, so later final-state comparison can detect stale verification;
- rejects conflicting user-owned `--json`/output paths where PatchTrace cannot
  preserve the evidence contract;
- never silently falls back to PTY text after structured parsing fails.

Trusted mode also applies a version-checked controlled execution/effect profile:

- explicitly set repository cwd, workspace-write sandbox, approval policy, and
  the complete writable-root inventory;
- explicitly set shell-network and temp behavior;
- allowlist inherited environment variables, record names/policy, and redact
  credential values;
- distinguish the selected repository from a bounded PatchTrace scratch/temp
  root and declared Codex authentication/runtime state; none of the latter is
  task evidence;
- place the canonical agent process and descendants inside a supervised
  containment boundary and require a quiescent agent-end checkpoint;
- record the effective security-relevant config/profile and effect-scope digest;
- reject danger-full-access, unaccounted `--add-dir` or config writable roots,
  command hooks, notification commands, unaccounted environment/effect channels,
  and MCP/plugin tools that can write outside the selected evidence scope;
- allow non-security user preferences only when they cannot widen the trusted
  write/effect boundary.

Phase 5 disables shell network access by default. Unknown writable roots,
unbounded inherited environment, or an external writer/network requirement
blocks trusted mode or applies an explicit verdict ceiling; repository evidence
does not prove external side effects.

The installed CLI's repeated `--config key=value` behavior and effective result
must be fixture-proven for every supported Codex version. If PatchTrace cannot
reliably expose or constrain that configuration, trusted preflight fails for
that version. The official
[Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
and [CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
document the relevant config layers, hooks, notifier, MCP servers, sandbox
writable roots, cwd, approval, `--add-dir`, and config overrides.

Phase 5 must also source-check the supported macOS process-containment
primitive. PatchTrace records descendant lifecycle, terminates/reaps accounted
children before agent-end capture, and treats a surviving, escaped, or
unaccounted descendant as incomplete trusted execution. Such a run selects
`rerun_required` and cannot emit `ready_to_accept`.

Interactive `codex` remains supported as an explicit secondary mode:

- remains PTY-based;
- uses the concrete Codex TUI fallback;
- labels final and command evidence as text-derived;
- never guesses that transcript tail equals final output;
- cannot emit `ready_to_accept` without the complete structured trusted
  contract.

### Final Message And Event Rules

- The adapter controls a fresh output path within the new run folder.
- The path must not pre-exist and is digested after the process ends.
- JSONL is parsed line by line; malformed/truncated lines produce explicit
  `malformed` or `incomplete` integrity.
- Unknown event types are preserved as raw evidence and ignored by rules that do
  not understand them.
- The structured final-message file and final agent-message event are reconciled
  when both exist; disagreement records `mismatched` integrity and degrades or
  blocks final-claim analysis.
- Schema output must contain exactly one valid entry for every stable `REQ-*`
  and `AC-*`; `VER-*` comes from PatchTrace execution and `OOS-*` is evaluated
  against evidence. Missing, duplicate, unexpected, or invalid response entries
  prevent trusted requirement coverage.
- Structured fulfillment status is exactly `claimed_done`, `not_done`, or
  `blocked`. A valid `not_done`/`blocked` entry is a fulfillment failure and
  selects `send_back`; a missing, duplicate, unexpected, or invalid entry is a
  protocol/capture defect and selects the applicable `rerun_required` or
  `cannot_assess` integrity path.
- Missing structured final output does not become TUI inference.

For an otherwise valid supported run, missing/malformed/truncated/mismatched
structured output is a named repeatable capture failure and therefore
`rerun_required`. An unknown-incompatible protocol/schema or post-capture digest
mutation is `cannot_assess` under ADR-0002; the adapter does not choose between
them ad hoc.

Structured capture integrity is a closed state:

- `complete`;
- `incomplete`;
- `malformed`;
- `mismatched`.

Raw JSONL remains the authoritative captured artifact. A derived final-message
file or future output schema can strengthen selection, but cannot replace or
silently repair contradictory raw events.

`--output-schema` is required in trusted mode. It is part of PatchTrace's
separately versioned execution protocol, not a mutation of the preserved user
task payload.

ADR-0002's terminal-state table applies even when a schema-valid final object
exists: only `exited(0)` continues to fulfillment analysis. `not_started`,
`spawn_failed`, non-zero exit, signal, interruption, or unknown outcome selects
`rerun_required`; unknown-incompatible schema or post-capture integrity damage
selects `cannot_assess`.

## Alternatives Considered

### Continue Parsing The TUI Everywhere

Rejected as the long-term primary path. Presentation redraws and markers are
fragile, and stronger documented data exists for explicit `codex exec`.

### Replace Interactive Codex With Exec

Rejected as a removal of interactive support. Interactive Codex remains useful
for live conversation, but it is no longer evidence-equivalent to the canonical
trusted run.

### Read Codex Private Session Storage

Rejected for now. Private on-disk rollout formats are not the narrow documented
public contract selected for PatchTrace.

### Use App Server As The Primary Protocol

Rejected for Phase 5. It is a broader experimental protocol surface and would
add lifecycle/client complexity before the stable `exec` path is exhausted.

### Build A Generic Agent Plugin System

Rejected. There is one real agent integration. A generic framework would invent
interfaces without a second implementation.

### Require An LLM To Find The Final Message

Rejected. It adds cost, privacy risk, nondeterminism, and another agent judgment
inside an evidence tool.

## Consequences

### Positive

- Codex format behavior has one real owner.
- The canonical trusted run captures structured final and command evidence.
- Every requirement and acceptance criterion has a schema-enforced final
  response position.
- Interactive behavior remains supported.
- Failed structured parsing cannot be disguised as weaker success.
- Future second-adapter work can learn from a concrete implementation.

### Negative / Trade-Offs

- Session capture needs PTY and piped transports.
- The two modes have different evidence strengths.
- Trusted mode owns a versioned execution/response protocol.
- PatchTrace must test against sanitized external event shapes.
- Codex CLI version drift remains a compatibility concern.

## Privacy And Security

- JSONL can contain prompts, intermediate messages, commands, paths, and output;
  treat it as sensitive local evidence.
- Final-message output is forced into this run's private folder.
- Task payload, response protocol, and output schema are stored and digested
  separately.
- Effective security-relevant Codex configuration and writable scope are stored
  and digested; unsafe or unaccounted writers block trusted mode.
- Adapter-owned paths must be fresh, bounded regular non-symlink files and are
  digested before analysis.
- No raw event, transcript, or final message is committed or uploaded.
- Fixtures must be synthetic or explicitly sanitized.
- The model detects accidental mutation and inconsistent evidence; it is not a
  tamper-proof boundary against another malicious process running as the same
  local user.

## Revisit Triggers

- Codex changes or removes documented `--json` or final-message behavior.
- Supported macOS execution cannot provide the required descendant containment
  and quiescent agent-end checkpoint.
- Interactive Codex exposes a stable public structured stream.
- A second real agent adapter is implemented.
- The structured response contract cannot represent real task items without
  misleading coverage.
