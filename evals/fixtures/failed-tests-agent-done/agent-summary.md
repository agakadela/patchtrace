# Agent Summary

Requested task: fix checkout inventory reservation so failed payments release
reserved seats.

What I changed:

- Added a `releaseReservation` call when checkout payment confirmation fails.
- Updated reservation state after successful payment.
- Added tests for failed payment release and successful checkout.

Verification run:

```text
pnpm test tests/checkout/reservations.test.ts
```

All tests pass and the checkout reservation bug is fixed.
