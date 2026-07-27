# PatchTrace Domain Language

Purpose: canonical product language. Use these terms consistently in code,
reports, plans, ADRs, and review discussion.

## Canonical Terms

| Term | Meaning | Do not confuse with |
|---|---|---|
| PatchTrace | Local-first CLI that binds one coding-agent run to task, Git, command, and final-claim evidence so a developer can decide whether to accept, review, rerun, or send back the work. | AI code reviewer, correctness oracle, approval agent |
| run | One PatchTrace execution with a stable ID, explicit target repository, explicit execution root, and local run folder. | Test run, CI job, Codex account session |
| run folder | Private PatchTrace-owned storage for one run. The Phase 5 target is `<git-metadata-dir>/patchtrace/runs/<run-id>/`, outside the tracked worktree; the current implementation still uses `.patchtrace/runs/<run-id>/`. | Cache, build output, project root |
| task contract | Validated user-authored Markdown containing outcome, requirements, acceptance criteria, required verification, and out-of-scope work. It is both the evaluation contract and the unchanged user task payload delivered in trusted mode. | PatchTrace execution protocol, agent claim |
| task payload | Exact user task bytes preserved, digested, and delivered to Codex in trusted mode. | PatchTrace execution protocol |
| execution protocol | Separately versioned PatchTrace instructions/schema added around the unchanged task payload so Codex returns one structured result per `REQ-*` and `AC-*`. | User task, inferred prompt intent |
| task requirement | One explicit, reviewable obligation from the task contract. | Agent claim, evidence item |
| acceptance criterion | One explicit observable condition linked to one or more requirements and a closed independent evidence predicate. | Required verification command, agent claim |
| evidence basis | One typed atom inside an acceptance evidence predicate: exact deterministic Git/artifact property, named final-verification outcome, or explicit human inspection. | Agent claim |
| acceptance evidence predicate | Closed, user-declared deterministic expression that tells PatchTrace exactly which typed Git/artifact properties or `VER-*` outcomes satisfy an `AC-*`; it may instead require explicit human inspection. PatchTrace evaluates the expression and never infers semantic sufficiency from a changed file. | Natural-language code review, agent claim |
| task item taxonomy | `REQ-*` requirements and `AC-*` acceptance criteria require structured Codex entries; `VER-*` commands are executed by PatchTrace; `OOS-*` constraints are evaluated against evidence; `Outcome` is the single goal. | Every Markdown list item has the same semantics |
| structured fulfillment status | Codex's schema-valid status for one `REQ-*` or `AC-*`: `claimed_done`, `not_done`, or `blocked`. A missing/invalid entry is a capture defect, not a fulfillment status. | Independent evidence, verification verdict |
| agent claim | A specific statement in the agent's identified final output about a change, test, command, or completed result. | Task requirement, evidence, correctness |
| evidence item | Typed local material with provenance, integrity metadata, and a locator. | Conclusion, verdict, correctness proof |
| provenance | Where an evidence item came from, how it was captured or derived, and how it is bound to the run. | Confidence score |
| evidence kind | What the evidence represents, such as task material, final message, Git change, command result, or transcript. | Capture method |
| capture method | How evidence was obtained, such as user-supplied file, Git snapshot, Codex JSONL, final-message file, or PTY transcript. | Evidence kind |
| directness | Whether an evidence statement is direct structured data, deterministically derived data, or text inference. | Attribution |
| integrity metadata | Schema/producer/parser versions plus artifact digest used to detect mutation and interpret compatibility. | Correctness guarantee |
| session attribution | Classification of a Git change against the baseline and agent-end snapshots of the controlled PatchTrace agent session. | Proof of human or process authorship |
| session-attributed change | Delta between the complete captured baseline and agent-end state assigned to the PatchTrace session under the documented rules, including supported changes to a previously dirty path. | `agent-authored change` |
| pre-existing change | Material present in the captured baseline before the PatchTrace session delta. | Session-attributed change |
| unattributable change | Material whose baseline/agent-end state, history, or repository scope is too incomplete to compute the session delta reliably. | Unsupported claim |
| agent-authored change | Strong causal claim that the coding agent, rather than a person or another process, produced a change. PatchTrace does not use this label without isolation that proves it. | Session-attributed change |
| final output | Agent message selected by an agent-specific structural source. Trusted mode requires the schema-valid structured response; interactive mode may use an explicitly weaker marker fallback. | Last transcript lines, entire transcript |
| structured final message | Final agent message captured through a documented structured Codex mechanism and bound to the current run. | TUI marker fallback |
| command result | Command invocation plus completion state/exit information when available. | Text mentioning a command |
| required verification | Explicit user-authorized command from the task contract, executed by PatchTrace after agent capture and bound through verification-end state. | Command mentioned or run earlier by Codex |
| agent-end state | Repository snapshot captured immediately after Codex ends and before PatchTrace runs required verification. | Verification-end state |
| verification-end state | Repository snapshot captured after required verification and used to prove whether checks applied without changing relevant repository state. | Agent-end state |
| verification-phase delta | Relevant tracked or non-ignored repository change observed between agent-end and verification-end during PatchTrace's ordered verification phase. It is outside the agent session delta; the snapshots establish timing, not which concurrent process wrote it. | Agent session delta |
| quiescent checkpoint | Repository checkpoint captured only after the supervised process tree has no surviving accounted descendants and its effect-scope enforcement is still intact. | Promise that no unrelated actor can ever change the repository later |
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
| claim support | Bounded relationship between one explicit agent claim and available evidence. | Correctness |
| requirement coverage | Relationship between one task requirement, relevant agent claims, and evidence. | Claim support |
| verification verdict | Decisive evidence-based task-fulfillment decision: `ready_to_accept`, `send_back`, `review_required`, `rerun_required`, or `cannot_assess`. | Correctness proof, autonomous acceptance |
| recommended action | Concrete next step attached to the verification verdict. | Vague caution or generic checklist |
| cannot verify | First-class statement that a conclusion cannot be established from captured material. | Generic disclaimer |
| review first | Ordered, evidence-explained starting points for human review. | Changed-file order |
| AnalysisResult | Single validated interpretation consumed by all report renderers. | A renderer-specific analysis |
| verification package | The manifest, local evidence artifacts, and three Markdown reports for one run. | Correctness certificate |

