export type TestResult = "pass" | "fail" | "missing" | "unknown";

export interface TestQualityInput {
  diffText: string;
  summaryText: string;
  testOutputText?: string;
}

export interface TestQualityAssessment {
  observedCommand?: string;
  result: TestResult;
  evidenceSummary: string;
  appearsToProve: string[];
  weakOrMissing: string[];
}

function extractObservedCommand(summaryText: string, testOutputText?: string): string | undefined {
  const summaryCommand = summaryText.match(/\bpnpm\s+test[^\r\n`]*/)?.[0].trim();

  if (summaryCommand) {
    return summaryCommand;
  }

  return testOutputText?.match(/\b(vitest|pnpm|npm|yarn)\s+[^\r\n]*/)?.[0].trim();
}

function detectResult(testOutputText?: string): TestResult {
  if (!testOutputText) {
    return "missing";
  }

  if (/\b(failed|failures?|error)\b/i.test(testOutputText) && !/\b0 failed\b/i.test(testOutputText)) {
    return "fail";
  }

  if (/\bpassed\b/i.test(testOutputText) || /✓/.test(testOutputText)) {
    return "pass";
  }

  return "unknown";
}

function includesAll(text: string, needles: string[]): boolean {
  const normalizedText = text.toLowerCase();

  return needles.every((needle) => normalizedText.includes(needle.toLowerCase()));
}

function appearsToExercisePaymentWebhook(input: TestQualityInput): boolean {
  return includesAll(input.diffText, [
    "grants paid access for checkout.session.completed",
    "does not grant paid access twice for the same event",
  ]);
}

export function assessTestQuality(input: TestQualityInput): TestQualityAssessment {
  const result = detectResult(input.testOutputText);
  const observedCommand = extractObservedCommand(input.summaryText, input.testOutputText);

  if (result === "missing") {
    return {
      observedCommand,
      result,
      evidenceSummary: "No test output was provided.",
      appearsToProve: [],
      weakOrMissing: ["Test output is missing, so PatchTrace cannot assess behavioral proof."],
    };
  }

  if (!appearsToExercisePaymentWebhook(input)) {
    return {
      observedCommand,
      result,
      evidenceSummary: "The provided test evidence does not clearly exercise the payment webhook path.",
      appearsToProve: [],
      weakOrMissing: ["Behavioral coverage for the changed payment webhook path is unclear."],
    };
  }

  return {
    observedCommand,
    result,
    evidenceSummary: "Weak or missing duplicate-event test evidence.",
    appearsToProve: [
      "A checkout session can call the entitlement grant path.",
      "A repeated event ID can avoid a second entitlement grant in the tested setup.",
    ],
    weakOrMissing: [
      "Duplicate events arriving concurrently.",
      "Database-level uniqueness for Stripe event IDs.",
      "Behavior when entitlement update succeeds but event recording fails.",
      "Behavior when event recording succeeds but entitlement update fails.",
      "Verification that the webhook signature and event construction paths are tested with realistic Stripe payloads.",
    ],
  };
}
