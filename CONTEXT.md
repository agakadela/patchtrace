# PatchTrace Domain Language

Purpose: canonical product language. Use these terms consistently in code,
reports, plans, ADRs, and review discussion.

## Canonical Terms

| Term | Meaning | Do not confuse with |
|---|---|---|
| PatchTrace | Local-first CLI that binds one coding-agent run to task, Git, command, and final-claim evidence so a human can review the work. | AI code reviewer, correctness oracle, approval agent |
| run | One PatchTrace execution with a stable ID, explicit target repository, explicit execution root, and local run folder. | Test run, CI job, Codex account session |
| run folder | Private PatchTrace-owned storage for one run. The Phase 5 target is `<git-metadata-dir>/patchtrace/runs/<run-id>/`, outside the tracked worktree; the current implementation still uses `.patchtrace/runs/<run-id>/`. | Cache, build output, project root |
| task contract | Explicit user-supplied evaluation contract stating requested outcome, requirements, acceptance criteria, required verification, and out-of-scope work. It does not by itself prove which prompt bytes the agent received. | Agent claim, inferred prompt intent, prompt-delivery evidence |
| raw task contract | Task material copied and bound to a run before PatchTrace interprets requirement coverage. | Parsed task requirements |
| task requirement | One explicit, reviewable obligation from the task contract. | Agent claim, evidence item |
| agent claim | A specific statement in the agent's identified final output about a change, test, command, or completed result. | Task requirement, evidence, correctness |
| evidence item | Typed local material with provenance, integrity metadata, and a locator. | Conclusion, verdict, correctness proof |
| provenance | Where an evidence item came from, how it was captured or derived, and how it is bound to the run. | Confidence score |
| evidence kind | What the evidence represents, such as task material, final message, Git change, command result, or transcript. | Capture method |
| capture method | How evidence was obtained, such as user-supplied file, Git snapshot, Codex JSONL, final-message file, or PTY transcript. | Evidence kind |
| directness | Whether an evidence statement is direct structured data, deterministically derived data, or text inference. | Attribution |
| integrity metadata | Schema/producer/parser versions plus artifact digest used to detect mutation and interpret compatibility. | Correctness guarantee |
| session attribution | Classification of a Git change against the baseline and end snapshot of the controlled PatchTrace session. | Proof of human or process authorship |
| session-attributed change | Change absent from the relevant baseline and captured within the PatchTrace session under the documented attribution rules. | `agent-authored change` |
| pre-existing change | Change already present when the PatchTrace session started and unchanged by the captured session delta. | Session-attributed change |
| unattributable change | Change whose pre-existing and in-session portions cannot be separated reliably. | Unsupported claim |
| agent-authored change | Strong causal claim that the coding agent, rather than a person or another process, produced a change. PatchTrace does not use this label without isolation that proves it. | Session-attributed change |
| final output | Agent message selected by an agent-specific structural source or an explicit conservative fallback. | Last transcript lines, entire transcript |
| structured final message | Final agent message captured through a documented structured Codex mechanism and bound to the current run. | TUI marker fallback |
| command result | Command invocation plus completion state/exit information when available. | Text mentioning a command |
| repository state fingerprint | Digestable identity of the selected repository state: HEAD, index, and the bounded supported worktree inventory. | Full filesystem snapshot, correctness proof |
| verification freshness | Whether command-result evidence is bound to the final analyzed repository state: `state_bound`, `stale`, `unknown`, or `N/A`. | Command success, evidence directness |
| PTY command signal | Command-like or result-like text observed in the terminal stream without structured execution metadata. | Structured command result |
| text inference | Deterministic interpretation of transcript text when no stronger structured evidence exists. | Direct evidence |
| structured capture integrity | Whether the expected structured stream/artifact is `complete`, `incomplete`, `malformed`, or `mismatched`. | Analysis outcome |
| wrapped command outcome | What happened to the wrapped process: not started, spawn failure, exited, signaled, interrupted, or unknown. | Analysis outcome |
| analysis outcome | Whether PatchTrace completed, degraded, or blocked analysis, plus explicit reason codes. | Wrapped command outcome, verification verdict |
| completed analysis | Required trusted inputs were bound and interpreted into one valid `AnalysisResult`. | Reports written, code accepted or correct |
| degraded analysis | Analysis ran, but one or more evidence limitations materially reduce what it can assess. | Failed wrapped command |
| blocked analysis | PatchTrace cannot safely perform the intended analysis from the captured material. | Rejected code |
| package outcome | Whether the manifest and requested reports were published: `complete`, `partial`, or `failed`, with artifact-level reasons. | Analysis outcome, verification verdict |
| claim support | Conservative relationship between one explicit agent claim and available evidence. | Correctness |
| requirement coverage | Relationship between one task requirement, relevant agent claims, and evidence. | Claim support |
| verification verdict | Decisive evidence-based recommendation: `ready_for_human_acceptance`, `review_required`, `send_back`, `rerun_required`, or `cannot_assess`. | Correctness proof, autonomous acceptance |
| recommended action | Concrete next step attached to the verification verdict. | Vague caution or generic checklist |
| cannot verify | First-class statement that a conclusion cannot be established from captured material. | Generic disclaimer |
| review first | Ordered, evidence-explained starting points for human review. | Changed-file order |
| AnalysisResult | Single validated interpretation consumed by all report renderers. | A renderer-specific analysis |
| verification package | The manifest, local evidence artifacts, and three Markdown reports for one run. | Correctness certificate |

