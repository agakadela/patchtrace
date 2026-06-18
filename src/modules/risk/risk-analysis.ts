export interface RiskAnalysisInput {
  changedFiles: string[];
  diffText: string;
}

export interface RiskArea {
  label: string;
  filePath: string;
  detail: string;
}

export interface ReviewFirstTarget {
  filePath: string;
  guidance: string;
}

export interface RiskAnalysisResult {
  riskAreas: RiskArea[];
  reviewFirst: ReviewFirstTarget[];
}

function findChangedFile(changedFiles: string[], predicate: (filePath: string) => boolean): string | undefined {
  return changedFiles.find(predicate);
}

function mentionsAny(text: string, needles: string[]): boolean {
  return needles.some((needle) => text.includes(needle));
}

function hasStrongStorageGuarantee(diffText: string): boolean {
  return /\b(unique|@@unique|transaction|\$transaction|upsert|on conflict)\b/i.test(diffText);
}

function orderReviewTargets(
  reviewFirst: ReviewFirstTarget[],
  preferredPaths: Array<string | undefined>,
): ReviewFirstTarget[] {
  const orderedTargets = preferredPaths.flatMap((filePath) =>
    filePath ? reviewFirst.filter((target) => target.filePath === filePath) : [],
  );
  const remainingTargets = reviewFirst.filter(
    (target) => !orderedTargets.some((orderedTarget) => orderedTarget.filePath === target.filePath),
  );

  return [...orderedTargets, ...remainingTargets];
}

export function analyzeRiskAndReviewFirst(input: RiskAnalysisInput): RiskAnalysisResult {
  const webhookRoute = findChangedFile(
    input.changedFiles,
    (filePath) => filePath.includes("stripe") && filePath.includes("webhook") && filePath.endsWith("route.ts"),
  );
  const entitlementFile = findChangedFile(input.changedFiles, (filePath) => filePath.includes("entitlements"));
  const stripeEventStore = findChangedFile(input.changedFiles, (filePath) => filePath.includes("stripe-events"));
  const webhookTest = findChangedFile(
    input.changedFiles,
    (filePath) => filePath.includes("stripe-webhook") && filePath.endsWith(".test.ts"),
  );

  const riskAreas: RiskArea[] = [];
  const reviewFirst: ReviewFirstTarget[] = [];

  if (
    webhookRoute &&
    mentionsAny(input.diffText, ["constructEvent", "stripe-signature", "checkout.session.completed"]) &&
    mentionsAny(input.diffText, ["grantPaidAccess", "paid access"])
  ) {
    riskAreas.push({
      label: "Payment/webhook/access risk",
      filePath: webhookRoute,
      detail: "accepts provider events and can grant paid access.",
    });
    reviewFirst.push({
      filePath: webhookRoute,
      guidance:
        "confirm idempotency ordering, signature handling, error behavior, and whether duplicate event checks are race-safe.",
    });
  }

  if (entitlementFile && mentionsAny(input.diffText, ["grantPaidAccess", "stripeCustomerId", 'plan: "pro"'])) {
    riskAreas.push({
      label: "Entitlement risk",
      filePath: entitlementFile,
      detail: "updates plan state and customer linkage.",
    });
    reviewFirst.push({
      filePath: entitlementFile,
      guidance: "confirm paid access updates are correct, auditable, and scoped to the intended user/customer mapping.",
    });
  }

  if (stripeEventStore && mentionsAny(input.diffText, ["hasProcessedEvent", "markEventProcessed", "eventId"])) {
    const storageDetail = hasStrongStorageGuarantee(input.diffText)
      ? "records processed events; verify storage and entitlement updates stay atomic under retries."
      : "records processed events but the diff does not show uniqueness or transactional guarantees.";

    riskAreas.push({
      label: "Idempotency-storage risk",
      filePath: stripeEventStore,
      detail: storageDetail,
    });
    reviewFirst.push({
      filePath: stripeEventStore,
      guidance:
        "confirm `eventId` has a unique database constraint and that event recording is atomic with the entitlement decision or otherwise safe under retries.",
    });
  }

  if (webhookTest && mentionsAny(input.diffText, ["does not grant paid access twice", "toHaveBeenCalledTimes(1)"])) {
    riskAreas.push({
      label: "Test-quality risk",
      filePath: webhookTest,
      detail:
        "exercises the happy path and sequential duplicate path, but it does not demonstrate the highest-risk duplicate delivery cases.",
    });
    reviewFirst.push({
      filePath: webhookTest,
      guidance:
        "add or inspect tests for concurrent duplicates, database constraint behavior, realistic signed payloads, and partial-failure cases.",
    });
  }

  return {
    riskAreas,
    reviewFirst: orderReviewTargets(reviewFirst, [webhookRoute, stripeEventStore, entitlementFile, webhookTest]),
  };
}
