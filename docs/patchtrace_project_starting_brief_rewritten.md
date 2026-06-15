# PatchTrace - Project Starting Brief

Status: working project brief  
Working name: **PatchTrace**  
Repo name: `patchtrace`  
Current decision: continue as a **local-first public OSS devtool candidate**  
Primary scope: **local patch verification for AI-assisted coding**  
Primary product slice: **Local Patch Verification Engine**  
Out of scope for V0: SaaS, auth, teams, GitHub OAuth, public proof, client updates, social posts, video replay, automatic correctness scoring

---

## 1. One-line definition

**PatchTrace helps developers verify what an AI coding agent changed before they accept the patch.**

Longer version:

> PatchTrace analyzes an AI-agent coding session through the actual patch: changed files, git diff, agent claims, test output, risk areas, weak or missing evidence, cannot-verify items, and review-first files. It produces a conservative verification brief for the human reviewer.

The product is not a generic brief generator.

It is a local verification layer between:

```text
AI agent says "done"
```

and:

```text
developer accepts the patch
```

---

## 2. Core repositioning

The previous direction was too close to:

```text
paste agent summary + notes -> get markdown brief
```

That is useful, but too soft for the public OSS product goal.

The new direction is:

```text
local repo / patch / test output / agent summary
-> structured analysis pipeline
-> claim/evidence matrix
-> risk and test-quality assessment
-> review-first list
-> VERIFICATION_BRIEF.md
```

PatchTrace should start from the patch, not from a blank form.

V0 can still accept manual agent notes, but the technical spine should be real:

- inspect changed files,
- read a git diff,
- parse or ingest test output,
- compare agent claims against evidence,
- classify changed areas by risk,
- flag weak tests,
- produce a conservative verdict.

---

## 3. Why this exists

AI coding agents can produce code faster than developers can comfortably review it.

After a session with Codex, Cursor, Claude Code, GitHub Copilot coding agent, or another agent, the developer usually has:

- an agent summary,
- a changed working tree,
- a diff,
- terminal output,
- test output,
- partial notes,
- uncertainty about what was actually verified.

The bottleneck is no longer only:

```text
Can the agent make code changes?
```

The bottleneck is:

```text
Can the developer verify what the agent changed without reading the whole patch cold?
```

PatchTrace reduces that review bottleneck by turning agent work into a source-backed verification brief.

It does not replace human review.

It helps the human start review from the right files, with the right questions, and without trusting the agent summary as truth.

---

## 4. Product framing

PatchTrace is not:

- an AI code reviewer,
- a correctness oracle,
- a model benchmark,
- a generic eval platform,
- a content generator,
- a client update tool,
- a video/replay app,
- an agent observability dashboard,
- a replacement for tests,
- a replacement for code review.

PatchTrace is:

> a local patch verification tool for AI-assisted coding work.

It helps the developer answer:

1. What did the agent claim it changed?
2. What files actually changed?
3. What does the diff appear to touch?
4. What evidence supports each claim?
5. Which claims are unsupported or only partially supported?
6. Which areas are risky: auth, data, payments, webhooks, AI cost, jobs, migrations, storage?
7. What tests/checks were run?
8. Do the tests actually cover the risky behavior?
9. Which checks are missing?
10. What cannot be verified from local source and provided output?
11. Which files should the developer review first?
12. Should the developer accept, review carefully, or send the agent back?

---

## 5. Public OSS positioning

PatchTrace exists as a useful open-source devtool, not as AI hype.

A developer evaluating the project should see:

- clear problem framing,
- source-backed reasoning,
- conservative trust boundaries,
- a real TypeScript domain model,
- deterministic analysis where possible,
- explicit limits where proof is missing,
- test-quality awareness,
- good local-first product judgment,
- practical use of AI agents without losing control.

The project should communicate:

> Coding agents are useful, but their patches still need evidence-backed human review.

It should not say:

> I built a trendy AI wrapper.

Engineering quality is shown through decisions:

- local-first because code and diffs can be sensitive,
- no correctness score because false precision is dangerous,
- no production safety claims without runtime evidence,
- no SaaS before the local workflow proves value,
- no generic warnings unless tied to changed files, evidence, or missing evidence.

---

## 6. Working name rationale

