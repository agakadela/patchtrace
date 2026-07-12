# ARCHITECTURE.md

System source of truth: stack, package convention, data flow, and trust
boundaries.

Template rules:
- Keep this short and current.
- Do not duplicate product scope from `docs/SPEC.md`.
- Do not duplicate detailed auth/API/UI/AI/integration contracts; link to
  risk-triggered docs when they exist.
- If unknown, write `UNKNOWN`. If not applicable, write `N/A` and why.

## Status

- Last reviewed: 2026-07-12
- Reviewed by: `$aga-spec` Phase 4 interview and product-architecture review
- Related ADRs: `docs/decisions/ADR-0001-project-foundation.md`

## Stack

| Layer | Decision | Source / ADR | Notes |
|---|---|---|---|
| App framework | N/A | `ADR-0001` | V0 is a local CLI, not a web app. |
| Language | Python >=3.11 | `ADR-0001` | Local CLI with typed models and PTY/session capture. |
| Project manager | `uv` | `ADR-0001` | Project/dependency/env/lock workflow. |
| CLI framework | Typer | `ADR-0001` | Subcommands: `run`, `analyze`, `watch`. |
| Session capture | Pexpect | `ADR-0001` | PTY-based capture for interactive Codex CLI sessions. |
| PTY platform primitive | Python stdlib `pty` | `ADR-0001` | POSIX/macOS/Linux concept underlying the wrapper. |
| Structured models | Pydantic v2 | `ADR-0001` | Validate run manifests, evidence, claims, verdicts, reports. |
| Test runner | pytest | `ADR-0001` | Unit, integration, fixture, and fake-command PTY tests. |
| Lint/format | Ruff | `ADR-0001` | Fast linter and formatter. |
| Typecheck | mypy | `ADR-0001` | Static checking without adding a separate runtime dependency. |
| Database | N/A | `ADR-0001` | V0 stores local files only. |
| Migrations | N/A | `ADR-0001` | No schema migrations in V0. |
| Auth | N/A | `ADR-0001` | V0 has no users, sessions, teams, or accounts. |
| Payments | N/A | `ADR-0001` | V0 has no billing or entitlements. |
| AI provider | N/A for V0 | `ADR-0001` | Must be useful without LLM calls. Future LLM use is opt-in only. |
| Hosting/deploy | N/A for V0 | `ADR-0001` | Local CLI only; package publishing is a later decision. |
| Monitoring | N/A for V0 | `ADR-0001` | Local stdout/stderr, run folders, and tests. |

## Package Convention

Default principle: organize code by product and system capability ownership, not
by global technical-layer dumps.

- Chosen convention: Python `src` layout with an import package under
  `src/patchtrace/`.
- Exact root path: `src/patchtrace/`.
- Reason: PatchTrace is a local CLI package with clear capability boundaries:
  CLI commands, session capture, Codex adapter, git/VCS collection, analysis,
  report rendering, models, and run storage.
- Why not `src/modules`: in Python, "module" usually means a `.py` file, so a
  `modules/` package is less idiomatic than capability packages.
- Why not `features`: V0 has no UI screens or user-facing app features.
- Why not global `utils`: it hides ownership. Shared primitives must remain
  small and have a clear package owner.

Accepted implementation shape:

```text
src/
  patchtrace/
    __init__.py
    __main__.py
    cli/
      app.py
      commands/
        run.py
        analyze.py
        watch.py
    session/
      recorder.py
      transcript.py
      terminal.py
    adapters/
      codex.py
    vcs/
      git.py
      snapshot.py
    analysis/
      analyzer.py
      claims.py
      risk.py
      test_evidence.py
      verdict.py
    reports/
      summary.py
      feedback.py
      verification_brief.py
    models/
      run.py
      evidence.py
      report.py
    storage/
      runs.py
tests/
  unit/
  integration/
  fixtures/
docs/
```

## Data Flow

Primary full flow:

```text
developer runs `patchtrace run -- codex`
  -> CLI creates run folder
  -> storage records run metadata
  -> vcs records pre-run git state
  -> session launches Codex CLI through PTY
  -> session records transcript locally
  -> vcs records post-run git state, changed files, and diff
  -> session normalizes terminal noise and isolates claim-bearing final output
  -> analysis consumes normalized transcript and local evidence once
  -> analysis extracts a bounded set of explicit agent claims
  -> analysis returns one validated AnalysisResult with evidence relationships,
     gaps, next actions, and a conservative verdict
  -> reports render SUMMARY.md, AGENT_FEEDBACK.md, and VERIFICATION_BRIEF.md
     from that shared result
```

Fallback manual flow:

```text
developer runs `patchtrace analyze`
  -> CLI reads current git state and optional transcript/run material
  -> analysis runs with available evidence
  -> reports clearly mark missing transcript or test evidence
```

Watch flow:

```text
developer runs `patchtrace watch`
  -> watcher detects working-tree changes and idle state
  -> analysis creates limited patch-only output if no transcript exists
  -> reports label trigger source and evidence limits
```

Notes:

- The transcript is evidence, not truth.
- The agent summary is never treated as proof.
- Missing local/provided material should produce explicit gaps, not confident
  guesses.
- Full claim-vs-evidence analysis requires session material.
- The Phase 4 analysis module has one conceptual interface:
  `analyze_run(run_evidence) -> AnalysisResult`. Its implementation may use
  private pure-function seams, but callers and report tests use the single
  result-producing interface.
