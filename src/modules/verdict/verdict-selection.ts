import type { AgentClaimAssessment } from "../claims/claim-analysis.js";
import type { ReviewFirstTarget, RiskArea } from "../risk/risk-analysis.js";
import type { TestQualityAssessment } from "../test-quality/test-quality-analysis.js";

export type ConservativeVerdict = "needs_human_review" | "send_agent_back" | "insufficient_material";

export interface VerdictSelectionInput {
  agentClaims: AgentClaimAssessment[];
  hasUsablePatchMaterial: boolean;
  reviewFirst: ReviewFirstTarget[];
  riskAreas: RiskArea[];
  testQuality: TestQualityAssessment;
}

export interface VerdictAssessment {
  verdict: ConservativeVerdict;
  rationale: string;
  cannotVerify: string[];
  suggestedNextChecks: string[];
}

function hasRisk(riskAreas: RiskArea[], label: string): boolean {
  return riskAreas.some((risk) => risk.label === label);
}

function isPaymentWebhookIdempotencySlice(input: VerdictSelectionInput): boolean {
  return (
    hasRisk(input.riskAreas, "Payment/webhook/access risk") &&
    hasRisk(input.riskAreas, "Entitlement risk") &&
    hasRisk(input.riskAreas, "Idempotency-storage risk")
  );
}

function selectPaymentWebhookVerdict(): VerdictAssessment {
  return {
    verdict: "needs_human_review",
    rationale:
      "The provided local material shows a sequential duplicate-event guard and passing tests, but it does not prove deployed Stripe configuration, database uniqueness, provider replay behavior, or remediation for prior duplicate grants. Review the payment webhook and entitlement path before accepting.",
    cannotVerify: [
      "Cannot verify Stripe production settings: endpoint URL, enabled events, webhook signing secret, retry settings, live/test mode separation, or dashboard state.",
      "Cannot verify deployed environment variables such as `STRIPE_WEBHOOK_SECRET`.",
      "Cannot verify production database constraints or migrations for `stripeEvent.eventId`.",
      "Cannot verify provider replay behavior or real Stripe webhook delivery logs.",
      "Cannot verify that paid access is revoked or corrected for previously duplicated events.",
    ],
    suggestedNextChecks: [
      "Add a database uniqueness assertion or migration evidence for Stripe event IDs.",
      "Add a duplicate-event race test or an insert-first idempotency test using a real or faithful fake persistence layer.",
      "Run a local Stripe CLI replay or provider-dashboard replay in a non-production environment and capture the output.",
      "Inspect Stripe dashboard webhook settings before treating production behavior as verified.",
    ],
  };
}

function selectInsufficientMaterialVerdict(input: VerdictSelectionInput): VerdictAssessment {
  const cannotVerify = [
    "Cannot verify changed-file scope because `--changed-files <path>` was not provided with usable local material.",
    "Cannot verify diff hunks because `--diff <path>` was not provided with usable local material.",
    "Cannot collect a live git comparison in this Phase 3 saved-material path; pass saved local material instead.",
  ];

  if (input.testQuality.result === "missing") {
    cannotVerify.push("Cannot verify test behavior because `--test-output <path>` was not provided.");
  }

  return {
    verdict: "insufficient_material",
    rationale:
      "PatchTrace cannot analyze changed files or diff hunks because no saved patch material was provided. This brief is an explicit missing-material state, not evidence that the patch was reviewed.",
    cannotVerify,
    suggestedNextChecks: [
      "Add `--diff <path>` with a saved patch diff.",
      "Add `--changed-files <path>` with the changed-file list for that diff.",
      "Add `--test-output <path>` with the relevant test or command output.",
    ],
  };
}

export function selectConservativeVerdict(input: VerdictSelectionInput): VerdictAssessment {
  if (!input.hasUsablePatchMaterial) {
    return selectInsufficientMaterialVerdict(input);
  }

  if (isPaymentWebhookIdempotencySlice(input)) {
    return selectPaymentWebhookVerdict();
  }

  return {
    verdict: "needs_human_review",
    rationale:
      "The provided local material is enough for an initial PatchTrace brief, but human review is still required before accepting the change.",
    cannotVerify: [],
    suggestedNextChecks: [],
  };
}