### Chosen working name: `PatchTrace`

Why:

- **Patch** points to actual code changes, diffs, branches, and agent-produced patches.
- **Trace** points to evidence, review trail, claims, tests, and risk reasoning.
- It sounds like a devtool.
- It does not overpromise automated correctness.
- It fits a GitHub open-source project.

Primary tagline:

> Verify what your coding agent changed before you accept it.

Alternative taglines:

- Trace agent claims back to the patch.
- Turn agent work into an evidence-backed review brief.
- Review AI-agent changes faster, without trusting the summary.

---

## 7. Primary user

Primary user:

- developers using coding agents,
- solo engineers,
- AI-assisted freelancers,
- small software studios,
- engineers reviewing agent-created PRs,
- teams experimenting with AI-agent workflows.

This is a dogfood-first public OSS devtool, not a validated SaaS.

External market demand is not assumed.

---

## 8. V0 product concept

### V0 name

**Local Patch Verification Engine**

### V0 goal

Help a developer produce a useful verification brief from a local patch created by an AI coding agent.

### V0 shape

CLI-first, with optional local HTML report later.

A good V0 can be:

```bash
patchtrace analyze --base main --head working-tree --summary agent-summary.md --test-output test-output.txt
```

or:

```bash
patchtrace analyze --diff patch.diff --changed-files changed-files.txt --summary agent-summary.md --test-output test-output.txt
```

### V0 input

Primary input:

- local git diff,
- changed file list,
- agent summary or session notes,
- test output,
- optional manual developer notes,
- optional session goal.

Secondary input later:

- pasted diff,
- saved agent log,
- local JSON session export,
- PR diff file.

### V0 output

Primary output:

- `VERIFICATION_BRIEF.md`

Optional output:

- `patchtrace-report.json`
- `REVIEW_FIRST.md`
- local static HTML report

The Markdown report is the core artifact.

---

## 9. Core workflow

The core workflow should be:

```text
collect patch material
-> normalize inputs
-> extract agent claims
-> identify changed files and changed areas
-> match claims to evidence
-> classify risk areas
-> assess test evidence
-> identify cannot-verify items
-> rank review-first files
-> build conservative verdict
-> export verification brief
```

The important part is not that every step is perfect.

The important part is that every step is explicit, testable, and conservative.

---

## 10. Core reasoning model

PatchTrace should follow this model:

```text
agent claim
-> patch evidence
-> test evidence
-> risk area
-> missing verification
-> review-first files
-> verdict
```

Example:

```text
Agent claim:
Added duplicate webhook protection.

Patch evidence:
- app/api/stripe/webhook/route.ts changed
- lib/billing/entitlements.ts changed
- diff includes a processed event lookup

Test evidence:
- billing-webhook.test.ts added
- test output shows passing webhook handler test

Test quality:
- test appears to check 200 response
- no evidence that the same Stripe event was sent twice
- no assertion that entitlement is granted only once

Risk:
- payment/access boundary
- webhook idempotency
- entitlement state

Missing verification:
- no duplicate event test evidence
- no processed event persistence proof
- no production Stripe webhook setting proof

Review first:
1. app/api/stripe/webhook/route.ts
2. lib/billing/entitlements.ts
3. billing-webhook.test.ts

Verdict:
Needs focused human review before accepting.
```

---

## 11. Claim vs evidence

This is the most important product idea.

The agent summary is not trusted as truth.

PatchTrace should extract or accept agent claims, then compare them against provided evidence.

### Claim support levels

```ts
type ClaimSupport =
  | "supported"
  | "partially_supported"
  | "unsupported"
  | "contradicted"
  | "cannot_determine";
```

### Supported claim

A claim is supported when the provided material contains direct evidence.

Example:

```text
Claim:
Added tests for duplicate webhook processing.

Evidence:
- billing-webhook.test.ts added
- test output includes "duplicate event is ignored"
- assertion checks entitlement is granted once
```

### Partially supported claim

A claim is partially supported when related files changed, but key proof is missing.

Example:

```text
Claim:
Added duplicate webhook protection.

Evidence:
- webhook route changed
- diff includes processed event lookup

Missing:
- no duplicate event test output
- no persistence/constraint evidence
```