- Report renderers do not parse raw artifacts or independently rerun analysis.
- `analyze` and `watch` may later supply different evidence inputs to the same
  analysis interface; Phase 4 does not implement those command flows.

## Trust Boundaries

| Boundary | Validation | Auth/AuthZ Enforcement | Logging | Failure Behavior |
|---|---|---|---|---|
| CLI args -> command handlers | Validate subcommand, wrapped command, paths, and option combinations. | N/A | CLI stderr and run manifest where applicable. | Exit non-zero with actionable message. |
| PatchTrace -> Codex CLI process | Preserve terminal behavior through PTY; record command and exit status. | N/A | `agent-session.txt`, `run.json`. | Capture exit code; still analyze available material. |
| PTY transcript -> claims | Extract explicit claims only; strip/normalize control sequences for analysis. | N/A | Include transcript source and offsets where practical. | Mark claim material missing/limited if extraction fails. |
| Local git repo -> patch evidence | Use local git commands in the target repo only. | N/A | Save before/after status, changed files, diff. | Mark patch material missing or no-change instead of inventing evidence. |
| Test output -> test evidence | Parse conservatively; distinguish pass/fail from behavior proof. | N/A | Include command/test evidence when present. | Mark test evidence missing, weak, unknown, or contradictory. |
| Analyzer -> report package | Validate report objects with Pydantic before rendering. | N/A | Write report artifact paths to `run.json`. | Do not silently write misleading partial reports. |
| CLI -> external services | N/A in V0. | N/A | N/A | No external calls by default. |

## Server-Side Enforcement Points

- Auth/session checked at: N/A because V0 has no auth.
- Authorization checked at: N/A because V0 has no users or accounts.
- Tenant/workspace isolation checked at: N/A because V0 has no tenant model.
- DB-level isolation/RLS: N/A because V0 has no database.
- Entitlements checked at: N/A because V0 has no payments.

## Data Model Overview

Do not maintain full schemas here. Keep canonical schema definitions in code
once implementation exists.

| Concept | Storage | Owner Package | Notes |
|---|---|---|---|
| Run manifest | `.patchtrace/runs/<run-id>/run.json` | `models`, `storage` | Run ID, command, timestamps, exit code, artifact paths, trigger source. |
| Session transcript | `.patchtrace/runs/<run-id>/agent-session.txt` | `session` | Raw-ish local transcript captured from PTY, normalized for analysis separately. |
| Git snapshot | `.patchtrace/runs/<run-id>/git-before.txt`, `git-after.txt`, `patch.diff`, `changed-files.txt` | `vcs` | Local patch material before/after wrapped session. |
| Agent claim | In-memory/report object | `analysis` | Explicit claim extracted from transcript/session material. |
| Evidence source | In-memory/report object | `models`, `analysis` | Source-backed material: transcript span, diff hunk, file path, test output, command output. |
| Analysis result | In-memory validated object | `models`, `analysis` | Single source for claim assessments, evidence gaps, next actions, review targets, and conservative verdict consumed by all reports. |
| Risk area | In-memory/report object | `analysis` | Conservative risk classification tied to evidence. |
| Verification package | Markdown files plus manifest | `reports`, `storage` | `SUMMARY.md`, `AGENT_FEEDBACK.md`, `VERIFICATION_BRIEF.md`. |

## External Systems

| System | Purpose | Source Doc | Failure Path |
|---|---|---|---|
| Codex CLI | First wrapped agent command for dogfooding. | `docs/SPEC.md`; implementation adapter once built. | If unavailable or exits non-zero, record failure and analyze available material. |

No external network service is required in V0.

Future optional integrations such as non-Codex adapters, LLM extraction, GitHub
PR integration, package publishing, or hosted services require explicit approval
and matching risk-triggered docs.

## Environments

| Environment | URL | Database/Provider Project | Notes |
|---|---|---|---|
| local | N/A | N/A | V0 runs as a local CLI. |
| preview/staging | N/A | N/A | N/A until a hosted surface exists. |
| production | N/A | N/A | N/A until package release or hosted service is planned. |

## Observability

- Error monitoring: N/A for V0 local CLI.
- Logs: CLI stdout/stderr and local run folders.
- Alerts: N/A.
- Dashboards: N/A.

## Known Constraints

- V0 must be useful without an LLM.
- Full claim-vs-evidence analysis depends on session transcript material.
- Phase 4 intentionally recognizes only explicit claims about changed files,
  completed changes, tests, and verification commands; arbitrary semantic
  understanding is deferred.
- `patchtrace watch` is a secondary safety net, not the source of full session
  truth.
- Markdown report quality and ready-to-paste agent feedback are the product bar.
- The report must not claim correctness, safety, guarantees, or production
  verification without evidence.
- Fixture expectations should precede analyzer behavior.
- V0 targets macOS/Linux-style PTY workflows first; Windows support is not a V0
  acceptance criterion.

## Source Notes

- Python `src` layout and `pyproject.toml`: Python Packaging User Guide.
- `uv` and Ruff: Astral official docs.
- Typer: Typer official docs.
- Pexpect: Pexpect official docs.
- Python `pty`: Python standard library docs.
- Pydantic, pytest, mypy: official docs.

## Change Log

| Date | Change | Reason | Commit/PR |
|---|---|---|---|
| 2026-07-12 | Added the Phase 4 single-analysis-result seam and bounded deterministic claim flow | Accepted `$aga-spec` Phase 4 architecture review | N/A |
| 2026-07-02 | Reframed architecture for Python V0 as Codex CLI session recorder and local verification package | New `$aga-spec` direction | N/A |