## Required Distinctions

| Keep separate | Why |
|---|---|
| Task requirement / agent claim / evidence item | The task defines obligations, the agent describes its work, and evidence supports or conflicts with either. |
| Task payload / execution protocol | The user task remains unchanged; PatchTrace's versioned instructions and response schema are recorded separately. |
| Requirement / acceptance criterion / verification / out-of-scope constraint | They receive different ID namespaces and different analyzer behavior; only requirements and acceptance criteria require Codex completion entries. |
| Session attribution / agent authorship | A controlled session boundary can attribute a delta to the session without proving which actor authored every byte. |
| Agent-end state / verification-end state | Verification must not silently rewrite the state attributed to Codex; any relevant later delta is reported separately. |
| Wrapped command outcome / analysis outcome | A process may exit zero while analysis is degraded or blocked; a non-zero process may still leave useful evidence. |
| Analysis outcome / package outcome | `AnalysisResult` is finalized before rendering; a report-write failure cannot retroactively change the analysis. |
| Capture method / evidence kind / directness | JSONL is a transport/capture form, command result is a kind, and text inference is an interpretation method. |
| Command result / verification freshness | A real passing command may still be stale for the final repository state. |
| Claim support / requirement coverage / correctness | Supported claims can omit requirements, and neither relationship proves correct code. |
| Verification verdict / human decision | PatchTrace determines the next action within its task-fulfillment contract; the developer retains final authority and may act or override it. |
| Verification verdict / CLI exit | The verdict determines what to do with the work; CLI exit reports wrapper/tool execution status under the documented compatibility rule. |
| Current implementation / target architecture / deferred idea | Planned boundaries must not be presented as implemented code. |

## Naming Rules

- Use `session-attributed`, `pre-existing`, and `unattributable` for Git
  attribution.
- Do not use `agent-authored` unless a future isolation mechanism proves causal
  authorship.
- Use `verification verdict` for the decisive task-fulfillment decision and
  `recommended action` for the concrete next step.
- `ready_to_accept` means every supported task condition, final verification,
  attribution, and integrity rule passed. It is a task-fulfillment verdict, not
  general code review.
- An agent claim is never an evidence atom for an acceptance
  criterion.
- Use `blocked` only for analysis that cannot safely proceed, not for ordinary
  missing support on one claim.
- A required verification result can support `ready_to_accept` only when its
  repository state fingerprint matches the final analyzed state.
- Use `rerun_required` for missing, stale, malformed, incomplete, or mismatched
  capture in a valid supported run when a named repeat can repair it. Use
  `cannot_assess` for an unusable/unsupported contract, incompatible format, or
  integrity damage that the existing run cannot repair. A valid failing result
  is evidence for `send_back`, not a reason to recapture the same failure.
- Use `Codex adapter` for the one concrete agent-specific boundary. Do not call
  it a plugin system.
- Use `structured` only when the source is a documented machine-readable
  interface. Terminal text remains PTY/transcript evidence.
- In trusted mode, the manifest separately binds the unchanged task payload and
  the PatchTrace execution protocol delivered to Codex.
- Use `UNKNOWN` for facts not established and `N/A` when a concept does not
  apply, with the reason.

## Open Naming Questions

### Blocking

- N/A for the product/architecture re-baseline.

### Non-Blocking

- Exact user-facing labels for analysis reason codes.
- Exact fixed-section Markdown list grammar and stable task-item ID spelling.

## Update Log

| Date | Change | Reason |
|---|---|---|
| 2026-07-27 | Confirmed Markdown task payload, structured Codex protocol, final verification, dirty-baseline attribution, and `ready_to_accept`. | `$aga-spec` whole-product interview |
| 2026-07-27 | Added trust-chain, provenance, task, attribution, outcome, and decisive verification-verdict language. | Product and architecture re-baseline after Phase 4 dogfooding |
| 2026-07-05 | Recorded run ID format. | Initial Python CLI run storage |
| 2026-07-02 | Established Python V0 session-recording vocabulary. | Python foundation |