### Unsupported claim

A claim is unsupported when the agent says something, but provided files/tests/notes do not back it up.

Example:

```text
Claim:
Added test coverage.

Unsupported:
No test file changed. No test output provided.
```

### Contradicted claim

A claim is contradicted when agent says the work is complete but provided evidence shows failure.

Example:

```text
Claim:
All tests pass.

Contradiction:
Provided test output shows `billing-webhook.test.ts` failed.
```

PatchTrace should be intentionally conservative.

---

## 12. Patch evidence

PatchTrace should collect evidence from the actual changed material.

V0 evidence sources:

```ts
type EvidenceType =
  | "changed_file"
  | "diff_hunk"
  | "test_file"
  | "test_output"
  | "agent_summary"
  | "developer_note"
  | "command_output";
```

Examples of useful evidence:

- file path changed,
- new test file added,
- removed auth check,
- added database migration,
- touched payment/webhook handler,
- test command passed or failed,
- diff includes idempotency guard,
- diff includes rate limiting,
- diff includes public env variable use,
- developer note says runtime flow was manually checked.

Evidence should be tied to source material.

Bad:

```text
Looks safe.
```

Good:

```text
Payment webhook route changed and test output was provided, but no duplicate-event test evidence was found.
```

---

## 13. Changed area detection

PatchTrace should identify changed areas from file paths, filenames, and diff content.

V0 can use a ruleset. It does not need full semantic code understanding.

Examples:

```text
app/api/stripe/webhook/route.ts -> payment, webhook, API route
middleware.ts -> auth/session/routing boundary
supabase/migrations/* -> database/schema/data integrity
lib/ai/* -> AI endpoint/cost/model boundary
inngest/* -> async/background jobs
```

Changed area detection should feed:

- risk classification,
- review-first ranking,
- missing verification suggestions,
- test-quality expectations.

---

## 14. Risk area detection

PatchTrace should detect risk areas from changed files, diff content, test output, and manual context.

### Payment / billing / entitlement

Patterns:

```text
stripe
checkout
payment
webhook
billing
subscription
invoice
entitlement
credits
access
customer portal
```

Review concerns:

- webhook signature verification,
- idempotency,
- duplicate events,
- failed payment behavior,
- access granted from untrusted redirect,
- product state vs payment state,
- missing processed event guard,
- missing transaction,
- refund/cancel/dispute behavior.

Expected verification:

- webhook signature test or code evidence,
- duplicate event test,
- entitlement state assertion,
- failed payment/cancellation behavior if relevant,
- cannot-verify production Stripe dashboard settings.

### Auth / session / permissions

Patterns:

```text
auth
session
login
middleware
permissions
roles
membership
workspaceId
organizationId
userId
ownerId
```

Review concerns:

- missing auth,
- missing ownership check,
- trusting userId from the client,
- tenant boundary gaps,
- role escalation,
- middleware matcher gaps,
- frontend-only protection.

Expected verification:

- User A/User B access test,
- ownership assertion,
- route/API authorization check,
- cannot-verify deployed auth provider/dashboard settings if relevant.

### AI endpoint / cost boundary

Patterns:

```text
openai
anthropic
ai
llm
chat
generate
model
tokens
usage
rate limit
```

Review concerns:

- no auth,
- no rate limit,
- no usage/cost logging,
- no input length limit,
- model output not validated,
- retries multiplying cost,
- public endpoint calling paid model.

Expected verification:

- auth check evidence,
- rate limit evidence,
- usage logging evidence,
- input validation evidence,
- cannot-verify production API key/env state.

### Background jobs / async

Patterns:

```text
inngest
queue
job
worker
cron
retry
sync
webhook
```

Review concerns:

- idempotency,
- duplicate processing,
- partial failure,
- retry loops,
- missing dead-letter path,
- missing observability,
- silent failures.

Expected verification:

- idempotency test,
- retry behavior evidence,
- failed job behavior,
- logging/monitoring evidence.

### Database / data integrity

Patterns:

```text
migration
schema
prisma
drizzle
sql
insert
update
transaction
constraint
unique
foreign key
```

Review concerns:

- multi-step write without transaction,
- check-then-create without unique constraint,
- missing foreign key,
- missing index,
- silent partial failure,
- migration not covered by tests,
- data shape drift.