## Required Distinctions

| Keep separate | Why |
|---|---|
| Task requirement / agent claim / evidence item | The task defines obligations, the agent describes its work, and evidence supports or conflicts with either. |
| Session attribution / agent authorship | A controlled session boundary can attribute a delta to the session without proving which actor authored every byte. |
| Wrapped command outcome / analysis outcome | A process may exit zero while analysis is degraded or blocked; a non-zero process may still leave useful evidence. |
| Analysis outcome / package outcome | `AnalysisResult` is finalized before rendering; a report-write failure cannot retroactively change the analysis. |
| Capture method / evidence kind / directness | JSONL is a transport/capture form, command result is a kind, and text inference is an interpretation method. |
| Command result / verification freshness | A real passing command may still be stale for the final repository state. |
| Claim support / requirement coverage / correctness | Supported claims can omit requirements, and neither relationship proves correct code. |
| Verification verdict / human decision | PatchTrace recommends the next decision strongly; the reviewer retains final authority and may accept or override it. |
| Verification verdict / CLI exit | The verdict recommends what to do with the work; CLI exit reports wrapper/tool execution status under the documented compatibility rule. |
| Current implementation / target architecture / deferred idea | Planned boundaries must not be presented as implemented code. |

## Naming Rules

- Use `session-attributed`, `pre-existing`, and `unattributable` for Git
  attribution.
- Do not use `agent-authored` unless a future isolation mechanism proves causal
  authorship.
- Use `verification verdict` for the decisive recommendation and
  `recommended action` for the concrete next step.
- `ready_for_human_acceptance` means the captured task, claims, and required
  evidence are sufficiently aligned for the human to accept; it is not a claim
  that the code is mathematically proven correct.
- Use `blocked` only for analysis that cannot safely proceed, not for ordinary
  missing support on one claim.
- A required verification result can support `ready_for_human_acceptance` only
  when its repository state fingerprint matches the final analyzed state.
- Use `rerun_required` for missing, stale, malformed, incomplete, or mismatched
  result capture. A valid failing result is evidence for `send_back`, not a
  reason to recapture the same failure.
- Use `Codex adapter` for the one concrete agent-specific boundary. Do not call
  it a plugin system.
- Use `structured` only when the source is a documented machine-readable
  interface. Terminal text remains PTY/transcript evidence.
- A task contract binds the user's evaluation criteria. Claim that the agent
  received the same material only when separate prompt-delivery evidence exists.
- Use `UNKNOWN` for facts not established and `N/A` when a concept does not
  apply, with the reason.

## Open Naming Questions

### Blocking

- N/A for the product/architecture re-baseline.

### Non-Blocking

- Exact user-facing labels for analysis reason codes.
- Whether `task contract` V1 authoring uses Markdown headings, a small JSON
  schema, or both. Phase 5 captures raw material; Phase 6 decides the parsed
  contract.

## Update Log

| Date | Change | Reason |
|---|---|---|
| 2026-07-27 | Added trust-chain, provenance, task, attribution, outcome, and decisive verification-verdict language. | Product and architecture re-baseline after Phase 4 dogfooding |
| 2026-07-05 | Recorded run ID format. | Initial Python CLI run storage |
| 2026-07-02 | Established Python V0 session-recording vocabulary. | Python foundation |
