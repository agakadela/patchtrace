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

### Preserve Two Explicit Capture Modes

Interactive `codex`:

- remains PTY-based;
- uses the concrete Codex TUI fallback;
- labels final and command evidence as text-derived;
- never guesses that transcript tail equals final output.

Explicit `codex exec`:

- uses separate piped stdout/stderr;
- stores JSONL event boundaries;
- uses a PatchTrace-owned final-message path inside this run's private folder;
- records requested and effective commands;
- captures a repository state fingerprint when each structured command event
  completes, so later final-state comparison can detect stale verification;
- rejects conflicting user-owned `--json`/output paths where PatchTrace cannot
  preserve the evidence contract;
- never silently falls back to PTY text after structured parsing fails.

PatchTrace never converts interactive `codex` to `codex exec` silently.

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
- Missing structured final output does not become TUI inference.

Structured capture integrity is a closed state:

- `complete`;
- `incomplete`;
- `malformed`;
- `mismatched`.

Raw JSONL remains the authoritative captured artifact. A derived final-message
file or future output schema can strengthen selection, but cannot replace or
silently repair contradictory raw events.

`--output-schema` is not forced in Phase 5. It changes the agent's requested
response contract and is not required to capture trustworthy final output.

## Alternatives Considered

### Continue Parsing The TUI Everywhere

Rejected as the long-term primary path. Presentation redraws and markers are
fragile, and stronger documented data exists for explicit `codex exec`.

### Replace Interactive Codex With Exec

Rejected. Interactive Codex is the current dogfood workflow. `exec` has a
different prompt, transport, and interaction model.

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
- Structured final and command evidence is available when the user selects
  `codex exec`.
- Interactive behavior remains supported.
- Failed structured parsing cannot be disguised as weaker success.
- Future second-adapter work can learn from a concrete implementation.

### Negative / Trade-Offs

- Session capture needs PTY and piped transports.
- The two modes have different evidence strengths.
- PatchTrace must test against sanitized external event shapes.
- Codex CLI version drift remains a compatibility concern.

## Privacy And Security

- JSONL can contain prompts, intermediate messages, commands, paths, and output;
  treat it as sensitive local evidence.
- Final-message output is forced into this run's private folder.
- Adapter-owned paths must be fresh, bounded regular non-symlink files and are
  digested before analysis.
- No raw event, transcript, or final message is committed or uploaded.
- Fixtures must be synthetic or explicitly sanitized.
- The model detects accidental mutation and inconsistent evidence; it is not a
  tamper-proof boundary against another malicious process running as the same
  local user.

## Revisit Triggers

- Codex changes or removes documented `--json` or final-message behavior.
- Interactive Codex exposes a stable public structured stream.
- A second real agent adapter is implemented.
- Users need a PatchTrace-controlled structured response schema after dogfooding.
