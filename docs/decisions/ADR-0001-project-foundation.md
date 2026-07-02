# ADR-0001: Project Foundation

- Date: 2026-07-02
- Status: accepted
- Owner: project maintainer(s)

## Context

PatchTrace Python is a local-first devtool for recording Codex CLI sessions and
turning the resulting transcript, git patch material, and test/command evidence
into a review package.

The foundation preserves conservative evidence briefs, claim skepticism,
fixture-first development, and no false confidence. The Python version centers
the stronger first workflow: PatchTrace should wrap the agent session instead
of only analyzing saved materials afterward.

The foundation decisions optimize for:
- dogfooding with Aga's Codex CLI workflow;
- local transcript and patch capture;
- evidence-backed reports and ready-to-paste agent feedback;
- fixture-first development;
- conservative trust boundaries;
- a small Python CLI package that can later become OSS.

## Decision Summary

| Area | Decision | Why | Revisit When |
|---|---|---|---|
| Stack | Python >=3.11 CLI | Python has strong local automation, PTY/session capture, and CLI ergonomics. | PTY support or packaging needs force another runtime. |
| Project manager | `uv` | Fast project/dependency/env/lock workflow. | Contributor workflow requires a different standard. |
| Build metadata | `pyproject.toml` | Standard Python project configuration. | N/A. |
| CLI framework | Typer | Typed subcommand-oriented CLI for `run`, `analyze`, `watch`. | CLI needs outgrow Typer or dependency becomes costly. |
| Session capture | Pexpect | Purpose-built PTY control for interactive child applications. | Direct stdlib `pty` implementation is simpler or Pexpect cannot handle target behavior. |
| Structured models | Pydantic v2 | Validate run manifests, evidence, claims, verdicts, and report objects. | Runtime validation becomes unnecessary or too heavy. |
| Test runner | pytest | Good fit for unit, integration, and fixture-first tests. | Test suite needs capabilities pytest does not support. |
| Lint/format | Ruff | Fast linter/formatter with `pyproject.toml` support. | Rules or formatting needs require a supplement. |
| Typecheck | mypy | Static checking without adding a separate runtime dependency. | Pyright becomes necessary for better coverage or team preference. |
| Database | N/A | V0 stores local run folders only. | Local history/cache/querying becomes part of product scope. |
| Migrations | N/A | No database in V0. | A database is introduced. |
| Hosting/deploy | N/A for V0 | V0 is local CLI only. | Publishing/release/distribution is planned. |
| Auth/session | N/A | No users, teams, or accounts in V0. | Hosted service, team workspace, or protected surface is introduced. |
| Tenancy/workspace | N/A | No user accounts or multi-tenant data in V0. | Team/hosted features are introduced. |
| Data isolation | Local-first, no external calls by default | Diffs and transcripts can be sensitive. | Any external provider or cloud feature is proposed. |
| Payments/entitlements | N/A | No billing in V0. | Paid distribution or hosted service is planned. |
| Primary interface | `patchtrace run -- codex` | Full claim-vs-evidence requires session material. | Another agent becomes the primary dogfood target. |
| Fallback interface | `patchtrace analyze` | Supports existing working trees and saved material. | Manual analysis is unused after dogfooding. |
| Background interface | `patchtrace watch` as secondary safety net | Useful patch-only fallback, but not full session truth. | Watch becomes reliable enough to promote. |
| Package convention | `src/patchtrace/<capability>/...` | Idiomatic Python package layout with clear capability ownership. | Boundaries become misleading after implementation. |
| AI boundary | No required AI/LLM in V0 | Tool verifying agents should not depend on agent judgment by default. | Opt-in extraction/summarization is explicitly approved. |
| Monitoring | N/A for V0 | Local CLI uses stdout/stderr and run artifacts. | Hosted surface or telemetry is proposed. |

## Decisions

### Stack

- Framework: N/A; local CLI.
- Language: Python >=3.11.
- Project manager: `uv`.
- Runtime interface: local command line.
- CLI framework: Typer.
- Session capture: Pexpect over a pseudo-terminal.
- Structured data validation: Pydantic v2.
- Test runner: pytest.
- Lint/format: Ruff.
- Typecheck: mypy.
- Reasoning: this stack maps directly to the product problem: launch and record
  an interactive CLI agent, capture local git evidence, validate structured run
  data, and generate local Markdown artifacts.

