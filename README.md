# PatchTrace

Verify AI-agent code changes before you accept them.

PatchTrace is a local-first open-source devtool that turns patch material, agent claims, and test or command output into a structured verification brief.

It traces agent claims back to local evidence, flags weak or missing test evidence, identifies risky changed areas, lists what cannot be verified from provided material, and tells you which files to review first.

PatchTrace does not replace human code review. It helps you start review with better evidence.

## Status

- Stage: framing / foundation docs
- Current phase: see `docs/PLAN.md`
- Product spec: see `docs/SPEC.md`
- Architecture: see `docs/ARCHITECTURE.md`
- Verification history: see `docs/VERIFY_LOG.md`
- Agent workflow: see `docs/AGENT_WORKFLOW.md`

## Source Of Truth

| Area | File |
|---|---|
| Product scope and success criteria | `docs/SPEC.md` |
| Current execution plan | `docs/PLAN.md` |
| Stack, module convention, data flow, trust boundaries | `docs/ARCHITECTURE.md` |
| Domain language | `CONTEXT.md` |
| Irreversible decisions | `docs/decisions/` |
| Verification proof | `docs/VERIFY_LOG.md` |
| Agent operating workflow | `docs/AGENT_WORKFLOW.md` |

Risk-triggered docs are created only when triggered:

| Trigger | File |
|---|---|
| First protected route/user | `docs/AUTH_ACCESS_MODEL.md` |
| Shared endpoint/action/webhook/public API | `docs/API_CONTRACTS.md` |
| Second view | `docs/UI_SYSTEM.md` |
| First AI call | `docs/AI_BOUNDARIES.md` |
| Provider with webhook/callback | `docs/INTEGRATIONS.md` |
| Existing/rescue repo | `docs/SYSTEM_MAP.md` |
| Launch prep | `docs/OPERATIONS.md` |
| Client delivery | `docs/HANDOFF.md` |

## Intended V0

V0 is a local CLI:

```bash
patchtrace analyze --base main --summary .patchtrace/agent-summary.md --test-output .patchtrace/test-output.txt --out VERIFICATION_BRIEF.md
```

The CLI is not scaffolded yet. Current work is the accepted spec and foundation decision gate before implementation.

## Setup

N/A until the implementation package is scaffolded.

Planned foundation:

```bash
pnpm install
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

## Environment

- Local app URL: N/A; V0 is a CLI.
- Preview/staging URL: N/A.
- Production URL: N/A.
- Database projects are separated by environment: N/A; V0 has no database.
- Secrets live in: N/A; V0 should not require secrets.

Do not put real secrets in README, docs, screenshots, commits, or chat.

## Development Workflow

- Read `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, and `docs/PLAN.md` before work.
- Work on one task at a time.
- Use `using-agent-skills` when the right skill path is unclear.
- Commit after each standard task once the target git repo exists.
- Use `pause before commit` for high-risk work.
- Merge only after review and runtime verification.

## Deployment

- Provider: N/A for V0.
- Deploy command/process: N/A until package release or hosted surface exists.
- Rollback process: see `docs/OPERATIONS.md` once launch prep begins.
- Monitoring: N/A for V0 local CLI.

## Known Limitations

- PatchTrace does not prove code correctness.
- PatchTrace does not claim a patch is safe or production verified.
- V0 has no SaaS, auth, teams, GitHub integration, HTML report, or required LLM calls.
- The first implementation should be fixture-first, with hand-written expected verification briefs before analyzer behavior.
