# Phase 4.1 — Trust Hardening

**Status:** in progress; T1 implemented and verified; T2 and T3 not started

**Baseline:** Phase 4 complete; Phase 4.1 T1 adds external run storage.

**Roadmap:** [ROADMAP.md](ROADMAP.md)

**Next task:** T2 — Enforce the evidence trust ceiling for file/change claims.
Implementation stops after T1 in this build; T2 requires a separate task.

Work on one task at a time, in order T1 → T2 → T3. Each task ends in a
verified, user-visible slice and a commit.

**Goal:** remove known false-confidence paths from the Phase 4 baseline before implementing Phase 5 provenance work.

Phase 4.1 does not expand PatchTrace into semantic correctness or requirement satisfaction. It makes existing evidence labels no stronger than the evidence they represent.

## T1 — Keep run artifacts outside the working tree

**Status:** implemented and verified.
Storage decision: [ARCHITECTURE.md](ARCHITECTURE.md#25-run-storage-decision--phase-41-t1).
Evidence: [VERIFY_LOG.md](VERIFY_LOG.md).

### Outcome

PatchTrace session material cannot be accidentally staged with the repository being reviewed.

### Scope

* move the default run-package storage outside the target repository working tree;
* preserve a stable association between a run and its repository;
* keep the generated run location discoverable from the CLI;
* do not modify the user's `.gitignore`;
* record the concrete local storage location and repository association decision
  during T1; the implementation decision is recorded in the linked architecture section.

### Acceptance

* in a fresh Git repository, run PatchTrace and generate a complete review package;
* run `git add .`;
* no PatchTrace transcript, diff, report, manifest, or other session artifact is staged;
* PatchTrace still prints or otherwise exposes the location of the generated package;
* the package can still identify which repository/run it belongs to.

### Verification

* temporary-repository integration test;
* explicit `git add .` regression test;
* existing run-package tests remain green.

### Out of scope

* cloud storage;
* package publishing;
* automatic cleanup/retention policy;
* modifying user Git configuration or `.gitignore`.

---

## T2 — Enforce the evidence trust ceiling for file/change claims

### Outcome

A file-path observation proves only what the captured file evidence actually establishes.

Example:

> Claim: “Fixed authentication in `auth.py`.”

If the evidence only shows that `auth.py` changed:

> Observed: `auth.py` changed.
> Assessment: cannot determine whether authentication was fixed.

### Scope

* separate observed file facts from semantic claim assessment;
* do not mark a semantic change claim `SUPPORTED` solely because a referenced path changed;
* use `CANNOT_DETERMINE` when the semantic part of the claim is not established;
* use `PARTIALLY_SUPPORTED` only when a specific identifiable part of the claim is actually supported;
* require every referenced target in a multi-file claim to be considered;
* distinguish relevant change types where they are directly observable, such as modified vs removed/deleted.

### Required regression cases

1. “Fixed authentication in `auth.py`” + comment-only change → not `SUPPORTED`.
2. “Deleted `auth.py`” + file merely modified → not `SUPPORTED`.
3. Claim names files A and B + only A changed → whole claim not `SUPPORTED`.
4. Exact bounded claim whose complete factual content is established by captured evidence → may still be `SUPPORTED`.
   This can establish a fact about captured material, such as a diff containing a
   file modification. It does not establish that the agent made that change
   during this session; session attribution remains Phase 5 work.
5. Existing generic completed-change claims remain conservative.

### Acceptance

* no known counterexample produces semantic overconfirmation;
* report wording clearly separates the observed fact from the unresolved semantic claim;
* `SUPPORTED`, `PARTIALLY_SUPPORTED`, and `CANNOT_DETERMINE` each have a distinct evidence meaning;
* no LLM or semantic judge is introduced.

### Verification

* focused analyzer unit tests;
* fixture matrix extended with the known false-positive cases;
* cross-report assertions prove all reports consume the same assessment result.

### Out of scope

* proving semantic correctness from arbitrary diffs;
* LLM-based diff interpretation;
* requirement satisfaction;
* general code-quality evaluation.

---

## T3 — Use latest command attempt and preserve command outcome semantics

### Outcome

A verification claim is evaluated against the latest captured attempt of that exact command, not an earlier successful run.

### Scope

* preserve multiple executions of the same verification command;
* use the latest execution before final output for claim assessment;
* an incomplete or result-less latest attempt must not fall back to an earlier PASS;
* preserve earlier attempts as history/evidence;
* correctly distinguish zero failures from actual failures;
* keep verification freshness relative to later code changes explicitly unresolved for now.

### Required regression cases

```text
pytest → PASS
pytest → FAIL
final: tests passed
```

Result: contradicted.

```text
pytest → FAIL
pytest → PASS
final: tests passed
```

Result: supported with respect to the latest captured command result. This is
transcript-derived evidence, not independent proof of execution or freshness
relative to the final repository state.

```text
pytest → PASS
pytest → no result / interrupted
final: tests passed
```

Result: not supported by the latest attempt; latest result is unknown/incomplete.

```text
3 passed, 0 failed
```

Result: PASS, not FAIL.

### Decision behavior

Claim–evidence truth and work state remain separate.

If the agent says:

```text
Tests failed: `pytest`.
```

and captured evidence confirms that failure:

* the claim itself may be accurately supported;
* the run decision must still surface the failed verification as the important next action.

A truthful negative claim must not make a failed verification look healthy.

### Acceptance

* latest-attempt semantics are deterministic;
* interrupted/latest-unknown execution never inherits an earlier PASS;
* prior attempts remain available for review;
* confirmed failed verification is surfaced in the quick decision even when the agent described it truthfully;
* no claim is made yet that the verification result is fresh relative to the final repository state.

### Verification

* focused command-evidence unit tests;
* pass→fail, fail→pass, pass→unknown, repeated-command, and `0 failed` regressions;
* summary/feedback/verification-brief consistency tests.

### Out of scope

* proving that tests cover the task;
* proving tests ran against final repository state;
* structured command events;
* requirement coverage.

---

## Phase 4.1 closure

Before returning to Phase 5:

* Ruff lint passes;
* Ruff format check passes;
* mypy passes;
* full pytest passes;
* build passes;
* fresh-repository `git add .` dogfood does not stage PatchTrace artifacts;
* all known false-`SUPPORTED` counterexamples are regression-tested;
* repeated-command chronology behaves according to the latest attempt;
* truthful reports of failed verification still produce a failure-oriented next action.

After Phase 4.1, continue with the existing [Phase 5 T1–T3 plan](PHASE_5_PLAN.md)
without changing its intended Git-provenance scope, followed by Phase 5 T4–T7.
Requirement coverage remains Phase 6. Record the Phase 4.1 closeout in
`VERIFY_LOG.md`, restore the deferred Phase 5 plan to `PLAN.md`, update phase
status and links, and remove the deferred copy to keep a single task owner.