Expected verification:

- migration file evidence,
- constraint/index evidence,
- transaction evidence if multi-step write,
- test or manual check for duplicate/concurrent behavior.

### Storage / files

Patterns:

```text
storage
bucket
upload
signed url
file
image
audio
pdf
```

Review concerns:

- public/private boundary,
- file type validation,
- file size validation,
- private files in public bucket,
- overwrite path risk,
- predictable object paths,
- missing cleanup.

Expected verification:

- file validation evidence,
- private access test,
- signed URL expiry check,
- cannot-verify cloud bucket policy if not provided.

---

## 15. Test Quality Review

Test results are not automatically proof.

PatchTrace should distinguish:

```text
Tests passed.
```

from:

```text
Tests prove the risky behavior claimed by the agent.
```

### Test Quality Review should ask

1. What behavior do the tests actually verify?
2. Do they cover the changed logic?
3. Do they cover the risky path?
4. Could they pass even if the original bug still exists?
5. Are they too mocked?
6. Do they assert meaningful state or just existence?
7. Do they test behavior or implementation details?
8. Was there any failed-before / passed-after evidence?
9. Is the test near the risk area or unrelated?
10. Does test output match the agent claim?

### Common weak test patterns

- `expect(result).toBeDefined()`
- only checks that handler returns `200`
- mocks the entire logic that should be tested
- tests UI text while bug was backend state
- snapshot-only tests
- no assertion on final state
- happy path only
- test file added but no output provided
- passing test output from unrelated test suite
- no failed-before / passed-after evidence

### Stronger test evidence

For duplicate Stripe webhook protection:

```text
same event sent twice
-> event is processed once
-> entitlement is granted once
-> processed event is persisted
```

For tenant access:

```text
User A owns record A
User B owns record B
User B cannot read/update/delete record A
API returns forbidden or empty result
```

For AI endpoint cost control:

```text
unauthenticated request rejected
large input rejected or truncated
rate limit triggered
usage event recorded
```

### Test quality labels

```ts
type TestEvidenceStrength =
  | "strong"
  | "medium"
  | "weak"
  | "missing"
  | "contradictory"
  | "not_applicable";
```

PatchTrace should not claim full coverage.

It should say what the provided test evidence appears to prove, what it does not prove, and which test would be useful next.

---

## 16. Cannot verify discipline

PatchTrace must not create false certainty.

`Cannot verify` is a core feature, not a disclaimer.

Examples:

```text
Cannot verify:
- Production Stripe webhook endpoint settings.
- Live webhook replay behavior.
- Vercel production environment variables.
- Supabase dashboard RLS state.
- Runtime permission behavior with real users.
- Actual deployed security headers.
- Backup restore behavior.
- Real user flow in production.
- Provider dashboard configuration.
- Whether the app was deployed after this patch.
```

PatchTrace should use `cannot verify` whenever proof requires:

- production dashboard access,
- deployed runtime behavior,
- provider configuration,
- secrets/env values,
- live database state,
- real user accounts,
- logs not provided,
- manual QA not provided.

The tool should not hide these limits.

This is part of the value.

---

## 17. Review-first output

Developers do not need 30 vague warnings.

PatchTrace should produce a short, file-specific review-first list.

Bad output:

```text
Potential risks:
- security
- performance
- maintainability
- edge cases
- testing
```

Good output:

```text
Review first:
1. app/api/stripe/webhook/route.ts
   Reason: payment state changes and duplicate event handling live here.

2. lib/billing/entitlements.ts
   Reason: access grant/revoke logic changed.

3. billing-webhook.test.ts
   Reason: test exists, but provided output does not prove duplicate event behavior.
```

Review-first ranking should consider:

- high-risk area touched,
- centrality of file path,
- claim/evidence mismatch,
- missing tests,
- failed tests,
- diff size,
- files that mutate money/access/data,
- migrations or schema changes,
- auth/session boundaries.

---

## 18. Verdict model

Verdicts must be conservative.

Allowed verdicts:

```ts
type Verdict =
  | "ready_for_focused_review"
  | "needs_human_review"
  | "send_agent_back"
  | "insufficient_material";
```

No verdict should say:

