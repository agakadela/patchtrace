# VERIFICATION_BRIEF.md

Fixture: `auth-session-ownership`

## Conservative verdict

Conservative verdict: needs_human_review

The patch adds an authentication gate, but the provided material does not prove
project ownership enforcement. Review the route and persistence update before
accepting the agent's ownership claim.

## Inputs reviewed

| Material | Source |
|---|---|
| Agent summary | `agent-summary.md` |
| Changed files | `changed-files.txt` |
| Patch evidence | `patch.diff` |
| Test evidence | `test-output.txt` |
| Manual notes | `notes.md` |

## Agent claims and support

| Agent claim | Support | Evidence-backed assessment |
|---|---|---|
| Users can only update projects they own. | partially_supported | Auth/session ownership claim: partially supported. The route now requires a session and passes `userId` into `updateProject`, but `src/lib/projects.ts` still updates with `where: { id: input.projectId }` and does not show an owner condition or policy-backed isolation. |
| Unauthenticated requests return `401`. | supported | `app/api/projects/[projectId]/route.ts` returns `401` when `getSessionUser()` is null, and the test output shows the unauthenticated test passed. |
| Tests cover project ownership. | unsupported | The test covers a signed-in happy path and no-session path, but it does not exercise user A attempting to update user B's project. |
| No database or RLS changes are needed. | cannot_determine | Cannot verify server-side ownership enforcement from the route-level session check alone. No database policy, unique owner lookup, or two-user proof is included. |

## Risk areas

- Access-control risk: `app/api/projects/[projectId]/route.ts` is a write route for project data.
- Session risk: `src/lib/auth/session.ts` establishes the identity boundary used by the route.
- Ownership-isolation risk: `src/lib/projects.ts` updates by project ID without visible owner scoping.
- Test-quality risk: `tests/api/projects.test.ts` does not include a cross-user ownership denial test.

## Test quality

Observed test command:

```text
pnpm test tests/api/projects.test.ts
```

Result: pass.

What the test evidence appears to prove:

- A signed-in request can reach the update path.
- A missing session returns `401`.

What remains weak or missing:

- Manual two-user test is missing.
- No test shows one user being denied access to another user's project.
- No persistence-level assertion verifies `ownerId` or tenant scoping in the update query.
- No database or RLS policy evidence is provided.

## Cannot verify from provided material

- Cannot verify server-side ownership enforcement for cross-user project updates.
- Cannot verify row-level security, database policy, or equivalent isolation.
- Cannot verify production session configuration or session spoofing resistance.
- Cannot verify audit logs or recovery behavior for unauthorized write attempts.

## Review first

1. `src/lib/projects.ts` - confirm the update query scopes by owner/user and cannot update another user's project by ID alone.
2. `app/api/projects/[projectId]/route.ts` - confirm the session user is required for every write path and error handling does not leak project existence.
3. `src/lib/auth/session.ts` - confirm the session source is trusted and cannot be bypassed in tests or runtime.
4. `tests/api/projects.test.ts` - add a second-user denial test and, if available, a persistence-level ownership assertion.

## Suggested next checks

- Add a test where `user_a` attempts to update a project owned by `user_b`.
- Change or inspect the persistence query so project writes include owner or workspace scope.
- Capture database policy or repository-layer evidence if ownership is enforced below the route.
- Run a manual two-user check before accepting the ownership claim.
