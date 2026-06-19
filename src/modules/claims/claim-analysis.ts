export type ClaimSupport = "supported" | "partially_supported" | "unsupported" | "contradicted" | "cannot_determine";

export interface ClaimAnalysisInput {
  diffText: string;
  summaryText: string;
  testOutputText?: string;
}

export interface AgentClaimAssessment {
  claim: string;
  support: ClaimSupport;
  assessment: string;
}

function includesAll(text: string, needles: string[]): boolean {
  const normalizedText = text.toLowerCase();

  return needles.every((needle) => normalizedText.includes(needle.toLowerCase()));
}

function hasStrongIdempotencyStorage(diffText: string): boolean {
  return /\b(unique|@@unique|transaction|\$transaction|upsert|on conflict)\b/i.test(diffText);
}

function hasSequentialDuplicateTest(input: ClaimAnalysisInput): boolean {
  return (
    includesAll(input.diffText, ["does not grant paid access twice", "toHaveBeenCalledTimes(1)"]) ||
    includesAll(input.testOutputText ?? "", ["does not grant paid access twice", "passed"])
  );
}

function hasProcessedEventGuard(diffText: string): boolean {
  return includesAll(diffText, ["hasProcessedEvent(event.id)", "markEventProcessed(event.id)", "grantPaidAccess"]);
}

function hasAlreadyProcessedResponse(diffText: string): boolean {
  return includesAll(diffText, ["hasProcessedEvent(event.id)", "duplicate: true"]);
}

function maybeAssessDuplicateWebhookClaim(input: ClaimAnalysisInput): AgentClaimAssessment | undefined {
  if (!includesAll(input.summaryText, ["duplicate events", "double-grant paid access"])) {
    return undefined;
  }

  const support: ClaimSupport =
    hasProcessedEventGuard(input.diffText) && hasSequentialDuplicateTest(input) && !hasStrongIdempotencyStorage(input.diffText)
      ? "partially_supported"
      : "cannot_determine";

  return {
    claim: "Duplicate Stripe webhooks do not double-grant paid access.",
    support,
    assessment:
      support === "partially_supported"
        ? "Duplicate webhook claim: partially supported. The diff checks `hasProcessedEvent(event.id)` before granting access and records the event afterward, and the test repeats the same event ID sequentially. The patch does not show a database uniqueness constraint, transaction, insert-first idempotency strategy, or concurrent duplicate delivery test."
        : "Cannot determine duplicate webhook behavior from the provided summary and local material.",
  };
}

function maybeAssessAlreadyProcessedClaim(input: ClaimAnalysisInput): AgentClaimAssessment | undefined {
  if (!includesAll(input.summaryText, ["return `200`", "already processed"])) {
    return undefined;
  }

  return {
    claim: "Already-processed events return `200`.",
    support: hasAlreadyProcessedResponse(input.diffText) ? "supported" : "cannot_determine",
    assessment: hasAlreadyProcessedResponse(input.diffText)
      ? "`app/api/stripe/webhook/route.ts` returns JSON for an already processed event before the entitlement branch."
      : "Cannot determine the already-processed response from the provided patch evidence.",
  };
}

function maybeAssessDuplicateTestClaim(input: ClaimAnalysisInput): AgentClaimAssessment | undefined {
  if (!includesAll(input.summaryText, ["added tests", "duplicate", "webhook deliveries"])) {
    return undefined;
  }

  return {
    claim: "Tests cover duplicate webhook deliveries.",
    support: hasSequentialDuplicateTest(input) ? "partially_supported" : "cannot_determine",
    assessment: hasSequentialDuplicateTest(input)
      ? "Weak or missing duplicate-event test evidence. The test output shows a passing duplicate-event test, but the test appears mock-heavy and only covers a sequential repeat of the same event in one process. It does not prove provider retry behavior, concurrent delivery, database constraint enforcement, or failed-first-processing behavior."
      : "Cannot determine duplicate-event test coverage from the provided test evidence.",
  };
}

function maybeAssessDashboardClaim(input: ClaimAnalysisInput): AgentClaimAssessment | undefined {
  if (!includesAll(input.summaryText, ["no stripe production dashboard changes", "needed"])) {
    return undefined;
  }

  return {
    claim: "No Stripe production dashboard changes are needed.",
    support: "cannot_determine",
    assessment: "Cannot verify Stripe production settings from local diff, agent summary, or test output.",
  };
}

export function assessAgentClaims(input: ClaimAnalysisInput): AgentClaimAssessment[] {
  return [
    maybeAssessDuplicateWebhookClaim(input),
    maybeAssessAlreadyProcessedClaim(input),
    maybeAssessDuplicateTestClaim(input),
    maybeAssessDashboardClaim(input),
  ].filter((assessment): assessment is AgentClaimAssessment => Boolean(assessment));
}