```text
Correct.
Safe.
Guaranteed.
Production verified.
```

unless there is actual proof, which V0 usually will not have.

### Example verdicts

```text
Verdict: Needs human review before accepting.

Reason:
Payment/access logic changed. The agent claims tests were added, but provided test output does not prove duplicate webhook behavior. Production Stripe webhook settings cannot be verified from local source.
```

```text
Verdict: Send agent back for another round.

Reason:
The main claim is contradicted by provided test output. The agent says the work is complete, but the billing test suite is failing.
```

```text
Verdict: Ready for focused human review.

Reason:
The main claim is supported by changed files and relevant passing test output. Review should still start with entitlement state and duplicate event handling before accepting.
```

```text
Verdict: Insufficient material.

Reason:
Agent summary was provided, but no diff, changed file list, or test output was available. PatchTrace cannot evaluate claim support from the current material.
```

---

## 19. V0 CLI workflow

### Command examples

Analyze working tree against main:

```bash
patchtrace analyze --base main --head working-tree --summary agent-summary.md --test-output test-output.txt
```

Analyze a saved diff:

```bash
patchtrace analyze --diff patch.diff --summary agent-summary.md --test-output test-output.txt
```

Generate JSON and Markdown:

```bash
patchtrace analyze --base main --summary agent-summary.md --test-output test-output.txt --json report.json --out VERIFICATION_BRIEF.md
```

### V0 commands

```text
patchtrace init
patchtrace analyze
patchtrace export
patchtrace fixtures
```

Possible first command set:

```bash
patchtrace analyze \
  --base main \
  --summary .patchtrace/agent-summary.md \
  --test-output .patchtrace/test-output.txt \
  --notes .patchtrace/manual-notes.md \
  --out VERIFICATION_BRIEF.md
```

### V0 generated files

```text
.patchtrace/
  agent-summary.md
  test-output.txt
  manual-notes.md
  report.json
VERIFICATION_BRIEF.md
```

---

## 20. Optional local UI

The first version does not need a full UI.

A local HTML report can be added after the CLI works.

Useful UI later:

- claim/evidence matrix,
- changed file map,
- risk tags,
- weak test warnings,
- review-first list,
- cannot-verify list,
- Markdown export.

UI should visualize the analysis.

It should not replace the core engine.

---

## 21. Data model

Suggested minimal types:

```ts
type PatchTraceInput = {
  sessionGoal?: string;
  agentSummary?: string;
  manualNotes?: string;
  changedFiles: ChangedFile[];
  diffHunks: DiffHunk[];
  testOutput?: TestOutput;
  commandOutput?: CommandOutput[];
  createdAt: string;
};

type ChangedFile = {
  path: string;
  status: "added" | "modified" | "deleted" | "renamed" | "unknown";
  additions?: number;
  deletions?: number;
};

type DiffHunk = {
  filePath: string;
  hunkHeader?: string;
  addedLines: string[];
  removedLines: string[];
};

type AgentClaim = {
  id: string;
  text: string;
  source: "agent_summary" | "manual_note";
  normalizedCategory?: string;
};

type Evidence = {
  id: string;
  type: EvidenceType;
  summary: string;
  filePath?: string;
  rawExcerpt?: string;
};

type ClaimAssessment = {
  claimId: string;
  support: ClaimSupport;
  supportingEvidence: Evidence[];
  missingEvidence: MissingCheck[];
  contradictions: Evidence[];
  notes: string[];
};

type RiskArea = {
  id: string;
  type:
    | "payment"
    | "auth"
    | "data_access"
    | "database"
    | "ai_cost"
    | "webhook"
    | "background_job"
    | "storage"
    | "deployment"
    | "unknown";
  severity: "low" | "medium" | "high";
  reason: string;
  evidence: Evidence[];
};

type TestQualityAssessment = {
  strength: TestEvidenceStrength;
  testsFound: Evidence[];
  appearsToVerify: string[];
  doesNotVerify: string[];
  weakPatterns: string[];
  suggestedNextTests: string[];
};

type ReviewTarget = {
  filePath: string;
  priority: 1 | 2 | 3 | 4 | 5;
  reason: string;
  relatedClaims: string[];
  relatedRisks: string[];
};

type CannotVerifyItem = {
  text: string;
  reason: string;
  requiredEvidence?: string;
};

type VerificationBrief = {
  sessionGoal?: string;
  summary: string;
  claims: AgentClaim[];
  claimAssessments: ClaimAssessment[];
  changedAreas: string[];
  riskAreas: RiskArea[];
  testQuality: TestQualityAssessment;
  checksRun: string[];
  checksMissing: MissingCheck[];
  reviewFirst: ReviewTarget[];
  cannotVerify: CannotVerifyItem[];
  suggestedNextSteps: string[];
  verdict: Verdict;
};
```