### Database And Migrations

- Database: N/A for V0.
- Migration tool: N/A for V0.
- Run storage: local files under `.patchtrace/runs/<run-id>/`.
- Rule: if a database is introduced later, schema changes must happen only
  through repo migrations.
- Local/preview/prod separation: N/A until a database or hosted service exists.
- Backup/PITR expectation before production migrations: N/A until production
  data exists.

### Auth And Sessions

- Identity provider: N/A for V0.
- Session model: N/A for V0 user accounts.
- Agent session: a local recorded CLI run, not an authenticated app session.
- Server-side auth enforcement point: N/A for V0.
- UI role: N/A because V0 has no UI.

### Tenancy And Data Isolation

- Tenant/workspace model: N/A for V0.
- `workspace_id` from first table: N/A because V0 has no database tables.
- DB-level isolation/RLS or equivalent: N/A for V0.
- Two-user test expectation: N/A for V0; required if hosted/team/user data
  exists later.

### Entitlements And Payments

- Payment provider: N/A for V0.
- Paid access source of truth: N/A for V0.
- Event idempotency table: N/A for V0.
- Dashboard + DB verification required: N/A for V0.

### API/Interface Style

- Primary style: CLI commands.
- First public command target: `patchtrace run -- codex`.
- Fallback command target: `patchtrace analyze`.
- Secondary command target: `patchtrace watch`.
- Validation boundary: Typer argument parsing and Pydantic validation for run
  manifests/report objects.
- Error taxonomy:
  - validation: invalid flags, missing command, incompatible options;
  - environment: not in a git repo, Codex command unavailable, PTY unsupported;
  - filesystem: unreadable or unwritable run paths;
  - wrapped command: non-zero exit or interrupted agent process;
  - material: missing transcript, missing diff, missing test output;
  - analyzer: unexpected parse or report generation error;
  - provider failure: N/A in V0 because no provider calls.
- Idempotency policy: running analysis on the same saved run material should
  produce stable report content except timestamps or run IDs.

### Conventions

- IDs: stable string IDs for runs, claims, evidence, risks, and review targets
  where needed.
- Run IDs: timestamp plus short stable suffix unless implementation finds a
  simpler deterministic convention.
- Time/timezones: use ISO 8601 for run timestamps.
- Money: N/A for PatchTrace product state; analyzed patches may mention money
  only as code context.
- Soft delete: N/A for V0.
- Logging: CLI stdout/stderr plus local run artifacts; no telemetry by default.
- Error handling: no silent catch blocks; errors should be explicit and
  actionable.
- Privacy: no external network calls, telemetry, or LLM submission by default.

### AI Boundary

- AI role: N/A in V0.
- Human checkpoint required before: adding any LLM call, model dependency,
  external provider, or network submission of code/diffs/transcripts/summaries.
- Cost/retry caps: N/A in V0; required if AI calls are added later.
- Logging/failure path: N/A in V0; required if AI calls are added later.
- Future rule: if an LLM is introduced, it may extract or summarize explicit
  material only; it must not be treated as truth or as a correctness oracle.

### Package Convention

- Default principle: organize code by product and system capability ownership,
  not by technical layer dumps.
- Chosen convention: `src/patchtrace/<capability>/...`.
- Exact root path: `src/patchtrace`.
- Reason: Python packages are normally organized under an import package; this
  project has clear capabilities: CLI, session capture, adapters, VCS, analysis,
  reports, models, and storage.
- Why not `src/modules`: in Python, "module" usually means a `.py` file, and a
  `modules/` package would be less idiomatic.
- Why not `features`: V0 has no UI screens or feature slices.
- Why not global `utils`: shared helpers become ownership-free dumping grounds.
- Shared code policy: only genuinely generic primitives may live outside the
  main capability packages, and they should remain small.
- Dependency boundaries:
  - `cli` calls package services and owns user-facing command wiring.
  - `session` owns PTY capture and transcript normalization.
  - `adapters` owns tool-specific behavior, starting with Codex CLI.
  - `vcs` owns local git state collection.
  - `analysis` owns product judgment.
  - `reports` owns Markdown rendering.
  - `models` owns Pydantic schemas shared across boundaries.
  - `storage` owns run folder paths and persistence.

