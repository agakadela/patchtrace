# ADR-0003: Codex Capture Modes and Trust Ceilings

- Date: 2026-07-27
- Status: accepted
- Owner: project maintainer

The accepted decision is the capture-mode policy and feasibility gate. App
Server adoption remains unresolved.

## Context

Interactive Codex use is the primary PatchTrace experience. The current PTY
preserves that workflow, but its final output depends on terminal markers and
its command evidence is inferred from text.

Official Codex surfaces provide typed evidence for non-interactive execution,
and App Server exposes threads, turns, and typed items. Those facts alone do not
show that PatchTrace can observe the same normal interactive session without
building a replacement client or relying on unstable surfaces.

PatchTrace needs better evidence without silently replacing the user's workflow
or treating an experimental candidate as accepted architecture.

## Decision

### Keep interactive PTY as compatibility mode

The PTY workflow remains the primary interactive mode. It preserves the current
terminal experience and has an explicit lower trust ceiling.

Final output is accepted only when exactly one supported marker identifies it.
A missing or ambiguous marker degrades final-output evidence. PatchTrace never
guesses that the last transcript lines are the final answer.

### Add structured execution as a separate task mode

`codex exec --json` may support an optional Codex structured task mode. It is
not an automatic replacement for the interactive session.

PatchTrace consumes only documented event types needed for task delivery,
commands, file changes, lifecycle, and final messages. The Git capture envelope
remains the local source for repository attribution.

### Make task delivery claims transport-bounded

In a Codex-specific mode, the preserved raw task artifact is the initial prompt
source. The manifest records its digest, delivery method, attempted boundary,
observable confirmation, and limitations.

Tests target the nearest reliable official boundary. PatchTrace does not claim
byte-for-byte receipt when receipt is not observable and never claims that the
model understood the task.

Generic wrapped commands preserve task material for analysis but mark delivery
unverified.

### Gate structured-interactive capture with a prototype

App Server is an official and promising candidate, not the accepted target
integration.

A one-day feasibility prototype must determine:

1. whether the required typed events exist;
2. whether they describe the same interactive session;
3. whether PatchTrace can obtain them officially without its own client;
4. whether the required surface is stable;
5. the minimum integration and maintenance cost.

The result is `GO`, `NO-GO`, or `CANNOT VERIFY`. A custom TUI, large protocol
proxy, private formats, or disproportionate integration is `NO-GO` for Phase 5.

The prototype is not production capability. A `GO` still requires a later
reviewable implementation slice.

### Enforce per-mode trust ceilings

Reports and verdicts cannot exceed the evidence exposed by their capture mode.

If App Server is `NO-GO` or `CANNOT VERIFY`, Phase 5 may close with:

- marker-based PTY compatibility mode;
- structured `exec --json` task mode;
- no structured-interactive high-trust final output;
- explicit degradation for missing or ambiguous PTY markers.

That result must not be described as complete final-output provenance.

## Alternatives considered

### Replace PTY with structured execution

Rejected. It changes an interactive conversation into a non-interactive task
workflow and would make evidence quality dictate product UX.

### Accept App Server immediately

Rejected. Typed threads and turns do not prove access to the same interactive
session, a stable transport, or proportionate integration.

### Build a PatchTrace Codex client or TUI

Rejected for the current local CLI. It duplicates the primary user experience
and creates a large maintenance surface.

### Parse private Codex files or protocols

Rejected. Private formats can change without compatibility guarantees and
cannot support a trustworthy evidence product.

### Use transcript-tail or LLM fallback

Rejected. Either can select the wrong text and convert uncertainty into a false
claim assessment.

### Create a generic agent plugin framework

Rejected. One Codex-specific boundary solves the present problem. A second
adapter requires a concrete future trigger.

## Consequences

Positive:

- interactive UX remains intact;
- structured evidence can improve a separate task workflow;
- every mode has honest, testable limitations;
- feasibility research stays small and decision-oriented;
- private or disproportionate work has a clear stop condition.

Costs and limits:

- PTY final-output evidence remains fragile when markers are absent;
- structured and interactive modes need distinct fixtures and user-facing copy;
- a feasibility `GO` does not itself deliver production integration;
- Phase 5 may close without structured-interactive high-trust output.

## References

- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/)
- [Codex App Server](https://developers.openai.com/codex/app-server/)
- [PatchTrace architecture](../ARCHITECTURE.md)
- [Phase 5 plan](../PLAN.md)