---

## 22. Suggested architecture

V0 should have a small but real engine.

```text
src/
  cli/
    index.ts
    commands/
      analyze.ts
      init.ts
      export.ts
  core/
    collect-git-material.ts
    parse-diff.ts
    parse-test-output.ts
    extract-claims.ts
    detect-changed-areas.ts
    match-claim-evidence.ts
    classify-risk-areas.ts
    assess-test-quality.ts
    build-cannot-verify.ts
    rank-review-first.ts
    build-verdict.ts
    build-verification-brief.ts
    export-markdown.ts
  rules/
    risk-rules.ts
    test-quality-rules.ts
    claim-patterns.ts
    file-area-rules.ts
  schemas/
    patchtrace-input.ts
    verification-brief.ts
  evals/
    fixtures/
  tests/
```

Architecture principle:

> Keep the analysis pipeline explicit. Do not hide core judgment inside one LLM prompt.

---

## 23. AI usage

AI is optional in V0.

The first strong version can be mostly rules-based:

- git diff collection,
- path and keyword matching,
- basic claim extraction from agent summary,
- test output parsing,
- deterministic risk classification,
- templated Markdown generation.

If an LLM is used later:

- use it only for extraction/summarization,
- pass structured input,
- request structured JSON,
- validate with Zod,
- never treat LLM output as truth,
- always tie output back to evidence,
- keep cannot-verify conservative,
- never ask the model to guarantee correctness.

Bad use of AI:

```text
Is this patch safe?
```

Better use of AI:

```text
Extract explicit claims from this agent summary as JSON. Do not infer claims that are not stated.
```

---

## 24. Internal evals for PatchTrace

PatchTrace needs fixture-based tests so it does not generate vague confidence.

Do not build a full eval platform.

Create small test cases with expected outputs.

### Fixture structure

```text
evals/
  fixtures/
    01-unsupported-test-claim/
      agent-summary.md
      patch.diff
      changed-files.txt
      test-output.txt
      manual-notes.md
      expected-report.json
```

### First five fixtures

#### 1. Unsupported test claim

Agent claims tests were added, but no test files or test output are provided.

Expected:

- unsupported claim,
- missing test evidence,
- verdict: needs human review or insufficient material.

#### 2. Payment/webhook risk

Changed files include Stripe webhook and entitlement logic.

Expected:

- risk areas: payment, webhook, access, idempotency,
- review-first includes webhook and entitlement files,
- cannot verify production Stripe settings,
- missing duplicate-event test if not present.

#### 3. Auth/session risk

Changed files include middleware/session/permissions.

Expected:

- risk areas: auth, session, authorization,
- review-first includes changed auth files,
- missing User A/User B or ownership test if not present.

#### 4. Failed tests vs agent "done" claim

Agent says work is complete, but test output includes failure.

Expected:

- contradiction,
- checks run include failing test,
- verdict: send agent back.

#### 5. Weak test quality

Test file exists and passes, but only checks `toBeDefined()` or handler returns 200.

Expected:

- test found,
- weak test evidence,
- missing behavior assertion,
- suggested next test.

### Additional fixtures later

- public AI endpoint without rate limit,
- Supabase/RLS data boundary change,
- database migration without uniqueness constraint,
- background job retry/idempotency risk,
- storage bucket private/public risk.

---

## 25. Verification Brief structure

The main output should be a Markdown report.

```text
# Verification Brief

## 1. Session goal
## 2. Patch summary
## 3. Agent claims
## 4. Claim/evidence matrix
## 5. Changed areas
## 6. Risk areas
## 7. Test quality review
## 8. Checks run
## 9. Checks missing
## 10. Review first
## 11. Cannot verify
## 12. Suggested next steps
## 13. Verdict
```