### Feedback Loops

- Install/sync: `uv sync` after scaffold.
- Lint: `uv run ruff check .` after scaffold.
- Format check: `uv run ruff format --check .` after scaffold.
- Typecheck: `uv run mypy src tests` after scaffold.
- Tests: `uv run pytest` after scaffold.
- Build: `uv build` after scaffold.
- CI: sync/install, lint, format check, typecheck, tests, and build before
  release/PR merge after scaffold.
- Error monitoring: N/A for V0.
- Seed data / two test accounts: N/A for V0.

## Alternatives Considered

| Alternative | Why Not Chosen | Cost Of Switching Later |
|---|---|---|
| Saved diff analyzer first | Does not reliably provide agent claims because transcript/session data is missing. | Medium; can remain as `analyze` fallback. |
| Watcher first | Cannot know agent claims without session material and can trigger too early. | Low; remains secondary safety net. |
| Web app first | Adds auth/hosting/UI before local workflow proves value. | Medium; web app can wrap the CLI engine later. |
| SaaS or GitHub App first | Creates privacy, auth, integration, and trust complexity too early. | High; platform assumptions would shape the product prematurely. |
| LLM-first analyzer | Risks generic output, privacy concerns, cost, and hidden judgment. | Medium; optional LLM extraction can be added later behind validated schemas. |
| Raw stdlib `pty` only | Lower dependency count, but more low-level behavior to implement and test. | Low; Pexpect can be replaced if it becomes a problem. |
| `argparse` only | Standard library, but less ergonomic for typed subcommands and future CLI growth. | Low; Typer can be swapped early if needed. |
| Pyright | Strong checker, but adds a separate checker/runtime setup to a Python-first repo. | Low to medium; can add later if mypy is insufficient. |
| Flat package layout | Simpler direct imports, but easier to accidentally import root files. | Low; source layout is cleaner before code exists. |
| Global `utils` layout | Encourages technical-layer ownership instead of product/capability ownership. | Medium; refactor cost grows as helpers multiply. |

## Consequences

### Positive

- Captures the agent session at the moment claims are made.
- Keeps full claim-vs-evidence analysis grounded in transcript and patch
  evidence.
- Produces a useful next-step package, not only a report.
- Protects sensitive code, diffs, and transcripts by default.
- Avoids false confidence from LLM or correctness-score framing.
- Keeps future GitHub, HTML, package, or AI integrations possible without
  committing to them early.

### Negative / Trade-Offs

- Users must run Codex through PatchTrace for the full V0 experience.
- PTY capture can have edge cases with interactive terminal applications.
- V0 is POSIX/macOS/Linux-oriented; Windows support is deferred.
- Early claim extraction will be intentionally conservative and rules-based.
- `watch` is useful but cannot be treated as full session truth.

### Operational Requirements Created By This ADR

- Create fake-command PTY fixtures before real Codex dogfood tests.
- Keep all report claims evidence-backed.
- Treat transcripts as sensitive local material.
- Require explicit approval before adding external services or LLM calls.
- Run lint, format check, typecheck, tests, build, and fixture checks once the
  scaffold exists.

## Follow-Up Docs Triggered

- [ ] `docs/AUTH_ACCESS_MODEL.md` after first protected route/user.
- [ ] `docs/API_CONTRACTS.md` after first shared endpoint/action/webhook/public API.
- [ ] `docs/UI_SYSTEM.md` after second view.
- [ ] `docs/AI_BOUNDARIES.md` after first AI call.
- [ ] `docs/INTEGRATIONS.md` after first provider webhook/callback.
- [ ] `docs/OPERATIONS.md` before package release, background service install,
      or launch preparation.

Current V0 triggers none of the above risk docs.

## Revisit Triggers

- `patchtrace run -- codex` fails to preserve usable Codex CLI interaction.
- The CLI is dogfooded on 3-5 real Codex sessions and report quality demands a
  different architecture.
- Optional JSON becomes a public interface.
- A non-Codex adapter becomes part of the next accepted phase.
- LLM extraction is proposed.
- A local HTML report becomes necessary for comprehension.
- Package publishing or release automation begins.
