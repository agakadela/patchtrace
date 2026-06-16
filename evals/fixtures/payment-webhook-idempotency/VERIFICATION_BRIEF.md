# VERIFICATION_BRIEF.md

Fixture: `payment-webhook-idempotency`

## Conservative verdict

Conservative verdict: needs_human_review

The patch is a reasonable start for sequential duplicate Stripe webhook events,
but the provided material does not prove production-safe idempotency or access
correctness. Review the webhook and entitlement path before accepting.

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
| Duplicate Stripe webhooks do not double-grant paid access. | partially_supported | Duplicate webhook claim: partially supported. The diff checks `hasProcessedEvent(event.id)` before granting access and records the event afterward, and the test repeats the same event ID sequentially. The patch does not show a database uniqueness constraint, transaction, insert-first idempotency strategy, or concurrent duplicate delivery test. |
| Already-processed events return `200`. | supported | `app/api/stripe/webhook/route.ts` returns JSON for an already processed event before the entitlement branch. |
| Tests cover duplicate webhook deliveries. | weak | Weak or missing duplicate-event test evidence. The test output shows a passing duplicate-event test, but the test appears mock-heavy and only covers a sequential repeat of the same event in one process. It does not prove provider retry behavior, concurrent delivery, database constraint enforcement, or failed-first-processing behavior. |
| No Stripe production dashboard changes are needed. | cannot_determine | Cannot verify Stripe production settings from local diff, agent summary, or test output. |

## Risk areas

- Payment/webhook/access risk: `app/api/stripe/webhook/route.ts` accepts provider events and can grant paid access.
- Entitlement risk: `src/lib/billing/entitlements.ts` updates plan state and customer linkage.
- Idempotency-storage risk: `src/lib/billing/stripe-events.ts` records processed events but the diff does not show uniqueness or transactional guarantees.
- Test-quality risk: `tests/api/stripe-webhook.test.ts` exercises the happy path and sequential duplicate path, but it does not demonstrate the highest-risk duplicate delivery cases.

## Test quality

Observed test command:

```text
pnpm test tests/api/stripe-webhook.test.ts
```

Result: pass.

What the test evidence appears to prove:

- A checkout session can call the entitlement grant path.
- A repeated event ID can avoid a second entitlement grant in the tested setup.

What remains weak or missing:

- Duplicate events arriving concurrently.
- Database-level uniqueness for Stripe event IDs.
- Behavior when entitlement update succeeds but event recording fails.
- Behavior when event recording succeeds but entitlement update fails.
- Verification that the webhook signature and event construction paths are tested with realistic Stripe payloads.

## Cannot verify from provided material

- Cannot verify Stripe production settings: endpoint URL, enabled events, webhook signing secret, retry settings, live/test mode separation, or dashboard state.
- Cannot verify deployed environment variables such as `STRIPE_WEBHOOK_SECRET`.
- Cannot verify production database constraints or migrations for `stripeEvent.eventId`.
- Cannot verify provider replay behavior or real Stripe webhook delivery logs.
- Cannot verify that paid access is revoked or corrected for previously duplicated events.

## Review first

1. `app/api/stripe/webhook/route.ts` - confirm idempotency ordering, signature handling, error behavior, and whether duplicate event checks are race-safe.
2. `src/lib/billing/stripe-events.ts` - confirm `eventId` has a unique database constraint and that event recording is atomic with the entitlement decision or otherwise safe under retries.
3. `src/lib/billing/entitlements.ts` - confirm paid access updates are correct, auditable, and scoped to the intended user/customer mapping.
4. `tests/api/stripe-webhook.test.ts` - add or inspect tests for concurrent duplicates, database constraint behavior, realistic signed payloads, and partial-failure cases.

## Suggested next checks

- Add a database uniqueness assertion or migration evidence for Stripe event IDs.
- Add a duplicate-event race test or an insert-first idempotency test using a real or faithful fake persistence layer.
- Run a local Stripe CLI replay or provider-dashboard replay in a non-production environment and capture the output.
- Inspect Stripe dashboard webhook settings before treating production behavior as verified.