### Claim/evidence matrix example

```md
| Claim | Support | Evidence | Missing / concern |
|---|---|---|---|
| Added duplicate webhook protection | Partially supported | Webhook route changed; processed event lookup appears in diff | No duplicate event test output; no persistence/constraint evidence |
| Added tests | Weak support | billing-webhook.test.ts changed | Test appears to assert 200 response only |
| All tests pass | Contradicted | Provided test output shows one failing suite | Send agent back before accepting |
```

---

## 26. Suggested next steps output

PatchTrace should suggest practical next steps tied to evidence gaps.

Good examples:

```text
Suggested next steps:
- Ask the agent to add a duplicate webhook event test.
- Manually review entitlement grant/revoke logic.
- Verify whether processed event persistence is transactional.
- Run the webhook test suite locally.
- Do not accept until failing billing test is resolved.
```

Bad examples:

```text
Improve security.
Add more tests.
Review carefully.
```

Every next step should answer:

```text
What should the developer or agent do next, and why?
```

---

## 27. V0 success criteria

PatchTrace V0 is successful if, after 3-5 dogfood sessions:

1. It helps identify where to start review faster.
2. It catches unsupported agent claims.
3. It makes weak/missing test evidence visible.
4. It produces useful cannot-verify items.
5. It reduces cognitive load before reading the full diff.
6. It does not create false confidence.
7. The developer would voluntarily use it again.
8. The generated report is good enough to commit into a repo as review context.

Time target:

```text
A useful verification brief should take under 5 minutes to generate from local patch material and pasted agent/test notes.
```

If PatchTrace takes longer than writing manual review notes and does not improve quality, it fails.

---

## 28. What not to build in V0

Do not build:

- SaaS,
- login,
- teams,
- billing,
- GitHub OAuth,
- PR integration,
- cloud sync,
- comments,
- notifications,
- client updates,
- public/social summaries,
- video replay,
- PNG cards,
- carousel exports,
- full Codex/Cursor/Claude log parser,
- MCP integration,
- agent observability dashboard,
- full eval platform,
- automatic correctness scoring.

These are distractions until the local verification workflow proves useful.

---

## 29. Main risks

### 29.1 False promise

Risk:

> Users think PatchTrace proves code correctness.

Mitigation:

- never claim correctness,
- use conservative verdicts,
- always include cannot-verify,
- keep report language evidence-based.

### 29.2 Too much manual input

Risk:

> The tool adds work instead of reducing review burden.

Mitigation:

- collect git diff automatically,
- allow pasted agent summary/test output,
- keep required input minimal,
- make first run useful in under 5 minutes.

### 29.3 Vague output

Risk:

> Output becomes generic AI checklist noise.

Mitigation:

- review-first list must be file-specific,
- warnings must tie to evidence or missing evidence,
- no generic risk list without changed files.

### 29.4 Overreaching test analysis

Risk:

> Tool pretends to know whether tests are truly sufficient.

Mitigation:

- phrase as "test evidence appears weak/strong based on provided material,"
- suggest missing tests,
- do not guarantee coverage.

### 29.5 Privacy/secrets

Risk:

> User pastes sensitive data or sends private code to an LLM.

Mitigation:

- local-first by default,
- no cloud in V0,
- do not ask for `.env`,
- add input warnings,
- later add redaction checks,
- LLM use must be opt-in if added.

### 29.6 It might be only a template

Risk:

> A good prompt/template is enough.

Mitigation:

- prove value through actual diff/test ingestion,
- dogfood with real sessions,
- compare against manual notes,
- if template wins, keep it as an OSS workflow asset instead of forcing a product.

---

## 30. Market notes

Market facts can support timing, but they are not product validation.

The current thesis:

> AI-agent coding increases output, but human verification remains the bottleneck.

Any public README or case study should verify current market statistics before publishing them.

Use market notes carefully:

- AI coding adoption is rising,
- trust in AI-generated output remains a concern,
- coding agents are moving toward autonomous branch/PR workflows,
- agent-generated PRs create new review burden,
- research and platform guidance increasingly discuss where agentic coding fails.

These support the timing.

