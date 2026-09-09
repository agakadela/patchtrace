# PatchTrace

PatchTrace is a local evidence and verification layer for coding-agent runs. It
helps a developer decide whether the captured evidence is sufficient to review
or accept a run, whether more verification is needed, or whether work should be
sent back to the agent.

PatchTrace does not prove semantic correctness and does not make the final
decision for the developer.

## Current status

Version `0.1.0` includes the Phase 4 baseline, Phase 4.1 T1 storage hardening,
T2 file/change claim assessment, T3 command-attempt semantics, and Phase 5 T1
Git session capture, T2 attribution, T3 report provenance, T4 lifecycle outcomes, and T5 task capture.
The implemented command is:

```bash
patchtrace run -- <command>
```

It:

- runs the command in an interactive PTY;
- preserves the terminal transcript;
- records Git status before and after the command;
- records the final staged and unstaged diff visible after the command;
- preserves before/after HEAD, dirty paths, bounded untracked file bytes, and
  patches for a straightforward commit range in `git-session.json`;
- applies deterministic rules to bounded claims in one identified final answer;
- writes one local review package outside the reviewed working tree (location
  below).

`patchtrace analyze` and `patchtrace watch` are placeholders and exit with an
explicit not-implemented error.

## Try it

PatchTrace requires Python 3.11 or newer and uses
[uv](https://docs.astral.sh/uv/) for project development.

```bash
uv sync
uv run patchtrace run -- python tests/fixtures/fake_agent.py
```

To wrap an installed interactive Codex CLI:

```bash
uv run patchtrace run -- codex
```

The wrapped command retains its normal terminal interaction. When it exits,
PatchTrace prints the path to the generated package.

## Capture a task

```bash
uv run patchtrace run --task-file tests/fixtures/tasks/valid.md -- python tests/fixtures/fake_agent.py
```

Supply a UTF-8 Markdown file with this minimal structure:

```markdown
## Outcome
Describe the intended result.

## Requirements
1. Describe one requirement per line.
```

Optional `## Acceptance Criteria`, `## Required Verification`, and
`## Out of Scope` sections accept numbered items or `N/A`. Run `patchtrace run
--help` to discover the option. The exact
[Task Contract V1 syntax and failure mapping](docs/ARCHITECTURE.md#213-task-contract-v1-capture--phase-5-t5)
are documented in the architecture.

The package adds the unchanged `task.md`, a parsed `task.json`, and a SHA-256
binding in `run.json`. Invalid input is preserved with a parsing failure and
stops before the command starts. Omitting the option permits the generic run
with a visible trust limitation. Task capture does not send a prompt to the
wrapped command or evaluate requirement satisfaction.

## Run package

Packages use `$XDG_STATE_HOME/patchtrace/repos/<repository-id>/runs/<run-id>/`;
when `XDG_STATE_HOME` is unset, empty, or relative, the base is `~/.local/state`.
The CLI prints the absolute path. `run.json` identifies the run and records
`repository_root`, the original canonical Git worktree path. Subdirectory runs
share the same repository key; moving a checkout creates a new key.

Storage inside the reviewed worktree, including through a symlink, is rejected
before the wrapped command runs. Set `XDG_STATE_HOME` to an absolute external
directory if that occurs. PatchTrace does not edit `.gitignore` or Git settings.
Existing packages in `.patchtrace` remain where they are.
See the [storage decision](docs/ARCHITECTURE.md#25-run-storage-decision--phase-41-t1).

A complete package contains:

```text
<external-state>/patchtrace/repos/<repository-id>/runs/<run-id>/
├── run.json
├── agent-session.txt
├── git-before.txt
├── git-after.txt
├── changed-files.txt
├── patch.diff
├── git-session.json
├── SUMMARY.md
├── AGENT_FEEDBACK.md
└── VERIFICATION_BRIEF.md
```

`run.json` links the envelope through `git_evidence.session_envelope_path`.
Capture uses non-mutating Git commands. Active external content filters are
unsupported and fail capture without execution. If capture fails after repository
validation, the CLI exits 1 and prints the partial run path; `git-session.json`
preserves the failing stage, error, recovery guidance, and completed boundaries.
See the [capture contract](docs/ARCHITECTURE.md#29-git-session-envelope--phase-5-t1).

`run.json` schema version 2 records three independent outcomes:

- `process_outcome`: `not_started`, `completed`, `failed`, or `unknown`;
- `analysis_outcome`: `not_run`, `completed`, `degraded`, or `failed`;
- `package_outcome`: `partial`, `complete`, or `failed`.

For example, a command can exit 0, have no identifiable final answer, and produce
`completed` / `degraded` / `complete`. Evidence verdicts remain review guidance.
A package is marked `complete` only after required artifacts and all reports are
written and the final manifest is replaced. Reports link to `run.json` for that
final fact. On failure, inspect its `failures` entries and the printed partial
package path. If the manifest cannot be saved, the CLI says so; an older partial
checkpoint may be all that remains, or no manifest may exist.

CLI exit behavior:

| Condition | Exit status |
| --- | --- |
| Complete package, including degraded analysis | Wrapped command status (0 or non-zero; signals use 128 + signal) |
| Capture, analysis execution, package validation, or write failure | 1; the manifest retains any observed command status |
| Missing command | 2 |

The legacy combined `outcome` field is removed. Existing packages stay unchanged;
old manifests are not silently upgraded or accepted by the version-2 model.
Phase 4 raw fixtures still exercise their evidence semantics through explicit
version-2 test manifests. See the
[lifecycle contract and compatibility decision](docs/ARCHITECTURE.md#212-lifecycle-outcomes--phase-5-t4).

The reports are deterministic views of one validated analysis result:

- `SUMMARY.md` gives the verdict, most important gap, and next action.
- `AGENT_FEEDBACK.md` turns evidence gaps into follow-up requests.
- `VERIFICATION_BRIEF.md` links assessed claims to local evidence for review.

## Current evidence limits

All three reports show the same Git attribution, source references, and
limitations from one analysis result. Attribution counts describe material
observations, not unique files. See the
[report contract](docs/ARCHITECTURE.md#211-report-provenance--phase-5-t3).
Current limits:

- the final Git diff can include work that existed before the run;
- untracked bytes are limited to 1 MiB per file / 8 MiB per boundary; symlink
  content is omitted;
- commit evidence supports at most 100 commits in a direct single-parent range;
  merges, rewrites and unborn HEAD ranges carry explicit limitations;
- unchanged initial dirty material is pre-existing; later work on the same dirty
  path remains indeterminate because its bytes cannot be separated;
- the PTY parser requires exactly one supported final-answer marker;
- a missing or ambiguous marker degrades claim evidence; PatchTrace does not
  guess from the transcript tail;
- command and test signals are inferred from terminal text, not structured
  command events;
- there is no preserved task contract or requirement-coverage analysis;
- a passing check is not proven fresh relative to the final repository state.

Treat current verdicts as review guidance within those limits, not as proof of
correctness or acceptance.

## Product direction

Phase 4.1 — Trust Hardening is closed. It addressed three gaps in the Phase 4 baseline:

1. keep run artifacts outside the reviewed working tree so `git add .` cannot
   accidentally stage them;
2. prevent a changed file path from confirming a semantic change claim;
3. assess the latest captured command attempt, parse zero failures correctly,
   and surface failed verification even when the agent reports it truthfully.

The active phase is **Phase 5 — Trusted Capture and Session Provenance**.
T1–T4 implement Git capture, attribution, report provenance, and independent
lifecycle outcomes. T5 — Task Contract capture is next; [PLAN.md](docs/PLAN.md)
owns task status. The phase strengthens capture before broadening analysis:

1. distinguish session-attributed, pre-existing, and indeterminate Git changes;
2. separate process, analysis, and package outcomes;
3. preserve a simple Task Contract and bind it to the run;
4. pass that same preserved task through supported Codex-specific modes;
5. test whether the official Codex App Server can provide structured evidence
   for the same interactive session without replacing the current UX.

Interactive PTY remains the primary compatibility workflow. Structured Codex
execution may be offered as a separate higher-evidence task mode. App Server is
a candidate subject to a small feasibility prototype, not an accepted target
architecture.

See:

- [Product specification](docs/SPEC.md)
- [Roadmap](docs/ROADMAP.md)
- [Active Phase 5 plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Domain language](CONTEXT.md)

## Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv build
```

Verification milestones are recorded in
[docs/VERIFY_LOG.md](docs/VERIFY_LOG.md).
