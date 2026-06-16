# VERIFICATION_BRIEF.md

Fixture: `failed-tests-agent-done`

## Conservative verdict

Conservative verdict: send_agent_back

The agent says the reservation bug is fixed and all tests pass, but the supplied
test output shows a failing reservation test. The work should go back to the
agent before manual acceptance.

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
| All tests pass. | contradicted | Agent done claim: contradicted. `test-output.txt` shows `tests/checkout/reservations.test.ts` has 1 failed test. |
| The checkout reservation bug is fixed. | contradicted | Cannot verify completion while tests are failing. The failing test is for releasing the reservation when payment fails, which is the requested behavior. |
| Tests were added for failed payment release and successful checkout. | partially_supported | The diff shows tests for both scenarios, but the failed-payment release test does not pass in the provided output. |

## Risk areas

- Checkout/payment risk: `src/checkout/confirm-payment.ts` controls reservation state after payment outcomes.
- Reservation-state risk: `src/checkout/reservations.ts` changes paid and released states.
- Test-failure risk: `tests/checkout/reservations.test.ts` directly fails on the bug path.

## Test quality

Observed test command:

```text
pnpm test tests/checkout/reservations.test.ts
```

Result: fail.

Failed test evidence:

- `confirmPayment > releases the reservation when payment fails` failed.
- The failure says `releaseReservation` was expected with `res_123` but had 0 calls.

What the test evidence appears to prove:

- The requested failure-path behavior is not passing in the supplied run.
- The agent's "all tests pass" claim conflicts with the provided output.

## Cannot verify from provided material

- Cannot verify completion while tests are failing.
- Cannot verify whether the failure is in production logic, test mocking, or payment fixture setup without another patch or rerun.
- Cannot verify inventory/reservation consistency after failed payments.

## Review first

1. `tests/checkout/reservations.test.ts` - reproduce the failing test and confirm whether the mock setup or implementation is wrong.
2. `src/checkout/confirm-payment.ts` - inspect the failed-payment branch and whether the caught/returned payment failure path actually calls `releaseReservation`.
3. `src/checkout/reservations.ts` - confirm release state is idempotent and valid for already-paid or expired reservations.

## Suggested next checks

- Send the agent back with the failing test output.
- Re-run `pnpm test tests/checkout/reservations.test.ts` after the fix.
- Add a regression check for both thrown payment failures and non-paid payment statuses if they are separate paths.