They do not prove demand for PatchTrace as a paid product.

---

## 31. Repo quality bar

PatchTrace should look like a serious small devtool.

Minimum repo structure:

```text
README.md
docs/
  problem.md
  architecture.md
  verification-model.md
  limitations.md
  dogfood-notes.md
examples/
  verification-briefs/
src/
  cli/
  core/
  rules/
  schemas/
  evals/
tests/
```

Docs that matter:

- `docs/problem.md` - what problem this solves,
- `docs/verification-model.md` - claim/evidence/test/risk/cannot-verify model,
- `docs/architecture.md` - why the pipeline is built this way,
- `docs/limitations.md` - what PatchTrace does not prove,
- `docs/dogfood-notes.md` - results from real agent sessions.

The README should be short, practical, and demo-led.

---

## 32. Suggested README opening

```md
# PatchTrace

Verify AI-agent code changes before you accept them.

PatchTrace is a local-first devtool that turns a git diff, changed files, agent summary, and test output into a structured verification brief.

It traces agent claims back to patch evidence, flags weak or missing test evidence, identifies risky changed areas, lists what cannot be verified locally, and tells you which files to review first.

It does not replace human code review.
It helps you start review with better evidence.
```

---

## 33. Demo scenario

The strongest demo should use a payment/webhook patch.

Why:

- high consequence,
- clear risk area,
- common AI-agent false confidence,
- test quality matters,
- cannot-verify is natural.

Demo input:

```text
Agent claim:
Added duplicate Stripe webhook protection and tests.

Changed files:
- app/api/stripe/webhook/route.ts
- lib/billing/entitlements.ts
- tests/billing-webhook.test.ts

Test output:
- billing-webhook.test.ts passes
```

PatchTrace output:

```text
Claim support:
Partially supported.

Evidence:
Webhook route and entitlement logic changed.
A billing webhook test exists.

Weak test warning:
The provided test appears to check successful response only. No evidence found that the same event is sent twice or that entitlement state changes only once.

Cannot verify:
Production Stripe webhook settings, live replay behavior, production env vars.

Review first:
1. app/api/stripe/webhook/route.ts
2. lib/billing/entitlements.ts
3. tests/billing-webhook.test.ts

Verdict:
Needs focused human review before accepting.
```

That demo shows the whole product in one screen.

---

## 34. Build phases

### Phase 0 - Manual fixtures

Create 3-5 realistic fixtures before building the full engine.

Scenarios:

1. payment/webhook/idempotency change,
2. auth/session/ownership change,
3. agent claims tests were added but evidence is weak or missing,
4. test output fails while agent says done,
5. AI endpoint added without usage/rate-limit evidence.

Output:

- hand-written expected `VERIFICATION_BRIEF.md`,
- expected JSON shape,
- initial rules to support each scenario.

### Phase 1 - CLI vertical slice

Build:

- collect git diff,
- collect changed files,
- ingest agent summary,
- ingest test output,
- run risk rules,
- run claim/evidence matching,
- export Markdown.

Done when:

- the CLI works on fixture repos,
- tests pass,
- report is useful enough to read before a manual diff review.

### Phase 2 - Better analysis

Add:

- stronger diff parsing,
- test-output adapters,
- more risk rules,
- better review-first ranking,
- JSON report,
- local HTML report if useful.

### Phase 3 - Dogfood on real agent sessions

Use PatchTrace on real Codex/Cursor/Claude Code sessions.

Record:

- where it helped,
- where it was noisy,
- which sections were ignored,
- which section changed the review decision,
- whether it saved time.

Do not add cloud/SaaS until this phase proves repeated value.

---

## 35. Final current decision

Proceed with PatchTrace, but with a stronger technical direction.

Current scope:

```text
Local Patch Verification Engine
```

Primary interface:

```text
CLI-first local devtool
```

Primary input:

```text
git diff + changed files + agent summary + test output
```

Primary output:

```text
VERIFICATION_BRIEF.md
```

Core process:

```text
patch -> claims -> evidence -> tests -> risks -> missing verification -> review-first -> verdict
```

Primary user:

```text
developer reviewing AI-agent coding work before accepting a patch
```

Do not expand into client/public/video/SaaS modes until the local verification engine proves useful.
